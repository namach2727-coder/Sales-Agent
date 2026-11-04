"""Tenant-safe Google Search Console connection lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.commerce.service import CommerceService, CommerceForbidden
from app.config import Settings
from app.models import CommerceAuditLog, Store, Tenant, TenantMembership, TenantSubscription, utc_now
from app.seo_service.models import SeoGoogleConnection, SeoGoogleOAuthState, SeoSearchProperty
from app.seo_service.provider import GoogleOAuthTokens, GoogleSeoProvider, GoogleSite
from app.seo_service.security import SeoTokenCipher, new_oauth_state, state_digest


class SeoServiceError(RuntimeError):
    code = "seo_service_error"


class SeoForbidden(SeoServiceError):
    code = "seo_entitlement_required"


class SeoInvalidState(SeoServiceError):
    code = "invalid_google_oauth_state"


class SeoConflict(SeoServiceError):
    code = "seo_connection_conflict"


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class SeoGoogleConnectionService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def scope(self, principal: AuthenticatedPrincipal) -> tuple[Tenant, Store, TenantSubscription]:
        try:
            tenant, store = CommerceService(self.session).customer_scope(principal)
        except CommerceForbidden as exc:
            raise SeoForbidden("An active customer tenant and store are required") from exc
        subscription = self.session.scalar(
            select(TenantSubscription).where(
                TenantSubscription.tenant_id == tenant.id,
                TenantSubscription.store_id == store.id,
                TenantSubscription.status == "active",
                TenantSubscription.current_period_end.is_(None)
                | (TenantSubscription.current_period_end > utc_now()),
            ).order_by(TenantSubscription.id.desc())
        )
        limit = int((subscription.limits_json or {}).get("seo_site_limit", 0)) if subscription else 0
        if limit < 1:
            raise SeoForbidden("An active SEO entitlement is required for this store")
        return tenant, store, subscription

    def begin(self, principal: AuthenticatedPrincipal, provider: GoogleSeoProvider) -> tuple[str, datetime]:
        tenant, store, _subscription = self.scope(principal)
        state = new_oauth_state()
        expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.seo_google_oauth_state_ttl_minutes)
        self.session.add(SeoGoogleOAuthState(
            state_digest=state_digest(state), tenant_id=tenant.id, store_id=store.id,
            initiated_by_user_id=principal.user_id, expires_at=expires_at,
        ))
        self.session.add(CommerceAuditLog(
            tenant_id=tenant.id, store_id=store.id, actor_user_id=principal.user_id,
            action="seo.google_oauth_started", target_type="store",
            target_public_id=store.public_id, details_json={},
        ))
        self.session.commit()
        return provider.authorization_url(state), expires_at

    def _consume_state(self, state: str) -> SeoGoogleOAuthState:
        if not state or len(state) > 512:
            raise SeoInvalidState("Google OAuth state is invalid")
        item = self.session.scalar(
            select(SeoGoogleOAuthState)
            .where(SeoGoogleOAuthState.state_digest == state_digest(state))
            .with_for_update()
        )
        now = datetime.now(UTC)
        if item is None or item.consumed_at is not None or _aware(item.expires_at) <= now:
            self.session.rollback()
            raise SeoInvalidState("Google OAuth state is invalid or expired")
        item.consumed_at = now
        self.session.commit()
        self.session.refresh(item)
        return item

    def complete(self, state: str, code: str, provider: GoogleSeoProvider) -> tuple[SeoGoogleConnection, int]:
        oauth_state = self._consume_state(state)
        tenant = self.session.get(Tenant, oauth_state.tenant_id)
        store = self.session.scalar(select(Store).where(
            Store.id == oauth_state.store_id, Store.tenant_id == oauth_state.tenant_id
        ))
        membership = self.session.scalar(select(TenantMembership.id).where(
            TenantMembership.tenant_id == oauth_state.tenant_id,
            TenantMembership.user_id == oauth_state.initiated_by_user_id,
            TenantMembership.status == "active",
        ))
        subscription = self.session.scalar(select(TenantSubscription).where(
            TenantSubscription.tenant_id == oauth_state.tenant_id,
            TenantSubscription.store_id == oauth_state.store_id,
            TenantSubscription.status == "active",
        ).order_by(TenantSubscription.id.desc()))
        limit = int((subscription.limits_json or {}).get("seo_site_limit", 0)) if subscription else 0
        if (tenant is None or tenant.status != "active" or store is None
                or store.status not in {"active", "onboarding"} or membership is None or limit < 1):
            raise SeoForbidden("The original tenant, store membership, or SEO entitlement is no longer active")

        tokens = provider.exchange_code(code)
        existing = self.session.scalar(select(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == tenant.id,
            SeoGoogleConnection.store_id == store.id,
        ))
        if tokens.refresh_token is None and (existing is None or existing.google_subject != tokens.subject):
            raise SeoConflict("Google did not return a refresh token. Revoke the existing DirectPilot grant and reconnect.")
        cipher = SeoTokenCipher.from_settings(self.settings)
        encrypted_refresh = (
            cipher.encrypt(tokens.refresh_token) if tokens.refresh_token
            else existing.encrypted_refresh_token
        )
        now = utc_now()
        if existing is None:
            existing = SeoGoogleConnection(
                tenant_id=tenant.id, store_id=store.id, google_subject=tokens.subject,
                google_email=tokens.email, encrypted_refresh_token=encrypted_refresh,
                granted_scopes=list(tokens.scopes), status="active",
                connected_by_user_id=oauth_state.initiated_by_user_id, connected_at=now,
                last_verified_at=now,
            )
            self.session.add(existing)
        else:
            existing.google_subject = tokens.subject
            existing.google_email = tokens.email
            existing.encrypted_refresh_token = encrypted_refresh
            existing.granted_scopes = list(tokens.scopes)
            existing.status = "active"
            existing.connected_by_user_id = oauth_state.initiated_by_user_id
            existing.connected_at = now
            existing.last_verified_at = now
            existing.disconnected_at = None
        self.session.add(CommerceAuditLog(
            tenant_id=tenant.id, store_id=store.id,
            actor_user_id=oauth_state.initiated_by_user_id,
            action="seo.google_connected", target_type="seo_google_connection",
            target_public_id=existing.public_id,
            details_json={"scope_count": len(tokens.scopes)},
        ))
        try:
            self.session.flush()
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise SeoConflict("Google account connection conflicts with an existing record") from exc
        self.session.refresh(existing)
        count = self.discover_properties(tenant.id, store.id, existing, tokens, provider)
        return existing, count

    def discover_properties(self, tenant_id: int, store_id: int, connection: SeoGoogleConnection,
                            tokens: GoogleOAuthTokens, provider: GoogleSeoProvider) -> int:
        access_token = tokens.access_token
        sites = provider.list_sites(access_token)
        self._upsert_properties(tenant_id, store_id, connection, sites)
        connection.last_verified_at = utc_now()
        self.session.commit()
        return len(sites)

    def _upsert_properties(self, tenant_id: int, store_id: int,
                           connection: SeoGoogleConnection, sites: list[GoogleSite]) -> None:
        allowed = {"siteOwner", "siteFullUser", "siteRestrictedUser", "siteUnverifiedUser"}
        for site in sites:
            if site.permission_level not in allowed or not site.site_url.startswith(("sc-domain:", "http://", "https://")):
                continue
            item = self.session.scalar(select(SeoSearchProperty).where(
                SeoSearchProperty.tenant_id == tenant_id,
                SeoSearchProperty.store_id == store_id,
                SeoSearchProperty.property_uri == site.site_url,
            ))
            if item is None:
                item = SeoSearchProperty(
                    tenant_id=tenant_id, store_id=store_id, connection_id=connection.id,
                    property_uri=site.site_url, permission_level=site.permission_level,
                )
                self.session.add(item)
            else:
                item.connection_id = connection.id
                item.permission_level = site.permission_level
                item.discovered_at = utc_now()

    def status(self, principal: AuthenticatedPrincipal):
        tenant, store, _subscription = self.scope(principal)
        connection = self.session.scalar(select(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == tenant.id,
            SeoGoogleConnection.store_id == store.id,
        ))
        properties = list(self.session.scalars(select(SeoSearchProperty).where(
            SeoSearchProperty.tenant_id == tenant.id,
            SeoSearchProperty.store_id == store.id,
        ).order_by(SeoSearchProperty.property_uri)).all())
        selected = next((p.property_uri for p in properties if p.is_selected), None)
        return connection, properties, selected

    def select_property(self, principal: AuthenticatedPrincipal, property_public_id: str) -> SeoSearchProperty:
        tenant, store, _subscription = self.scope(principal)
        target = self.session.scalar(select(SeoSearchProperty).where(
            SeoSearchProperty.public_id == property_public_id,
            SeoSearchProperty.tenant_id == tenant.id,
            SeoSearchProperty.store_id == store.id,
        ))
        if target is None:
            raise SeoConflict("The selected Search Console property is not available to this store")
        properties = self.session.scalars(select(SeoSearchProperty).where(
            SeoSearchProperty.tenant_id == tenant.id,
            SeoSearchProperty.store_id == store.id,
        )).all()
        now = utc_now()
        for item in properties:
            item.is_selected = item.id == target.id
            item.selected_at = now if item.id == target.id else None
        self.session.add(CommerceAuditLog(
            tenant_id=tenant.id, store_id=store.id, actor_user_id=principal.user_id,
            action="seo.property_selected", target_type="seo_search_property",
            target_public_id=target.public_id, details_json={"permission_level": target.permission_level},
        ))
        self.session.commit()
        self.session.refresh(target)
        return target

    def disconnect(self, principal: AuthenticatedPrincipal, provider: GoogleSeoProvider) -> None:
        tenant, store, _subscription = self.scope(principal)
        connection = self.session.scalar(select(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == tenant.id,
            SeoGoogleConnection.store_id == store.id,
        ).with_for_update())
        if connection is None or connection.status == "disconnected":
            return
        cipher = SeoTokenCipher.from_settings(self.settings)
        refresh_token = cipher.decrypt(connection.encrypted_refresh_token)
        try:
            provider.revoke(refresh_token)
        except Exception:
            # Local credential deletion is authoritative even if Google's revoke endpoint is unavailable.
            pass
        connection.encrypted_refresh_token = ""
        connection.status = "disconnected"
        connection.disconnected_at = utc_now()
        self.session.execute(
            SeoSearchProperty.__table__.delete().where(
                SeoSearchProperty.tenant_id == tenant.id,
                SeoSearchProperty.store_id == store.id,
            )
        )
        self.session.add(CommerceAuditLog(
            tenant_id=tenant.id, store_id=store.id, actor_user_id=principal.user_id,
            action="seo.google_disconnected", target_type="seo_google_connection",
            target_public_id=connection.public_id, details_json={},
        ))
        self.session.commit()
