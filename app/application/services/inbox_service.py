"""Human control operations for the authenticated customer inbox."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.application.outbound import OutboundDeliveryResult
from app.application.services.conversation_service import ConversationService
from app.application.services.instagram_outbound_delivery import (
    InstagramOutboundDeliveryService,
)
from app.conversation_core.domain import normalize_optional_text
from app.conversation_core.exceptions import (
    ConversationCoreError,
    ConversationValidationError,
)
from app.conversation_core.models import Conversation, ConversationMessage
from app.tenant_management.context import TenantStoreContext


class InboxError(ConversationCoreError):
    """Base error for customer inbox actions."""


class InboxConversationStateError(InboxError):
    code = "conversation_state_conflict"


class InboxManualReplyError(InboxError):
    code = "manual_reply_unavailable"


@dataclass(frozen=True, slots=True)
class ManualReplyResult:
    message: ConversationMessage
    delivery: OutboundDeliveryResult


class InboxService:
    """Coordinate takeover, resume, and one manual outbound reply."""

    def __init__(
        self,
        conversation_service: ConversationService,
        outbound_delivery: InstagramOutboundDeliveryService | None = None,
    ) -> None:
        self.conversations = conversation_service
        self.outbound = outbound_delivery

    def take_over(
        self,
        conversation_public_id: str,
        *,
        context: TenantStoreContext,
        changed_at: datetime | None = None,
    ) -> Conversation:
        conversation = self._conversation(conversation_public_id, context)
        if conversation.status == "human_active":
            return conversation
        if conversation.status not in {
            "open",
            "waiting_for_customer",
            "handoff_requested",
        }:
            raise InboxConversationStateError(
                "conversation cannot be taken over in its current state"
            )
        return self.conversations.change_status(
            conversation.public_id,
            "human_active",
            tenant_id=context.tenant_id,
            store_id=_store_id(context),
            changed_at=changed_at,
        )

    def resume_ai(
        self,
        conversation_public_id: str,
        *,
        context: TenantStoreContext,
        changed_at: datetime | None = None,
    ) -> Conversation:
        conversation = self._conversation(conversation_public_id, context)
        if conversation.status in {"open", "waiting_for_customer"}:
            return conversation
        if conversation.status != "human_active":
            raise InboxConversationStateError(
                "conversation cannot resume AI in its current state"
            )
        return self.conversations.change_status(
            conversation.public_id,
            "open",
            tenant_id=context.tenant_id,
            store_id=_store_id(context),
            changed_at=changed_at,
        )

    def send_manual_reply(
        self,
        conversation_public_id: str,
        *,
        text: str,
        context: TenantStoreContext,
        idempotency_key: str | None = None,
        occurred_at: datetime | None = None,
        correlation_id: str | None = None,
        before_provider_call: Callable[[], None] | None = None,
    ) -> ManualReplyResult:
        conversation = self._conversation(conversation_public_id, context)
        if conversation.status != "human_active":
            raise InboxConversationStateError(
                "manual replies require human takeover"
            )
        history = self.conversations.messages.list_by_conversation(
            conversation.id,
            tenant_id=context.tenant_id,
            store_id=_store_id(context),
        )
        inbound = next(
            (
                message
                for message in reversed(history)
                if message.direction == "inbound"
            ),
            None,
        )
        if inbound is None:
            raise InboxManualReplyError("conversation has no customer message")
        normalized = normalize_optional_text(text, field="text", maximum=10_000)
        if normalized is None:
            raise ConversationValidationError("text is required")
        key = idempotency_key or f"human:{uuid4().hex}"
        if len(key) > 64 or not key.strip():
            raise ConversationValidationError("invalid idempotency_key")
        message = self.conversations.append_message(
            conversation.public_id,
            tenant_id=context.tenant_id,
            store_id=_store_id(context),
            idempotency_key=key.strip(),
            direction="outbound",
            content_type="text",
            occurred_at=occurred_at or datetime.now(UTC),
            text=normalized,
            reply_to_message_id=inbound.id,
            metadata={
                "author_type": "human",
                "source": "inbox_manual_reply",
            },
        )
        if self.outbound is None:
            raise InboxManualReplyError("Instagram delivery is unavailable")
        delivery = self.outbound.deliver(
            message.public_id,
            conversation_public_id=conversation.public_id,
            context=context,
            correlation_id=correlation_id,
            before_provider_call=before_provider_call,
        )
        return ManualReplyResult(message=message, delivery=delivery)

    def _conversation(
        self,
        conversation_public_id: str,
        context: TenantStoreContext,
    ) -> Conversation:
        return self.conversations.get_conversation(
            conversation_public_id,
            tenant_id=context.tenant_id,
            store_id=_store_id(context),
        )


def _store_id(context: TenantStoreContext) -> int:
    if context.store_id is None:
        raise InboxManualReplyError("store context is required")
    return context.store_id
