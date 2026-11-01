"""Tenant-safe F1 onboarding. No metric jobs, billing activation or CMS writes."""
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authz.permissions import PermissionCode
from app.config import Settings
from app.models import Store, Tenant, TenantAuditLog
from app.seo_growth.google_client import (
    GoogleGscError, GoogleSearchConsoleClient, create_oauth_state, create_pkce_pair,
    validate_property_identifier,
)
from app.seo_growth.models import SeoAccessGrant, SeoGoogleConnection, SeoOAuthAttempt, SeoSite
from app.seo_growth.security import SeoCipher, SeoError, digest, frontend_origin
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


def now() -> datetime:
    return datetime.now(UTC)


class SeoOnboardingService:
    def __init__(self, db: Session, settings: Settings, principal: AuthenticatedPrincipal,
                 tenant_public_id: str, store_public_id: str, *, mutation: bool,
                 cleanup: bool = False, provider: GoogleSearchConsoleClient | None = None):
        self.db, self.settings, self.principal = db, settings, principal
        self._provider = provider
        try:
            self.scope = resolve_authorized_context(
                db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id,
                tenant_permission=PermissionCode.TENANT_SETTINGS_UPDATE if mutation else PermissionCode.TENANT_SETTINGS_READ,
                store_permission=PermissionCode.STORE_UPDATE if mutation else PermissionCode.STORE_READ,
                platform_permission=PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ,
                operational=not cleanup,
            )
        except TenantManagementError:
            raise SeoError("not_found", 404) from None
        self.tenant, self.store, self.user = self.scope.tenant_id, self.scope.store_id, principal.user_id

    @property
    def provider(self) -> GoogleSearchConsoleClient:
        frontend_origin(self.settings)
        if self._provider is None:
            self._provider = GoogleSearchConsoleClient(
                client_id=self.settings.seo_google_client_id,
                client_secret=self.settings.seo_google_client_secret.get_secret_value(),
                redirect_uri=self.settings.seo_google_redirect_uri,
            )
        return self._provider

    def _lock(self) -> None:
        # Serialize quota checks and lifecycle writes across all app workers.
        self.db.execute(select(Store.id).where(Store.id == self.store, Store.tenant_id == self.tenant).with_for_update())

    def _grant(self) -> SeoAccessGrant:
        if not self.settings.seo_growth_enabled:
            raise SeoError("seo_not_enabled", 403)
        grant = self.db.scalar(select(SeoAccessGrant).where(
            SeoAccessGrant.tenant_id == self.tenant, SeoAccessGrant.store_id == self.store,
            SeoAccessGrant.status == "active", SeoAccessGrant.expires_at > now(),
        ).execution_options(populate_existing=True))
        if grant is None:
            raise SeoError("seo_access_required", 403)
        return grant

    def _connections(self):
        return select(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == self.tenant,
            SeoGoogleConnection.store_id == self.store,
            SeoGoogleConnection.user_id == self.user,
        )

    def _sites(self):
        return select(SeoSite).where(SeoSite.tenant_id == self.tenant, SeoSite.store_id == self.store)

    def _audit(self, action: str, target: str, *, details: dict | None = None) -> None:
        self.db.add(TenantAuditLog(tenant_id=self.tenant, store_id=self.store,
            actor_identity_id=self.user, action="seo." + action, target_type="seo",
            target_public_id=target, details_json=details or {}))

    def _seal(self, secret: str, purpose: str) -> str:
        return SeoCipher(self.settings).encrypt(secret, tenant=self.tenant, store=self.store, user=self.user, purpose=purpose)

    def _open(self, secret: str, purpose: str) -> str:
        return SeoCipher(self.settings).decrypt(secret, tenant=self.tenant, store=self.store, user=self.user, purpose=purpose)

    def status(self) -> dict:
        grant = self.db.scalar(select(SeoAccessGrant).where(
            SeoAccessGrant.tenant_id == self.tenant, SeoAccessGrant.store_id == self.store,
            SeoAccessGrant.status == "active", SeoAccessGrant.expires_at > now(),
        ).execution_options(populate_existing=True))
        configured = False
        if self.settings.seo_growth_enabled:
            try:
                _ = self.provider
                SeoCipher(self.settings)
                configured = True
            except (SeoError, GoogleGscError):
                pass
        connection = self.db.scalar(self._connections())
        return {"enabled": self.settings.seo_growth_enabled, "configured": configured,
                "access_granted": grant is not None, "max_sites": grant.max_sites if grant else 0,
                "connection": connection_read(connection) if connection else None}

    def begin(self) -> dict:
        self._grant()
        provider = self.provider
        self._lock()
        grant = self._grant()
        recent = self.db.scalar(select(func.count()).select_from(SeoOAuthAttempt).where(
            SeoOAuthAttempt.store_id == self.store, SeoOAuthAttempt.tenant_id == self.tenant,
            SeoOAuthAttempt.user_id == self.user, SeoOAuthAttempt.created_at > now() - timedelta(minutes=10),
        ))
        if recent >= 5:
            raise SeoError("seo_connect_rate_limited", 429)
        self._connection_capacity(grant)
        state = create_oauth_state()
        verifier, challenge = create_pkce_pair()
        expires = now() + timedelta(minutes=10)
        # Starting over invalidates every older flow, including an exchange in
        # progress. It cannot overwrite a later connection on callback return.
        self._cancel_attempts()
        self.db.add(SeoOAuthAttempt(tenant_id=self.tenant, store_id=self.store, user_id=self.user,
            state_digest=digest(state), session_digest=digest(self.principal.session_id),
            encrypted_verifier=self._seal(verifier, "pkce"), expires_at=expires))
        self._audit("oauth_started", self.scope.store_public_id)
        self.db.commit()
        return {"authorization_url": provider.authorization_url(state=state, code_challenge=challenge, force_consent=True),
                "expires_at": expires}

    def _connection_capacity(self, grant: SeoAccessGrant) -> None:
        existing = self.db.scalar(self._connections())
        active = self.db.scalar(select(func.count()).select_from(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == self.tenant, SeoGoogleConnection.store_id == self.store,
            SeoGoogleConnection.status != "disconnected"))
        if (existing is None or existing.status == "disconnected") and active >= grant.max_connections:
            raise SeoError("seo_connection_limit", 409)

    def _cancel_attempts(self) -> None:
        self.db.execute(update(SeoOAuthAttempt).execution_options(synchronize_session="fetch").where(
            SeoOAuthAttempt.tenant_id == self.tenant, SeoOAuthAttempt.store_id == self.store,
            SeoOAuthAttempt.user_id == self.user, SeoOAuthAttempt.cancelled_at.is_(None),
        ).values(cancelled_at=now(), encrypted_verifier=None))

    def complete(self, state: str, *, code: str | None, denied: bool = False) -> str:
        self._grant()
        provider = self.provider
        attempt = self.db.scalar(select(SeoOAuthAttempt).where(
            SeoOAuthAttempt.state_digest == digest(state), SeoOAuthAttempt.tenant_id == self.tenant,
            SeoOAuthAttempt.store_id == self.store, SeoOAuthAttempt.user_id == self.user,
            SeoOAuthAttempt.session_digest == digest(self.principal.session_id),
            SeoOAuthAttempt.used_at.is_(None), SeoOAuthAttempt.cancelled_at.is_(None),
            SeoOAuthAttempt.expires_at > now(),
        ))
        if attempt is None or not attempt.encrypted_verifier:
            raise SeoError("seo_oauth_state_invalid")
        verifier = self._open(attempt.encrypted_verifier, "pkce")
        attempt_id = attempt.id
        # Atomic compare-and-set, committed BEFORE token exchange. This also
        # prevents replay after a Google timeout or process crash.
        result = self.db.execute(update(SeoOAuthAttempt).execution_options(synchronize_session="fetch").where(
            SeoOAuthAttempt.id == attempt_id, SeoOAuthAttempt.used_at.is_(None),
            SeoOAuthAttempt.cancelled_at.is_(None), SeoOAuthAttempt.expires_at > now(),
        ).values(used_at=now(), encrypted_verifier=None))
        self.db.commit()
        if result.rowcount != 1:
            raise SeoError("seo_oauth_state_invalid")
        if denied:
            self._audit("oauth_denied", self.scope.store_public_id)
            self.db.commit()
            return "denied"
        if not code:
            raise SeoError("seo_oauth_code_missing")
        tokens = provider.exchange_code(code=code, code_verifier=verifier)
        # Never attach an old account's refresh token to a different consent.
        if not tokens.refresh_token:
            raise SeoError("seo_google_consent_required")
        self._lock()
        grant = self._grant()
        # Recheck access after the external request and after acquiring lock.
        try:
            resolve_authorized_context(self.db, self.principal,
                tenant_public_id=self.scope.tenant_public_id, store_public_id=self.scope.store_public_id,
                store_permission=PermissionCode.STORE_UPDATE, platform_permission=PermissionCode.TENANT_UPDATE)
        except TenantManagementError:
            raise SeoError("not_found", 404) from None
        valid = self.db.scalar(select(SeoOAuthAttempt.id).where(
            SeoOAuthAttempt.id == attempt_id, SeoOAuthAttempt.cancelled_at.is_(None), SeoOAuthAttempt.expires_at > now()))
        if valid is None:
            raise SeoError("seo_oauth_state_invalid")
        self._connection_capacity(grant)
        connection = self.db.scalar(self._connections())
        if connection is None:
            connection = SeoGoogleConnection(tenant_id=self.tenant, store_id=self.store, user_id=self.user)
            self.db.add(connection)
        else:
            # The Google account may have changed. Existing sites require fresh
            # explicit selection; never reuse earlier property authorization.
            self.db.execute(update(SeoSite).where(SeoSite.connection_id == connection.id,
                SeoSite.tenant_id == self.tenant, SeoSite.store_id == self.store).values(status="disconnected"))
        connection.encrypted_refresh_token = self._seal(tokens.refresh_token, "refresh")
        connection.key_version = self.settings.seo_token_key_version
        connection.granted_scope = tokens.scope
        connection.status, connection.disconnected_at = "connected", None
        self.db.flush()
        self._audit("google_connected", connection.public_id)
        self.db.commit()
        return "connected"

    def _connection(self, public_id: str) -> SeoGoogleConnection:
        connection = self.db.scalar(self._connections().where(SeoGoogleConnection.public_id == public_id))
        if connection is None:
            raise SeoError("not_found", 404)
        return connection

    def properties(self, public_id: str) -> list:
        self._grant()
        connection = self._connection(public_id)
        if connection.status != "connected" or not connection.encrypted_refresh_token:
            raise SeoError("seo_reauthorization_required", 409)
        if connection.key_version != self.settings.seo_token_key_version:
            raise SeoError("seo_credential_unavailable", 503)
        token = self._open(connection.encrypted_refresh_token, "refresh")
        try:
            tokens = self.provider.refresh_access_token(refresh_token=token, verified_scope=connection.granted_scope)
            return self.provider.list_properties(access_token=tokens.access_token)
        except GoogleGscError as exc:
            if exc.code == "google_authorization_expired":
                # Conditional update cannot revive or overwrite a concurrent
                # reconnect/disconnect with a different credential.
                self.db.execute(update(SeoGoogleConnection).where(
                    SeoGoogleConnection.id == connection.id, SeoGoogleConnection.status == "connected",
                    SeoGoogleConnection.encrypted_refresh_token == connection.encrypted_refresh_token,
                ).values(status="reauthorization_required"))
                self.db.commit()
            raise

    def add_site(self, connection_public_id: str, property_id: str) -> SeoSite:
        self._grant()
        try:
            property_id = validate_property_identifier(property_id)
        except ValueError:
            raise SeoError("seo_property_invalid", 422) from None
        connection = self._connection(connection_public_id)
        original_credential = connection.encrypted_refresh_token
        properties = self.properties(connection_public_id)
        selected = next((item for item in properties if item.site_url == property_id), None)
        if selected is None:
            raise SeoError("seo_property_not_granted", 403)
        self._lock()
        grant = self._grant()
        self.db.refresh(connection)
        if connection.status != "connected" or connection.encrypted_refresh_token != original_credential:
            raise SeoError("seo_connection_changed", 409)
        site = self.db.scalar(self._sites().where(SeoSite.property_id == selected.site_url))
        if site is not None and site.status == "connected":
            if site.connection_id != connection.id:
                raise SeoError("seo_site_already_connected", 409)
            return site
        count = self.db.scalar(select(func.count()).select_from(SeoSite).where(
            SeoSite.tenant_id == self.tenant, SeoSite.store_id == self.store, SeoSite.status == "connected"))
        if count >= grant.max_sites:
            raise SeoError("seo_site_limit", 409)
        if site is None:
            site = SeoSite(tenant_id=self.tenant, store_id=self.store, property_id=selected.site_url)
            self.db.add(site)
        site.connection_id, site.permission_level, site.status = connection.id, selected.permission_level, "connected"
        self.db.flush()
        self._audit("site_connected", site.public_id)
        self.db.commit()
        return site

    def sites(self, *, limit: int = 20, offset: int = 0) -> list[SeoSite]:
        self._grant()
        return list(self.db.scalars(self._sites().order_by(SeoSite.id).limit(limit).offset(offset)))

    def disconnect_site(self, public_id: str) -> None:
        self._lock()
        site = self.db.scalar(self._sites().where(SeoSite.public_id == public_id))
        if site is None:
            raise SeoError("not_found", 404)
        if site.status != "disconnected":
            site.status = "disconnected"
            self._audit("site_disconnected", site.public_id)
            self.db.commit()

    def disconnect(self, public_id: str, *, revoke_google: bool) -> dict:
        self._lock()
        connection = self._connection(public_id)
        token = None
        # Local deletion still works after key rotation/configuration failure.
        if revoke_google and connection.encrypted_refresh_token:
            try:
                token = self._open(connection.encrypted_refresh_token, "refresh")
            except SeoError:
                pass
        self._cancel_attempts()
        connection.encrypted_refresh_token, connection.status, connection.disconnected_at = None, "disconnected", now()
        self.db.execute(update(SeoSite).where(SeoSite.connection_id == connection.id,
            SeoSite.tenant_id == self.tenant, SeoSite.store_id == self.store).values(status="disconnected"))
        self._audit("google_disconnected", connection.public_id)
        self.db.commit()
        revoked = False
        if revoke_google and token:
            try:
                revoked = self.provider.revoke_token(refresh_token=token)
            except (SeoError, GoogleGscError):
                pass
        result = "revoked" if revoked else "unconfirmed" if revoke_google else "not_requested"
        self._audit("google_revocation", connection.public_id, details={"result": result})
        self.db.commit()
        return {"status": "disconnected", "google_revocation": result}

    def redirect(self, status: str) -> str:
        return frontend_origin(self.settings) + "/dashboard/seo?" + urlencode({
            "seo": status, "tenant": self.scope.tenant_public_id, "store": self.scope.store_public_id})


def connection_read(connection: SeoGoogleConnection) -> dict:
    return {"public_id": connection.public_id, "status": connection.status,
            "connected_at": connection.created_at, "updated_at": connection.updated_at}


def callback_service(db: Session, settings: Settings, principal: AuthenticatedPrincipal,
                     state: str, provider=None) -> SeoOnboardingService:
    if not state or len(state) > 128:
        raise SeoError("seo_oauth_state_invalid")
    attempt = db.scalar(select(SeoOAuthAttempt).where(
        SeoOAuthAttempt.state_digest == digest(state), SeoOAuthAttempt.user_id == principal.user_id,
        SeoOAuthAttempt.session_digest == digest(principal.session_id),
        SeoOAuthAttempt.used_at.is_(None), SeoOAuthAttempt.cancelled_at.is_(None), SeoOAuthAttempt.expires_at > now(),
    ))
    if attempt is None:
        raise SeoError("seo_oauth_state_invalid")
    tenant, store = db.get(Tenant, attempt.tenant_id), db.get(Store, attempt.store_id)
    return SeoOnboardingService(db, settings, principal, tenant.public_id, store.public_id, mutation=True, provider=provider)
