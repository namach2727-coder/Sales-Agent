"""Transport-independent conversation domain rules and value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import unicodedata

from app.conversation_core.exceptions import (
    ConversationImmutableError,
    ConversationInvalidTransitionError,
    ConversationValidationError,
)


CONVERSATION_STATUSES = frozenset(
    {
        "open",
        "waiting_for_customer",
        "handoff_requested",
        "human_active",
        "closed",
        "archived",
    }
)
MESSAGE_DIRECTIONS = frozenset({"inbound", "outbound", "system"})
MESSAGE_CONTENT_TYPES = frozenset(
    {
        "text",
        "image",
        "video",
        "audio",
        "file",
        "sticker",
        "reaction",
        "unsupported",
    }
)
PARTICIPANT_TYPES = frozenset(
    {"customer", "instagram_business", "system", "operator"}
)
ASSIGNMENT_STATUSES = frozenset({"assigned", "released"})
PROCESSING_STATUSES = frozenset({"pending", "processed", "ignored", "failed"})
SUPPORTED_INBOUND_EVENT_TYPES = frozenset({"messaging"})


_CONVERSATION_TRANSITIONS = {
    "open": {
        "waiting_for_customer",
        "handoff_requested",
        "human_active",
        "closed",
    },
    "waiting_for_customer": {
        "open",
        "handoff_requested",
        "human_active",
        "closed",
    },
    "handoff_requested": {"open", "human_active", "closed"},
    "human_active": {"waiting_for_customer", "open", "closed"},
    "closed": {"open", "archived"},
    "archived": set(),
}
_PROCESSING_TRANSITIONS = {
    "pending": {"processed", "ignored", "failed"},
    "failed": {"pending", "ignored"},
    "processed": set(),
    "ignored": set(),
}


def normalize_identifier(
    value: str | None,
    *,
    field: str,
    required: bool = False,
    maximum: int = 200,
) -> str | None:
    """Normalize a provider or public identifier and reject unsafe values."""

    if value is None:
        if required:
            raise ConversationValidationError(f"{field} is required")
        return None
    if not isinstance(value, str):
        raise ConversationValidationError(f"invalid {field}")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized:
        if required:
            raise ConversationValidationError(f"{field} cannot be blank")
        return None
    has_control_character = any(ord(character) < 32 for character in normalized)
    if len(normalized) > maximum or has_control_character:
        raise ConversationValidationError(f"invalid {field}")
    return normalized


def normalize_optional_text(
    value: str | None,
    *,
    field: str,
    maximum: int,
) -> str | None:
    """Normalize free text while preserving meaningful line and tab structure."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise ConversationValidationError(f"invalid {field}")
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return None
    if len(normalized) > maximum:
        raise ConversationValidationError(f"invalid {field}")
    if any(
        ord(character) < 32 and character not in {"\n", "\t"}
        for character in normalized
    ):
        raise ConversationValidationError(f"invalid {field}")
    return normalized


def normalize_metadata(
    value: dict[str, object] | None,
    *,
    field: str = "metadata",
    maximum_bytes: int = 16_384,
) -> dict[str, object]:
    """Validate JSON metadata and return a detached JSON-compatible copy."""

    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConversationValidationError(f"invalid {field}")
    try:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        raise ConversationValidationError(f"invalid {field}") from None
    if len(serialized.encode("utf-8")) > maximum_bytes:
        raise ConversationValidationError(f"invalid {field}")
    copied = json.loads(serialized)
    if not isinstance(copied, dict):
        raise ConversationValidationError(f"invalid {field}")
    return copied


def validate_conversation_transition(current: str, target: str) -> str:
    """Validate a requested conversation lifecycle transition."""

    if current not in CONVERSATION_STATUSES or target not in CONVERSATION_STATUSES:
        raise ConversationValidationError("invalid conversation status")
    if current == target or target not in _CONVERSATION_TRANSITIONS[current]:
        raise ConversationInvalidTransitionError(
            "conversation status transition is not allowed"
        )
    return target


def ensure_conversation_mutable(status: str) -> None:
    """Reject mutation attempts against terminal archived conversations."""

    if status not in CONVERSATION_STATUSES:
        raise ConversationValidationError("invalid conversation status")
    if status == "archived":
        raise ConversationImmutableError("conversation is immutable")


def is_conversation_terminal(status: str) -> bool:
    """Return whether a validated conversation status is terminal."""

    if status not in CONVERSATION_STATUSES:
        raise ConversationValidationError("invalid conversation status")
    return status == "archived"


