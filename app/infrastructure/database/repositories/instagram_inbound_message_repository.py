"""Focused persistence queries for Instagram conversation ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.conversation_core.models import Conversation, ConversationMessage
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
)
from app.models import Store, Tenant


@dataclass(frozen=True, slots=True)
class InstagramInboundEventContext:
    event_id: int
    event_public_id: str
    event_type: str
    event_processing_status: str
    event_idempotency_key: str
    provider_message_id: str | None
    external_sender_id: str | None
    external_recipient_id: str | None
    provider_event_at: datetime | None
    occurred_at: datetime
    normalized_payload: dict[str, object]
    tenant_id: int
    tenant_public_id: str
    tenant_status: str
    store_id: int
    store_public_id: str
    store_status: str
    connection_id: int
    connection_public_id: str
    connection_status: str


@dataclass(frozen=True, slots=True)
class PersistedMessageReference:
    conversation_public_id: str
    message_public_id: str


class InstagramInboundMessageRepository:
    """Read trusted Instagram scope and persisted processing references."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_event_context(
        self,
        event_public_id: str,
    ) -> InstagramInboundEventContext | None:
        row = self.session.execute(
            select(
                InstagramInboundEvent,
                InstagramConnection,
                Tenant,
                Store,
            )
            .join(
                InstagramConnection,
                and_(
                    InstagramConnection.id
                    == InstagramInboundEvent.instagram_connection_id,
                    InstagramConnection.tenant_id
                    == InstagramInboundEvent.tenant_id,
                    InstagramConnection.store_id
                    == InstagramInboundEvent.store_id,
                ),
            )
            .join(
                Tenant,
                Tenant.id == InstagramInboundEvent.tenant_id,
            )
            .join(
                Store,
                and_(
                    Store.id == InstagramInboundEvent.store_id,
                    Store.tenant_id == InstagramInboundEvent.tenant_id,
                ),
            )
            .where(InstagramInboundEvent.public_id == event_public_id)
        ).one_or_none()
        if row is None:
            return None
        event, connection, tenant, store = row
        return InstagramInboundEventContext(
            event_id=event.id,
            event_public_id=event.public_id,
            event_type=event.event_type,
            event_processing_status=event.processing_status,
            event_idempotency_key=event.idempotency_key,
            provider_message_id=event.provider_event_id,
            external_sender_id=event.external_sender_id,
            external_recipient_id=event.external_recipient_id,
            provider_event_at=event.provider_event_at,
            occurred_at=event.occurred_at,
            normalized_payload=event.normalized_payload,
            tenant_id=tenant.id,
            tenant_public_id=tenant.public_id,
            tenant_status=tenant.status,
            store_id=store.id,
            store_public_id=store.public_id,
            store_status=store.status,
            connection_id=connection.id,
            connection_public_id=connection.public_id,
            connection_status=connection.status,
        )

    def find_message_reference(
        self,
        idempotency_key: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> PersistedMessageReference | None:
        row = self.session.execute(
            select(
                Conversation.public_id,
                ConversationMessage.public_id,
            )
            .join(
                Conversation,
                and_(
                    Conversation.id == ConversationMessage.conversation_id,
                    Conversation.tenant_id == ConversationMessage.tenant_id,
                    Conversation.store_id == ConversationMessage.store_id,
                ),
            )
            .where(
                ConversationMessage.idempotency_key == idempotency_key,
                ConversationMessage.tenant_id == tenant_id,
                ConversationMessage.store_id == store_id,
            )
        ).one_or_none()
        if row is None:
            return None
        return PersistedMessageReference(
            conversation_public_id=row[0],
            message_public_id=row[1],
        )

    def find_conversation_public_id(
        self,
        *,
        tenant_id: int,
        store_id: int,
        connection_id: int,
        provider_participant_key: str,
    ) -> str | None:
        return self.session.scalar(
            select(Conversation.public_id).where(
                Conversation.tenant_id == tenant_id,
                Conversation.store_id == store_id,
                Conversation.instagram_connection_id == connection_id,
                Conversation.provider_participant_key
                == provider_participant_key,
            )
        )
