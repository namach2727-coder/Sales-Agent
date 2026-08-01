"""Application orchestration for one persisted, provider-neutral AI reply."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from uuid import uuid4

from app.application.knowledge import KnowledgeEngine
from app.application.llm import LLMProvider, LLMResponse
from app.application.prompts import (
    PromptBuilder,
    PromptConversationMessage,
)
from app.application.services.conversation_service import ConversationService
from app.conversation_core.models import Conversation, ConversationMessage
from app.infrastructure.database.repositories import MessageRepository
from app.tenant_management.context import TenantStoreContext


AI_RESPONSE_STATUSES = frozenset({"open", "waiting_for_customer"})


class AIResponseOrchestratorError(Exception):
    code = "ai_response_orchestrator_error"


class AIResponseScopeError(AIResponseOrchestratorError):
    code = "invalid_scope"


class AIResponseConversationStateError(AIResponseOrchestratorError):
    code = "invalid_conversation_state"


class AIResponseCustomerMessageRequiredError(AIResponseOrchestratorError):
    code = "customer_message_required"


class AIResponseInvalidProviderResultError(AIResponseOrchestratorError):
    code = "invalid_provider_result"


class AIResponseOrchestrator:
    """Coordinate existing application boundaries without owning a transaction."""

    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        message_repository: MessageRepository,
        knowledge_engine: KnowledgeEngine,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
    ) -> None:
        self.conversations = conversation_service
        self.messages = message_repository
        self.knowledge = knowledge_engine
        self.prompt_builder = prompt_builder
        self.llm = llm_provider

    def generate_response(
        self,
        conversation_public_id: str,
        *,
        context: TenantStoreContext,
        preferred_language: str | None = None,
        occurred_at: datetime | None = None,
    ) -> str:
        tenant_id, store_id, tenant_public_id, store_public_id = (
            _active_scope(context)
        )
        conversation = self.conversations.get_conversation(
            conversation_public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        _validate_conversation_state(conversation)

        history = self.messages.list_by_conversation(
            conversation.id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        latest_customer_message = _latest_customer_message(history)
        knowledge_context = self.knowledge.retrieve(
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            customer_question=latest_customer_message.text,
            conversation_public_id=conversation.public_id,
        )
        prompt_package = self.prompt_builder.build(
            knowledge_context=knowledge_context,
            conversation_public_id=conversation.public_id,
            recent_messages=tuple(
                _prompt_message(message, conversation.public_id)
                for message in history[:-1]
            ),
            latest_customer_message=latest_customer_message.text,
            preferred_language=preferred_language,
        )
        response = self.llm.generate(prompt_package)
        _validate_provider_result(response)

        response_time = _aware_datetime(
            occurred_at or datetime.now(UTC),
            field="occurred_at",
        )
        assistant_message = self.conversations.append_message(
            conversation.public_id,
            tenant_id=tenant_id,
            store_id=store_id,
            idempotency_key=_assistant_message_key(response),
            direction="outbound",
            content_type="text",
            occurred_at=response_time,
            text=response.text,
            reply_to_message_id=latest_customer_message.id,
            metadata=_assistant_metadata(response),
        )
        if conversation.status == "open":
            self.conversations.change_status(
                conversation.public_id,
                "waiting_for_customer",
                tenant_id=tenant_id,
                store_id=store_id,
                changed_at=response_time,
            )
        return assistant_message.public_id


def _active_scope(
    context: TenantStoreContext,
) -> tuple[int, int, str, str]:
    if not isinstance(context, TenantStoreContext):
        raise AIResponseScopeError("trusted tenant/store context is required")
    if (
        context.tenant_status != "active"
        or context.store_status != "active"
        or context.store_id is None
        or context.store_public_id is None
    ):
        raise AIResponseScopeError("active tenant/store context is required")
    return (
        context.tenant_id,
        context.store_id,
        context.tenant_public_id,
        context.store_public_id,
    )


def _validate_conversation_state(conversation: Conversation) -> None:
    if conversation.status not in AI_RESPONSE_STATUSES:
        raise AIResponseConversationStateError(
            "conversation is not eligible for an AI response"
        )


def _latest_customer_message(
    history: tuple[ConversationMessage, ...],
) -> ConversationMessage:
    if not history:
        raise AIResponseCustomerMessageRequiredError(
            "latest conversation message must be customer text"
        )
    latest = history[-1]
    if (
        latest.direction != "inbound"
        or latest.content_type != "text"
        or latest.text is None
        or not latest.text.strip()
    ):
        raise AIResponseCustomerMessageRequiredError(
            "latest conversation message must be customer text"
        )
    return latest


def _prompt_message(
    message: ConversationMessage,
    conversation_public_id: str,
) -> PromptConversationMessage:
    return PromptConversationMessage(
        public_id=message.public_id,
        conversation_public_id=conversation_public_id,
        direction=message.direction,
        content_type=message.content_type,
        text=message.text,
        occurred_at=_aware_datetime(
            message.occurred_at,
            field="message.occurred_at",
        ),
    )


def _validate_provider_result(response: object) -> None:
    if (
        not isinstance(response, LLMResponse)
        or not isinstance(response.text, str)
        or not response.text.strip()
    ):
        raise AIResponseInvalidProviderResultError(
            "LLM provider returned an invalid response"
        )


def _assistant_message_key(response: LLMResponse) -> str:
    request_key = response.request_public_id or str(uuid4())
    return hashlib.sha256(
        f"ai-response:{request_key}".encode("utf-8")
    ).hexdigest()


def _assistant_metadata(response: LLMResponse) -> dict[str, object]:
    metadata: dict[str, object] = {
        "author_type": "assistant",
        "source": "ai_response_orchestrator",
        "llm_provider": response.provider,
        "llm_model": response.model,
    }
    optional_values: tuple[tuple[str, object | None], ...] = (
        ("llm_finish_reason", response.finish_reason),
        ("llm_request_public_id", response.request_public_id),
        ("llm_provider_request_id", response.provider_request_id),
        ("llm_input_tokens", response.input_tokens),
        ("llm_output_tokens", response.output_tokens),
        ("llm_total_tokens", response.total_tokens),
    )
    metadata.update(
        (key, value) for key, value in optional_values if value is not None
    )
    return metadata


def _aware_datetime(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise AIResponseOrchestratorError(f"invalid {field}")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value
