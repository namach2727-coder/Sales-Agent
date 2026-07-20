import hashlib
import hmac
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chat import process_chat
from app.config import Settings, get_settings
from app.database import get_db
from app.models import ManyChatEvent, utc_now
from app.schemas import ChatRequest


router = APIRouter(prefix="/integrations/manychat", tags=["manychat"])
MAX_INSTAGRAM_REPLY_LENGTH = 1000


class ManyChatContact(BaseModel):
    """Contact fields sent by a ManyChat Dynamic Block request."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(max_length=40)
    page_id: str = Field(max_length=40)
    first_name: str | None = Field(default=None, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    name: str | None = Field(default=None, max_length=200)
    last_input_text: str = Field(max_length=4096)
    last_interaction: datetime
    live_chat_url: HttpUrl | None = None

    @field_validator("id", "page_id", mode="before")
    @classmethod
    def normalize_identifier(cls, value: Any) -> str:
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ValueError("must be a string or integer identifier")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("first_name", "last_name", "name", mode="before")
    @classmethod
    def normalize_optional_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string")
        return value.strip() or None

    @field_validator("last_input_text")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    def display_name(self) -> str | None:
        if self.name:
            return self.name
        joined = " ".join(part for part in (self.first_name, self.last_name) if part)
        return joined[:200] or None


class ManyChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contact: ManyChatContact
    request_id: str | None = Field(default=None, max_length=200)

    @field_validator("request_id", mode="before")
    @classmethod
    def normalize_request_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string")
        return value.strip() or None


class ManyChatTextMessage(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ManyChatContent(BaseModel):
    type: Literal["instagram"] = "instagram"
    messages: list[ManyChatTextMessage]
    actions: list[dict] = Field(default_factory=list)
    quick_replies: list[dict] = Field(default_factory=list)


class ManyChatDynamicBlockResponse(BaseModel):
    version: Literal["v2"] = "v2"
    content: ManyChatContent


def is_secret_configured(value: str) -> bool:
    normalized = value.strip().lower() if value else ""
    return bool(normalized and not normalized.startswith("replace-me"))


def require_manychat_bearer(
    authorization: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> Settings:
    secret = settings.manychat_dynamic_block_secret
    if not is_secret_configured(secret):
        raise HTTPException(
            status_code=503,
            detail="ManyChat Dynamic Block secret is not configured",
        )

    scheme, separator, supplied = (authorization or "").partition(" ")
    valid = (
        bool(separator)
        and scheme.lower() == "bearer"
        and bool(supplied.strip())
        and hmac.compare_digest(
            supplied.strip().encode("utf-8"),
            secret.strip().encode("utf-8"),
        )
    )
    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid ManyChat authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return settings


def manychat_request_key(payload: ManyChatRequest) -> str:
    contact = payload.contact
    canonical = "\x1f".join(
        (
            contact.page_id,
            contact.id,
            contact.last_interaction.isoformat(timespec="microseconds"),
            contact.last_input_text,
            payload.request_id or "",
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_dynamic_block_response(reply: str) -> dict:
    text = reply.strip()[:MAX_INSTAGRAM_REPLY_LENGTH]
    return {
        "version": "v2",
        "content": {
            "type": "instagram",
            "messages": [{"type": "text", "text": text}],
            "actions": [],
            "quick_replies": [],
        },
    }


def record_failed_event(
    db: Session,
    payload: ManyChatRequest,
    request_key: str,
    error_type: str,
) -> None:
    """Persist a retryable failure without retaining exception details."""

    try:
        event = db.scalar(
            select(ManyChatEvent).where(ManyChatEvent.request_key == request_key)
        )
        if event is None:
            event = ManyChatEvent(
                request_key=request_key,
                page_id=payload.contact.page_id,
                contact_id=payload.contact.id,
                last_interaction=payload.contact.last_interaction,
                message_text=payload.contact.last_input_text,
            )
            db.add(event)
        if event.status != "processed":
            event.status = "failed"
            event.error_message = f"Processing failed ({error_type})"
            event.processed_at = utc_now()
            db.commit()
    except Exception:
        db.rollback()


@router.post(
    "/instagram",
    response_model=ManyChatDynamicBlockResponse,
    summary="Answer an Instagram message from a ManyChat Dynamic Block",
)
def receive_manychat_instagram(
    payload: ManyChatRequest,
    db: Session = Depends(get_db),
    _settings: Settings = Depends(require_manychat_bearer),
) -> dict:
    request_key = manychat_request_key(payload)
    existing = db.scalar(
        select(ManyChatEvent).where(ManyChatEvent.request_key == request_key)
    )
    if existing and existing.status == "processed" and existing.response_text:
        return build_dynamic_block_response(existing.response_text)
    if existing and existing.status == "processing":
        raise HTTPException(status_code=409, detail="ManyChat request is already processing")

    event = existing
    if event is None:
        event = ManyChatEvent(
            request_key=request_key,
            page_id=payload.contact.page_id,
            contact_id=payload.contact.id,
            last_interaction=payload.contact.last_interaction,
            message_text=payload.contact.last_input_text,
            status="processing",
        )
        db.add(event)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            concurrent = db.scalar(
                select(ManyChatEvent).where(ManyChatEvent.request_key == request_key)
            )
            if concurrent and concurrent.status == "processed" and concurrent.response_text:
                return build_dynamic_block_response(concurrent.response_text)
            raise HTTPException(
                status_code=409,
                detail="ManyChat request is already processing",
            ) from None
    else:
        event.status = "processing"
        event.error_message = None
        event.processed_at = None

    try:
        contact = payload.contact
        chat_result = process_chat(
            db,
            ChatRequest(
                instagram_user_id=f"manychat:{contact.page_id}:{contact.id}",
                message=contact.last_input_text,
                customer_name=contact.display_name(),
            ),
            channel="manychat-instagram",
            commit=False,
        )
        reply = chat_result["reply"].strip()[:MAX_INSTAGRAM_REPLY_LENGTH]
        event.response_text = reply
        event.status = "processed"
        event.error_message = None
        event.processed_at = utc_now()
        db.commit()
        return build_dynamic_block_response(reply)
    except Exception as exc:
        db.rollback()
        record_failed_event(db, payload, request_key, exc.__class__.__name__)
        raise HTTPException(
            status_code=500,
            detail="Could not process the ManyChat request",
        ) from None