def validate_processing_transition(current: str, target: str) -> str:
    """Validate an inbound event processing transition."""

    if current not in PROCESSING_STATUSES or target not in PROCESSING_STATUSES:
        raise ConversationValidationError("invalid processing status")
    if current == target or target not in _PROCESSING_TRANSITIONS[current]:
        raise ConversationInvalidTransitionError(
            "processing status transition is not allowed"
        )
    return target


def _required_identifier(value: str | None, field: str) -> str:
    normalized = normalize_identifier(
        value,
        field=field,
        required=True,
        maximum=100,
    )
    assert normalized is not None
    return normalized


@dataclass(frozen=True, slots=True)
class IncomingConversationEvent:
    instagram_inbound_event_public_id: str
    tenant_public_id: str
    store_public_id: str
    instagram_connection_public_id: str
    provider_participant_key: str
    provider_message_id: str | None
    idempotency_key: str
    event_type: str
    direction: str
    content_type: str
    text: str | None
    provider_event_at: datetime | None
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        for field in (
            "instagram_inbound_event_public_id",
            "tenant_public_id",
            "store_public_id",
            "instagram_connection_public_id",
        ):
            object.__setattr__(
                self,
                field,
                _required_identifier(getattr(self, field), field),
            )

        participant_key = normalize_identifier(
            self.provider_participant_key,
            field="provider_participant_key",
            required=True,
            maximum=200,
        )
        provider_message_id = normalize_identifier(
            self.provider_message_id,
            field="provider_message_id",
            maximum=200,
        )
        idempotency_key = normalize_identifier(
            self.idempotency_key,
            field="idempotency_key",
            required=True,
            maximum=200,
        )
        event_type = normalize_identifier(
            self.event_type,
            field="event_type",
            required=True,
            maximum=100,
        )
        direction = normalize_identifier(
            self.direction,
            field="direction",
            required=True,
            maximum=100,
        )
        content_type = normalize_identifier(
            self.content_type,
            field="content_type",
            required=True,
            maximum=100,
        )
        text = normalize_optional_text(self.text, field="text", maximum=10_000)

        if event_type not in SUPPORTED_INBOUND_EVENT_TYPES:
            raise ConversationValidationError("invalid event_type")
        if direction != "inbound":
            raise ConversationValidationError("invalid direction")
        if content_type not in MESSAGE_CONTENT_TYPES:
            raise ConversationValidationError("invalid content_type")
        if content_type == "text" and text is None:
            raise ConversationValidationError("text is required for text content")
        if self.provider_event_at is not None:
            if (
                not isinstance(self.provider_event_at, datetime)
                or self.provider_event_at.tzinfo is None
                or self.provider_event_at.utcoffset() is None
            ):
                raise ConversationValidationError(
                    "provider_event_at must be timezone-aware"
                )

        assert participant_key is not None
        assert idempotency_key is not None
        assert event_type is not None
        assert direction is not None
        assert content_type is not None
        object.__setattr__(self, "provider_participant_key", participant_key)
        object.__setattr__(self, "provider_message_id", provider_message_id)
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "content_type", content_type)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "metadata", normalize_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class ConversationIdentity:
    instagram_connection_public_id: str
    provider_participant_key: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "instagram_connection_public_id",
            _required_identifier(
                self.instagram_connection_public_id,
                "instagram_connection_public_id",
            ),
        )
        participant_key = normalize_identifier(
            self.provider_participant_key,
            field="provider_participant_key",
            required=True,
            maximum=200,
        )
        assert participant_key is not None
        object.__setattr__(self, "provider_participant_key", participant_key)


@dataclass(frozen=True, slots=True)
class MessageIdentity:
    tenant_public_id: str
    idempotency_key: str
    instagram_connection_public_id: str
    provider_message_id: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_public_id",
            _required_identifier(self.tenant_public_id, "tenant_public_id"),
        )
        idempotency_key = normalize_identifier(
            self.idempotency_key,
            field="idempotency_key",
            required=True,
            maximum=200,
        )
        assert idempotency_key is not None
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(
            self,
            "instagram_connection_public_id",
            _required_identifier(
                self.instagram_connection_public_id,
                "instagram_connection_public_id",
            ),
        )
        object.__setattr__(
            self,
            "provider_message_id",
            normalize_identifier(
                self.provider_message_id,
                field="provider_message_id",
                maximum=200,
            ),
        )


@dataclass(frozen=True, slots=True)
class AssignmentCommand:
    conversation_public_id: str
    assignee_user_public_id: str
    actor_user_public_id: str
    reason: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "conversation_public_id",
            "assignee_user_public_id",
            "actor_user_public_id",
        ):
            object.__setattr__(
                self,
                field,
                _required_identifier(getattr(self, field), field),
            )
        object.__setattr__(
            self,
            "reason",
            normalize_optional_text(self.reason, field="reason", maximum=500),
        )


