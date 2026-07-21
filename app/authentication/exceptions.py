"""Typed authentication errors with safe external mappings."""


class AuthenticationError(Exception):
    pass


class AuthenticationRequired(AuthenticationError):
    pass


class InvalidCredentials(AuthenticationError):
    pass


class SessionExpired(AuthenticationError):
    pass


class SessionRevoked(AuthenticationError):
    pass


class IdentityDisabled(AuthenticationError):
    pass


class AccountTemporarilyLocked(AuthenticationError):
    pass


class IdentityConflict(AuthenticationError):
    pass


class MembershipConflict(AuthenticationError):
    pass


class AuthenticationValidationError(AuthenticationError):
    pass
