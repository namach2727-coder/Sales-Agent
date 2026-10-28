"""Authorization guard for future SEO SSO grant endpoints.

This module does NOT issue credentials or authorize cross-domain redirects.
The SSO grant/exchange protocol must be added only after one-time code
storage, CSRF protection, revocation and audit tests are implemented.
"""
from fastapi import Depends, HTTPException

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal


def require_seo_admin(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> AuthenticatedPrincipal:
    """Only the existing DirectPilot platform super-admin may use SEO SSO."""
    if "platform_super_admin" not in principal.platform_role_codes:
        raise HTTPException(
            status_code=403,
            detail={"code": "seo_admin_forbidden", "message": "SEO admin access denied"},
        )
    return principal
