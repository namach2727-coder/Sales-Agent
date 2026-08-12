"""Persistence operations for conversations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.conversation_core.models import Conversation
from app.infrastructure.database.repositories.base import BaseRepository
from app.models import utc_now


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Conversation)

    def create(self, conversation: Conversation) -> Conversation:
        self.add(conversation)
        self.flush()
        return conversation

    def get_by_public_id(
        self,
        public_id: str,
        *,
        tenant_id: int,
        store_id: int,
    ) -> Conversation | None:
        return self.session.scalar(
            select(Conversation).where(
                Conversation.public_id == public_id,
                Conversation.tenant_id == tenant_id,
                Conversation.store_id == store_id,
            )
        )

    def list_by_store(
        self,
        *,
        tenant_id: int,
        store_id: int,
    ) -> tuple[Conversation, ...]:
        return tuple(
            self.session.scalars(
                select(Conversation)
                .where(
                    Conversation.tenant_id == tenant_id,
                    Conversation.store_id == store_id,
                )
                .order_by(Conversation.created_at.desc(), Conversation.id.desc())
            ).all()
        )

    def page_by_store(
        self,
        *,
        tenant_id: int,
        store_id: int,
        page: int,
        page_size: int,
    ) -> tuple[tuple[Conversation, ...], int]:
        scoped = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.store_id == store_id,
            )
        )
        total = self.session.scalar(
            select(func.count()).select_from(scoped.subquery())
        ) or 0
        items = tuple(
            self.session.scalars(
                scoped.order_by(
                    Conversation.last_message_at.desc().nullslast(),
                    Conversation.created_at.desc(),
                    Conversation.id.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

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
        if conversation is None:
            return None
        conversation.status = status
        conversation.revision += 1
        self.flush()
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
        if conversation is None:
            return None
        conversation.status = "archived"
        conversation.archived_at = archived_at or utc_now()
        conversation.revision += 1
        self.flush()
        return conversation
