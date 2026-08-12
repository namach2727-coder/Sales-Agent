import asyncio
import hashlib
import hmac
import json

import httpx
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.instagram import InstagramClient, extract_incoming_comments, get_fresh_settings
from app.main import app, settings
from app.models import (
    InstagramCommentEvent,
    InstagramCommentPublicReply,
    InstagramEvent,
    InstagramMediaProduct,
    Product,
    Store,
    StoreModule,
)


def sign_payload(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_legacy_instagram_client_fails_closed_before_network(monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_send_enabled", False)
    monkeypatch.setattr(settings, "meta_access_token", "credential")
    monkeypatch.setattr(settings, "meta_ig_user_id", "account")

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("network client must not be constructed")

    monkeypatch.setattr(httpx, "AsyncClient", ForbiddenClient)
    with pytest.raises(RuntimeError, match="outbound delivery is disabled"):
        asyncio.run(InstagramClient(settings).send_text("recipient", "message"))


def test_instagram_status_and_webhook_verification(monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_verify_token", "pytest-verify-token")
    monkeypatch.setattr(settings, "meta_app_secret", "pytest-app-secret")
    monkeypatch.setattr(settings, "meta_access_token", "")
    monkeypatch.setattr(settings, "meta_ig_user_id", "")
    monkeypatch.setattr(settings, "meta_send_enabled", False)

    app.dependency_overrides[get_fresh_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            status_response = client.get("/instagram/status")
            verification_response = client.get(
                "/webhooks/instagram",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "pytest-verify-token",
                    "hub.challenge": "123456789",
                },
            )
            rejected_response = client.get(
                "/webhooks/instagram",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong-token",
                    "hub.challenge": "123456789",
                },
            )
    finally:
        app.dependency_overrides.pop(get_fresh_settings, None)

    status = status_response.json()
    assert status_response.status_code == 200
    assert status["ready_to_receive"] is True
    assert status["ready_to_send"] is False
    assert "meta_access_token" not in status
    assert verification_response.status_code == 200
    assert verification_response.text == "123456789"
    assert rejected_response.status_code == 403


def test_instagram_webhook_rejects_invalid_signature(monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_app_secret", "pytest-app-secret")
    monkeypatch.setattr(settings, "meta_signature_required", True)
    payload = json.dumps({"object": "instagram", "entry": []}).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/instagram",
            content=payload,
            headers={
                "content-type": "application/json",
                "x-hub-signature-256": "sha256=invalid",
            },
        )

    assert response.status_code == 401


def test_instagram_webhook_processes_finglish_and_deduplicates(monkeypatch) -> None:
    secret = "pytest-app-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_access_token", "pytest-access-token")
    monkeypatch.setattr(settings, "meta_ig_user_id", "17841400000000000")
    monkeypatch.setattr(settings, "meta_send_enabled", True)
    monkeypatch.setattr(settings, "meta_signature_required", True)

    sent_messages: list[tuple[str, str]] = []

    async def fake_send_text(self, recipient_id: str, text: str) -> dict:
        sent_messages.append((recipient_id, text))
        return {"recipient_id": recipient_id, "message_id": "pytest-reply-mid-1"}

    monkeypatch.setattr(InstagramClient, "send_text", fake_send_text)

    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "time": 1720000000000,
                "messaging": [
                    {
                        "sender": {"id": "pytest-instagram-user"},
                        "recipient": {"id": "17841400000000000"},
                        "timestamp": 1720000000000,
                        "message": {
                            "mid": "pytest-incoming-mid-1",
                            "text": "gheymat iphone 15 chande?",
                        },
                    }
                ],
            }
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-hub-signature-256": sign_payload(body, secret),
    }

    with TestClient(app) as client:
        first_response = client.post("/webhooks/instagram", content=body, headers=headers)
        duplicate_response = client.post("/webhooks/instagram", content=body, headers=headers)

    assert first_response.status_code == 200
    assert first_response.json()["processed"] == 1
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["duplicates"] == 1
    assert len(sent_messages) == 1
    assert sent_messages[0][0] == "pytest-instagram-user"
    assert "72,500,000 تومان" in sent_messages[0][1]

    with SessionLocal() as db:
        event = db.scalar(
            select(InstagramEvent).where(
                InstagramEvent.message_id == "pytest-incoming-mid-1"
            )
        )
        assert event is not None
        assert event.status == "sent"
        assert event.response_message_id == "pytest-reply-mid-1"


def test_instagram_webhook_ignores_echo_messages(monkeypatch) -> None:
    secret = "pytest-app-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_signature_required", True)
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "messaging": [
                    {
                        "sender": {"id": "17841400000000000"},
                        "recipient": {"id": "pytest-instagram-user"},
                        "message": {
                            "mid": "pytest-echo-mid-1",
                            "text": "echo",
                            "is_echo": True,
                        },
                    }
                ],
            }
        ],
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/instagram",
            content=body,
            headers={
                "content-type": "application/json",
                "x-hub-signature-256": sign_payload(body, secret),
            },
        )

    assert response.status_code == 200
    assert response.json()["received"] == 0


