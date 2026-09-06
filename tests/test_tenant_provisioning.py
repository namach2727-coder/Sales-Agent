from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import (
    AdminAuditLog,
    ModuleDefinition,
    SeedHistory,
    Store,
    StoreModule,
    TenantMembership,
)
from app.module_catalog import MODULE_SEEDS
from app.provisioning import (
    ProvisioningConflictError,
    ProvisioningExecutionError,
    ProvisioningTransactionError,
    ProvisioningValidationError,
    TenantProvisioningRequest,
    TenantProvisioningService,
)
from app.provisioning.models import ProvisioningStatus
from tools import provision_tenant
from tools.seeding import SeedExecutionError


ROOT = Path(__file__).resolve().parents[1]


def _config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


@pytest.fixture
def provisioning_engine(tmp_path: Path) -> Engine:
    path = tmp_path / "provisioning.db"
    command.upgrade(_config(path), "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    yield engine
    engine.dispose()


def _request(
    *,
    name: str = "Example Store",
    slug: str = "example-store",
    profile: str = "test",
    modules: tuple[str, ...] = (),
) -> TenantProvisioningRequest:
    return TenantProvisioningRequest(
        name=name,
        slug=slug,
        profile=profile,
        requested_module_codes=modules,
    )


def _provision(engine: Engine, request: TenantProvisioningRequest, **kwargs):
    with Session(engine, expire_on_commit=False) as session:
        return TenantProvisioningService(session, **kwargs).provision(request)


def test_valid_provisioning_is_atomic_audited_and_tenant_scoped(
    provisioning_engine: Engine,
) -> None:
    result = _provision(provisioning_engine, _request())
    assert result.status is ProvisioningStatus.SUCCEEDED
    assert result.tenant_status == "active"
    assert result.seed_names == (
        "system.module_definitions",
        "tenant.module_entitlements",
    )
    assert result.completed_steps == (
        "validate_identity",
        "create_tenant",
        "establish_tenant_context",
        "run_tenant_seeds",
        "configure_modules",
        "verify_tenant",
        "finalize_tenant",
        "record_audit",
    )
    with Session(provisioning_engine) as session:
        store = session.scalar(select(Store).where(Store.slug == "example-store"))
        assert store is not None and store.status == "active"
        definition_count = session.scalar(select(func.count()).select_from(ModuleDefinition))
        rows = list(
            session.scalars(select(StoreModule).where(StoreModule.store_id == store.id))
        )
        assert len(rows) == definition_count == len(MODULE_SEEDS)
        assert all(row.store_id == store.id and row.status == "inactive" for row in rows)
        history = list(session.scalars(select(SeedHistory).order_by(SeedHistory.id)))
        assert [row.tenant_id for row in history] == [None, store.id]
        audit = session.scalar(
            select(AdminAuditLog).where(AdminAuditLog.action == "tenant_provisioned")
        )
        assert audit is not None
        assert audit.details_json["operation_id"] == result.operation_id
        assert session.scalar(select(func.count()).select_from(TenantMembership)) == 0


def test_slug_is_trimmed_and_lowercased(provisioning_engine: Engine) -> None:
    result = _provision(provisioning_engine, _request(slug="  Mixed-Case  "))
    assert result.tenant_slug == "mixed-case"


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "bad_slug",
        "-leading",
        "trailing-",
        "duplicate--separator",
        "a" * 64,
        "admin",
        "api",
        "auth",
        "openapi",
        "internal",
    ],
)
def test_invalid_or_reserved_slugs_fail_without_writes(
    provisioning_engine: Engine, slug: str
) -> None:
    with pytest.raises(ProvisioningValidationError):
        _provision(provisioning_engine, _request(slug=slug))
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 0
        assert session.scalar(select(func.count()).select_from(ModuleDefinition)) == 0


def test_duplicate_and_case_insensitive_duplicate_are_conflicts(
    provisioning_engine: Engine,
) -> None:
    _provision(provisioning_engine, _request(slug="alpha"))
    with pytest.raises(ProvisioningConflictError):
        _provision(provisioning_engine, _request(slug=" ALPHA "))
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 1


def test_database_unique_race_is_translated_and_rolled_back(
    provisioning_engine: Engine,
) -> None:
    def insert_competitor(context) -> None:
        context.session.add(
            Store(name="Concurrent Store", slug=context.request.slug, status="active")
        )
        context.session.flush()

    with Session(provisioning_engine) as session:
        service = TenantProvisioningService(
            session, step_overrides={"validate_identity": insert_competitor}
        )
        with pytest.raises(ProvisioningConflictError):
            service.provision(_request(slug="race-store"))
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 0


def test_service_rejects_ambiguous_outer_transaction_ownership(
    provisioning_engine: Engine,
) -> None:
    with Session(provisioning_engine) as session, session.begin():
        with pytest.raises(ProvisioningTransactionError):
            TenantProvisioningService(session).provision(_request())


def test_unknown_profile_module_and_duplicate_modules_are_rejected(
    provisioning_engine: Engine,
) -> None:
    invalid = (
        _request(profile="staging"),
        _request(slug="unknown-module", modules=("missing",)),
        _request(slug="duplicate-module", modules=("sales_agent_core", "sales_agent_core")),
        _request(slug="planned-module", modules=("analytics",)),
    )
    for request in invalid:
        with pytest.raises(ProvisioningValidationError):
            _provision(provisioning_engine, request)
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 0


