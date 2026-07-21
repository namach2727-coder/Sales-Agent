"""Immutable verified identity and session value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.authz.context import AuthorizationPrincipal, PrincipalType


@dataclass(frozen=True, slots=True)
class PrincipalMembership:
    membership_id: int
    tenant_id: int
    tenant_slug: str
    status: str
    role_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    user_id: int
    email: str
    display_name: str
    session_id: str
    authenticated_at: datetime
    platform_role_codes: tuple[str, ...]
    tenant_memberships: tuple[PrincipalMembership, ...]

    def as_authorization_principal(
        self, tenant_id: int | None = None
    ) -> AuthorizationPrincipal:
        membership = next(
            (
                item
                for item in self.tenant_memberships
                if item.tenant_id == tenant_id and item.status == "active"
            ),
            None,
        )
        return AuthorizationPrincipal(
            subject_id=str(self.user_id),
            subject_type=PrincipalType.USER,
            authenticated=True,
            tenant_id=tenant_id,
            membership_id=membership.membership_id if membership else None,
        )


@dataclass(frozen=True, slots=True)
class SessionCredential:
    token: str
    principal: AuthenticatedPrincipal
    expires_at: datetime