@dataclass(frozen=True, slots=True)
class ReleaseAssignmentCommand:
    conversation_public_id: str
    actor_user_public_id: str
    reason: str | None = None

    def __post_init__(self) -> None:
        for field in ("conversation_public_id", "actor_user_public_id"):
            object.__setattr__(
                self,
                field,
                _required_identifier(getattr(self, field), field),
            )
        object.__setattr__(
            self,
            "reason",
            normalize_optional_text(self.reason, field="reason", maximum=500),
        )


@dataclass(frozen=True, slots=True)
class ReadStateCommand:
    conversation_public_id: str
    user_public_id: str
    last_read_message_public_id: str

    def __post_init__(self) -> None:
        for field in (
            "conversation_public_id",
            "user_public_id",
            "last_read_message_public_id",
        ):
            object.__setattr__(
                self,
                field,
                _required_identifier(getattr(self, field), field),
            )


@dataclass(frozen=True, slots=True)
class ConversationTransitionCommand:
    conversation_public_id: str
    current_status: str
    target_status: str
    actor_user_public_id: str
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "conversation_public_id",
            _required_identifier(
                self.conversation_public_id,
                "conversation_public_id",
            ),
        )
        object.__setattr__(
            self,
            "actor_user_public_id",
            _required_identifier(self.actor_user_public_id, "actor_user_public_id"),
        )
        current_status = normalize_identifier(
            self.current_status,
            field="current_status",
            required=True,
            maximum=100,
        )
        target_status = normalize_identifier(
            self.target_status,
            field="target_status",
            required=True,
            maximum=100,
        )
        assert current_status is not None
        assert target_status is not None
        validate_conversation_transition(current_status, target_status)
        object.__setattr__(self, "current_status", current_status)
        object.__setattr__(self, "target_status", target_status)
        object.__setattr__(
            self,
            "reason",
            normalize_optional_text(self.reason, field="reason", maximum=500),
        )


def classify_incoming_message(
    *,
    event_type: str,
    normalized_payload: dict[str, object],
) -> tuple[str, str | None, dict[str, object]]:
    """Classify a safe Foundation-08 payload without retaining its raw body."""

    normalized_event_type = normalize_identifier(
        event_type,
        field="event_type",
        required=True,
        maximum=100,
    )
    if normalized_event_type not in SUPPORTED_INBOUND_EVENT_TYPES:
        raise ConversationValidationError("invalid event_type")
    if not isinstance(normalized_payload, dict):
        raise ConversationValidationError("invalid normalized_payload")
    message = normalized_payload.get("message")
    if not isinstance(message, dict):
        raise ConversationValidationError("invalid message payload")

    provider_message_id = normalize_identifier(
        message.get("id") if isinstance(message.get("id"), str) else None,
        field="provider_message_id",
        maximum=200,
    )
    metadata: dict[str, object] = {}
    if provider_message_id is not None:
        metadata["provider_message_id"] = provider_message_id

    raw_text = message.get("text")
    text = (
        normalize_optional_text(raw_text, field="message text", maximum=10_000)
        if isinstance(raw_text, str)
        else None
    )
    if text is not None:
        return "text", text, normalize_metadata(metadata)

    metadata["classification"] = "unsupported"
    return "unsupported", None, normalize_metadata(metadata)


def deterministic_message_key(
    *,
    instagram_connection_public_id: str,
    provider_participant_key: str,
    provider_message_id: str | None,
    inbound_event_idempotency_key: str,
) -> str:
    """Build the stable, namespaced identity for an inbound message."""

    connection_id = _required_identifier(
        instagram_connection_public_id,
        "instagram_connection_public_id",
    )
    participant_key = normalize_identifier(
        provider_participant_key,
        field="provider_participant_key",
        required=True,
        maximum=200,
    )
    message_id = normalize_identifier(
        provider_message_id,
        field="provider_message_id",
        maximum=200,
    )
    event_key = normalize_identifier(
        inbound_event_idempotency_key,
        field="inbound_event_idempotency_key",
        required=True,
        maximum=200,
    )
    assert participant_key is not None
    assert event_key is not None
    encoded = json.dumps(
        {
            "inbound_event_idempotency_key": event_key,
            "instagram_connection_public_id": connection_id,
            "namespace": "conversation-message-v1",
            "provider_message_id": message_id,
            "provider_participant_key": participant_key,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
