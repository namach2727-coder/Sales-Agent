from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.automation.router import router as automation_router
from app.business_knowledge.router import router as knowledge_router
from app.commerce.router import router as commerce_router
from app.config import Settings, get_settings
from app.conversation_core.models import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
)
from app.conversation_core.router import router as inbox_router
from app.database import get_db
from app.instagram_channel.models import InstagramConnection
from app.models import Store, TenantAuditLog
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


@pytest.fixture
def customer_api(tmp_path: Path):
    database = tmp_path / "customer-final-uat.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=str(engine.url),
        session_cookie_secure=False,
    )
    application = FastAPI()
    application.include_router(commerce_router)
    application.include_router(knowledge_router)
    application.include_router(inbox_router)
    application.include_router(automation_router)

    def override_db():
        with Session(engine) as db:
            yield db

    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(application), engine
    engine.dispose()


def _register(client: TestClient, name: str) -> tuple[dict, dict[str, str]]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{name}@example.com",
            "password": PASSWORD,
            "display_name": f"Customer {name}",
            "tenant_name": f"Tenant {name}",
            "tenant_slug": f"tenant-{name}",
            "store_name": f"Store {name}",
            "store_slug": f"store-{name}",
        },
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    return registration.json(), {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def _scope_path(registration: dict) -> str:
    return (
        f"/api/v1/tenants/{registration['tenant_public_id']}"
        f"/stores/{registration['store_public_id']}"
    )


def test_owner_can_create_read_update_profile_and_other_tenant_cannot(customer_api) -> None:
    client, _engine = customer_api
    owner, owner_headers = _register(client, "knowledge-owner")
    other, other_headers = _register(client, "knowledge-other")
    profile_url = f"{_scope_path(owner)}/business-knowledge/profile"

    created = client.post(
        profile_url,
        headers=owner_headers,
        json={"expected_revision": 0, "display_name": "فروشگاه آزمایشی"},
    )
    assert created.status_code == 201
    assert created.json()["revision"] == 1
    read = client.get(profile_url, headers=owner_headers)
    assert read.status_code == 200
    updated = client.patch(
        profile_url,
        headers=owner_headers,
        json={"expected_revision": 1, "description": "توضیحات معتبر"},
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2

    forbidden_scope = (
        f"/api/v1/tenants/{owner['tenant_public_id']}"
        f"/stores/{owner['store_public_id']}/business-knowledge/profile"
    )
    assert client.get(forbidden_scope, headers=other_headers).status_code == 404
    invalid = client.patch(
        profile_url,
        headers=owner_headers,
        json={"expected_revision": 2, "display_name": ""},
    )
    assert invalid.status_code == 422
    assert other["tenant_public_id"] != owner["tenant_public_id"]


def _seed_inbox(engine, registration: dict) -> tuple[str, str]:
    now = datetime.now(UTC)
    with Session(engine) as db, db.begin():
        store = db.scalar(
            select(Store).where(Store.public_id == registration["store_public_id"])
        )
        assert store is not None
        connection = InstagramConnection(
            tenant_id=store.tenant_id,
            store_id=store.id,
            instagram_account_id=f"uat-account-{uuid.uuid4().hex}",
            status="active",
            encrypted_access_token="test-encrypted-placeholder",
        )
        db.add(connection)
        db.flush()
        older = Conversation(
            tenant_id=store.tenant_id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            provider_participant_key=f"participant-{uuid.uuid4().hex}",
            last_message_at=now - timedelta(minutes=5),
            last_outbound_message_at=now - timedelta(minutes=5),
            message_count=1,
            outbound_message_count=1,
        )
        latest = Conversation(
            tenant_id=store.tenant_id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            provider_participant_key=f"participant-{uuid.uuid4().hex}",
            last_message_at=now,
            last_outbound_message_at=now,
            message_count=2,
            outbound_message_count=2,
        )
        db.add_all((older, latest))
        db.flush()
        db.add(
            ConversationParticipant(
                tenant_id=store.tenant_id,
                store_id=store.id,
                conversation_id=latest.id,
                participant_type="customer",
                provider_participant_key=latest.provider_participant_key,
                display_name="مشتری آزمایشی",
                username="uat_customer",
            )
        )
        for index, occurred_at in enumerate(
            (now - timedelta(seconds=1), now), start=1
        ):
            db.add(
                ConversationMessage(
                    tenant_id=store.tenant_id,
                    store_id=store.id,
                    conversation_id=latest.id,
                    instagram_connection_id=connection.id,
                    idempotency_key=uuid.uuid4().hex,
                    direction="outbound",
                    content_type="text",
                    text=f"safe message {index}",
                    occurred_at=occurred_at,
                    metadata_json={"delivery_status": "sent"},
                )
            )
        db.add(
            ConversationMessage(
                tenant_id=store.tenant_id,
                store_id=store.id,
                conversation_id=older.id,
                instagram_connection_id=connection.id,
                idempotency_key=uuid.uuid4().hex,
                direction="outbound",
                content_type="text",
                text="older message",
                occurred_at=now - timedelta(minutes=5),
            )
        )
        return latest.public_id, older.public_id


def test_inbox_is_scoped_paginated_and_deterministically_ordered(customer_api) -> None:
    client, engine = customer_api
    owner, owner_headers = _register(client, "inbox-owner")
    _other, other_headers = _register(client, "inbox-other")
    latest_public_id, older_public_id = _seed_inbox(engine, owner)
    inbox = f"{_scope_path(owner)}/inbox"

    first_page = client.get(
        f"{inbox}/conversations?page=1&page_size=1", headers=owner_headers
    )
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 2
    assert first_page.json()["items"][0]["public_id"] == latest_public_id
    second_page = client.get(
        f"{inbox}/conversations?page=2&page_size=1", headers=owner_headers
    )
    assert second_page.json()["items"][0]["public_id"] == older_public_id

    conversation = client.get(
        f"{inbox}/conversations/{latest_public_id}", headers=owner_headers
    )
    assert conversation.status_code == 200
    assert conversation.json()["participant_username"] == "uat_customer"
    messages = client.get(
        f"{inbox}/conversations/{latest_public_id}/messages?page=1&page_size=10",
        headers=owner_headers,
    )
    assert messages.status_code == 200
    assert [item["content"] for item in messages.json()["items"]] == [
        "safe message 1",
        "safe message 2",
    ]
    assert all("provider" not in str(item) for item in messages.json()["items"])
    assert client.get(
        f"{inbox}/conversations/{latest_public_id}", headers=other_headers
    ).status_code == 404


def test_automation_state_is_audited_revisioned_and_tenant_scoped(customer_api) -> None:
    client, engine = customer_api
    owner, owner_headers = _register(client, "automation-owner")
    _other, other_headers = _register(client, "automation-other")
    url = f"{_scope_path(owner)}/automation"

    initial = client.get(url, headers=owner_headers)
    assert initial.status_code == 200
    assert initial.json()["enabled"] is True
    disabled = client.patch(
        url,
        headers=owner_headers,
        json={"enabled": False, "expected_revision": 1},
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False
    assert disabled.json()["revision"] == 2
    stale = client.patch(
        url,
        headers=owner_headers,
        json={"enabled": True, "expected_revision": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_revision"
    assert client.patch(
        url,
        headers=other_headers,
        json={"enabled": True, "expected_revision": 2},
    ).status_code == 404
    enabled = client.patch(
        url,
        headers=owner_headers,
        json={"enabled": True, "expected_revision": 2},
    )
    assert enabled.status_code == 200
    assert enabled.json()["revision"] == 3
    with Session(engine) as db:
        actions = tuple(
            db.scalars(
                select(TenantAuditLog.action).where(
                    TenantAuditLog.target_public_id == owner["store_public_id"]
                )
            ).all()
        )
    assert "store.automation_disabled" in actions
    assert "store.automation_enabled" in actions
