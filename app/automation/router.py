from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.automation.schemas import AutomationStateRead, AutomationStateUpdate
from app.automation.service import (
    AutomationControlConflict,
    AutomationControlError,
    AutomationControlService,
)
from app.database import get_db
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


router = APIRouter(
    prefix="/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/automation",
    tags=["automation-control"],
)


def _service(
    tenant_public_id: str,
    store_public_id: str,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    mutation: bool,
) -> AutomationControlService:
    permission = PermissionCode.STORE_UPDATE if mutation else PermissionCode.STORE_READ
    try:
        context = resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            tenant_permission=permission,
            store_permission=permission,
            platform_permission=(
                PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ
            ),
            operational=False,
        )
    except TenantManagementError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        ) from exc
    assert context.store_id is not None
    return AutomationControlService(
        db,
        tenant_id=context.tenant_id,
        store_id=context.store_id,
        actor_identity_id=principal.user_id,
    )


def _read(store) -> AutomationStateRead:
    return AutomationStateRead(
        enabled=store.automation_enabled,
        revision=store.automation_revision,
        updated_at=store.updated_at,
    )


@router.get("", response_model=AutomationStateRead)
def read_automation_state(
    tenant_public_id: str,
    store_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> AutomationStateRead:
    return _read(_service(tenant_public_id, store_public_id, principal, db, mutation=False).read())


@router.patch("", response_model=AutomationStateRead)
def update_automation_state(
    tenant_public_id: str,
    store_public_id: str,
    payload: AutomationStateUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> AutomationStateRead:
    try:
        store = _service(
            tenant_public_id, store_public_id, principal, db, mutation=True
        ).update(**payload.model_dump())
    except AutomationControlConflict as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except AutomationControlError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        ) from exc
    return _read(store)
