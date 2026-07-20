"""Read-only relational authorization lookups."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authz.context import AuthorizationPrincipal, PermissionScope
from app.models import (
    AuthPermission,
    AuthPlatformRoleAssignment,
    AuthRole,
    AuthRolePermission,
    AuthTenantRoleAssignment,
    TenantMembership,
)


class AuthorizationRepository:
    def __init__(self, session: Session):
        self.session = session

    def platform_permissions(self, principal: AuthorizationPrincipal) -> set[str]:
        if principal.subject_id is None:
            return set()
        return set(
            self.session.scalars(
                select(AuthPermission.code)
                .join(AuthRolePermission, AuthRolePermission.permission_code == AuthPermission.code)
                .join(AuthRole, AuthRole.code == AuthRolePermission.role_code)
                .join(AuthPlatformRoleAssignment, AuthPlatformRoleAssignment.role_code == AuthRole.code)
                .where(
                    AuthPlatformRoleAssignment.principal_type == principal.subject_type.value,
                    AuthPlatformRoleAssignment.principal_id == principal.subject_id,
                    AuthPlatformRoleAssignment.status == "active",
                    AuthRole.scope == PermissionScope.PLATFORM.value,
                    AuthPermission.scope == PermissionScope.PLATFORM.value,
                )
            ).all()
        )

    def tenant_permissions(
        self, principal: AuthorizationPrincipal, tenant_id: int
    ) -> tuple[set[str], int | None, str]:
        if principal.subject_id is None:
            return set(), None, "membership_missing"
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.principal_type == principal.subject_type.value,
                TenantMembership.principal_id == principal.subject_id,
            )
        )
        if membership is None:
            return set(), None, "membership_missing"
        if membership.status != "active":
            return set(), membership.id, "membership_inactive"
        permissions = set(
            self.session.scalars(
                select(AuthPermission.code)
                .join(AuthRolePermission, AuthRolePermission.permission_code == AuthPermission.code)
                .join(AuthRole, AuthRole.code == AuthRolePermission.role_code)
                .join(AuthTenantRoleAssignment, AuthTenantRoleAssignment.role_code == AuthRole.code)
                .where(
                    AuthTenantRoleAssignment.membership_id == membership.id,
                    AuthTenantRoleAssignment.status == "active",
                    AuthRole.scope == PermissionScope.TENANT.value,
                    AuthPermission.scope == PermissionScope.TENANT.value,
                )
            ).all()
        )
        return permissions, membership.id, "resolved"
