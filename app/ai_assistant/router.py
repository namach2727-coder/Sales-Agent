from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_assistant.schemas import AISettingsRead, AISettingsUpdate, AIUsageRead
from app.ai_assistant.service import AIAssistantConflict, AIAssistantError, AIAssistantService
from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.database import get_db
from app.module_catalog import has_capability
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


router = APIRouter(prefix="/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/ai-assistant", tags=["ai-assistant"])


def _service(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal, db: Session, *, mutation: bool) -> AIAssistantService:
    permission = PermissionCode.STORE_UPDATE if mutation else PermissionCode.STORE_READ
    try:
        context = resolve_authorized_context(db, principal, tenant_public_id=tenant_public_id, store_public_id=store_public_id, tenant_permission=permission, store_permission=permission, platform_permission=PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ, operational=False)
    except TenantManagementError as exc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resource not found"}) from exc
    assert context.store_id is not None
    if not context.platform_access and not has_capability(db, tenant_id=context.tenant_id, store_id=context.store_id, capability_code="ai_assistant"):
        raise HTTPException(status_code=403, detail={"code": "ai_assistant_unavailable", "message": "AI Assistant subscription required"})
    return AIAssistantService(db, tenant_id=context.tenant_id, store_id=context.store_id, actor_identity_id=principal.user_id)


def _read(store) -> AISettingsRead:
    return AISettingsRead(enabled=store.ai_enabled, revision=store.ai_revision, updated_at=store.updated_at)


@router.get("/settings", response_model=AISettingsRead)
def read_settings(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AISettingsRead:
    return _read(_service(tenant_public_id, store_public_id, principal, db, mutation=False).read())


@router.patch("/settings", response_model=AISettingsRead)
def update_settings(tenant_public_id: str, store_public_id: str, payload: AISettingsUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AISettingsRead:
    try:
        return _read(_service(tenant_public_id, store_public_id, principal, db, mutation=True).update(**payload.model_dump()))
    except AIAssistantConflict as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)}) from exc
    except AIAssistantError as exc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resource not found"}) from exc


@router.get("/usage", response_model=AIUsageRead)
def read_usage(tenant_public_id: str, store_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AIUsageRead:
    usage = _service(tenant_public_id, store_public_id, principal, db, mutation=False).usage()
    return AIUsageRead(
        request_count=usage.request_count,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        request_limit=usage.request_limit,
        token_limit=usage.token_limit,
        remaining_requests=None if usage.request_limit is None else max(0, usage.request_limit - usage.request_count),
        remaining_tokens=None if usage.token_limit is None else max(0, usage.token_limit - usage.total_tokens),
        period_start=usage.period_start,
        period_end=usage.period_end,
    )
