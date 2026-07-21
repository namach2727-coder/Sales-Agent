"""FastAPI token extraction, session verification, and RBAC composition."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.exceptions import AuthenticationError
from app.authentication.passwords import PasswordService
from app.authentication.service import AuthenticationService
from app.authz.exceptions import PermissionDeniedError
from app.authz.service import AuthorizationService
from app.config import Settings, get_settings
from app.database import get_db


def extract_session_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization:
        scheme, separator, value = authorization.partition(" ")
        if scheme.casefold() != "bearer" or not separator or not value.strip():
            raise HTTPException(
                status_code=401,
                detail={"code": "authentication_required", "message": "Authentication required"},
            )
        return value.strip()
    return request.cookies.get(settings.session_cookie_name)


def build_authentication_service(
    db: Session, settings: Settings
) -> AuthenticationService:
    return AuthenticationService(
        db,
        password_service=PasswordService(
            minimum_length=settings.password_min_length,
            maximum_length=settings.password_max_length,
        ),
        session_ttl_minutes=settings.session_ttl_minutes,
        login_max_failures=settings.login_max_failures,
        login_lockout_minutes=settings.login_lockout_minutes,
    )


def resolve_request_principal(
    request: Request, db: Session, settings: Settings
) -> AuthenticatedPrincipal | None:
    token = extract_session_token(request, settings)
    if token is None:
        return None
    if not settings.authentication_enabled:
        raise HTTPException(
            status_code=503,
            detail={"code": "authentication_unavailable", "message": "Authentication unavailable"},
        )
    try:
        principal = build_authentication_service(db, settings).resolve_session(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_session", "message": "Authentication required"},
        ) from exc
    request.state.authenticated_principal = principal
    return principal


def optional_current_principal(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedPrincipal | None:
    cached = getattr(request.state, "authenticated_principal", None)
    if isinstance(cached, AuthenticatedPrincipal):
        return cached
    return resolve_request_principal(request, db, settings)


def require_authenticated_principal(
    principal: AuthenticatedPrincipal | None = Depends(optional_current_principal),
) -> AuthenticatedPrincipal:
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "authentication_required", "message": "Authentication required"},
        )
    return principal


get_current_principal = require_authenticated_principal


def require_platform_permission(
    permission_code: str,
) -> Callable[..., AuthenticatedPrincipal]:
    def dependency(
        principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
        db: Session = Depends(get_db),
    ) -> AuthenticatedPrincipal:
        try:
            AuthorizationService(db).require(
                principal.as_authorization_principal(), permission_code
            )
        except PermissionDeniedError as exc:
            raise HTTPException(
                status_code=403,
                detail={"code": "permission_denied", "message": "Permission denied"},
            ) from exc
        return principal

    return dependency


def require_tenant_permission(
    permission_code: str,
) -> Callable[..., AuthenticatedPrincipal]:
    def dependency(
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
        db: Session = Depends(get_db),
    ) -> AuthenticatedPrincipal:
        tenant_context = getattr(request.state, "tenant_context", None)
        tenant_id = getattr(tenant_context, "store_id", None)
        try:
            AuthorizationService(db).require(
                principal.as_authorization_principal(tenant_id),
                permission_code,
                tenant_id=tenant_id,
            )
        except PermissionDeniedError as exc:
            raise HTTPException(
                status_code=403,
                detail={"code": "permission_denied", "message": "Permission denied"},
            ) from exc
        return principal

    return dependency
