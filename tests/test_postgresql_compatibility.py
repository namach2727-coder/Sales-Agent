from __future__ import annotations

from datetime import UTC, datetime
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.services import ConversationService
from app.database import engine
from app.infrastructure.database.repositories import (
    ConversationRepository,
    MessageRepository,
)
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramWebhookDelivery,
)
from app.models import Store, Tenant


pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="requires explicit PostgreSQL test database",
)


def test_postgresql_database_is_at_alembic_head() -> None:
    with engine.connect() as connection:
        assert connection.scalar(
            text("SELECT version_num FROM alembic_version")
        ) == "0014_transport_neutral_inbound"


def test_postgresql_conversation_path_handles_json_boolean_and_timezone() -> None:
    label = uuid.uuid4().hex
    now = datetime.now(UTC)

    with Session(engine, expire_on_commit=False) as session:
        transaction = session.begin()
        try:
            tenant = Tenant(
                name=label,
                slug=f"pg-{label}",
                status="active",
            )
            session.add(tenant)
            session.flush()
            store = Store(
                tenant_id=tenant.id,
                name=label,
                slug=f"pg-{label}",
                status="active",
                currency_code="IRR",
            )
            session.add(store)
            session.flush()
            connection = InstagramConnection(
                tenant_id=tenant.id,
                store_id=store.id,
                instagram_account_id=f"pg-{label}",
                status="active",
            )
            session.add(connection)
            session.flush()
            delivery = InstagramWebhookDelivery(
                provider="meta",
                external_delivery_key=f"delivery-{label}",
                payload_hash=label.ljust(64, "0")[:64],
                raw_payload={"message": {"text": "سلام"}, "nested": [1, True]},
                signature_valid=True,
                verification_state="verified",
                processing_status="accepted",
                tenant_id=tenant.id,
                store_id=store.id,
                instagram_connection_id=connection.id,
                received_at=now,
            )
            session.add(delivery)
            session.flush()
            session.expire(delivery)

            assert delivery.signature_valid is True
            assert delivery.raw_payload["nested"] == [1, True]
            assert delivery.received_at.tzinfo is not None

            service = ConversationService(
                ConversationRepository(session),
                MessageRepository(session),
            )
            conversation = service.create_conversation(
                tenant_id=tenant.id,
                store_id=store.id,
                instagram_connection_id=connection.id,
                provider_participant_key=f"customer-{label}",
            )
            message = service.append_message(
                conversation.public_id,
                tenant_id=tenant.id,
                store_id=store.id,
                idempotency_key=label.ljust(64, "1")[:64],
                direction="outbound",
                content_type="text",
                text="پاسخ آزمایشی",
                occurred_at=now,
                metadata={"source": "postgresql-compatibility"},
            )

            session.expire(message)
            assert message.metadata_json == {
                "source": "postgresql-compatibility"
            }
            assert message.occurred_at.tzinfo is not None
            assert conversation.message_count == 1
            assert conversation.outbound_message_count == 1
        finally:
            transaction.rollback()
