from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authz.context import PermissionRequirement
from app.authz.exceptions import PermissionDeniedError
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.models import Store, StoreAccessAssignment, Tenant, TenantMembership
from app.tenant_management.domain import AccessDeniedError, ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class TenantStoreContext:
    tenant_id: int
    tenant_public_id: str
    tenant_status: str
    membership_id: int | None
    store_id: int | None = None
    store_public_id: str | None = None
    store_status: str | None = None
    platform_access: bool = False


def _platform_allowed(session: Session, principal: AuthenticatedPrincipal, permission: str) -> bool:
    return AuthorizationService(session).check(
        principal.as_authorization_principal(),
        PermissionRequirement(permission),
    ).allowed


def resolve_authorized_context(
    session: Session,
    principal: AuthenticatedPrincipal,
    *,
    tenant_public_id: str,
    store_public_id: str | None = None,
    tenant_permission: str = PermissionCode.TENANT_SETTINGS_READ,
    store_permission: str = PermissionCode.STORE_READ,
    platform_permission: str = PermissionCode.TENANT_READ,
    operational: bool = True,
) -> TenantStoreContext:
    tenant = session.scalar(select(Tenant).where(Tenant.public_id == tenant_public_id))
    if tenant is None or tenant.deleted_at is not None:
        raise ResourceNotFoundError("resource not found")
    platform = _platform_allowed(session, principal, platform_permission)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == principal.user_id,
            TenantMembership.principal_id == str(principal.user_id),
        )
    )
    if not platform:
        if membership is None or membership.status != "active":
            raise ResourceNotFoundError("resource not found")
        try:
            required_permission = store_permission if store_public_id is not None else tenant_permission
            AuthorizationService(session).require(
                principal.as_authorization_principal(tenant.id),
                required_permission,
                tenant_id=tenant.id,
            )
        except PermissionDeniedError as exc:
            raise ResourceNotFoundError("resource not found") from exc
    if operational and tenant.status != "active":
        raise AccessDeniedError("tenant is not active")
    store = None
    if store_public_id is not None:
        store = session.scalar(
            select(Store).where(
                Store.public_id == store_public_id,
                Store.tenant_id == tenant.id,
                Store.deleted_at.is_(None),
            )
        )
        if store is None:
            raise ResourceNotFoundError("resource not found")
        if not platform:
            assert membership is not None
            permitted = membership.all_store_access or session.scalar(
                select(StoreAccessAssignment.id).where(
                    StoreAccessAssignment.membership_id == membership.id,
                    StoreAccessAssignment.store_id == store.id,
                    StoreAccessAssignment.status == "active",
                )
            ) is not None
            if not permitted:
                raise ResourceNotFoundError("resource not found")
            try:
                AuthorizationService(session).require(
                    principal.as_authorization_principal(tenant.id),
                    store_permission,
                    tenant_id=tenant.id,
                )
            except PermissionDeniedError as exc:
                raise ResourceNotFoundError("resource not found") from exc
        if operational and store.status != "active":
            raise AccessDeniedError("store is not active")
    return TenantStoreContext(
        tenant_id=tenant.id,
        tenant_public_id=tenant.public_id,
        tenant_status=tenant.status,
        membership_id=membership.id if membership else None,
        store_id=store.id if store else None,
        store_public_id=store.public_id if store else None,
        store_status=store.status if store else None,
        platform_access=platform,
    )


def store_by_domain(session: Session, hostname: str) -> Store | None:
    normalized = hostname.strip().lower().rstrip(".")
    return session.scalar(
        select(Store).where(
            or_(Store.subdomain == normalized, Store.custom_domain == normalized),
            Store.status == "active",
            Store.deleted_at.is_(None),
        )
    )
