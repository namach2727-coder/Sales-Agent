from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher, Type
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService, normalize_email, token_digest
from app.authentication.exceptions import (
    AccountTemporarilyLocked,
    AuthenticationValidationError,
    IdentityConflict,
    IdentityDisabled,
    InvalidCredentials,
    SessionExpired,
    SessionRevoked,
)
from app.models import AuthSession, IdentityAuditLog, UserIdentity
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs) -> None:
        self.value += timedelta(**kwargs)


@pytest.fixture
def auth_engine(tmp_path: Path):
    path = tmp_path / "authentication.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


@pytest.fixture
def fast_passwords() -> PasswordService:
    return PasswordService(
        minimum_length=12,
        hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID),
    )


def service(engine, passwords, *, clock=None, token=None, failures=5):
    session = Session(engine, expire_on_commit=False)
    return session, AuthenticationService(
        session,
        password_service=passwords,
        now=clock,
        token_factory=(lambda: token) if token else None,
        login_max_failures=failures,
        login_lockout_minutes=15,
        session_ttl_minutes=30,
    )


def create_user(engine, passwords, email="User@Example.COM"):
    session, auth = service(engine, passwords)
    try:
        return auth.create_user(
            email=email,
            display_name="Test User",
            password="correct horse battery staple",
        )
    finally:
        session.close()


def test_email_normalization_and_case_insensitive_uniqueness(auth_engine, fast_passwords) -> None:
    assert normalize_email(" User@Example.COM ") == "user@example.com"
    user = create_user(auth_engine, fast_passwords)
    assert user.normalized_email == "user@example.com"
    session, auth = service(auth_engine, fast_passwords)
    try:
        with pytest.raises(IdentityConflict):
            auth.create_user(
                email="user@example.com",
                display_name="Duplicate",
                password="another secure password",
            )
    finally:
        session.close()


def test_password_policy_and_argon2_hash_are_enforced(auth_engine, fast_passwords) -> None:
    with pytest.raises(AuthenticationValidationError):
        fast_passwords.hash("short")
    with pytest.raises(AuthenticationValidationError):
        fast_passwords.hash(" " * 20)
    user = create_user(auth_engine, fast_passwords)
    assert user.password_hash.startswith("$argon2id$")
    assert "correct horse" not in user.password_hash
    assert "password_hash" not in repr(user)


def test_valid_login_stores_only_token_hash(auth_engine, fast_passwords) -> None:
    user = create_user(auth_engine, fast_passwords)
    raw = "A" * 64
    session, auth = service(auth_engine, fast_passwords, token=raw)
    try:
        credential = auth.authenticate_password(
            email=user.email,
            password="correct horse battery staple",
            user_agent="private user agent",
        )
    finally:
        session.close()
    assert credential.token == raw
    with Session(auth_engine) as db:
        stored = db.scalar(select(AuthSession).where(AuthSession.user_id == user.id))
        assert stored.token_hash == token_digest(raw)
        assert raw not in stored.token_hash
        assert stored.user_agent_hash and "private user agent" not in stored.user_agent_hash


def test_unknown_and_wrong_password_fail_generically(auth_engine, fast_passwords) -> None:
    user = create_user(auth_engine, fast_passwords)
    for email in (user.email, "missing@example.com"):
        session, auth = service(auth_engine, fast_passwords)
        try:
            with pytest.raises(InvalidCredentials, match="invalid credentials"):
                auth.authenticate_password(email=email, password="incorrect password value")
        finally:
            session.close()
    with Session(auth_engine) as db:
        failed = db.scalars(
            select(IdentityAuditLog).where(IdentityAuditLog.event_code == "auth.login_failed")
        ).all()
        assert len(failed) == 2
        assert all(item.reason_code == "invalid_credentials" for item in failed)


