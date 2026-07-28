"""Persistence models for FOUNDATION-07 Business Profile and Knowledge."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
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


STATUS_CHECK = "status IN ('draft', 'published', 'archived')"
TIMESTAMP_STATE_CHECK = (
    "(status = 'draft' AND published_at IS NULL AND archived_at IS NULL) OR "
    "(status = 'published' AND published_at IS NOT NULL AND archived_at IS NULL) OR "
    "(status = 'archived' AND published_at IS NULL AND archived_at IS NOT NULL)"
)


class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_business_profiles_id_tenant"),
        UniqueConstraint("store_id", name="uq_business_profiles_store"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_business_profiles_store_tenant",
        ),
        CheckConstraint(STATUS_CHECK, name="ck_business_profiles_status"),
        CheckConstraint("revision >= 1", name="ck_business_profiles_revision"),
        CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_profiles_timestamp_state",
        ),
        Index(
            "ix_business_profiles_tenant_store_status",
            "tenant_id",
            "store_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    business_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    address_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_hours_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BusinessPolicy(Base):
    __tablename__ = "business_policies"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_business_policies_id_tenant"),
        UniqueConstraint(
            "store_id", "code", name="uq_business_policies_store_code"
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_business_policies_store_tenant",
        ),
        CheckConstraint(STATUS_CHECK, name="ck_business_policies_status"),
        CheckConstraint("revision >= 1", name="ck_business_policies_revision"),
        CheckConstraint("priority >= 0", name="ck_business_policies_priority"),
        CheckConstraint(
            "policy_type IN ('shipping', 'returns', 'refunds', 'payment', "
            "'warranty', 'service', 'privacy', 'custom')",
            name="ck_business_policies_policy_type",
        ),
        CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_policies_timestamp_state",
        ),
        Index(
            "ix_business_policies_tenant_store_status",
            "tenant_id",
            "store_id",
            "status",
        ),
        Index(
            "ix_business_policies_tenant_store_type",
            "tenant_id",
            "store_id",
            "policy_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(100))
    policy_type: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BusinessFAQ(Base):
    __tablename__ = "business_faqs"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_business_faqs_id_tenant"),
        UniqueConstraint(
            "store_id",
            "normalized_question",
            name="uq_business_faqs_store_question",
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_business_faqs_store_tenant",
        ),
        CheckConstraint(STATUS_CHECK, name="ck_business_faqs_status"),
        CheckConstraint("revision >= 1", name="ck_business_faqs_revision"),
        CheckConstraint("priority >= 0", name="ck_business_faqs_priority"),
        CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_faqs_timestamp_state",
        ),
        Index(
            "ix_business_faqs_tenant_store_status",
            "tenant_id",
            "store_id",
            "status",
        ),
        Index(
            "ix_business_faqs_tenant_store_question",
            "tenant_id",
            "store_id",
            "normalized_question",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    question: Mapped[str] = mapped_column(String(500))
    normalized_question: Mapped[str] = mapped_column(String(500))
    answer: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BusinessKnowledgeEntry(Base):
    __tablename__ = "business_knowledge_entries"
    __table_args__ = (
        UniqueConstraint(
            "id", "tenant_id", name="uq_business_knowledge_entries_id_tenant"
        ),
        UniqueConstraint(
            "store_id", "slug", name="uq_business_knowledge_entries_store_slug"
        ),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_business_knowledge_entries_store_tenant",
        ),
        CheckConstraint(
            STATUS_CHECK, name="ck_business_knowledge_entries_status"
        ),
        CheckConstraint(
            "revision >= 1", name="ck_business_knowledge_entries_revision"
        ),
        CheckConstraint(
            "priority >= 0", name="ck_business_knowledge_entries_priority"
        ),
        CheckConstraint(
            "entry_type IN ('fact', 'instruction', 'reference', 'custom')",
            name="ck_business_knowledge_entries_entry_type",
        ),
        CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_knowledge_entries_timestamp_state",
        ),
        Index(
            "ix_business_knowledge_entries_tenant_store_status",
            "tenant_id",
            "store_id",
            "status",
        ),
        Index(
            "ix_business_knowledge_entries_tenant_store_type",
            "tenant_id",
            "store_id",
            "entry_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    slug: Mapped[str] = mapped_column(String(100))
    entry_type: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
