"""Authentication persistence queries without transaction ownership."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuthSession, TenantMembership, UserIdentity


class AuthenticationRepository:
    def __init__(self, session: Session):
        self.session = session

    def user_by_normalized_email(self, normalized_email: str) -> UserIdentity | None:
        return self.session.scalar(
            select(UserIdentity).where(
                UserIdentity.normalized_email == normalized_email
            )
        )

    def session_by_hash(self, token_hash: str) -> AuthSession | None:
        return self.session.scalar(
            select(AuthSession).where(AuthSession.token_hash == token_hash)
        )

    def user_memberships(self, user_id: int) -> tuple[TenantMembership, ...]:
        return tuple(
            self.session.scalars(
                select(TenantMembership)
                .where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.status == "active",
                )
                .order_by(TenantMembership.tenant_id)
            ).all()
        )
