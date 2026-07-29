from __future__ import annotations

from datetime import UTC, datetime, timedelta
import itertools
import uuid

import pytest
from sqlalchemy import CheckConstraint, DateTime, UniqueConstraint, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as registered_models  # noqa: F401
from app.conversation_core.models import (
    Conversation,
    ConversationAssignment,
    ConversationMessage,
    ConversationParticipant,
    ConversationProcessingRecord,
    ConversationReadState,
)
from app.database import Base
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
    InstagramWebhookDelivery,
)
from app.models import Store, Tenant


_sequence = itertools.count(1)
CONVERSATION_TABLES = {
    "conversations",
    "conversation_participants",
    "conversation_messages",
    "conversation_assignments",
    "conversation_read_states",
    "conversation_processing_records",
}


@pytest.fixture(autouse=True)
def clean_test_customers():
    """Keep persistence tests independent from the legacy application fixture."""

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


def unique_label(prefix: str) -> str:
    return f"{prefix}-{next(_sequence)}"


def create_scope(db: Session, prefix: str = "scope"):
    label = unique_label(prefix)
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
        instagram_account_id=unique_label("ig"),
        status="active",
    )
    db.add(connection)
    db.commit()
    return tenant, store, connection


def create_inbound_event(
    db: Session,
    tenant: Tenant,
    store: Store,
    connection: InstagramConnection,
) -> InstagramInboundEvent:
    key = unique_label("event")
    delivery = InstagramWebhookDelivery(
        provider="meta",
        external_delivery_key=unique_label("delivery"),
        payload_hash=key.ljust(64, "0")[:64],
        raw_payload={},
        signature_valid=True,
        verification_state="verified",
        processing_status="accepted",
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
    )
    db.add(delivery)
    db.flush()
    now = datetime.now(UTC)
    inbound_event = InstagramInboundEvent(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        webhook_delivery_id=delivery.id,
        provider="meta",
        provider_event_id=unique_label("mid"),
        idempotency_key=key.ljust(64, "1")[:64],
        event_type="messaging",
        object_type="message",
        external_sender_id=unique_label("sender"),
        external_recipient_id=connection.instagram_account_id,
        normalized_payload={"message": {"text": "hello"}},
        processing_status="ready",
        occurred_at=now,
        received_at=now,
    )
    db.add(inbound_event)
    db.commit()
    return inbound_event


def create_conversation(
    db: Session,
    tenant: Tenant,
    store: Store,
    connection: InstagramConnection,
    **overrides: object,
) -> Conversation:
    values: dict[str, object] = {
        "tenant_id": tenant.id,
        "store_id": store.id,
        "instagram_connection_id": connection.id,
        "provider_participant_key": unique_label("customer"),
        "status": "open",
    }
    values.update(overrides)
    conversation = Conversation(**values)
    db.add(conversation)
    db.commit()
    return conversation


def create_participant(
    db: Session,
    conversation: Conversation,
    **overrides: object,
) -> ConversationParticipant:
    values: dict[str, object] = {
        "tenant_id": conversation.tenant_id,
        "store_id": conversation.store_id,
        "conversation_id": conversation.id,
        "participant_type": "customer",
        "provider_participant_key": unique_label("participant"),
    }
    values.update(overrides)
    participant = ConversationParticipant(**values)
    db.add(participant)
    db.commit()
    return participant


def create_message(
    db: Session,
    conversation: Conversation,
    connection: InstagramConnection,
    inbound_event: InstagramInboundEvent | None,
    **overrides: object,
) -> ConversationMessage:
    values: dict[str, object] = {
        "tenant_id": conversation.tenant_id,
        "store_id": conversation.store_id,
        "conversation_id": conversation.id,
        "instagram_connection_id": connection.id,
        "instagram_inbound_event_id": (
            inbound_event.id if inbound_event is not None else None
        ),
        "provider_message_id": unique_label("provider-message"),
        "idempotency_key": unique_label("message-key").ljust(64, "0")[:64],
        "direction": "inbound",
        "content_type": "text",
        "text": "hello",
        "occurred_at": datetime.now(UTC),
    }
    values.update(overrides)
    message = ConversationMessage(**values)
    db.add(message)
    db.commit()
    return message


def constraint_names(table_name: str, constraint_type: type) -> set[str | None]:
    return {
        constraint.name
        for constraint in Base.metadata.tables[table_name].constraints
        if isinstance(constraint, constraint_type)
    }


def foreign_key_columns(table_name: str) -> set[tuple[str, ...]]:
    return {
        tuple(element.parent.name for element in constraint.elements)
        for constraint in Base.metadata.tables[table_name].foreign_key_constraints
    }


def test_all_conversation_tables_are_registered() -> None:
    assert CONVERSATION_TABLES <= set(Base.metadata.tables)


