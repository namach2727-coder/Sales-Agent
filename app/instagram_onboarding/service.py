"""Tenant-safe orchestration for official Instagram customer onboarding."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authz.exceptions import PermissionDeniedError
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.commerce.service import CommerceService
from app.config import Settings
from app.instagram_channel.models import InstagramConnection, InstagramOAuthState
from app.instagram_channel.security import FernetTokenCipher
from app.instagram_onboarding.provider import (
    InstagramOAuthAccount,
    InstagramOAuthProvider,
)
from app.models import (
    CommerceAuditLog,
    Store,
    Tenant,
    TenantMembership,
    TenantSubscription,
    utc_now,
)


class InstagramOnboardingError(Exception):
    code = "instagram_onboarding_error"


class InstagramOnboardingForbidden(InstagramOnboardingError):
    code = "instagram_entitlement_required"


class InstagramOnboardingInvalidState(InstagramOnboardingError):
    code = "invalid_oauth_state"


class InstagramOnboardingConflict(InstagramOnboardingError):
    code = "instagram_connection_conflict"


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class InstagramOnboardingService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def scope(
        self, principal: AuthenticatedPrincipal
    ) -> tuple[Tenant, Store, TenantSubscription | None]:
        tenant, store = CommerceService(self.session).customer_scope(principal)
        try:
            AuthorizationService(self.session).require(
                principal.as_authorization_principal(tenant.id),
                PermissionCode.INSTAGRAM_CONNECTION_CREDENTIALS_MANAGE,
                tenant_id=tenant.id,
            )
        except PermissionDeniedError as exc:
            raise InstagramOnboardingForbidden(
                "Instagram connection permission is required"
            ) from exc
        subscription = self.session.scalar(
            select(TenantSubscription)
            .where(
                TenantSubscription.tenant_id == tenant.id,
                TenantSubscription.store_id == store.id,
                TenantSubscription.status == "active",
            )
            .order_by(TenantSubscription.id.desc())
        )
        return tenant, store, subscription

    @staticmethod
    def account_limit(subscription: TenantSubscription | None) -> int:
        if subscription is None:
            return 0
        return max(0, int((subscription.limits_json or {}).get("instagram_account_limit", 0)))

    def status(
        self, principal: AuthenticatedPrincipal
    ) -> tuple[Tenant, Store, int, list[InstagramConnection]]:
        tenant, store, subscription = self.scope(principal)
        limit = self.account_limit(subscription)
        accounts = list(
            self.session.scalars(
                select(InstagramConnection)
                .where(
                    InstagramConnection.tenant_id == tenant.id,
                    InstagramConnection.store_id == store.id,
                    InstagramConnection.status != "archived",
                )
                .order_by(InstagramConnection.created_at, InstagramConnection.public_id)
            ).all()
        )
        return tenant, store, limit, accounts

    def begin(
        self,
        principal: AuthenticatedPrincipal,
        provider: InstagramOAuthProvider,
    ) -> tuple[str, datetime]:
        tenant, store, limit, accounts = self.status(principal)
        # The existing Instagram model permits one connection per store. An
        # existing record is deliberately re-authorizable rather than treated
        # as exhausted capacity.
        if limit < 1:
            raise InstagramOnboardingForbidden(
                "An active Instagram entitlement with available capacity is required"
            )
        nonce = secrets.token_urlsafe(32)
        authorization_url = provider.authorization_url(nonce)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self.settings.meta_oauth_state_ttl_minutes
        )
        item = InstagramOAuthState(
            state_digest=_digest(nonce),
            tenant_id=tenant.id,
            store_id=store.id,
            initiated_by_user_id=principal.user_id,
            expires_at=expires_at,
        )
        self.session.add(item)
        self.session.flush()
        self.session.add(
            CommerceAuditLog(
                tenant_id=tenant.id,
                store_id=store.id,
                actor_user_id=principal.user_id,
                action="instagram.oauth_started",
                target_type="store",
                target_public_id=store.public_id,
                details_json={"state_public_id": item.public_id},
            )
        )
        self.session.commit()
        return authorization_url, expires_at

    def _consume_state(self, state: str) -> InstagramOAuthState:
        normalized = state.strip()
        if not normalized or len(normalized) > 512:
            raise InstagramOnboardingInvalidState("OAuth state is invalid")
        item = self.session.scalar(
            select(InstagramOAuthState)
            .where(InstagramOAuthState.state_digest == _digest(normalized))
            .with_for_update()
        )
        now = datetime.now(UTC)
        if (
            item is None
            or item.consumed_at is not None
            or _aware(item.expires_at) <= now
        ):
            self.session.rollback()
            raise InstagramOnboardingInvalidState("OAuth state is invalid or expired")
        item.consumed_at = now
        self.session.commit()
        self.session.refresh(item)
        return item

    def complete(
        self,
        *,
        state: str,
        code: str,
        provider: InstagramOAuthProvider,
    ) -> tuple[InstagramConnection, Tenant, Store]:
        oauth_state = self._consume_state(state)
        account = provider.exchange(code)
        tenant = self.session.get(Tenant, oauth_state.tenant_id)
        store = self.session.get(Store, oauth_state.store_id)
        if tenant is None or store is None or tenant.status != "active" or store.status not in {"onboarding", "active"}:
            raise InstagramOnboardingConflict("OAuth target is no longer available")
        subscription = self.session.scalar(
            select(TenantSubscription).where(
                TenantSubscription.tenant_id == tenant.id,
                TenantSubscription.store_id == store.id,
                TenantSubscription.status == "active",
            )
        )
        membership_exists = self.session.scalar(
            select(TenantMembership.id).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == oauth_state.initiated_by_user_id,
                TenantMembership.status == "active",
            )
        )
        if membership_exists is None:
            raise InstagramOnboardingForbidden(
                "Instagram onboarding authorization is no longer valid"
            )
        if self.account_limit(subscription) < 1:
            raise InstagramOnboardingForbidden("Instagram entitlement is no longer active")
        connection = self._save_connection(oauth_state, account)
        return connection, tenant, store

    def _save_connection(
        self, oauth_state: InstagramOAuthState, account: InstagramOAuthAccount
    ) -> InstagramConnection:
        connection = self.session.scalar(
            select(InstagramConnection).where(
                InstagramConnection.tenant_id == oauth_state.tenant_id,
                InstagramConnection.store_id == oauth_state.store_id,
            )
        )
        now = utc_now()
        cipher = FernetTokenCipher.from_settings(self.settings)
        if connection is None:
            connection = InstagramConnection(
                tenant_id=oauth_state.tenant_id,
                store_id=oauth_state.store_id,
                meta_app_id=self.settings.meta_app_id.strip(),
                instagram_account_id=account.account_id,
                instagram_username=account.username,
                external_account_name="Instagram OAuth",
                status="active",
                connected_at=now,
                last_verified_at=now,
                revision=1,
            )
            self.session.add(connection)
        elif connection.status == "archived":
            raise InstagramOnboardingConflict("Archived connection cannot be reused")
        else:
            connection.meta_app_id = self.settings.meta_app_id.strip()
            connection.instagram_account_id = account.account_id
            connection.instagram_username = account.username
            connection.status = "active"
            connection.status_reason = "Connected with official Instagram Login"
            connection.connected_at = connection.connected_at or now
            connection.disconnected_at = None
            connection.last_verified_at = now
            connection.revision += 1
        connection.encrypted_access_token = cipher.encrypt(account.access_token)
        connection.token_type = account.token_type
        connection.token_scopes = list(account.scopes)
        connection.token_updated_at = now
        if account.expires_in is not None:
            connection.token_expires_at = now + timedelta(seconds=account.expires_in)
        try:
            self.session.flush()
            self.session.add(
                CommerceAuditLog(
                    tenant_id=oauth_state.tenant_id,
                    store_id=oauth_state.store_id,
                    actor_user_id=oauth_state.initiated_by_user_id,
                    action="instagram.oauth_connected",
                    target_type="instagram_connection",
                    target_public_id=connection.public_id,
                    details_json={
                        "status": "active",
                        "scope_count": len(account.scopes),
                    },
                )
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise InstagramOnboardingConflict(
                "Instagram account is already connected"
            ) from exc
        self.session.refresh(connection)
        return connection
