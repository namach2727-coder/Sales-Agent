"""Tenant/store-scoped Google Search Console OAuth persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, JSON,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import new_public_id, utc_now


class SeoGoogleOAuthState(Base):
    __tablename__ = "seo_google_oauth_states"
    __table_args__ = (
        UniqueConstraint("state_digest", name="uq_seo_google_oauth_state_digest"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"), ("stores.id", "stores.tenant_id"),
            name="fk_seo_google_oauth_state_store_tenant",
        ),
        Index("ix_seo_google_oauth_state_scope", "tenant_id", "store_id", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    state_digest: Mapped[str] = mapped_column(String(64), unique=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    initiated_by_user_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SeoGoogleConnection(Base):
    __tablename__ = "seo_google_connections"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", "store_id", name="uq_seo_google_connection_scope"),
        UniqueConstraint("store_id", name="uq_seo_google_connection_store"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"), ("stores.id", "stores.tenant_id"),
            name="fk_seo_google_connection_store_tenant",
        ),
        CheckConstraint(
            "status IN ('active', 'reauthorization_required', 'disconnected')",
            name="ck_seo_google_connection_status",
        ),
        Index("ix_seo_google_connection_tenant_store", "tenant_id", "store_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    google_subject: Mapped[str] = mapped_column(String(255), index=True)
    google_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    granted_scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    connected_by_user_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), index=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SeoSearchProperty(Base):
    __tablename__ = "seo_search_properties"
    __table_args__ = (
        UniqueConstraint("store_id", "property_uri", name="uq_seo_property_store_uri"),
        ForeignKeyConstraint(
            ("connection_id", "tenant_id", "store_id"),
            ("seo_google_connections.id", "seo_google_connections.tenant_id", "seo_google_connections.store_id"),
            name="fk_seo_property_connection_scope",
        ),
        CheckConstraint("permission_level IN ('siteOwner', 'siteFullUser', 'siteRestrictedUser', 'siteUnverifiedUser')",
                        name="ck_seo_property_permission"),
        Index("ix_seo_property_scope", "tenant_id", "store_id", "is_selected"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    connection_id: Mapped[int] = mapped_column(Integer, index=True)
    property_uri: Mapped[str] = mapped_column(String(2048))
    permission_level: Mapped[str] = mapped_column(String(32))
    is_selected: Mapped[bool] = mapped_column(default=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
