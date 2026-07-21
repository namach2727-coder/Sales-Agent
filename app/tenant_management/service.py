from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authz.context import PrincipalType
from app.models import (
    AuthRole,
    AuthTenantRoleAssignment,
    Store,
    StoreAccessAssignment,
    Tenant,
    TenantAuditLog,
    TenantMembership,
    UserIdentity,
)
from app.tenant_management.domain import (
    ConflictError,
    InvalidTransitionError,
    ResourceNotFoundError,
    ValidationError,
    normalize_custom_domain,
    normalize_name,
    normalize_slug,
    normalize_store_settings,
    normalize_subdomain,
)


def _now() -> datetime:
    return datetime.now(UTC)


class TenantStoreService:
    """Owns validated lifecycle mutations and tenant-scoped queries."""

    def __init__(self, session: Session, *, actor_identity_id: int | None = None) -> None:
        self.session = session
        self.actor_identity_id = actor_identity_id

    def _audit(
        self,
        tenant: Tenant,
        action: str,
        target_type: str,
        target_public_id: str,
        *,
        store: Store | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            TenantAuditLog(
                tenant_id=tenant.id,
                store_id=store.id if store else None,
                actor_identity_id=self.actor_identity_id,
                action=action,
                target_type=target_type,
                target_public_id=target_public_id,
                details_json=details or {},
            )
        )

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("normalized identifier already exists") from exc

    def create_tenant(self, *, name: str, slug: str) -> Tenant:
        tenant = Tenant(
            name=normalize_name(name),
            slug=normalize_slug(slug),
            status="active",
            created_by_identity_id=self.actor_identity_id,
        )
        self.session.add(tenant)
        self.session.flush()
        self._audit(tenant, "tenant.created", "tenant", tenant.public_id)
        self._commit()
        self.session.refresh(tenant)
        return tenant

    def update_tenant(self, tenant: Tenant, *, name: str | None = None, slug: str | None = None) -> Tenant:
        if tenant.status == "archived":
            raise InvalidTransitionError("archived tenant cannot be updated")
        before = {"name": tenant.name, "slug": tenant.slug}
        if name is not None:
            tenant.name = normalize_name(name)
        if slug is not None:
            tenant.slug = normalize_slug(slug)
        self._audit(
            tenant, "tenant.updated", "tenant", tenant.public_id,
            details={"before": before, "after": {"name": tenant.name, "slug": tenant.slug}},
        )
        self._commit()
        return tenant

    def transition_tenant(self, tenant: Tenant, target: str) -> Tenant:
        allowed = {
            "active": {"suspended", "archived"},
            "suspended": {"active", "archived"},
            "archived": set(),
        }
        if target == tenant.status:
            return tenant
        if target not in allowed.get(tenant.status, set()):
            raise InvalidTransitionError(f"cannot transition tenant from {tenant.status} to {target}")
        previous = tenant.status
        tenant.status = target
        now = _now()
        tenant.suspended_at = now if target == "suspended" else None
        tenant.archived_at = now if target == "archived" else tenant.archived_at
        self._audit(
            tenant, f"tenant.{target}", "tenant", tenant.public_id,
            details={"from": previous, "to": target},
        )
        self._commit()
        return tenant

    def create_store(
        self,
        tenant: Tenant,
        *,
        name: str,
        slug: str,
        timezone: str = "Asia/Tehran",
        locale: str = "fa-IR",
        currency_code: str = "IRR",
        subdomain: str | None = None,
        custom_domain: str | None = None,
    ) -> Store:
        if tenant.status != "active":
            raise InvalidTransitionError("active stores require an active tenant")
        timezone, locale, currency_code = normalize_store_settings(timezone, locale, currency_code)
        store = Store(
            tenant=tenant,
            name=normalize_name(name),
            slug=normalize_slug(slug),
            status="active",
            timezone=timezone,
            locale=locale,
            currency_code=currency_code,
            subdomain=normalize_subdomain(subdomain),
            custom_domain=normalize_custom_domain(custom_domain),
        )
        self.session.add(store)
        self.session.flush()
        self._audit(tenant, "store.created", "store", store.public_id, store=store)
        self._commit()
        self.session.refresh(store)
        return store

    def update_store(
        self,
        tenant: Tenant,
        store: Store,
        *,
        name: str | None = None,
        slug: str | None = None,
        timezone: str | None = None,
        locale: str | None = None,
        currency_code: str | None = None,
        subdomain: str | None = None,
        custom_domain: str | None = None,
        domains_supplied: bool = False,
    ) -> Store:
        if store.tenant_id != tenant.id or store.status == "archived":
            raise ResourceNotFoundError("resource not found")
        before_domains = {"subdomain": store.subdomain, "custom_domain": store.custom_domain}
        if name is not None:
            store.name = normalize_name(name)
        if slug is not None:
            store.slug = normalize_slug(slug)
        if timezone is not None or locale is not None or currency_code is not None:
            store.timezone, store.locale, store.currency_code = normalize_store_settings(
                timezone or store.timezone,
                locale or store.locale,
                currency_code or store.currency_code,
            )
        if domains_supplied:
            store.subdomain = normalize_subdomain(subdomain)
            store.custom_domain = normalize_custom_domain(custom_domain)
        self._audit(tenant, "store.updated", "store", store.public_id, store=store)
        if before_domains != {"subdomain": store.subdomain, "custom_domain": store.custom_domain}:
            self._audit(
                tenant, "store.domains_updated", "store", store.public_id, store=store,
                details={"before": before_domains, "after": {"subdomain": store.subdomain, "custom_domain": store.custom_domain}},
            )
        self._commit()
        return store

    def transition_store(self, tenant: Tenant, store: Store, target: str) -> Store:
        if store.tenant_id != tenant.id:
            raise ResourceNotFoundError("resource not found")
        allowed = {
            "active": {"suspended", "archived"},
            "suspended": {"active", "archived"},
            "archived": set(),
        }
        if target == store.status:
            return store
        if target == "active" and tenant.status != "active":
            raise InvalidTransitionError("store cannot be active under an inactive tenant")
        if target not in allowed.get(store.status, set()):
            raise InvalidTransitionError(f"cannot transition store from {store.status} to {target}")
        previous = store.status
        store.status = target
        now = _now()
        store.suspended_at = now if target == "suspended" else None
        store.archived_at = now if target == "archived" else store.archived_at
        self._audit(
            tenant, f"store.{target}", "store", store.public_id, store=store,
            details={"from": previous, "to": target},
        )
        self._commit()
        return store

    def add_membership(
        self,
        tenant: Tenant,
        identity: UserIdentity,
        *,
        role_codes: tuple[str, ...],
        all_store_access: bool = False,
        stores: tuple[Store, ...] = (),
        status: str = "active",
    ) -> TenantMembership:
        if status not in {"invited", "active"}:
            raise ValidationError("new membership status must be invited or active")
        existing = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == identity.id,
            )
        )
        if existing is not None:
            raise ConflictError("membership already exists")
        roles = list(
            self.session.scalars(
                select(AuthRole).where(
                    AuthRole.code.in_(role_codes), AuthRole.scope == "tenant"
                )
            ).all()
        )
        if {role.code for role in roles} != set(role_codes):
            raise ValidationError("one or more tenant role codes are unknown")
        membership = TenantMembership(
            user_id=identity.id,
            tenant_id=tenant.id,
            principal_type=PrincipalType.USER.value,
            principal_id=str(identity.id),
            status=status,
            all_store_access=all_store_access,
            invited_at=_now() if status == "invited" else None,
            activated_at=_now() if status == "active" else None,
        )
        self.session.add(membership)
        self.session.flush()
        for role in roles:
            self.session.add(
                AuthTenantRoleAssignment(
                    membership_id=membership.id, role_code=role.code, status="active"
                )
            )
        for store in stores:
            if store.tenant_id != tenant.id:
                raise ResourceNotFoundError("resource not found")
            self.session.add(
                StoreAccessAssignment(
                    membership_id=membership.id,
                    store_id=store.id,
                    status="active",
                    created_by_identity_id=self.actor_identity_id,
                )
            )
        self._audit(
            tenant, "membership.created", "membership", membership.public_id,
            details={"status": status, "role_codes": sorted(role_codes), "all_store_access": all_store_access},
        )
        self._commit()
        return membership

    def transition_membership(self, tenant: Tenant, membership: TenantMembership, target: str) -> TenantMembership:
        if membership.tenant_id != tenant.id or target not in {"active", "suspended", "revoked"}:
            raise ResourceNotFoundError("resource not found")
        if membership.status == "revoked" and target != "revoked":
            raise InvalidTransitionError("revoked membership cannot be reactivated")
        if membership.status == target:
            return membership
        membership.status = target
        now = _now()
        membership.activated_at = now if target == "active" else membership.activated_at
        membership.suspended_at = now if target == "suspended" else None
        membership.revoked_at = now if target == "revoked" else membership.revoked_at
        self._audit(
            tenant, f"membership.{target}", "membership", membership.public_id,
            details={"status": target},
        )
        self._commit()
        return membership

    def bootstrap(
        self,
        *,
        tenant_name: str,
        tenant_slug: str,
        store_name: str,
        store_slug: str,
        owner_identity: UserIdentity,
    ) -> tuple[Tenant, Store, TenantMembership]:
        """Atomically create a tenant, first store, and owner access."""
        if owner_identity.status != "active" or not owner_identity.email_verified:
            raise ValidationError("owner identity must be active and verified")
        if self.session.in_transaction():
            self.session.rollback()
        try:
            with self.session.begin():
                if self.session.scalar(
                    select(Tenant.id).where(func.lower(Tenant.slug) == normalize_slug(tenant_slug))
                ) is not None:
                    raise ConflictError("tenant slug already exists")
                tenant = Tenant(
                    name=normalize_name(tenant_name),
                    slug=normalize_slug(tenant_slug),
                    status="active",
                    created_by_identity_id=self.actor_identity_id or owner_identity.id,
                )
                self.session.add(tenant)
                self.session.flush()
                store = Store(
                    tenant=tenant,
                    name=normalize_name(store_name),
                    slug=normalize_slug(store_slug),
                    status="active",
                    subdomain=normalize_subdomain(tenant.slug),
                )
                self.session.add(store)
                self.session.flush()
                owner_role = self.session.get(AuthRole, "tenant_owner")
                if owner_role is None:
                    raise ValidationError("required authorization seeds are missing")
                membership = TenantMembership(
                    user_id=owner_identity.id,
                    tenant_id=tenant.id,
                    principal_type=PrincipalType.USER.value,
                    principal_id=str(owner_identity.id),
                    status="active",
                    all_store_access=True,
                    activated_at=_now(),
                )
                self.session.add(membership)
                self.session.flush()
                self.session.add(
                    AuthTenantRoleAssignment(
                        membership_id=membership.id,
                        role_code="tenant_owner",
                        status="active",
                    )
                )
                self.session.add(
                    StoreAccessAssignment(
                        membership_id=membership.id,
                        store_id=store.id,
                        status="active",
                        created_by_identity_id=self.actor_identity_id or owner_identity.id,
                    )
                )
                self._audit(tenant, "tenant.bootstrap", "tenant", tenant.public_id, details={"initial_store_public_id": store.public_id})
                self._audit(tenant, "store.created", "store", store.public_id, store=store)
                self._audit(tenant, "membership.created", "membership", membership.public_id, details={"role_codes": ["tenant_owner"], "all_store_access": True})
            return tenant, store, membership
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("tenant bootstrap conflicts with existing data") from exc
