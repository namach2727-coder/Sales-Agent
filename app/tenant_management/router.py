from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal, require_platform_permission
from app.authz.context import PermissionRequirement
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.database import get_db
from app.models import (
    AuthTenantRoleAssignment,
    Store,
    StoreAccessAssignment,
    Tenant,
    TenantMembership,
    UserIdentity,
)
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import (
    AccessDeniedError,
    ConflictError,
    InvalidTransitionError,
    ResourceNotFoundError,
    TenantManagementError,
    ValidationError,
)
from app.tenant_management.schemas import (
    MembershipCreate,
    MembershipRead,
    MembershipStatusUpdate,
    StoreCreate,
    StorePage,
    StoreRead,
    StoreUpdate,
    TenantBootstrap,
    TenantCreate,
    TenantPage,
    TenantRead,
    TenantUpdate,
)
from app.tenant_management.service import TenantStoreService


router = APIRouter(prefix="/api/v1", tags=["tenant-store-management"])


def _raise(error: TenantManagementError) -> None:
    if isinstance(error, ValidationError):
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": str(error)})
    if isinstance(error, ConflictError):
        raise HTTPException(status_code=409, detail={"code": "conflict", "message": str(error)})
    if isinstance(error, InvalidTransitionError):
        raise HTTPException(status_code=409, detail={"code": "invalid_transition", "message": str(error)})
    if isinstance(error, AccessDeniedError):
        raise HTTPException(status_code=403, detail={"code": "inactive_scope", "message": str(error)})
    raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resource not found"})


def _platform_allowed(db: Session, principal: AuthenticatedPrincipal, code: str) -> bool:
    return AuthorizationService(db).check(
        principal.as_authorization_principal(), PermissionRequirement(code)
    ).allowed


def _tenant(db: Session, public_id: str) -> Tenant:
    item = db.scalar(select(Tenant).where(Tenant.public_id == public_id, Tenant.deleted_at.is_(None)))
    if item is None:
        raise ResourceNotFoundError("resource not found")
    return item


def _store(db: Session, tenant_id: int, public_id: str) -> Store:
    item = db.scalar(
        select(Store).where(
            Store.public_id == public_id,
            Store.tenant_id == tenant_id,
            Store.deleted_at.is_(None),
        )
    )
    if item is None:
        raise ResourceNotFoundError("resource not found")
    return item


@router.post(
    "/tenants",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an empty tenant boundary",
)
def create_tenant(
    payload: TenantCreate,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.TENANT_CREATE)),
    db: Session = Depends(get_db),
) -> Tenant:
    try:
        return TenantStoreService(db, actor_identity_id=principal.user_id).create_tenant(**payload.model_dump())
    except TenantManagementError as exc:
        _raise(exc)


@router.post(
    "/tenants/bootstrap",
    status_code=status.HTTP_201_CREATED,
    summary="Atomically create a tenant, first store and owner membership",
)
def bootstrap_tenant(
    payload: TenantBootstrap,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.TENANT_PROVISION)),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    owner = db.scalar(
        select(UserIdentity).where(UserIdentity.normalized_email == payload.owner_email.strip().casefold())
    )
    if owner is None:
        raise HTTPException(status_code=422, detail={"code": "owner_identity_invalid", "message": "Owner identity must already exist"})
    try:
        tenant, store, membership = TenantStoreService(
            db, actor_identity_id=principal.user_id
        ).bootstrap(owner_identity=owner, **payload.model_dump(exclude={"owner_email"}))
        return {
            "tenant": TenantRead.model_validate(tenant),
            "store": StoreRead.model_validate(store),
            "membership_public_id": membership.public_id,
        }
    except TenantManagementError as exc:
        _raise(exc)


@router.get("/tenants", response_model=TenantPage, summary="List only authorized tenants")
def list_tenants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(active|suspended|archived)$"),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = select(Tenant).where(Tenant.deleted_at.is_(None))
    if not _platform_allowed(db, principal, PermissionCode.TENANT_READ):
        query = query.join(TenantMembership).where(
            TenantMembership.user_id == principal.user_id,
            TenantMembership.status == "active",
        )
    if status_filter:
        query = query.where(Tenant.status == status_filter)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(or_(func.lower(Tenant.name).like(pattern), Tenant.slug.like(pattern)))
    query = query.distinct()
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Tenant.id).offset((page - 1) * page_size).limit(page_size)).all())
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/tenants/{tenant_public_id}", response_model=TenantRead)
def read_tenant(
    tenant_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> Tenant:
    try:
        resolve_authorized_context(db, principal, tenant_public_id=tenant_public_id, operational=False)
        return _tenant(db, tenant_public_id)
    except TenantManagementError as exc:
        _raise(exc)


@router.patch("/tenants/{tenant_public_id}", response_model=TenantRead)
def update_tenant(
    tenant_public_id: str,
    payload: TenantUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> Tenant:
    try:
        resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.TENANT_SETTINGS_UPDATE,
            platform_permission=PermissionCode.TENANT_UPDATE,
            operational=False,
        )
        return TenantStoreService(db, actor_identity_id=principal.user_id).update_tenant(
            _tenant(db, tenant_public_id), **payload.model_dump(exclude_unset=True)
        )
    except TenantManagementError as exc:
        _raise(exc)


def _tenant_transition(
    tenant_public_id: str,
    target: str,
    principal: AuthenticatedPrincipal,
    db: Session,
) -> Tenant:
    permission = PermissionCode.TENANT_ARCHIVE if target == "archived" else PermissionCode.TENANT_SUSPEND
    try:
        resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.TENANT_SETTINGS_UPDATE,
            platform_permission=permission,
            operational=False,
        )
        return TenantStoreService(db, actor_identity_id=principal.user_id).transition_tenant(
            _tenant(db, tenant_public_id), target
        )
    except TenantManagementError as exc:
        _raise(exc)