def test_requested_modules_activate_with_dependencies(provisioning_engine: Engine) -> None:
    result = _provision(
        provisioning_engine,
        _request(modules=("comments_to_dm",)),
    )
    assert result.module_codes == ("comments_to_dm", "sales_agent_core")
    with Session(provisioning_engine) as session:
        store = session.scalar(select(Store).where(Store.slug == "example-store"))
        rows = {
            row.module_code: row
            for row in session.scalars(
                select(StoreModule).where(StoreModule.store_id == store.id)
            )
        }
        assert rows["comments_to_dm"].status == "active"
        assert rows["sales_agent_core"].status == "active"
        assert rows["comments_to_dm"].source == "provisioning"


def test_provisioning_tenant_a_does_not_modify_tenant_b(
    provisioning_engine: Engine,
) -> None:
    beta = _provision(
        provisioning_engine,
        _request(slug="beta", modules=("sales_agent_core",)),
    )
    with Session(provisioning_engine) as session, session.begin():
        beta_core = session.scalar(
            select(StoreModule).where(
                StoreModule.store_id == beta.tenant_id,
                StoreModule.module_code == "sales_agent_core",
            )
        )
        beta_core.limits_json = {"manager_owned": 77}
    _provision(provisioning_engine, _request(slug="alpha"))
    with Session(provisioning_engine) as session:
        beta_rows = list(
            session.scalars(
                select(StoreModule).where(StoreModule.store_id == beta.tenant_id)
            )
        )
        assert len(beta_rows) == len(MODULE_SEEDS)
        beta_core = next(row for row in beta_rows if row.module_code == "sales_agent_core")
        assert beta_core.status == "active"
        assert beta_core.limits_json == {"manager_owned": 77}


def test_injected_step_failure_rolls_back_everything(
    provisioning_engine: Engine,
) -> None:
    def fail(context) -> None:
        context.session.add(
            StoreModule(
                store_id=context.tenant.id,
                module_code="sales_agent_core",
                status="active",
                currency="IRR",
                billing_interval="month",
                limits_json={},
                source="test",
            )
        )
        raise RuntimeError("intentional test failure")

    with Session(provisioning_engine) as session:
        service = TenantProvisioningService(
            session, step_overrides={"configure_modules": fail}
        )
        with pytest.raises(ProvisioningExecutionError) as captured:
            service.provision(_request())
        assert captured.value.failed_step == "configure_modules"
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 0
        assert session.scalar(select(func.count()).select_from(StoreModule)) == 0
        assert session.scalar(select(func.count()).select_from(SeedHistory)) == 0
        assert session.scalar(select(func.count()).select_from(AdminAuditLog)) == 0


def test_seed_failure_rolls_back_tenant_and_global_seed_changes(
    provisioning_engine: Engine,
) -> None:
    class FailingSeedRunner:
        def run_in_session(self, session, *args, **kwargs):
            session.add(
                ModuleDefinition(
                    code="temporary",
                    name="Temporary",
                    short_description="Temporary",
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
            session.flush()
            raise SeedExecutionError("test.failure", None)  # type: ignore[arg-type]

    with Session(provisioning_engine) as session:
        service = TenantProvisioningService(
            session, seed_runner=FailingSeedRunner()  # type: ignore[arg-type]
        )
        with pytest.raises(ProvisioningExecutionError):
            service.provision(_request())
    with Session(provisioning_engine) as session:
        assert session.scalar(select(func.count()).select_from(Store)) == 0
        assert session.get(ModuleDefinition, "temporary") is None


def test_dry_run_leaves_no_tenant_entitlement_seed_or_audit(
    provisioning_engine: Engine,
) -> None:
    with Session(provisioning_engine, expire_on_commit=False) as session:
        result = TenantProvisioningService(session).provision(
            _request(modules=("comments_to_dm",)), dry_run=True
        )
    assert result.status is ProvisioningStatus.PLANNED
    assert result.module_codes == ("comments_to_dm", "sales_agent_core")
    with Session(provisioning_engine) as session:
        for model in (Store, StoreModule, SeedHistory, AdminAuditLog, ModuleDefinition):
            assert session.scalar(select(func.count()).select_from(model)) == 0


def test_cli_success_validation_conflict_and_redaction(
    provisioning_engine: Engine, capsys
) -> None:
    url = str(provisioning_engine.url)
    base = [
        "--name",
        "CLI Store",
        "--slug",
        "cli-store",
        "--profile",
        "test",
        "--database-url",
        url,
    ]
    assert provision_tenant.main([*base, "--dry-run", "--json"]) == 0
    assert '"dry_run": true' in capsys.readouterr().out
    assert provision_tenant.main(base) == 0
    assert provision_tenant.main(base) == 3
    assert provision_tenant.main(
        [
            "--name",
            "Invalid",
            "--slug",
            "admin",
            "--profile",
            "test",
            "--database-url",
            url,
        ]
    ) == 2
    output = capsys.readouterr().out
    assert url not in output


def test_cli_never_reveals_database_credentials(capsys) -> None:
    secret = "must-not-appear"
    code = provision_tenant.main(
        [
            "--name",
            "Secure",
            "--slug",
            "secure",
            "--profile",
            "test",
            "--database-url",
            f"postgresql://user:{secret}@127.0.0.1:1/database",
        ]
    )
    assert code == 1
    assert secret not in capsys.readouterr().out
