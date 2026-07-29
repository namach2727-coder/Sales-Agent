from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import hashlib
import uuid

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.application.instagram import InstagramInboundMessageService
from app.application.services import ConversationService
from app.conversation_core.models import Conversation, ConversationMessage
from app.infrastructure.database.repositories import (
    ConversationRepository,
    InstagramInboundMessageRepository,
    MessageRepository,
)
from app.instagram_channel.exceptions import InstagramChannelNotFoundError
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
    InstagramWebhookDelivery,
)
from app.models import Store, Tenant


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inbound_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("instagram-inbound") / "inbound.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


def service_for(db: Session) -> InstagramInboundMessageService:
    return InstagramInboundMessageService(
        InstagramInboundMessageRepository(db),
        ConversationService(
            ConversationRepository(db),
            MessageRepository(db),
        ),
    )


def create_scope(
    engine,
    *,
    tenant: Tenant | None = None,
    connection_status: str = "active",
    store_status: str = "active",
) -> tuple[Tenant, Store, InstagramConnection]:
    suffix = uuid.uuid4().hex[:12]
    with Session(engine, expire_on_commit=False) as db:
        if tenant is None:
            tenant = Tenant(
                name=f"Tenant {suffix}",
                slug=f"tenant-{suffix}",
                status="active",
            )
            db.add(tenant)
            db.flush()
        else:
            tenant = db.merge(tenant)
        store = Store(
            tenant_id=tenant.id,
            name=f"Store {suffix}",
            slug=f"store-{suffix}",
            status=store_status,
            currency_code="IRR",
        )
        db.add(store)
        db.flush()
        connection = InstagramConnection(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_account_id=f"ig-{suffix}",
            facebook_page_id=f"page-{suffix}",
            status=connection_status,
            token_scopes=[],
        )
        db.add(connection)
        db.commit()
        return tenant, store, connection


def create_inbound_event(
    engine,
    scope: tuple[Tenant, Store, InstagramConnection],
    *,
    sender_id: str | None = "customer-1",
    message_id: str | None = None,
    text: str | None = "price?",
    event_type: str = "messaging",
    processing_status: str = "ready",
) -> InstagramInboundEvent:
    tenant, store, connection = scope
    provider_message_id = message_id or f"mid-{uuid.uuid4().hex}"
    idempotency_key = hashlib.sha256(
        f"{connection.public_id}:{provider_message_id}".encode()
    ).hexdigest()
    occurred_at = datetime.now(UTC)
    normalized_payload: dict[str, object]
    if event_type == "messaging":
        message: dict[str, object] = {}
        if provider_message_id is not None:
            message["id"] = provider_message_id
        if text is not None:
            message["text"] = text
        normalized_payload = {"message": message}
    else:
        normalized_payload = {"classification": "unsupported"}
    with Session(engine, expire_on_commit=False) as db:
        delivery = InstagramWebhookDelivery(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            provider="meta",
            external_delivery_key=f"delivery-{uuid.uuid4().hex}",
            payload_hash=uuid.uuid4().hex.ljust(64, "0"),
            raw_payload={"object": "instagram"},
            signature_algorithm="sha256",
            signature_valid=True,
            verification_state="verified",
            processing_status="processed",
            received_at=occurred_at,
            processed_at=occurred_at,
        )
        db.add(delivery)
        db.flush()
        inbound = InstagramInboundEvent(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            webhook_delivery_id=delivery.id,
            provider="meta",
            provider_event_id=provider_message_id,
            idempotency_key=idempotency_key,
            event_type=event_type,
            object_type=(
                "message" if event_type == "messaging" else "unsupported"
            ),
            external_object_id=provider_message_id,
            external_sender_id=sender_id,
            external_recipient_id=connection.instagram_account_id,
            provider_event_at=occurred_at,
            normalized_payload=normalized_payload,
            processing_status=processing_status,
            occurred_at=occurred_at,
            received_at=occurred_at,
        )
        db.add(inbound)
        db.commit()
        return inbound


def test_valid_inbound_text_creates_conversation_and_message(
    inbound_engine,
) -> None:
    scope = create_scope(inbound_engine)
    inbound = create_inbound_event(
        inbound_engine,
        scope,
        message_id=f"mid-{uuid.uuid4().hex}",
        text="قیمت آیفون؟",
    )

    with Session(inbound_engine, expire_on_commit=False) as db:
        result = service_for(db).process(inbound.public_id)
        db.commit()

    assert result.status == "processed"
    assert result.created_conversation is True
    assert result.conversation_public_id
    assert result.message_public_id
    with Session(inbound_engine) as db:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.public_id
                == result.conversation_public_id
            )
        )
        message = db.scalar(
            select(ConversationMessage).where(
                ConversationMessage.public_id == result.message_public_id
            )
        )
        assert conversation is not None
        assert message is not None
        assert conversation.provider_participant_key == "customer-1"
        assert conversation.message_count == 1
        assert message.direction == "inbound"
        assert message.provider_message_id == inbound.provider_event_id
        assert message.instagram_inbound_event_id == inbound.id
        assert message.provider_event_at is not None
        assert message.metadata_json["provider"] == "instagram"
        assert message.metadata_json["source"] == "instagram_webhook"


