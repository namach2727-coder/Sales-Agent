from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_channel.domain import parse_instagram_webhook
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
    InstagramWebhookDelivery,
)
from app.instagram_channel.router import public_router
from app.instagram_channel.service import InstagramWebhookIngestionService
from app.models import Store, Tenant, utc_now


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def webhook_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("foundation08-webhook") / "webhook.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


def create_connection(engine, *, status: str = "active") -> InstagramConnection:
    suffix = uuid.uuid4().hex[:12]
    with Session(engine, expire_on_commit=False) as db:
        tenant = Tenant(
            name=f"Tenant {suffix}", slug=f"tenant-{suffix}", status="active"
        )
        db.add(tenant)
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Main",
            slug="main",
            status="active",
            currency_code="IRR",
        )
        db.add(store)
        db.flush()
        connection = InstagramConnection(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_account_id=f"ig-{suffix}",
            facebook_page_id=f"page-{suffix}",
            status=status,
            token_scopes=[],
            archived_at=utc_now() if status == "archived" else None,
        )
        db.add(connection)
        db.commit()
        return connection


def messaging_payload(account_id: str, message_id: str = "mid-1") -> dict:
    return {
        "object": "instagram",
        "entry": [
            {
                "id": account_id,
                "messaging": [
                    {
                        "sender": {"id": "customer-1"},
                        "recipient": {"id": account_id},
                        "timestamp": 1720000000000,
                        "message": {"mid": message_id, "text": "price?"},
                    }
                ],
            }
        ],
    }


def body_for(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode()


def signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_parser_handles_messaging_comments_multiple_entries_and_unsupported() -> None:
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig-1",
                "messaging": [
                    {
                        "sender": {"id": "sender"},
                        "recipient": {"id": "ig-1"},
                        "message": {"mid": "mid-1", "text": "hello"},
                    }
                ],
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comment-1",
                            "from": {"id": "commenter"},
                            "text": "price",
                        },
                    },
                    {"field": "unsupported", "value": {"id": "other"}},
                ],
            },
            {"id": "ig-1", "changes": ["bad-fragment"]},
        ],
    }
    events = parse_instagram_webhook(payload)
    assert [item.event_type for item in events] == [
        "messaging",
        "comments",
        "unsupported",
        "unsupported",
    ]
    assert [item.position for item in events] == [0, 1, 2, 3]
    assert events[0].provider_event_id == "mid-1"
    assert events[1].provider_event_id == "comment-1"


def test_webhook_ingestion_routes_and_deduplicates_delivery(webhook_engine) -> None:
    connection = create_connection(webhook_engine)
    payload = messaging_payload(connection.instagram_account_id)
    body = body_for(payload)
    with Session(webhook_engine) as db:
        first = InstagramWebhookIngestionService(db).ingest(
            raw_body=body,
            payload=payload,
            external_delivery_key=None,
            correlation_id="correlation-1",
        )
    with Session(webhook_engine) as db:
        second = InstagramWebhookIngestionService(db).ingest(
            raw_body=body,
            payload=payload,
            external_delivery_key=None,
            correlation_id="correlation-2",
        )
        assert db.scalar(select(func.count()).select_from(InstagramWebhookDelivery)) == 1
        assert db.scalar(select(func.count()).select_from(InstagramInboundEvent)) == 1
        event_row = db.scalar(select(InstagramInboundEvent))
        assert event_row is not None
        assert event_row.tenant_id == connection.tenant_id
        assert event_row.store_id == connection.store_id
    assert first == ("accepted", False, 1)
    assert second == ("duplicate", True, 0)


def test_event_idempotency_across_distinct_deliveries(webhook_engine) -> None:
    connection = create_connection(webhook_engine)
    first_payload = messaging_payload(connection.instagram_account_id, "stable-mid")
    second_payload = {**first_payload, "delivery_marker": "different"}
    with Session(webhook_engine) as db:
        first = InstagramWebhookIngestionService(db).ingest(
            raw_body=body_for(first_payload),
            payload=first_payload,
            external_delivery_key="delivery-one",
            correlation_id=None,
        )
    with Session(webhook_engine) as db:
        second = InstagramWebhookIngestionService(db).ingest(
            raw_body=body_for(second_payload),
            payload=second_payload,
            external_delivery_key="delivery-two",
            correlation_id=None,
        )
        count = db.scalar(
            select(func.count())
            .select_from(InstagramInboundEvent)
            .where(
                InstagramInboundEvent.instagram_connection_id == connection.id,
                InstagramInboundEvent.provider_event_id == "stable-mid",
            )
        )
    assert first == ("accepted", False, 1)
    assert second == ("accepted", False, 0)
    assert count == 1


@pytest.mark.parametrize("status", ["disconnected", "revoked", "archived"])
def test_non_routable_or_unknown_account_creates_no_tenant_event(
    webhook_engine, status: str
) -> None:
    connection = create_connection(webhook_engine, status=status)
    payload = messaging_payload(connection.instagram_account_id)
    with Session(webhook_engine) as db:
        result = InstagramWebhookIngestionService(db).ingest(
            raw_body=body_for(payload),
            payload=payload,
            external_delivery_key=f"delivery-{status}-{uuid.uuid4()}",
            correlation_id=None,
        )
        delivery = db.scalar(
            select(InstagramWebhookDelivery).where(
                InstagramWebhookDelivery.payload_hash
                == hashlib.sha256(body_for(payload)).hexdigest()
            )
        )
        assert delivery is not None
        assert delivery.tenant_id is None
        assert delivery.processing_status == "ignored"
        assert db.scalar(
            select(func.count())
            .select_from(InstagramInboundEvent)
            .where(InstagramInboundEvent.instagram_connection_id == connection.id)
        ) == 0
    assert result == ("ignored", False, 0)


def public_client(engine, settings: Settings) -> TestClient:
    app = FastAPI()
    app.include_router(public_router)

    def database_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_public_verification_and_signature_contract(webhook_engine) -> None:
    settings = Settings(
        meta_verify_token="verify-token",
        meta_app_secret="app-secret",
    )
    client = public_client(webhook_engine, settings)
    accepted = client.get(
        "/api/v1/integrations/instagram/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token",
            "hub.challenge": "challenge-exact",
        },
    )
    rejected = client.get(
        "/api/v1/integrations/instagram/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "challenge-exact",
        },
    )
    assert accepted.status_code == 200
    assert accepted.text == "challenge-exact"
    assert rejected.status_code == 403

    connection = create_connection(webhook_engine)
    payload = messaging_payload(connection.instagram_account_id, str(uuid.uuid4()))
    body = body_for(payload)
    valid = client.post(
        "/api/v1/integrations/instagram/webhook",
        content=body,
        headers={"x-hub-signature-256": signature(body, "app-secret")},
    )
    invalid = client.post(
        "/api/v1/integrations/instagram/webhook",
        content=body,
        headers={"x-hub-signature-256": "sha256=" + ("0" * 64)},
    )
    malformed_json = b"{"
    bad_json = client.post(
        "/api/v1/integrations/instagram/webhook",
        content=malformed_json,
        headers={
            "x-hub-signature-256": signature(malformed_json, "app-secret")
        },
    )
    assert valid.status_code == 200
    assert valid.json()["status"] == "accepted"
    assert invalid.status_code == 401
    assert bad_json.status_code == 400