@pytest.mark.parametrize("table_name", sorted(CONVERSATION_TABLES))
def test_common_scope_and_public_columns_exist(table_name: str) -> None:
    columns = Base.metadata.tables[table_name].c
    assert {"id", "public_id", "tenant_id", "store_id", "created_at"} <= set(
        columns.keys()
    )
    assert columns.id.primary_key
    assert columns.public_id.type.length == 36
    assert columns.tenant_id.nullable is False
    assert columns.store_id.nullable is False
    assert isinstance(columns.created_at.type, DateTime)
    assert columns.created_at.type.timezone is True


def test_critical_columns_and_timezone_declarations() -> None:
    conversations = Base.metadata.tables["conversations"].c
    assert {
        "instagram_connection_id",
        "provider_participant_key",
        "status",
        "message_count",
        "revision",
        "updated_at",
        "closed_at",
        "archived_at",
    } <= set(conversations.keys())
    for name in (
        "last_message_at",
        "last_inbound_message_at",
        "last_outbound_message_at",
        "created_at",
        "updated_at",
        "closed_at",
        "archived_at",
    ):
        assert conversations[name].type.timezone is True

    messages = Base.metadata.tables["conversation_messages"].c
    assert {
        "instagram_inbound_event_id",
        "idempotency_key",
        "direction",
        "content_type",
        "text",
        "occurred_at",
        "metadata",
    } <= set(messages.keys())
    assert messages.occurred_at.type.timezone is True


def test_named_status_and_domain_check_constraints_exist() -> None:
    expected = {
        "conversations": "ck_conversations_status",
        "conversation_assignments": "ck_conversation_assignments_status",
        "conversation_processing_records": (
            "ck_conversation_processing_records_status"
        ),
    }
    for table_name, constraint_name in expected.items():
        assert constraint_name in constraint_names(table_name, CheckConstraint)
    assert (
        "ck_conversation_participants_type"
        in constraint_names("conversation_participants", CheckConstraint)
    )
    assert (
        "ck_conversation_messages_direction"
        in constraint_names("conversation_messages", CheckConstraint)
    )
    assert (
        "ck_conversation_messages_content_type"
        in constraint_names("conversation_messages", CheckConstraint)
    )


def test_required_unique_constraints_exist() -> None:
    expected = {
        "conversations": {
            "uq_conversations_connection_participant",
            "uq_conversations_id_tenant_store",
        },
        "conversation_messages": {
            "uq_conversation_messages_tenant_idempotency",
            "uq_conversation_messages_provider",
        },
        "conversation_read_states": {
            "uq_conversation_read_states_conversation_user"
        },
        "conversation_processing_records": {
            "uq_conversation_processing_records_inbound_event"
        },
    }
    for table_name, names in expected.items():
        assert names <= constraint_names(table_name, UniqueConstraint)


@pytest.mark.parametrize(
    ("table_name", "expected"),
    [
        (
            "conversations",
            {
                ("store_id", "tenant_id"),
                ("instagram_connection_id", "tenant_id", "store_id"),
            },
        ),
        (
            "conversation_messages",
            {
                ("conversation_id", "tenant_id", "store_id"),
                ("instagram_connection_id", "tenant_id", "store_id"),
                ("instagram_inbound_event_id", "tenant_id", "store_id"),
                ("sender_participant_id", "tenant_id", "store_id"),
                ("reply_to_message_id", "tenant_id", "store_id"),
            },
        ),
        (
            "conversation_processing_records",
            {
                ("instagram_inbound_event_id", "tenant_id", "store_id"),
                ("conversation_id", "tenant_id", "store_id"),
                ("message_id", "tenant_id", "store_id"),
            },
        ),
    ],
)
def test_composite_scope_foreign_keys_exist(
    table_name: str,
    expected: set[tuple[str, ...]],
) -> None:
    assert expected <= foreign_key_columns(table_name)


def test_create_all_and_valid_conversation(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    conversation = create_conversation(db, tenant, store, connection)
    assert conversation.id is not None
    assert conversation.status == "open"
    assert conversation.message_count == 0
    assert conversation.revision == 1


def test_duplicate_conversation_identity_is_rejected(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    participant_key = unique_label("same-customer")
    create_conversation(
        db,
        tenant,
        store,
        connection,
        provider_participant_key=participant_key,
    )
    duplicate = Conversation(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        provider_participant_key=participant_key,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "invalid"},
        {"message_count": -1},
        {
            "message_count": 2,
            "inbound_message_count": 1,
            "outbound_message_count": 0,
        },
        {"status": "archived", "archived_at": None},
        {"status": "open", "archived_at": datetime.now(UTC)},
    ],
)
def test_invalid_conversation_state_is_rejected(
    db: Session,
    overrides: dict[str, object],
) -> None:
    tenant, store, connection = create_scope(db)
    conversation = Conversation(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        provider_participant_key=unique_label("customer"),
        **overrides,
    )
    db.add(conversation)
    with pytest.raises(IntegrityError):
        db.commit()


