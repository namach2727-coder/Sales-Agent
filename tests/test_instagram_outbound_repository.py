from __future__ import annotations

from datetime import UTC, datetime
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import models as registered_models  # noqa: F401
from app.conversation_core.models import Conversation, ConversationMessage
from app.database import Base
from app.infrastructure.database.repositories import InstagramOutboundRepository
from app.instagram_channel.models import InstagramConnection
from app.models import Store, Tenant


def _database():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _records(db: Session):
    suffix = uuid.uuid4().hex
    tenant = Tenant(name=suffix, slug=suffix, status="active")
    db.add(tenant)
    db.flush()
    store = Store(
        tenant_id=tenant.id,
        name=suffix,
        slug=suffix,
        status="active",
        currency_code="IRR",
    )
    db.add(store)
    db.flush()
    connection = InstagramConnection(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_account_id=f"ig-{suffix}",
        status="active",
        encrypted_access_token="ciphertext",
    )
    db.add(connection)
    db.flush()
    conversation = Conversation(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        provider_participant_key=f"customer-{suffix}",
        status="open",
    )
    db.add(conversation)
    db.flush()
    message = ConversationMessage(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        instagram_connection_id=connection.id,
        idempotency_key=uuid.uuid4().hex,
        direction="outbound",
        content_type="text",
        text="answer",
        occurred_at=datetime.now(UTC),
        metadata_json={
            "author_type": "assistant",
            "source": "ai_response_orchestrator",
            "llm_total_tokens": 9,
        },
    )
    db.add(message)
    db.flush()
    return tenant, store, connection, conversation, message


def test_repository_resolves_scoped_message_and_active_connection() -> None:
    engine = _database()
    with Session(engine) as db:
        tenant, store, connection, conversation, message = _records(db)
        repository = InstagramOutboundRepository(db)

        context = repository.get_message_context(
            message.public_id,
            conversation_public_id=conversation.public_id,
            tenant_id=tenant.id,
            store_id=store.id,
        )
        connections = repository.list_active_connections(
            tenant_id=tenant.id,
            store_id=store.id,
        )

        assert context is not None
        assert context.provider_participant_key == conversation.provider_participant_key
        assert context.metadata["llm_total_tokens"] == 9
        assert len(connections) == 1
        assert connections[0].connection_id == connection.id
        assert connections[0].encrypted_access_token == "ciphertext"
    engine.dispose()


def test_repository_hides_cross_tenant_store_and_conversation_lookups() -> None:
    engine = _database()
    with Session(engine) as db:
        tenant, store, _, conversation, message = _records(db)
        repository = InstagramOutboundRepository(db)

        assert repository.get_message_context(
            message.public_id,
            conversation_public_id=conversation.public_id,
            tenant_id=tenant.id + 1,
            store_id=store.id,
        ) is None
        assert repository.get_message_context(
            message.public_id,
            conversation_public_id=conversation.public_id,
            tenant_id=tenant.id,
            store_id=store.id + 1,
        ) is None
        assert repository.get_message_context(
            message.public_id,
            conversation_public_id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            store_id=store.id,
        ) is None
    engine.dispose()


def test_repository_updates_existing_message_without_commit_and_rollback_restores() -> None:
    engine = _database()
    with Session(engine) as db:
        tenant, store, _, conversation, message = _records(db)
        db.commit()
        repository = InstagramOutboundRepository(db)

        assert repository.update_delivery(
            message.public_id,
            conversation_public_id=conversation.public_id,
            tenant_id=tenant.id,
            store_id=store.id,
            metadata={
                **message.metadata_json,
                "delivery_status": "sent",
                "delivery_provider": "instagram",
            },
            provider_message_id="meta-mid",
        )
        assert message.provider_message_id == "meta-mid"
        assert message.metadata_json["llm_total_tokens"] == 9
        db.rollback()
        db.expire_all()

        restored = db.scalar(
            select(ConversationMessage).where(
                ConversationMessage.id == message.id
            )
        )
        assert restored is not None
        assert restored.provider_message_id is None
        assert "delivery_status" not in restored.metadata_json
    engine.dispose()


def test_repository_update_is_scoped_and_does_not_mutate_wrong_message() -> None:
    engine = _database()
    with Session(engine) as db:
        tenant, store, _, conversation, message = _records(db)
        repository = InstagramOutboundRepository(db)
        assert not repository.update_delivery(
            message.public_id,
            conversation_public_id=conversation.public_id,
            tenant_id=tenant.id + 1,
            store_id=store.id,
            metadata={"delivery_status": "sent"},
        )
        assert "delivery_status" not in message.metadata_json
    engine.dispose()
