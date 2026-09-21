from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

import conftest
from app.commerce.router import admin_commerce_customers
from app.database import engine
from app.models import (
    ModuleDefinition,
    SaasPlan,
    Store,
    StoreModule,
    Tenant,
    TenantSubscription,
)


pytestmark = pytest.mark.skipif(
    not conftest.POSTGRES_TEST_ENABLED,
    reason="requires an explicitly configured disposable PostgreSQL test database",
)


def test_admin_customer_queries_remain_constant_on_postgresql() -> None:
    measurements: list[dict[str, float | int]] = []
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(bind=connection) as db:
                for code, dependencies in (
                    ("instagram_automation", []),
                    ("knowledge_base", []),
                    ("ai_assistant", ["knowledge_base"]),
                ):
                    if db.get(ModuleDefinition, code) is None:
                        db.add(
                            ModuleDefinition(
                                code=code,
                                name=code,
                                short_description="Synthetic performance fixture",
                                dependencies=dependencies,
                                availability="ready",
                                is_sellable=False,
                            )
                        )
                plan = SaasPlan(
                    code="SYNTHETIC_ADMIN_CUSTOMERS",
                    name="Synthetic Admin Customers",
                    product_family="LEGACY_BUNDLE",
                    module_codes=[
                        "instagram_automation",
                        "knowledge_base",
                        "ai_assistant",
                    ],
                    is_active=True,
                    is_purchasable=False,
                )
                db.add(plan)
                db.flush()
                now = datetime.now(UTC)

                def seed_customers(target: int) -> None:
                    for number in range(target):
                        tenant = Tenant(
                            name=f"000 Synthetic Tenant {number:04d}",
                            slug=f"synthetic-tenant-{number:04d}",
                            status="active",
                        )
                        db.add(tenant)
                        db.flush()
                        store = Store(
                            tenant_id=tenant.id,
                            name=f"Synthetic Store {number:04d}",
                            slug=f"synthetic-store-{number:04d}",
                            status="active",
                        )
                        db.add(store)
                        db.flush()
                        db.add(
                            TenantSubscription(
                                tenant_id=tenant.id,
                                store_id=store.id,
                                plan_id=plan.id,
                                product_family="LEGACY_BUNDLE",
                                source="ADMIN_GRANT",
                                status="active",
                                limits_json={},
                                starts_at=now - timedelta(days=1),
                                current_period_end=now + timedelta(days=30),
                            )
                        )
                        db.add_all(
                            StoreModule(
                                store_id=store.id,
                                module_code=code,
                                status="active",
                            )
                            for code in (
                                "instagram_automation",
                                "knowledge_base",
                                "ai_assistant",
                            )
                        )
                    db.flush()

                seed_customers(100)
                for size in (1, 10, 100):
                    db.expunge_all()
                    query_count = 0

                    def count_query(*_args: object) -> None:
                        nonlocal query_count
                        query_count += 1

                    event.listen(connection, "before_cursor_execute", count_query)
                    started = time.perf_counter()
                    try:
                        result = admin_commerce_customers(
                            page=1,
                            page_size=size,
                            _principal=None,  # type: ignore[arg-type]
                            db=db,
                        )
                    finally:
                        elapsed_ms = (time.perf_counter() - started) * 1000
                        event.remove(
                            connection, "before_cursor_execute", count_query
                        )
                    assert len(result) == size
                    assert query_count <= 15
                    measurements.append(
                        {
                            "customers": size,
                            "query_count": query_count,
                            "elapsed_ms": round(elapsed_ms, 2),
                        }
                    )
        finally:
            transaction.rollback()

    assert [item["query_count"] for item in measurements] == [5, 5, 5]
    print("ADMIN_CUSTOMER_QUERY_SCALING=" + json.dumps(measurements))
