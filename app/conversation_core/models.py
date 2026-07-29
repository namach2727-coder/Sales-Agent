"""SQLAlchemy persistence models for FOUNDATION-09A Conversation Core."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import new_public_id, utc_now


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversations_id_tenant_store",
        ),
        UniqueConstraint(
            "instagram_connection_id",
            "provider_participant_key",
            name="uq_conversations_connection_participant",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversations_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversations_store_tenant",
        ),
        ForeignKeyConstraint(
            ("instagram_connection_id", "tenant_id", "store_id"),
            (
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ),
            name="fk_conversations_instagram_connection_scope",
        ),
        CheckConstraint(
            "status IN ('open', 'waiting_for_customer', 'handoff_requested', "
            "'human_active', 'closed', 'archived')",
            name="ck_conversations_status",
        ),
        CheckConstraint("revision >= 1", name="ck_conversations_revision"),
        CheckConstraint(
            "message_count >= 0",
            name="ck_conversations_message_count",
        ),
        CheckConstraint(
            "inbound_message_count >= 0",
            name="ck_conversations_inbound_message_count",
        ),
        CheckConstraint(
            "outbound_message_count >= 0",
            name="ck_conversations_outbound_message_count",
        ),
        CheckConstraint(
            "message_count = inbound_message_count + outbound_message_count",
            name="ck_conversations_message_count_consistency",
        ),
        CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR "
            "(status != 'archived' AND archived_at IS NULL)",
            name="ck_conversations_archived_state",
        ),
        CheckConstraint(
            "status IN ('closed', 'archived') OR closed_at IS NULL",
            name="ck_conversations_closed_state",
        ),
        Index("ix_conversations_public_id", "public_id", unique=True),
        Index("ix_conversations_tenant_id", "tenant_id"),
        Index("ix_conversations_store_id", "store_id"),
        Index(
            "ix_conversations_instagram_connection_id",
            "instagram_connection_id",
        ),
        Index("ix_conversations_status", "status"),
        Index("ix_conversations_last_message_at", "last_message_at"),
        Index(
            "ix_conversations_tenant_store_status_last_message",
            "tenant_id",
            "store_id",
            "status",
            "last_message_at",
        ),
        Index(
            "ix_conversations_tenant_store_last_message",
            "tenant_id",
            "store_id",
            "last_message_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    instagram_connection_id: Mapped[int] = mapped_column(Integer)
    provider_participant_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="open")
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_inbound_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_outbound_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    inbound_message_count: Mapped[int] = mapped_column(Integer, default=0)
    outbound_message_count: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {
        "version_id_col": revision,
        "version_id_generator": False,
    }
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ConversationParticipant(Base):
    """Conversation actor.

    Ordinary uniqueness cannot eliminate every NULL-related duplicate on every
    supported database; the repository must also enforce participant identity.
    """

    __tablename__ = "conversation_participants"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_participants_id_tenant_store",
        ),
        UniqueConstraint(
            "conversation_id",
            "participant_type",
            "provider_participant_key",
            name="uq_conversation_participants_provider",
        ),
        UniqueConstraint(
            "conversation_id",
            "participant_type",
            "user_id",
            name="uq_conversation_participants_user",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversation_participants_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversation_participants_store_tenant",
        ),
        ForeignKeyConstraint(
            ("conversation_id", "tenant_id", "store_id"),
            ("conversations.id", "conversations.tenant_id", "conversations.store_id"),
            name="fk_conversation_participants_conversation_scope",
        ),
        CheckConstraint(
            "participant_type IN ('customer', 'instagram_business', "
            "'system', 'operator')",
            name="ck_conversation_participants_type",
        ),
        CheckConstraint(
            "(participant_type NOT IN ('customer', 'instagram_business')) OR "
            "(provider_participant_key IS NOT NULL AND user_id IS NULL)",
            name="ck_conversation_participants_provider_identity",
        ),
        CheckConstraint(
            "participant_type != 'operator' OR user_id IS NOT NULL",
            name="ck_conversation_participants_operator_identity",
        ),
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_conversation_participants_membership_time",
        ),
        Index(
            "ix_conversation_participants_public_id",
            "public_id",
            unique=True,
        ),
        Index(
            "ix_conversation_participants_tenant_store_conversation",
            "tenant_id",
            "store_id",
            "conversation_id",
        ),
        Index(
            "ix_conversation_participants_conversation_type",
            "conversation_id",
            "participant_type",
        ),
        Index(
            "ix_conversation_participants_provider_participant_key",
            "provider_participant_key",
        ),
        Index("ix_conversation_participants_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(Integer)
    participant_type: Mapped[str] = mapped_column(String(30))
    provider_participant_key: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_messages_id_tenant_store",
        ),
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_conversation_messages_tenant_idempotency",
        ),
        UniqueConstraint(
            "instagram_connection_id",
            "provider_message_id",
            name="uq_conversation_messages_provider",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversation_messages_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversation_messages_store_tenant",
        ),
        ForeignKeyConstraint(
            ("conversation_id", "tenant_id", "store_id"),
            ("conversations.id", "conversations.tenant_id", "conversations.store_id"),
            name="fk_conversation_messages_conversation_scope",
        ),
        ForeignKeyConstraint(
            ("instagram_connection_id", "tenant_id", "store_id"),
            (
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ),
            name="fk_conversation_messages_instagram_connection_scope",
        ),
        ForeignKeyConstraint(
            ("instagram_inbound_event_id", "tenant_id", "store_id"),
            (
                "instagram_inbound_events.id",
                "instagram_inbound_events.tenant_id",
                "instagram_inbound_events.store_id",
            ),
            name="fk_conversation_messages_inbound_event_scope",
        ),
        ForeignKeyConstraint(
            ("reply_to_message_id", "tenant_id", "store_id"),
            (
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ),
            name="fk_conversation_messages_reply_scope",
        ),
        ForeignKeyConstraint(
            ("sender_participant_id", "tenant_id", "store_id"),
            (
                "conversation_participants.id",
                "conversation_participants.tenant_id",
                "conversation_participants.store_id",
            ),
            name="fk_conversation_messages_sender_scope",
        ),
        CheckConstraint(
            "direction IN ('inbound', 'outbound', 'system')",
            name="ck_conversation_messages_direction",
        ),
        CheckConstraint(
            "content_type IN ('text', 'image', 'video', 'audio', 'file', "
            "'sticker', 'reaction', 'unsupported')",
            name="ck_conversation_messages_content_type",
        ),
        CheckConstraint(
            "content_type != 'text' OR text IS NOT NULL",
            name="ck_conversation_messages_text_content",
        ),
        CheckConstraint(
            "direction != 'inbound' OR instagram_inbound_event_id IS NOT NULL",
            name="ck_conversation_messages_inbound_linkage",
        ),
        Index("ix_conversation_messages_public_id", "public_id", unique=True),
        Index(
            "ix_conversation_messages_instagram_inbound_event_id",
            "instagram_inbound_event_id",
        ),
        Index("ix_conversation_messages_direction", "direction"),
        Index("ix_conversation_messages_content_type", "content_type"),
        Index("ix_conversation_messages_provider_event_at", "provider_event_at"),
        Index("ix_conversation_messages_occurred_at", "occurred_at"),
        Index(
            "ix_conversation_messages_tenant_store_conversation_occurred",
            "tenant_id",
            "store_id",
            "conversation_id",
            "occurred_at",
        ),
        Index(
            "ix_conversation_messages_conversation_occurred",
            "conversation_id",
            "occurred_at",
        ),
        Index(
            "ix_conversation_messages_tenant_store_direction_occurred",
            "tenant_id",
            "store_id",
            "direction",
            "occurred_at",
        ),
        Index(
            "ix_conversation_messages_connection_provider",
            "instagram_connection_id",
            "provider_message_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(Integer)
    instagram_connection_id: Mapped[int] = mapped_column(Integer)
    instagram_inbound_event_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(20))
    content_type: Mapped[str] = mapped_column(String(30))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_participant_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    reply_to_message_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    provider_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class ConversationAssignment(Base):
    """Assignment history.

    A repository transaction must enforce one currently assigned row. A future
    migration may add a PostgreSQL partial unique index after policy approval.
    """

    __tablename__ = "conversation_assignments"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_assignments_id_tenant_store",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversation_assignments_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversation_assignments_store_tenant",
        ),
        ForeignKeyConstraint(
            ("conversation_id", "tenant_id", "store_id"),
            ("conversations.id", "conversations.tenant_id", "conversations.store_id"),
            name="fk_conversation_assignments_conversation_scope",
        ),
        CheckConstraint(
            "status IN ('assigned', 'released')",
            name="ck_conversation_assignments_status",
        ),
        CheckConstraint(
            "(status = 'assigned' AND released_at IS NULL AND "
            "released_by_user_id IS NULL) OR "
            "(status = 'released' AND released_at IS NOT NULL AND "
            "released_by_user_id IS NOT NULL)",
            name="ck_conversation_assignments_state",
        ),
        CheckConstraint(
            "released_at IS NULL OR released_at >= assigned_at",
            name="ck_conversation_assignments_release_time",
        ),
        Index(
            "ix_conversation_assignments_public_id",
            "public_id",
            unique=True,
        ),
        Index("ix_conversation_assignments_assignee_user_id", "assignee_user_id"),
        Index("ix_conversation_assignments_status", "status"),
        Index(
            "ix_conversation_assignments_tenant_store_conversation_status",
            "tenant_id",
            "store_id",
            "conversation_id",
            "status",
        ),
        Index(
            "ix_conversation_assignments_assignee_status",
            "assignee_user_id",
            "status",
        ),
        Index(
            "ix_conversation_assignments_conversation_assigned",
            "conversation_id",
            "assigned_at",
        ),
        Index(
            "ix_conversation_assignments_conversation_status",
            "conversation_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(Integer)
    assignee_user_id: Mapped[int] = mapped_column(Integer)
    assigned_by_user_id: Mapped[int] = mapped_column(Integer)
    released_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="assigned")
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class ConversationReadState(Base):
    """Per-user read cursor.

    The repository must verify that the selected message belongs to the same
    conversation; portable CHECK constraints cannot inspect another table.
    """

    __tablename__ = "conversation_read_states"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_read_states_id_tenant_store",
        ),
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_read_states_conversation_user",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversation_read_states_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversation_read_states_store_tenant",
        ),
        ForeignKeyConstraint(
            ("conversation_id", "tenant_id", "store_id"),
            ("conversations.id", "conversations.tenant_id", "conversations.store_id"),
            name="fk_conversation_read_states_conversation_scope",
        ),
        ForeignKeyConstraint(
            ("last_read_message_id", "tenant_id", "store_id"),
            (
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ),
            name="fk_conversation_read_states_message_scope",
        ),
        Index(
            "ix_conversation_read_states_public_id",
            "public_id",
            unique=True,
        ),
        Index(
            "ix_conversation_read_states_tenant_store_user",
            "tenant_id",
            "store_id",
            "user_id",
        ),
        Index(
            "ix_conversation_read_states_conversation_user",
            "conversation_id",
            "user_id",
        ),
        Index(
            "ix_conversation_read_states_last_read_message_id",
            "last_read_message_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(Integer)
    last_read_message_id: Mapped[int] = mapped_column(Integer)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class ConversationProcessingRecord(Base):
    __tablename__ = "conversation_processing_records"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_processing_records_id_tenant_store",
        ),
        UniqueConstraint(
            "instagram_inbound_event_id",
            name="uq_conversation_processing_records_inbound_event",
        ),
        ForeignKeyConstraint(
            ("tenant_id",),
            ("tenants.id",),
            name="fk_conversation_processing_records_tenant",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_conversation_processing_records_store_tenant",
        ),
        ForeignKeyConstraint(
            ("instagram_inbound_event_id", "tenant_id", "store_id"),
            (
                "instagram_inbound_events.id",
                "instagram_inbound_events.tenant_id",
                "instagram_inbound_events.store_id",
            ),
            name="fk_conversation_processing_records_inbound_event_scope",
        ),
        ForeignKeyConstraint(
            ("conversation_id", "tenant_id", "store_id"),
            ("conversations.id", "conversations.tenant_id", "conversations.store_id"),
            name="fk_conversation_processing_records_conversation_scope",
        ),
        ForeignKeyConstraint(
            ("message_id", "tenant_id", "store_id"),
            (
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ),
            name="fk_conversation_processing_records_message_scope",
        ),
        CheckConstraint(
            "status IN ('pending', 'processed', 'ignored', 'failed')",
            name="ck_conversation_processing_records_status",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_conversation_processing_records_attempt_count",
        ),
        CheckConstraint(
            "status != 'processed' OR "
            "(conversation_id IS NOT NULL AND message_id IS NOT NULL AND "
            "processed_at IS NOT NULL AND failure_category IS NULL AND "
            "safe_failure_detail IS NULL)",
            name="ck_conversation_processing_records_processed",
        ),
        CheckConstraint(
            "status != 'ignored' OR processed_at IS NOT NULL",
            name="ck_conversation_processing_records_ignored",
        ),
        CheckConstraint(
            "status != 'failed' OR failure_category IS NOT NULL",
            name="ck_conversation_processing_records_failed",
        ),
        CheckConstraint(
            "status != 'pending' OR processed_at IS NULL",
            name="ck_conversation_processing_records_pending",
        ),
        Index(
            "ix_conversation_processing_records_public_id",
            "public_id",
            unique=True,
        ),
        Index(
            "ix_conversation_processing_records_status",
            "status",
        ),
        Index(
            "ix_conversation_processing_records_tenant_store_status_created",
            "tenant_id",
            "store_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_conversation_processing_records_inbound_event_id",
            "instagram_inbound_event_id",
        ),
        Index(
            "ix_conversation_processing_records_conversation_id",
            "conversation_id",
        ),
        Index(
            "ix_conversation_processing_records_message_id",
            "message_id",
        ),
        Index(
            "ix_conversation_processing_records_status_created",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id)
    tenant_id: Mapped[int] = mapped_column(Integer)
    store_id: Mapped[int] = mapped_column(Integer)
    instagram_inbound_event_id: Mapped[int] = mapped_column(Integer)
    conversation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    safe_failure_detail: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
