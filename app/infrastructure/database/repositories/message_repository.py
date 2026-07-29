"""Persistence operations for conversation messages."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conversation_core.models import ConversationMessage
from app.infrastructure.database.repositories.base import BaseRepository


class MessageRepository(BaseRepository[ConversationMessage]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ConversationMessage)

    def create(self, message: ConversationMessage) -> ConversationMessage:
        self.add(message)
        self.flush()
        return message

    def list_by_conversation(
        self,
        conversation_id: int,
        *,
        tenant_id: int,
        store_id: int,
    ) -> tuple[ConversationMessage, ...]:
        return tuple(
            self.session.scalars(
                select(ConversationMessage)
                .where(
                    ConversationMessage.conversation_id == conversation_id,
                    ConversationMessage.tenant_id == tenant_id,
                    ConversationMessage.store_id == store_id,
                )
                .order_by(
                    ConversationMessage.occurred_at,
                    ConversationMessage.id,
                )
            ).all()
        )

    def exists_message_key(
        self,
        idempotency_key: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> bool:
        message_id = self.session.scalar(
            select(ConversationMessage.id)
            .where(
                ConversationMessage.idempotency_key == idempotency_key,
                ConversationMessage.tenant_id == tenant_id,
                ConversationMessage.store_id == store_id,
            )
            .limit(1)
        )
        return message_id is not None
