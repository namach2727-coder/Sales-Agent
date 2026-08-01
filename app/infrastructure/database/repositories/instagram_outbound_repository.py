"""Tenant-scoped persistence required by Instagram outbound delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.conversation_core.models import Conversation, ConversationMessage
from app.instagram_channel.models import InstagramConnection


@dataclass(frozen=True, slots=True)
class InstagramOutboundMessageContext:
    message_public_id: str
    conversation_public_id: str
    conversation_id: int
    instagram_connection_id: int
    provider_participant_key: str
    direction: str
    content_type: str
    text: str | None
    provider_message_id: str | None
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class InstagramOutboundConnectionContext:
    connection_id: int
    connection_public_id: str
    instagram_account_id: str
    encrypted_access_token: str | None


class InstagramOutboundRepository:
    """Resolve and mutate outbound state without owning the transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_message_context(
        self,
        message_public_id: str,
        *,
        conversation_public_id: str,
        tenant_id: int,
        store_id: int,
    ) -> InstagramOutboundMessageContext | None:
        row = self.session.execute(
            select(ConversationMessage, Conversation)
            .join(
                Conversation,
                and_(
                    Conversation.id == ConversationMessage.conversation_id,
                    Conversation.tenant_id == ConversationMessage.tenant_id,
                    Conversation.store_id == ConversationMessage.store_id,
                ),
            )
            .where(
                ConversationMessage.public_id == message_public_id,
                ConversationMessage.tenant_id == tenant_id,
                ConversationMessage.store_id == store_id,
                Conversation.public_id == conversation_public_id,
            )
        ).one_or_none()
        if row is None:
            return None
        message, conversation = row
        return InstagramOutboundMessageContext(
            message_public_id=message.public_id,
            conversation_public_id=conversation.public_id,
            conversation_id=conversation.id,
            instagram_connection_id=conversation.instagram_connection_id,
            provider_participant_key=conversation.provider_participant_key,
            direction=message.direction,
            content_type=message.content_type,
            text=message.text,
            provider_message_id=message.provider_message_id,
            metadata=dict(message.metadata_json or {}),
        )

    def list_active_connections(
        self,
        *,
        tenant_id: int,
        store_id: int,
    ) -> tuple[InstagramOutboundConnectionContext, ...]:
        connections = self.session.scalars(
            select(InstagramConnection).where(
                InstagramConnection.tenant_id == tenant_id,
                InstagramConnection.store_id == store_id,
                InstagramConnection.status == "active",
            )
        ).all()
        return tuple(
            InstagramOutboundConnectionContext(
                connection_id=connection.id,
                connection_public_id=connection.public_id,
                instagram_account_id=connection.instagram_account_id,
                encrypted_access_token=connection.encrypted_access_token,
            )
            for connection in connections
        )

    def update_delivery(
        self,
        message_public_id: str,
        *,
        conversation_public_id: str,
        tenant_id: int,
        store_id: int,
        metadata: Mapping[str, object],
        provider_message_id: str | None = None,
    ) -> bool:
        message = self.session.scalar(
            select(ConversationMessage)
            .join(
                Conversation,
                and_(
                    Conversation.id == ConversationMessage.conversation_id,
                    Conversation.tenant_id == ConversationMessage.tenant_id,
                    Conversation.store_id == ConversationMessage.store_id,
                ),
            )
            .where(
                ConversationMessage.public_id == message_public_id,
                ConversationMessage.tenant_id == tenant_id,
                ConversationMessage.store_id == store_id,
                Conversation.public_id == conversation_public_id,
            )
        )
        if message is None:
            return False
        message.metadata_json = dict(metadata)
        if provider_message_id is not None:
            message.provider_message_id = provider_message_id
        self.session.flush()
        return True
