"""Composable permission plus product-entitlement policy."""

from sqlalchemy.orm import Session

from app.authz.context import AuthorizationPrincipal
from app.authz.exceptions import PermissionDeniedError
from app.authz.service import AuthorizationService
from app.models import Store
from app.module_catalog import module_enabled


def require_tenant_module_permission(
    session: Session,
    principal: AuthorizationPrincipal,
    *,
    store: Store,
    permission_code: str,
    module_code: str,
) -> None:
    AuthorizationService(session).require(
        principal, permission_code, tenant_id=store.id
    )
    if not module_enabled(session, store, module_code):
        raise PermissionDeniedError("module_not_entitled")
