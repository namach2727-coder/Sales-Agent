"""Audited, revisioned pilot access. Separate from paid subscriptions and pricing."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authz.exceptions import PermissionDeniedError
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.config import Settings
from app.models import AuthPlatformRoleAssignment, Store, Tenant, TenantAuditLog
from app.seo_growth.models import SeoAccessGrant, SeoGoogleConnection, SeoSite
from app.seo_growth.security import SeoError
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class SeoPilotAdminService:
    def __init__(self, db: Session, settings: Settings, principal: AuthenticatedPrincipal,
                 tenant_public_id: str, store_public_id: str):
        self.db, self.settings, self.principal = db, settings, principal
        self._authorize()
        try:
            self.scope = resolve_authorized_context(db, principal,
                tenant_public_id=tenant_public_id, store_public_id=store_public_id,
                platform_permission=PermissionCode.TENANT_ACCESS_MANAGE, operational=False)
        except TenantManagementError:
            raise SeoError("not_found", 404) from None

    def _authorize(self):
        # The trusted role snapshot and the current DB permission are both
        # required; a stale/revoked platform assignment cannot grant access.
        if "platform_super_admin" not in self.principal.platform_role_codes:
            raise SeoError("seo_pilot_admin_required", 403)
        active_role = self.db.scalar(select(AuthPlatformRoleAssignment.id).where(
            AuthPlatformRoleAssignment.principal_type == "user",
            AuthPlatformRoleAssignment.principal_id == str(self.principal.user_id),
            AuthPlatformRoleAssignment.role_code == "platform_super_admin",
            AuthPlatformRoleAssignment.status == "active",
        ))
        if active_role is None:
            raise SeoError("seo_pilot_admin_required", 403)
        try:
            AuthorizationService(self.db).require(self.principal.as_authorization_principal(), PermissionCode.TENANT_ACCESS_MANAGE)
        except PermissionDeniedError:
            raise SeoError("seo_pilot_admin_required", 403) from None

    def _grant(self):
        return self.db.scalar(select(SeoAccessGrant).where(
            SeoAccessGrant.tenant_id == self.scope.tenant_id,
            SeoAccessGrant.store_id == self.scope.store_id,
        ).execution_options(populate_existing=True))

    def _usage(self) -> dict:
        sites = self.db.scalar(select(func.count()).select_from(SeoSite).where(
            SeoSite.tenant_id == self.scope.tenant_id, SeoSite.store_id == self.scope.store_id,
            SeoSite.status == "connected"))
        connections = self.db.scalar(select(func.count()).select_from(SeoGoogleConnection).where(
            SeoGoogleConnection.tenant_id == self.scope.tenant_id,
            SeoGoogleConnection.store_id == self.scope.store_id,
            SeoGoogleConnection.status != "disconnected"))
        return {"connected_sites": sites, "google_connections": connections}

    @staticmethod
    def _read(grant):
        if grant is None:
            return None
        return {"status": grant.status, "max_sites": grant.max_sites,
            "max_connections": grant.max_connections, "expires_at": grant.expires_at,
            "revision": grant.revision, "effective": grant.status == "active" and _utc(grant.expires_at) > datetime.now(UTC),
            "source": "internal_pilot"}

    def read(self) -> dict:
        grant = self._grant()
        events = list(self.db.scalars(select(TenantAuditLog).where(
            TenantAuditLog.tenant_id == self.scope.tenant_id, TenantAuditLog.store_id == self.scope.store_id,
            TenantAuditLog.action.in_(("seo.pilot_access_granted", "seo.pilot_access_disabled")),
        ).order_by(TenantAuditLog.id.desc()).limit(20)))
        return {"tenant_public_id": self.scope.tenant_public_id,
            "store_public_id": self.scope.store_public_id,
            "feature_enabled": self.settings.seo_growth_enabled,
            "grant": self._read(grant), "revision": grant.revision if grant else 0,
            "usage": self._usage(), "audit": [{"action": e.action, "created_at": e.created_at,
                "changes": {k: v for k, v in e.details_json.items() if k in {"before", "after", "revision"}}} for e in events]}

    def write(self, *, enabled: bool, expected_revision: int, duration_days: int,
              max_sites: int, max_connections: int) -> dict:
        if enabled and not self.settings.seo_growth_enabled:
            raise SeoError("seo_not_enabled", 403)
        if not 1 <= duration_days <= 30 or not 1 <= max_sites <= 20 or not 1 <= max_connections <= 10:
            raise SeoError("seo_pilot_limits_invalid", 422)
        # Same lock used by customer connection/site quota writes. Concurrent
        # administrators cannot silently overwrite a newer grant revision.
        self.db.execute(select(Store.id).where(Store.id == self.scope.store_id,
            Store.tenant_id == self.scope.tenant_id).with_for_update())
        self._authorize()
        grant = self._grant()
        if (grant.revision if grant else 0) != expected_revision:
            raise SeoError("seo_pilot_revision_conflict", 409)
        if enabled:
            store = self.db.scalar(select(Store).where(Store.id == self.scope.store_id).execution_options(populate_existing=True))
            tenant_status = self.db.scalar(select(Tenant.status).where(Tenant.id == self.scope.tenant_id))
            if tenant_status != "active" or store.status != "active":
                raise SeoError("seo_scope_inactive", 409)
            usage = self._usage()
            if usage["connected_sites"] > max_sites or usage["google_connections"] > max_connections:
                raise SeoError("seo_pilot_limit_below_usage", 409)
        if grant is None and not enabled:
            raise SeoError("not_found", 404)
        before = self._read(grant)
        if grant is None:
            grant = SeoAccessGrant(tenant_id=self.scope.tenant_id, store_id=self.scope.store_id,
                revision=1, max_sites=max_sites, max_connections=max_connections,
                expires_at=datetime.now(UTC) + timedelta(days=duration_days))
            self.db.add(grant)
        else:
            grant.revision += 1
        if enabled:
            grant.max_sites, grant.max_connections = max_sites, max_connections
            grant.expires_at = datetime.now(UTC) + timedelta(days=duration_days)
        grant.status = "active" if enabled else "disabled"
        self.db.flush()
        after = self._read(grant)
        def snapshot(value):
            return {**value, "expires_at": value["expires_at"].isoformat()} if value else None
        self.db.add(TenantAuditLog(tenant_id=self.scope.tenant_id, store_id=self.scope.store_id,
            actor_identity_id=self.principal.user_id,
            action="seo.pilot_access_granted" if enabled else "seo.pilot_access_disabled",
            target_type="seo_pilot", target_public_id=self.scope.store_public_id,
            details_json={"before": snapshot(before), "after": snapshot(after), "revision": grant.revision}))
        self.db.commit()
        return {"grant": after, "revision": grant.revision}