def test_valid_customer_and_operator_participants(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    conversation = create_conversation(db, tenant, store, connection)
    customer = create_participant(db, conversation)
    operator = create_participant(
        db,
        conversation,
        participant_type="operator",
        provider_participant_key=None,
        user_id=123,
    )
    assert customer.provider_participant_key
    assert operator.user_id == 123


def test_invalid_customer_and_duplicate_provider_participant_are_rejected(
    db: Session,
) -> None:
    tenant, store, connection = create_scope(db)
    conversation = create_conversation(db, tenant, store, connection)
    missing_identity = ConversationParticipant(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        participant_type="customer",
    )
    db.add(missing_identity)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    key = unique_label("duplicate-participant")
    create_participant(
        db,
        conversation,
        provider_participant_key=key,
    )
    duplicate = ConversationParticipant(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        participant_type="customer",
        provider_participant_key=key,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()


def test_valid_inbound_message(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    inbound_event = create_inbound_event(db, tenant, store, connection)
    conversation = create_conversation(db, tenant, store, connection)
    message = create_message(db, conversation, connection, inbound_event)
    assert message.id is not None
    assert message.direction == "inbound"


@pytest.mark.parametrize(
    "overrides",
    [
        {"instagram_inbound_event_id": None},
        {"direction": "invalid"},
        {"content_type": "invalid"},
        {"content_type": "text", "text": None},
    ],
)
def test_invalid_message_state_is_rejected(
    db: Session,
    overrides: dict[str, object],
) -> None:
    tenant, store, connection = create_scope(db)
    inbound_event = create_inbound_event(db, tenant, store, connection)
    conversation = create_conversation(db, tenant, store, connection)
    values: dict[str, object] = {
        "tenant_id": tenant.id,
        "store_id": store.id,
        "conversation_id": conversation.id,
        "instagram_connection_id": connection.id,
        "instagram_inbound_event_id": inbound_event.id,
        "provider_message_id": unique_label("provider-message"),
        "idempotency_key": unique_label("key").ljust(64, "0")[:64],
        "direction": "inbound",
        "content_type": "text",
        "text": "hello",
        "occurred_at": datetime.now(UTC),
    }
    values.update(overrides)
    db.add(ConversationMessage(**values))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_message_keys_are_rejected(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    inbound_event = create_inbound_event(db, tenant, store, connection)
    conversation = create_conversation(db, tenant, store, connection)
    key = unique_label("same-key").ljust(64, "0")[:64]
    provider_id = unique_label("same-provider")
    create_message(
        db,
        conversation,
        connection,
        inbound_event,
        idempotency_key=key,
        provider_message_id=provider_id,
    )
    second_event = create_inbound_event(db, tenant, store, connection)
    duplicate_key = ConversationMessage(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        instagram_connection_id=connection.id,
        instagram_inbound_event_id=second_event.id,
        provider_message_id=unique_label("other-provider"),
        idempotency_key=key,
        direction="inbound",
        content_type="text",
        text="duplicate",
        occurred_at=datetime.now(UTC),
    )
    db.add(duplicate_key)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    duplicate_provider = ConversationMessage(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        instagram_connection_id=connection.id,
        instagram_inbound_event_id=second_event.id,
        provider_message_id=provider_id,
        idempotency_key=unique_label("other-key").ljust(64, "0")[:64],
        direction="inbound",
        content_type="text",
        text="duplicate",
        occurred_at=datetime.now(UTC),
    )
    db.add(duplicate_provider)
    with pytest.raises(IntegrityError):
        db.commit()


def test_cross_store_conversation_reference_is_rejected(db: Session) -> None:
    tenant, store_one, connection_one = create_scope(db, "one")
    conversation = create_conversation(db, tenant, store_one, connection_one)
    store_two = Store(
        tenant_id=tenant.id,
        name=unique_label("two"),
        slug=unique_label("two"),
        status="active",
        currency_code="IRR",
    )
    db.add(store_two)
    db.commit()
    participant = ConversationParticipant(
        tenant_id=tenant.id,
        store_id=store_two.id,
        conversation_id=conversation.id,
        participant_type="customer",
        provider_participant_key=unique_label("participant"),
    )
    db.add(participant)
    with pytest.raises(IntegrityError):
        db.commit()


def test_cross_tenant_sender_participant_reference_is_rejected(
    db: Session,
) -> None:
    tenant_one, store_one, connection_one = create_scope(db, "one")
    event_one = create_inbound_event(db, tenant_one, store_one, connection_one)
    conversation_one = create_conversation(
        db,
        tenant_one,
        store_one,
        connection_one,
    )
    tenant_two, store_two, connection_two = create_scope(db, "two")
    conversation_two = create_conversation(
        db,
        tenant_two,
        store_two,
        connection_two,
    )
    participant_two = create_participant(db, conversation_two)
    message = ConversationMessage(
        tenant_id=tenant_one.id,
        store_id=store_one.id,
        conversation_id=conversation_one.id,
        instagram_connection_id=connection_one.id,
        instagram_inbound_event_id=event_one.id,
        provider_message_id=unique_label("provider-message"),
        idempotency_key=unique_label("key").ljust(64, "0")[:64],
        direction="inbound",
        content_type="text",
        text="hello",
        sender_participant_id=participant_two.id,
        occurred_at=datetime.now(UTC),
    )
    db.add(message)
    with pytest.raises(IntegrityError):
        db.commit()


def test_assignment_state_constraints(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    conversation = create_conversation(db, tenant, store, connection)
    assignment = ConversationAssignment(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        assignee_user_id=10,
        assigned_by_user_id=11,
    )
    db.add(assignment)
    db.commit()
    assert assignment.status == "assigned"

    invalid_release = ConversationAssignment(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        assignee_user_id=12,
        assigned_by_user_id=11,
        status="released",
    )
    db.add(invalid_release)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    now = datetime.now(UTC)
    invalid_time = ConversationAssignment(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        assignee_user_id=13,
        assigned_by_user_id=11,
        released_by_user_id=11,
        status="released",
        assigned_at=now,
        released_at=now - timedelta(seconds=1),
    )
    db.add(invalid_time)
    with pytest.raises(IntegrityError):
        db.commit()


def test_read_state_uniqueness_and_cross_scope_message(db: Session) -> None:
    tenant_one, store_one, connection_one = create_scope(db, "one")
    event_one = create_inbound_event(db, tenant_one, store_one, connection_one)
    conversation_one = create_conversation(
        db,
        tenant_one,
        store_one,
        connection_one,
    )
    message_one = create_message(
        db,
        conversation_one,
        connection_one,
        event_one,
    )
    read_state = ConversationReadState(
        tenant_id=tenant_one.id,
        store_id=store_one.id,
        conversation_id=conversation_one.id,
        user_id=42,
        last_read_message_id=message_one.id,
    )
    db.add(read_state)
    db.commit()

    duplicate = ConversationReadState(
        tenant_id=tenant_one.id,
        store_id=store_one.id,
        conversation_id=conversation_one.id,
        user_id=42,
        last_read_message_id=message_one.id,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    tenant_two, store_two, connection_two = create_scope(db, "two")
    conversation_two = create_conversation(
        db,
        tenant_two,
        store_two,
        connection_two,
    )
    cross_scope = ConversationReadState(
        tenant_id=tenant_two.id,
        store_id=store_two.id,
        conversation_id=conversation_two.id,
        user_id=43,
        last_read_message_id=message_one.id,
    )
    db.add(cross_scope)
    with pytest.raises(IntegrityError):
        db.commit()


def test_processing_record_constraints(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    inbound_event = create_inbound_event(db, tenant, store, connection)
    pending = ConversationProcessingRecord(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_inbound_event_id=inbound_event.id,
    )
    db.add(pending)
    db.commit()
    assert pending.status == "pending"

    duplicate = ConversationProcessingRecord(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_inbound_event_id=inbound_event.id,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    other_event = create_inbound_event(db, tenant, store, connection)
    negative = ConversationProcessingRecord(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_inbound_event_id=other_event.id,
        attempt_count=-1,
    )
    db.add(negative)
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "processed", "processed_at": datetime.now(UTC)},
        {"status": "failed", "failure_category": None},
    ],
)
def test_invalid_processing_result_is_rejected(
    db: Session,
    overrides: dict[str, object],
) -> None:
    tenant, store, connection = create_scope(db)
    inbound_event = create_inbound_event(db, tenant, store, connection)
    record = ConversationProcessingRecord(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_inbound_event_id=inbound_event.id,
        **overrides,
    )
    db.add(record)
    with pytest.raises(IntegrityError):
        db.commit()


def test_public_ids_are_generated_unique_uuid_style(db: Session) -> None:
    tenant, store, connection = create_scope(db)
    first = create_conversation(db, tenant, store, connection)
    second = create_conversation(db, tenant, store, connection)
    assert first.public_id != second.public_id
    assert str(uuid.UUID(first.public_id)) == first.public_id
    assert str(uuid.UUID(second.public_id)) == second.public_id
