import re

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app, settings
from app.models import Conversation, Customer, TelegramEvent
from app.telegram import (
    TelegramAPIError,
    TelegramClient,
    extract_incoming_messages,
    normalize_telegram_command,
    telegram_reply_keyboard,
)
from app import telegram_setup


def telegram_update(
    update_id: int,
    text: str,
    sender_id: str = "pytest-telegram-user",
    chat_type: str = "private",
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id + 100,
            "from": {
                "id": sender_id,
                "is_bot": False,
                "first_name": "مشتری",
                "last_name": "تلگرام",
            },
            "chat": {"id": sender_id, "type": chat_type},
            "text": text,
        },
    }


def test_telegram_status_is_safe(monkeypatch) -> None:
    secret_token = "pytest:bot-token-must-not-leak"
    monkeypatch.setattr(settings, "telegram_bot_token", secret_token)
    monkeypatch.setattr(settings, "telegram_webhook_secret", "pytest-webhook-secret")
    monkeypatch.setattr(settings, "telegram_send_enabled", True)
    monkeypatch.setattr(settings, "telegram_polling_enabled", True)

    with TestClient(app) as client:
        response = client.get("/telegram/status")

    assert response.status_code == 200
    result = response.json()
    assert result["receive_mode"] == "polling"
    assert result["ready_to_receive"] is True
    assert result["ready_to_send"] is True
    assert secret_token not in response.text
    assert "telegram_bot_token" not in result


def test_telegram_webhook_rejects_wrong_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "telegram_webhook_secret", "pytest-webhook-secret")

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/telegram",
            json=telegram_update(910000001, "سلام"),
            headers={"x-telegram-bot-api-secret-token": "wrong-secret"},
        )

    assert response.status_code == 401


