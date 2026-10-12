"""Regression tests for safe, additive commercial-plan promotion."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic/versions/0024_ai_assistant_v1_catalog.py"
)


def _migration():
    spec = importlib.util.spec_from_file_location("ai_plan_catalog_migration", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _database(module):
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    metadata = sa.MetaData()
    fields = [
        sa.Column(column.name, column.type, unique=column.name == "code")
        for column in module._plan_table().columns
    ]
    table = sa.Table("saas_plans", metadata, sa.Column("id", sa.Integer, primary_key=True), *fields)
    metadata.create_all(engine)
    return engine, table


def test_ai_paid_plan_creation_is_idempotent_and_prices_are_server_side():
    module = _migration()
    engine, table = _database(module)
    with engine.begin() as conn:
        conn.execute(
            table.insert().values(
                code="AUTOMATION_V1",
                name="Automation",
                price_amount=4_900_000,
                module_codes=["instagram_automation"],
                is_purchasable=True,
            )
        )
        with patch.object(module.op, "get_bind", return_value=conn):
            module.upgrade()
            module.upgrade()
        rows = conn.execute(sa.select(table)).mappings().all()

    assert len(rows) == 2
    automation = next(row for row in rows if row["code"] == "AUTOMATION_V1")
    ai = next(row for row in rows if row["code"] == "AI_ASSISTANT_V1")
    assert automation["price_amount"] == 4_900_000
    assert automation["module_codes"] == ["instagram_automation"]
    assert ai["price_amount"] == 6_900_000
    assert ai["currency"] == "IRR"
    assert ai["duration_days"] == 30
    assert ai["ai_request_limit"] == 1_000
    assert ai["reply_limit"] == 1_000
    assert ai["module_codes"] == ["ai_assistant", "knowledge_base"]
    assert ai["product_family"] == "AI_ASSISTANT"
    assert ai["is_active"] is True
    assert ai["is_purchasable"] is True
    assert ai["trial_eligible"] is False


def test_ai_paid_plan_migration_never_overwrites_existing_admin_configuration():
    module = _migration()
    engine, table = _database(module)
    with engine.begin() as conn:
        conn.execute(
            table.insert().values(
                code="AI_ASSISTANT_V1",
                name="Admin-managed AI",
                price_amount=7_500_000,
                module_codes=["ai_assistant", "knowledge_base"],
                is_purchasable=False,
            )
        )
        with patch.object(module.op, "get_bind", return_value=conn):
            module.upgrade()
        rows = conn.execute(sa.select(table)).mappings().all()

    assert len(rows) == 1
    assert rows[0]["name"] == "Admin-managed AI"
    assert rows[0]["price_amount"] == 7_500_000
    assert rows[0]["is_purchasable"] is False


def test_downgrade_keeps_historical_commerce_data_untouched():
    module = _migration()
    engine, table = _database(module)
    with engine.begin() as conn:
        with patch.object(module.op, "get_bind", return_value=conn):
            module.upgrade()
            module.downgrade()
        assert conn.scalar(sa.select(sa.func.count()).select_from(table)) == 1
