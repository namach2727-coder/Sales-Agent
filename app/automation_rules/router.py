from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.automation_rules.schemas import AutomationRuleCreate, AutomationRulePage, AutomationRuleRead, AutomationRuleUpdate
from app.automation_rules.service import (
    AutomationRuleConflict, AutomationRuleError, AutomationRuleForbidden,
    AutomationRuleLimitReached, AutomationRuleNotFound, AutomationRuleService,
    AutomationRuleValidation,
)
from app.database import get_db
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


router = APIRouter(
    prefix="/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/automation-rules",
    tags=["automation-rules"],
)


def _service(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal, db: Session, *, mutation: bool) -> AutomationRuleService:
    permission = PermissionCode.STORE_UPDATE if mutation else PermissionCode.STORE_READ
    try:
        context = resolve_authorized_context(
            db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id,
            tenant_permission=permission, store_permission=permission,
            platform_permission=PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ,
            operational=False,
        )
    except TenantManagementError as exc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resource not found"}) from exc
    assert context.store_id is not None
    return AutomationRuleService(db, tenant_id=context.tenant_id, store_id=context.store_id, actor_identity_id=principal.user_id)


def _raise(exc: AutomationRuleError) -> None:
    if isinstance(exc, AutomationRuleNotFound):
        code = 404
    elif isinstance(exc, AutomationRuleConflict):
        code = 409
    elif isinstance(exc, AutomationRuleLimitReached):
        code = 409
    elif isinstance(exc, AutomationRuleForbidden):
        code = 403
    elif isinstance(exc, AutomationRuleValidation):
        code = 422
    else:
        code = 400
    raise HTTPException(status_code=code, detail={"code": exc.code, "message": str(exc)}) from exc


@router.get("", response_model=AutomationRulePage)
def list_rules(tenant_public_id: str, store_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)):
    try:
        items, total = _service(tenant_public_id, store_public_id, principal, db, mutation=False).list(page=page, page_size=page_size)
    except AutomationRuleError as exc:
        _raise(exc)
    return AutomationRulePage(page=page, page_size=page_size, total=total, items=items)


@router.post("", response_model=AutomationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(tenant_public_id: str, store_public_id: str, payload: AutomationRuleCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)):
    try:
        return _service(tenant_public_id, store_public_id, principal, db, mutation=True).create(**payload.model_dump())
    except AutomationRuleError as exc:
        _raise(exc)


@router.get("/{rule_public_id}", response_model=AutomationRuleRead)
def get_rule(tenant_public_id: str, store_public_id: str, rule_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)):
    try:
        return _service(tenant_public_id, store_public_id, principal, db, mutation=False).get(rule_public_id)
    except AutomationRuleError as exc:
        _raise(exc)


@router.patch("/{rule_public_id}", response_model=AutomationRuleRead)
def update_rule(tenant_public_id: str, store_public_id: str, rule_public_id: str, payload: AutomationRuleUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)):
    try:
        return _service(tenant_public_id, store_public_id, principal, db, mutation=True).update(rule_public_id, **payload.model_dump())
    except AutomationRuleError as exc:
        _raise(exc)


@router.delete("/{rule_public_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(tenant_public_id: str, store_public_id: str, rule_public_id: str, expected_revision: int = Query(..., ge=1), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)):
    try:
        _service(tenant_public_id, store_public_id, principal, db, mutation=True).delete(rule_public_id, expected_revision=expected_revision)
    except AutomationRuleError as exc:
        _raise(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
