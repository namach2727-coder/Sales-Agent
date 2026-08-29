import ast
import importlib.util
import runpy
import sys
from types import ModuleType
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect

from app.database import Base
from app import models  # noqa: F401 - registers metadata


ROOT = Path(__file__).resolve().parents[1]
POST_BASELINE_TABLES = {
    "seed_history",
    "auth_permissions",
    "auth_roles",
    "auth_role_permissions",
    "tenant_memberships",
    "auth_platform_role_assignments",
    "auth_tenant_role_assignments",
    "auth_audit_logs",
    "user_identities",
    "auth_sessions",
    "identity_audit_logs",
    "tenants",
    "store_access_assignments",
    "tenant_audit_logs",
    "catalog_attributes",
    "catalog_attribute_options",
    "catalog_brands",
    "catalog_categories",
    "catalog_media_assets",
    "catalog_tags",
    "catalog_brand_media",
    "catalog_category_media",
    "catalog_offerings",
    "catalog_product_attributes",
    "catalog_product_categories",
    "catalog_product_media",
    "catalog_product_tags",
    "catalog_variants",
    "catalog_skus",
    "catalog_variant_media",
    "catalog_variant_option_values",
    "catalog_sku_media",
    "catalog_store_availability",
    "catalog_store_prices",
    "business_profiles",
    "business_policies",
    "business_faqs",
    "business_knowledge_entries",
    "instagram_connections",
    "instagram_webhook_deliveries",
    "instagram_inbound_events",
    "conversations",
    "conversation_participants",
    "conversation_messages",
    "conversation_assignments",
    "conversation_read_states",
    "conversation_processing_records",
    "saas_plans",
    "subscription_orders",
    "manual_payments",
    "tenant_subscriptions",
    "commerce_audit_logs",
    "instagram_oauth_states",
}
BASELINE_TABLES = (
    set(Base.metadata.tables) - POST_BASELINE_TABLES - {"legacy_conversations"}
) | {"conversations"}
ALEMBIC_AVAILABLE = importlib.util.find_spec("alembic.config") is not None
requires_alembic = pytest.mark.skipif(
    not ALEMBIC_AVAILABLE,
    reason="Alembic is declared in requirements but unavailable in this environment",
)


def alembic_config(database_path: Path):
    from alembic.config import Config

    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config


def assignment_value(module: ast.Module, name: str):
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is not defined in baseline revision")


def test_baseline_source_remains_an_immutable_pre_seed_history_snapshot() -> None:
    source = ROOT / "alembic" / "versions" / "0001_baseline_schema.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    table_order = assignment_value(module, "TABLE_ORDER")
    indexes = assignment_value(module, "INDEXES")
    assert set(table_order) == BASELINE_TABLES
    assert len(table_order) == 25
    expected_indexes = {
        index.name
        for table_name in BASELINE_TABLES
        for table in (
            Base.metadata.tables[
                "legacy_conversations"
                if table_name == "conversations"
                else table_name
            ],
        )
        for index in table.indexes
    }
    expected_indexes -= {"ix_stores_public_id", "ix_stores_tenant_id"}
    expected_indexes.discard("ix_legacy_conversations_customer_id")
    expected_indexes.add("ix_conversations_customer_id")
    declared_indexes = {
        index_name
        for definitions in indexes.values()
        for index_name, _columns, _unique in definitions
    }
    assert declared_indexes == expected_indexes


def metadata_signature(
    metadata: sa.MetaData,
    table_names: set[str] | None = None,
) -> dict:
    result = {}
    for table_name, table in metadata.tables.items():
        if table_names is not None and table_name not in table_names:
            continue
        result[table_name] = {
            "columns": {
                column.name: (
                    str(column.type),
                    column.nullable,
                    column.primary_key,
                )
                for column in table.columns
            },
            "foreign_keys": {
                (
                    tuple(element.parent.name for element in constraint.elements),
                    tuple(element.target_fullname for element in constraint.elements),
                )
                for constraint in table.foreign_key_constraints
            },
            "unique": {
                (constraint.name, tuple(column.name for column in constraint.columns))
                for constraint in table.constraints
                if isinstance(constraint, sa.UniqueConstraint)
            },
            "indexes": {
                (
                    index.name,
                    tuple(column.name for column in index.columns),
                    index.unique,
                )
                for index in table.indexes
            },
        }
    return result


def test_baseline_operations_match_metadata_without_database(monkeypatch) -> None:
    class CaptureOperations:
        def __init__(self):
            self.metadata = sa.MetaData()

        def create_table(self, name, *elements):
            return sa.Table(name, self.metadata, *elements)

        def create_index(self, name, table_name, columns, unique=False):
            table = self.metadata.tables[table_name]
            sa.Index(name, *(table.c[column] for column in columns), unique=unique)

        def drop_index(self, name, *, table_name):
            table = self.metadata.tables[table_name]
            index = next(item for item in table.indexes if item.name == name)
            table.indexes.remove(index)

        def drop_table(self, name):
            self.metadata.remove(self.metadata.tables[name])

    operations = CaptureOperations()
    fake_alembic = ModuleType("alembic")
    fake_alembic.op = operations
    monkeypatch.setitem(sys.modules, "alembic", fake_alembic)
    namespace = runpy.run_path(
        str(ROOT / "alembic" / "versions" / "0001_baseline_schema.py")
    )
    namespace["upgrade"]()
    # The stores table is intentionally evolved by 0005; the immutable 0001
    # snapshot is still verified above and all unchanged baseline tables must
    # continue to match current metadata.
    unchanged = BASELINE_TABLES - {"stores", "conversations"}
    assert metadata_signature(operations.metadata, unchanged) == metadata_signature(
        Base.metadata, unchanged
    )
    namespace["downgrade"]()
    assert not operations.metadata.tables


