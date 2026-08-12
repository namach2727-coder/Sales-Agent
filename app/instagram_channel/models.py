"""Persistence models for FOUNDATION-08 Instagram Channel."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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


class InstagramConnection(Base):
    __tablename__ = "instagram_connections"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_instagram_connections_id_tenant_store",
        ),
        UniqueConstraint("store_id", name="uq_instagram_connections_store"),
        UniqueConstraint(
            "instagram_account_id",
            name="uq_instagram_connections_account",
        ),
        UniqueConstraint(
            "facebook_page_id",
            name="uq_instagram_connections_page",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_instagram_connections_store_tenant",
        ),
        CheckConstraint(
            "status IN ('pending', 'active', 'degraded', 'disconnected', "
            "'revoked', 'archived')",
            name="ck_instagram_connections_status",
        ),
        CheckConstraint("revision >= 1", name="ck_instagram_connections_revision"),
        CheckConstraint(
            "(status != 'archived' AND archived_at IS NULL) OR "
            "(status = 'archived' AND archived_at IS NOT NULL)",
            name="ck_instagram_connections_archived_state",
        ),
        Index(
            "ix_instagram_connections_tenant_store_status",
            "tenant_id",
            "store_id",
            "status",
        ),
        Index(
            "ix_instagram_connections_routing",
            "instagram_account_id",
            "facebook_page_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    meta_app_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    facebook_page_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    instagram_account_id: Mapped[str] = mapped_column(String(200), index=True)
    instagram_username: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    external_account_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    status_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disconnected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_webhook_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    token_scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    token_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class InstagramOAuthState(Base):
    """Single-use, tenant-bound OAuth correlation state.

    Only a SHA-256 digest is persisted. The browser-visible nonce is never
    recoverable from the database and no Meta credential is stored here.
    """

    __tablename__ = "instagram_oauth_states"
    __table_args__ = (
        UniqueConstraint("state_digest", name="uq_instagram_oauth_states_digest"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_instagram_oauth_states_store_tenant",
        ),
        Index(
            "ix_instagram_oauth_states_scope",
            "tenant_id",
            "store_id",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    state_digest: Mapped[str] = mapped_column(String(64), unique=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    initiated_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("user_identities.id"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class InstagramWebhookDelivery(Base):
    __tablename__ = "instagram_webhook_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_instagram_deliveries_id_tenant_store",
        ),
        UniqueConstraint(
            "provider",
            "external_delivery_key",
            name="uq_instagram_deliveries_external_key",
        ),
        UniqueConstraint(
            "provider",
            "payload_hash",
            name="uq_instagram_deliveries_payload_hash",
        ),
        ForeignKeyConstraint(
            ("instagram_connection_id", "tenant_id", "store_id"),
            (
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ),
            name="fk_instagram_deliveries_connection_scope",
        ),
        CheckConstraint("provider = 'meta'", name="ck_instagram_deliveries_provider"),
        CheckConstraint(
            "processing_status IN ('received', 'rejected', 'duplicate', "
            "'accepted', 'processed', 'failed', 'ignored')",
            name="ck_instagram_deliveries_status",
        ),
        CheckConstraint(
            "verification_state IN ('verified', 'unverified', 'invalid')",
            name="ck_instagram_deliveries_verification",
        ),
        CheckConstraint(
            "(tenant_id IS NULL AND store_id IS NULL AND "
            "instagram_connection_id IS NULL) OR "
            "(tenant_id IS NOT NULL AND store_id IS NOT NULL AND "
            "instagram_connection_id IS NOT NULL)",
            name="ck_instagram_deliveries_resolved_scope",
        ),
        CheckConstraint("retry_count >= 0", name="ck_instagram_deliveries_retries"),
        Index(
            "ix_instagram_deliveries_tenant_store_received",
            "tenant_id",
            "store_id",
            "received_at",
        ),
        Index(
            "ix_instagram_deliveries_connection_received",
            "instagram_connection_id",
            "received_at",
        ),
        Index(
            "ix_instagram_deliveries_status_received",
            "processing_status",
            "received_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), default="meta")
    external_delivery_key: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    payload_hash: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    signature_algorithm: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_state: Mapped[str] = mapped_column(
        String(20), default="unverified"
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), default="received", index=True
    )
    failure_category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    safe_failure_detail: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    correlation_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id"), nullable=True, index=True
    )
    store_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    instagram_connection_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )


class InstagramInboundEvent(Base):
    __tablename__ = "instagram_inbound_events"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "tenant_id",
            "store_id",
            name="uq_instagram_events_id_tenant_store",
        ),
        UniqueConstraint(
            "provider",
            "idempotency_key",
            name="uq_instagram_events_idempotency",
        ),
        ForeignKeyConstraint(
            ("instagram_connection_id", "tenant_id", "store_id"),
            (
                "instagram_connections.id",
                "instagram_connections.tenant_id",
                "instagram_connections.store_id",
            ),
            name="fk_instagram_events_connection_scope",
        ),
        ForeignKeyConstraint(
            ("webhook_delivery_id", "tenant_id", "store_id"),
            (
                "instagram_webhook_deliveries.id",
                "instagram_webhook_deliveries.tenant_id",
                "instagram_webhook_deliveries.store_id",
            ),
            name="fk_instagram_events_delivery_scope",
        ),
        CheckConstraint("provider = 'meta'", name="ck_instagram_events_provider"),
        CheckConstraint(
            "event_type IN ('messaging', 'comments', 'unsupported')",
            name="ck_instagram_events_type",
        ),
        CheckConstraint(
            "processing_status IN ('ready', 'ignored', 'failed')",
            name="ck_instagram_events_status",
        ),
        Index(
            "ix_instagram_events_tenant_store_received",
            "tenant_id",
            "store_id",
            "received_at",
        ),
        Index(
            "ix_instagram_events_connection_received",
            "instagram_connection_id",
            "received_at",
        ),
        Index(
            "ix_instagram_events_type_occurred",
            "event_type",
            "occurred_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    instagram_connection_id: Mapped[int] = mapped_column(Integer, index=True)
    webhook_delivery_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="meta")
    provider_event_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    object_type: Mapped[str] = mapped_column(String(100))
    external_object_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    external_sender_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    external_recipient_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    provider_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    normalized_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    processing_status: Mapped[str] = mapped_column(
        String(20), default="ready", index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