def test_extract_incoming_comments_supports_direct_and_changes_shapes() -> None:
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "field": "comments",
                "value": {
                    "id": "pytest-comment-direct",
                    "from": {"username": "pytest-commenter"},
                    "text": "gheymat",
                    "media": {
                        "id": "pytest-media-direct",
                        "media_product_type": "FEED",
                    },
                },
            },
            {
                "id": "17841400000000000",
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "pytest-comment-self",
                            "from": {
                                "id": "17841400000000000",
                                "username": "page-owner",
                                "self_ig_scoped_id": "pytest-self-id",
                            },
                            "text": "قیمت",
                            "media": {"id": "pytest-media-self"},
                        },
                    }
                ],
            },
        ],
    }

    comments = extract_incoming_comments(payload)

    assert len(comments) == 1
    assert comments[0].comment_id == "pytest-comment-direct"
    assert comments[0].media_id == "pytest-media-direct"
    assert comments[0].username == "pytest-commenter"


def test_instagram_comment_sends_one_private_price_reply_and_deduplicates(
    monkeypatch,
) -> None:
    secret = "pytest-comment-app-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_access_token", "pytest-access-token")
    monkeypatch.setattr(settings, "meta_ig_user_id", "17841400000000000")
    monkeypatch.setattr(settings, "meta_send_enabled", True)
    monkeypatch.setattr(settings, "meta_signature_required", True)

    sent_replies: list[tuple[str, str]] = []
    public_replies: list[tuple[str, str]] = []

    async def fake_private_reply(self, comment_id: str, text: str) -> dict:
        sent_replies.append((comment_id, text))
        return {
            "recipient_id": "pytest-comment-recipient",
            "message_id": "pytest-private-reply-mid",
        }

    async def fake_public_reply(self, comment_id: str, text: str) -> dict:
        public_replies.append((comment_id, text))
        return {"id": "pytest-public-reply-comment-id"}

    monkeypatch.setattr(InstagramClient, "send_private_reply", fake_private_reply)
    monkeypatch.setattr(InstagramClient, "send_public_comment_reply", fake_public_reply)
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "field": "comments",
                "value": {
                    "id": "pytest-comment-price-1",
                    "from": {"username": "pytest-commenter"},
                    "text": "gheymat?",
                    "media": {
                        "id": "pytest-media-iphone-15",
                        "media_product_type": "FEED",
                    },
                },
            }
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-hub-signature-256": sign_payload(body, secret),
    }

    with TestClient(app) as client:
        with SessionLocal() as db:
            product = db.scalar(
                select(Product).where(Product.name == "Apple iPhone 15 128GB")
            )
            assert product is not None
            db.add(
                InstagramMediaProduct(
                    media_id="pytest-media-iphone-15",
                    product_id=product.id,
                    media_product_type="FEED",
                )
            )
            db.commit()

        first = client.post("/webhooks/instagram", content=body, headers=headers)
        duplicate = client.post("/webhooks/instagram", content=body, headers=headers)

    assert first.status_code == 200
    assert first.json()["processed"] == 1
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicates"] == 1
    assert len(sent_replies) == 1
    assert sent_replies[0][0] == "pytest-comment-price-1"
    assert "72,500,000 تومان" in sent_replies[0][1]
    assert len(public_replies) == 1
    assert public_replies[0][0] == "pytest-comment-price-1"
    assert "Requests" in public_replies[0][1]

    with SessionLocal() as db:
        event = db.scalar(
            select(InstagramCommentEvent).where(
                InstagramCommentEvent.comment_id == "pytest-comment-price-1"
            )
        )
        assert event is not None
        assert event.status == "sent"
        assert event.response_message_id == "pytest-private-reply-mid"
        assert event.recipient_id == "pytest-comment-recipient"
        public_reply = db.scalar(
            select(InstagramCommentPublicReply).where(
                InstagramCommentPublicReply.comment_id == "pytest-comment-price-1"
            )
        )
        assert public_reply is not None
        assert public_reply.status == "sent"
        assert public_reply.reply_comment_id == "pytest-public-reply-comment-id"


