"""Transport-independent principal, requirement, context, and decision types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermissionScope(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"


class PrincipalType(str, Enum):
    USER = "user"
    PROVIDER_ADMIN = "provider_admin"
    SERVICE_ACCOUNT = "service_account"
    API_KEY = "api_key"
    ANONYMOUS = "anonymous"

    @classmethod
    def parse(cls, value: str | "PrincipalType") -> "PrincipalType":
        if isinstance(value, cls):
            return value
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise ValueError("unknown principal type") from exc


@dataclass(frozen=True, slots=True)
class AuthorizationPrincipal:
    subject_id: str | None
    subject_type: PrincipalType
    authenticated: bool
    tenant_id: int | None = None
    membership_id: int | None = None
    bootstrap_role_codes: tuple[str, ...] = ()

    @classmethod
    def anonymous(cls) -> "AuthorizationPrincipal":
        return cls(None, PrincipalType.ANONYMOUS, False)


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    tenant_id: int | None = None


@dataclass(frozen=True, slots=True)
class PermissionRequirement:
    permission_code: str


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    permission_code: str
    reason_code: str
    effective_permissions: tuple[str, ...] = ()
