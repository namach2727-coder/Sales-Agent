"""Instagram channel connectivity and inbound webhook ingestion.

Revision ID: 0008_instagram_channel
Revises: 0007_business_profile_knowledge
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_instagram_channel"
down_revision: Union[str, Sequence[str], None] = "0007_business_profile_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.create_table(
        "instagram_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("meta_app_id", sa.String(length=100), nullable=True),
        sa.Column("facebook_page_id", sa.String(length=200), nullable=True),
        sa.Column("instagram_account_id", sa.String(length=200), nullable=False),
        sa.Column("instagram_username", sa.String(length=100), nullable=True),
        sa.Column("external_account_name", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("status_reason", sa.String(length=500), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_webhook_received_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("encrypted_access_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=50), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_scopes", sa.JSON(), nullable=False),
        sa.Column("token_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status != 'archived' AND archived_at IS NULL) OR "
            "(status = 'archived' AND archived_at IS NOT NULL)",
            name="ck_instagram_connections_archived_state",
        ),
        sa.CheckConstraint(
            "revision >= 1", name="ck_instagram_connections_revision"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'degraded', 'disconnected', "
            "'revoked', 'archived')",
            name="ck_instagram_connections_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_instagram_connections_store_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instagram_account_id",
            name="uq_instagram_connections_account",
        ),
        sa.UniqueConstraint(
            "facebook_page_id",
            name="uq_instagram_connections_page",
        ),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_instagram_connections_id_tenant_store",
        ),
        sa.UniqueConstraint("store_id", name="uq_instagram_connections_store"),
    )
    op.create_index(
        op.f("ix_instagram_connections_public_id"),
        "instagram_connections",
        ["public_id"],
        unique=True,
    )
    for column in (
        "tenant_id",
        "store_id",
        "facebook_page_id",
        "instagram_account_id",
        "status",
    ):
        op.create_index(
            op.f(f"ix_instagram_connections_{column}"),
            "instagram_connections",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_instagram_connections_tenant_store_status",
        "instagram_connections",
        ["tenant_id", "store_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_connections_routing",
        "instagram_connections",
        ["instagram_account_id", "facebook_page_id", "status"],
        unique=False,
    )

    op.create_table(
        "instagram_webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("external_delivery_key", sa.String(length=200), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("signature_algorithm", sa.String(length=30), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=False),
        sa.Column("verification_state", sa.String(length=20), nullable=False),
        sa.Column("processing_status", sa.String(length=20), nullable=False),
        sa.Column("failure_category", sa.String(length=100), nullable=True),
        sa.Column("safe_failure_detail", sa.String(length=500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("instagram_connection_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "processing_status IN ('received', 'rejected', 'duplicate', "
            "'accepted', 'processed', 'failed', 'ignored')",
            name="ck_instagram_deliveries_status",
        ),
        sa.CheckConstraint(
            "provider = 'meta'", name="ck_instagram_deliveries_provider"
        ),
        sa.CheckConstraint(
            "(tenant_id IS NULL AND store_id IS NULL AND "
            "instagram_connection_id IS NULL) OR "
            "(tenant_id IS NOT NULL AND store_id IS NOT NULL AND "
            "instagram_connection_id IS NOT NULL)",
            name="ck_instagram_deliveries_resolved_scope",
        ),
        sa.CheckConstraint(
            "retry_count >= 0", name="ck_instagram_deliveries_retries"
        ),
        sa.CheckConstraint(
            "verification_state IN ('verified', 'unverified', 'invalid')",
            name="ck_instagram_deliveries_verification",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["instagram_connection_id", "tenant_id", "store_id"],
            [
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ],
            name="fk_instagram_deliveries_connection_scope",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "external_delivery_key",
            name="uq_instagram_deliveries_external_key",
        ),
        sa.UniqueConstraint(
            "provider",
            "payload_hash",
            name="uq_instagram_deliveries_payload_hash",
        ),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_instagram_deliveries_id_tenant_store",
        ),
    )
    op.create_index(
        op.f("ix_instagram_webhook_deliveries_public_id"),
        "instagram_webhook_deliveries",
        ["public_id"],
        unique=True,
    )
    for column in (
        "processing_status",
        "correlation_id",
        "tenant_id",
        "store_id",
        "instagram_connection_id",
    ):
        op.create_index(
            op.f(f"ix_instagram_webhook_deliveries_{column}"),
            "instagram_webhook_deliveries",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_instagram_deliveries_tenant_store_received",
        "instagram_webhook_deliveries",
        ["tenant_id", "store_id", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_deliveries_connection_received",
        "instagram_webhook_deliveries",
        ["instagram_connection_id", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_deliveries_status_received",
        "instagram_webhook_deliveries",
        ["processing_status", "received_at"],
        unique=False,
    )

    op.create_table(
        "instagram_inbound_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("instagram_connection_id", sa.Integer(), nullable=False),
        sa.Column("webhook_delivery_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_event_id", sa.String(length=200), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("external_object_id", sa.String(length=200), nullable=True),
        sa.Column("external_sender_id", sa.String(length=200), nullable=True),
        sa.Column("external_recipient_id", sa.String(length=200), nullable=True),
        sa.Column("provider_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('messaging', 'comments', 'unsupported')",
            name="ck_instagram_events_type",
        ),
        sa.CheckConstraint(
            "processing_status IN ('ready', 'ignored', 'failed')",
            name="ck_instagram_events_status",
        ),
        sa.CheckConstraint("provider = 'meta'", name="ck_instagram_events_provider"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["instagram_connection_id", "tenant_id", "store_id"],
            [
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ],
            name="fk_instagram_events_connection_scope",
        ),
        sa.ForeignKeyConstraint(
            ["webhook_delivery_id", "tenant_id", "store_id"],
            [
                "instagram_webhook_deliveries.id",
                "instagram_webhook_deliveries.tenant_id",
                "instagram_webhook_deliveries.store_id",
            ],
            name="fk_instagram_events_delivery_scope",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "idempotency_key",
            name="uq_instagram_events_idempotency",
        ),
    )
    op.create_index(
        op.f("ix_instagram_inbound_events_public_id"),
        "instagram_inbound_events",
        ["public_id"],
        unique=True,
    )
    for column in (
        "tenant_id",
        "store_id",
        "instagram_connection_id",
        "webhook_delivery_id",
        "provider_event_id",
        "event_type",
        "processing_status",
    ):
        op.create_index(
            op.f(f"ix_instagram_inbound_events_{column}"),
            "instagram_inbound_events",
            [column],
            unique=False,
        )
    op.create_index(
        "ix_instagram_events_tenant_store_received",
        "instagram_inbound_events",
        ["tenant_id", "store_id", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_events_connection_received",
        "instagram_inbound_events",
        ["instagram_connection_id", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_events_type_occurred",
        "instagram_inbound_events",
        ["event_type", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("instagram_inbound_events")
    op.drop_table("instagram_webhook_deliveries")
    op.drop_table("instagram_connections")
