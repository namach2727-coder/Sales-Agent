"""Tenant-scoped application service for the FOUNDATION-06 catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, TypeVar

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog.domain import (
    CatalogConflictError,
    CatalogNotFoundError,
    CatalogUnsafeOperationError,
    CatalogValidationError,
    canonical_combination_key,
    default_sku_code,
    normalize_barcode,
    normalize_code,
    normalize_currency,
    normalize_lifecycle,
    normalize_money,
    normalize_name,
    normalize_option_value,
    normalize_optional_text,
    normalize_product_type,
    normalize_sku,
    normalize_slug,
    validate_availability,
    validate_price,
)
from app.catalog.models import (
    Attribute,
    AttributeOption,
    Brand,
    BrandMedia,
    Category,
    CategoryMedia,
    MediaAsset,
    Product,
    ProductAttribute,
    ProductCategory,
    ProductMedia,
    ProductTag,
    SKU,
    SkuMedia,
    StoreAvailability,
    StorePrice,
    Tag,
    Variant,
    VariantMedia,
    VariantOptionValue,
)
from app.models import Store, TenantAuditLog


CatalogModel = TypeVar("CatalogModel")


def _now() -> datetime:
    return datetime.now(UTC)


class CatalogService:
    """Owns catalog invariants; every lookup is constrained by tenant_id."""

    def __init__(
        self,
        session: Session,
        *,
        tenant_id: int,
        actor_identity_id: int | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_identity_id = actor_identity_id

    def _audit(
        self,
        action: str,
        target_type: str,
        target_public_id: str,
        *,
        store_id: int | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            TenantAuditLog(
                tenant_id=self.tenant_id,
                store_id=store_id,
                actor_identity_id=self.actor_identity_id,
                action=action,
                target_type=target_type,
                target_public_id=target_public_id,
                details_json=details or {},
            )
        )

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise CatalogConflictError("catalog identifier or relationship already exists") from exc

    def _resource(
        self,
        model: type[CatalogModel],
        public_id: str,
        *,
        include_archived: bool = False,
    ) -> CatalogModel:
        clauses = [model.public_id == public_id, model.tenant_id == self.tenant_id]  # type: ignore[attr-defined]
        if not include_archived and hasattr(model, "status"):
            clauses.append(model.status != "archived")  # type: ignore[attr-defined]
        item = self.session.scalar(select(model).where(*clauses))
        if item is None:
            raise CatalogNotFoundError("resource not found")
        return item

    def _store(self, public_id: str) -> Store:
        store = self.session.scalar(
            select(Store).where(
                Store.public_id == public_id,
                Store.tenant_id == self.tenant_id,
                Store.deleted_at.is_(None),
            )
        )
        if store is None:
            raise CatalogNotFoundError("resource not found")
        return store

    @staticmethod
    def _page(query: Select[Any], session: Session, *, page: int, page_size: int) -> tuple[list[Any], int]:
        total = session.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
        items = list(
            session.scalars(
                query.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return items, total

    # Products -----------------------------------------------------------------

    def create_product(
        self,
        *,
        name: str,
        slug: str,
        product_type: str,
        description: str | None = None,
        short_description: str | None = None,
        status: str = "draft",
        is_featured: bool = False,
        sku_code: str | None = None,
        barcode: str | None = None,
    ) -> Product:
        """Atomically create Product + default Variant + default SKU."""

        normalized_slug = normalize_slug(slug)
        normalized_status = normalize_lifecycle(status)
        product = Product(
            tenant_id=self.tenant_id,
            name=normalize_name(name),
            slug=normalized_slug,
            product_type=normalize_product_type(product_type),
            description=normalize_optional_text(description),
            short_description=normalize_optional_text(short_description, maximum=500),
            status=normalized_status,
            is_featured=is_featured,
            archived_at=_now() if normalized_status == "archived" else None,
        )
        self.session.add(product)
        try:
            self.session.flush()
            variant = Variant(
                tenant_id=self.tenant_id,
                product_id=product.id,
                name="Default",
                combination_key="default",
                status=normalized_status,
                archived_at=_now() if normalized_status == "archived" else None,
            )
            self.session.add(variant)
            self.session.flush()
            sku = SKU(
                tenant_id=self.tenant_id,
                variant_id=variant.id,
                code=normalize_sku(sku_code) if sku_code else default_sku_code(normalized_slug),
                barcode=normalize_barcode(barcode),
                status=normalized_status,
                archived_at=_now() if normalized_status == "archived" else None,
            )
            self.session.add(sku)
            self.session.flush()
            self._audit(
                "catalog.product.created",
                "catalog_product",
                product.public_id,
                details={
                    "product_type": product.product_type,
                    "default_variant_public_id": variant.public_id,
                    "default_sku_public_id": sku.public_id,
                },
            )
            self._commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise CatalogConflictError("product slug, SKU code or barcode already exists") from exc
        self.session.refresh(product)
        return product

    def get_product(self, public_id: str, *, include_archived: bool = False) -> Product:
        return self._resource(Product, public_id, include_archived=include_archived)

    def list_products(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        product_type: str | None = None,
        brand_public_id: str | None = None,
        category_public_id: str | None = None,
        tag_public_id: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.tenant_id == self.tenant_id)
        if not include_archived:
            query = query.where(Product.status != "archived")
        if status:
            query = query.where(Product.status == normalize_lifecycle(status))
        if product_type:
            query = query.where(Product.product_type == normalize_product_type(product_type))
        if brand_public_id:
            brand = self._resource(Brand, brand_public_id)
            query = query.where(Product.brand_id == brand.id)
        if category_public_id:
            category = self._resource(Category, category_public_id)
            query = query.join(ProductCategory).where(ProductCategory.category_id == category.id)
        if tag_public_id:
            tag = self._resource(Tag, tag_public_id)
            query = query.join(ProductTag).where(ProductTag.tag_id == tag.id)
        if search:
            pattern = f"%{normalize_name(search, field='search', maximum=100).lower()}%"
            query = (
                query.outerjoin(Variant, Variant.product_id == Product.id)
                .outerjoin(SKU, SKU.variant_id == Variant.id)
                .where(or_(func.lower(Product.name).like(pattern), func.lower(SKU.code).like(pattern)))
            )
        return self._page(query.distinct().order_by(Product.created_at, Product.id), self.session, page=page, page_size=page_size)

    def update_product(self, public_id: str, **changes: object) -> Product:
        product = self.get_product(public_id)
        if "name" in changes and changes["name"] is not None:
            product.name = normalize_name(str(changes["name"]))
        if "slug" in changes and changes["slug"] is not None:
            product.slug = normalize_slug(str(changes["slug"]))
        if "description" in changes:
            product.description = normalize_optional_text(changes["description"])  # type: ignore[arg-type]
        if "short_description" in changes:
            product.short_description = normalize_optional_text(changes["short_description"], maximum=500)  # type: ignore[arg-type]
        if "product_type" in changes and changes["product_type"] is not None:
            product.product_type = normalize_product_type(str(changes["product_type"]))
        if "status" in changes and changes["status"] is not None:
            product.status = normalize_lifecycle(str(changes["status"]))
            if product.status == "archived":
                product.archived_at = _now()
        if "is_featured" in changes and changes["is_featured"] is not None:
            product.is_featured = bool(changes["is_featured"])
        self._audit("catalog.product.updated", "catalog_product", product.public_id)
        self._commit()
        return product

    def archive_product(self, public_id: str) -> Product:
        product = self.get_product(public_id)
        product.status = "archived"
        product.archived_at = _now()
        self._audit("catalog.product.archived", "catalog_product", product.public_id)
        self._commit()
        return product

    # Brands, tags, categories and attributes ----------------------------------

    def create_brand(
        self, *, name: str, slug: str, description: str | None = None, status: str = "active"
    ) -> Brand:
        brand = Brand(
            tenant_id=self.tenant_id,
            name=normalize_name(name),
            slug=normalize_slug(slug),
            description=normalize_optional_text(description),
            status=normalize_lifecycle(status),
        )
        self.session.add(brand)
        self.session.flush()
        self._audit("catalog.brand.created", "catalog_brand", brand.public_id)
        self._commit()
        return brand

    def update_brand(self, public_id: str, **changes: object) -> Brand:
        brand = self._resource(Brand, public_id)
        if changes.get("name") is not None:
            brand.name = normalize_name(str(changes["name"]))
        if changes.get("slug") is not None:
            brand.slug = normalize_slug(str(changes["slug"]))
        if "description" in changes:
            brand.description = normalize_optional_text(changes["description"])  # type: ignore[arg-type]
        if changes.get("status") is not None:
            brand.status = normalize_lifecycle(str(changes["status"]))
            if brand.status == "archived":
                brand.archived_at = _now()
        self._audit("catalog.brand.updated", "catalog_brand", brand.public_id)
        self._commit()
        return brand

    def create_tag(self, *, name: str, slug: str, status: str = "active") -> Tag:
        tag = Tag(
            tenant_id=self.tenant_id,
            name=normalize_name(name),
            slug=normalize_slug(slug),
            status=normalize_lifecycle(status),
        )
        self.session.add(tag)
        self.session.flush()
        self._audit("catalog.tag.created", "catalog_tag", tag.public_id)
        self._commit()
        return tag

    def update_tag(self, public_id: str, **changes: object) -> Tag:
        tag = self._resource(Tag, public_id)
        if changes.get("name") is not None:
            tag.name = normalize_name(str(changes["name"]))
        if changes.get("slug") is not None:
            tag.slug = normalize_slug(str(changes["slug"]))
        if changes.get("status") is not None:
            tag.status = normalize_lifecycle(str(changes["status"]))
            if tag.status == "archived":
                tag.archived_at = _now()
        self._audit("catalog.tag.updated", "catalog_tag", tag.public_id)
        self._commit()
        return tag

    def create_category(
        self,
        *,
        name: str,
        slug: str,
        parent_public_id: str | None = None,
        status: str = "active",
    ) -> Category:
        parent = self._resource(Category, parent_public_id) if parent_public_id else None
        category = Category(
            tenant_id=self.tenant_id,
            name=normalize_name(name),
            slug=normalize_slug(slug),
            parent_id=parent.id if parent else None,
            status=normalize_lifecycle(status),
        )
        self.session.add(category)
        self.session.flush()
        self._audit("catalog.category.created", "catalog_category", category.public_id)
        self._commit()
        return category

    def update_category(self, public_id: str, **changes: object) -> Category:
        category = self._resource(Category, public_id)
        if changes.get("name") is not None:
            category.name = normalize_name(str(changes["name"]))
        if changes.get("slug") is not None:
            category.slug = normalize_slug(str(changes["slug"]))
        if changes.get("status") is not None:
            category.status = normalize_lifecycle(str(changes["status"]))
            if category.status == "archived":
                category.archived_at = _now()
        if "parent_public_id" in changes:
            parent_public_id = changes["parent_public_id"]
            parent = self._resource(Category, str(parent_public_id)) if parent_public_id else None
            if parent and parent.id == category.id:
                raise CatalogValidationError("category cannot be its own parent")
            cursor = parent
            visited: set[int] = set()
            while cursor is not None:
                if cursor.id == category.id:
                    raise CatalogValidationError("category hierarchy cannot contain a cycle")
                if cursor.id in visited:
                    raise CatalogValidationError("existing category hierarchy is cyclic")
                visited.add(cursor.id)
                cursor = (
                    self.session.scalar(
                        select(Category).where(
                            Category.id == cursor.parent_id,
                            Category.tenant_id == self.tenant_id,
                        )
                    )
                    if cursor.parent_id
                    else None
                )
            category.parent_id = parent.id if parent else None
            self._audit(
                "catalog.category.hierarchy_changed",
                "catalog_category",
                category.public_id,
                details={"parent_public_id": parent.public_id if parent else None},
            )
        else:
            self._audit("catalog.category.updated", "catalog_category", category.public_id)
        self._commit()
        return category

    def create_attribute(
        self, *, name: str, code: str, status: str = "active"
    ) -> Attribute:
        attribute = Attribute(
            tenant_id=self.tenant_id,
            name=normalize_name(name),
            code=normalize_code(code),
            status=normalize_lifecycle(status),
        )
        self.session.add(attribute)
        self.session.flush()
        self._audit("catalog.attribute.created", "catalog_attribute", attribute.public_id)
        self._commit()
        return attribute

    def update_attribute(self, public_id: str, **changes: object) -> Attribute:
        attribute = self._resource(Attribute, public_id)
        if changes.get("name") is not None:
            attribute.name = normalize_name(str(changes["name"]))
        if changes.get("code") is not None:
            attribute.code = normalize_code(str(changes["code"]))
        if changes.get("status") is not None:
            next_status = normalize_lifecycle(str(changes["status"]))
            if next_status == "archived":
                assigned = self.session.scalar(
                    select(ProductAttribute.id).where(
                        ProductAttribute.tenant_id == self.tenant_id,
                        ProductAttribute.attribute_id == attribute.id,
                    )
                )
                if assigned is not None:
                    raise CatalogUnsafeOperationError("attribute is assigned to a product")
            attribute.status = next_status
            if next_status == "archived":
                attribute.archived_at = _now()
        self._audit("catalog.attribute.updated", "catalog_attribute", attribute.public_id)
        self._commit()
        return attribute

    def create_attribute_option(
        self,
        attribute_public_id: str,
        *,
        value: str,
        display_label: str | None = None,
        sort_order: int = 0,
        status: str = "active",
    ) -> AttributeOption:
        attribute = self._resource(Attribute, attribute_public_id)
        normalized_value, identity = normalize_option_value(value)
        option = AttributeOption(
            tenant_id=self.tenant_id,
            attribute_id=attribute.id,
            value=normalized_value,
            normalized_value=identity,
            display_label=normalize_optional_text(display_label, maximum=200),
            sort_order=sort_order,
            status=normalize_lifecycle(status),
        )
        self.session.add(option)
        self.session.flush()
        self._audit("catalog.attribute_option.created", "catalog_attribute_option", option.public_id)
        self._commit()
        return option

    def update_attribute_option(self, public_id: str, **changes: object) -> AttributeOption:
        option = self._resource(AttributeOption, public_id)
        if changes.get("value") is not None:
            option.value, option.normalized_value = normalize_option_value(str(changes["value"]))
        if "display_label" in changes:
            option.display_label = normalize_optional_text(changes["display_label"], maximum=200)  # type: ignore[arg-type]
        if changes.get("sort_order") is not None:
            option.sort_order = int(changes["sort_order"])
        if changes.get("status") is not None:
            next_status = normalize_lifecycle(str(changes["status"]))
            if next_status == "archived":
                used = self.session.scalar(
                    select(VariantOptionValue.id).where(
                        VariantOptionValue.tenant_id == self.tenant_id,
                        VariantOptionValue.attribute_option_id == option.id,
                    )
                )
                if used is not None:
                    raise CatalogUnsafeOperationError("attribute option is used by a variant")
            option.status = next_status
            if next_status == "archived":
                option.archived_at = _now()
        self._audit("catalog.attribute_option.updated", "catalog_attribute_option", option.public_id)
        self._commit()
        return option

    def list_reference(
        self,
        model: type[CatalogModel],
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        parent_public_id: str | None = None,
    ) -> tuple[list[CatalogModel], int]:
        query = select(model).where(model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        if hasattr(model, "status"):
            query = query.where(model.status != "archived")  # type: ignore[attr-defined]
            if status:
                query = query.where(model.status == normalize_lifecycle(status))  # type: ignore[attr-defined]
        if model is Category and parent_public_id is not None:
            parent = self._resource(Category, parent_public_id)
            query = query.where(Category.parent_id == parent.id)
        order = model.id  # type: ignore[attr-defined]
        return self._page(query.order_by(order), self.session, page=page, page_size=page_size)

    def assign_brand(self, product_public_id: str, brand_public_id: str | None) -> Product:
        product = self.get_product(product_public_id)
        brand = self._resource(Brand, brand_public_id) if brand_public_id else None
        product.brand_id = brand.id if brand else None
        self._audit(
            "catalog.product.brand_changed",
            "catalog_product",
            product.public_id,
            details={"brand_public_id": brand.public_id if brand else None},
        )
        self._commit()
        return product

    def _set_product_join(
        self,
        *,
        product_public_id: str,
        target_public_id: str,
        target_model: type[Category] | type[Tag],
        join_model: type[ProductCategory] | type[ProductTag],
        target_column: str,
        attach: bool,
    ) -> None:
        product = self.get_product(product_public_id)
        target = self._resource(target_model, target_public_id)
        query = select(join_model).where(
            join_model.tenant_id == self.tenant_id,
            join_model.product_id == product.id,
            getattr(join_model, target_column) == target.id,
        )
        existing = self.session.scalar(query)
        if attach and existing is None:
            self.session.add(
                join_model(
                    tenant_id=self.tenant_id,
                    product_id=product.id,
                    **{target_column: target.id},
                )
            )
        elif not attach and existing is not None:
            self.session.delete(existing)
        self._audit(
            f"catalog.product.{target_column}.{'assigned' if attach else 'removed'}",
            "catalog_product",
            product.public_id,
            details={"target_public_id": target.public_id},
        )
        self._commit()

    def set_product_category(self, product_public_id: str, category_public_id: str, *, attach: bool) -> None:
        self._set_product_join(
            product_public_id=product_public_id,
            target_public_id=category_public_id,
            target_model=Category,
            join_model=ProductCategory,
            target_column="category_id",
            attach=attach,
        )

    def set_product_tag(self, product_public_id: str, tag_public_id: str, *, attach: bool) -> None:
        self._set_product_join(
            product_public_id=product_public_id,
            target_public_id=tag_public_id,
            target_model=Tag,
            join_model=ProductTag,
            target_column="tag_id",
            attach=attach,
        )

    def set_product_attribute(
        self,
        product_public_id: str,
        attribute_public_id: str,
        *,
        attach: bool,
        sort_order: int = 0,
        is_variant_defining: bool = False,
    ) -> None:
        product = self.get_product(product_public_id)
        attribute = self._resource(Attribute, attribute_public_id)
        existing = self.session.scalar(
            select(ProductAttribute).where(
                ProductAttribute.product_id == product.id,
                ProductAttribute.attribute_id == attribute.id,
                ProductAttribute.tenant_id == self.tenant_id,
            )
        )
        if attach:
            if existing is None:
                existing = ProductAttribute(
                    tenant_id=self.tenant_id,
                    product_id=product.id,
                    attribute_id=attribute.id,
                )
                self.session.add(existing)
            existing.sort_order = sort_order
            existing.is_variant_defining = is_variant_defining
        elif existing is not None:
            used = self.session.scalar(
                select(VariantOptionValue.id)
                .join(Variant, Variant.id == VariantOptionValue.variant_id)
                .where(
                    Variant.product_id == product.id,
                    VariantOptionValue.attribute_id == attribute.id,
                    VariantOptionValue.tenant_id == self.tenant_id,
                )
            )
            if used is not None:
                raise CatalogUnsafeOperationError("attribute is used by a variant")
            self.session.delete(existing)
        self._audit(
            f"catalog.product.attribute.{'assigned' if attach else 'removed'}",
            "catalog_product",
            product.public_id,
            details={
                "attribute_public_id": attribute.public_id,
                "is_variant_defining": is_variant_defining if attach else None,
            },
        )
        self._commit()

    # Variants and SKUs ---------------------------------------------------------

    def _option_pairs(self, product: Product, option_public_ids: list[str]) -> list[tuple[AttributeOption, ProductAttribute]]:
        if len(set(option_public_ids)) != len(option_public_ids):
            raise CatalogValidationError("duplicate option supplied")
        if not option_public_ids:
            return []
        options = list(
            self.session.scalars(
                select(AttributeOption).where(
                    AttributeOption.tenant_id == self.tenant_id,
                    AttributeOption.public_id.in_(option_public_ids),
                    AttributeOption.status != "archived",
                )
            ).all()
        )
        if len(options) != len(option_public_ids):
            raise CatalogNotFoundError("resource not found")
        assignments = {
            item.attribute_id: item
            for item in self.session.scalars(
                select(ProductAttribute).where(
                    ProductAttribute.tenant_id == self.tenant_id,
                    ProductAttribute.product_id == product.id,
                    ProductAttribute.attribute_id.in_([item.attribute_id for item in options]),
                )
            ).all()
        }
        result: list[tuple[AttributeOption, ProductAttribute]] = []
        for option in options:
            assignment = assignments.get(option.attribute_id)
            if assignment is None:
                raise CatalogValidationError("attribute is not enabled for product")
            result.append((option, assignment))
        return result

    def create_variant(
        self,
        product_public_id: str,
        *,
        name: str | None = None,
        status: str = "draft",
        option_public_ids: list[str] | None = None,
    ) -> Variant:
        product = self.get_product(product_public_id)
        pairs = self._option_pairs(product, option_public_ids or [])
        defining = [
            (option.attribute_id, option.id)
            for option, assignment in pairs
            if assignment.is_variant_defining
        ]
        variant = Variant(
            tenant_id=self.tenant_id,
            product_id=product.id,
            name=normalize_optional_text(name, maximum=200),
            combination_key=canonical_combination_key(defining),
            status=normalize_lifecycle(status),
        )
        self.session.add(variant)
        try:
            self.session.flush()
            for option, _ in pairs:
                self.session.add(
                    VariantOptionValue(
                        tenant_id=self.tenant_id,
                        variant_id=variant.id,
                        attribute_id=option.attribute_id,
                        attribute_option_id=option.id,
                    )
                )
            self._audit("catalog.variant.created", "catalog_variant", variant.public_id)
            self._commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise CatalogConflictError("variant option combination already exists") from exc
        return variant

    def get_variant(self, public_id: str, *, include_archived: bool = False) -> Variant:
        return self._resource(Variant, public_id, include_archived=include_archived)

    def list_variants(self, product_public_id: str) -> list[Variant]:
        product = self.get_product(product_public_id)
        return list(
            self.session.scalars(
                select(Variant).where(
                    Variant.tenant_id == self.tenant_id,
                    Variant.product_id == product.id,
                    Variant.status != "archived",
                ).order_by(Variant.id)
            ).all()
        )

    def list_variants_page(
        self, product_public_id: str, *, page: int, page_size: int
    ) -> tuple[list[Variant], int]:
        product = self.get_product(product_public_id)
        query = select(Variant).where(
            Variant.tenant_id == self.tenant_id,
            Variant.product_id == product.id,
            Variant.status != "archived",
        ).order_by(Variant.id)
        return self._page(query, self.session, page=page, page_size=page_size)

    def update_variant(self, public_id: str, **changes: object) -> Variant:
        variant = self.get_variant(public_id)
        if "name" in changes:
            variant.name = normalize_optional_text(changes["name"], maximum=200)  # type: ignore[arg-type]
        if changes.get("status") is not None:
            variant.status = normalize_lifecycle(str(changes["status"]))
            if variant.status == "archived":
                variant.archived_at = _now()
        self._audit("catalog.variant.updated", "catalog_variant", variant.public_id)
        self._commit()
        return variant

    def replace_variant_options(self, public_id: str, option_public_ids: list[str]) -> Variant:
        variant = self.get_variant(public_id)
        product = self.session.scalar(
            select(Product).where(
                Product.id == variant.product_id,
                Product.tenant_id == self.tenant_id,
            )
        )
        if product is None:
            raise CatalogNotFoundError("resource not found")
        pairs = self._option_pairs(product, option_public_ids)
        defining = [
            (option.attribute_id, option.id)
            for option, assignment in pairs
            if assignment.is_variant_defining
        ]
        variant.combination_key = canonical_combination_key(defining)
        self.session.execute(
            delete(VariantOptionValue).where(
                VariantOptionValue.variant_id == variant.id,
                VariantOptionValue.tenant_id == self.tenant_id,
            )
        )
        for option, _ in pairs:
            self.session.add(
                VariantOptionValue(
                    tenant_id=self.tenant_id,
                    variant_id=variant.id,
                    attribute_id=option.attribute_id,
                    attribute_option_id=option.id,
                )
            )
        self._audit("catalog.variant.options_updated", "catalog_variant", variant.public_id)
        self._commit()
        return variant

    def create_sku(
        self,
        variant_public_id: str,
        *,
        code: str,
        barcode: str | None = None,
        status: str = "draft",
    ) -> SKU:
        variant = self.get_variant(variant_public_id)
        sku = SKU(
            tenant_id=self.tenant_id,
            variant_id=variant.id,
            code=normalize_sku(code),
            barcode=normalize_barcode(barcode),
            status=normalize_lifecycle(status),
        )
        self.session.add(sku)
        self.session.flush()
        self._audit("catalog.sku.created", "catalog_sku", sku.public_id)
        self._commit()
        return sku

    def get_sku(self, public_id: str, *, include_archived: bool = False) -> SKU:
        return self._resource(SKU, public_id, include_archived=include_archived)

    def _commercial_sku(self, public_id: str) -> SKU:
        sku = self.session.scalar(
            select(SKU)
            .join(Variant, Variant.id == SKU.variant_id)
            .join(Product, Product.id == Variant.product_id)
            .where(
                SKU.public_id == public_id,
                SKU.tenant_id == self.tenant_id,
                SKU.status != "archived",
                Variant.tenant_id == self.tenant_id,
                Variant.status != "archived",
                Product.tenant_id == self.tenant_id,
                Product.status != "archived",
            )
        )
        if sku is None:
            raise CatalogNotFoundError("resource not found")
        return sku

    def list_skus(
        self,
        *,
        page: int,
        page_size: int,
        product_public_id: str | None = None,
        variant_public_id: str | None = None,
        status: str | None = None,
        code: str | None = None,
    ) -> tuple[list[SKU], int]:
        query = select(SKU).where(SKU.tenant_id == self.tenant_id, SKU.status != "archived")
        if product_public_id:
            product = self.get_product(product_public_id)
            query = query.join(Variant).where(Variant.product_id == product.id)
        if variant_public_id:
            variant = self.get_variant(variant_public_id)
            query = query.where(SKU.variant_id == variant.id)
        if status:
            query = query.where(SKU.status == normalize_lifecycle(status))
        if code:
            query = query.where(func.lower(SKU.code).like(f"%{normalize_sku(code).lower()}%"))
        return self._page(query.order_by(SKU.id), self.session, page=page, page_size=page_size)

    def update_sku(self, public_id: str, **changes: object) -> SKU:
        sku = self.get_sku(public_id)
        if changes.get("code") is not None:
            sku.code = normalize_sku(str(changes["code"]))
        if "barcode" in changes:
            sku.barcode = normalize_barcode(changes["barcode"])  # type: ignore[arg-type]
        if changes.get("status") is not None:
            sku.status = normalize_lifecycle(str(changes["status"]))
            if sku.status == "archived":
                sku.archived_at = _now()
        self._audit("catalog.sku.updated", "catalog_sku", sku.public_id)
        self._commit()
        return sku

    # Media ---------------------------------------------------------------------

    def create_media_asset(
        self,
        *,
        storage_provider: str,
        storage_key: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        checksum: str | None = None,
        status: str = "pending",
        metadata: dict[str, object] | None = None,
    ) -> MediaAsset:
        normalized_status = status.strip().lower()
        if normalized_status not in {"pending", "ready", "failed", "archived"}:
            raise CatalogValidationError("invalid media status")
        if file_size < 0:
            raise CatalogValidationError("file_size cannot be negative")
        media = MediaAsset(
            tenant_id=self.tenant_id,
            storage_provider=normalize_name(storage_provider, field="storage_provider", maximum=50).lower(),
            storage_key=normalize_name(storage_key, field="storage_key", maximum=500),
            original_filename=normalize_name(original_filename, field="original_filename", maximum=255),
            mime_type=normalize_name(mime_type, field="mime_type", maximum=150).lower(),
            file_size=file_size,
            checksum=normalize_optional_text(checksum, maximum=128),
            status=normalized_status,
            metadata_json=metadata or {},
        )
        self.session.add(media)
        self.session.flush()
        self._audit("catalog.media.created", "catalog_media_asset", media.public_id)
        self._commit()
        return media

    _MEDIA_OWNER = {
        "product": (Product, ProductMedia, "product_id"),
        "variant": (Variant, VariantMedia, "variant_id"),
        "sku": (SKU, SkuMedia, "sku_id"),
        "brand": (Brand, BrandMedia, "brand_id"),
        "category": (Category, CategoryMedia, "category_id"),
    }

    def attach_media(
        self,
        *,
        owner_type: str,
        owner_public_id: str,
        media_public_id: str,
        role: str = "gallery",
        sort_order: int = 0,
        is_primary: bool = False,
    ) -> None:
        definition = self._MEDIA_OWNER.get(owner_type)
        if definition is None:
            raise CatalogValidationError("unsupported media owner type")
        owner_model, association_model, owner_column = definition
        owner = self._resource(owner_model, owner_public_id)
        media = self._resource(MediaAsset, media_public_id, include_archived=True)
        normalized_role = normalize_code(role)
        if is_primary:
            existing_primary = self.session.scalar(
                select(association_model).where(
                    getattr(association_model, owner_column) == owner.id,
                    association_model.tenant_id == self.tenant_id,
                    association_model.role == normalized_role,
                    association_model.is_primary.is_(True),
                )
            )
            if existing_primary is not None:
                existing_primary.is_primary = False
        association = association_model(
            tenant_id=self.tenant_id,
            media_asset_id=media.id,
            role=normalized_role,
            sort_order=sort_order,
            is_primary=is_primary,
            **{owner_column: owner.id},
        )
        self.session.add(association)
        self._audit(
            "catalog.media.attached",
            f"catalog_{owner_type}",
            owner.public_id,
            details={"media_public_id": media.public_id, "role": normalized_role},
        )
        self._commit()

    def detach_media(
        self,
        *,
        owner_type: str,
        owner_public_id: str,
        media_public_id: str,
        role: str = "gallery",
    ) -> None:
        definition = self._MEDIA_OWNER.get(owner_type)
        if definition is None:
            raise CatalogValidationError("unsupported media owner type")
        owner_model, association_model, owner_column = definition
        owner = self._resource(owner_model, owner_public_id)
        media = self._resource(MediaAsset, media_public_id, include_archived=True)
        association = self.session.scalar(
            select(association_model).where(
                getattr(association_model, owner_column) == owner.id,
                association_model.media_asset_id == media.id,
                association_model.tenant_id == self.tenant_id,
                association_model.role == normalize_code(role),
            )
        )
        if association is None:
            raise CatalogNotFoundError("resource not found")
        self.session.delete(association)
        self._audit(
            "catalog.media.detached",
            f"catalog_{owner_type}",
            owner.public_id,
            details={"media_public_id": media.public_id},
        )
        self._commit()

    def list_media(self, *, owner_type: str, owner_public_id: str) -> list[tuple[MediaAsset, Any]]:
        definition = self._MEDIA_OWNER.get(owner_type)
        if definition is None:
            raise CatalogValidationError("unsupported media owner type")
        owner_model, association_model, owner_column = definition
        owner = self._resource(owner_model, owner_public_id)
        rows = self.session.execute(
            select(MediaAsset, association_model)
            .join(association_model, association_model.media_asset_id == MediaAsset.id)
            .where(
                getattr(association_model, owner_column) == owner.id,
                association_model.tenant_id == self.tenant_id,
                MediaAsset.tenant_id == self.tenant_id,
            )
            .order_by(association_model.sort_order, association_model.id)
        ).all()
        return [(row[0], row[1]) for row in rows]

    def list_media_page(
        self,
        *,
        owner_type: str,
        owner_public_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[MediaAsset, Any]], int]:
        definition = self._MEDIA_OWNER.get(owner_type)
        if definition is None:
            raise CatalogValidationError("unsupported media owner type")
        owner_model, association_model, owner_column = definition
        owner = self._resource(owner_model, owner_public_id)
        base = (
            select(MediaAsset, association_model)
            .join(association_model, association_model.media_asset_id == MediaAsset.id)
            .where(
                getattr(association_model, owner_column) == owner.id,
                association_model.tenant_id == self.tenant_id,
                MediaAsset.tenant_id == self.tenant_id,
            )
        )
        total = self.session.scalar(
            select(func.count()).select_from(base.order_by(None).subquery())
        ) or 0
        rows = self.session.execute(
            base.order_by(association_model.sort_order, association_model.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return [(row[0], row[1]) for row in rows], total

    # Store commercial state ----------------------------------------------------

    def upsert_price(
        self,
        *,
        store_public_id: str,
        sku_public_id: str,
        currency: str,
        price: Decimal | int | str,
        compare_at_price: Decimal | int | str | None = None,
        is_active: bool = True,
    ) -> StorePrice:
        store = self._store(store_public_id)
        sku = self._commercial_sku(sku_public_id)
        normalized_currency = normalize_currency(currency)
        normalized_price = normalize_money(price, field="price")
        normalized_compare = (
            normalize_money(compare_at_price, field="compare_at_price")
            if compare_at_price is not None
            else None
        )
        validate_price(normalized_price, normalized_compare)
        item = self.session.scalar(
            select(StorePrice).where(
                StorePrice.tenant_id == self.tenant_id,
                StorePrice.store_id == store.id,
                StorePrice.sku_id == sku.id,
                StorePrice.currency == normalized_currency,
            )
        )
        if item is None:
            item = StorePrice(
                tenant_id=self.tenant_id,
                store_id=store.id,
                sku_id=sku.id,
                currency=normalized_currency,
            )
            self.session.add(item)
        item.price = normalized_price
        item.compare_at_price = normalized_compare
        item.is_active = is_active
        self.session.flush()
        self._audit(
            "catalog.store_price.changed",
            "catalog_store_price",
            item.public_id,
            store_id=store.id,
            details={"sku_public_id": sku.public_id, "currency": normalized_currency},
        )
        self._commit()
        return item

    def list_prices(
        self,
        *,
        page: int,
        page_size: int,
        store_public_id: str | None = None,
        sku_public_id: str | None = None,
        currency: str | None = None,
        active: bool | None = None,
        allowed_store_ids: tuple[int, ...] | None = None,
    ) -> tuple[list[StorePrice], int]:
        query = select(StorePrice).where(StorePrice.tenant_id == self.tenant_id)
        if allowed_store_ids is not None:
            query = query.where(StorePrice.store_id.in_(allowed_store_ids))
        if store_public_id:
            query = query.where(StorePrice.store_id == self._store(store_public_id).id)
        if sku_public_id:
            query = query.where(StorePrice.sku_id == self.get_sku(sku_public_id).id)
        if currency:
            query = query.where(StorePrice.currency == normalize_currency(currency))
        if active is not None:
            query = query.where(StorePrice.is_active == active)
        return self._page(query.order_by(StorePrice.id), self.session, page=page, page_size=page_size)

    def get_price(self, public_id: str) -> StorePrice:
        return self._resource(StorePrice, public_id, include_archived=True)

    def upsert_availability(
        self,
        *,
        store_public_id: str,
        sku_public_id: str,
        availability_status: str,
        quantity: int | None = None,
    ) -> StoreAvailability:
        store = self._store(store_public_id)
        sku = self._commercial_sku(sku_public_id)
        normalized_status, normalized_quantity = validate_availability(
            availability_status, quantity
        )
        item = self.session.scalar(
            select(StoreAvailability).where(
                StoreAvailability.tenant_id == self.tenant_id,
                StoreAvailability.store_id == store.id,
                StoreAvailability.sku_id == sku.id,
            )
        )
        if item is None:
            item = StoreAvailability(
                tenant_id=self.tenant_id,
                store_id=store.id,
                sku_id=sku.id,
            )
            self.session.add(item)
        item.availability_status = normalized_status
        item.quantity = normalized_quantity
        self.session.flush()
        self._audit(
            "catalog.store_availability.changed",
            "catalog_store_availability",
            item.public_id,
            store_id=store.id,
            details={"sku_public_id": sku.public_id, "status": normalized_status},
        )
        self._commit()
        return item

    def list_availability(
        self,
        *,
        page: int,
        page_size: int,
        store_public_id: str | None = None,
        sku_public_id: str | None = None,
        status: str | None = None,
        allowed_store_ids: tuple[int, ...] | None = None,
    ) -> tuple[list[StoreAvailability], int]:
        query = select(StoreAvailability).where(
            StoreAvailability.tenant_id == self.tenant_id
        )
        if allowed_store_ids is not None:
            query = query.where(StoreAvailability.store_id.in_(allowed_store_ids))
        if store_public_id:
            query = query.where(StoreAvailability.store_id == self._store(store_public_id).id)
        if sku_public_id:
            query = query.where(StoreAvailability.sku_id == self.get_sku(sku_public_id).id)
        if status:
            normalized_status, _ = validate_availability(status, None)
            query = query.where(StoreAvailability.availability_status == normalized_status)
        return self._page(query.order_by(StoreAvailability.id), self.session, page=page, page_size=page_size)

    def get_availability(self, public_id: str) -> StoreAvailability:
        return self._resource(StoreAvailability, public_id, include_archived=True)
