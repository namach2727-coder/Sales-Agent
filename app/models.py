from datetime import UTC, datetime
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_public_id() -> str:
    return str(uuid.uuid4())


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String(500), unique=True)
    answer: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    instagram_user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30), default="instagram")
    user_message: Mapped[str] = mapped_column(Text)
    assistant_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_human: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    customer: Mapped[Customer] = relationship(back_populates="conversations")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    customer: Mapped[Customer] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship()


class InstagramEvent(Base):
    __tablename__ = "instagram_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sender_id: Mapped[str] = mapped_column(String(100), index=True)
    recipient_id: Mapped[str] = mapped_column(String(100))
    message_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InstagramMediaProduct(Base):
    __tablename__ = "instagram_media_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    media_product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    permalink: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    product: Mapped[Product] = relationship()


class InstagramCommentEvent(Base):
    __tablename__ = "instagram_comment_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ig_account_id: Mapped[str] = mapped_column(String(100), index=True)
    media_id: Mapped[str] = mapped_column(String(100), index=True)
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text)
    media_product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InstagramCommentPublicReply(Base):
    __tablename__ = "instagram_comment_public_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    reply_text: Mapped[str] = mapped_column(Text)
    reply_comment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="processing", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TelegramEvent(Base):
    __tablename__ = "telegram_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    update_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    chat_id: Mapped[str] = mapped_column(String(100), index=True)
    sender_id: Mapped[str] = mapped_column(String(100), index=True)
    message_id: Mapped[str] = mapped_column(String(100))
    message_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ManyChatEvent(Base):
    __tablename__ = "manychat_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    page_id: Mapped[str] = mapped_column(String(40), index=True)
    contact_id: Mapped[str] = mapped_column(String(40), index=True)
    last_interaction: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    message_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="processing", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Tenant(Base):
    """Top-level customer boundary. Business data is never hard-deleted."""

    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'archived')",
            name="ck_tenants_status",
        ),
        Index("ix_tenants_slug_lower", "slug", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(63))
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_by_identity_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stores: Mapped[list["Store"]] = relationship(back_populates="tenant")
    memberships: Mapped[list["TenantMembership"]] = relationship(back_populates="tenant")


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_stores_id_tenant"),
        UniqueConstraint("tenant_id", "slug", name="uq_stores_tenant_slug"),
        UniqueConstraint("subdomain", name="uq_stores_subdomain"),
        UniqueConstraint("custom_domain", name="uq_stores_custom_domain"),
        CheckConstraint(
            "status IN ('active', 'suspended', 'archived', 'onboarding', 'provisioning', 'disabled', 'deleted')",
            name="ck_stores_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(63), index=True)
    status: Mapped[str] = mapped_column(String(20), default="onboarding", index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tehran")
    locale: Mapped[str] = mapped_column(String(16), default="fa-IR")
    currency_code: Mapped[str] = mapped_column(String(3), default="IRR")
    subdomain: Mapped[str | None] = mapped_column(String(63), nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant: Mapped[Tenant] = relationship(back_populates="stores")
    drafts: Mapped[list["TrainingDraft"]] = relationship(back_populates="store")
    versions: Mapped[list["KnowledgeVersion"]] = relationship(back_populates="store")
    audit_logs: Mapped[list["AdminAuditLog"]] = relationship(back_populates="store")
    modules: Mapped[list["StoreModule"]] = relationship(back_populates="store")

    def __init__(self, **kwargs: object) -> None:
        # Compatibility for legacy development/tests that created a Store as
        # the tenant root. Production services always pass an explicit tenant.
        if "tenant" not in kwargs and "tenant_id" not in kwargs:
            legacy_status = str(kwargs.get("status", "active"))
            tenant_status = (
                "archived" if legacy_status in {"deleted", "archived"}
                else "suspended" if legacy_status in {"disabled", "suspended"}
                else "active"
            )
            kwargs["tenant"] = Tenant(
                name=str(kwargs.get("name", "Store")),
                slug=str(kwargs.get("slug", new_public_id())).strip().lower(),
                status=tenant_status,
            )
        super().__init__(**kwargs)


class TrainingDraft(Base):
    __tablename__ = "training_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(20), default="manual")
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="uploaded", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    store: Mapped[Store] = relationship(back_populates="drafts")
    published_version: Mapped["KnowledgeVersion | None"] = relationship(
        back_populates="source_draft", uselist=False
    )


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "version_number", name="uq_knowledge_versions_store_version"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    source_draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("training_drafts.id"), unique=True, nullable=True
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    store: Mapped[Store] = relationship(back_populates="versions")
    source_draft: Mapped[TrainingDraft | None] = relationship(
        back_populates="published_version"
    )
    categories: Mapped[list["ProductCategory"]] = relationship(back_populates="version")
    catalog_products: Mapped[list["CatalogProduct"]] = relationship(
        back_populates="version"
    )
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(
        back_populates="version"
    )


class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_version_id",
            "normalized_name",
            name="uq_product_categories_version_normalized_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_version_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_versions.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[KnowledgeVersion] = relationship(back_populates="categories")
    catalog_products: Mapped[list["CatalogProduct"]] = relationship(
        back_populates="category"
    )


class CatalogProduct(Base):
    __tablename__ = "catalog_products"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_version_id",
            "external_key",
            name="uq_catalog_products_version_external_key",
        ),
        UniqueConstraint(
            "knowledge_version_id",
            "product_id",
            name="uq_catalog_products_version_product",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_version_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_versions.id"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_categories.id"), nullable=True, index=True
    )
    external_key: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[KnowledgeVersion] = relationship(back_populates="catalog_products")
    product: Mapped[Product] = relationship()
    category: Mapped[ProductCategory | None] = relationship(
        back_populates="catalog_products"
    )
    aliases: Mapped[list["ProductAlias"]] = relationship(
        back_populates="catalog_product"
    )


class ProductAlias(Base):
    __tablename__ = "product_aliases"
    __table_args__ = (
        UniqueConstraint(
            "catalog_product_id",
            "normalized_value",
            name="uq_product_aliases_product_normalized",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_product_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_products.id"), index=True
    )
    value: Mapped[str] = mapped_column(String(200))
    normalized_value: Mapped[str] = mapped_column(String(200), index=True)
    kind: Mapped[str] = mapped_column(String(30), default="generated")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    catalog_product: Mapped[CatalogProduct] = relationship(back_populates="aliases")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_version_id",
            "kind",
            "title",
            name="uq_knowledge_items_version_kind_title",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_version_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_versions.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    normalized_title: Mapped[str] = mapped_column(String(500))
    answer: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    version: Mapped[KnowledgeVersion] = relationship(back_populates="knowledge_items")


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    store: Mapped[Store] = relationship(back_populates="audit_logs")


class ProductMediaAsset(Base):
    """A private, manager-uploaded product image.

    The opaque ID is safe to expose in the local admin UI. ``storage_key`` is
    generated by the server and never derived from the original filename.
    """

    __tablename__ = "product_media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), default="image/jpeg")
    byte_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="ready", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    product: Mapped[Product] = relationship()


class SocialContentDraft(Base):
    """Manager-reviewed social copy for one product image."""

    __tablename__ = "social_content_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    media_asset_id: Mapped[str] = mapped_column(
        ForeignKey("product_media_assets.id"), index=True
    )
    caption: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    alt_text: Mapped[str] = mapped_column(String(1000), default="")
    sales_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    product: Mapped[Product] = relationship()
    media_asset: Mapped[ProductMediaAsset] = relationship()


class InstagramPublishJob(Base):
    """Idempotent record of the two-step Instagram publishing operation."""

    __tablename__ = "instagram_publish_jobs"
    __table_args__ = (
        UniqueConstraint("content_draft_id", name="uq_instagram_publish_job_draft"),
        UniqueConstraint("idempotency_key", name="uq_instagram_publish_job_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    content_draft_id: Mapped[int] = mapped_column(
        ForeignKey("social_content_drafts.id"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    meta_container_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_media_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    permalink: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    content_draft: Mapped[SocialContentDraft] = relationship()


class ModuleDefinition(Base):
    """Provider-owned sellable capability and its default pricing."""

    __tablename__ = "module_definitions"

    code: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    short_description: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50), default="sales", index=True)
    monthly_price: Mapped[int] = mapped_column(Integer, default=0)
    setup_price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="IRR")
    dependencies: Mapped[list[str]] = mapped_column(JSON, default=list)
    default_limits: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    availability: Mapped[str] = mapped_column(String(20), default="ready", index=True)
    is_sellable: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    store_modules: Mapped[list["StoreModule"]] = relationship(
        back_populates="module"
    )


class StoreModule(Base):
    """One store's entitlement to a separately priced module."""

    __tablename__ = "store_modules"
    __table_args__ = (
        UniqueConstraint("store_id", "module_code", name="uq_store_module"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    module_code: Mapped[str] = mapped_column(
        ForeignKey("module_definitions.code"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="inactive", index=True)
    custom_monthly_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="IRR")
    billing_interval: Mapped[str] = mapped_column(String(20), default="month")
    limits_json: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    store: Mapped[Store] = relationship(back_populates="modules")
    module: Mapped[ModuleDefinition] = relationship(back_populates="store_modules")


class StoreInstagramConnection(Base):
    """Maps a Meta professional account to its tenant without exposing tokens."""

    __tablename__ = "store_instagram_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"), unique=True, index=True
    )
    ig_user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    token_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_key_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    store: Mapped[Store] = relationship()


class SeedHistory(Base):
    """Credential-free audit record for one explicit seed execution."""

    __tablename__ = "seed_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    seed_name: Mapped[str] = mapped_column(String(100), index=True)
    seed_version: Mapped[str] = mapped_column(String(50))
    profile: Mapped[str] = mapped_column(String(20))
    scope: Mapped[str] = mapped_column(String(20))
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), index=True)
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuthPermission(Base):
    """Stable, system-seeded authorization capability."""

    __tablename__ = "auth_permissions"

    code: Mapped[str] = mapped_column(String(100), primary_key=True)
    scope: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(String(500))
    system_managed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AuthRole(Base):
    """Role definition; assignments are stored separately by scope."""

    __tablename__ = "auth_roles"

    code: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200))
    scope: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    system_managed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AuthRolePermission(Base):
    __tablename__ = "auth_role_permissions"
    __table_args__ = (
        UniqueConstraint("role_code", "permission_code", name="uq_auth_role_permission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    role_code: Mapped[str] = mapped_column(
        ForeignKey("auth_roles.code"), index=True
    )
    permission_code: Mapped[str] = mapped_column(
        ForeignKey("auth_permissions.code"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TenantMembership(Base):
    """Explicit principal membership in exactly one tenant."""

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "principal_type",
            "principal_id",
            name="uq_tenant_membership_principal",
        ),
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership_user"),
        CheckConstraint(
            "status IN ('invited', 'active', 'suspended', 'revoked', 'disabled')",
            name="ck_tenant_memberships_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    principal_type: Mapped[str] = mapped_column(String(30))
    principal_id: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    all_store_access: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    store_access: Mapped[list["StoreAccessAssignment"]] = relationship(
        back_populates="membership"
    )


class StoreAccessAssignment(Base):
    """Explicit store access layered on top of tenant RBAC roles."""

    __tablename__ = "store_access_assignments"
    __table_args__ = (
        UniqueConstraint("membership_id", "store_id", name="uq_store_access_membership_store"),
        CheckConstraint(
            "status IN ('active', 'suspended', 'revoked')",
            name="ck_store_access_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("tenant_memberships.id"), index=True
    )
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_by_identity_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    membership: Mapped[TenantMembership] = relationship(back_populates="store_access")
    store: Mapped[Store] = relationship()


class TenantAuditLog(Base):
    """Credential-free lifecycle and access audit for tenants and stores."""

    __tablename__ = "tenant_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int | None] = mapped_column(
        ForeignKey("stores.id"), nullable=True, index=True
    )
    actor_identity_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(50))
    target_public_id: Mapped[str] = mapped_column(String(100))
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class UserIdentity(Base):
    """Persistent login identity; hashes are never serialized by API schemas."""

    __tablename__ = "user_identities"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'disabled')", name="ck_user_identities_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    normalized_email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    is_service_account: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AuthSession(Base):
    """Revocable opaque session. Only a one-way token digest is persisted."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'revoked', 'expired')",
            name="ck_auth_sessions_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class IdentityAuditLog(Base):
    """Sanitized security event without credentials or request payloads."""

    __tablename__ = "identity_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_code: Mapped[str] = mapped_column(String(100), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True, index=True
    )
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_identities.id"), nullable=True, index=True
    )
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("auth_sessions.id"), nullable=True, index=True
    )
    outcome: Mapped[str] = mapped_column(String(20), default="succeeded")
    reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class AuthPlatformRoleAssignment(Base):
    __tablename__ = "auth_platform_role_assignments"
    __table_args__ = (
        UniqueConstraint(
            "principal_type",
            "principal_id",
            "role_code",
            name="uq_auth_platform_principal_role",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    principal_type: Mapped[str] = mapped_column(String(30))
    principal_id: Mapped[str] = mapped_column(String(200), index=True)
    role_code: Mapped[str] = mapped_column(ForeignKey("auth_roles.code"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AuthTenantRoleAssignment(Base):
    __tablename__ = "auth_tenant_role_assignments"
    __table_args__ = (
        UniqueConstraint("membership_id", "role_code", name="uq_auth_tenant_membership_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("tenant_memberships.id"), index=True
    )
    role_code: Mapped[str] = mapped_column(ForeignKey("auth_roles.code"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AuthAuditLog(Base):
    """Credential-free audit for access configuration mutations."""

    __tablename__ = "auth_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id"), nullable=True, index=True
    )
    actor_principal_type: Mapped[str] = mapped_column(String(30))
    actor_principal_id: Mapped[str] = mapped_column(String(200), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_principal_type: Mapped[str] = mapped_column(String(30))
    target_principal_id: Mapped[str] = mapped_column(String(200))
    target_role_code: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(20), default="succeeded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


# Register FOUNDATION-06 catalog tables with the shared SQLAlchemy metadata.
# The import is intentionally last so the legacy models above remain available
# while the new modular catalog references Tenant and Store by table name.
from app.catalog import models as catalog_models  # noqa: E402,F401
