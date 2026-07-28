"""Versioned tenant-scoped REST API for FOUNDATION-06."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.catalog.domain import (
    CatalogConflictError,
    CatalogError,
    CatalogNotFoundError,
    CatalogUnsafeOperationError,
    CatalogValidationError,
)
from app.catalog.models import (
    Attribute,
    AttributeOption,
    Brand,
    Category,
    MediaAsset,
    Product,
    SKU,
    StoreAvailability,
    StorePrice,
    Tag,
    Variant,
    VariantOptionValue,
)
from app.catalog.schemas import (
    AttributeAssignment,
    AttributeCreate,
    AttributeOptionCreate,
    AttributeOptionPage,
    AttributeOptionRead,
    AttributeOptionUpdate,
    AttributeRead,
    AttributePage,
    AttributeUpdate,
    BrandAssignment,
    BrandCreate,
    BrandPage,
    BrandRead,
    BrandUpdate,
    CategoryCreate,
    CategoryPage,
    CategoryRead,
    CategoryUpdate,
    MediaAssetCreate,
    MediaAssetRead,
    MediaAssociationRead,
    MediaAssociationPage,
    MediaAttach,
    MediaOwnerType,
    NamedReferenceCreate,
    NamedReferenceUpdate,
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductUpdate,
    SkuCreate,
    SkuPage,
    SkuRead,
    SkuUpdate,
    StoreAvailabilityPage,
    StoreAvailabilityRead,
    StoreAvailabilityUpsert,
    StorePricePage,
    StorePriceRead,
    StorePriceUpsert,
    TagPage,
    TagRead,
    VariantCreate,
    VariantOptionsUpdate,
    VariantPage,
    VariantRead,
    VariantUpdate,
)
from app.catalog.service import CatalogService
from app.database import get_db
from app.models import Store, StoreAccessAssignment, TenantMembership
from app.tenant_management.context import resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


router = APIRouter(
    prefix="/api/v1/tenants/{tenant_public_id}/catalog",
    tags=["business-catalog"],
)


def _raise(error: Exception) -> None:
    if isinstance(error, CatalogValidationError):
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, (CatalogConflictError, CatalogUnsafeOperationError)):
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, (CatalogNotFoundError, TenantManagementError)):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        )
    raise error


def _service(
    tenant_public_id: str,
    permission: str,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    mutation: bool,
) -> CatalogService:
    try:
        context = resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            tenant_permission=permission,
            platform_permission=(
                PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ
            ),
        )
    except TenantManagementError as exc:
        _raise(exc)
    return CatalogService(
        db,
        tenant_id=context.tenant_id,
        actor_identity_id=principal.user_id,
    )


def _allowed_store_ids(
    tenant_public_id: str,
    permission: str,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    mutation: bool,
    requested_store_public_id: str | None = None,
) -> tuple[int, ...] | None:
    """Enforce F05 explicit store access for store-specific catalog state."""

    try:
        context = resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            store_public_id=requested_store_public_id,
            tenant_permission=permission,
            store_permission=permission,
            platform_permission=(
                PermissionCode.TENANT_UPDATE if mutation else PermissionCode.TENANT_READ
            ),
        )
    except TenantManagementError as exc:
        _raise(exc)
    if requested_store_public_id is not None or context.platform_access:
        return None
    membership = db.get(TenantMembership, context.membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resource not found"})
    if membership.all_store_access:
        return None
    return tuple(
        db.scalars(
            select(StoreAccessAssignment.store_id).where(
                StoreAccessAssignment.membership_id == membership.id,
                StoreAccessAssignment.status == "active",
            )
        ).all()
    )


def _product_read(db: Session, item: Product) -> ProductRead:
    brand_public_id = (
        db.scalar(
            select(Brand.public_id).where(
                Brand.id == item.brand_id,
                Brand.tenant_id == item.tenant_id,
            )
        )
        if item.brand_id
        else None
    )
    return ProductRead.model_validate(
        {**item.__dict__, "brand_public_id": brand_public_id}
    )


def _products_read(db: Session, items: list[Product]) -> list[ProductRead]:
    brand_ids = {item.brand_id for item in items if item.brand_id is not None}
    tenant_ids = {item.tenant_id for item in items}
    brands = (
        dict(
            db.execute(
                select(Brand.id, Brand.public_id).where(
                    Brand.id.in_(brand_ids),
                    Brand.tenant_id.in_(tenant_ids),
                )
            ).all()
        )
        if brand_ids
        else {}
    )
    return [
        ProductRead.model_validate(
            {**item.__dict__, "brand_public_id": brands.get(item.brand_id)}
        )
        for item in items
    ]


def _variant_read(db: Session, item: Variant) -> VariantRead:
    product_public_id = db.scalar(
        select(Product.public_id).where(
            Product.id == item.product_id,
            Product.tenant_id == item.tenant_id,
        )
    )
    option_ids = list(
        db.scalars(
            select(AttributeOption.public_id)
            .join(
                VariantOptionValue,
                VariantOptionValue.attribute_option_id == AttributeOption.id,
            )
            .where(
                VariantOptionValue.variant_id == item.id,
                VariantOptionValue.tenant_id == item.tenant_id,
                AttributeOption.tenant_id == item.tenant_id,
            )
            .order_by(AttributeOption.id)
        ).all()
    )
    return VariantRead.model_validate(
        {
            **item.__dict__,
            "product_public_id": product_public_id,
            "option_public_ids": option_ids,
        }
    )


def _variants_read(db: Session, items: list[Variant]) -> list[VariantRead]:
    if not items:
        return []
    product_ids = {item.product_id for item in items}
    tenant_ids = {item.tenant_id for item in items}
    products = dict(
        db.execute(
            select(Product.id, Product.public_id).where(
                Product.id.in_(product_ids),
                Product.tenant_id.in_(tenant_ids),
            )
        ).all()
    )
    option_rows = db.execute(
        select(VariantOptionValue.variant_id, AttributeOption.public_id)
        .join(
            AttributeOption,
            AttributeOption.id == VariantOptionValue.attribute_option_id,
        )
        .where(
            VariantOptionValue.variant_id.in_([item.id for item in items]),
            VariantOptionValue.tenant_id.in_(tenant_ids),
            AttributeOption.tenant_id.in_(tenant_ids),
        )
        .order_by(VariantOptionValue.variant_id, AttributeOption.id)
    ).all()
    options: dict[int, list[str]] = {}
    for variant_id, public_id in option_rows:
        options.setdefault(variant_id, []).append(public_id)
    return [
        VariantRead.model_validate(
            {
                **item.__dict__,
                "product_public_id": products.get(item.product_id),
                "option_public_ids": options.get(item.id, []),
            }
        )
        for item in items
    ]


def _sku_read(db: Session, item: SKU) -> SkuRead:
    variant_public_id = db.scalar(
        select(Variant.public_id).where(
            Variant.id == item.variant_id,
            Variant.tenant_id == item.tenant_id,
        )
    )
    return SkuRead.model_validate(
        {**item.__dict__, "variant_public_id": variant_public_id}
    )


def _skus_read(db: Session, items: list[SKU]) -> list[SkuRead]:
    variant_ids = {item.variant_id for item in items}
    tenant_ids = {item.tenant_id for item in items}
    variants = (
        dict(
            db.execute(
                select(Variant.id, Variant.public_id).where(
                    Variant.id.in_(variant_ids),
                    Variant.tenant_id.in_(tenant_ids),
                )
            ).all()
        )
        if variant_ids
        else {}
    )
    return [
        SkuRead.model_validate(
            {**item.__dict__, "variant_public_id": variants.get(item.variant_id)}
        )
        for item in items
    ]


def _category_read(db: Session, item: Category) -> CategoryRead:
    parent_public_id = (
        db.scalar(
            select(Category.public_id).where(
                Category.id == item.parent_id,
                Category.tenant_id == item.tenant_id,
            )
        )
        if item.parent_id
        else None
    )
    return CategoryRead.model_validate(
        {**item.__dict__, "parent_public_id": parent_public_id}
    )


def _categories_read(db: Session, items: list[Category]) -> list[CategoryRead]:
    parent_ids = {item.parent_id for item in items if item.parent_id is not None}
    tenant_ids = {item.tenant_id for item in items}
    parents = (
        dict(
            db.execute(
                select(Category.id, Category.public_id).where(
                    Category.id.in_(parent_ids),
                    Category.tenant_id.in_(tenant_ids),
                )
            ).all()
        )
        if parent_ids
        else {}
    )
    return [
        CategoryRead.model_validate(
            {
                **item.__dict__,
                "parent_public_id": parents.get(item.parent_id),
            }
        )
        for item in items
    ]


def _option_read(db: Session, item: AttributeOption) -> AttributeOptionRead:
    attribute_public_id = db.scalar(
        select(Attribute.public_id).where(
            Attribute.id == item.attribute_id,
            Attribute.tenant_id == item.tenant_id,
        )
    )
    return AttributeOptionRead.model_validate(
        {**item.__dict__, "attribute_public_id": attribute_public_id}
    )


def _options_read(
    db: Session,
    items: list[AttributeOption],
) -> list[AttributeOptionRead]:
    attribute_ids = {item.attribute_id for item in items}
    tenant_ids = {item.tenant_id for item in items}
    attributes = (
        dict(
            db.execute(
                select(Attribute.id, Attribute.public_id).where(
                    Attribute.id.in_(attribute_ids),
                    Attribute.tenant_id.in_(tenant_ids),
                )
            ).all()
        )
        if attribute_ids
        else {}
    )
    return [
        AttributeOptionRead.model_validate(
            {
                **item.__dict__,
                "attribute_public_id": attributes.get(item.attribute_id),
            }
        )
        for item in items
    ]


def _media_read(item: MediaAsset) -> MediaAssetRead:
    return MediaAssetRead.model_validate(
        {**item.__dict__, "metadata": item.metadata_json}
    )


def _price_read(db: Session, item: StorePrice) -> StorePriceRead:
    store_public_id = db.scalar(
        select(Store.public_id).where(
            Store.id == item.store_id,
            Store.tenant_id == item.tenant_id,
        )
    )
    sku_public_id = db.scalar(
        select(SKU.public_id).where(
            SKU.id == item.sku_id,
            SKU.tenant_id == item.tenant_id,
        )
    )
    return StorePriceRead(
        public_id=item.public_id,
        store_public_id=store_public_id or "",
        sku_public_id=sku_public_id or "",
        currency=item.currency,
        price=item.price,
        compare_at_price=item.compare_at_price,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _availability_read(db: Session, item: StoreAvailability) -> StoreAvailabilityRead:
    store_public_id = db.scalar(
        select(Store.public_id).where(
            Store.id == item.store_id,
            Store.tenant_id == item.tenant_id,
        )
    )
    sku_public_id = db.scalar(
        select(SKU.public_id).where(
            SKU.id == item.sku_id,
            SKU.tenant_id == item.tenant_id,
        )
    )
    return StoreAvailabilityRead(
        public_id=item.public_id,
        store_public_id=store_public_id or "",
        sku_public_id=sku_public_id or "",
        availability_status=item.availability_status,
        quantity=item.quantity,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _prices_read(db: Session, items: list[StorePrice]) -> list[StorePriceRead]:
    store_ids = {item.store_id for item in items}
    sku_ids = {item.sku_id for item in items}
    tenant_ids = {item.tenant_id for item in items}
    stores = dict(
        db.execute(
            select(Store.id, Store.public_id).where(
                Store.id.in_(store_ids),
                Store.tenant_id.in_(tenant_ids),
            )
        ).all()
    ) if store_ids else {}
    skus = dict(
        db.execute(
            select(SKU.id, SKU.public_id).where(
                SKU.id.in_(sku_ids),
                SKU.tenant_id.in_(tenant_ids),
            )
        ).all()
    ) if sku_ids else {}
    return [
        StorePriceRead(
            public_id=item.public_id,
            store_public_id=stores.get(item.store_id, ""),
            sku_public_id=skus.get(item.sku_id, ""),
            currency=item.currency,
            price=item.price,
            compare_at_price=item.compare_at_price,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


def _availability_items_read(db: Session, items: list[StoreAvailability]) -> list[StoreAvailabilityRead]:
    store_ids = {item.store_id for item in items}
    sku_ids = {item.sku_id for item in items}
    tenant_ids = {item.tenant_id for item in items}
    stores = dict(
        db.execute(
            select(Store.id, Store.public_id).where(
                Store.id.in_(store_ids),
                Store.tenant_id.in_(tenant_ids),
            )
        ).all()
    ) if store_ids else {}
    skus = dict(
        db.execute(
            select(SKU.id, SKU.public_id).where(
                SKU.id.in_(sku_ids),
                SKU.tenant_id.in_(tenant_ids),
            )
        ).all()
    ) if sku_ids else {}
    return [
        StoreAvailabilityRead(
            public_id=item.public_id,
            store_public_id=stores.get(item.store_id, ""),
            sku_public_id=skus.get(item.sku_id, ""),
            availability_status=item.availability_status,
            quantity=item.quantity,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


# Products ---------------------------------------------------------------------


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    tenant_public_id: str,
    payload: ProductCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        item = _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).create_product(**payload.model_dump())
        return _product_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/products", response_model=ProductPage)
def list_products(
    tenant_public_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    product_type: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductPage:
    try:
        service = _service(
            tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False
        )
        items, total = service.list_products(
            page=page,
            page_size=page_size,
            status=status_filter,
            product_type=product_type,
            brand_public_id=brand,
            category_public_id=category,
            tag_public_id=tag,
            search=search,
        )
        return ProductPage(
            items=_products_read(db, items),
            page=page,
            page_size=page_size,
            total=total,
        )
    except CatalogError as exc:
        _raise(exc)


@router.get("/products/{product_public_id}", response_model=ProductRead)
def read_product(
    tenant_public_id: str,
    product_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        item = _service(
            tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False
        ).get_product(product_public_id)
        return _product_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/products/{product_public_id}", response_model=ProductRead)
def update_product(
    tenant_public_id: str,
    product_public_id: str,
    payload: ProductUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        item = _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).update_product(product_public_id, **payload.model_dump(exclude_unset=True))
        return _product_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/products/{product_public_id}", response_model=ProductRead)
def archive_product(
    tenant_public_id: str,
    product_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        item = _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).archive_product(product_public_id)
        return _product_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.put("/products/{product_public_id}/brand", response_model=ProductRead)
def assign_brand(
    tenant_public_id: str,
    product_public_id: str,
    payload: BrandAssignment,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ProductRead:
    try:
        item = _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).assign_brand(product_public_id, payload.brand_public_id)
        return _product_read(db, item)
    except CatalogError as exc:
        _raise(exc)


def _product_relation(
    tenant_public_id: str,
    product_public_id: str,
    target_public_id: str,
    relation: str,
    attach: bool,
    principal: AuthenticatedPrincipal,
    db: Session,
) -> Response:
    try:
        service = _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        )
        if relation == "category":
            service.set_product_category(product_public_id, target_public_id, attach=attach)
        else:
            service.set_product_tag(product_public_id, target_public_id, attach=attach)
        return Response(status_code=204)
    except CatalogError as exc:
        _raise(exc)


@router.put("/products/{product_public_id}/categories/{category_public_id}", status_code=204)
def assign_category(tenant_public_id: str, product_public_id: str, category_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    return _product_relation(tenant_public_id, product_public_id, category_public_id, "category", True, principal, db)


@router.delete("/products/{product_public_id}/categories/{category_public_id}", status_code=204)
def remove_category(tenant_public_id: str, product_public_id: str, category_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    return _product_relation(tenant_public_id, product_public_id, category_public_id, "category", False, principal, db)


@router.put("/products/{product_public_id}/tags/{tag_public_id}", status_code=204)
def assign_tag(tenant_public_id: str, product_public_id: str, tag_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    return _product_relation(tenant_public_id, product_public_id, tag_public_id, "tag", True, principal, db)


@router.delete("/products/{product_public_id}/tags/{tag_public_id}", status_code=204)
def remove_tag(tenant_public_id: str, product_public_id: str, tag_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    return _product_relation(tenant_public_id, product_public_id, tag_public_id, "tag", False, principal, db)


@router.put("/products/{product_public_id}/attributes/{attribute_public_id}", status_code=204)
def assign_attribute(
    tenant_public_id: str,
    product_public_id: str,
    attribute_public_id: str,
    payload: AttributeAssignment,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> Response:
    try:
        _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).set_product_attribute(
            product_public_id,
            attribute_public_id,
            attach=True,
            **payload.model_dump(),
        )
        return Response(status_code=204)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/products/{product_public_id}/attributes/{attribute_public_id}", status_code=204)
def remove_attribute(tenant_public_id: str, product_public_id: str, attribute_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    try:
        _service(
            tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True
        ).set_product_attribute(product_public_id, attribute_public_id, attach=False)
        return Response(status_code=204)
    except CatalogError as exc:
        _raise(exc)


# Variants and SKUs -------------------------------------------------------------


@router.post("/products/{product_public_id}/variants", response_model=VariantRead, status_code=201)
def create_variant(tenant_public_id: str, product_public_id: str, payload: VariantCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_variant(product_public_id, **payload.model_dump())
        return _variant_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/products/{product_public_id}/variants", response_model=VariantPage)
def list_variants(tenant_public_id: str, product_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantPage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_variants_page(product_public_id, page=page, page_size=page_size)
        return VariantPage(items=_variants_read(db, items), page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/variants/{variant_public_id}", response_model=VariantRead)
def read_variant(tenant_public_id: str, variant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).get_variant(variant_public_id)
        return _variant_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/variants/{variant_public_id}", response_model=VariantRead)
def update_variant(tenant_public_id: str, variant_public_id: str, payload: VariantUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_variant(variant_public_id, **payload.model_dump(exclude_unset=True))
        return _variant_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/variants/{variant_public_id}", response_model=VariantRead)
def archive_variant(tenant_public_id: str, variant_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_variant(variant_public_id, status="archived")
        return _variant_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.put("/variants/{variant_public_id}/options", response_model=VariantRead)
def assign_variant_options(tenant_public_id: str, variant_public_id: str, payload: VariantOptionsUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> VariantRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).replace_variant_options(variant_public_id, payload.option_public_ids)
        return _variant_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.post("/variants/{variant_public_id}/skus", response_model=SkuRead, status_code=201)
def create_sku(tenant_public_id: str, variant_public_id: str, payload: SkuCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> SkuRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_sku(variant_public_id, **payload.model_dump())
        return _sku_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/skus", response_model=SkuPage)
def list_skus(
    tenant_public_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    product: str | None = None,
    variant: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    code: str | None = None,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> SkuPage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_skus(
            page=page, page_size=page_size, product_public_id=product,
            variant_public_id=variant, status=status_filter, code=code,
        )
        return SkuPage(items=_skus_read(db, items), page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/skus/{sku_public_id}", response_model=SkuRead)
def read_sku(tenant_public_id: str, sku_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> SkuRead:
    try:
        return _sku_read(db, _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).get_sku(sku_public_id))
    except CatalogError as exc:
        _raise(exc)


@router.patch("/skus/{sku_public_id}", response_model=SkuRead)
def update_sku(tenant_public_id: str, sku_public_id: str, payload: SkuUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> SkuRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_sku(sku_public_id, **payload.model_dump(exclude_unset=True))
        return _sku_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/skus/{sku_public_id}", response_model=SkuRead)
def archive_sku(tenant_public_id: str, sku_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> SkuRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_sku(sku_public_id, status="archived")
        return _sku_read(db, item)
    except CatalogError as exc:
        _raise(exc)


# Reference data ---------------------------------------------------------------


@router.post("/brands", response_model=BrandRead, status_code=201)
def create_brand(tenant_public_id: str, payload: BrandCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Brand:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_brand(**payload.model_dump())
    except CatalogError as exc:
        _raise(exc)


@router.get("/brands", response_model=BrandPage)
def list_brands(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), status_filter: str | None = Query(default=None, alias="status"), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> BrandPage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_reference(Brand, page=page, page_size=page_size, status=status_filter)
        return BrandPage(items=items, page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/brands/{public_id}", response_model=BrandRead)
def read_brand(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Brand:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)._resource(Brand, public_id)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/brands/{public_id}", response_model=BrandRead)
def update_brand(tenant_public_id: str, public_id: str, payload: BrandUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Brand:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_brand(public_id, **payload.model_dump(exclude_unset=True))
    except CatalogError as exc:
        _raise(exc)


@router.delete("/brands/{public_id}", response_model=BrandRead)
def archive_brand(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Brand:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_brand(public_id, status="archived")
    except CatalogError as exc:
        _raise(exc)


@router.post("/tags", response_model=TagRead, status_code=201)
def create_tag(tenant_public_id: str, payload: NamedReferenceCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tag:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_tag(**payload.model_dump())
    except CatalogError as exc:
        _raise(exc)


@router.get("/tags", response_model=TagPage)
def list_tags(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), status_filter: str | None = Query(default=None, alias="status"), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> TagPage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_reference(Tag, page=page, page_size=page_size, status=status_filter)
        return TagPage(items=items, page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/tags/{public_id}", response_model=TagRead)
def read_tag(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tag:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)._resource(Tag, public_id)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/tags/{public_id}", response_model=TagRead)
def update_tag(tenant_public_id: str, public_id: str, payload: NamedReferenceUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tag:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_tag(public_id, **payload.model_dump(exclude_unset=True))
    except CatalogError as exc:
        _raise(exc)


@router.delete("/tags/{public_id}", response_model=TagRead)
def archive_tag(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Tag:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_tag(public_id, status="archived")
    except CatalogError as exc:
        _raise(exc)


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(tenant_public_id: str, payload: CategoryCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> CategoryRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_category(**payload.model_dump())
        return _category_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/categories", response_model=CategoryPage)
def list_categories(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), parent: str | None = None, status_filter: str | None = Query(default=None, alias="status"), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> CategoryPage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_reference(Category, page=page, page_size=page_size, status=status_filter, parent_public_id=parent)
        return CategoryPage(
            items=_categories_read(db, items),
            page=page,
            page_size=page_size,
            total=total,
        )
    except CatalogError as exc:
        _raise(exc)


@router.get("/categories/{public_id}", response_model=CategoryRead)
def read_category(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> CategoryRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)._resource(Category, public_id)
        return _category_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/categories/{public_id}", response_model=CategoryRead)
def update_category(tenant_public_id: str, public_id: str, payload: CategoryUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> CategoryRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_category(public_id, **payload.model_dump(exclude_unset=True))
        return _category_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/categories/{public_id}", response_model=CategoryRead)
def archive_category(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> CategoryRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_category(public_id, status="archived")
        return _category_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.post("/attributes", response_model=AttributeRead, status_code=201)
def create_attribute(tenant_public_id: str, payload: AttributeCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Attribute:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_attribute(**payload.model_dump())
    except CatalogError as exc:
        _raise(exc)


@router.get("/attributes", response_model=AttributePage)
def list_attributes(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), status_filter: str | None = Query(default=None, alias="status"), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributePage:
    try:
        items, total = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False).list_reference(Attribute, page=page, page_size=page_size, status=status_filter)
        return AttributePage(items=items, page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/attributes/{public_id}", response_model=AttributeRead)
def read_attribute(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Attribute:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)._resource(Attribute, public_id)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/attributes/{public_id}", response_model=AttributeRead)
def update_attribute(tenant_public_id: str, public_id: str, payload: AttributeUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Attribute:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_attribute(public_id, **payload.model_dump(exclude_unset=True))
    except CatalogError as exc:
        _raise(exc)


@router.delete("/attributes/{public_id}", response_model=AttributeRead)
def archive_attribute(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Attribute:
    try:
        return _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_attribute(public_id, status="archived")
    except CatalogError as exc:
        _raise(exc)


@router.post("/attributes/{attribute_public_id}/options", response_model=AttributeOptionRead, status_code=201)
def create_attribute_option(tenant_public_id: str, attribute_public_id: str, payload: AttributeOptionCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributeOptionRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).create_attribute_option(attribute_public_id, **payload.model_dump())
        return _option_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/attributes/{attribute_public_id}/options", response_model=AttributeOptionPage)
def list_attribute_options(tenant_public_id: str, attribute_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributeOptionPage:
    try:
        service = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)
        attribute = service._resource(Attribute, attribute_public_id)
        query = select(AttributeOption).where(AttributeOption.tenant_id == service.tenant_id, AttributeOption.attribute_id == attribute.id, AttributeOption.status != "archived")
        items, total = service._page(query.order_by(AttributeOption.sort_order, AttributeOption.id), db, page=page, page_size=page_size)
        return AttributeOptionPage(
            items=_options_read(db, items),
            page=page,
            page_size=page_size,
            total=total,
        )
    except CatalogError as exc:
        _raise(exc)


@router.get("/attribute-options/{public_id}", response_model=AttributeOptionRead)
def read_attribute_option(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributeOptionRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_READ, principal, db, mutation=False)._resource(AttributeOption, public_id)
        return _option_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.patch("/attribute-options/{public_id}", response_model=AttributeOptionRead)
def update_attribute_option(tenant_public_id: str, public_id: str, payload: AttributeOptionUpdate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributeOptionRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_attribute_option(public_id, **payload.model_dump(exclude_unset=True))
        return _option_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/attribute-options/{public_id}", response_model=AttributeOptionRead)
def archive_attribute_option(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> AttributeOptionRead:
    try:
        item = _service(tenant_public_id, PermissionCode.CATALOG_MANAGE, principal, db, mutation=True).update_attribute_option(public_id, status="archived")
        return _option_read(db, item)
    except CatalogError as exc:
        _raise(exc)


# Media ------------------------------------------------------------------------


@router.post("/media-assets", response_model=MediaAssetRead, status_code=201)
def create_media_asset(tenant_public_id: str, payload: MediaAssetCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> MediaAssetRead:
    try:
        item = _service(tenant_public_id, PermissionCode.MEDIA_MANAGE, principal, db, mutation=True).create_media_asset(**payload.model_dump())
        return _media_read(item)
    except CatalogError as exc:
        _raise(exc)


@router.post("/media/{owner_type}/{owner_public_id}", status_code=204)
def attach_media(tenant_public_id: str, owner_type: MediaOwnerType, owner_public_id: str, payload: MediaAttach, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    try:
        _service(tenant_public_id, PermissionCode.MEDIA_MANAGE, principal, db, mutation=True).attach_media(owner_type=owner_type, owner_public_id=owner_public_id, **payload.model_dump())
        return Response(status_code=204)
    except CatalogError as exc:
        _raise(exc)


@router.delete("/media/{owner_type}/{owner_public_id}/{media_public_id}", status_code=204)
def detach_media(tenant_public_id: str, owner_type: MediaOwnerType, owner_public_id: str, media_public_id: str, role: str = "gallery", principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> Response:
    try:
        _service(tenant_public_id, PermissionCode.MEDIA_MANAGE, principal, db, mutation=True).detach_media(owner_type=owner_type, owner_public_id=owner_public_id, media_public_id=media_public_id, role=role)
        return Response(status_code=204)
    except CatalogError as exc:
        _raise(exc)


@router.get("/media/{owner_type}/{owner_public_id}", response_model=MediaAssociationPage)
def list_media(tenant_public_id: str, owner_type: MediaOwnerType, owner_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> MediaAssociationPage:
    try:
        rows, total = _service(tenant_public_id, PermissionCode.MEDIA_READ, principal, db, mutation=False).list_media_page(owner_type=owner_type, owner_public_id=owner_public_id, page=page, page_size=page_size)
        return MediaAssociationPage(items=[MediaAssociationRead(media=_media_read(media), role=link.role, sort_order=link.sort_order, is_primary=link.is_primary) for media, link in rows], page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


# Store prices and availability ------------------------------------------------


@router.put("/prices", response_model=StorePriceRead)
def upsert_price(tenant_public_id: str, payload: StorePriceUpsert, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StorePriceRead:
    try:
        _allowed_store_ids(
            tenant_public_id,
            PermissionCode.PRICING_MANAGE,
            principal,
            db,
            mutation=True,
            requested_store_public_id=payload.store_public_id,
        )
        item = _service(tenant_public_id, PermissionCode.PRICING_MANAGE, principal, db, mutation=True).upsert_price(**payload.model_dump())
        return _price_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/prices", response_model=StorePricePage)
def list_prices(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), store: str | None = None, sku: str | None = None, currency: str | None = None, active: bool | None = None, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StorePricePage:
    try:
        allowed = _allowed_store_ids(
            tenant_public_id,
            PermissionCode.PRICING_READ,
            principal,
            db,
            mutation=False,
            requested_store_public_id=store,
        )
        items, total = _service(tenant_public_id, PermissionCode.PRICING_READ, principal, db, mutation=False).list_prices(page=page, page_size=page_size, store_public_id=store, sku_public_id=sku, currency=currency, active=active, allowed_store_ids=allowed)
        return StorePricePage(items=_prices_read(db, items), page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/prices/{public_id}", response_model=StorePriceRead)
def read_price(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StorePriceRead:
    try:
        item = _service(tenant_public_id, PermissionCode.PRICING_READ, principal, db, mutation=False).get_price(public_id)
        store_public_id = db.scalar(
            select(Store.public_id).where(
                Store.id == item.store_id,
                Store.tenant_id == item.tenant_id,
            )
        )
        if store_public_id is None:
            raise CatalogNotFoundError("resource not found")
        _allowed_store_ids(
            tenant_public_id,
            PermissionCode.PRICING_READ,
            principal,
            db,
            mutation=False,
            requested_store_public_id=store_public_id,
        )
        return _price_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.put("/availability", response_model=StoreAvailabilityRead)
def upsert_availability(tenant_public_id: str, payload: StoreAvailabilityUpsert, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StoreAvailabilityRead:
    try:
        _allowed_store_ids(
            tenant_public_id,
            PermissionCode.AVAILABILITY_MANAGE,
            principal,
            db,
            mutation=True,
            requested_store_public_id=payload.store_public_id,
        )
        item = _service(tenant_public_id, PermissionCode.AVAILABILITY_MANAGE, principal, db, mutation=True).upsert_availability(**payload.model_dump())
        return _availability_read(db, item)
    except CatalogError as exc:
        _raise(exc)


@router.get("/availability", response_model=StoreAvailabilityPage)
def list_availability(tenant_public_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), store: str | None = None, sku: str | None = None, status_filter: str | None = Query(default=None, alias="status"), principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StoreAvailabilityPage:
    try:
        allowed = _allowed_store_ids(
            tenant_public_id,
            PermissionCode.AVAILABILITY_READ,
            principal,
            db,
            mutation=False,
            requested_store_public_id=store,
        )
        items, total = _service(tenant_public_id, PermissionCode.AVAILABILITY_READ, principal, db, mutation=False).list_availability(page=page, page_size=page_size, store_public_id=store, sku_public_id=sku, status=status_filter, allowed_store_ids=allowed)
        return StoreAvailabilityPage(items=_availability_items_read(db, items), page=page, page_size=page_size, total=total)
    except CatalogError as exc:
        _raise(exc)


@router.get("/availability/{public_id}", response_model=StoreAvailabilityRead)
def read_availability(tenant_public_id: str, public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> StoreAvailabilityRead:
    try:
        item = _service(tenant_public_id, PermissionCode.AVAILABILITY_READ, principal, db, mutation=False).get_availability(public_id)
        store_public_id = db.scalar(
            select(Store.public_id).where(
                Store.id == item.store_id,
                Store.tenant_id == item.tenant_id,
            )
        )
        if store_public_id is None:
            raise CatalogNotFoundError("resource not found")
        _allowed_store_ids(
            tenant_public_id,
            PermissionCode.AVAILABILITY_READ,
            principal,
            db,
            mutation=False,
            requested_store_public_id=store_public_id,
        )
        return _availability_read(db, item)
    except CatalogError as exc:
        _raise(exc)
