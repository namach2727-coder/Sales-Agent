from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import models as registered_models  # noqa: F401
from app.application.knowledge import KnowledgeContext
from app.application.llm import LLMProviderUnavailableError, LLMResponse
from app.application.prompts import PromptMetadata, PromptPackage
from app.application.services import (
    AIResponseConversationStateError,
    AIResponseInvalidProviderResultError,
    AIResponseOrchestrator,
    ConversationService,
)
import app.application.services.ai_response_orchestrator as orchestrator_module
from app.conversation_core.models import Conversation, ConversationMessage
from app.database import Base
from app.infrastructure.database.repositories import (
    ConversationRepository,
    MessageRepository,
)
from app.instagram_channel.models import InstagramConnection
from app.models import Store, Tenant
from app.tenant_management.context import TenantStoreContext


TENANT_PUBLIC_ID = "00000000-0000-4000-8000-000000000101"
STORE_PUBLIC_ID = "00000000-0000-4000-8000-000000000102"
CONVERSATION_PUBLIC_ID = "00000000-0000-4000-8000-000000000103"
PROMPT_PACKAGE = PromptPackage(
    system_prompt="system",
    user_prompt="user",
    metadata=PromptMetadata(
        conversation_public_id=CONVERSATION_PUBLIC_ID,
        preferred_language="fa-IR",
        knowledge_confidence=0.0,
        business_profile_public_id=None,
        product_public_ids=(),
        faq_public_ids=(),
        business_rule_public_ids=(),
        knowledge_snippet_public_ids=(),
        recent_message_public_ids=(),
    ),
)


