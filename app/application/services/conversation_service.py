"""Application orchestration for the MVP conversation core."""

from __future__ import annotations

from datetime import UTC, datetime

from app.conversation_core.domain import (
    MESSAGE_CONTENT_TYPES,
    MESSAGE_DIRECTIONS,
    ensure_conversation_mutable,
    normalize_identifier,
    normalize_metadata,
    normalize_optional_text,
    validate_conversation_transition,
)
from app.conversation_core.exceptions import (
    ConversationConflictError,
    ConversationNotFoundError,
    ConversationValidationError,
)
from app.conversation_core.models import Conversation, ConversationMessage
from app.infrastructure.database.repositories import (
    ConversationRepository,
    MessageRepository,
)


class ConversationService:
    """Coordinate conversation rules without owning a database transaction."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self.conversations = conversation_repository
        self.messages = message_repository

    def create_conversation(
        self,
        *,
        tenant_id: int,
        store_id: int,
        instagram_connection_id: int,
        provider_participant_key: str,
        subject: str | None = None,
    ) -> Conversation:
        participant_key = _required_identifier(
            provider_participant_key,
            field="provider_participant_key",
            maximum=200,
        )
        conversation = Conversation(
            tenant_id=_positive_id(tenant_id, field="tenant_id"),
            store_id=_positive_id(store_id, field="store_id"),
            instagram_connection_id=_positive_id(
                instagram_connection_id,
                field="instagram_connection_id",
            ),
            provider_participant_key=participant_key,
            subject=normalize_optional_text(
                subject,
                field="subject",
                maximum=500,
            ),
            status="open",
        )
        return self.conversations.create(conversation)

    def get_conversation(
        self,
        conversation_public_id: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> Conversation:
        public_id = _required_identifier(
            conversation_public_id,
            field="conversation_public_id",
            maximum=36,
        )
        conversation = self.conversations.get_by_public_id(
            public_id,
            tenant_id=_positive_id(tenant_id, field="tenant_id"),
            store_id=_positive_id(store_id, field="store_id"),
        )
        if conversation is None:
            raise ConversationNotFoundError("conversation not found")
        return conversation

    def get_or_create_conversation(
        self,
        *,
        tenant_id: int,
        store_id: int,
        instagram_connection_id: int,
        provider_participant_key: str,
        subject: str | None = None,
    ) -> Conversation:
        scoped_tenant_id = _positive_id(tenant_id, field="tenant_id")
        scoped_store_id = _positive_id(store_id, field="store_id")
        connection_id = _positive_id(
            instagram_connection_id,
            field="instagram_connection_id",
        )
        participant_key = _required_identifier(
            provider_participant_key,
            field="provider_participant_key",
            maximum=200,
        )
        for conversation in self.conversations.list_by_store(
            tenant_id=scoped_tenant_id,
            store_id=scoped_store_id,
        ):
            if (
                conversation.instagram_connection_id == connection_id
                and conversation.provider_participant_key == participant_key
            ):
                return conversation
        return self.create_conversation(
            tenant_id=scoped_tenant_id,
            store_id=scoped_store_id,
            instagram_connection_id=connection_id,
            provider_participant_key=participant_key,
            subject=subject,
        )

    def append_message(
        self,
        conversation_public_id: str,
        *,
        tenant_id: int,
        store_id: int,
        idempotency_key: str,
        direction: str,
        content_type: str,
        occurred_at: datetime,
        text: str | None = None,
        instagram_inbound_event_id: int | None = None,
        provider_message_id: str | None = None,
        sender_participant_id: int | None = None,
        reply_to_message_id: int | None = None,
        provider_event_at: datetime | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ConversationMessage:
        conversation = self.get_conversation(
            conversation_public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        ensure_conversation_mutable(conversation.status)
        message_key = _required_identifier(
            idempotency_key,
            field="idempotency_key",
            maximum=64,
        )
        if self.messages.exists_message_key(
            message_key,
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
        ):
            raise ConversationConflictError("message already exists")

        message = self._build_message(
            conversation,
            idempotency_key=message_key,
            direction=direction,
            content_type=content_type,
            occurred_at=occurred_at,
            text=text,
            instagram_inbound_event_id=instagram_inbound_event_id,
            provider_message_id=provider_message_id,
            sender_participant_id=sender_participant_id,
            reply_to_message_id=reply_to_message_id,
            provider_event_at=provider_event_at,
            metadata=metadata,
        )
        created = self.messages.create(message)
        self._record_message(conversation, created)
        self.conversations.flush()
        return created

    def archive_conversation(
        self,
        conversation_public_id: str,
        *,
        tenant_id: int,
        store_id: int,
        archived_at: datetime | None = None,
    ) -> Conversation:
        conversation = self.get_conversation(
            conversation_public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        validate_conversation_transition(conversation.status, "archived")
        timestamp = _aware_datetime(
            archived_at or datetime.now(UTC),
            field="archived_at",
        )
        archived = self.conversations.archive(
            conversation.public_id,
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
            archived_at=timestamp,
        )
        if archived is None:
            raise ConversationNotFoundError("conversation not found")
        return archived

    def change_status(
        self,
        conversation_public_id: str,
        target_status: str,
        *,
        tenant_id: int,
        store_id: int,
        changed_at: datetime | None = None,
    ) -> Conversation:
        conversation = self.get_conversation(
            conversation_public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        target = _required_identifier(
            target_status,
            field="target_status",
            maximum=30,
        )
        validate_conversation_transition(conversation.status, target)
        timestamp = _aware_datetime(
            changed_at or datetime.now(UTC),
            field="changed_at",
        )
        if target == "archived":
            return self.archive_conversation(
                conversation.public_id,
                tenant_id=conversation.tenant_id,
                store_id=conversation.store_id,
                archived_at=timestamp,
            )

        conversation.closed_at = timestamp if target == "closed" else None
        updated = self.conversations.update_status(
            conversation.public_id,
            target,
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
        )
        if updated is None:
            raise ConversationNotFoundError("conversation not found")
        return updated

    @staticmethod
    def _build_message(
        conversation: Conversation,
        *,
        idempotency_key: str,
        direction: str,
        content_type: str,
        occurred_at: datetime,
        text: str | None,
        instagram_inbound_event_id: int | None,
        provider_message_id: str | None,
        sender_participant_id: int | None,
        reply_to_message_id: int | None,
        provider_event_at: datetime | None,
        metadata: dict[str, object] | None,
    ) -> ConversationMessage:
        normalized_direction = _message_value(
            direction,
            field="direction",
            allowed=MESSAGE_DIRECTIONS,
        )
        normalized_content_type = _message_value(
            content_type,
            field="content_type",
            allowed=MESSAGE_CONTENT_TYPES,
        )
        normalized_text = normalize_optional_text(
            text,
            field="text",
            maximum=10_000,
        )
        if normalized_content_type == "text" and normalized_text is None:
            raise ConversationValidationError(
                "text is required for text content"
            )
        if (
            normalized_direction == "inbound"
            and instagram_inbound_event_id is None
        ):
            raise ConversationValidationError(
                "instagram_inbound_event_id is required for inbound messages"
            )

        message_time = _aware_datetime(occurred_at, field="occurred_at")
        provider_time = (
            _aware_datetime(provider_event_at, field="provider_event_at")
            if provider_event_at is not None
            else None
        )
        message = ConversationMessage(
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
            conversation_id=conversation.id,
            instagram_connection_id=conversation.instagram_connection_id,
            instagram_inbound_event_id=_optional_positive_id(
                instagram_inbound_event_id,
                field="instagram_inbound_event_id",
            ),
            provider_message_id=normalize_identifier(
                provider_message_id,
                field="provider_message_id",
                maximum=200,
            ),
            idempotency_key=idempotency_key,
            direction=normalized_direction,
            content_type=normalized_content_type,
            text=normalized_text,
            sender_participant_id=_optional_positive_id(
                sender_participant_id,
                field="sender_participant_id",
            ),
            reply_to_message_id=_optional_positive_id(
                reply_to_message_id,
                field="reply_to_message_id",
            ),
            provider_event_at=provider_time,
            occurred_at=message_time,
            metadata_json=normalize_metadata(metadata),
        )
        return message

    @staticmethod
    def _record_message(
        conversation: Conversation,
        message: ConversationMessage,
    ) -> None:
        conversation.last_message_at = _latest_timestamp(
            conversation.last_message_at,
            message.occurred_at,
        )
        if message.direction == "inbound":
            conversation.inbound_message_count += 1
            conversation.message_count += 1
            conversation.last_inbound_message_at = _latest_timestamp(
                conversation.last_inbound_message_at,
                message.occurred_at,
            )
        elif message.direction == "outbound":
            conversation.outbound_message_count += 1
            conversation.message_count += 1
            conversation.last_outbound_message_at = _latest_timestamp(
                conversation.last_outbound_message_at,
                message.occurred_at,
            )
        conversation.revision += 1


def _positive_id(value: int, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConversationValidationError(f"invalid {field}")
    return value


def _optional_positive_id(value: int | None, *, field: str) -> int | None:
    return None if value is None else _positive_id(value, field=field)


def _required_identifier(
    value: str,
    *,
    field: str,
    maximum: int,
) -> str:
    normalized = normalize_identifier(
        value,
        field=field,
        required=True,
        maximum=maximum,
    )
    assert normalized is not None
    return normalized


def _message_value(
    value: str,
    *,
    field: str,
    allowed: frozenset[str],
) -> str:
    normalized = _required_identifier(value, field=field, maximum=30)
    if normalized not in allowed:
        raise ConversationValidationError(f"invalid {field}")
    return normalized


def _aware_datetime(value: datetime, *, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ConversationValidationError(f"{field} must be timezone-aware")
    return value


def _latest_timestamp(
    current: datetime | None,
    candidate: datetime,
) -> datetime:
    if current is None:
        return candidate
    normalized_current = (
        current.replace(tzinfo=UTC) if current.tzinfo is None else current
    )
    normalized_candidate = candidate.astimezone(UTC)
    return (
        candidate
        if normalized_candidate >= normalized_current.astimezone(UTC)
        else current
    )
