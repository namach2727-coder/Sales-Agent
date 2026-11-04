"""Customer-facing Google Search Console connection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.config import Settings, get_settings
from app.database import get_db
from app.seo_service.provider import GoogleSearchConsoleClient, GoogleSeoProviderError
from app.seo_service.schemas import (
    SeoGoogleCallbackRead, SeoGoogleConnectRead, SeoGooglePropertyRead,
    SeoGoogleStatusRead, SeoSelectPropertyRequest,
)
from app.seo_service.service import (
    SeoConflict, SeoForbidden, SeoGoogleConnectionService, SeoInvalidState, SeoServiceError,
)

router = APIRouter(prefix="/api/v1/seo/google", tags=["seo-google"])


def get_google_seo_provider(settings: Settings = Depends(get_settings)):
    return GoogleSearchConsoleClient(settings)


def _raise(exc: Exception) -> None:
    if isinstance(exc, SeoForbidden):
        status = 403
    elif isinstance(exc, SeoInvalidState):
        status = 400
    elif isinstance(exc, SeoConflict):
        status = 409
    elif isinstance(exc, GoogleSeoProviderError):
        status = 502
    else:
        status = 422
    code = getattr(exc, "code", "seo_service_error")
    message = str(exc) if not isinstance(exc, GoogleSeoProviderError) else "Google authorization failed"
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


@router.post("/connect", response_model=SeoGoogleConnectRead)
def connect(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: GoogleSearchConsoleClient = Depends(get_google_seo_provider),
):
    try:
        url, expires = SeoGoogleConnectionService(db, settings).begin(principal, provider)
        return SeoGoogleConnectRead(authorization_url=url, expires_at=expires)
    except (SeoServiceError, GoogleSeoProviderError) as exc:
        _raise(exc)


@router.get("/callback", response_model=SeoGoogleCallbackRead)
def callback(
    code: str | None = Query(default=None, min_length=1, max_length=4096),
    state: str = Query(min_length=1, max_length=512),
    error: str | None = Query(default=None, max_length=128),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: GoogleSearchConsoleClient = Depends(get_google_seo_provider),
):
    if error:
        raise HTTPException(status_code=400, detail={"code": "google_authorization_denied", "message": "Google authorization was not completed"})
    if not code:
        raise HTTPException(status_code=400, detail={"code": "google_authorization_code_missing", "message": "Google did not return an authorization code"})
    try:
        connection, count = SeoGoogleConnectionService(db, settings).complete(state, code, provider, principal)
        return SeoGoogleCallbackRead(
            connected=connection.status == "active",
            google_email=connection.google_email,
            discovered_properties=count,
        )
    except (SeoServiceError, GoogleSeoProviderError) as exc:
        _raise(exc)


@router.get("/status", response_model=SeoGoogleStatusRead)
def status(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        connection, properties, selected = SeoGoogleConnectionService(db, settings).status(principal)
        return SeoGoogleStatusRead(
            connected=connection is not None and connection.status == "active",
            status=connection.status if connection else "not_connected",
            google_email=connection.google_email if connection else None,
            connected_at=connection.connected_at if connection else None,
            property_count=len(properties),
            selected_property=selected,
        )
    except SeoServiceError as exc:
        _raise(exc)


@router.post("/properties/refresh")
def refresh_properties(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: GoogleSearchConsoleClient = Depends(get_google_seo_provider),
):
    try:
        count = SeoGoogleConnectionService(db, settings).refresh_properties(principal, provider)
        return {"refreshed_properties": count}
    except (SeoServiceError, GoogleSeoProviderError) as exc:
        _raise(exc)


@router.get("/properties", response_model=list[SeoGooglePropertyRead])
def properties(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        _connection, items, _selected = SeoGoogleConnectionService(db, settings).status(principal)
        return [SeoGooglePropertyRead(
            public_id=item.public_id, property_uri=item.property_uri,
            permission_level=item.permission_level, is_selected=item.is_selected,
        ) for item in items]
    except SeoServiceError as exc:
        _raise(exc)


@router.post("/properties/select", response_model=SeoGooglePropertyRead)
def select_property(
    payload: SeoSelectPropertyRequest,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        item = SeoGoogleConnectionService(db, settings).select_property(principal, payload.property_public_id)
        return SeoGooglePropertyRead(
            public_id=item.public_id, property_uri=item.property_uri,
            permission_level=item.permission_level, is_selected=item.is_selected,
        )
    except SeoServiceError as exc:
        _raise(exc)


@router.delete("/connection", status_code=204)
def disconnect(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: GoogleSearchConsoleClient = Depends(get_google_seo_provider),
):
    try:
        SeoGoogleConnectionService(db, settings).disconnect(principal, provider)
    except (SeoServiceError, GoogleSeoProviderError) as exc:
        _raise(exc)