class FakeConversationRepository:
    def __init__(self, conversation: Conversation) -> None:
        self.conversation = conversation
        self.flush_count = 0

    def get_by_public_id(
        self,
        public_id: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> Conversation | None:
        if (
            public_id == self.conversation.public_id
            and tenant_id == self.conversation.tenant_id
            and store_id == self.conversation.store_id
        ):
            return self.conversation
        return None

    def update_status(
        self,
        public_id: str,
        status: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> Conversation | None:
        conversation = self.get_by_public_id(
            public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        if conversation is not None:
            conversation.status = status
            conversation.revision += 1
        return conversation

    def flush(self) -> None:
        self.flush_count += 1


class FakeMessageRepository:
    def __init__(self, messages: list[ConversationMessage]) -> None:
        self.items = messages
        self.create_calls: list[ConversationMessage] = []

    def list_by_conversation(
        self,
        conversation_id: int,
        *,
        tenant_id: int,
        store_id: int,
    ) -> tuple[ConversationMessage, ...]:
        return tuple(
            message
            for message in self.items
            if message.conversation_id == conversation_id
            and message.tenant_id == tenant_id
            and message.store_id == store_id
        )

    def exists_message_key(
        self,
        idempotency_key: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> bool:
        return any(
            message.idempotency_key == idempotency_key
            and message.tenant_id == tenant_id
            and message.store_id == store_id
            for message in self.items
        )

    def create(self, message: ConversationMessage) -> ConversationMessage:
        message.id = len(self.items) + 1
        message.public_id = str(uuid.uuid4())
        message.created_at = datetime.now(UTC)
        self.items.append(message)
        self.create_calls.append(message)
        return message


class FakeKnowledgeEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def retrieve(self, **kwargs: Any) -> KnowledgeContext:
        self.calls.append(kwargs)
        return KnowledgeContext(
            matched_products=(),
            faq=(),
            business_profile=None,
            business_rules=(),
            knowledge_snippets=(),
            confidence=0.0,
            conversation_public_id=kwargs["conversation_public_id"],
        )


class FakePromptBuilder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def build(self, **kwargs: Any) -> PromptPackage:
        self.calls.append(kwargs)
        return PROMPT_PACKAGE


class FakeProvider:
    def __init__(
        self,
        response: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or LLMResponse(
            text="Assistant answer",
            provider="fake",
            model="fake-model",
            finish_reason="completed",
            input_tokens=20,
            output_tokens=7,
            total_tokens=27,
            request_public_id=(
                "00000000-0000-4000-8000-000000000104"
            ),
            provider_request_id="provider-request-1",
        )
        self.error = error
        self.calls: list[PromptPackage] = []

    def generate(self, prompt_package: PromptPackage) -> LLMResponse:
        self.calls.append(prompt_package)
        if self.error is not None:
            raise self.error
        return self.response  # type: ignore[return-value]


def _context() -> TenantStoreContext:
    return TenantStoreContext(
        tenant_id=1,
        tenant_public_id=TENANT_PUBLIC_ID,
        tenant_status="active",
        membership_id=None,
        store_id=10,
        store_public_id=STORE_PUBLIC_ID,
        store_status="active",
        platform_access=False,
    )


def _conversation(*, status: str = "open") -> Conversation:
    return Conversation(
        id=100,
        public_id=CONVERSATION_PUBLIC_ID,
        tenant_id=1,
        store_id=10,
        instagram_connection_id=1000,
        provider_participant_key="customer-1",
        status=status,
        message_count=2,
        inbound_message_count=1,
        outbound_message_count=1,
        revision=1,
    )


def _history(conversation: Conversation) -> list[ConversationMessage]:
    started = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    return [
        ConversationMessage(
            id=1,
            public_id="00000000-0000-4000-8000-000000000105",
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
            conversation_id=conversation.id,
            instagram_connection_id=conversation.instagram_connection_id,
            idempotency_key="previous-message",
            direction="outbound",
            content_type="text",
            text="Previous answer",
            occurred_at=started,
        ),
        ConversationMessage(
            id=2,
            public_id="00000000-0000-4000-8000-000000000106",
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
            conversation_id=conversation.id,
            instagram_connection_id=conversation.instagram_connection_id,
            instagram_inbound_event_id=500,
            idempotency_key="latest-customer-message",
            direction="inbound",
            content_type="text",
            text="What is the price?",
            occurred_at=started + timedelta(minutes=1),
        ),
    ]


def _orchestrator(
    *,
    conversation: Conversation | None = None,
    provider: FakeProvider | None = None,
) -> SimpleNamespace:
    selected_conversation = conversation or _conversation()
    conversation_repository = FakeConversationRepository(
        selected_conversation
    )
    message_repository = FakeMessageRepository(
        _history(selected_conversation)
    )
    conversation_service = ConversationService(
        conversation_repository,  # type: ignore[arg-type]
        message_repository,  # type: ignore[arg-type]
    )
    knowledge = FakeKnowledgeEngine()
    prompt_builder = FakePromptBuilder()
    llm = provider or FakeProvider()
    orchestrator = AIResponseOrchestrator(
        conversation_service=conversation_service,
        message_repository=message_repository,  # type: ignore[arg-type]
        knowledge_engine=knowledge,  # type: ignore[arg-type]
        prompt_builder=prompt_builder,  # type: ignore[arg-type]
        llm_provider=llm,
    )
    return SimpleNamespace(
        orchestrator=orchestrator,
        conversation=selected_conversation,
        conversations=conversation_repository,
        messages=message_repository,
        knowledge=knowledge,
        prompt_builder=prompt_builder,
        provider=llm,
    )


def test_successful_orchestration_invokes_pipeline_and_persists_assistant() -> None:
    setup = _orchestrator()
    occurred_at = datetime(2026, 8, 1, 8, 2, tzinfo=UTC)

    public_id = setup.orchestrator.generate_response(
        CONVERSATION_PUBLIC_ID,
        context=_context(),
        preferred_language="fa-IR",
        occurred_at=occurred_at,
    )

    assert setup.knowledge.calls == [
        {
            "tenant_public_id": TENANT_PUBLIC_ID,
            "store_public_id": STORE_PUBLIC_ID,
            "customer_question": "What is the price?",
            "conversation_public_id": CONVERSATION_PUBLIC_ID,
        }
    ]
    prompt_call = setup.prompt_builder.calls[0]
    assert prompt_call["latest_customer_message"] == "What is the price?"
    assert prompt_call["preferred_language"] == "fa-IR"
    assert len(prompt_call["recent_messages"]) == 1
    assert setup.provider.calls == [PROMPT_PACKAGE]

    assistant = setup.messages.create_calls[0]
    assert public_id == assistant.public_id
    assert assistant.direction == "outbound"
    assert assistant.content_type == "text"
    assert assistant.text == "Assistant answer"
    assert assistant.reply_to_message_id == 2
    assert assistant.occurred_at == occurred_at
    assert setup.conversation.message_count == 3
    assert setup.conversation.outbound_message_count == 2
    assert setup.conversation.last_message_at == occurred_at
    assert setup.conversation.last_outbound_message_at == occurred_at
    assert setup.conversation.status == "waiting_for_customer"


def test_token_usage_and_provider_trace_are_persisted_in_metadata() -> None:
    setup = _orchestrator()

    setup.orchestrator.generate_response(
        CONVERSATION_PUBLIC_ID,
        context=_context(),
    )

    metadata = setup.messages.create_calls[0].metadata_json
    assert metadata == {
        "author_type": "assistant",
        "llm_finish_reason": "completed",
        "llm_input_tokens": 20,
        "llm_model": "fake-model",
        "llm_output_tokens": 7,
        "llm_provider": "fake",
        "llm_provider_request_id": "provider-request-1",
        "llm_request_public_id": (
            "00000000-0000-4000-8000-000000000104"
        ),
        "llm_total_tokens": 27,
        "source": "ai_response_orchestrator",
    }


def test_provider_failure_does_not_persist_or_change_conversation() -> None:
    failure = LLMProviderUnavailableError("provider unavailable")
    setup = _orchestrator(provider=FakeProvider(error=failure))

    with pytest.raises(LLMProviderUnavailableError) as raised:
        setup.orchestrator.generate_response(
            CONVERSATION_PUBLIC_ID,
            context=_context(),
        )

    assert raised.value is failure
    assert setup.messages.create_calls == []
    assert setup.conversation.status == "open"
    assert setup.conversation.message_count == 2


def test_blank_or_non_contract_provider_response_is_rejected() -> None:
    blank_response = SimpleNamespace(text="   ")
    setup = _orchestrator(provider=FakeProvider(response=blank_response))

    with pytest.raises(AIResponseInvalidProviderResultError):
        setup.orchestrator.generate_response(
            CONVERSATION_PUBLIC_ID,
            context=_context(),
        )

    assert setup.messages.create_calls == []
    assert setup.conversation.status == "open"


@pytest.mark.parametrize("status", ["handoff_requested", "human_active", "closed", "archived"])
def test_ineligible_conversation_status_stops_before_knowledge_or_provider(
    status: str,
) -> None:
    setup = _orchestrator(conversation=_conversation(status=status))

    with pytest.raises(AIResponseConversationStateError):
        setup.orchestrator.generate_response(
            CONVERSATION_PUBLIC_ID,
            context=_context(),
        )

    assert setup.knowledge.calls == []
    assert setup.provider.calls == []
    assert setup.messages.create_calls == []


def test_caller_rollback_reverts_message_counters_and_status() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        label = uuid.uuid4().hex
        tenant = Tenant(
            public_id=TENANT_PUBLIC_ID,
            name=label,
            slug=label,
            status="active",
        )
        db.add(tenant)
        db.flush()
        store = Store(
            public_id=STORE_PUBLIC_ID,
            tenant_id=tenant.id,
            name=label,
            slug=label,
            status="active",
            currency_code="IRR",
        )
        db.add(store)
        db.flush()
        connection = InstagramConnection(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_account_id=f"ig-{label}",
            status="active",
        )
        db.add(connection)
        db.flush()
        conversations = ConversationRepository(db)
        messages = MessageRepository(db)
        service = ConversationService(conversations, messages)
        conversation = service.create_conversation(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            provider_participant_key="customer-rollback",
        )
        service.append_message(
            conversation.public_id,
            tenant_id=tenant.id,
            store_id=store.id,
            idempotency_key="rollback-inbound",
            direction="inbound",
            content_type="text",
            occurred_at=datetime.now(UTC),
            text="Question",
            instagram_inbound_event_id=999,
        )
        db.commit()

        knowledge = FakeKnowledgeEngine()
        prompt_builder = FakePromptBuilder()
        orchestrator = AIResponseOrchestrator(
            conversation_service=service,
            message_repository=messages,
            knowledge_engine=knowledge,  # type: ignore[arg-type]
            prompt_builder=prompt_builder,  # type: ignore[arg-type]
            llm_provider=FakeProvider(),
        )
        context = TenantStoreContext(
            tenant_id=tenant.id,
            tenant_public_id=tenant.public_id,
            tenant_status="active",
            membership_id=None,
            store_id=store.id,
            store_public_id=store.public_id,
            store_status="active",
        )

        orchestrator.generate_response(
            conversation.public_id,
            context=context,
        )
        assert conversation.status == "waiting_for_customer"
        assert conversation.message_count == 2
        assert len(
            messages.list_by_conversation(
                conversation.id,
                tenant_id=tenant.id,
                store_id=store.id,
            )
        ) == 2

        db.rollback()
        db.expire_all()
        restored = db.scalar(
            select(Conversation).where(Conversation.id == conversation.id)
        )
        assert restored is not None
        assert restored.status == "open"
        assert restored.message_count == 1
        assert restored.outbound_message_count == 0
        assert len(
            messages.list_by_conversation(
                restored.id,
                tenant_id=tenant.id,
                store_id=store.id,
            )
        ) == 1
    engine.dispose()


def test_orchestrator_has_no_instagram_outbound_dependency() -> None:
    source = Path(orchestrator_module.__file__).read_text(
        encoding="utf-8"
    ).casefold()

    for prohibited in ("instagram", "send_message", "meta_send", "outbound api"):
        assert prohibited not in source
