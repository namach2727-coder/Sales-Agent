from datetime import UTC, datetime, timedelta
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.ai_assistant.service import (
    AIAssistantConflict,
    AIAssistantService,
    AIRequestQuotaExceeded,
    AIRequestQuotaService,
    _quota_lock_statement,
    ai_is_enabled,
)
from app.database import Base
from app.models import ModuleDefinition, SaasPlan, Store, Tenant, TenantSubscription


@pytest.fixture()
def engine():
    value = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(value)
    return value


def _scope(
    db: Session,
    *,
    family: str = "AI_ASSISTANT",
    request_limit: int | None = 10,
) -> tuple[Tenant, Store]:
    suffix = uuid.uuid4().hex
    tenant = Tenant(name="AI Tenant", slug=f"ai-{suffix}", status="active")
    db.add(tenant); db.flush()
    store = Store(tenant_id=tenant.id, name="AI Store", slug=f"ai-store-{suffix}", status="active")
    db.add(store); db.flush()
    for code, dependencies in (("knowledge_base", []), ("ai_assistant", ["knowledge_base"])):
        if db.get(ModuleDefinition, code) is None:
            db.add(ModuleDefinition(code=code, name=code, short_description=code, dependencies=dependencies, is_sellable=False))
    plan = SaasPlan(code=f"AI_{suffix.upper()}", name=family, product_family=family, price_amount=0, currency="IRR", duration_days=30, billing_unit="day", automation_limit=0, reply_limit=0, instagram_account_limit=1, ai_request_limit=request_limit, ai_token_limit=1000, is_active=True, is_purchasable=False, trial_eligible=False, module_codes=["ai_assistant", "knowledge_base"])
    db.add(plan); db.flush()
    now = datetime.now(UTC)
    limits = {"ai_token_limit": 1000}
    if request_limit is not None:
        limits["ai_request_limit"] = request_limit
    db.add(TenantSubscription(tenant_id=tenant.id, store_id=store.id, plan_id=plan.id, product_family=family, source="ADMIN_GRANT", status="active", limits_json=limits, starts_at=now, current_period_end=now + timedelta(days=30)))
    db.commit()
    return tenant, store


def test_ai_state_is_revisioned_and_defaults_enabled(engine) -> None:
    with Session(engine) as db:
        tenant, store = _scope(db)
        service = AIAssistantService(db, tenant_id=tenant.id, store_id=store.id)
        assert service.read().ai_enabled is True
        assert ai_is_enabled(db, tenant_id=tenant.id, store_id=store.id) is True
        updated = service.update(enabled=False, expected_revision=1)
        assert updated.ai_enabled is False and updated.ai_revision == 2
        assert ai_is_enabled(db, tenant_id=tenant.id, store_id=store.id) is False
        with pytest.raises(AIAssistantConflict):
            service.update(enabled=True, expected_revision=1)


def test_usage_uses_subscription_snapshot_and_exposes_no_provider_config(engine) -> None:
    with Session(engine) as db:
        tenant, store = _scope(db)
        usage = AIAssistantService(db, tenant_id=tenant.id, store_id=store.id).usage()
        assert usage.request_count == 0
        assert usage.request_limit == 10
        assert usage.token_limit == 1000
        assert not any(key in usage.__slots__ for key in ("provider", "model", "api_key"))


def test_ai_state_is_store_scoped(engine) -> None:
    with Session(engine) as db:
        tenant, store = _scope(db)
        other = Store(tenant_id=tenant.id, name="Other", slug="other", status="active")
        db.add(other); db.commit()
        assert ai_is_enabled(db, tenant_id=tenant.id, store_id=other.id) is True
        assert ai_is_enabled(db, tenant_id=tenant.id + 999, store_id=store.id) is False


def test_zero_request_limit_blocks_and_null_limit_is_unlimited(engine) -> None:
    with Session(engine) as db:
        tenant, store = _scope(db, request_limit=0)
        with pytest.raises(AIRequestQuotaExceeded):
            AIRequestQuotaService(db).ensure_available(
                tenant_id=tenant.id,
                store_id=store.id,
            )

    with Session(engine) as db:
        tenant, store = _scope(db, request_limit=None)
        summary = AIRequestQuotaService(db).ensure_available(
            tenant_id=tenant.id,
            store_id=store.id,
        )
        assert summary.request_limit is None


def test_quota_lock_is_stable_and_uses_postgres_for_update() -> None:
    compiled = str(
        _quota_lock_statement([3, 1]).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "ORDER BY tenant_subscriptions.id" in compiled
    assert compiled.endswith("FOR UPDATE")