def test_instagram_comment_with_unmapped_media_is_recorded_without_reply(
    monkeypatch,
) -> None:
    secret = "pytest-unmapped-comment-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_ig_user_id", "17841400000000000")
    monkeypatch.setattr(settings, "meta_send_enabled", True)
    monkeypatch.setattr(settings, "meta_signature_required", True)
    sent_replies: list[str] = []
    public_replies: list[str] = []

    async def fake_private_reply(self, comment_id: str, text: str) -> dict:
        sent_replies.append(comment_id)
        return {}

    async def fake_public_reply(self, comment_id: str, text: str) -> dict:
        public_replies.append(comment_id)
        return {}

    monkeypatch.setattr(InstagramClient, "send_private_reply", fake_private_reply)
    monkeypatch.setattr(InstagramClient, "send_public_comment_reply", fake_public_reply)
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "field": "comments",
                "value": {
                    "id": "pytest-comment-unmapped",
                    "from": {"username": "pytest-commenter"},
                    "text": "قیمت",
                    "media": {"id": "pytest-media-unmapped"},
                },
            }
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"x-hub-signature-256": sign_payload(body, secret)},
        )

    assert response.status_code == 200
    assert response.json()["received"] == 1
    assert response.json()["processed"] == 0
    assert sent_replies == []
    assert public_replies == []
    with SessionLocal() as db:
        event = db.scalar(
            select(InstagramCommentEvent).where(
                InstagramCommentEvent.comment_id == "pytest-comment-unmapped"
            )
        )
        assert event is not None
        assert event.status == "unmapped"


def test_disabled_comment_module_records_event_without_sending(monkeypatch) -> None:
    secret = "pytest-disabled-comment-module-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_access_token", "pytest-access-token")
    monkeypatch.setattr(settings, "meta_ig_user_id", "17841400000000000")
    monkeypatch.setattr(settings, "meta_send_enabled", True)
    monkeypatch.setattr(settings, "meta_signature_required", True)
    private_calls: list[str] = []
    public_calls: list[str] = []

    async def fake_private_reply(self, comment_id: str, text: str) -> dict:
        private_calls.append(comment_id)
        return {}

    async def fake_public_reply(self, comment_id: str, text: str) -> dict:
        public_calls.append(comment_id)
        return {}

    monkeypatch.setattr(InstagramClient, "send_private_reply", fake_private_reply)
    monkeypatch.setattr(InstagramClient, "send_public_comment_reply", fake_public_reply)
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "field": "comments",
                "value": {
                    "id": "pytest-comment-module-disabled",
                    "from": {"username": "pytest-commenter"},
                    "text": "قیمت؟",
                    "media": {"id": "pytest-media-module-disabled"},
                },
            }
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )

    with TestClient(app) as client:
        with SessionLocal() as db:
            store = db.scalar(select(Store).where(Store.slug == "default"))
            assert store is not None
            entitlement = db.scalar(
                select(StoreModule).where(
                    StoreModule.store_id == store.id,
                    StoreModule.module_code == "comments_to_dm",
                )
            )
            assert entitlement is not None
            entitlement.status = "inactive"
            db.commit()
        try:
            response = client.post(
                "/webhooks/instagram",
                content=body,
                headers={"x-hub-signature-256": sign_payload(body, secret)},
            )
        finally:
            with SessionLocal() as db:
                store = db.scalar(select(Store).where(Store.slug == "default"))
                entitlement = db.scalar(
                    select(StoreModule).where(
                        StoreModule.store_id == store.id,
                        StoreModule.module_code == "comments_to_dm",
                    )
                )
                entitlement.status = "active"
                db.commit()

    assert response.status_code == 200
    assert response.json()["processed"] == 0
    assert private_calls == []
    assert public_calls == []
    with SessionLocal() as db:
        event = db.scalar(
            select(InstagramCommentEvent).where(
                InstagramCommentEvent.comment_id
                == "pytest-comment-module-disabled"
            )
        )
        assert event is not None
        assert event.status == "ignored_module_disabled"


def test_instagram_comment_does_not_claim_dm_was_sent_when_private_reply_fails(
    monkeypatch,
) -> None:
    secret = "pytest-private-failure-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_access_token", "pytest-access-token")
    monkeypatch.setattr(settings, "meta_ig_user_id", "17841400000000000")
    monkeypatch.setattr(settings, "meta_send_enabled", True)
    monkeypatch.setattr(settings, "meta_signature_required", True)
    public_replies: list[str] = []

    async def failing_private_reply(self, comment_id: str, text: str) -> dict:
        raise httpx.ConnectError("pytest connection failure")

    async def fake_public_reply(self, comment_id: str, text: str) -> dict:
        public_replies.append(comment_id)
        return {}

    monkeypatch.setattr(InstagramClient, "send_private_reply", failing_private_reply)
    monkeypatch.setattr(InstagramClient, "send_public_comment_reply", fake_public_reply)
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "field": "comments",
                "value": {
                    "id": "pytest-comment-private-failure",
                    "from": {"username": "pytest-commenter"},
                    "text": "price",
                    "media": {"id": "pytest-media-private-failure"},
                },
            }
        ],
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    with TestClient(app) as client:
        with SessionLocal() as db:
            product = db.scalar(
                select(Product).where(Product.name == "Apple iPhone 15 128GB")
            )
            assert product is not None
            db.add(
                InstagramMediaProduct(
                    media_id="pytest-media-private-failure",
                    product_id=product.id,
                )
            )
            db.commit()
        response = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"x-hub-signature-256": sign_payload(body, secret)},
        )

    assert response.status_code == 200
    assert response.json()["failed"] == 1
    assert public_replies == []
