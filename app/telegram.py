import hmac
from dataclasses import dataclass

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chat import process_chat
from app.config import Settings, get_settings
from app.database import get_db
from app.models import TelegramEvent, utc_now
from app.schemas import ChatRequest, TelegramStatus


router = APIRouter(tags=["telegram"])


@dataclass(frozen=True)
class IncomingTelegramMessage:
    update_id: int
    chat_id: str
    sender_id: str
    message_id: str
    text: str
    customer_name: str | None


class TelegramAPIError(RuntimeError):
    """A token-safe Telegram API error suitable for logs and database storage."""


def is_configured(value: str) -> bool:
    return bool(value and value.strip() and value.strip().lower() != "replace-me")


def telegram_reply_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "محصولات موجود"}, {"text": "ثبت سفارش"}],
            [{"text": "ارتباط با اپراتور"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": "پیام خود را فارسی یا فینگلیش بنویسید…",
    }


def normalize_telegram_command(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("/"):
        return stripped

    command = stripped.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
    commands = {
        "/start": "سلام",
        "/help": "سلام",
        "/products": "چه محصولاتی دارید؟",
        "/order": "سفارش من را ثبت کن",
        "/operator": "می‌خواهم با اپراتور صحبت کنم",
    }
    return commands.get(command, stripped)


def extract_incoming_messages(payload: dict) -> list[IncomingTelegramMessage]:
    update_id = payload.get("update_id")
    message = payload.get("message")
    if not isinstance(update_id, int) or not isinstance(message, dict):
        return []

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    text = message.get("text")
    message_id = message.get("message_id")

    # The MVP intentionally ignores groups, channels, bots, media, and edited messages.
    if chat.get("type") != "private" or sender.get("is_bot"):
        return []
    if not isinstance(text, str) or not text.strip():
        return []
    if message_id is None or chat.get("id") is None or sender.get("id") is None:
        return []

    name_parts = [sender.get("first_name"), sender.get("last_name")]
    customer_name = " ".join(part.strip() for part in name_parts if isinstance(part, str) and part.strip())
    if not customer_name and isinstance(sender.get("username"), str):
        customer_name = f"@{sender['username']}"

    return [
        IncomingTelegramMessage(
            update_id=update_id,
            chat_id=str(chat["id"]),
            sender_id=str(sender["id"]),
            message_id=str(message_id),
            text=normalize_telegram_command(text),
            customer_name=customer_name or None,
        )
    ]


def verify_telegram_secret(supplied: str | None, settings: Settings) -> None:
    if not is_configured(settings.telegram_webhook_secret):
        raise HTTPException(status_code=503, detail="Telegram webhook secret is not configured")
    if not supplied or not hmac.compare_digest(supplied, settings.telegram_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")


class TelegramClient:
    api_base = "https://api.telegram.org"

    def __init__(self, settings: Settings):
        self.settings = settings

    def api_url(self, method: str) -> str:
        if not is_configured(self.settings.telegram_bot_token):
            raise TelegramAPIError("Telegram bot token is not configured")
        return f"{self.api_base}/bot{self.settings.telegram_bot_token}/{method}"

    async def _post(self, method: str, payload: dict, timeout: float = 15.0):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(self.api_url(method), json=payload)
        except TelegramAPIError:
            raise
        except httpx.HTTPError as exc:
            # Do not store the exception URL because it contains the bot token.
            raise TelegramAPIError(
                f"Telegram API is unreachable ({exc.__class__.__name__})"
            ) from None

        try:
            result = response.json()
        except ValueError:
            result = {}
        if response.is_error or not result.get("ok"):
            description = result.get("description")
            safe_description = str(description)[:500] if description else f"HTTP {response.status_code}"
            raise TelegramAPIError(f"Telegram API error: {safe_description}")
        return result.get("result")

    async def send_text(self, chat_id: str, text: str) -> dict:
        result = await self._post(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": telegram_reply_keyboard(),
            },
        )
        if not isinstance(result, dict):
            raise TelegramAPIError("Telegram API returned an invalid sendMessage response")
        return result

    async def get_updates(self, offset: int | None = None) -> list[dict]:
        poll_timeout = max(1, min(self.settings.telegram_poll_timeout, 50))
        payload: dict = {
            "timeout": poll_timeout,
            "limit": 50,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        result = await self._post("getUpdates", payload, timeout=poll_timeout + 10.0)
        if not isinstance(result, list):
            raise TelegramAPIError("Telegram API returned an invalid getUpdates response")
        return result

    async def get_webhook_info(self) -> dict:
        result = await self._post("getWebhookInfo", {})
        if not isinstance(result, dict):
            raise TelegramAPIError("Telegram API returned an invalid getWebhookInfo response")
        return result

    async def get_me(self) -> dict:
        result = await self._post("getMe", {})
        if not isinstance(result, dict) or not result.get("is_bot"):
            raise TelegramAPIError("Telegram API returned an invalid getMe response")
        return result


async def deliver_response(
    event: TelegramEvent,
    db: Session,
    client: TelegramClient,
    settings: Settings,
) -> bool:
    if not settings.telegram_send_enabled:
        event.status = "simulated"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True

    try:
        result = await client.send_text(event.chat_id, event.response_text or "")
        response_message_id = result.get("message_id")
        event.response_message_id = str(response_message_id) if response_message_id is not None else None
        event.status = "sent"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True
    except TelegramAPIError as exc:
        event.status = "failed"
        event.error_message = str(exc)[:1000]
        event.processed_at = utc_now()
        db.commit()
        return False


async def process_telegram_payload(
    payload: dict,
    db: Session,
    client: TelegramClient,
    settings: Settings,
) -> dict[str, int | str]:
    messages = extract_incoming_messages(payload)
    summary: dict[str, int | str] = {
        "status": "ok",
        "received": len(messages),
        "processed": 0,
        "duplicates": 0,
        "failed": 0,
    }

    for incoming in messages:
        existing = db.scalar(
            select(TelegramEvent).where(TelegramEvent.update_id == incoming.update_id)
        )
        if existing:
            if existing.status == "failed" and existing.response_text:
                delivered = await deliver_response(existing, db, client, settings)
                summary["processed" if delivered else "failed"] += 1
            else:
                summary["duplicates"] += 1
            continue

        event = TelegramEvent(
            update_id=incoming.update_id,
            chat_id=incoming.chat_id,
            sender_id=incoming.sender_id,
            message_id=incoming.message_id,
            message_text=incoming.text,
            status="processing",
        )
        db.add(event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            summary["duplicates"] += 1
            continue

        try:
            chat_result = process_chat(
                db,
                ChatRequest(
                    instagram_user_id=f"telegram:{incoming.sender_id}",
                    message=incoming.text,
                    customer_name=incoming.customer_name,
                ),
                channel="telegram",
            )
            event.response_text = chat_result["reply"]
            event.status = "ready"
            db.commit()
            delivered = await deliver_response(event, db, client, settings)
            summary["processed" if delivered else "failed"] += 1
        except Exception as exc:
            db.rollback()
            persisted_event = db.scalar(
                select(TelegramEvent).where(TelegramEvent.update_id == incoming.update_id)
            )
            if persisted_event:
                persisted_event.status = "failed"
                # TelegramAPIError is already token-safe. Other errors contain no API URL here.
                persisted_event.error_message = str(exc)[:1000]
                persisted_event.processed_at = utc_now()
                db.commit()
            summary["failed"] += 1

    if summary["failed"]:
        summary["status"] = "retry"
    return summary


@router.get("/telegram/status", response_model=TelegramStatus)
def telegram_status(settings: Settings = Depends(get_settings)) -> dict:
    token_ready = is_configured(settings.telegram_bot_token)
    secret_ready = is_configured(settings.telegram_webhook_secret)
    receive_mode = "polling" if settings.telegram_polling_enabled else "webhook"
    return {
        "mode": "live" if settings.telegram_send_enabled else "simulation",
        "receive_mode": receive_mode,
        "webhook_path": "/webhooks/telegram",
        "bot_token_configured": token_ready,
        "webhook_secret_configured": secret_ready,
        "polling_enabled": settings.telegram_polling_enabled,
        "send_enabled": settings.telegram_send_enabled,
        "ready_to_receive": token_ready
        and (settings.telegram_polling_enabled or secret_ready),
        "ready_to_send": settings.telegram_send_enabled and token_ready,
    }


@router.post("/webhooks/telegram")
async def receive_telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    verify_telegram_secret(
        request.headers.get("x-telegram-bot-api-secret-token"), settings
    )
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid Telegram update")

    result = await process_telegram_payload(
        payload,
        db,
        TelegramClient(settings),
        settings,
    )
    status_code = 503 if result["failed"] else 200
    return JSONResponse(content=result, status_code=status_code)
