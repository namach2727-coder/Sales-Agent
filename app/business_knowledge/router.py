"""Authenticated Store-scoped REST API for FOUNDATION-07."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.context import AuthorizationContext, PermissionRequirement
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.business_knowledge.domain import (
    BusinessKnowledgeConflictError,
    BusinessKnowledgeError,
    BusinessKnowledgeInvalidTransitionError,
    BusinessKnowledgeNotFoundError,
    BusinessKnowledgeStaleWriteError,
    BusinessKnowledgeStoreStateError,
    BusinessKnowledgeValidationError,
)
from app.business_knowledge.models import (
    BusinessFAQ,
    BusinessKnowledgeEntry,
    BusinessPolicy,
    BusinessProfile,
)
from app.business_knowledge.schemas import (
    BusinessFAQCreate,
    BusinessFAQPage,
    BusinessFAQRead,
    BusinessFAQUpdate,
    BusinessKnowledgeEntryCreate,
    BusinessKnowledgeEntryPage,
    BusinessKnowledgeEntryRead,
    BusinessKnowledgeEntryUpdate,
    BusinessPolicyCreate,
    BusinessPolicyPage,
    BusinessPolicyRead,
    BusinessPolicyUpdate,
    BusinessProfileCreate,
    BusinessProfileRead,
    BusinessProfileUpdate,
    EntryType,
    KnowledgeStatus,
    LifecycleTransition,
    PolicyType,
)
from app.business_knowledge.service import (
    BusinessKnowledgePermissionError,
    BusinessKnowledgeService,
)
from app.database import get_db
from app.tenant_management.context import (
    TenantStoreContext,
    resolve_authorized_context,
)
from app.tenant_management.domain import TenantManagementError


router = APIRouter(
    prefix=(
        "/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}"
        "/business-knowledge"
    ),
    tags=["business-profile-knowledge"],
)


def _raise(error: Exception) -> None:
    if isinstance(error, BusinessKnowledgeValidationError):
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, BusinessKnowledgeStaleWriteError):
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(
        error,
        (
            BusinessKnowledgeConflictError,
            BusinessKnowledgeInvalidTransitionError,
        ),
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, (BusinessKnowledgePermissionError, BusinessKnowledgeStoreStateError)):
        raise HTTPException(
            status_code=403,
            detail={"code": error.code, "message": "Permission denied"},
        )
    if isinstance(error, (BusinessKnowledgeNotFoundError, TenantManagementError)):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        )
    raise error


def _service(
    tenant_public_id: str,
    store_public_id: str,
    permission: str,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    mutation: bool,
) -> tuple[BusinessKnowledgeService, TenantStoreContext]:
    try:
        context = resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            tenant_permission=permission,
            store_permission=permission,
            platform_permission=(
                PermissionCode.TENANT_UPDATE
                if mutation
                else PermissionCode.TENANT_READ
            ),
            operational=False,
        )
    except TenantManagementError as exc:
        _raise(exc)
    assert context.store_id is not None and context.store_status is not None
    return (
        BusinessKnowledgeService(
            db,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            tenant_status=context.tenant_status,
            store_status=context.store_status,
            actor_identity_id=principal.user_id,
        ),
        context,
    )


def _publish_allowed(
    db: Session,
    principal: AuthenticatedPrincipal,
    context: TenantStoreContext,
) -> bool:
    if context.platform_access:
        return True
    return AuthorizationService(db).check(
        principal.as_authorization_principal(context.tenant_id),
        PermissionRequirement(PermissionCode.KNOWLEDGE_PUBLISH),
        AuthorizationContext(context.tenant_id),
    ).allowed


@router.post(
    "/profile",
    response_model=BusinessProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    tenant_public_id: str,
    store_public_id: str,
    payload: BusinessProfileCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessProfile:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.BUSINESS_PROFILE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.create_profile(**payload.model_dump())
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/profile", response_model=BusinessProfileRead)
def read_profile(
    tenant_public_id: str,
    store_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessProfile:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.BUSINESS_PROFILE_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_profile()
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.patch("/profile", response_model=BusinessProfileRead)
def update_profile(
    tenant_public_id: str,
    store_public_id: str,
    payload: BusinessProfileUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessProfile:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.BUSINESS_PROFILE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.update_profile(
            expected_revision=payload.expected_revision,
            changes=payload.model_dump(
                exclude_unset=True, exclude={"expected_revision"}
            ),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post("/profile/transitions", response_model=BusinessProfileRead)
def transition_profile(
    tenant_public_id: str,
    store_public_id: str,
    payload: LifecycleTransition,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessProfile:
    try:
        service, context = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.BUSINESS_PROFILE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.transition(
            BusinessProfile,
            None,
            expected_revision=payload.expected_revision,
            target_status=payload.target_status,
            publish_authorized=_publish_allowed(db, principal, context),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/policies",
    response_model=BusinessPolicyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_policy(
    tenant_public_id: str,
    store_public_id: str,
    payload: BusinessPolicyCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessPolicy:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.create_policy(**payload.model_dump())
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/policies", response_model=BusinessPolicyPage)
def list_policies(
    tenant_public_id: str,
    store_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: KnowledgeStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    policy_type: PolicyType | None = Query(default=None),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_policies(
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
            policy_type=policy_type,
        )
        return {"items": items, "page": page, "page_size": page_size, "total": total}
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/policies/{policy_public_id}", response_model=BusinessPolicyRead)
def read_policy(
    tenant_public_id: str,
    store_public_id: str,
    policy_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessPolicy:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_policy(policy_public_id)
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.patch("/policies/{policy_public_id}", response_model=BusinessPolicyRead)
def update_policy(
    tenant_public_id: str,
    store_public_id: str,
    policy_public_id: str,
    payload: BusinessPolicyUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessPolicy:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.update_policy(
            policy_public_id,
            expected_revision=payload.expected_revision,
            changes=payload.model_dump(
                exclude_unset=True, exclude={"expected_revision"}
            ),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/policies/{policy_public_id}/transitions",
    response_model=BusinessPolicyRead,
)
def transition_policy(
    tenant_public_id: str,
    store_public_id: str,
    policy_public_id: str,
    payload: LifecycleTransition,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessPolicy:
    try:
        service, context = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.transition(
            BusinessPolicy,
            policy_public_id,
            expected_revision=payload.expected_revision,
            target_status=payload.target_status,
            publish_authorized=_publish_allowed(db, principal, context),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/faqs",
    response_model=BusinessFAQRead,
    status_code=status.HTTP_201_CREATED,
)
def create_faq(
    tenant_public_id: str,
    store_public_id: str,
    payload: BusinessFAQCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessFAQ:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.create_faq(**payload.model_dump())
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/faqs", response_model=BusinessFAQPage)
def list_faqs(
    tenant_public_id: str,
    store_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: KnowledgeStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_faqs(
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
        return {"items": items, "page": page, "page_size": page_size, "total": total}
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/faqs/{faq_public_id}", response_model=BusinessFAQRead)
def read_faq(
    tenant_public_id: str,
    store_public_id: str,
    faq_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessFAQ:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_faq(faq_public_id)
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.patch("/faqs/{faq_public_id}", response_model=BusinessFAQRead)
def update_faq(
    tenant_public_id: str,
    store_public_id: str,
    faq_public_id: str,
    payload: BusinessFAQUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessFAQ:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.update_faq(
            faq_public_id,
            expected_revision=payload.expected_revision,
            changes=payload.model_dump(
                exclude_unset=True, exclude={"expected_revision"}
            ),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/faqs/{faq_public_id}/transitions",
    response_model=BusinessFAQRead,
)
def transition_faq(
    tenant_public_id: str,
    store_public_id: str,
    faq_public_id: str,
    payload: LifecycleTransition,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessFAQ:
    try:
        service, context = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.transition(
            BusinessFAQ,
            faq_public_id,
            expected_revision=payload.expected_revision,
            target_status=payload.target_status,
            publish_authorized=_publish_allowed(db, principal, context),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/entries",
    response_model=BusinessKnowledgeEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entry(
    tenant_public_id: str,
    store_public_id: str,
    payload: BusinessKnowledgeEntryCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeEntry:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.create_entry(**payload.model_dump())
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/entries", response_model=BusinessKnowledgeEntryPage)
def list_entries(
    tenant_public_id: str,
    store_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status_filter: KnowledgeStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    entry_type: EntryType | None = Query(default=None),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_entries(
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
            entry_type=entry_type,
        )
        return {"items": items, "page": page, "page_size": page_size, "total": total}
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.get("/entries/{entry_public_id}", response_model=BusinessKnowledgeEntryRead)
def read_entry(
    tenant_public_id: str,
    store_public_id: str,
    entry_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeEntry:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_entry(entry_public_id)
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.patch("/entries/{entry_public_id}", response_model=BusinessKnowledgeEntryRead)
def update_entry(
    tenant_public_id: str,
    store_public_id: str,
    entry_public_id: str,
    payload: BusinessKnowledgeEntryUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeEntry:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.update_entry(
            entry_public_id,
            expected_revision=payload.expected_revision,
            changes=payload.model_dump(
                exclude_unset=True, exclude={"expected_revision"}
            ),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)


@router.post(
    "/entries/{entry_public_id}/transitions",
    response_model=BusinessKnowledgeEntryRead,
)
def transition_entry(
    tenant_public_id: str,
    store_public_id: str,
    entry_public_id: str,
    payload: LifecycleTransition,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeEntry:
    try:
        service, context = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.KNOWLEDGE_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return service.transition(
            BusinessKnowledgeEntry,
            entry_public_id,
            expected_revision=payload.expected_revision,
            target_status=payload.target_status,
            publish_authorized=_publish_allowed(db, principal, context),
        )
    except BusinessKnowledgeError as exc:
        _raise(exc)