def test_lockout_activates_expires_and_success_resets(auth_engine, fast_passwords) -> None:
    user = create_user(auth_engine, fast_passwords)
    clock = Clock()
    for _ in range(3):
        session, auth = service(auth_engine, fast_passwords, clock=clock, failures=3)
        try:
            with pytest.raises(InvalidCredentials):
                auth.authenticate_password(email=user.email, password="incorrect password value")
        finally:
            session.close()
    session, auth = service(auth_engine, fast_passwords, clock=clock, failures=3)
    try:
        with pytest.raises(AccountTemporarilyLocked):
            auth.authenticate_password(
                email=user.email, password="correct horse battery staple"
            )
    finally:
        session.close()
    clock.advance(minutes=16)
    session, auth = service(auth_engine, fast_passwords, clock=clock, failures=3)
    try:
        auth.authenticate_password(
            email=user.email, password="correct horse battery staple"
        )
    finally:
        session.close()
    with Session(auth_engine) as db:
        current = db.get(UserIdentity, user.id)
        assert current.failed_login_count == 0 and current.locked_until is None


def test_service_account_and_disabled_user_cannot_password_login(auth_engine, fast_passwords) -> None:
    password_hash = fast_passwords.hash("correct horse battery staple")
    with Session(auth_engine) as db, db.begin():
        db.add_all([
            UserIdentity(email="service@example.com", normalized_email="service@example.com", display_name="Service", password_hash=password_hash, status="active", is_service_account=True),
            UserIdentity(email="disabled@example.com", normalized_email="disabled@example.com", display_name="Disabled", password_hash=password_hash, status="disabled", is_service_account=False),
        ])
    for email in ("service@example.com", "disabled@example.com"):
        session, auth = service(auth_engine, fast_passwords)
        try:
            with pytest.raises(InvalidCredentials):
                auth.authenticate_password(email=email, password="correct horse battery staple")
        finally:
            session.close()


def test_session_expiry_revocation_and_disabled_identity_are_rejected(auth_engine, fast_passwords) -> None:
    user = create_user(auth_engine, fast_passwords)
    clock = Clock()
    session, auth = service(auth_engine, fast_passwords, clock=clock)
    credential = auth.authenticate_password(email=user.email, password="correct horse battery staple")
    session.close()

    session, auth = service(auth_engine, fast_passwords, clock=clock)
    assert auth.resolve_session(credential.token).user_id == user.id
    session.close()
    clock.advance(minutes=31)
    session, auth = service(auth_engine, fast_passwords, clock=clock)
    with pytest.raises(SessionExpired):
        auth.resolve_session(credential.token)
    session.close()

    session, auth = service(auth_engine, fast_passwords, clock=clock)
    second = auth.authenticate_password(email=user.email, password="correct horse battery staple")
    auth.revoke_session(session_id=second.principal.session_id, actor_user_id=user.id)
    with pytest.raises(SessionRevoked):
        auth.resolve_session(second.token)
    session.close()

    session, auth = service(auth_engine, fast_passwords, clock=clock)
    third = auth.authenticate_password(email=user.email, password="correct horse battery staple")
    auth.set_user_enabled(user_id=user.id, enabled=False)
    with pytest.raises((IdentityDisabled, SessionRevoked)):
        auth.resolve_session(third.token)
    session.close()


def test_password_change_revokes_every_existing_session(auth_engine, fast_passwords) -> None:
    user = create_user(auth_engine, fast_passwords)
    tokens = []
    for _ in range(2):
        session, auth = service(auth_engine, fast_passwords)
        tokens.append(auth.authenticate_password(email=user.email, password="correct horse battery staple").token)
        session.close()
    session, auth = service(auth_engine, fast_passwords)
    auth.set_password(user_id=user.id, password="a completely new secure password")
    session.close()
    with Session(auth_engine) as db:
        assert db.scalar(
            select(func.count()).select_from(AuthSession).where(AuthSession.status == "active")
        ) == 0


def test_duplicate_session_token_hash_has_database_protection(auth_engine) -> None:
    with Session(auth_engine) as db, db.begin():
        user = UserIdentity(email="unique@example.com", normalized_email="unique@example.com", display_name="Unique", password_hash=None, status="disabled", is_service_account=False)
        db.add(user)
        db.flush()
        now = datetime.now(UTC)
        db.add_all([
            AuthSession(id="one", user_id=user.id, token_hash="a" * 64, status="active", created_at=now, expires_at=now + timedelta(hours=1), last_seen_at=now),
            AuthSession(id="two", user_id=user.id, token_hash="a" * 64, status="active", created_at=now, expires_at=now + timedelta(hours=1), last_seen_at=now),
        ])
        with pytest.raises(IntegrityError):
            db.flush()
