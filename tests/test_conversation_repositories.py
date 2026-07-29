from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

import pytest
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import Session

from app import models as registered_models  # noqa: F401
from app.conversation_core.models import Conversation, ConversationMessage
from app.database import Base
from app.infrastructure.database.repositories import (
    BaseRepository,
    ConversationRepository,
    MessageRepository,
)
from app.instagram_channel.models import InstagramConnection
from app.models import Store, Tenant


@pytest.fixture(autouse=True)
def clean_test_customers():
    """Keep repository tests independent from the legacy application fixture."""

    yield


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def create_scope(db: Session) -> tuple[Tenant, Store, InstagramConnection]:
    label = uuid.uuid4().hex
    tenant = Tenant(name=label, slug=label, status="active")
    db.add(tenant)
    db.flush()
    store = Store(
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
    return tenant, store, connection


def conversation_for(
    tenant: Tenant,
    store: Store,
    connection: InstagramConnection,
    *,
    participant_key: str | None = None,
) -> Conversation:
    return Conversation(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        provider_participant_key=participant_key or uuid.uuid4().hex,
        status="open",
    )


def outbound_message_for(
    conversation: Conversation,
    connection: InstagramConnection,
    *,
    idempotency_key: str,
    occurred_at: datetime,
) -> ConversationMessage:
    return ConversationMessage(
        tenant_id=conversation.tenant_id,
        store_id=conversation.store_id,
        conversation_id=conversation.id,
        instagram_connection_id=connection.id,
        provider_message_id=f"provider-{idempotency_key}",
        idempotency_key=idempotency_key,
        direction="outbound",
        content_type="text",
        text="hello",
        occurred_at=occurred_at,
    )


def test_base_repository_helpers_do_not_own_the_transaction(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant, store, connection = create_scope(db)
    repository = BaseRepository(db, Conversation)
    conversation = conversation_for(tenant, store, connection)

    def reject_commit() -> None:
        raise AssertionError("repositories must not commit")

    monkeypatch.setattr(db, "commit", reject_commit)

    assert repository.add(conversation) is conversation
    repository.flush()
    assert repository.get_by_id(conversation.id) is conversation

    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation.id)
        .values(subject="database value")
        .execution_options(synchronize_session=False)
    )
    assert repository.refresh(conversation) is conversation
    assert conversation.subject == "database value"

    repository.delete(conversation)
    repository.flush()
    assert repository.get_by_id(conversation.id) is None


def test_conversation_repository_is_store_scoped_and_deterministic(
    db: Session,
) -> None:
    tenant, store, connection = create_scope(db)
    other_tenant, other_store, other_connection = create_scope(db)
    repository = ConversationRepository(db)

    first = repository.create(
        conversation_for(tenant, store, connection, participant_key="first")
    )
    second = repository.create(
        conversation_for(tenant, store, connection, participant_key="second")
    )
    other = repository.create(
        conversation_for(
            other_tenant,
            other_store,
            other_connection,
            participant_key="other",
        )
    )

    assert first.id is not None
    assert first.public_id is not None
    assert repository.get_by_public_id(
        first.public_id,
        tenant_id=tenant.id,
        store_id=store.id,
    ) is first
    assert (
        repository.get_by_public_id(
            first.public_id,
            tenant_id=other_tenant.id,
            store_id=other_store.id,
        )
        is None
    )
    assert repository.list_by_store(
        tenant_id=tenant.id,
        store_id=store.id,
    ) == (second, first)
    assert other not in repository.list_by_store(
        tenant_id=tenant.id,
        store_id=store.id,
    )


def test_conversation_status_and_archive_updates_are_store_scoped(
    db: Session,
) -> None:
    tenant, store, connection = create_scope(db)
    other_tenant, other_store, _other_connection = create_scope(db)
    repository = ConversationRepository(db)
    conversation = repository.create(conversation_for(tenant, store, connection))

    assert (
        repository.update_status(
            conversation.public_id,
            "closed",
            tenant_id=other_tenant.id,
            store_id=other_store.id,
        )
        is None
    )
    updated = repository.update_status(
        conversation.public_id,
        "closed",
        tenant_id=tenant.id,
        store_id=store.id,
    )
    assert updated is conversation
    assert conversation.status == "closed"
    assert conversation.revision == 2

    archived_at = datetime.now(UTC)
    archived = repository.archive(
        conversation.public_id,
        tenant_id=tenant.id,
        store_id=store.id,
        archived_at=archived_at,
    )
    assert archived is conversation
    assert conversation.status == "archived"
    assert conversation.archived_at == archived_at
    assert conversation.revision == 3


def test_message_repository_creates_lists_and_checks_keys_within_scope(
    db: Session,
) -> None:
    tenant, store, connection = create_scope(db)
    other_tenant, other_store, other_connection = create_scope(db)
    conversations = ConversationRepository(db)
    messages = MessageRepository(db)
    conversation = conversations.create(
        conversation_for(tenant, store, connection)
    )
    other_conversation = conversations.create(
        conversation_for(other_tenant, other_store, other_connection)
    )
    now = datetime.now(UTC)

    later = messages.create(
        outbound_message_for(
            conversation,
            connection,
            idempotency_key="later",
            occurred_at=now + timedelta(seconds=1),
        )
    )
    earlier = messages.create(
        outbound_message_for(
            conversation,
            connection,
            idempotency_key="earlier",
            occurred_at=now,
        )
    )
    other = messages.create(
        outbound_message_for(
            other_conversation,
            other_connection,
            idempotency_key="shared-key",
            occurred_at=now,
        )
    )

    assert messages.list_by_conversation(
        conversation.id,
        tenant_id=tenant.id,
        store_id=store.id,
    ) == (earlier, later)
    assert other not in messages.list_by_conversation(
        conversation.id,
        tenant_id=tenant.id,
        store_id=store.id,
    )
    assert messages.exists_message_key(
        "later",
        tenant_id=tenant.id,
        store_id=store.id,
    )
    assert not messages.exists_message_key(
        "shared-key",
        tenant_id=tenant.id,
        store_id=store.id,
    )
    assert messages.exists_message_key(
        "shared-key",
        tenant_id=other_tenant.id,
        store_id=other_store.id,
    )
