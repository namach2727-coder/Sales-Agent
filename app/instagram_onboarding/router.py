"""Customer-facing official Instagram onboarding routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_onboarding.provider import (
    InstagramOAuthError,
    InstagramOAuthProvider,
    MetaInstagramOAuthClient,
)
from app.instagram_onboarding.schemas import (
    InstagramAccountRead,
    InstagramCallbackResponse,
    InstagramConnectResponse,
    InstagramStatusResponse,
)
from app.instagram_onboarding.service import (
    InstagramOnboardingConflict,
    InstagramOnboardingError,
    InstagramOnboardingForbidden,
    InstagramOnboardingInvalidState,
    InstagramOnboardingService,
)


router = APIRouter(prefix="/api/v1/integrations/instagram", tags=["instagram-onboarding"])


def get_instagram_oauth_provider(
    settings: Settings = Depends(get_settings),
) -> InstagramOAuthProvider:
    return MetaInstagramOAuthClient(settings)


def _raise(error: Exception) -> None:
    if isinstance(error, InstagramOnboardingForbidden):
        status_code = 403
    elif isinstance(error, InstagramOnboardingInvalidState):
        status_code = 400
    elif isinstance(error, InstagramOnboardingConflict):
        status_code = 409
    elif isinstance(error, InstagramOAuthError):
        status_code = 502
    else:
        status_code = 422
    code = getattr(error, "code", "instagram_provider_error")
    message = "Instagram authorization failed" if isinstance(error, InstagramOAuthError) else str(error)
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _account(item) -> InstagramAccountRead:
    return InstagramAccountRead(
        connection_public_id=item.public_id,
        instagram_username=item.instagram_username,
        status=item.status,
        token_configured=item.encrypted_access_token is not None,
        connected_at=item.connected_at,
    )


@router.post("/connect", response_model=InstagramConnectResponse)
def connect(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: InstagramOAuthProvider = Depends(get_instagram_oauth_provider),
) -> InstagramConnectResponse:
    try:
        authorization_url, expires_at = InstagramOnboardingService(db, settings).begin(principal, provider)
        return InstagramConnectResponse(authorization_url=authorization_url, expires_at=expires_at)
    except (InstagramOnboardingError, InstagramOAuthError) as exc:
        _raise(exc)


@router.get("/callback", response_model=InstagramCallbackResponse)
def callback(
    code: str = Query(min_length=1, max_length=4096),
    state: str = Query(min_length=1, max_length=512),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: InstagramOAuthProvider = Depends(get_instagram_oauth_provider),
) -> InstagramCallbackResponse:
    try:
        connection, tenant, store = InstagramOnboardingService(db, settings).complete(
            state=state, code=code, provider=provider
        )
        return InstagramCallbackResponse(
            connection_public_id=connection.public_id,
            tenant_public_id=tenant.public_id,
            store_public_id=store.public_id,
            instagram_username=connection.instagram_username,
            status=connection.status,
        )
    except (InstagramOnboardingError, InstagramOAuthError) as exc:
        _raise(exc)


@router.get("/status", response_model=InstagramStatusResponse)
def status(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> InstagramStatusResponse:
    try:
        _tenant, _store, limit, accounts = InstagramOnboardingService(db, settings).status(principal)
        return InstagramStatusResponse(
            entitled=limit > 0,
            account_limit=limit,
            connected_accounts=len(accounts),
            accounts=[_account(item) for item in accounts],
        )
    except InstagramOnboardingError as exc:
        _raise(exc)


@router.get("/accounts", response_model=list[InstagramAccountRead])
def accounts(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[InstagramAccountRead]:
    try:
        _tenant, _store, _limit, items = InstagramOnboardingService(db, settings).status(principal)
        return [_account(item) for item in items]
    except InstagramOnboardingError as exc:
        _raise(exc)
