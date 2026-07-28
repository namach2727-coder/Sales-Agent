"""Persistence models for the FOUNDATION-06 lean business catalog.

The `catalog_*` names deliberately coexist with the pre-foundation demo tables.
They provide a tenant-safe aggregate without changing legacy sales behavior.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import new_public_id, utc_now


LIFECYCLE_CHECK = "status IN ('draft', 'active', 'inactive', 'archived')"


class BusinessOffering(Base):
    """Tenant-owned offering; physical, digital and service share one aggregate."""

    __tablename__ = "catalog_offerings"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_offerings_id_tenant"),
        UniqueConstraint("tenant_id", "slug", name="uq_catalog_offerings_tenant_slug"),
        ForeignKeyConstraint(
            ("brand_id", "tenant_id"),
            ("catalog_brands.id", "catalog_brands.tenant_id"),
            name="fk_catalog_offerings_brand_tenant",
        ),
        CheckConstraint(
            "product_type IN ('physical', 'digital', 'service')",
            name="ck_catalog_offerings_product_type",
        ),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_offerings_status"),
        Index("ix_catalog_offerings_tenant_status", "tenant_id", "status"),
        Index("ix_catalog_offerings_tenant_type", "tenant_id", "product_type"),
        Index("ix_catalog_offerings_tenant_brand", "tenant_id", "brand_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    brand_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Variant(Base):
    __tablename__ = "catalog_variants"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_variants_id_tenant"),
        UniqueConstraint("product_id", "combination_key", name="uq_catalog_variant_combination"),
        ForeignKeyConstraint(
            ("product_id", "tenant_id"),
            ("catalog_offerings.id", "catalog_offerings.tenant_id"),
            name="fk_catalog_variants_product_tenant",
        ),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_variants_status"),
        Index("ix_catalog_variants_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    combination_key: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SKU(Base):
    __tablename__ = "catalog_skus"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_skus_id_tenant"),
        UniqueConstraint("tenant_id", "code", name="uq_catalog_skus_tenant_code"),
        UniqueConstraint("tenant_id", "barcode", name="uq_catalog_skus_tenant_barcode"),
        ForeignKeyConstraint(
            ("variant_id", "tenant_id"),
            ("catalog_variants.id", "catalog_variants.tenant_id"),
            name="fk_catalog_skus_variant_tenant",
        ),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_skus_status"),
        Index("ix_catalog_skus_tenant_variant", "tenant_id", "variant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    variant_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Attribute(Base):
    __tablename__ = "catalog_attributes"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_attributes_id_tenant"),
        UniqueConstraint("tenant_id", "code", name="uq_catalog_attributes_tenant_code"),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_attributes_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AttributeOption(Base):
    __tablename__ = "catalog_attribute_options"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_attribute_options_id_tenant"),
        UniqueConstraint(
            "attribute_id", "normalized_value", name="uq_catalog_attribute_option_value"
        ),
        ForeignKeyConstraint(
            ("attribute_id", "tenant_id"),
            ("catalog_attributes.id", "catalog_attributes.tenant_id"),
            name="fk_catalog_attribute_options_attribute_tenant",
        ),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_attribute_options_status"),
        Index("ix_catalog_attribute_options_tenant_attribute", "tenant_id", "attribute_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    attribute_id: Mapped[int] = mapped_column(Integer, index=True)
    value: Mapped[str] = mapped_column(String(200))
    normalized_value: Mapped[str] = mapped_column(String(200))
    display_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductAttribute(Base):
    __tablename__ = "catalog_product_attributes"
    __table_args__ = (
        UniqueConstraint("product_id", "attribute_id", name="uq_catalog_product_attribute"),
        ForeignKeyConstraint(
            ("product_id", "tenant_id"),
            ("catalog_offerings.id", "catalog_offerings.tenant_id"),
            name="fk_catalog_product_attributes_product_tenant",
        ),
        ForeignKeyConstraint(
            ("attribute_id", "tenant_id"),
            ("catalog_attributes.id", "catalog_attributes.tenant_id"),
            name="fk_catalog_product_attributes_attribute_tenant",
        ),
        Index("ix_catalog_product_attributes_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    attribute_id: Mapped[int] = mapped_column(Integer, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_variant_defining: Mapped[bool] = mapped_column(Boolean, default=False)


class VariantOptionValue(Base):
    __tablename__ = "catalog_variant_option_values"
    __table_args__ = (
        UniqueConstraint("variant_id", "attribute_id", name="uq_catalog_variant_attribute"),
        UniqueConstraint(
            "variant_id", "attribute_option_id", name="uq_catalog_variant_option"
        ),
        ForeignKeyConstraint(
            ("variant_id", "tenant_id"),
            ("catalog_variants.id", "catalog_variants.tenant_id"),
            name="fk_catalog_variant_options_variant_tenant",
        ),
        ForeignKeyConstraint(
            ("attribute_id", "tenant_id"),
            ("catalog_attributes.id", "catalog_attributes.tenant_id"),
            name="fk_catalog_variant_options_attribute_tenant",
        ),
        ForeignKeyConstraint(
            ("attribute_option_id", "tenant_id"),
            ("catalog_attribute_options.id", "catalog_attribute_options.tenant_id"),
            name="fk_catalog_variant_options_option_tenant",
        ),
        Index("ix_catalog_variant_options_tenant_variant", "tenant_id", "variant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    variant_id: Mapped[int] = mapped_column(Integer, index=True)
    attribute_id: Mapped[int] = mapped_column(Integer, index=True)
    attribute_option_id: Mapped[int] = mapped_column(Integer, index=True)


class Category(Base):
    __tablename__ = "catalog_categories"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_categories_id_tenant"),
        UniqueConstraint("tenant_id", "slug", name="uq_catalog_categories_tenant_slug"),
        ForeignKeyConstraint(
            ("parent_id", "tenant_id"),
            ("catalog_categories.id", "catalog_categories.tenant_id"),
            name="fk_catalog_categories_parent_tenant",
        ),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_categories_status"),
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_catalog_category_not_self"),
        Index("ix_catalog_categories_tenant_parent", "tenant_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OfferingCategoryAssignment(Base):
    __tablename__ = "catalog_product_categories"
    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_catalog_product_category"),
        ForeignKeyConstraint(
            ("product_id", "tenant_id"),
            ("catalog_offerings.id", "catalog_offerings.tenant_id"),
            name="fk_catalog_product_categories_product_tenant",
        ),
        ForeignKeyConstraint(
            ("category_id", "tenant_id"),
            ("catalog_categories.id", "catalog_categories.tenant_id"),
            name="fk_catalog_product_categories_category_tenant",
        ),
        Index("ix_catalog_product_categories_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    category_id: Mapped[int] = mapped_column(Integer, index=True)


class Brand(Base):
    __tablename__ = "catalog_brands"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_brands_id_tenant"),
        UniqueConstraint("tenant_id", "slug", name="uq_catalog_brands_tenant_slug"),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_brands_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Tag(Base):
    __tablename__ = "catalog_tags"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_tags_id_tenant"),
        UniqueConstraint("tenant_id", "slug", name="uq_catalog_tags_tenant_slug"),
        CheckConstraint(LIFECYCLE_CHECK, name="ck_catalog_tags_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductTag(Base):
    __tablename__ = "catalog_product_tags"
    __table_args__ = (
        UniqueConstraint("product_id", "tag_id", name="uq_catalog_product_tag"),
        ForeignKeyConstraint(
            ("product_id", "tenant_id"),
            ("catalog_offerings.id", "catalog_offerings.tenant_id"),
            name="fk_catalog_product_tags_product_tenant",
        ),
        ForeignKeyConstraint(
            ("tag_id", "tenant_id"),
            ("catalog_tags.id", "catalog_tags.tenant_id"),
            name="fk_catalog_product_tags_tag_tenant",
        ),
        Index("ix_catalog_product_tags_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    tag_id: Mapped[int] = mapped_column(Integer, index=True)


class MediaAsset(Base):
    __tablename__ = "catalog_media_assets"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_catalog_media_assets_id_tenant"),
        UniqueConstraint("tenant_id", "storage_provider", "storage_key", name="uq_catalog_media_storage_key"),
        CheckConstraint(
            "status IN ('pending', 'ready', 'failed', 'archived')",
            name="ck_catalog_media_assets_status",
        ),
        CheckConstraint("file_size >= 0", name="ck_catalog_media_assets_file_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    storage_provider: Mapped[str] = mapped_column(String(50))
    storage_key: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(150))
    file_size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductMedia(Base):
    __tablename__ = "catalog_product_media"
    __table_args__ = (
        UniqueConstraint("product_id", "media_asset_id", "role", name="uq_catalog_product_media"),
        ForeignKeyConstraint(
            ("product_id", "tenant_id"),
            ("catalog_offerings.id", "catalog_offerings.tenant_id"),
            name="fk_catalog_product_media_product_tenant",
        ),
        ForeignKeyConstraint(
            ("media_asset_id", "tenant_id"),
            ("catalog_media_assets.id", "catalog_media_assets.tenant_id"),
            name="fk_catalog_product_media_asset_tenant",
        ),
        Index(
            "ix_catalog_product_media_one_primary",
            "product_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    media_asset_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(50), default="gallery")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class VariantMedia(Base):
    __tablename__ = "catalog_variant_media"
    __table_args__ = (
        UniqueConstraint("variant_id", "media_asset_id", "role", name="uq_catalog_variant_media"),
        ForeignKeyConstraint(
            ("variant_id", "tenant_id"),
            ("catalog_variants.id", "catalog_variants.tenant_id"),
            name="fk_catalog_variant_media_variant_tenant",
        ),
        ForeignKeyConstraint(
            ("media_asset_id", "tenant_id"),
            ("catalog_media_assets.id", "catalog_media_assets.tenant_id"),
            name="fk_catalog_variant_media_asset_tenant",
        ),
        Index(
            "ix_catalog_variant_media_one_primary",
            "variant_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    variant_id: Mapped[int] = mapped_column(Integer, index=True)
    media_asset_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(50), default="gallery")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class SkuMedia(Base):
    __tablename__ = "catalog_sku_media"
    __table_args__ = (
        UniqueConstraint("sku_id", "media_asset_id", "role", name="uq_catalog_sku_media"),
        ForeignKeyConstraint(
            ("sku_id", "tenant_id"),
            ("catalog_skus.id", "catalog_skus.tenant_id"),
            name="fk_catalog_sku_media_sku_tenant",
        ),
        ForeignKeyConstraint(
            ("media_asset_id", "tenant_id"),
            ("catalog_media_assets.id", "catalog_media_assets.tenant_id"),
            name="fk_catalog_sku_media_asset_tenant",
        ),
        Index(
            "ix_catalog_sku_media_one_primary",
            "sku_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    sku_id: Mapped[int] = mapped_column(Integer, index=True)
    media_asset_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(50), default="gallery")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class BrandMedia(Base):
    __tablename__ = "catalog_brand_media"
    __table_args__ = (
        UniqueConstraint("brand_id", "media_asset_id", "role", name="uq_catalog_brand_media"),
        ForeignKeyConstraint(
            ("brand_id", "tenant_id"),
            ("catalog_brands.id", "catalog_brands.tenant_id"),
            name="fk_catalog_brand_media_brand_tenant",
        ),
        ForeignKeyConstraint(
            ("media_asset_id", "tenant_id"),
            ("catalog_media_assets.id", "catalog_media_assets.tenant_id"),
            name="fk_catalog_brand_media_asset_tenant",
        ),
        Index(
            "ix_catalog_brand_media_one_primary",
            "brand_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    brand_id: Mapped[int] = mapped_column(Integer, index=True)
    media_asset_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(50), default="gallery")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class CategoryMedia(Base):
    __tablename__ = "catalog_category_media"
    __table_args__ = (
        UniqueConstraint("category_id", "media_asset_id", "role", name="uq_catalog_category_media"),
        ForeignKeyConstraint(
            ("category_id", "tenant_id"),
            ("catalog_categories.id", "catalog_categories.tenant_id"),
            name="fk_catalog_category_media_category_tenant",
        ),
        ForeignKeyConstraint(
            ("media_asset_id", "tenant_id"),
            ("catalog_media_assets.id", "catalog_media_assets.tenant_id"),
            name="fk_catalog_category_media_asset_tenant",
        ),
        Index(
            "ix_catalog_category_media_one_primary",
            "category_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    category_id: Mapped[int] = mapped_column(Integer, index=True)
    media_asset_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(50), default="gallery")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class StorePrice(Base):
    __tablename__ = "catalog_store_prices"
    __table_args__ = (
        UniqueConstraint("store_id", "sku_id", "currency", name="uq_catalog_store_price"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_catalog_store_prices_store_tenant",
        ),
        ForeignKeyConstraint(
            ("sku_id", "tenant_id"),
            ("catalog_skus.id", "catalog_skus.tenant_id"),
            name="fk_catalog_store_prices_sku_tenant",
        ),
        CheckConstraint("price >= 0", name="ck_catalog_store_prices_price"),
        CheckConstraint(
            "compare_at_price IS NULL OR compare_at_price >= price",
            name="ck_catalog_store_prices_compare",
        ),
        Index("ix_catalog_store_prices_tenant_store", "tenant_id", "store_id"),
        Index("ix_catalog_store_prices_tenant_sku", "tenant_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    sku_id: Mapped[int] = mapped_column(Integer, index=True)
    currency: Mapped[str] = mapped_column(String(3))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class StoreAvailability(Base):
    __tablename__ = "catalog_store_availability"
    __table_args__ = (
        UniqueConstraint("store_id", "sku_id", name="uq_catalog_store_availability"),
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_catalog_store_availability_store_tenant",
        ),
        ForeignKeyConstraint(
            ("sku_id", "tenant_id"),
            ("catalog_skus.id", "catalog_skus.tenant_id"),
            name="fk_catalog_store_availability_sku_tenant",
        ),
        CheckConstraint(
            "availability_status IN ('in_stock', 'low_stock', 'out_of_stock', 'preorder', 'unavailable')",
            name="ck_catalog_store_availability_status",
        ),
        CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_catalog_store_availability_quantity"),
        CheckConstraint(
            "NOT (quantity = 0 AND availability_status = 'in_stock')",
            name="ck_catalog_store_availability_zero",
        ),
        Index("ix_catalog_store_availability_tenant_store", "tenant_id", "store_id"),
        Index("ix_catalog_store_availability_tenant_sku", "tenant_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), default=new_public_id, unique=True, index=True
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    sku_id: Mapped[int] = mapped_column(Integer, index=True)
    availability_status: Mapped[str] = mapped_column(String(20), index=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


# Public domain aliases keep the aggregate vocabulary concise without placing
# duplicate legacy class names in SQLAlchemy's declarative class registry.
Product = BusinessOffering
ProductCategory = OfferingCategoryAssignment
