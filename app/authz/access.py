"""Transactional role assignment and revocation operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authz.context import AuthorizationPrincipal, PermissionScope, PrincipalType
from app.authz.exceptions import (
    AccessConflictError,
    AccessValidationError,
    PermissionDeniedError,
)
from app.authz.permissions import PermissionCode
from app.authz.service import AuthorizationService
from app.models import (
    AuthAuditLog,
    AuthPlatformRoleAssignment,
    AuthRole,
    AuthTenantRoleAssignment,
    TenantMembership,
)


@dataclass(frozen=True, slots=True)
class RoleAssignmentResult:
    principal_type: str
    principal_id: str
    role_code: str
    tenant_id: int | None
    status: str
    changed: bool


class RoleAssignmentService:
    """Own one transaction for an auditable access mutation."""

    def __init__(
        self,
        session: Session,
        actor: AuthorizationPrincipal,
        *,
        audit_writer: Callable[[Session, AuthAuditLog], None] | None = None,
    ) -> None:
        self.session = session
        self.actor = actor
        self.audit_writer = audit_writer or (lambda session, record: session.add(record))

    def assign_role(
        self,
        *,
        principal_type: str | PrincipalType,
        principal_id: str,
        role_code: str,
        tenant_id: int | None = None,
    ) -> RoleAssignmentResult:
        return self._mutate(
            action="role_assigned",
            principal_type=principal_type,
            principal_id=principal_id,
            role_code=role_code,
            tenant_id=tenant_id,
            target_status="active",
        )

    def revoke_role(
        self,
        *,
        principal_type: str | PrincipalType,
        principal_id: str,
        role_code: str,
        tenant_id: int | None = None,
    ) -> RoleAssignmentResult:
        return self._mutate(
            action="role_revoked",
            principal_type=principal_type,
            principal_id=principal_id,
            role_code=role_code,
            tenant_id=tenant_id,
            target_status="revoked",
        )

    def _mutate(
        self,
        *,
        action: str,
        principal_type: str | PrincipalType,
        principal_id: str,
        role_code: str,
        tenant_id: int | None,
        target_status: str,
    ) -> RoleAssignmentResult:
        if self.session.in_transaction():
            raise AccessValidationError("access mutation requires a clean session")
        try:
            resolved_type = PrincipalType.parse(principal_type)
        except ValueError as exc:
            raise AccessValidationError("unknown principal type") from exc
        target_id = principal_id.strip()
        code = role_code.strip().lower()
        if not target_id or resolved_type is PrincipalType.ANONYMOUS:
            raise AccessValidationError("a stable non-anonymous principal is required")

        transaction = self.session.begin()
        try:
            role = self.session.get(AuthRole, code)
            if role is None:
                raise AccessValidationError("unknown role code")
            scope = PermissionScope(role.scope)
            if scope is PermissionScope.PLATFORM and tenant_id is not None:
                raise AccessValidationError("platform role assignment cannot include a tenant")
            if scope is PermissionScope.TENANT and tenant_id is None:
                raise AccessValidationError("tenant role assignment requires an explicit tenant")
            self._authorize_assignment(scope, tenant_id)
            changed = self._write_assignment(
                resolved_type,
                target_id,
                role,
                tenant_id,
                target_status,
            )
            record = AuthAuditLog(
                tenant_id=tenant_id,
                actor_principal_type=self.actor.subject_type.value,
                actor_principal_id=self.actor.subject_id or "unknown",
                action=action,
                target_principal_type=resolved_type.value,
                target_principal_id=target_id,
                target_role_code=role.code,
                outcome="succeeded" if changed else "unchanged",
            )
            self.audit_writer(self.session, record)
            self.session.flush()
            transaction.commit()
            return RoleAssignmentResult(
                principal_type=resolved_type.value,
                principal_id=target_id,
                role_code=role.code,
                tenant_id=tenant_id,
                status=target_status,
                changed=changed,
            )
        except IntegrityError as exc:
            transaction.rollback()
            raise AccessConflictError("role assignment conflict") from exc
        except Exception:
            transaction.rollback()
            raise

    def _authorize_assignment(
        self, scope: PermissionScope, tenant_id: int | None
    ) -> None:
        authz = AuthorizationService(self.session)
        if scope is PermissionScope.PLATFORM:
            authz.require(self.actor, PermissionCode.PLATFORM_ACCESS_MANAGE)
            return
        assert tenant_id is not None
        try:
            authz.require(
                self.actor,
                PermissionCode.TENANT_MEMBERS_MANAGE,
                tenant_id=tenant_id,
            )
        except PermissionDeniedError:
            authz.require(self.actor, PermissionCode.TENANT_ACCESS_MANAGE)

    def _write_assignment(
        self,
        principal_type: PrincipalType,
        principal_id: str,
        role: AuthRole,
        tenant_id: int | None,
        target_status: str,
    ) -> bool:
        if role.scope == PermissionScope.PLATFORM.value:
            assignment = self.session.scalar(
                select(AuthPlatformRoleAssignment).where(
                    AuthPlatformRoleAssignment.principal_type == principal_type.value,
                    AuthPlatformRoleAssignment.principal_id == principal_id,
                    AuthPlatformRoleAssignment.role_code == role.code,
                )
            )
            if assignment is None:
                if target_status == "revoked":
                    return False
                self.session.add(
                    AuthPlatformRoleAssignment(
                        principal_type=principal_type.value,
                        principal_id=principal_id,
                        role_code=role.code,
                        status=target_status,
                    )
                )
                return True
            if assignment.status == target_status:
                return False
            assignment.status = target_status
            return True

        assert tenant_id is not None
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.principal_type == principal_type.value,
                TenantMembership.principal_id == principal_id,
            )
        )
        if membership is None:
            if target_status == "revoked":
                return False
            membership = TenantMembership(
                tenant_id=tenant_id,
                principal_type=principal_type.value,
                principal_id=principal_id,
                status="active",
            )
            self.session.add(membership)
            self.session.flush()
        elif membership.status != "active":
            raise AccessValidationError("tenant membership is not active")
        assignment = self.session.scalar(
            select(AuthTenantRoleAssignment).where(
                AuthTenantRoleAssignment.membership_id == membership.id,
                AuthTenantRoleAssignment.role_code == role.code,
            )
        )
        if assignment is None:
            if target_status == "revoked":
                return False
            self.session.add(
                AuthTenantRoleAssignment(
                    membership_id=membership.id,
                    role_code=role.code,
                    status=target_status,
                )
            )
            return True
        if assignment.status == target_status:
            return False
        assignment.status = target_status
        return True

    def list_principal_roles(
        self,
        principal: AuthorizationPrincipal,
        *,
        tenant_id: int | None = None,
    ) -> tuple[str, ...]:
        if principal.subject_id is None:
            return ()
        if tenant_id is None:
            codes = self.session.scalars(
                select(AuthPlatformRoleAssignment.role_code).where(
                    AuthPlatformRoleAssignment.principal_type == principal.subject_type.value,
                    AuthPlatformRoleAssignment.principal_id == principal.subject_id,
                    AuthPlatformRoleAssignment.status == "active",
                )
            ).all()
        else:
            membership_id = self.session.scalar(
                select(TenantMembership.id).where(
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.principal_type == principal.subject_type.value,
                    TenantMembership.principal_id == principal.subject_id,
                    TenantMembership.status == "active",
                )
            )
            if membership_id is None:
                return ()
            codes = self.session.scalars(
                select(AuthTenantRoleAssignment.role_code).where(
                    AuthTenantRoleAssignment.membership_id == membership_id,
                    AuthTenantRoleAssignment.status == "active",
                )
            ).all()
        return tuple(sorted(set(codes)))
