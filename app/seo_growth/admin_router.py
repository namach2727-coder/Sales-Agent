"""System-admin-only SEO pilot access, without paid plan or token operations."""
from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.config import Settings, get_settings
from app.database import get_db
from app.seo_growth.pilot_admin import SeoPilotAdminService
from app.seo_growth.router import fail
from app.seo_growth.security import SeoError, frontend_origin

router = APIRouter(prefix="/api/v1/admin/seo/pilot-grants", tags=["seo-pilot-admin"])


class PilotGrantWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tenant_public_id: str = Field(min_length=36, max_length=36)
    store_public_id: str = Field(min_length=36, max_length=36)
    enabled: bool
    expected_revision: int = Field(ge=0)
    duration_days: int = Field(ge=1, le=30)
    max_sites: int = Field(ge=1, le=20)
    max_connections: int = Field(ge=1, le=10)


@router.get("")
def read_grant(response: Response, tenant_public_id: str = Query(min_length=36, max_length=36),
               store_public_id: str = Query(min_length=36, max_length=36),
               db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
               principal: AuthenticatedPrincipal = Depends(require_authenticated_principal)):
    response.headers["Cache-Control"] = "no-store"
    try:
        return SeoPilotAdminService(db, settings, principal, tenant_public_id, store_public_id).read()
    except SeoError as exc:
        fail(exc)


@router.post("")
def write_grant(payload: PilotGrantWrite, request: Request, response: Response,
                db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
                principal: AuthenticatedPrincipal = Depends(require_authenticated_principal)):
    response.headers["Cache-Control"] = "no-store"
    try:
        # Permission is checked before scope mutation or any external call.
        service = SeoPilotAdminService(db, settings, principal, payload.tenant_public_id, payload.store_public_id)
        if request.headers.get("x-csrf-token") != "seo" or request.headers.get("origin") != frontend_origin(settings, require_callback=False):
            raise SeoError("seo_csrf_invalid", 403)
        return service.write(**payload.model_dump(exclude={"tenant_public_id", "store_public_id"}))
    except SeoError as exc:
        fail(exc)