@router.post("/tenants/{tenant_public_id}/suspend", response_model=TenantRead)
def suspend_tenant(tenant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tenant:
    return _tenant_transition(tenant_public_id, "suspended", principal, db)


@router.post("/tenants/{tenant_public_id}/reactivate", response_model=TenantRead)
def reactivate_tenant(tenant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tenant:
    return _tenant_transition(tenant_public_id, "active", principal, db)


@router.post("/tenants/{tenant_public_id}/archive", response_model=TenantRead)
def archive_tenant(tenant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tenant:
    return _tenant_transition(tenant_public_id, "archived", principal, db)


@router.post("/tenants/{tenant_public_id}/stores", response_model=StoreRead, status_code=201)
def create_store(
    tenant_public_id: str,
    payload: StoreCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> Store:
    try:
        resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.STORE_CREATE,
            platform_permission=PermissionCode.TENANT_UPDATE,
        )
        return TenantStoreService(db, actor_identity_id=principal.user_id).create_store(
            _tenant(db, tenant_public_id), **payload.model_dump()
        )
    except TenantManagementError as exc:
        _raise(exc)


@router.get("/tenants/{tenant_public_id}/stores", response_model=StorePage)
def list_stores(
    tenant_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(active|suspended|archived)$"),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.STORE_READ,
            operational=False,
        )
        query = select(Store).where(Store.tenant_id == context.tenant_id, Store.deleted_at.is_(None))
        if not context.platform_access:
            membership = db.get(TenantMembership, context.membership_id)
            if membership is None:
                raise ResourceNotFoundError("resource not found")
            if not membership.all_store_access:
                query = query.join(StoreAccessAssignment).where(
                    StoreAccessAssignment.membership_id == membership.id,
                    StoreAccessAssignment.status == "active",
                )
        if status_filter:
            query = query.where(Store.status == status_filter)
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(or_(func.lower(Store.name).like(pattern), Store.slug.like(pattern)))
        query = query.distinct()
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(db.scalars(query.order_by(Store.id).offset((page - 1) * page_size).limit(page_size)).all())
        return {"items": items, "page": page, "page_size": page_size, "total": total}
    except TenantManagementError as exc:
        _raise(exc)


@router.get("/tenants/{tenant_public_id}/stores/{store_public_id}", response_model=StoreRead)
def read_store(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Store:
    try:
        context = resolve_authorized_context(db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id, operational=False)
        return _store(db, context.tenant_id, store_public_id)
    except TenantManagementError as exc:
        _raise(exc)


@router.patch("/tenants/{tenant_public_id}/stores/{store_public_id}", response_model=StoreRead)
def update_store(tenant_public_id: str, store_public_id: str, payload: StoreUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Store:
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id,
            store_permission=PermissionCode.STORE_UPDATE,
            platform_permission=PermissionCode.TENANT_UPDATE,
            operational=False,
        )
        values = payload.model_dump(exclude_unset=True)
        domains_supplied = bool({"subdomain", "custom_domain"} & payload.model_fields_set)
        return TenantStoreService(db, actor_identity_id=principal.user_id).update_store(
            _tenant(db, tenant_public_id), _store(db, context.tenant_id, store_public_id),
            domains_supplied=domains_supplied, **values,
        )
    except TenantManagementError as exc:
        _raise(exc)


def _store_transition(tenant_public_id: str, store_public_id: str, target: str, principal: AuthenticatedPrincipal, db: Session) -> Store:
    store_permission = PermissionCode.STORE_ARCHIVE if target == "archived" else PermissionCode.STORE_SUSPEND
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id,
            store_permission=store_permission, platform_permission=PermissionCode.TENANT_UPDATE,
            operational=False,
        )
        tenant = _tenant(db, tenant_public_id)
        return TenantStoreService(db, actor_identity_id=principal.user_id).transition_store(
            tenant, _store(db, context.tenant_id, store_public_id), target
        )
    except TenantManagementError as exc:
        _raise(exc)


@router.post("/tenants/{tenant_public_id}/stores/{store_public_id}/suspend", response_model=StoreRead)
def suspend_store(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Store:
    return _store_transition(tenant_public_id, store_public_id, "suspended", principal, db)


@router.post("/tenants/{tenant_public_id}/stores/{store_public_id}/reactivate", response_model=StoreRead)
def reactivate_store(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Store:
    return _store_transition(tenant_public_id, store_public_id, "active", principal, db)


@router.post("/tenants/{tenant_public_id}/stores/{store_public_id}/archive", response_model=StoreRead)
def archive_store(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Store:
    return _store_transition(tenant_public_id, store_public_id, "archived", principal, db)


@router.post("/tenants/{tenant_public_id}/memberships", response_model=MembershipRead, status_code=201)
def add_membership(tenant_public_id: str, payload: MembershipCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> MembershipRead:
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.TENANT_MEMBERS_MANAGE_V2,
            platform_permission=PermissionCode.TENANT_ACCESS_MANAGE,
            operational=False,
        )
        tenant = _tenant(db, tenant_public_id)
        identity = db.scalar(select(UserIdentity).where(UserIdentity.normalized_email == payload.identity_email))
        if identity is None:
            raise ValidationError("identity does not exist")
        stores = tuple(
            db.scalars(
                select(Store).where(
                    Store.tenant_id == tenant.id,
                    Store.public_id.in_(payload.store_public_ids),
                )
            ).all()
        )
        if len(stores) != len(set(payload.store_public_ids)):
            raise ResourceNotFoundError("resource not found")
        membership = TenantStoreService(db, actor_identity_id=principal.user_id).add_membership(
            tenant, identity,
            role_codes=tuple(payload.role_codes),
            all_store_access=payload.all_store_access,
            stores=stores,
            status=payload.status,
        )
        return _membership_read(db, membership, identity)
    except TenantManagementError as exc:
        _raise(exc)


@router.get("/tenants/{tenant_public_id}/memberships", response_model=list[MembershipRead])
def list_memberships(tenant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> list[MembershipRead]:
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.TENANT_MEMBERS_READ,
            platform_permission=PermissionCode.TENANT_ACCESS_MANAGE,
            operational=False,
        )
        memberships = list(db.scalars(select(TenantMembership).where(TenantMembership.tenant_id == context.tenant_id).order_by(TenantMembership.id)).all())
        identities = {item.id: item for item in db.scalars(select(UserIdentity).where(UserIdentity.id.in_([m.user_id for m in memberships if m.user_id is not None]))).all()}
        return [_membership_read(db, item, identities[item.user_id]) for item in memberships if item.user_id in identities]
    except TenantManagementError as exc:
        _raise(exc)


@router.patch("/tenants/{tenant_public_id}/memberships/{membership_public_id}", response_model=MembershipRead)
def update_membership_status(tenant_public_id: str, membership_public_id: str, payload: MembershipStatusUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> MembershipRead:
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id,
            tenant_permission=PermissionCode.TENANT_MEMBERS_MANAGE_V2,
            platform_permission=PermissionCode.TENANT_ACCESS_MANAGE,
            operational=False,
        )
        membership = db.scalar(select(TenantMembership).where(TenantMembership.public_id == membership_public_id, TenantMembership.tenant_id == context.tenant_id))
        if membership is None or membership.user_id is None:
            raise ResourceNotFoundError("resource not found")
        membership = TenantStoreService(db, actor_identity_id=principal.user_id).transition_membership(_tenant(db, tenant_public_id), membership, payload.status)
        identity = db.get(UserIdentity, membership.user_id)
        assert identity is not None
        return _membership_read(db, membership, identity)
    except TenantManagementError as exc:
        _raise(exc)


def _membership_read(db: Session, membership: TenantMembership, identity: UserIdentity) -> MembershipRead:
    role_codes = list(db.scalars(select(AuthTenantRoleAssignment.role_code).where(AuthTenantRoleAssignment.membership_id == membership.id, AuthTenantRoleAssignment.status == "active")).all())
    store_public_ids = list(db.scalars(select(Store.public_id).join(StoreAccessAssignment, StoreAccessAssignment.store_id == Store.id).where(StoreAccessAssignment.membership_id == membership.id, StoreAccessAssignment.status == "active")).all())
    return MembershipRead(
        public_id=membership.public_id,
        display_name=identity.display_name,
        status=membership.status,
        all_store_access=membership.all_store_access,
        role_codes=sorted(role_codes),
        store_public_ids=sorted(store_public_ids),
    )