def test_telegram_webhook_processes_finglish_and_deduplicates(monkeypatch) -> None:
    monkeypatch.setattr(settings, "telegram_bot_token", "pytest-bot-token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "pytest-webhook-secret")
    monkeypatch.setattr(settings, "telegram_send_enabled", True)

    sent_messages: list[tuple[str, str]] = []

    async def fake_send_text(self, chat_id: str, text: str) -> dict:
        sent_messages.append((chat_id, text))
        return {"message_id": 777}

    monkeypatch.setattr(TelegramClient, "send_text", fake_send_text)
    payload = telegram_update(910000002, "gheymat iphone 15 chande?")
    headers = {"x-telegram-bot-api-secret-token": "pytest-webhook-secret"}

    with TestClient(app) as client:
        first = client.post("/webhooks/telegram", json=payload, headers=headers)
        duplicate = client.post("/webhooks/telegram", json=payload, headers=headers)

    assert first.status_code == 200
    assert first.json()["processed"] == 1
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicates"] == 1
    assert len(sent_messages) == 1
    assert "72,500,000 تومان" in sent_messages[0][1]

    with SessionLocal() as db:
        event = db.scalar(
            select(TelegramEvent).where(TelegramEvent.update_id == 910000002)
        )
        customer = db.scalar(
            select(Customer).where(
                Customer.instagram_user_id == "telegram:pytest-telegram-user"
            )
        )
        assert event is not None
        assert event.status == "sent"
        assert event.response_message_id == "777"
        assert customer is not None
        conversation = db.scalar(
            select(Conversation)
            .where(Conversation.customer_id == customer.id)
            .order_by(Conversation.id.desc())
        )
        assert conversation is not None
        assert conversation.channel == "telegram"


def test_telegram_failed_send_retries_without_duplicate_conversation(monkeypatch) -> None:
    monkeypatch.setattr(settings, "telegram_bot_token", "pytest-bot-token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "pytest-webhook-secret")
    monkeypatch.setattr(settings, "telegram_send_enabled", True)
    attempts = 0

    async def flaky_send_text(self, chat_id: str, text: str) -> dict:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TelegramAPIError("Telegram API is temporarily unreachable")
        return {"message_id": 778}

    monkeypatch.setattr(TelegramClient, "send_text", flaky_send_text)
    payload = telegram_update(
        910000003,
        "salam, gheymat samsung a55 chande?",
        sender_id="pytest-telegram-retry-user",
    )
    headers = {"x-telegram-bot-api-secret-token": "pytest-webhook-secret"}

    with TestClient(app) as client:
        failed = client.post("/webhooks/telegram", json=payload, headers=headers)
        retried = client.post("/webhooks/telegram", json=payload, headers=headers)

    assert failed.status_code == 503
    assert failed.json()["failed"] == 1
    assert retried.status_code == 200
    assert retried.json()["processed"] == 1
    assert attempts == 2

    with SessionLocal() as db:
        customer = db.scalar(
            select(Customer).where(
                Customer.instagram_user_id == "telegram:pytest-telegram-retry-user"
            )
        )
        assert customer is not None
        count = db.scalar(
            select(func.count(Conversation.id)).where(
                Conversation.customer_id == customer.id
            )
        )
        assert count == 1


def test_telegram_commands_keyboard_and_private_text_filter() -> None:
    assert normalize_telegram_command("/start referral") == "سلام"
    assert normalize_telegram_command("/operator@demo_bot") == "می‌خواهم با اپراتور صحبت کنم"
    keyboard = telegram_reply_keyboard()
    button_texts = {
        button["text"]
        for row in keyboard["keyboard"]
        for button in row
    }
    assert {"محصولات موجود", "ثبت سفارش", "ارتباط با اپراتور"} <= button_texts
    assert extract_incoming_messages(
        telegram_update(910000004, "سلام", chat_type="group")
    ) == []
    non_text_update = telegram_update(910000005, "سلام")
    del non_text_update["message"]["text"]
    assert extract_incoming_messages(non_text_update) == []


def test_local_telegram_setup_saves_verified_token_without_exposing_it(
    monkeypatch, tmp_path
) -> None:
    env_path = tmp_path / ".env"
    example_path = tmp_path / ".env.example"
    example_path.write_text(
        "APP_NAME=Keep Me\n"
        "TELEGRAM_BOT_TOKEN=replace-me\n"
        "TELEGRAM_BOT_TOKEN=duplicate-must-be-removed\n"
        "TELEGRAM_SEND_ENABLED=false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(telegram_setup, "ENV_PATH", env_path)
    monkeypatch.setattr(telegram_setup, "ENV_EXAMPLE_PATH", example_path)
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "")
    monkeypatch.setattr(settings, "telegram_send_enabled", False)
    monkeypatch.setattr(settings, "telegram_polling_enabled", False)

    async def fake_get_me(self) -> dict:
        return {"id": 123, "is_bot": True, "username": "pytest_demo_bot"}

    monkeypatch.setattr(TelegramClient, "get_me", fake_get_me)
    fake_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"

    with TestClient(
        app,
        base_url="http://127.0.0.1:8000",
        client=("127.0.0.1", 50000),
    ) as client:
        page = client.get("/telegram/setup")
        nonce_match = re.search(r'const setupNonce = "([^"]+)";', page.text)
        assert nonce_match is not None
        response = client.post(
            "/telegram/setup",
            json={
                "token": (
                    "Use this token to access the HTTP API:\r\n"
                    f"\u200f`{fake_token}`\r\n"
                    "Keep your token secure."
                ),
                "setup_nonce": nonce_match.group(1),
            },
            headers={
                "origin": "http://127.0.0.1:8000",
                "sec-fetch-site": "same-origin",
            },
        )
        status_response = client.get("/telegram/status")

    assert page.status_code == 200
    assert 'type="password"' in page.text
    assert page.headers["cache-control"] == "no-store"
    assert page.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert response.status_code == 200
    assert response.json()["bot_username"] == "pytest_demo_bot"
    assert response.json()["token_verified"] is True
    assert fake_token not in response.text
    assert status_response.json()["ready_to_send"] is True

    saved = env_path.read_text(encoding="utf-8")
    assert "APP_NAME=Keep Me" in saved
    assert saved.count("TELEGRAM_BOT_TOKEN=") == 1
    assert f"TELEGRAM_BOT_TOKEN={fake_token}" in saved
    assert "TELEGRAM_SEND_ENABLED=true" in saved
    assert not list(tmp_path.glob(".*.tmp"))


def test_local_telegram_setup_rejects_remote_client_and_wrong_origin(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(telegram_setup, "ENV_PATH", tmp_path / ".env")

    with TestClient(
        app,
        base_url="http://127.0.0.1:8000",
        client=("192.0.2.10", 50000),
    ) as remote_client:
        remote_response = remote_client.get("/telegram/setup")

    with TestClient(
        app,
        base_url="http://127.0.0.1:8000",
        client=("127.0.0.1", 50000),
    ) as local_client:
        page = local_client.get("/telegram/setup")
        nonce = re.search(r'const setupNonce = "([^"]+)";', page.text).group(1)
        wrong_origin_response = local_client.post(
            "/telegram/setup",
            json={
                "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                "setup_nonce": nonce,
            },
            headers={"origin": "https://evil.example"},
        )

    assert remote_response.status_code == 403
    assert wrong_origin_response.status_code == 403
    assert not (tmp_path / ".env").exists()


def test_local_telegram_setup_defers_verification_when_network_is_unavailable(
    monkeypatch, tmp_path
) -> None:
    env_path = tmp_path / ".env"
    monkeypatch.setattr(telegram_setup, "ENV_PATH", env_path)
    monkeypatch.setattr(telegram_setup, "ENV_EXAMPLE_PATH", tmp_path / "missing.example")
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "")
    monkeypatch.setattr(settings, "telegram_send_enabled", False)
    monkeypatch.setattr(settings, "telegram_polling_enabled", False)

    async def unavailable_get_me(self) -> dict:
        raise TelegramAPIError("Telegram API is unreachable (ConnectError)")

    monkeypatch.setattr(TelegramClient, "get_me", unavailable_get_me)
    fake_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"

    with TestClient(
        app,
        base_url="http://127.0.0.1:8000",
        client=("127.0.0.1", 50000),
    ) as client:
        page = client.get("/telegram/setup")
        nonce = re.search(r'const setupNonce = "([^"]+)";', page.text).group(1)
        response = client.post(
            "/telegram/setup",
            json={"token": fake_token, "setup_nonce": nonce},
            headers={"origin": "http://127.0.0.1:8000"},
        )

    assert response.status_code == 200
    assert response.json()["token_verified"] is False
    assert fake_token not in response.text
    assert f"TELEGRAM_BOT_TOKEN={fake_token}" in env_path.read_text(encoding="utf-8")
