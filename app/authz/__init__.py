"""Public authorization API."""

from app.authz.context import (
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationPrincipal,
    PermissionRequirement,
    PermissionScope,
    PrincipalType,
)
from app.authz.exceptions import (
    AccessConflictError,
    AccessManagementError,
    AccessValidationError,
    AuthorizationError,
    InvalidAuthorizationContextError,
    PermissionDeniedError,
)
from app.authz.permissions import PermissionCode, RoleDefinition
from app.authz.service import AuthorizationService
from app.authz.access import RoleAssignmentResult, RoleAssignmentService

__all__ = [
    "AccessConflictError", "AccessManagementError", "AccessValidationError",
    "AuthorizationContext", "AuthorizationDecision", "AuthorizationError",
    "AuthorizationPrincipal", "AuthorizationService",
    "InvalidAuthorizationContextError", "PermissionCode", "PermissionDeniedError",
    "PermissionRequirement", "PermissionScope", "PrincipalType", "RoleDefinition",
    "RoleAssignmentResult", "RoleAssignmentService",
]
