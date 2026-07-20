"""Safe authorization and access-management failures."""


class AuthorizationError(RuntimeError):
    code = "authorization_error"


class PermissionDeniedError(AuthorizationError):
    code = "permission_denied"

    def __init__(self, reason_code: str):
        super().__init__("permission denied")
        self.reason_code = reason_code


class InvalidAuthorizationContextError(AuthorizationError):
    code = "invalid_authorization_context"


class AccessManagementError(AuthorizationError):
    code = "access_management_error"


class AccessValidationError(AccessManagementError):
    code = "access_validation_error"


class AccessConflictError(AccessManagementError):
    code = "access_conflict"
