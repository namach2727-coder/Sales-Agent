"""Read-only, tenant-safe snapshot queries for the Knowledge Engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.business_knowledge.models import (
    BusinessFAQ,
    BusinessKnowledgeEntry,
    BusinessPolicy,
    BusinessProfile,
)
from app.catalog.models import (
    Attribute,
    AttributeOption,
    Product,
    SKU,
    StoreAvailability,
    StorePrice,
    Variant,
    VariantOptionValue,
)
from app.models import Store, Tenant


@dataclass(frozen=True, slots=True)
class KnowledgeScope:
    tenant_id: int
    store_id: int
    currency_code: str


@dataclass(frozen=True, slots=True)
class CatalogPriceSnapshot:
    currency: str
    price: Decimal
    compare_at_price: Decimal | None


@dataclass(frozen=True, slots=True)
class CatalogAvailabilitySnapshot:
    status: str
    quantity: int | None


@dataclass(frozen=True, slots=True)
class CatalogOptionSnapshot:
    attribute_public_id: str
    attribute_code: str
    attribute_name: str
    option_public_id: str
    value: str
    display_label: str | None


@dataclass(frozen=True, slots=True)
class CatalogSkuSnapshot:
    public_id: str
    code: str
    barcode: str | None
    price: CatalogPriceSnapshot | None
    availability: CatalogAvailabilitySnapshot | None


@dataclass(frozen=True, slots=True)
class CatalogVariantSnapshot:
    public_id: str
    name: str | None
    options: tuple[CatalogOptionSnapshot, ...]
    skus: tuple[CatalogSkuSnapshot, ...]


@dataclass(frozen=True, slots=True)
class CatalogProductSnapshot:
    public_id: str
    name: str
    description: str | None
    short_description: str | None
    product_type: str
    variants: tuple[CatalogVariantSnapshot, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    products: tuple[CatalogProductSnapshot, ...]
    profile: BusinessProfile | None
    faqs: tuple[BusinessFAQ, ...]
    policies: tuple[BusinessPolicy, ...]
    entries: tuple[BusinessKnowledgeEntry, ...]


class KnowledgeRepository:
    """Load one active store's published business and catalog snapshot."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def resolve_active_scope(
        self,
        *,
        tenant_public_id: str,
        store_public_id: str,
    ) -> KnowledgeScope | None:
        row = self.session.execute(
            select(Tenant.id, Store.id, Store.currency_code)
            .join(
                Store,
                and_(
                    Store.tenant_id == Tenant.id,
                    Store.public_id == store_public_id,
                    Store.status == "active",
                ),
            )
            .where(
                Tenant.public_id == tenant_public_id,
                Tenant.status == "active",
            )
        ).one_or_none()
        if row is None:
            return None
        return KnowledgeScope(
            tenant_id=row[0],
            store_id=row[1],
            currency_code=row[2],
        )

    def load_snapshot(self, scope: KnowledgeScope) -> KnowledgeSnapshot:
        return KnowledgeSnapshot(
            products=self._catalog(scope),
            profile=self.session.scalar(
                select(BusinessProfile).where(
                    BusinessProfile.tenant_id == scope.tenant_id,
                    BusinessProfile.store_id == scope.store_id,
                    BusinessProfile.status == "published",
                )
            ),
            faqs=tuple(
                self.session.scalars(
                    select(BusinessFAQ)
                    .where(
                        BusinessFAQ.tenant_id == scope.tenant_id,
                        BusinessFAQ.store_id == scope.store_id,
                        BusinessFAQ.status == "published",
                    )
                    .order_by(BusinessFAQ.priority, BusinessFAQ.public_id)
                ).all()
            ),
            policies=tuple(
                self.session.scalars(
                    select(BusinessPolicy)
                    .where(
                        BusinessPolicy.tenant_id == scope.tenant_id,
                        BusinessPolicy.store_id == scope.store_id,
                        BusinessPolicy.status == "published",
                    )
                    .order_by(
                        BusinessPolicy.priority,
                        BusinessPolicy.public_id,
                    )
                ).all()
            ),
            entries=tuple(
                self.session.scalars(
                    select(BusinessKnowledgeEntry)
                    .where(
                        BusinessKnowledgeEntry.tenant_id == scope.tenant_id,
                        BusinessKnowledgeEntry.store_id == scope.store_id,
                        BusinessKnowledgeEntry.status == "published",
                    )
                    .order_by(
                        BusinessKnowledgeEntry.priority,
                        BusinessKnowledgeEntry.public_id,
                    )
                ).all()
            ),
        )

    def _catalog(
        self,
        scope: KnowledgeScope,
    ) -> tuple[CatalogProductSnapshot, ...]:
        products = list(
            self.session.scalars(
                select(Product)
                .where(
                    Product.tenant_id == scope.tenant_id,
                    Product.status == "active",
                )
                .order_by(Product.name, Product.public_id)
            ).all()
        )
        if not products:
            return ()
        product_ids = [item.id for item in products]
        variants = list(
            self.session.scalars(
                select(Variant)
                .where(
                    Variant.tenant_id == scope.tenant_id,
                    Variant.product_id.in_(product_ids),
                    Variant.status == "active",
                )
                .order_by(Variant.product_id, Variant.public_id)
            ).all()
        )
        variant_ids = [item.id for item in variants]
        skus = (
            list(
                self.session.scalars(
                    select(SKU)
                    .where(
                        SKU.tenant_id == scope.tenant_id,
                        SKU.variant_id.in_(variant_ids),
                        SKU.status == "active",
                    )
                    .order_by(SKU.variant_id, SKU.code, SKU.public_id)
                ).all()
            )
            if variant_ids
            else []
        )
        sku_ids = [item.id for item in skus]
        prices = {
            item.sku_id: CatalogPriceSnapshot(
                currency=item.currency,
                price=item.price,
                compare_at_price=item.compare_at_price,
            )
            for item in (
                self.session.scalars(
                    select(StorePrice).where(
                        StorePrice.tenant_id == scope.tenant_id,
                        StorePrice.store_id == scope.store_id,
                        StorePrice.sku_id.in_(sku_ids),
                        StorePrice.currency == scope.currency_code,
                        StorePrice.is_active.is_(True),
                    )
                ).all()
                if sku_ids
                else ()
            )
        }
        availability = {
            item.sku_id: CatalogAvailabilitySnapshot(
                status=item.availability_status,
                quantity=item.quantity,
            )
            for item in (
                self.session.scalars(
                    select(StoreAvailability).where(
                        StoreAvailability.tenant_id == scope.tenant_id,
                        StoreAvailability.store_id == scope.store_id,
                        StoreAvailability.sku_id.in_(sku_ids),
                    )
                ).all()
                if sku_ids
                else ()
            )
        }
        options_by_variant: dict[int, list[CatalogOptionSnapshot]] = {
            item: [] for item in variant_ids
        }
        if variant_ids:
            option_rows = self.session.execute(
                select(
                    VariantOptionValue.variant_id,
                    Attribute.public_id,
                    Attribute.code,
                    Attribute.name,
                    AttributeOption.public_id,
                    AttributeOption.value,
                    AttributeOption.display_label,
                )
                .join(
                    Attribute,
                    and_(
                        Attribute.id
                        == VariantOptionValue.attribute_id,
                        Attribute.tenant_id
                        == VariantOptionValue.tenant_id,
                    ),
                )
                .join(
                    AttributeOption,
                    and_(
                        AttributeOption.id
                        == VariantOptionValue.attribute_option_id,
                        AttributeOption.tenant_id
                        == VariantOptionValue.tenant_id,
                    ),
                )
                .where(
                    VariantOptionValue.tenant_id == scope.tenant_id,
                    VariantOptionValue.variant_id.in_(variant_ids),
                    Attribute.status == "active",
                    AttributeOption.status == "active",
                )
                .order_by(
                    VariantOptionValue.variant_id,
                    Attribute.code,
                    AttributeOption.sort_order,
                    AttributeOption.public_id,
                )
            ).all()
            for row in option_rows:
                options_by_variant[row[0]].append(
                    CatalogOptionSnapshot(
                        attribute_public_id=row[1],
                        attribute_code=row[2],
                        attribute_name=row[3],
                        option_public_id=row[4],
                        value=row[5],
                        display_label=row[6],
                    )
                )

        skus_by_variant: dict[int, list[CatalogSkuSnapshot]] = {
            item: [] for item in variant_ids
        }
        for sku in skus:
            skus_by_variant[sku.variant_id].append(
                CatalogSkuSnapshot(
                    public_id=sku.public_id,
                    code=sku.code,
                    barcode=sku.barcode,
                    price=prices.get(sku.id),
                    availability=availability.get(sku.id),
                )
            )
        variants_by_product: dict[
            int, list[CatalogVariantSnapshot]
        ] = {item: [] for item in product_ids}
        for variant in variants:
            variants_by_product[variant.product_id].append(
                CatalogVariantSnapshot(
                    public_id=variant.public_id,
                    name=variant.name,
                    options=tuple(options_by_variant[variant.id]),
                    skus=tuple(skus_by_variant[variant.id]),
                )
            )
        return tuple(
            CatalogProductSnapshot(
                public_id=product.public_id,
                name=product.name,
                description=product.description,
                short_description=product.short_description,
                product_type=product.product_type,
                variants=tuple(variants_by_product[product.id]),
            )
            for product in products
        )
