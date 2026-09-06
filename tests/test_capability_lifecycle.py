from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    ModuleDefinition,
    SaasPlan,
    Store,
    StoreModule,
    SubscriptionOrder,
    Tenant,
    TenantSubscription,
)
from app.module_catalog import effective_capabilities, has_capability


CAPABILITIES = {
    "instagram_automation",
    "knowledge_base",
    "ai_assistant",
}


@pytest.fixture
def capability_db(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'capabilities.db').as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as db, db.begin():
        tenant = Tenant(name="Tenant", slug="capability-tenant", status="active")
        other_tenant = Tenant(
            name="Other Tenant", slug="other-capability-tenant", status="active"
        )
        db.add_all((tenant, other_tenant))
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Store",
            slug="capability-store",
            status="active",
        )
        other_store = Store(
            tenant_id=tenant.id,
            name="Other Store",
            slug="other-capability-store",
            status="active",
        )
        db.add_all((store, other_store))
        db.flush()
        for code in sorted(CAPABILITIES):
            db.add(
                ModuleDefinition(
                    code=code,
                    name=code,
                    short_description=code,
                    category="sales",
                    monthly_price=0,
                    currency="IRR",
                    dependencies=["knowledge_base"] if code == "ai_assistant" else [],
                    default_limits={},
                    availability="ready",
                    is_sellable=False,
                )
            )
            db.add(
                StoreModule(
                    store_id=store.id,
                    module_code=code,
                    status="active",
                    currency="IRR",
                    source="subscription",
                )
            )
        plans = {
            "TRIAL": CAPABILITIES,
            "START": {"instagram_automation"},
            "PRO": CAPABILITIES,
        }
        for code, module_codes in plans.items():
            db.add(
                SaasPlan(
                    code=code,
                    name=code.title(),
                    price_amount=0 if code == "TRIAL" else 1,
                    currency="IRR",
                    reply_limit=1,
                    automation_limit=1,
                    instagram_account_limit=1,
                    duration_days=14 if code == "TRIAL" else 30,
                    module_codes=sorted(module_codes),
                    is_active=True,
                )
            )
    try:
        yield engine
    finally:
        engine.dispose()


def _activate(
    db: Session,
    *,
    tenant_id: int,
    store_id: int,
    plan_code: str,
    starts_at: datetime,
    current_period_end: datetime | None = None,
) -> TenantSubscription:
    plan = db.query(SaasPlan).filter_by(code=plan_code).one()
    order = SubscriptionOrder(
        tenant_id=tenant_id,
        store_id=store_id,
        user_id=1,
        plan_id=plan.id,
        status="paid",
        price_amount=plan.price_amount,
        currency="IRR",
    )
    db.add(order)
    db.flush()
    subscription = TenantSubscription(
        tenant_id=tenant_id,
        store_id=store_id,
        plan_id=plan.id,
        order_id=order.id,
        status="active",
        limits_json={},
        starts_at=starts_at,
        current_period_end=current_period_end or starts_at + timedelta(days=30),
    )
    db.add(subscription)
    db.flush()
    return subscription


@pytest.mark.parametrize(
    ("plan_code", "expected"),
    (
        ("TRIAL", CAPABILITIES),
        ("START", {"instagram_automation"}),
        ("PRO", CAPABILITIES),
    ),
)
def test_plan_capabilities_are_effective(capability_db, plan_code, expected):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code=plan_code,
            starts_at=now,
        )
        assert set(
            effective_capabilities(
                db, tenant_id=tenant.id, store_id=store.id, now=now
            )
        ) == expected


def test_latest_subscription_controls_upgrade_and_downgrade(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now - timedelta(days=2),
        )
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="START",
            starts_at=now - timedelta(days=1),
        )
        assert set(
            effective_capabilities(
                db, tenant_id=tenant.id, store_id=store.id, now=now
            )
        ) == {"instagram_automation"}

        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now,
        )
        assert set(
            effective_capabilities(
                db, tenant_id=tenant.id, store_id=store.id, now=now
            )
        ) == CAPABILITIES


def test_expired_latest_subscription_fails_closed(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now - timedelta(days=10),
            current_period_end=now - timedelta(days=1),
        )
        assert effective_capabilities(
            db, tenant_id=tenant.id, store_id=store.id, now=now
        ) == ()


def test_stale_store_module_cannot_grant_unpurchased_capability(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="START",
            starts_at=now,
        )
        assert not has_capability(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            capability_code="knowledge_base",
            now=now,
        )


def test_store_module_and_definition_state_fail_closed(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now,
        )
        knowledge = db.query(StoreModule).filter_by(
            store_id=store.id, module_code="knowledge_base"
        ).one()
        knowledge.status = "inactive"
        assert set(
            effective_capabilities(
                db, tenant_id=tenant.id, store_id=store.id, now=now
            )
        ) == {"instagram_automation"}

        automation = db.get(ModuleDefinition, "instagram_automation")
        assert automation is not None
        automation.availability = "planned"
        assert not has_capability(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            capability_code="instagram_automation",
            now=now,
        )


def test_capability_dependency_must_be_granted_by_effective_plan(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        plan = db.query(SaasPlan).filter_by(code="PRO").one()
        plan.module_codes = ["instagram_automation", "ai_assistant"]
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now,
        )
        assert set(
            effective_capabilities(
                db, tenant_id=tenant.id, store_id=store.id, now=now
            )
        ) == {"instagram_automation"}


def test_capabilities_are_tenant_and_store_scoped(capability_db):
    now = datetime.now(UTC)
    with Session(capability_db) as db, db.begin():
        tenant = db.query(Tenant).filter_by(slug="capability-tenant").one()
        other_tenant = db.query(Tenant).filter_by(slug="other-capability-tenant").one()
        store = db.query(Store).filter_by(slug="capability-store").one()
        other_store = db.query(Store).filter_by(slug="other-capability-store").one()
        _activate(
            db,
            tenant_id=tenant.id,
            store_id=store.id,
            plan_code="PRO",
            starts_at=now,
        )
        assert effective_capabilities(
            db, tenant_id=other_tenant.id, store_id=store.id, now=now
        ) == ()
        assert effective_capabilities(
            db, tenant_id=tenant.id, store_id=other_store.id, now=now
        ) == ()
