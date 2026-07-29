"""Application pipeline from a trusted Instagram event to Conversation Core."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.application.services.conversation_service import ConversationService
from app.conversation_core.domain import (
    IncomingConversationEvent,
    classify_incoming_message,
    deterministic_message_key,
    normalize_identifier,
)
from app.conversation_core.exceptions import ConversationConflictError
from app.infrastructure.database.repositories.instagram_inbound_message_repository import (
    InstagramInboundEventContext,
    InstagramInboundMessageRepository,
    PersistedMessageReference,
)
from app.instagram_channel.domain import (
    ROUTABLE_CONNECTION_STATUSES,
    WRITABLE_STORE_STATUSES,
)
from app.instagram_channel.exceptions import InstagramChannelNotFoundError


ProcessingStatus = Literal["processed", "duplicate", "ignored"]


@dataclass(frozen=True, slots=True)
class InstagramInboundProcessingResult:
    status: ProcessingStatus
    conversation_public_id: str | None = None
    message_public_id: str | None = None
    created_conversation: bool = False
    reason: str | None = None


class InstagramInboundMessageService:
    """Persist one already verified and normalized Instagram message."""

    def __init__(
        self,
        repository: InstagramInboundMessageRepository,
        conversation_service: ConversationService,
    ) -> None:
        self.repository = repository
        self.conversations = conversation_service

    def process(
        self,
        event_public_id: str,
    ) -> InstagramInboundProcessingResult:
        normalized_event_public_id = normalize_identifier(
            event_public_id,
            field="instagram_inbound_event_public_id",
            required=True,
            maximum=36,
        )
        assert normalized_event_public_id is not None
        context = self.repository.get_event_context(
            normalized_event_public_id
        )
        if context is None:
            raise InstagramChannelNotFoundError(
                "Instagram inbound event was not found"
            )

        scope_reason = self._scope_rejection_reason(context)
        if scope_reason is not None:
            return self._ignored(scope_reason)
        if context.event_processing_status == "ignored":
            return self._ignored("unsupported_event")
        if context.event_processing_status != "ready":
            return self._ignored("event_not_ready")
        if context.event_type != "messaging":
            return self._ignored("unsupported_event")
        if context.external_sender_id is None:
            return self._ignored("missing_sender")

        content_type, text, classification_metadata = (
            classify_incoming_message(
                event_type=context.event_type,
                normalized_payload=context.normalized_payload,
            )
        )
        metadata = {
            **classification_metadata,
            "provider": "instagram",
            "source": "instagram_webhook",
            "sender_instagram_id": context.external_sender_id,
        }
        if context.external_recipient_id is not None:
            metadata["recipient_instagram_id"] = (
                context.external_recipient_id
            )

        incoming = IncomingConversationEvent(
            instagram_inbound_event_public_id=context.event_public_id,
            tenant_public_id=context.tenant_public_id,
            store_public_id=context.store_public_id,
            instagram_connection_public_id=context.connection_public_id,
            provider_participant_key=context.external_sender_id,
            provider_message_id=context.provider_message_id,
            idempotency_key=context.event_idempotency_key,
            event_type=context.event_type,
            direction="inbound",
            content_type=content_type,
            text=text,
            provider_event_at=_aware(context.provider_event_at),
            metadata=metadata,
        )
        message_key = deterministic_message_key(
            instagram_connection_public_id=(
                incoming.instagram_connection_public_id
            ),
            provider_participant_key=incoming.provider_participant_key,
            provider_message_id=incoming.provider_message_id,
            inbound_event_idempotency_key=incoming.idempotency_key,
        )
        duplicate = self.repository.find_message_reference(
            message_key,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
        )
        if duplicate is not None:
            return self._duplicate(duplicate)

        existing_conversation_public_id = (
            self.repository.find_conversation_public_id(
                tenant_id=context.tenant_id,
                store_id=context.store_id,
                connection_id=context.connection_id,
                provider_participant_key=(
                    incoming.provider_participant_key
                ),
            )
        )
        conversation = self.conversations.get_or_create_conversation(
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            instagram_connection_id=context.connection_id,
            provider_participant_key=incoming.provider_participant_key,
        )
        try:
            message = self.conversations.append_message(
                conversation.public_id,
                tenant_id=context.tenant_id,
                store_id=context.store_id,
                idempotency_key=message_key,
                direction=incoming.direction,
                content_type=incoming.content_type,
                occurred_at=_aware(context.occurred_at) or datetime.now(UTC),
                text=incoming.text,
                instagram_inbound_event_id=context.event_id,
                provider_message_id=incoming.provider_message_id,
                provider_event_at=incoming.provider_event_at,
                metadata=incoming.metadata,
            )
        except ConversationConflictError:
            duplicate = self.repository.find_message_reference(
                message_key,
                tenant_id=context.tenant_id,
                store_id=context.store_id,
            )
            if duplicate is None:
                raise
            return self._duplicate(duplicate)

        return InstagramInboundProcessingResult(
            status="processed",
            conversation_public_id=conversation.public_id,
            message_public_id=message.public_id,
            created_conversation=(
                existing_conversation_public_id is None
            ),
        )

    @staticmethod
    def _scope_rejection_reason(
        context: InstagramInboundEventContext,
    ) -> str | None:
        if context.tenant_status != "active":
            return "inactive_tenant"
        if context.store_status not in WRITABLE_STORE_STATUSES:
            return "inactive_store"
        if context.connection_status not in ROUTABLE_CONNECTION_STATUSES:
            return "inactive_channel"
        return None

    @staticmethod
    def _ignored(reason: str) -> InstagramInboundProcessingResult:
        return InstagramInboundProcessingResult(
            status="ignored",
            reason=reason,
        )

    @staticmethod
    def _duplicate(
        reference: PersistedMessageReference,
    ) -> InstagramInboundProcessingResult:
        return InstagramInboundProcessingResult(
            status="duplicate",
            conversation_public_id=reference.conversation_public_id,
            message_public_id=reference.message_public_id,
            created_conversation=False,
        )


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value
