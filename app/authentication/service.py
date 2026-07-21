"""Transactional identity, password, session, and principal service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import hashlib
import secrets
import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import (
    AuthenticatedPrincipal,
    PrincipalMembership,
    SessionCredential,
)
from app.authentication.exceptions import (
    AccountTemporarilyLocked,
    AuthenticationValidationError,
    IdentityConflict,
    IdentityDisabled,
    InvalidCredentials,
    MembershipConflict,
    SessionExpired,
    SessionRevoked,
)
from app.authentication.passwords import PasswordService
from app.authentication.repository import AuthenticationRepository
from app.authz.context import PrincipalType
from app.models import (
    AuthPlatformRoleAssignment,
    AuthSession,
    AuthTenantRoleAssignment,
    IdentityAuditLog,
    Store,
    TenantMembership,
    UserIdentity,
)


def normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    if not normalized or len(normalized) > 320 or normalized.count("@") != 1:
        raise AuthenticationValidationError("invalid email address")
    local, domain = normalized.split("@", 1)
    if not local or not domain or "." not in domain:
        raise AuthenticationValidationError("invalid email address")
    return normalized


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def metadata_digest(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value[:1024].encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthenticationService:
    """Owns one database transaction for each state-changing operation."""

    def __init__(
        self,
        session: Session,
        *,
        password_service: PasswordService | None = None,
        session_ttl_minutes: int = 480,
        login_max_failures: int = 5,
        login_lockout_minutes: int = 15,
        now: Callable[[], datetime] | None = None,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self.session = session
        self.repository = AuthenticationRepository(session)
        self.passwords = password_service or PasswordService()
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self.login_max_failures = login_max_failures
        self.lockout_duration = timedelta(minutes=login_lockout_minutes)
        self.now = now or (lambda: datetime.now(UTC))
        self.token_factory = token_factory or (lambda: secrets.token_urlsafe(48))

    def _require_clean_session(self) -> None:
        if self.session.in_transaction():
            raise AuthenticationValidationError(
                "authentication mutation requires a clean session"
            )

    def _audit(
        self,
        event_code: str,
        *,
        actor_user_id: int | None = None,
        target_user_id: int | None = None,
        tenant_id: int | None = None,
        session_id: str | None = None,
        outcome: str = "succeeded",
        reason_code: str | None = None,
    ) -> None:
        self.session.add(
            IdentityAuditLog(
                event_code=event_code,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                outcome=outcome,
                reason_code=reason_code,
            )
        )

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        email_verified: bool = False,
        is_service_account: bool = False,
        actor_user_id: int | None = None,
    ) -> UserIdentity:
        self._require_clean_session()
        normalized = normalize_email(email)
        name = display_name.strip()
        if not name or len(name) > 200:
            raise AuthenticationValidationError("invalid display name")
        if is_service_account:
            raise AuthenticationValidationError(
                "service-account credentials are outside this milestone"
            )
        password_hash = self.passwords.hash(password)
        now = self.now()
        try:
            with self.session.begin():
                if self.repository.user_by_normalized_email(normalized) is not None:
                    raise IdentityConflict("identity already exists")
                user = UserIdentity(
                    email=email.strip(),
                    normalized_email=normalized,
                    display_name=name,
                    password_hash=password_hash,
                    status="active",
                    is_service_account=False,
                    email_verified=email_verified,
                    password_changed_at=now,
                )
                self.session.add(user)
                self.session.flush()
                self._audit(
                    "identity.created",
                    actor_user_id=actor_user_id,
                    target_user_id=user.id,
                )
            return user
        except IntegrityError as exc:
            self.session.rollback()
            raise IdentityConflict("identity already exists") from exc

    def authenticate_password(
        self, *, email: str, password: str, user_agent: str | None = None
    ) -> SessionCredential:
        self._require_clean_session()
        try:
            normalized = normalize_email(email)
        except AuthenticationValidationError:
            normalized = "invalid@invalid.local"
        now = self.now()
        failure: Exception | None = None
        credential: SessionCredential | None = None
        with self.session.begin():
            user = self.repository.user_by_normalized_email(normalized)
            if user is None:
                self.passwords.verify_dummy(password)
                self._audit(
                    "auth.login_failed", outcome="denied", reason_code="invalid_credentials"
                )
                failure = InvalidCredentials("invalid credentials")
            elif user.status != "active" or user.is_service_account:
                self.passwords.verify_dummy(password)
                self._audit(
                    "auth.login_failed",
                    target_user_id=user.id,
                    outcome="denied",
                    reason_code="invalid_credentials",
                )
                failure = InvalidCredentials("invalid credentials")
            elif user.locked_until and _aware(user.locked_until) > now:
                self.passwords.verify_dummy(password)
                self._audit(
                    "auth.login_failed",
                    target_user_id=user.id,
                    outcome="denied",
                    reason_code="account_temporarily_locked",
                )
                failure = AccountTemporarilyLocked("invalid credentials")
            elif not user.password_hash or not self.passwords.verify(
                user.password_hash, password
            ):
                user.failed_login_count += 1
                if user.failed_login_count >= self.login_max_failures:
                    user.locked_until = now + self.lockout_duration
                self._audit(
                    "auth.login_failed",
                    target_user_id=user.id,
                    outcome="denied",
                    reason_code="invalid_credentials",
                )
                failure = InvalidCredentials("invalid credentials")
            else:
                if self.passwords.needs_rehash(user.password_hash):
                    user.password_hash = self.passwords.hash(password)
                user.failed_login_count = 0
                user.locked_until = None
                user.last_login_at = now
                token = self.token_factory()
                if len(token) < 32:
                    raise AuthenticationValidationError("session token entropy is insufficient")
                auth_session = AuthSession(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    token_hash=token_digest(token),
                    status="active",
                    created_at=now,
                    expires_at=now + self.session_ttl,
                    last_seen_at=now,
                    user_agent_hash=metadata_digest(user_agent),
                )
                self.session.add(auth_session)
                self.session.flush()
                self._audit(
                    "auth.login_succeeded",
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    session_id=auth_session.id,
                )
                self._audit(
                    "auth.session_created",
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    session_id=auth_session.id,
                )
                credential = SessionCredential(
                    token=token,
                    principal=self._principal(user, auth_session),
                    expires_at=auth_session.expires_at,
                )
        if failure is not None:
            raise failure
        assert credential is not None
        return credential

    def resolve_session(self, token: str) -> AuthenticatedPrincipal:
        self._require_clean_session()
        if not token or len(token) < 32 or len(token) > 2048:
            raise InvalidCredentials("invalid session")
        now = self.now()
        principal: AuthenticatedPrincipal | None = None
        error: Exception | None = None
        with self.session.begin():
            auth_session = self.repository.session_by_hash(token_digest(token))
            if auth_session is None:
                error = InvalidCredentials("invalid session")
            elif auth_session.status != "active" or auth_session.revoked_at is not None:
                error = SessionRevoked("session revoked")
            elif _aware(auth_session.expires_at) <= now:
                auth_session.status = "expired"
                error = SessionExpired("session expired")
            else:
                user = self.session.get(UserIdentity, auth_session.user_id)
                if user is None or user.status != "active":
                    error = IdentityDisabled("identity disabled")
                else:
                    auth_session.last_seen_at = now
                    principal = self._principal(user, auth_session)
        if error is not None:
            raise error
        assert principal is not None
        return principal

    def _principal(
        self, user: UserIdentity, auth_session: AuthSession
    ) -> AuthenticatedPrincipal:
        platform_roles = tuple(
            sorted(
                self.session.scalars(
                    select(AuthPlatformRoleAssignment.role_code).where(
                        AuthPlatformRoleAssignment.principal_type
                        == PrincipalType.USER.value,
                        AuthPlatformRoleAssignment.principal_id == str(user.id),
                        AuthPlatformRoleAssignment.status == "active",
                    )
                ).all()
            )
        )
        memberships: list[PrincipalMembership] = []
        for membership in self.repository.user_memberships(user.id):
            store = self.session.get(Store, membership.tenant_id)
            if store is None:
                continue
            roles = tuple(
                sorted(
                    self.session.scalars(
                        select(AuthTenantRoleAssignment.role_code).where(
                            AuthTenantRoleAssignment.membership_id == membership.id,
                            AuthTenantRoleAssignment.status == "active",
                        )
                    ).all()
                )
            )
            memberships.append(
                PrincipalMembership(
                    membership_id=membership.id,
                    tenant_id=membership.tenant_id,
                    tenant_slug=store.slug,
                    status=membership.status,
                    role_codes=roles,
                )
            )
        return AuthenticatedPrincipal(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            session_id=auth_session.id,
            authenticated_at=_aware(auth_session.created_at),
            platform_role_codes=platform_roles,
            tenant_memberships=tuple(memberships),
        )

    def revoke_session(
        self, *, session_id: str, actor_user_id: int, target_user_id: int | None = None
    ) -> bool:
        self._require_clean_session()
        with self.session.begin():
            auth_session = self.session.get(AuthSession, session_id)
            if auth_session is None:
                return False
            owner_id = target_user_id if target_user_id is not None else actor_user_id
            if auth_session.user_id != owner_id:
                raise InvalidCredentials("session could not be resolved")
            result = self.session.execute(
                update(AuthSession)
                .where(
                    AuthSession.id == session_id,
                    AuthSession.user_id == owner_id,
                    AuthSession.status == "active",
                )
                .values(status="revoked", revoked_at=self.now())
                .execution_options(synchronize_session=False)
            )
            changed = result.rowcount == 1
            self._audit(
                "auth.session_revoked",
                actor_user_id=actor_user_id,
                target_user_id=auth_session.user_id,
                session_id=auth_session.id,
                outcome="succeeded" if changed else "unchanged",
            )
            return changed

    def revoke_all_user_sessions(
        self, *, user_id: int, actor_user_id: int | None = None
    ) -> int:
        self._require_clean_session()
        with self.session.begin():
            count = self._revoke_sessions_in_transaction(user_id)
            self._audit(
                "auth.all_sessions_revoked",
                actor_user_id=actor_user_id,
                target_user_id=user_id,
                outcome="succeeded" if count else "unchanged",
            )
            return count

    def _revoke_sessions_in_transaction(self, user_id: int) -> int:
        result = self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.status == "active",
            )
            .values(status="revoked", revoked_at=self.now())
            .execution_options(synchronize_session=False)
        )
        return int(result.rowcount or 0)

    def set_password(
        self, *, user_id: int, password: str, actor_user_id: int | None = None
    ) -> None:
        self._require_clean_session()
        password_hash = self.passwords.hash(password)
        with self.session.begin():
            user = self.session.get(UserIdentity, user_id)
            if user is None:
                raise AuthenticationValidationError("identity not found")
            if user.is_service_account:
                raise AuthenticationValidationError("service account password login is disabled")
            user.password_hash = password_hash
            user.password_changed_at = self.now()
            user.failed_login_count = 0
            user.locked_until = None
            self._revoke_sessions_in_transaction(user.id)
            self._audit(
                "identity.password_changed",
                actor_user_id=actor_user_id,
                target_user_id=user.id,
            )

    def set_user_enabled(
        self, *, user_id: int, enabled: bool, actor_user_id: int | None = None
    ) -> None:
        self._require_clean_session()
        with self.session.begin():
            user = self.session.get(UserIdentity, user_id)
            if user is None:
                raise AuthenticationValidationError("identity not found")
            user.status = "active" if enabled else "disabled"
            if not enabled:
                self._revoke_sessions_in_transaction(user.id)
            self._audit(
                "identity.enabled" if enabled else "identity.disabled",
                actor_user_id=actor_user_id,
                target_user_id=user.id,
            )

    def add_tenant_membership(
        self, *, user_id: int, tenant_id: int, actor_user_id: int | None = None
    ) -> TenantMembership:
        self._require_clean_session()
        try:
            with self.session.begin():
                user = self.session.get(UserIdentity, user_id)
                store = self.session.get(Store, tenant_id)
                if user is None or store is None:
                    raise AuthenticationValidationError("identity or tenant not found")
                existing = self.session.scalar(
                    select(TenantMembership).where(
                        TenantMembership.tenant_id == tenant_id,
                        TenantMembership.user_id == user_id,
                    )
                )
                if existing is not None:
                    raise MembershipConflict("membership already exists")
                membership = TenantMembership(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    principal_type=PrincipalType.USER.value,
                    principal_id=str(user.id),
                    status="active",
                )
                self.session.add(membership)
                self.session.flush()
                self._audit(
                    "tenant.membership_created",
                    actor_user_id=actor_user_id,
                    target_user_id=user.id,
                    tenant_id=tenant_id,
                )
            return membership
        except IntegrityError as exc:
            self.session.rollback()
            raise MembershipConflict("membership already exists") from exc

    def set_membership_enabled(
        self,
        *,
        user_id: int,
        tenant_id: int,
        enabled: bool,
        actor_user_id: int | None = None,
    ) -> None:
        self._require_clean_session()
        with self.session.begin():
            membership = self.session.scalar(
                select(TenantMembership).where(
                    TenantMembership.user_id == user_id,
                    TenantMembership.tenant_id == tenant_id,
                )
            )
            if membership is None:
                raise AuthenticationValidationError("membership not found")
            membership.status = "active" if enabled else "disabled"
            self._audit(
                "tenant.membership_enabled" if enabled else "tenant.membership_disabled",
                actor_user_id=actor_user_id,
                target_user_id=user_id,
                tenant_id=tenant_id,
            )

    def list_sessions(self, user_id: int) -> tuple[AuthSession, ...]:
        return tuple(
            self.session.scalars(
                select(AuthSession)
                .where(AuthSession.user_id == user_id)
                .order_by(AuthSession.created_at.desc())
            ).all()
        )
