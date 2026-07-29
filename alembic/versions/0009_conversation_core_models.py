"""Add tenant-safe conversation core persistence and isolate legacy history.

Revision ID: 0009_conversation_core_models
Revises: 0008_instagram_channel
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_conversation_core_models"
down_revision: Union[str, Sequence[str], None] = "0008_instagram_channel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The forward rename preserves every legacy row and was explicitly reviewed.
DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = True
EMPTY_DOWNGRADE_ALLOWED = False


def _create_public_id_index(table_name: str) -> None:
    op.create_index(
        f"ix_{table_name}_public_id",
        table_name,
        ["public_id"],
        unique=True,
    )


def upgrade() -> None:
    op.rename_table("conversations", "legacy_conversations")
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            sa.text(
                "ALTER SEQUENCE conversations_id_seq "
                "RENAME TO legacy_conversations_id_seq"
            )
        )
    op.drop_index(
        "ix_conversations_customer_id",
        table_name="legacy_conversations",
    )
    op.create_index(
        "ix_legacy_conversations_customer_id",
        "legacy_conversations",
        ["customer_id"],
        unique=False,
    )

    with op.batch_alter_table("instagram_inbound_events") as batch_op:
        batch_op.create_unique_constraint(
            "uq_instagram_events_id_tenant_store",
            ["id", "tenant_id", "store_id"],
        )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("instagram_connection_id", sa.Integer(), nullable=False),
        sa.Column("provider_participant_key", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_inbound_message_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_outbound_message_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("inbound_message_count", sa.Integer(), nullable=False),
        sa.Column("outbound_message_count", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR "
            "(status != 'archived' AND archived_at IS NULL)",
            name="ck_conversations_archived_state",
        ),
        sa.CheckConstraint(
            "status IN ('closed', 'archived') OR closed_at IS NULL",
            name="ck_conversations_closed_state",
        ),
        sa.CheckConstraint(
            "inbound_message_count >= 0",
            name="ck_conversations_inbound_message_count",
        ),
        sa.CheckConstraint(
            "message_count >= 0",
            name="ck_conversations_message_count",
        ),
        sa.CheckConstraint(
            "message_count = inbound_message_count + outbound_message_count",
            name="ck_conversations_message_count_consistency",
        ),
        sa.CheckConstraint(
            "outbound_message_count >= 0",
            name="ck_conversations_outbound_message_count",
        ),
        sa.CheckConstraint("revision >= 1", name="ck_conversations_revision"),
        sa.CheckConstraint(
            "status IN ('open', 'waiting_for_customer', 'handoff_requested', "
            "'human_active', 'closed', 'archived')",
            name="ck_conversations_status",
        ),
        sa.ForeignKeyConstraint(
            ["instagram_connection_id", "tenant_id", "store_id"],
            [
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ],
            name="fk_conversations_instagram_connection_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversations_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversations_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instagram_connection_id",
            "provider_participant_key",
            name="uq_conversations_connection_participant",
        ),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversations_id_tenant_store",
        ),
    )
    _create_public_id_index("conversations")
    op.create_index(
        "ix_conversations_tenant_id",
        "conversations",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_store_id",
        "conversations",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_instagram_connection_id",
        "conversations",
        ["instagram_connection_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_status",
        "conversations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_last_message_at",
        "conversations",
        ["last_message_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_tenant_store_status_last_message",
        "conversations",
        ["tenant_id", "store_id", "status", "last_message_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_tenant_store_last_message",
        "conversations",
        ["tenant_id", "store_id", "last_message_at"],
        unique=False,
    )

    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("participant_type", sa.String(length=30), nullable=False),
        sa.Column(
            "provider_participant_key",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("username", sa.String(length=200), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_conversation_participants_membership_time",
        ),
        sa.CheckConstraint(
            "participant_type != 'operator' OR user_id IS NOT NULL",
            name="ck_conversation_participants_operator_identity",
        ),
        sa.CheckConstraint(
            "(participant_type NOT IN ('customer', 'instagram_business')) OR "
            "(provider_participant_key IS NOT NULL AND user_id IS NULL)",
            name="ck_conversation_participants_provider_identity",
        ),
        sa.CheckConstraint(
            "participant_type IN ('customer', 'instagram_business', "
            "'system', 'operator')",
            name="ck_conversation_participants_type",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "tenant_id", "store_id"],
            ["conversations.id", "conversations.tenant_id", "conversations.store_id"],
            name="fk_conversation_participants_conversation_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversation_participants_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversation_participants_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "participant_type",
            "provider_participant_key",
            name="uq_conversation_participants_provider",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "participant_type",
            "user_id",
            name="uq_conversation_participants_user",
        ),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_participants_id_tenant_store",
        ),
    )
    _create_public_id_index("conversation_participants")
    op.create_index(
        "ix_conversation_participants_tenant_store_conversation",
        "conversation_participants",
        ["tenant_id", "store_id", "conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_participants_conversation_type",
        "conversation_participants",
        ["conversation_id", "participant_type"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_participants_provider_participant_key",
        "conversation_participants",
        ["provider_participant_key"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_participants_user_id",
        "conversation_participants",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("instagram_connection_id", sa.Integer(), nullable=False),
        sa.Column("instagram_inbound_event_id", sa.Integer(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("content_type", sa.String(length=30), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("sender_participant_id", sa.Integer(), nullable=True),
        sa.Column("reply_to_message_id", sa.Integer(), nullable=True),
        sa.Column("provider_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "content_type IN ('text', 'image', 'video', 'audio', 'file', "
            "'sticker', 'reaction', 'unsupported')",
            name="ck_conversation_messages_content_type",
        ),
        sa.CheckConstraint(
            "direction IN ('inbound', 'outbound', 'system')",
            name="ck_conversation_messages_direction",
        ),
        sa.CheckConstraint(
            "direction != 'inbound' OR instagram_inbound_event_id IS NOT NULL",
            name="ck_conversation_messages_inbound_linkage",
        ),
        sa.CheckConstraint(
            "content_type != 'text' OR text IS NOT NULL",
            name="ck_conversation_messages_text_content",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "tenant_id", "store_id"],
            ["conversations.id", "conversations.tenant_id", "conversations.store_id"],
            name="fk_conversation_messages_conversation_scope",
        ),
        sa.ForeignKeyConstraint(
            ["instagram_connection_id", "tenant_id", "store_id"],
            [
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ],
            name="fk_conversation_messages_instagram_connection_scope",
        ),
        sa.ForeignKeyConstraint(
            ["instagram_inbound_event_id", "tenant_id", "store_id"],
            [
                "instagram_inbound_events.id",
                "instagram_inbound_events.tenant_id",
                "instagram_inbound_events.store_id",
            ],
            name="fk_conversation_messages_inbound_event_scope",
        ),
        sa.ForeignKeyConstraint(
            ["reply_to_message_id", "tenant_id", "store_id"],
            [
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ],
            name="fk_conversation_messages_reply_scope",
        ),
        sa.ForeignKeyConstraint(
            ["sender_participant_id", "tenant_id", "store_id"],
            [
                "conversation_participants.id",
                "conversation_participants.tenant_id",
                "conversation_participants.store_id",
            ],
            name="fk_conversation_messages_sender_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversation_messages_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversation_messages_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_messages_id_tenant_store",
        ),
        sa.UniqueConstraint(
            "instagram_connection_id",
            "provider_message_id",
            name="uq_conversation_messages_provider",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_conversation_messages_tenant_idempotency",
        ),
    )
    _create_public_id_index("conversation_messages")
    op.create_index(
        "ix_conversation_messages_instagram_inbound_event_id",
        "conversation_messages",
        ["instagram_inbound_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_direction",
        "conversation_messages",
        ["direction"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_content_type",
        "conversation_messages",
        ["content_type"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_provider_event_at",
        "conversation_messages",
        ["provider_event_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_occurred_at",
        "conversation_messages",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_tenant_store_conversation_occurred",
        "conversation_messages",
        ["tenant_id", "store_id", "conversation_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_conversation_occurred",
        "conversation_messages",
        ["conversation_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_tenant_store_direction_occurred",
        "conversation_messages",
        ["tenant_id", "store_id", "direction", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_connection_provider",
        "conversation_messages",
        ["instagram_connection_id", "provider_message_id"],
        unique=False,
    )

    op.create_table(
        "conversation_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("assignee_user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
        sa.Column("released_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "released_at IS NULL OR released_at >= assigned_at",
            name="ck_conversation_assignments_release_time",
        ),
        sa.CheckConstraint(
            "(status = 'assigned' AND released_at IS NULL AND "
            "released_by_user_id IS NULL) OR "
            "(status = 'released' AND released_at IS NOT NULL AND "
            "released_by_user_id IS NOT NULL)",
            name="ck_conversation_assignments_state",
        ),
        sa.CheckConstraint(
            "status IN ('assigned', 'released')",
            name="ck_conversation_assignments_status",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "tenant_id", "store_id"],
            ["conversations.id", "conversations.tenant_id", "conversations.store_id"],
            name="fk_conversation_assignments_conversation_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversation_assignments_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversation_assignments_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_assignments_id_tenant_store",
        ),
    )
    _create_public_id_index("conversation_assignments")
    op.create_index(
        "ix_conversation_assignments_assignee_user_id",
        "conversation_assignments",
        ["assignee_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_assignments_status",
        "conversation_assignments",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_assignments_tenant_store_conversation_status",
        "conversation_assignments",
        ["tenant_id", "store_id", "conversation_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_assignments_assignee_status",
        "conversation_assignments",
        ["assignee_user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_assignments_conversation_assigned",
        "conversation_assignments",
        ["conversation_id", "assigned_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_assignments_conversation_status",
        "conversation_assignments",
        ["conversation_id", "status"],
        unique=False,
    )

    op.create_table(
        "conversation_read_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_read_message_id", sa.Integer(), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id", "tenant_id", "store_id"],
            ["conversations.id", "conversations.tenant_id", "conversations.store_id"],
            name="fk_conversation_read_states_conversation_scope",
        ),
        sa.ForeignKeyConstraint(
            ["last_read_message_id", "tenant_id", "store_id"],
            [
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ],
            name="fk_conversation_read_states_message_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversation_read_states_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversation_read_states_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_read_states_conversation_user",
        ),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_read_states_id_tenant_store",
        ),
    )
    _create_public_id_index("conversation_read_states")
    op.create_index(
        "ix_conversation_read_states_tenant_store_user",
        "conversation_read_states",
        ["tenant_id", "store_id", "user_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_read_states_conversation_user",
        "conversation_read_states",
        ["conversation_id", "user_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_read_states_last_read_message_id",
        "conversation_read_states",
        ["last_read_message_id"],
        unique=False,
    )

    op.create_table(
        "conversation_processing_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("instagram_inbound_event_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("failure_category", sa.String(length=100), nullable=True),
        sa.Column("safe_failure_detail", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_conversation_processing_records_attempt_count",
        ),
        sa.CheckConstraint(
            "status != 'failed' OR failure_category IS NOT NULL",
            name="ck_conversation_processing_records_failed",
        ),
        sa.CheckConstraint(
            "status != 'ignored' OR processed_at IS NOT NULL",
            name="ck_conversation_processing_records_ignored",
        ),
        sa.CheckConstraint(
            "status != 'pending' OR processed_at IS NULL",
            name="ck_conversation_processing_records_pending",
        ),
        sa.CheckConstraint(
            "status != 'processed' OR "
            "(conversation_id IS NOT NULL AND message_id IS NOT NULL AND "
            "processed_at IS NOT NULL AND failure_category IS NULL AND "
            "safe_failure_detail IS NULL)",
            name="ck_conversation_processing_records_processed",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processed', 'ignored', 'failed')",
            name="ck_conversation_processing_records_status",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "tenant_id", "store_id"],
            ["conversations.id", "conversations.tenant_id", "conversations.store_id"],
            name="fk_conversation_processing_records_conversation_scope",
        ),
        sa.ForeignKeyConstraint(
            ["instagram_inbound_event_id", "tenant_id", "store_id"],
            [
                "instagram_inbound_events.id",
                "instagram_inbound_events.tenant_id",
                "instagram_inbound_events.store_id",
            ],
            name="fk_conversation_processing_records_inbound_event_scope",
        ),
        sa.ForeignKeyConstraint(
            ["message_id", "tenant_id", "store_id"],
            [
                "conversation_messages.id",
                "conversation_messages.tenant_id",
                "conversation_messages.store_id",
            ],
            name="fk_conversation_processing_records_message_scope",
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_conversation_processing_records_store_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_conversation_processing_records_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_conversation_processing_records_id_tenant_store",
        ),
        sa.UniqueConstraint(
            "instagram_inbound_event_id",
            name="uq_conversation_processing_records_inbound_event",
        ),
    )
    _create_public_id_index("conversation_processing_records")
    op.create_index(
        "ix_conversation_processing_records_status",
        "conversation_processing_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_processing_records_tenant_store_status_created",
        "conversation_processing_records",
        ["tenant_id", "store_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_processing_records_inbound_event_id",
        "conversation_processing_records",
        ["instagram_inbound_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_processing_records_conversation_id",
        "conversation_processing_records",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_processing_records_message_id",
        "conversation_processing_records",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_processing_records_status_created",
        "conversation_processing_records",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("conversation_processing_records")
    op.drop_table("conversation_read_states")
    op.drop_table("conversation_assignments")
    op.drop_table("conversation_messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")

    with op.batch_alter_table("instagram_inbound_events") as batch_op:
        batch_op.drop_constraint(
            "uq_instagram_events_id_tenant_store",
            type_="unique",
        )

    op.drop_index(
        "ix_legacy_conversations_customer_id",
        table_name="legacy_conversations",
    )
    op.create_index(
        "ix_conversations_customer_id",
        "legacy_conversations",
        ["customer_id"],
        unique=False,
    )
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            sa.text(
                "ALTER SEQUENCE legacy_conversations_id_seq "
                "RENAME TO conversations_id_seq"
            )
        )
    op.rename_table("legacy_conversations", "conversations")
