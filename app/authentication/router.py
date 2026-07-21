"""Explicit login, logout, current identity, and session endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import (
    build_authentication_service,
    extract_session_token,
    require_authenticated_principal,
)
from app.authentication.exceptions import AuthenticationError, InvalidCredentials
from app.authentication.schemas import (
    LoginInput,
    LoginResponse,
    MembershipRead,
    OperationResponse,
    PrincipalRead,
    SessionRead,
)
from app.config import Settings, get_settings
from app.database import get_db


router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger("sales_assistant.authentication")


def _principal_read(principal: AuthenticatedPrincipal) -> PrincipalRead:
    return PrincipalRead(
        user_id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
        session_id=principal.session_id,
        authenticated_at=principal.authenticated_at,
        tenant_memberships=[
            MembershipRead(
                tenant_id=item.tenant_id,
                tenant_slug=item.tenant_slug,
                status=item.status,
            )
            for item in principal.tenant_memberships
            if item.status == "active"
        ],
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"description": "Invalid credentials"}},
)
def login(
    payload: LoginInput,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    if not settings.authentication_enabled:
        raise HTTPException(
            status_code=503,
            detail={"code": "authentication_unavailable", "message": "Authentication unavailable"},
        )
    try:
        credential = build_authentication_service(db, settings).authenticate_password(
            email=payload.email,
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthenticationError as exc:
        logger.warning(
            "authentication login denied",
            extra={"event_code": "auth.login_denied"},
        )
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "Invalid credentials"},
        ) from exc
    response.set_cookie(
        key=settings.session_cookie_name,
        value=credential.token,
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return LoginResponse(
        access_token=credential.token,
        expires_at=credential.expires_at,
        principal=_principal_read(credential.principal),
    )


@router.post("/logout", response_model=OperationResponse)
def logout(
    request: Request,
    response: Response,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OperationResponse:
    build_authentication_service(db, settings).revoke_session(
        session_id=principal.session_id,
        actor_user_id=principal.user_id,
    )
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )
    return OperationResponse(status="revoked")


@router.get("/me", response_model=PrincipalRead)
def me(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> PrincipalRead:
    return _principal_read(principal)


@router.get("/sessions", response_model=list[SessionRead])
def sessions(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[SessionRead]:
    rows = build_authentication_service(db, settings).list_sessions(principal.user_id)
    return [SessionRead.model_validate(item) for item in rows]


@router.delete("/sessions/{session_id}/revoke", response_model=OperationResponse)
def revoke_session(
    session_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OperationResponse:
    try:
        changed = build_authentication_service(db, settings).revoke_session(
            session_id=session_id,
            actor_user_id=principal.user_id,
        )
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        ) from exc
    if not changed:
        # Constant result for a missing or already-revoked own session.
        return OperationResponse(status="unchanged")
    return OperationResponse(status="revoked")
