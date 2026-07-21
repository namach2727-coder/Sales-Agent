"""FastAPI adapters that keep authentication separate from authorization."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.admin import require_admin_mutation, require_admin_read
from app.authz.context import AuthorizationPrincipal, PrincipalType
from app.authz.exceptions import PermissionDeniedError
from app.authz.service import AuthorizationService
from app.config import Settings, get_settings
from app.database import get_db


LOCAL_PROVIDER_ADMIN_SUBJECT = "local-provider-admin"


def local_provider_admin_principal() -> AuthorizationPrincipal:
    """Temporary compatibility mapping for the authenticated local admin.

    The existing loopback/same-origin authentication executes before this
    principal is created. The explicit role has a finite permission list in the
    immutable system catalog; it is not a wildcard or route-level bypass.
    """

    return AuthorizationPrincipal(
        subject_id=LOCAL_PROVIDER_ADMIN_SUBJECT,
        subject_type=PrincipalType.PROVIDER_ADMIN,
        authenticated=True,
        bootstrap_role_codes=("platform_super_admin",),
    )


def get_current_authorization_principal(request: Request) -> AuthorizationPrincipal:
    principal = getattr(request.state, "authorization_principal", None)
    return (
        principal
        if isinstance(principal, AuthorizationPrincipal)
        else AuthorizationPrincipal.anonymous()
    )


def require_permission(permission_code: str) -> Callable[..., AuthorizationPrincipal]:
    """Generic deny-by-default guard for future authenticated routes."""

    def dependency(
        request: Request,
        principal: AuthorizationPrincipal = Depends(get_current_authorization_principal),
        db: Session = Depends(get_db),
    ) -> AuthorizationPrincipal:
        if not principal.authenticated:
            raise HTTPException(status_code=401, detail="Authentication required")
        tenant_context = getattr(request.state, "tenant_context", None)
        tenant_id = getattr(tenant_context, "store_id", None)
        try:
            AuthorizationService(db).require(
                principal, permission_code, tenant_id=tenant_id
            )
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail="Permission denied") from exc
        return principal

    return dependency


def require_admin_permission(
    permission_code: str,
    *,
    mutation: bool,
) -> Callable[..., AuthorizationPrincipal]:
    """Preserve local-admin authentication, then enforce explicit RBAC."""

    def dependency(
        request: Request,
        db: Session = Depends(get_db),
        settings: Settings = Depends(get_settings),
    ) -> AuthorizationPrincipal:
        from app.authentication.dependencies import resolve_request_principal

        authenticated = resolve_request_principal(request, db, settings)
        if authenticated is not None:
            principal = authenticated.as_authorization_principal()
        else:
            if not settings.legacy_admin_adapter_enabled:
                raise HTTPException(status_code=401, detail="Authentication required")
            if mutation:
                require_admin_mutation(request, settings)
            else:
                require_admin_read(request, settings)
            principal = local_provider_admin_principal()
        try:
            AuthorizationService(db).require(principal, permission_code)
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail="Permission denied") from exc
        return principal

    return dependency
