from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

import pytest

from app.application.services import ConversationService
from app.conversation_core.exceptions import (
    ConversationConflictError,
    ConversationInvalidTransitionError,
    ConversationNotFoundError,
)
from app.conversation_core.models import Conversation, ConversationMessage


class FakeConversationRepository:
    def __init__(self) -> None:
        self.items: list[Conversation] = []
        self.flush_count = 0

    def create(self, conversation: Conversation) -> Conversation:
        conversation.id = len(self.items) + 1
        conversation.public_id = str(uuid.uuid4())
        conversation.message_count = 0
        conversation.inbound_message_count = 0
        conversation.outbound_message_count = 0
        conversation.revision = 1
        conversation.created_at = datetime.now(UTC)
        conversation.updated_at = conversation.created_at
        self.items.append(conversation)
        return conversation

    def get_by_public_id(
        self,
        public_id: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> Conversation | None:
        return next(
            (
                conversation
                for conversation in self.items
                if conversation.public_id == public_id
                and conversation.tenant_id == tenant_id
                and conversation.store_id == store_id
            ),
            None,
        )

    def list_by_store(
        self,
        *,
        tenant_id: int,
        store_id: int,
    ) -> tuple[Conversation, ...]:
        return tuple(
            conversation
            for conversation in self.items
            if conversation.tenant_id == tenant_id
            and conversation.store_id == store_id
        )

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

    def archive(
        self,
        public_id: str,
        *,
        tenant_id: int,
        store_id: int,
        archived_at: datetime | None = None,
    ) -> Conversation | None:
        conversation = self.get_by_public_id(
            public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
        if conversation is not None:
            conversation.status = "archived"
            conversation.archived_at = archived_at
            conversation.revision += 1
        return conversation

    def flush(self) -> None:
        self.flush_count += 1


class FakeMessageRepository:
    def __init__(self) -> None:
        self.items: list[ConversationMessage] = []

    def create(self, message: ConversationMessage) -> ConversationMessage:
        message.id = len(self.items) + 1
        message.public_id = str(uuid.uuid4())
        message.created_at = datetime.now(UTC)
        self.items.append(message)
        return message

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


@pytest.fixture
def repositories() -> tuple[
    FakeConversationRepository,
    FakeMessageRepository,
]:
    return FakeConversationRepository(), FakeMessageRepository()


@pytest.fixture
def service(
    repositories: tuple[
        FakeConversationRepository,
        FakeMessageRepository,
    ],
) -> ConversationService:
    conversations, messages = repositories
    return ConversationService(conversations, messages)  # type: ignore[arg-type]


def create_conversation(
    service: ConversationService,
    *,
    tenant_id: int = 1,
    store_id: int = 10,
    connection_id: int = 100,
    participant_key: str = "customer-1",
) -> Conversation:
    return service.create_conversation(
        tenant_id=tenant_id,
        store_id=store_id,
        instagram_connection_id=connection_id,
        provider_participant_key=participant_key,
    )


def test_create_conversation_normalizes_business_input(
    service: ConversationService,
) -> None:
    conversation = service.create_conversation(
        tenant_id=1,
        store_id=10,
        instagram_connection_id=100,
        provider_participant_key="  customer-1  ",
        subject="  Product question\r\nurgent  ",
    )

    assert conversation.public_id
    assert conversation.status == "open"
    assert conversation.provider_participant_key == "customer-1"
    assert conversation.subject == "Product question\nurgent"


def test_get_conversation_returns_existing_scoped_record(
    service: ConversationService,
) -> None:
    existing = create_conversation(service)

    assert service.get_conversation(
        existing.public_id,
        tenant_id=existing.tenant_id,
        store_id=existing.store_id,
    ) is existing


def test_get_or_create_returns_existing_identity(
    service: ConversationService,
    repositories: tuple[
        FakeConversationRepository,
        FakeMessageRepository,
    ],
) -> None:
    conversations, _messages = repositories
    existing = create_conversation(service)

    result = service.get_or_create_conversation(
        tenant_id=existing.tenant_id,
        store_id=existing.store_id,
        instagram_connection_id=existing.instagram_connection_id,
        provider_participant_key=existing.provider_participant_key,
    )

    assert result is existing
    assert conversations.items == [existing]


def test_get_or_create_creates_for_a_new_conversation_identity(
    service: ConversationService,
    repositories: tuple[
        FakeConversationRepository,
        FakeMessageRepository,
    ],
) -> None:
    conversations, _messages = repositories
    existing = create_conversation(service)

    created = service.get_or_create_conversation(
        tenant_id=existing.tenant_id,
        store_id=existing.store_id,
        instagram_connection_id=existing.instagram_connection_id,
        provider_participant_key="customer-2",
    )

    assert created is not existing
    assert len(conversations.items) == 2


def test_append_message_persists_and_updates_conversation_aggregate(
    service: ConversationService,
    repositories: tuple[
        FakeConversationRepository,
        FakeMessageRepository,
    ],
) -> None:
    conversations, messages = repositories
    conversation = create_conversation(service)
    occurred_at = datetime.now(UTC)

    message = service.append_message(
        conversation.public_id,
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
        idempotency_key="message-key",
        direction="outbound",
        content_type="text",
        text="  Thank you  ",
        occurred_at=occurred_at,
        metadata={"source": "operator"},
    )

    assert messages.items == [message]
    assert message.text == "Thank you"
    assert message.conversation_id == conversation.id
    assert conversation.message_count == 1
    assert conversation.outbound_message_count == 1
    assert conversation.inbound_message_count == 0
    assert conversation.last_message_at == occurred_at
    assert conversation.last_outbound_message_at == occurred_at
    assert conversation.revision == 2
    assert conversations.flush_count == 1

    with pytest.raises(ConversationConflictError):
        service.append_message(
            conversation.public_id,
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
            idempotency_key="message-key",
            direction="outbound",
            content_type="text",
            text="duplicate",
            occurred_at=occurred_at,
        )


def test_archive_requires_valid_transition_and_sets_timestamp(
    service: ConversationService,
) -> None:
    conversation = create_conversation(service)
    closed_at = datetime.now(UTC)
    service.change_status(
        conversation.public_id,
        "closed",
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
        changed_at=closed_at,
    )
    archived_at = closed_at + timedelta(seconds=1)

    archived = service.archive_conversation(
        conversation.public_id,
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
        archived_at=archived_at,
    )

    assert archived.status == "archived"
    assert archived.closed_at == closed_at
    assert archived.archived_at == archived_at
    with pytest.raises(ConversationInvalidTransitionError):
        service.archive_conversation(
            conversation.public_id,
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
        )


def test_change_status_applies_domain_transition_and_closed_lifecycle(
    service: ConversationService,
) -> None:
    conversation = create_conversation(service)
    changed_at = datetime.now(UTC)

    closed = service.change_status(
        conversation.public_id,
        "closed",
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
        changed_at=changed_at,
    )
    assert closed.status == "closed"
    assert closed.closed_at == changed_at

    reopened = service.change_status(
        conversation.public_id,
        "open",
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
    )
    assert reopened.status == "open"
    assert reopened.closed_at is None

    with pytest.raises(ConversationInvalidTransitionError):
        service.change_status(
            conversation.public_id,
            "archived",
            tenant_id=conversation.tenant_id,
            store_id=conversation.store_id,
        )


@pytest.mark.parametrize(
    ("tenant_id", "store_id"),
    [
        (2, 10),
        (1, 20),
    ],
)
def test_tenant_and_store_isolation_hide_conversations(
    service: ConversationService,
    tenant_id: int,
    store_id: int,
) -> None:
    conversation = create_conversation(service)

    with pytest.raises(ConversationNotFoundError):
        service.get_conversation(
            conversation.public_id,
            tenant_id=tenant_id,
            store_id=store_id,
        )
    with pytest.raises(ConversationNotFoundError):
        service.append_message(
            conversation.public_id,
            tenant_id=tenant_id,
            store_id=store_id,
            idempotency_key=f"isolated-{tenant_id}-{store_id}",
            direction="outbound",
            content_type="text",
            text="hidden",
            occurred_at=datetime.now(UTC),
        )
