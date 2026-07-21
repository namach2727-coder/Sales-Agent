from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Store, UserIdentity
from tools import manage_identities
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


@pytest.fixture
def identity_engine(tmp_path: Path):
    path = tmp_path / "identity-cli.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    with Session(engine) as db, db.begin():
        db.add(Store(name="Demo", slug="demo", status="active"))
    yield engine
    engine.dispose()


def args(command: str, engine, *extra: str) -> list[str]:
    return [command, *extra, "--database-url", str(engine.url)]


def password_prompt(monkeypatch, value=PASSWORD) -> None:
    monkeypatch.setattr(manage_identities.getpass, "getpass", lambda _: value)


def test_cli_help_does_not_open_database(monkeypatch) -> None:
    monkeypatch.setattr(
        manage_identities, "create_engine", lambda *_: (_ for _ in ()).throw(AssertionError())
    )
    with pytest.raises(SystemExit) as result:
        manage_identities.main(["--help"])
    assert result.value.code == 0


def test_cli_create_list_show_and_duplicate_handling(
    identity_engine, monkeypatch, capsys
) -> None:
    password_prompt(monkeypatch)
    create = args(
        "create-user",
        identity_engine,
        "--email", "CLI@Example.com",
        "--display-name", "CLI User",
        "--json",
    )
    assert manage_identities.main(create) == 0
    output = capsys.readouterr().out
    assert "cli@example.com" not in output  # original display email is preserved
    assert PASSWORD not in output and "password_hash" not in output
    assert manage_identities.main(create) == 3
    assert manage_identities.main(args("list-users", identity_engine, "--json")) == 0
    listed = capsys.readouterr().out
    assert "CLI@Example.com" in listed and "password_hash" not in listed


def test_cli_membership_disable_and_password_change(identity_engine, monkeypatch) -> None:
    password_prompt(monkeypatch)
    assert manage_identities.main(args(
        "create-user", identity_engine,
        "--email", "member@example.com", "--display-name", "Member"
    )) == 0
    with Session(identity_engine) as db:
        user_id = db.scalar(select(UserIdentity.id).where(UserIdentity.normalized_email == "member@example.com"))
    assert manage_identities.main(args(
        "add-tenant-membership", identity_engine,
        "--user-id", str(user_id), "--tenant", "demo"
    )) == 0
    assert manage_identities.main(args(
        "disable-tenant-membership", identity_engine,
        "--user-id", str(user_id), "--tenant", "demo"
    )) == 0
    password_prompt(monkeypatch, "a completely changed secure password")
    assert manage_identities.main(args(
        "set-password", identity_engine, "--user-id", str(user_id)
    )) == 0
    assert manage_identities.main(args(
        "disable-user", identity_engine, "--user-id", str(user_id)
    )) == 0
    assert manage_identities.main(args(
        "enable-user", identity_engine, "--user-id", str(user_id)
    )) == 0


def test_identity_seed_is_non_production_disabled_and_idempotent(identity_engine) -> None:
    registry = default_registry()
    definition = next(
        item
        for item in registry.definitions()
        if item.name == "development.disabled_identity_placeholder"
    )
    assert definition.production_safe is False
    runner = SeedRunner(identity_engine, registry)
    first = runner.run("test", seed_names=(definition.name,))
    second = runner.run("test", seed_names=(definition.name,))
    assert first.results[0].status.value == second.results[0].status.value == "unchanged"
    with Session(identity_engine) as db:
        placeholder = db.scalar(
            select(UserIdentity).where(
                UserIdentity.normalized_email == "disabled-placeholder@example.invalid"
            )
        )
        assert placeholder.status == "disabled" and placeholder.password_hash is None


def test_production_seed_selection_never_creates_identity(identity_engine) -> None:
    # Remove the test fixture placeholder, then prove the default production selection excludes it.
    with Session(identity_engine) as db, db.begin():
        placeholder = db.scalar(select(UserIdentity))
        db.delete(placeholder)
    report = SeedRunner(identity_engine, default_registry()).run("production")
    assert "development.disabled_identity_placeholder" not in {
        item.seed_name for item in report.results
    }
    with Session(identity_engine) as db:
        assert db.scalar(select(func.count()).select_from(UserIdentity)) == 0


def test_authentication_settings_validate_boundaries() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, password_min_length=5)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, login_max_failures=1)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, session_ttl_minutes=1)