@requires_alembic
def test_alembic_loads_with_one_linear_head() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["0014_transport_neutral_inbound"]
    baseline = scripts.get_revision("0001_baseline_schema")
    seed_history = scripts.get_revision("0002_create_seed_history")
    rbac = scripts.get_revision("0003_authorization_rbac")
    identity = scripts.get_revision("0004_authentication_identity")
    tenant_store = scripts.get_revision("0005_tenant_store_management")
    catalog = scripts.get_revision("0006_lean_business_catalog")
    knowledge = scripts.get_revision("0007_business_profile_knowledge")
    instagram = scripts.get_revision("0008_instagram_channel")
    conversations = scripts.get_revision("0009_conversation_core_models")
    commerce = scripts.get_revision("0010_saas_commerce")
    instagram_onboarding = scripts.get_revision("0011_instagram_oauth_onboarding")
    billing_duration = scripts.get_revision("0012_plan_billing_duration")
    store_automation = scripts.get_revision("0013_store_automation_control")
    head = scripts.get_revision("0014_transport_neutral_inbound")
    assert baseline is not None and baseline.down_revision is None
    assert seed_history is not None and seed_history.down_revision == "0001_baseline_schema"
    assert rbac is not None and rbac.down_revision == "0002_create_seed_history"
    assert identity is not None and identity.down_revision == "0003_authorization_rbac"
    assert tenant_store is not None and tenant_store.down_revision == "0004_authentication_identity"
    assert catalog is not None and catalog.down_revision == "0005_tenant_store_management"
    assert knowledge is not None and knowledge.down_revision == "0006_lean_business_catalog"
    assert instagram is not None and instagram.down_revision == "0007_business_profile_knowledge"
    assert conversations is not None and conversations.down_revision == "0008_instagram_channel"
    assert commerce is not None and commerce.down_revision == "0009_conversation_core_models"
    assert instagram_onboarding is not None and instagram_onboarding.down_revision == "0010_saas_commerce"
    assert billing_duration is not None and billing_duration.down_revision == "0011_instagram_oauth_onboarding"
    assert store_automation is not None and store_automation.down_revision == "0012_plan_billing_duration"
    assert head is not None and head.down_revision == "0013_store_automation_control"


@requires_alembic
def test_baseline_upgrade_matches_registered_metadata(tmp_path) -> None:
    from alembic import command

    database_path = tmp_path / "upgrade.db"
    config = alembic_config(database_path)
    command.upgrade(config, "head")

    inspector = inspect(create_engine(f"sqlite:///{database_path.as_posix()}"))
    expected_tables = set(Base.metadata.tables)
    assert set(inspector.get_table_names()) == expected_tables | {"alembic_version"}
    for table_name, table in Base.metadata.tables.items():
        actual_columns = {
            column["name"]: (column["nullable"], bool(column.get("primary_key")))
            for column in inspector.get_columns(table_name)
        }
        expected_columns = {
            column.name: (column.nullable, column.primary_key)
            for column in table.columns
        }
        assert actual_columns == expected_columns
        assert {item["name"] for item in inspector.get_indexes(table_name)} == {
            index.name for index in table.indexes
        }
        actual_fks = {
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
            )
            for item in inspector.get_foreign_keys(table_name)
        }
        expected_fks = {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.elements[0].column.table.name,
                tuple(element.column.name for element in constraint.elements),
            )
            for constraint in table.foreign_key_constraints
        }
        assert actual_fks == expected_fks


@requires_alembic
def test_migration_history_loads(tmp_path) -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    history = list(scripts.walk_revisions())
    assert [revision.revision for revision in history] == [
        "0014_transport_neutral_inbound",
        "0013_store_automation_control",
        "0012_plan_billing_duration",
        "0011_instagram_oauth_onboarding",
        "0010_saas_commerce",
        "0009_conversation_core_models",
        "0008_instagram_channel",
        "0007_business_profile_knowledge",
        "0006_lean_business_catalog",
        "0005_tenant_store_management",
        "0004_authentication_identity",
        "0003_authorization_rbac",
        "0002_create_seed_history",
        "0001_baseline_schema",
    ]


@requires_alembic
def test_upgrade_downgrade_upgrade_round_trip_uses_temporary_database(tmp_path) -> None:
    from alembic import command

    database_path = tmp_path / "round-trip.db"
    config = alembic_config(database_path)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    after_downgrade = set(
        inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names()
    )
    assert after_downgrade <= {"alembic_version"}
    command.upgrade(config, "head")
    final_tables = set(
        inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names()
    )
    assert set(Base.metadata.tables).issubset(final_tables)
