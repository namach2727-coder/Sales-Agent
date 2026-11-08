"""Store-scoped customer SEO grants, OAuth attempts and encrypted connections."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import new_public_id, utc_now


class SeoAccessGrant(Base):
    """Explicit internal pilot entitlement; no implicit Instagram access or price."""
    __tablename__ = "seo_access_grants"
    __table_args__ = (
        ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]),
        UniqueConstraint("tenant_id", "store_id", name="uq_seo_grant_scope"),
        CheckConstraint("max_sites BETWEEN 1 AND 20", name="ck_seo_grant_sites"),
        CheckConstraint("max_connections BETWEEN 1 AND 10", name="ck_seo_grant_connections"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_seo_grant_status"),
        CheckConstraint("revision >= 1", name="ck_seo_grant_revision"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    max_sites: Mapped[int] = mapped_column(default=1)
    max_connections: Mapped[int] = mapped_column(default=1)
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SeoOAuthAttempt(Base):
    __tablename__ = "seo_oauth_attempts"
    __table_args__ = (
        ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), index=True)
    state_digest: Mapped[str] = mapped_column(String(64), unique=True)
    session_digest: Mapped[str] = mapped_column(String(64))
    encrypted_verifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SeoGoogleConnection(Base):
    __tablename__ = "seo_google_connections"
    __table_args__ = (
        ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]),
        UniqueConstraint("tenant_id", "store_id", "user_id", name="uq_seo_connection_owner"),
        UniqueConstraint("id", "tenant_id", "store_id", name="uq_seo_connection_scope"),
        CheckConstraint("status IN ('connected', 'reauthorization_required', 'disconnected')", name="ck_seo_connection_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), index=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_version: Mapped[str] = mapped_column(String(30))
    granted_scope: Mapped[str] = mapped_column(Text)
    consent_version: Mapped[str] = mapped_column(String(30), default="seo-readonly-v1")
    status: Mapped[str] = mapped_column(String(30), default="connected")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SeoSite(Base):
    __tablename__ = "seo_sites"
    __table_args__ = (
        ForeignKeyConstraint(["connection_id", "tenant_id", "store_id"],
                             ["seo_google_connections.id", "seo_google_connections.tenant_id", "seo_google_connections.store_id"]),
        UniqueConstraint("tenant_id", "store_id", "property_id", name="uq_seo_site_property"),
        UniqueConstraint("id", "tenant_id", "store_id", name="uq_seo_sites_id_tenant_store"),
        CheckConstraint("status IN ('connected', 'disconnected', 'permission_lost')", name="ck_seo_site_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    tenant_id: Mapped[int] = mapped_column(index=True)
    store_id: Mapped[int] = mapped_column(index=True)
    connection_id: Mapped[int] = mapped_column(index=True)
    property_id: Mapped[str] = mapped_column(String(2048))
    permission_level: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="connected")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)



class SeoCrawlAuditEvent(Base):
    """Credential-free, time-bounded evidence for one crawler decision or request."""
    __tablename__ = "seo_crawl_audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        CheckConstraint(
            "event_kind IN ('robots', 'page')",
            name="ck_seo_crawl_audit_event_kind",
        ),
        CheckConstraint(
            "outcome IN ('allowed', 'blocked', 'fetched', 'failed', 'redirected')",
            name="ck_seo_crawl_audit_outcome",
        ),
        CheckConstraint(
            "robots_decision IN ('allow', 'disallow', 'unavailable_allow', 'unavailable_block', 'not_checked')",
            name="ck_seo_crawl_audit_robots_decision",
        ),
        CheckConstraint("http_status IS NULL OR http_status BETWEEN 100 AND 599",
                        name="ck_seo_crawl_audit_http_status"),
        CheckConstraint("bytes_received >= 0", name="ck_seo_crawl_audit_bytes"),
        CheckConstraint("duration_ms >= 0", name="ck_seo_crawl_audit_duration"),
        Index("ix_seo_crawl_audit_crawl_id", "crawl_id"),
        Index("ix_seo_crawl_audit_site_created",
              "tenant_id", "store_id", "site_id", "created_at"),
        Index("ix_seo_crawl_audit_expiry", "expires_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(nullable=False)
    site_id: Mapped[int] = mapped_column(nullable=False)
    crawl_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    robots_decision: Mapped[str] = mapped_column(String(24), nullable=False, default="not_checked", server_default="not_checked")
    url_host: Mapped[str] = mapped_column(String(253), nullable=False)
    url_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    http_status: Mapped[int | None] = mapped_column(nullable=True)
    bytes_received: Mapped[int] = mapped_column(default=0, nullable=False, server_default="0")
    duration_ms: Mapped[int] = mapped_column(default=0, nullable=False, server_default="0")
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
