from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import (
    AuthPermission,
    AuthRole,
    AuthRolePermission,
    ModuleDefinition,
    SeedHistory,
    Store,
    StoreModule,
)
from tools import seed_data
from tools.seeding import (
    SeedContext,
    SeedDefinition,
    SeedExecutionError,
    SeedMutation,
    SeedOwnership,
    SeedProfile,
    SeedRegistry,
    SeedRunner,
    SeedScope,
    SeedStatus,
    SeedValidationError,
    default_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def _config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


@pytest.fixture
def seed_engine(tmp_path: Path) -> Engine:
    database_path = tmp_path / "seed.db"
    command.upgrade(_config(database_path), "head")
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    yield engine
    engine.dispose()


def _definition(
    name: str,
    handler,
    *,
    order: int = 100,
    dependencies: tuple[str, ...] = (),
    scope: SeedScope = SeedScope.GLOBAL,
    profiles: frozenset[SeedProfile] = frozenset(SeedProfile),
    production_safe: bool = True,
) -> SeedDefinition:
    return SeedDefinition(
        name=name,
        version="1",
        scope=scope,
        compatible_profiles=profiles,
        production_safe=production_safe,
        ownership=SeedOwnership.CREATE_ONLY,
        handler=handler,
        order=order,
        dependencies=dependencies,
    )


def _unchanged(_: SeedContext) -> SeedMutation:
    return SeedMutation(status=SeedStatus.UNCHANGED, unchanged=1)


def _create_store(engine: Engine, slug: str, *, status: str = "active") -> Store:
    with Session(engine) as session, session.begin():
        store = Store(name=slug.title(), slug=slug, status=status)
        session.add(store)
        session.flush()
        store_id = store.id
    with Session(engine) as session:
        return session.get(Store, store_id)


def test_registry_rejects_duplicate_seed_names() -> None:
    registry = SeedRegistry()
    registry.register(_definition("test.duplicate", _unchanged))
    with pytest.raises(SeedValidationError, match="duplicate seed name"):
        registry.register(_definition("test.duplicate", _unchanged))


def test_execution_order_is_deterministic_and_dependency_aware(seed_engine: Engine) -> None:
    calls: list[str] = []

    def handler(name: str):
        def run(_: SeedContext) -> SeedMutation:
            calls.append(name)
            return SeedMutation(status=SeedStatus.UNCHANGED, unchanged=1)

        return run

    registry = SeedRegistry()
    registry.register(_definition("test.third", handler("third"), order=30, dependencies=("test.second",)))
    registry.register(_definition("test.first", handler("first"), order=10))
    registry.register(_definition("test.second", handler("second"), order=20))
    SeedRunner(seed_engine, registry).run("test")
    assert calls == ["first", "second", "third"]


def test_unknown_profile_fails(seed_engine: Engine) -> None:
    with pytest.raises(SeedValidationError, match="unknown seed profile"):
        SeedRunner(seed_engine, default_registry()).run("staging")


def test_production_rejects_demo_only_seed(seed_engine: Engine) -> None:
    registry = SeedRegistry()
    registry.register(
        _definition(
            "demo.catalog",
            _unchanged,
            profiles=frozenset({SeedProfile.PRODUCTION, SeedProfile.DEMO}),
            production_safe=False,
        )
    )
    with pytest.raises(SeedValidationError, match="rejects non-production-safe"):
        SeedRunner(seed_engine, registry).run("production", seed_names=("demo.catalog",))


def test_tenant_seed_requires_explicit_tenant(seed_engine: Engine) -> None:
    with pytest.raises(SeedValidationError, match="requires --tenant"):
        SeedRunner(seed_engine, default_registry()).run(
            "production", seed_names=("tenant.module_entitlements",)
        )


def test_unknown_tenant_fails(seed_engine: Engine) -> None:
    with pytest.raises(SeedValidationError, match="does not exist"):
        SeedRunner(seed_engine, default_registry()).run(
            "production", tenant_slug="missing-store"
        )


def test_global_seed_runs_without_tenant_and_is_idempotent(seed_engine: Engine) -> None:
    runner = SeedRunner(seed_engine, default_registry())
    first = runner.run("production", seed_names=("system.module_definitions",))
    second = runner.run("production", seed_names=("system.module_definitions",))
    assert first.results[0].status is SeedStatus.CREATED
    assert first.results[0].created > 0
    assert second.results[0].status is SeedStatus.UNCHANGED
    with Session(seed_engine) as session:
        codes = list(session.scalars(select(ModuleDefinition.code)).all())
        assert len(codes) == len(set(codes))
        assert session.scalar(select(func.count()).select_from(SeedHistory)) == 2


def test_create_only_seed_does_not_overwrite_user_managed_fields(seed_engine: Engine) -> None:
    runner = SeedRunner(seed_engine, default_registry())
    runner.run("production", seed_names=("system.module_definitions",))
    with Session(seed_engine) as session, session.begin():
        module = session.get(ModuleDefinition, "sales_agent_core")
        assert module is not None
        module.monthly_price = 123456
        module.name = "Manager-owned name"
    runner.run("production", seed_names=("system.module_definitions",))
    with Session(seed_engine) as session:
        module = session.get(ModuleDefinition, "sales_agent_core")
        assert module is not None
        assert module.monthly_price == 123456
        assert module.name == "Manager-owned name"


def test_dry_run_shows_dependency_operations_but_persists_nothing(seed_engine: Engine) -> None:
    _create_store(seed_engine, "alpha")
    report = SeedRunner(seed_engine, default_registry()).run(
        "development", tenant_slug="alpha", dry_run=True
    )
    assert [result.seed_name for result in report.results] == [
        "system.module_definitions",
        "tenant.module_entitlements",
        "system.auth_permissions",
        "system.auth_roles",
        "system.auth_role_permissions",
    ]
    assert all(result.status is SeedStatus.CREATED for result in report.results)
    with Session(seed_engine) as session:
        assert session.scalar(select(func.count()).select_from(ModuleDefinition)) == 0
        assert session.scalar(select(func.count()).select_from(StoreModule)) == 0
        assert session.scalar(select(func.count()).select_from(AuthPermission)) == 0
        assert session.scalar(select(func.count()).select_from(AuthRole)) == 0
        assert session.scalar(select(func.count()).select_from(AuthRolePermission)) == 0
        assert session.scalar(select(func.count()).select_from(SeedHistory)) == 0


def test_failed_seed_rolls_back_and_records_safe_failure(seed_engine: Engine) -> None:
    def fail(context: SeedContext) -> SeedMutation:
        context.session.add(
            ModuleDefinition(
                code="must_rollback",
                name="Rollback",
                short_description="Rollback",
                category="test",
                monthly_price=0,
                setup_price=0,
                currency="IRR",
                dependencies=[],
                default_limits={},
                availability="ready",
                is_sellable=False,
                sort_order=999,
            )
        )
        context.session.flush()
        raise RuntimeError("sensitive internal detail")

    registry = SeedRegistry()
    registry.register(_definition("test.rollback", fail))
    with pytest.raises(SeedExecutionError, match="rolled back"):
        SeedRunner(seed_engine, registry).run("test")
    with Session(seed_engine) as session:
        assert session.get(ModuleDefinition, "must_rollback") is None
        history = session.scalar(select(SeedHistory).where(SeedHistory.seed_name == "test.rollback"))
        assert history is not None
        assert history.status == "failed"
        assert history.summary == {"error_type": "RuntimeError"}


def test_failure_report_preserves_completed_seed_results(seed_engine: Engine) -> None:
    def fail(_: SeedContext) -> SeedMutation:
        raise RuntimeError("failure")

    registry = SeedRegistry()
    registry.register(_definition("test.first", _unchanged, order=10))
    registry.register(_definition("test.failure", fail, order=20))
    with pytest.raises(SeedExecutionError) as captured:
        SeedRunner(seed_engine, registry).run("test")
    report = captured.value.report
    assert report is not None
    assert [result.status for result in report.results] == [
        SeedStatus.UNCHANGED,
        SeedStatus.FAILED,
    ]
    assert report.counts["unchanged"] == 1
    assert report.counts["failed"] == 1


def test_seed_history_redacts_sensitive_summary_fields(seed_engine: Engine) -> None:
    def safe_result(_: SeedContext) -> SeedMutation:
        return SeedMutation(
            status=SeedStatus.UNCHANGED,
            unchanged=1,
            summary={"api_token": "must-not-persist", "safe_count": 1},
        )

    registry = SeedRegistry()
    registry.register(_definition("test.safe_summary", safe_result))
    SeedRunner(seed_engine, registry).run("test")
    with Session(seed_engine) as session:
        history = session.scalar(
            select(SeedHistory).where(SeedHistory.seed_name == "test.safe_summary")
        )
        assert history is not None
        assert history.summary["api_token"] == "[redacted]"
        assert history.summary["safe_count"] == 1


def test_tenant_seed_for_alpha_does_not_modify_beta(seed_engine: Engine) -> None:
    alpha = _create_store(seed_engine, "alpha")
    beta = _create_store(seed_engine, "beta")
    runner = SeedRunner(seed_engine, default_registry())
    runner.run("production", seed_names=("system.module_definitions",))
    with Session(seed_engine) as session, session.begin():
        session.add(
            StoreModule(
                store_id=beta.id,
                module_code="sales_agent_core",
                status="active",
                currency="IRR",
                billing_interval="month",
                limits_json={"manager_owned": 1},
                source="manual",
            )
        )
    runner.run(
        "production",
        tenant_slug="alpha",
        seed_names=("tenant.module_entitlements",),
    )
    with Session(seed_engine) as session:
        alpha_rows = list(session.scalars(select(StoreModule).where(StoreModule.store_id == alpha.id)))
        beta_rows = list(session.scalars(select(StoreModule).where(StoreModule.store_id == beta.id)))
        assert len(alpha_rows) > 1
        assert len(beta_rows) == 1
        assert beta_rows[0].status == "active"
        assert beta_rows[0].limits_json == {"manager_owned": 1}


def test_named_seed_selection_and_invalid_name(seed_engine: Engine) -> None:
    runner = SeedRunner(seed_engine, default_registry())
    report = runner.run("test", seed_names=("system.module_definitions",))
    assert [result.seed_name for result in report.results] == ["system.module_definitions"]
    with pytest.raises(SeedValidationError, match="unknown seed name"):
        runner.run("test", seed_names=("missing.seed",))


def test_cli_list_does_not_open_or_mutate_a_database(monkeypatch, capsys) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("--list must not create an engine")

    monkeypatch.setattr(seed_data, "create_engine", forbidden)
    assert seed_data.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "system.module_definitions" in output
    assert "tenant.module_entitlements" in output


def test_cli_exit_codes_and_successful_explicit_database(seed_engine: Engine, capsys) -> None:
    url = str(seed_engine.url)
    assert seed_data.main([]) == 2
    assert seed_data.main(["--profile", "unknown", "--database-url", url]) == 2
    assert seed_data.main(
        [
            "--profile",
            "test",
            "--database-url",
            url,
            "--seed",
            "missing.seed",
        ]
    ) == 2
    assert seed_data.main(
        [
            "--profile",
            "test",
            "--database-url",
            url,
            "--seed",
            "system.module_definitions",
        ]
    ) == 0
    assert "Seed summary:" in capsys.readouterr().out


def test_explicit_database_does_not_modify_configured_application_database(
    seed_engine: Engine, tmp_path: Path, monkeypatch
) -> None:
    protected_path = tmp_path / "protected.db"
    protected_engine = create_engine(f"sqlite:///{protected_path.as_posix()}")
    with protected_engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE protected_marker (id INTEGER PRIMARY KEY)")
    protected_engine.dispose()
    before = protected_path.read_bytes()
    monkeypatch.setattr(
        seed_data,
        "get_settings",
        lambda: SimpleNamespace(database_url=f"sqlite:///{protected_path.as_posix()}"),
    )
    assert seed_data.main(
        [
            "--profile",
            "test",
            "--database-url",
            str(seed_engine.url),
            "--seed",
            "system.module_definitions",
        ]
    ) == 0
    assert protected_path.read_bytes() == before


def test_seed_history_migration_upgrades_and_downgrades(seed_engine: Engine) -> None:
    database_path = Path(seed_engine.url.database)
    seed_engine.dispose()
    config = _config(database_path)
    command.downgrade(config, "0001_baseline_schema")
    downgraded = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "seed_history" not in inspect(downgraded).get_table_names()
    downgraded.dispose()
    command.upgrade(config, "head")
    upgraded = create_engine(f"sqlite:///{database_path.as_posix()}")
    assert "seed_history" in inspect(upgraded).get_table_names()
    upgraded.dispose()


def test_migration_graph_still_has_exactly_one_head() -> None:
    from alembic.script import ScriptDirectory

    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert scripts.get_heads() == ["0003_authorization_rbac"]


def test_application_startup_does_not_seed_data(tmp_path: Path, monkeypatch) -> None:
    from app import main

    startup_engine = create_engine(f"sqlite:///{(tmp_path / 'startup.db').as_posix()}")
    monkeypatch.setattr(main, "engine", startup_engine)
    with TestClient(main.app) as client:
        assert client.get("/health").status_code == 200
    with Session(startup_engine) as session:
        assert session.scalar(select(func.count()).select_from(ModuleDefinition)) == 0
        assert session.scalar(select(func.count()).select_from(Store)) == 0
    startup_engine.dispose()


def test_public_gateway_startup_does_not_seed_data(tmp_path: Path, monkeypatch) -> None:
    from app import public_instagram_gateway

    startup_engine = create_engine(f"sqlite:///{(tmp_path / 'gateway.db').as_posix()}")
    monkeypatch.setattr(public_instagram_gateway, "engine", startup_engine)
    with TestClient(public_instagram_gateway.app):
        pass
    with Session(startup_engine) as session:
        assert session.scalar(select(func.count()).select_from(ModuleDefinition)) == 0
        assert session.scalar(select(func.count()).select_from(Store)) == 0
    startup_engine.dispose()


def test_production_admin_read_does_not_repair_missing_seed_data(seed_engine: Engine) -> None:
    from app.admin_modules import _ensure_catalog_and_legacy_store

    with Session(seed_engine) as session:
        with pytest.raises(HTTPException) as captured:
            _ensure_catalog_and_legacy_store(
                session,
            )
        assert captured.value.status_code == 503
        assert session.scalar(select(func.count()).select_from(ModuleDefinition)) == 0
        assert session.scalar(select(func.count()).select_from(Store)) == 0
