"""Transport-independent Instagram connection and webhook rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any
import unicodedata

from app.instagram_channel.exceptions import (
    InstagramChannelInvalidTransitionError,
    InstagramChannelValidationError,
    InstagramWebhookPayloadError,
)


CONNECTION_STATUSES = frozenset(
    {"pending", "active", "degraded", "disconnected", "revoked", "archived"}
)
ROUTABLE_CONNECTION_STATUSES = frozenset({"active", "degraded"})
READABLE_STORE_STATUSES = frozenset({"onboarding", "active", "suspended"})
WRITABLE_STORE_STATUSES = frozenset({"onboarding", "active"})
SUPPORTED_EVENT_TYPES = frozenset({"messaging", "comments", "unsupported"})


def normalize_identifier(
    value: str | None,
    *,
    field: str,
    required: bool = False,
    maximum: int = 200,
) -> str | None:
    if value is None:
        if required:
            raise InstagramChannelValidationError(f"{field} is required")
        return None
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized:
        if required:
            raise InstagramChannelValidationError(f"{field} cannot be blank")
        return None
    if len(normalized) > maximum or any(ord(char) < 32 for char in normalized):
        raise InstagramChannelValidationError(f"invalid {field}")
    return normalized


def normalize_optional_text(
    value: str | None, *, field: str, maximum: int
) -> str | None:
    if value is None:
        return None
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    if not normalized:
        return None
    if len(normalized) > maximum or any(ord(char) < 32 for char in normalized):
        raise InstagramChannelValidationError(f"invalid {field}")
    return normalized


def normalize_scopes(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = normalize_identifier(
            raw, field="token scope", required=True, maximum=200
        )
        assert value is not None
        if value not in seen:
            seen.add(value)
            result.append(value)
        if len(result) > 100:
            raise InstagramChannelValidationError("too many token scopes")
    return result


def validate_transition(current: str, target: str) -> str:
    if current not in CONNECTION_STATUSES or target not in CONNECTION_STATUSES:
        raise InstagramChannelValidationError("invalid connection status")
    allowed = {
        "pending": {"active", "disconnected", "revoked", "archived"},
        "active": {"degraded", "disconnected", "revoked", "archived"},
        "degraded": {"active", "disconnected", "revoked", "archived"},
        "disconnected": {"active", "revoked", "archived"},
        "revoked": {"active", "archived"},
        "archived": set(),
    }
    if target not in allowed[current]:
        raise InstagramChannelInvalidTransitionError(
            f"cannot transition from {current} to {target}"
        )
    return target


def canonical_payload_hash(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()


def deterministic_key(*parts: object) -> str:
    encoded = json.dumps(
        list(parts),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class ParsedInstagramEvent:
    routing_account_id: str | None
    provider_event_id: str | None
    idempotency_key: str
    event_type: str
    object_type: str
    external_object_id: str | None
    external_sender_id: str | None
    external_recipient_id: str | None
    provider_event_at: datetime | None
    normalized_payload: dict[str, object]
    position: int


def _messaging_event(
    *,
    entry_id: str | None,
    fragment: object,
    position: int,
) -> ParsedInstagramEvent:
    if not isinstance(fragment, dict):
        return _unsupported_event(entry_id, fragment, position, "messaging")
    sender = fragment.get("sender")
    recipient = fragment.get("recipient")
    message = fragment.get("message")
    sender_id = sender.get("id") if isinstance(sender, dict) else None
    recipient_id = recipient.get("id") if isinstance(recipient, dict) else None
    message_id = message.get("mid") if isinstance(message, dict) else None
    text = message.get("text") if isinstance(message, dict) else None
    if not isinstance(sender_id, str):
        sender_id = None
    if not isinstance(recipient_id, str):
        recipient_id = None
    if not isinstance(message_id, str):
        message_id = None
    normalized_message: dict[str, object] = {}
    if message_id:
        normalized_message["id"] = message_id
    if isinstance(text, str):
        normalized_message["text"] = text
    normalized: dict[str, object] = {"message": normalized_message}
    key = deterministic_key(
        "messaging",
        message_id,
        entry_id,
        sender_id,
        recipient_id,
        fragment.get("timestamp"),
        fragment,
    )
    return ParsedInstagramEvent(
        routing_account_id=recipient_id or entry_id,
        provider_event_id=message_id,
        idempotency_key=key,
        event_type="messaging",
        object_type="message",
        external_object_id=message_id,
        external_sender_id=sender_id,
        external_recipient_id=recipient_id,
        provider_event_at=_timestamp(fragment.get("timestamp")),
        normalized_payload=normalized,
        position=position,
    )


def _change_event(
    *,
    entry_id: str | None,
    fragment: object,
    position: int,
) -> ParsedInstagramEvent:
    if not isinstance(fragment, dict):
        return _unsupported_event(entry_id, fragment, position, "change")
    field = fragment.get("field")
    value = fragment.get("value")
    if field not in {"comments", "live_comments"} or not isinstance(value, dict):
        return _unsupported_event(entry_id, fragment, position, str(field or "change"))
    comment_id = value.get("id")
    sender = value.get("from")
    sender_id = sender.get("id") if isinstance(sender, dict) else None
    if not isinstance(comment_id, str):
        comment_id = None
    if not isinstance(sender_id, str):
        sender_id = None
    normalized: dict[str, object] = {}
    for key in ("id", "text", "media_id", "parent_id"):
        item = value.get(key)
        if isinstance(item, str):
            normalized[key] = item
    key = deterministic_key(
        "comments",
        comment_id,
        entry_id,
        sender_id,
        value.get("created_time"),
        value,
    )
    return ParsedInstagramEvent(
        routing_account_id=entry_id,
        provider_event_id=comment_id,
        idempotency_key=key,
        event_type="comments",
        object_type="comment",
        external_object_id=comment_id,
        external_sender_id=sender_id,
        external_recipient_id=entry_id,
        provider_event_at=_timestamp(value.get("created_time")),
        normalized_payload=normalized,
        position=position,
    )


def _unsupported_event(
    entry_id: str | None,
    fragment: object,
    position: int,
    object_type: str,
) -> ParsedInstagramEvent:
    safe_type = object_type[:100] if object_type else "unknown"
    return ParsedInstagramEvent(
        routing_account_id=entry_id,
        provider_event_id=None,
        idempotency_key=deterministic_key(
            "unsupported", entry_id, position, safe_type, fragment
        ),
        event_type="unsupported",
        object_type=safe_type,
        external_object_id=None,
        external_sender_id=None,
        external_recipient_id=entry_id,
        provider_event_at=None,
        normalized_payload={"classification": "unsupported"},
        position=position,
    )


def parse_instagram_webhook(payload: object) -> list[ParsedInstagramEvent]:
    """Normalize supported transport events without applying business semantics."""

    if not isinstance(payload, dict) or payload.get("object") != "instagram":
        raise InstagramWebhookPayloadError("unsupported webhook object")
    entries = payload.get("entry")
    if not isinstance(entries, list):
        raise InstagramWebhookPayloadError("webhook entry must be a list")
    result: list[ParsedInstagramEvent] = []
    position = 0
    for entry in entries:
        if not isinstance(entry, dict):
            result.append(_unsupported_event(None, entry, position, "entry"))
            position += 1
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str):
            entry_id = None
        messaging = entry.get("messaging")
        if isinstance(messaging, list):
            for fragment in messaging:
                result.append(
                    _messaging_event(
                        entry_id=entry_id,
                        fragment=fragment,
                        position=position,
                    )
                )
                position += 1
        changes = entry.get("changes")
        if isinstance(changes, list):
            for fragment in changes:
                result.append(
                    _change_event(
                        entry_id=entry_id,
                        fragment=fragment,
                        position=position,
                    )
                )
                position += 1
        if not isinstance(messaging, list) and not isinstance(changes, list):
            result.append(_unsupported_event(entry_id, entry, position, "entry"))
            position += 1
    return result
