import hashlib
import hmac
import json
from dataclasses import dataclass

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chat import format_price, normalize_text, process_chat
from app.config import Settings, get_settings
from app.database import get_db
from app.models import (
    InstagramCommentEvent,
    InstagramCommentPublicReply,
    InstagramEvent,
    InstagramMediaProduct,
    Product,
    utc_now,
)
from app.module_catalog import module_enabled, store_for_instagram_account
from app.schemas import ChatRequest, InstagramStatus


router = APIRouter(tags=["instagram"])


def get_fresh_settings() -> Settings:
    """Reload mutable local credentials for webhook verification requests."""
    return Settings()


@dataclass(frozen=True)
class IncomingInstagramMessage:
    message_id: str
    sender_id: str
    recipient_id: str
    text: str


@dataclass(frozen=True)
class IncomingInstagramComment:
    comment_id: str
    ig_account_id: str
    media_id: str
    username: str | None
    text: str
    media_product_type: str | None


def is_configured(value: str) -> bool:
    return bool(value and value.strip() and value.strip().lower() != "replace-me")


def verify_meta_signature(body: bytes, signature: str | None, settings: Settings) -> None:
    if not settings.meta_signature_required:
        return
    if not is_configured(settings.meta_app_secret):
        raise HTTPException(status_code=503, detail="Meta app secret is not configured")
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing Meta webhook signature")

    expected = hmac.new(
        settings.meta_app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid Meta webhook signature")


def extract_incoming_messages(payload: dict) -> list[IncomingInstagramMessage]:
    if payload.get("object") != "instagram":
        return []

    incoming: list[IncomingInstagramMessage] = []
    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message") or {}
            if message.get("is_echo") or message.get("is_self") or message.get("is_deleted"):
                continue

            message_id = message.get("mid")
            sender_id = (event.get("sender") or {}).get("id")
            recipient_id = (event.get("recipient") or {}).get("id") or entry.get("id")
            text = message.get("text")
            if not all((message_id, sender_id, recipient_id, isinstance(text, str), text.strip())):
                continue
            if sender_id == recipient_id:
                continue

            incoming.append(
                IncomingInstagramMessage(
                    message_id=str(message_id),
                    sender_id=str(sender_id),
                    recipient_id=str(recipient_id),
                    text=text.strip(),
                )
            )
    return incoming


def extract_incoming_comments(payload: dict) -> list[IncomingInstagramComment]:
    """Normalize both Instagram Login comment webhook payload shapes."""
    if payload.get("object") != "instagram":
        return []

    incoming: list[IncomingInstagramComment] = []
    for entry in payload.get("entry", []):
        account_id = str(entry.get("id") or "")
        changes: list[dict] = []
        if entry.get("field") == "comments" and isinstance(entry.get("value"), dict):
            changes.append({"field": "comments", "value": entry["value"]})
        changes.extend(
            change
            for change in entry.get("changes", [])
            if isinstance(change, dict) and change.get("field") == "comments"
        )

        for change in changes:
            value = change.get("value") or {}
            author = value.get("from") or {}
            media = value.get("media") or {}
            comment_id = value.get("id")
            media_id = media.get("id")
            text = value.get("text")
            author_id = str(author.get("id") or "")

            # Meta marks comments made by the professional account itself with
            # self_ig_scoped_id. The ID comparison is an additional loop guard.
            if author.get("self_ig_scoped_id") or (author_id and author_id == account_id):
                continue
            if not all((account_id, comment_id, media_id, isinstance(text, str), text.strip())):
                continue

            username = author.get("username")
            incoming.append(
                IncomingInstagramComment(
                    comment_id=str(comment_id),
                    ig_account_id=account_id,
                    media_id=str(media_id),
                    username=str(username) if username else None,
                    text=text.strip(),
                    media_product_type=(
                        str(media.get("media_product_type"))
                        if media.get("media_product_type")
                        else None
                    ),
                )
            )
    return incoming


def is_price_comment(text: str) -> bool:
    normalized = normalize_text(text)
    return "قیمت" in normalized or "price" in text.casefold()


def build_comment_private_reply(product: Product) -> str:
    if not product.is_available:
        return f"سلام 👋 {product.name} فعلاً موجود نیست. برای پیگیری موجودی، همین پیام را پاسخ دهید."
    return (
        f"سلام 👋 {product.name} موجود است. قیمت فرضی آن {format_price(product.price)} است. "
        "برای ثبت سفارش، همین پیام را پاسخ دهید و بنویسید «سفارشم را ثبت کن»."
    )


PUBLIC_PRICE_REPLY = (
    "قیمت در دایرکت ارسال شد ✅ اگر پیام را ندیدید، پوشه Requests را بررسی کنید."
)


class InstagramClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def send_url(self) -> str:
        return (
            f"https://graph.instagram.com/{self.settings.meta_api_version}/"
            f"{self.settings.meta_ig_user_id}/messages"
        )

    async def send_text(self, recipient_id: str, text: str) -> dict:
        self._ensure_send_enabled()
        if not is_configured(self.settings.meta_access_token):
            raise RuntimeError("Meta access token is not configured")
        if not is_configured(self.settings.meta_ig_user_id):
            raise RuntimeError("Instagram professional account ID is not configured")

        headers = {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.send_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_private_reply(self, comment_id: str, text: str) -> dict:
        self._ensure_send_enabled()
        if not is_configured(self.settings.meta_access_token):
            raise RuntimeError("Meta access token is not configured")
        if not is_configured(self.settings.meta_ig_user_id):
            raise RuntimeError("Instagram professional account ID is not configured")

        headers = {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "recipient": {"comment_id": comment_id},
            "message": {"text": text},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.send_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_public_comment_reply(self, comment_id: str, text: str) -> dict:
        self._ensure_send_enabled()
        if not is_configured(self.settings.meta_access_token):
            raise RuntimeError("Meta access token is not configured")

        url = (
            f"https://graph.instagram.com/{self.settings.meta_api_version}/"
            f"{comment_id}/replies"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json={"message": text})
            response.raise_for_status()
            return response.json()

    def _ensure_send_enabled(self) -> None:
        if not self.settings.meta_send_enabled:
            raise RuntimeError("Instagram outbound delivery is disabled")


async def deliver_response(
    event: InstagramEvent,
    db: Session,
    client: InstagramClient,
    settings: Settings,
) -> bool:
    if not settings.meta_send_enabled:
        event.status = "simulated"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True

    try:
        result = await client.send_text(event.sender_id, event.response_text or "")
        event.response_message_id = result.get("message_id")
        event.status = "sent"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True
    except (httpx.HTTPError, RuntimeError) as exc:
        event.status = "failed"
        event.error_message = str(exc)[:1000]
        event.processed_at = utc_now()
        db.commit()
        return False


async def deliver_comment_response(
    event: InstagramCommentEvent,
    db: Session,
    client: InstagramClient,
    settings: Settings,
) -> bool:
    if not settings.meta_send_enabled:
        event.status = "simulated"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True

    try:
        result = await client.send_private_reply(event.comment_id, event.response_text or "")
        event.recipient_id = result.get("recipient_id")
        event.response_message_id = result.get("message_id")
        event.status = "sent"
        event.processed_at = utc_now()
        event.error_message = None
        db.commit()
        return True
    except (httpx.HTTPError, RuntimeError) as exc:
        event.status = "failed"
        event.error_message = str(exc)[:1000]
        event.processed_at = utc_now()
        db.commit()
        return False


async def ensure_public_comment_reply(
    comment_id: str,
    db: Session,
    client: InstagramClient,
    settings: Settings,
) -> bool:
    existing = db.scalar(
        select(InstagramCommentPublicReply).where(
            InstagramCommentPublicReply.comment_id == comment_id
        )
    )
    if existing is not None:
        return existing.status in {"sent", "simulated"}

    reply = InstagramCommentPublicReply(
        comment_id=comment_id,
        reply_text=PUBLIC_PRICE_REPLY,
        status="processing",
    )
    db.add(reply)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False

    if not settings.meta_send_enabled:
        reply.status = "simulated"
        reply.processed_at = utc_now()
        db.commit()
        return True

    try:
        result = await client.send_public_comment_reply(comment_id, reply.reply_text)
        reply.reply_comment_id = result.get("id")
        reply.status = "sent"
        reply.error_message = None
        reply.processed_at = utc_now()
        db.commit()
        return True
    except (httpx.HTTPError, RuntimeError) as exc:
        reply.status = "failed"
        reply.error_message = str(exc)[:1000]
        reply.processed_at = utc_now()
        db.commit()
        return False


@router.get("/instagram/status", response_model=InstagramStatus)
def instagram_status(settings: Settings = Depends(get_settings)) -> dict:
    verify_ready = is_configured(settings.meta_verify_token)
    secret_ready = is_configured(settings.meta_app_secret)
    token_ready = is_configured(settings.meta_access_token)
    account_ready = is_configured(settings.meta_ig_user_id)
    return {
        "mode": "live" if settings.meta_send_enabled else "simulation",
        "webhook_path": "/webhooks/instagram",
        "api_version": settings.meta_api_version,
        "verify_token_configured": verify_ready,
        "app_secret_configured": secret_ready,
        "access_token_configured": token_ready,
        "instagram_user_id_configured": account_ready,
        "signature_required": settings.meta_signature_required,
        "send_enabled": settings.meta_send_enabled,
        "ready_to_receive": verify_ready and (secret_ready or not settings.meta_signature_required),
        "ready_to_send": settings.meta_send_enabled and token_ready and account_ready,
    }


@router.get("/webhooks/instagram", response_class=PlainTextResponse)
def verify_instagram_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    settings: Settings = Depends(get_fresh_settings),
) -> PlainTextResponse:
    if not is_configured(settings.meta_verify_token):
        raise HTTPException(status_code=503, detail="Meta verify token is not configured")
    if hub_mode == "subscribe" and hmac.compare_digest(
        hub_verify_token or "", settings.meta_verify_token
    ):
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhooks/instagram")
async def receive_instagram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    body = await request.body()
    verify_meta_signature(body, request.headers.get("x-hub-signature-256"), settings)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    messages = extract_incoming_messages(payload)
    comments = extract_incoming_comments(payload)
    client = InstagramClient(settings)
    summary = {
        "received": len(messages) + len(comments),
        "processed": 0,
        "duplicates": 0,
        "failed": 0,
    }

    for incoming in messages:
        existing = db.scalar(
            select(InstagramEvent).where(InstagramEvent.message_id == incoming.message_id)
        )
        if existing:
            if existing.status == "failed" and existing.response_text:
                delivered = await deliver_response(existing, db, client, settings)
                summary["processed" if delivered else "failed"] += 1
            else:
                summary["duplicates"] += 1
            continue

        event = InstagramEvent(
            message_id=incoming.message_id,
            sender_id=incoming.sender_id,
            recipient_id=incoming.recipient_id,
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
            store = store_for_instagram_account(
                db, incoming.recipient_id, settings
            )
            if store is None:
                event.status = "unmapped_store"
                event.processed_at = utc_now()
                db.commit()
                summary["failed"] += 1
                continue
            if not module_enabled(db, store, "sales_agent_core"):
                event.status = "ignored_module_disabled"
                event.processed_at = utc_now()
                db.commit()
                continue
            chat_result = process_chat(
                db,
                ChatRequest(
                    instagram_user_id=incoming.sender_id,
                    message=incoming.text,
                ),
                channel="instagram",
                store_slug=store.slug,
            )
            event.response_text = chat_result["reply"]
            event.status = "ready"
            db.commit()
            delivered = await deliver_response(event, db, client, settings)
            summary["processed" if delivered else "failed"] += 1
        except Exception as exc:
            db.rollback()
            persisted_event = db.scalar(
                select(InstagramEvent).where(InstagramEvent.message_id == incoming.message_id)
            )
            if persisted_event:
                persisted_event.status = "failed"
                persisted_event.error_message = str(exc)[:1000]
                persisted_event.processed_at = utc_now()
                db.commit()
            summary["failed"] += 1

    for incoming in comments:
        existing = db.scalar(
            select(InstagramCommentEvent).where(
                InstagramCommentEvent.comment_id == incoming.comment_id
            )
        )
        if existing:
            if existing.status == "sent":
                await ensure_public_comment_reply(
                    existing.comment_id, db, client, settings
                )
            summary["duplicates"] += 1
            continue

        event = InstagramCommentEvent(
            comment_id=incoming.comment_id,
            ig_account_id=incoming.ig_account_id,
            media_id=incoming.media_id,
            username=incoming.username,
            comment_text=incoming.text,
            media_product_type=incoming.media_product_type,
            status="processing",
        )
        db.add(event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            summary["duplicates"] += 1
            continue

        store = store_for_instagram_account(db, incoming.ig_account_id, settings)
        if store is None:
            event.status = "unmapped_store"
            event.processed_at = utc_now()
            db.commit()
            summary["failed"] += 1
            continue
        if not module_enabled(db, store, "comments_to_dm"):
            event.status = "ignored_module_disabled"
            event.processed_at = utc_now()
            db.commit()
            continue

        if not is_price_comment(incoming.text):
            event.status = "ignored"
            event.processed_at = utc_now()
            db.commit()
            continue

        mapping = db.scalar(
            select(InstagramMediaProduct).where(
                InstagramMediaProduct.media_id == incoming.media_id
            )
        )
        if mapping is None:
            event.status = "unmapped"
            event.processed_at = utc_now()
            db.commit()
            continue

        event.response_text = build_comment_private_reply(mapping.product)
        event.status = "ready"
        db.commit()
        delivered = await deliver_comment_response(event, db, client, settings)
        if delivered:
            await ensure_public_comment_reply(event.comment_id, db, client, settings)
        summary["processed" if delivered else "failed"] += 1

    return {"status": "ok", **summary}
