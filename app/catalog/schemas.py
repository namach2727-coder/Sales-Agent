"""Public API schemas for the lean business catalog.

Tenant IDs and internal database identifiers are intentionally absent.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LifecycleStatus = Literal["draft", "active", "inactive", "archived"]
ProductType = Literal["physical", "digital", "service"]
AvailabilityStatus = Literal[
    "in_stock", "low_stock", "out_of_stock", "preorder", "unavailable"
]
MediaStatus = Literal["pending", "ready", "failed", "archived"]
MediaOwnerType = Literal["product", "variant", "sku", "brand", "category"]


class Page(BaseModel):
    page: int
    page_size: int
    total: int


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)
    product_type: ProductType
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    status: LifecycleStatus = "draft"
    is_featured: bool = False
    sku_code: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    product_type: ProductType | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    status: LifecycleStatus | None = None
    is_featured: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    description: str | None
    short_description: str | None
    product_type: ProductType
    status: LifecycleStatus
    brand_public_id: str | None = None
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class ProductPage(Page):
    items: list[ProductRead]


class BrandAssignment(BaseModel):
    brand_public_id: str | None = None


class AttributeAssignment(BaseModel):
    sort_order: int = 0
    is_variant_defining: bool = False


class VariantCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    status: LifecycleStatus = "draft"
    option_public_ids: list[str] = Field(default_factory=list, max_length=50)


class VariantUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    status: LifecycleStatus | None = None


class VariantOptionsUpdate(BaseModel):
    option_public_ids: list[str] = Field(default_factory=list, max_length=50)


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    product_public_id: str
    name: str | None
    combination_key: str
    status: LifecycleStatus
    option_public_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class VariantPage(Page):
    items: list[VariantRead]


class SkuCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    status: LifecycleStatus = "draft"


class SkuUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    status: LifecycleStatus | None = None


class SkuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    variant_public_id: str
    code: str
    barcode: str | None
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class SkuPage(Page):
    items: list[SkuRead]


class NamedReferenceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)
    status: LifecycleStatus = "active"


class NamedReferenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    status: LifecycleStatus | None = None


class BrandCreate(NamedReferenceCreate):
    description: str | None = None


class BrandUpdate(NamedReferenceUpdate):
    description: str | None = None


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    description: str | None
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class BrandPage(Page):
    items: list[BrandRead]


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class TagPage(Page):
    items: list[TagRead]


class CategoryCreate(NamedReferenceCreate):
    parent_public_id: str | None = None


class CategoryUpdate(NamedReferenceUpdate):
    parent_public_id: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    parent_public_id: str | None = None
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class CategoryPage(Page):
    items: list[CategoryRead]


class AttributeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=100)
    status: LifecycleStatus = "active"


class AttributeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    code: str | None = Field(default=None, min_length=1, max_length=100)
    status: LifecycleStatus | None = None


class AttributeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    code: str
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class AttributePage(Page):
    items: list[AttributeRead]


class AttributeOptionCreate(BaseModel):
    value: str = Field(min_length=1, max_length=200)
    display_label: str | None = Field(default=None, max_length=200)
    sort_order: int = 0
    status: LifecycleStatus = "active"


class AttributeOptionUpdate(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=200)
    display_label: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None
    status: LifecycleStatus | None = None


class AttributeOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    attribute_public_id: str
    value: str
    display_label: str | None
    sort_order: int
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class AttributeOptionPage(Page):
    items: list[AttributeOptionRead]


class MediaAssetCreate(BaseModel):
    storage_provider: str = Field(min_length=1, max_length=50)
    storage_key: str = Field(min_length=1, max_length=500)
    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=150)
    file_size: int = Field(ge=0)
    checksum: str | None = Field(default=None, max_length=128)
    status: MediaStatus = "pending"
    metadata: dict[str, object] = Field(default_factory=dict)


class MediaAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    storage_provider: str
    storage_key: str
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str | None
    status: MediaStatus
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class MediaAttach(BaseModel):
    media_public_id: str
    role: str = Field(default="gallery", min_length=1, max_length=50)
    sort_order: int = 0
    is_primary: bool = False


class MediaAssociationRead(BaseModel):
    media: MediaAssetRead
    role: str
    sort_order: int
    is_primary: bool


class MediaAssociationPage(Page):
    items: list[MediaAssociationRead]


class StorePriceUpsert(BaseModel):
    store_public_id: str
    sku_public_id: str
    currency: str = Field(min_length=3, max_length=3)
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True


class StorePriceRead(BaseModel):
    public_id: str
    store_public_id: str
    sku_public_id: str
    currency: str
    price: Decimal
    compare_at_price: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StorePricePage(Page):
    items: list[StorePriceRead]


class StoreAvailabilityUpsert(BaseModel):
    store_public_id: str
    sku_public_id: str
    availability_status: AvailabilityStatus
    quantity: int | None = Field(default=None, ge=0)


class StoreAvailabilityRead(BaseModel):
    public_id: str
    store_public_id: str
    sku_public_id: str
    availability_status: AvailabilityStatus
    quantity: int | None
    created_at: datetime
    updated_at: datetime


class StoreAvailabilityPage(Page):
    items: list[StoreAvailabilityRead]