def test_existing_conversation_is_reused_and_duplicate_is_idempotent(
    inbound_engine,
) -> None:
    scope = create_scope(inbound_engine)
    first_event = create_inbound_event(inbound_engine, scope)
    second_event = create_inbound_event(inbound_engine, scope)

    with Session(inbound_engine, expire_on_commit=False) as db:
        service = service_for(db)
        first = service.process(first_event.public_id)
        second = service.process(second_event.public_id)
        duplicate = service.process(second_event.public_id)
        db.commit()

    assert first.status == "processed"
    assert first.created_conversation is True
    assert second.status == "processed"
    assert second.created_conversation is False
    assert duplicate.status == "duplicate"
    assert duplicate.created_conversation is False
    assert duplicate.conversation_public_id == second.conversation_public_id
    assert duplicate.message_public_id == second.message_public_id
    with Session(inbound_engine) as db:
        assert db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.instagram_connection_id == scope[2].id
            )
        ) == 1
        assert db.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(
                ConversationMessage.instagram_connection_id == scope[2].id
            )
        ) == 2


def test_tenant_and_store_scopes_do_not_share_conversations(
    inbound_engine,
) -> None:
    first_scope = create_scope(inbound_engine)
    second_store_scope = create_scope(
        inbound_engine,
        tenant=first_scope[0],
    )
    second_tenant_scope = create_scope(inbound_engine)
    scopes = (first_scope, second_store_scope, second_tenant_scope)
    events = [
        create_inbound_event(
            inbound_engine,
            scope,
            sender_id="shared-customer",
            message_id="shared-provider-mid",
        )
        for scope in scopes
    ]

    with Session(inbound_engine, expire_on_commit=False) as db:
        results = [
            service_for(db).process(item.public_id) for item in events
        ]
        db.commit()

    assert all(item.status == "processed" for item in results)
    assert len(
        {item.conversation_public_id for item in results}
    ) == 3
    with Session(inbound_engine) as db:
        for scope, result in zip(scopes, results, strict=True):
            conversation = db.scalar(
                select(Conversation).where(
                    Conversation.public_id
                    == result.conversation_public_id
                )
            )
            assert conversation is not None
            assert conversation.tenant_id == scope[0].id
            assert conversation.store_id == scope[1].id
            assert conversation.instagram_connection_id == scope[2].id


def test_unknown_or_inactive_channel_is_safe(
    inbound_engine,
) -> None:
    with Session(inbound_engine) as db:
        with pytest.raises(InstagramChannelNotFoundError):
            service_for(db).process(str(uuid.uuid4()))

    inactive_scope = create_scope(
        inbound_engine,
        connection_status="disconnected",
    )
    inbound = create_inbound_event(inbound_engine, inactive_scope)
    with Session(inbound_engine) as db:
        result = service_for(db).process(inbound.public_id)
        assert result.status == "ignored"
        assert result.reason == "inactive_channel"
        assert db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.instagram_connection_id
                == inactive_scope[2].id
            )
        ) == 0


def test_unsupported_or_incomplete_event_is_ignored(
    inbound_engine,
) -> None:
    scope = create_scope(inbound_engine)
    unsupported = create_inbound_event(
        inbound_engine,
        scope,
        event_type="unsupported",
        processing_status="ignored",
    )
    missing_sender = create_inbound_event(
        inbound_engine,
        scope,
        sender_id=None,
    )

    with Session(inbound_engine) as db:
        service = service_for(db)
        unsupported_result = service.process(unsupported.public_id)
        missing_sender_result = service.process(missing_sender.public_id)

    assert unsupported_result.status == "ignored"
    assert unsupported_result.reason == "unsupported_event"
    assert missing_sender_result.status == "ignored"
    assert missing_sender_result.reason == "missing_sender"


def test_processing_result_exposes_only_public_references(
    inbound_engine,
) -> None:
    scope = create_scope(inbound_engine)
    inbound = create_inbound_event(inbound_engine, scope)
    with Session(inbound_engine) as db:
        result = service_for(db).process(inbound.public_id)

    serialized = asdict(result)
    assert set(serialized) == {
        "status",
        "conversation_public_id",
        "message_public_id",
        "created_conversation",
        "reason",
    }
    assert isinstance(result.conversation_public_id, str)
    assert isinstance(result.message_public_id, str)
    assert not any(
        isinstance(value, int) and not isinstance(value, bool)
        for value in serialized.values()
    )


def test_pipeline_never_commits_or_rolls_back_its_session(
    inbound_engine,
) -> None:
    scope = create_scope(inbound_engine)
    inbound = create_inbound_event(inbound_engine, scope)
    with Session(inbound_engine) as db:
        original_rollback = db.rollback
        with (
            patch.object(
                db,
                "commit",
                side_effect=AssertionError("pipeline called commit"),
            ),
            patch.object(
                db,
                "rollback",
                side_effect=AssertionError("pipeline called rollback"),
            ),
        ):
            result = service_for(db).process(inbound.public_id)
            assert result.status == "processed"
        original_rollback()

    with Session(inbound_engine) as db:
        assert db.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(
                ConversationMessage.instagram_inbound_event_id
                == inbound.id
            )
        ) == 0
