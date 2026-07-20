from fastapi.testclient import TestClient
from sqlalchemy import func, select

import app.manychat as manychat
from app.database import SessionLocal
from app.main import app, settings
from app.models import Conversation, Customer, ManyChatEvent, Order


SECRET = "pytest-manychat-dynamic-block-secret"


def manychat_payload(
    *,
    contact_id: str = "pytest-manychat-contact",
    message: str = "gheymat iphone 15 chande?",
    interaction: str = "2026-07-11T10:30:00+00:00",
) -> dict:
    return {
        "contact": {
            "id": contact_id,
            "page_id": "pytest-manychat-page",
            "first_name": "Test",
            "last_name": "Customer",
            "name": "Test Customer",
            "last_input_text": message,
            "last_interaction": interaction,
            "live_chat_url": "https://manychat.com/profile/example",
        }
    }


def authorization(secret: str = SECRET) -> dict[str, str]:
    return {"authorization": f"Bearer {secret}"}


def test_manychat_rejects_missing_or_wrong_bearer_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", SECRET)

    with TestClient(app) as client:
        missing = client.post(
            "/integrations/manychat/instagram", json=manychat_payload()
        )
        wrong = client.post(
            "/integrations/manychat/instagram",
            json=manychat_payload(),
            headers=authorization("wrong-secret"),
        )

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert wrong.status_code == 401
    assert SECRET not in missing.text
    assert SECRET not in wrong.text


def test_manychat_requires_configured_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", "replace-me")

    with TestClient(app) as client:
        response = client.post(
            "/integrations/manychat/instagram",
            json=manychat_payload(),
            headers=authorization(),
        )

    assert response.status_code == 503


def test_manychat_returns_instagram_v2_response_and_deduplicates(monkeypatch) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", SECRET)
    payload = manychat_payload()

    with TestClient(app) as client:
        first = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )
        duplicate = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert first.json() == duplicate.json()
    result = first.json()
    assert result["version"] == "v2"
    assert result["content"]["type"] == "instagram"
    assert result["content"]["actions"] == []
    assert result["content"]["quick_replies"] == []
    assert result["content"]["messages"][0]["type"] == "text"
    assert "72,500,000" in result["content"]["messages"][0]["text"]

    customer_key = "manychat:pytest-manychat-page:pytest-manychat-contact"
    with SessionLocal() as db:
        customer = db.scalar(
            select(Customer).where(Customer.instagram_user_id == customer_key)
        )
        assert customer is not None
        assert customer.name == "Test Customer"
        assert db.scalar(
            select(func.count(Conversation.id)).where(
                Conversation.customer_id == customer.id,
                Conversation.channel == "manychat-instagram",
            )
        ) == 1
        event = db.scalar(
            select(ManyChatEvent).where(
                ManyChatEvent.contact_id == "pytest-manychat-contact"
            )
        )
        assert event is not None
        assert event.status == "processed"


def test_manychat_validates_contact_payload_and_accepts_numeric_ids(monkeypatch) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", SECRET)
    parsed = manychat.ManyChatRequest.model_validate(
        {
            "contact": {
                "id": 123456,
                "page_id": 5243105,
                "last_input_text": "price",
                "last_interaction": "2026-07-11T10:30:00+00:00",
            }
        }
    )
    assert parsed.contact.id == "123456"
    assert parsed.contact.page_id == "5243105"

    invalid = manychat_payload(message="   ")
    with TestClient(app) as client:
        response = client.post(
            "/integrations/manychat/instagram",
            json=invalid,
            headers=authorization(),
        )

    assert response.status_code == 422


def test_manychat_failed_attempt_is_retryable_without_duplicate_chat(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", SECRET)
    original_process_chat = manychat.process_chat

    def fail_once(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(manychat, "process_chat", fail_once)
    payload = manychat_payload(contact_id="pytest-manychat-retry")
    with TestClient(app) as client:
        failed = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )
        monkeypatch.setattr(manychat, "process_chat", original_process_chat)
        retried = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )

    assert failed.status_code == 500
    assert "simulated failure" not in failed.text
    assert retried.status_code == 200

    with SessionLocal() as db:
        customer = db.scalar(
            select(Customer).where(
                Customer.instagram_user_id
                == "manychat:pytest-manychat-page:pytest-manychat-retry"
            )
        )
        assert customer is not None
        assert db.scalar(
            select(func.count(Conversation.id)).where(
                Conversation.customer_id == customer.id
            )
        ) == 1


def test_manychat_duplicate_order_request_creates_one_order(monkeypatch) -> None:
    monkeypatch.setattr(settings, "manychat_dynamic_block_secret", SECRET)
    contact_id = "pytest-manychat-order"
    customer_key = f"manychat:pytest-manychat-page:{contact_id}"
    payload = manychat_payload(
        contact_id=contact_id,
        message="haminja sefaresh mano sabt kon",
        interaction="2026-07-11T10:35:00+00:00",
    )

    with TestClient(app) as client:
        client.post(
            "/chat",
            json={
                "instagram_user_id": customer_key,
                "message": "gheymat iphone 15 chande?",
            },
        )
        client.post(
            "/chat",
            json={
                "instagram_user_id": customer_key,
                "message": "shomare man 09121234567 ast",
            },
        )
        first = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )
        duplicate = client.post(
            "/integrations/manychat/instagram",
            json=payload,
            headers=authorization(),
        )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert first.json() == duplicate.json()

    with SessionLocal() as db:
        customer = db.scalar(
            select(Customer).where(Customer.instagram_user_id == customer_key)
        )
        assert customer is not None
        assert db.scalar(
            select(func.count(Conversation.id)).where(
                Conversation.customer_id == customer.id,
                Conversation.channel == "manychat-instagram",
            )
        ) == 1
        assert db.scalar(
            select(func.count(Order.id)).where(Order.customer_id == customer.id)
        ) == 1
