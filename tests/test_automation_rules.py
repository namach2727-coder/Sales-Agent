from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.authentication.router import router as auth_router
from app.automation_rules.models import AutomationRule
from app.automation_rules.router import router as rules_router
from app.commerce.router import router as commerce_router
from app.database import get_db
from app.models import SaasPlan, TenantSubscription
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


@pytest.fixture
def rules_api(tmp_path: Path):
    database = tmp_path / "rules.db"
    url = f"sqlite:///{database.as_posix()}"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    engine = create_engine(url)
    SeedRunner(engine, default_registry()).run("test")
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(commerce_router)
    app.include_router(rules_router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def customer(client: TestClient, suffix: str) -> tuple[dict[str, str], dict]:
    created = client.post("/api/v1/auth/register", json={
        "email": f"rules-{suffix}@example.com", "password": PASSWORD,
        "display_name": "Rule Owner", "tenant_name": f"Tenant {suffix}",
        "tenant_slug": f"rules-tenant-{suffix}", "store_name": f"Store {suffix}",
        "store_slug": f"rules-store-{suffix}",
    })
    assert created.status_code == 201, created.text
    login = client.post("/api/v1/auth/login", json={
        "email": f"rules-{suffix}@example.com", "password": PASSWORD,
    })
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, created.json()


def route(scope: dict, rule_id: str = "") -> str:
    base = f"/api/v1/tenants/{scope['tenant_public_id']}/stores/{scope['store_public_id']}/automation-rules"
    return f"{base}/{rule_id}" if rule_id else base


def payload(trigger: str = "DM_KEYWORD", *, expected_revision: int = 0) -> dict:
    return {
        "expected_revision": expected_revision,
        "name": f"{trigger} rule",
        "enabled": True,
        "trigger_type": trigger,
        "match_type": "CONTAINS",
        "keywords": [" قیمت ", "موجودی"],
        "action_type": "SEND_PRIVATE_MESSAGE" if trigger == "COMMENT_KEYWORD" else "SEND_MESSAGE",
        "action_payload": {"text": " پاسخ قطعی فروشگاه "},
        "priority": 100,
    }


@pytest.mark.parametrize("trigger", ["DM_KEYWORD", "STORY_REPLY_KEYWORD", "COMMENT_KEYWORD"])
def test_valid_trigger_rules_create_with_clean_data_and_revision(rules_api, trigger: str) -> None:
    client, _ = rules_api
    headers, scope = customer(client, trigger.lower().replace("_", "-"))
    response = client.post(route(scope), headers=headers, json=payload(trigger))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["revision"] == 1
    assert body["keywords"] == ["قیمت", "موجودی"]
    assert body["action_payload"] == {"text": "پاسخ قطعی فروشگاه"}


@pytest.mark.parametrize("field,value", [
    ("trigger_type", "REGEX"), ("match_type", "REGEX"),
    ("keywords", []), ("keywords", ["  "]),
    ("action_payload", {"text": "  "}), ("priority", -1), ("priority", 10001),
])
def test_invalid_rule_input_is_rejected(rules_api, field: str, value) -> None:
    client, _ = rules_api
    case_number = ["trigger_type", "match_type", "keywords", "keywords", "action_payload", "priority", "priority"].index(field)
    headers, scope = customer(client, f"invalid-{field.replace('_', '-')}-{case_number}")
    data = payload()
    data[field] = value
    assert client.post(route(scope), headers=headers, json=data).status_code == 422


def test_invalid_trigger_action_combination_is_rejected(rules_api) -> None:
    client, _ = rules_api
    headers, scope = customer(client, "combo")
    data = payload("COMMENT_KEYWORD")
    data["action_type"] = "SEND_MESSAGE"
    assert client.post(route(scope), headers=headers, json=data).status_code == 422


def test_crud_revision_pagination_and_limit(rules_api) -> None:
    client, engine = rules_api
    headers, scope = customer(client, "crud")
    created = [client.post(route(scope), headers=headers, json=payload()).json() for _ in range(3)]
    listing = client.get(route(scope), headers=headers, params={"page": 1, "page_size": 2})
    assert listing.status_code == 200
    assert listing.json()["total"] == 3 and len(listing.json()["items"]) == 2
    item = client.get(route(scope, created[0]["public_id"]), headers=headers)
    assert item.status_code == 200
    changed = client.patch(route(scope, created[0]["public_id"]), headers=headers, json={
        "expected_revision": 1, "name": "Updated", "enabled": False, "priority": 200,
    })
    assert changed.status_code == 200 and changed.json()["revision"] == 2
    stale = client.patch(route(scope, created[0]["public_id"]), headers=headers, json={"expected_revision": 1, "name": "stale"})
    assert stale.status_code == 409
    limit = client.post(route(scope), headers=headers, json=payload())
    assert limit.status_code == 409 and limit.json()["detail"]["code"] == "automation_limit_reached"
    assert client.delete(route(scope, created[0]["public_id"]), headers=headers, params={"expected_revision": 2}).status_code == 204
    replacement = client.post(route(scope), headers=headers, json=payload())
    assert replacement.status_code == 201
    with Session(engine) as db:
        assert db.scalar(select(AutomationRule).where(AutomationRule.public_id == created[0]["public_id"])) is None


def test_tenant_and_store_isolation_fail_closed(rules_api) -> None:
    client, _ = rules_api
    headers_a, scope_a = customer(client, "isolation-a")
    headers_b, scope_b = customer(client, "isolation-b")
    rule = client.post(route(scope_a), headers=headers_a, json=payload()).json()
    assert client.get(route(scope_a, rule["public_id"]), headers=headers_b).status_code == 404
    assert client.get(route(scope_b, rule["public_id"]), headers=headers_a).status_code == 404
    assert client.patch(route(scope_a, rule["public_id"]), headers=headers_b, json={"expected_revision": 1, "name": "foreign"}).status_code == 404
    assert client.delete(route(scope_a, rule["public_id"]), headers=headers_b, params={"expected_revision": 1}).status_code == 404


def test_missing_capability_denies_management_without_deleting_rules(rules_api) -> None:
    client, engine = rules_api
    headers, scope = customer(client, "downgrade")
    rule = client.post(route(scope), headers=headers, json=payload()).json()
    with Session(engine) as db, db.begin():
        subscription = db.scalar(select(TenantSubscription).order_by(TenantSubscription.id.desc()))
        assert subscription is not None
        plan = db.get(SaasPlan, subscription.plan_id)
        assert plan is not None
        plan.module_codes = ["knowledge_base", "ai_assistant"]
    assert client.get(route(scope), headers=headers).status_code == 403
    assert client.patch(route(scope, rule["public_id"]), headers=headers, json={"expected_revision": 1, "name": "blocked"}).status_code == 403
    assert client.delete(route(scope, rule["public_id"]), headers=headers, params={"expected_revision": 1}).status_code == 403
    with Session(engine) as db:
        assert db.scalar(select(AutomationRule).where(AutomationRule.public_id == rule["public_id"])) is not None


def test_phase_b_crud_has_no_ai_or_instagram_runtime_dependency() -> None:
    source = "\n".join(
        (ROOT / "app" / "automation_rules" / name).read_text(encoding="utf-8")
        for name in ("models.py", "schemas.py", "service.py", "router.py")
    ).lower()
    for forbidden in ("promptbuilder", "knowledgeengine", "groq", "openai", "ollama", "instagramgraphsender"):
        assert forbidden not in source
