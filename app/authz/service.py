"""Deny-by-default authorization decisions reusable outside HTTP."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.authz.context import (
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationPrincipal,
    PermissionRequirement,
    PermissionScope,
)
from app.authz.exceptions import PermissionDeniedError
from app.authz.permissions import PERMISSION_BY_CODE, ROLE_BY_CODE
from app.authz.repository import AuthorizationRepository


class AuthorizationService:
    def __init__(self, session: Session):
        self.repository = AuthorizationRepository(session)

    def check(
        self,
        principal: AuthorizationPrincipal,
        requirement: PermissionRequirement,
        context: AuthorizationContext | None = None,
    ) -> AuthorizationDecision:
        code = requirement.permission_code.strip().lower()
        definition = PERMISSION_BY_CODE.get(code)
        if definition is None:
            return AuthorizationDecision(False, code, "unknown_permission")
        if not principal.authenticated or principal.subject_id is None:
            return AuthorizationDecision(False, code, "unauthenticated")

        bootstrap_permissions: set[str] = set()
        for role_code in principal.bootstrap_role_codes:
            role = ROLE_BY_CODE.get(role_code)
            if role is not None and role.scope is definition.scope:
                bootstrap_permissions.update(role.permission_codes)

        if definition.scope is PermissionScope.PLATFORM:
            if code in bootstrap_permissions:
                return AuthorizationDecision(True, code, "explicit_role_grant", tuple(sorted(bootstrap_permissions)))
            effective = self.repository.platform_permissions(principal)
            return AuthorizationDecision(
                code in effective,
                code,
                "explicit_role_grant" if code in effective else "permission_missing",
                tuple(sorted(effective)),
            )

        tenant_id = context.tenant_id if context else None
        if tenant_id is None:
            return AuthorizationDecision(False, code, "tenant_context_missing")
        if principal.tenant_id is not None and principal.tenant_id != tenant_id:
            return AuthorizationDecision(False, code, "cross_tenant_denied")
        effective, membership_id, reason = self.repository.tenant_permissions(
            principal, tenant_id
        )
        if principal.membership_id is not None and membership_id != principal.membership_id:
            return AuthorizationDecision(False, code, "cross_tenant_denied")
        return AuthorizationDecision(
            code in effective,
            code,
            "explicit_role_grant" if code in effective else reason if reason != "resolved" else "permission_missing",
            tuple(sorted(effective)),
        )

    def require(
        self,
        principal: AuthorizationPrincipal,
        permission_code: str,
        *,
        tenant_id: int | None = None,
    ) -> AuthorizationDecision:
        decision = self.check(
            principal,
            PermissionRequirement(permission_code),
            AuthorizationContext(tenant_id=tenant_id),
        )
        if not decision.allowed:
            raise PermissionDeniedError(decision.reason_code)
        return decision

    def effective_permissions(
        self,
        principal: AuthorizationPrincipal,
        *,
        tenant_id: int | None = None,
    ) -> tuple[str, ...]:
        codes: set[str] = set()
        for definition in PERMISSION_BY_CODE.values():
            decision = self.check(
                principal,
                PermissionRequirement(definition.code),
                AuthorizationContext(tenant_id=tenant_id),
            )
            if decision.allowed:
                codes.add(definition.code)
        return tuple(sorted(codes))
