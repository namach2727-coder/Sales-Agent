from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import Settings, validate_runtime_settings
from app.database import build_engine
from app.main import app
from app.models import AuthPlatformRoleAssignment, IdentityAuditLog, UserIdentity
from app.operations import readiness
from tools.bootstrap_admin import main as bootstrap_admin
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


def test_deployed_settings_fail_closed_and_accept_explicit_uat() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_runtime_settings(Settings(app_env="uat"))
    settings = Settings(
        app_env="uat",
        database_url="postgresql+psycopg://user:password@database/app",
        application_secret="a" * 40,
        trusted_hosts=["uat.example.com"],
        cors_allowed_origins=["https://uat.example.com"],
        force_https=True,
        session_cookie_secure=True,
        legacy_admin_adapter_enabled=False,
    )
    validate_runtime_settings(settings)


def test_wildcard_cors_and_weak_secret_are_rejected() -> None:
    settings = Settings(
        app_env="integration",
        database_url="postgresql+psycopg://user:password@database/app",
        application_secret="replace-me",
        trusted_hosts=["integration.example.com"],
        cors_allowed_origins=["*"],
    )
    with pytest.raises(ValueError, match="APPLICATION_SECRET"):
        validate_runtime_settings(settings)


def test_mounted_application_secret_is_loaded(tmp_path: Path) -> None:
    secret_file = tmp_path / "application-secret"
    secret_file.write_text("z" * 40, encoding="utf-8")
    settings = Settings(application_secret_file=str(secret_file))
    assert settings.application_secret.get_secret_value() == "z" * 40


def test_postgresql_engine_uses_pre_ping_and_configured_pool() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@database/app",
        database_pool_size=3,
        database_max_overflow=4,
        database_pool_timeout=7,
        database_pool_recycle=600,
    )
    engine = build_engine(settings)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.pool.size() == 3
        assert engine.pool._pre_ping is True
        assert engine.pool._max_overflow == 4
        assert engine.pool._timeout == 7
        assert engine.pool._recycle == 600
    finally:
        engine.dispose()


def test_operational_headers_liveness_and_version() -> None:
    with TestClient(app) as client:
        live = client.get("/live", headers={"X-Request-ID": "pytest-correlation-1"})
        version = client.get("/version")
    assert live.status_code == 200
    assert live.headers["X-Request-ID"] == "pytest-correlation-1"
    assert live.headers["X-Content-Type-Options"] == "nosniff"
    assert version.status_code == 200
    assert set(version.json()) == {"service", "version", "build", "environment"}


def test_readiness_requires_database_at_single_head(tmp_path: Path) -> None:
    path = tmp_path / "ready.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        result = readiness(engine)
        assert result.ready is True
        assert result.current_revision == "0006_lean_business_catalog"
    finally:
        engine.dispose()


def test_first_admin_bootstrap_is_audited_and_single_use(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "bootstrap.db"
    url = f"sqlite:///{path.as_posix()}"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    engine = create_engine(url)
    SeedRunner(engine, default_registry()).run("production")
    engine.dispose()
    monkeypatch.setenv("BOOTSTRAP_TEST_PASSWORD", "a secure bootstrap password")
    arguments = [
        "--email", "first-admin@example.invalid",
        "--display-name", "First Admin",
        "--database-url", url,
        "--password-env", "BOOTSTRAP_TEST_PASSWORD",
    ]
    assert bootstrap_admin(arguments) == 0
    assert bootstrap_admin(arguments) == 1
    engine = create_engine(url)
    with Session(engine) as session:
        user = session.scalar(select(UserIdentity).where(UserIdentity.normalized_email == "first-admin@example.invalid"))
        assert user is not None
        assert session.scalar(
            select(AuthPlatformRoleAssignment).where(
                AuthPlatformRoleAssignment.principal_id == str(user.id),
                AuthPlatformRoleAssignment.role_code == "platform_super_admin",
                AuthPlatformRoleAssignment.status == "active",
            )
        ) is not None
        assert session.scalar(
            select(IdentityAuditLog).where(
                IdentityAuditLog.event_code == "bootstrap.platform_admin_created"
            )
        ) is not None
    engine.dispose()
