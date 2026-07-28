from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal, PrincipalMembership
from app.authentication.dependencies import require_authenticated_principal
from app.catalog.domain import (
    CatalogConflictError,
    CatalogNotFoundError,
    CatalogUnsafeOperationError,
    CatalogValidationError,
    canonical_combination_key,
)
from app.catalog.models import (
    MediaAsset,
    Product,
    ProductCategory,
    ProductMedia,
    SKU,
    StoreAvailability,
    StorePrice,
    Variant,
)
from app.catalog.router import router
from app.catalog.service import CatalogService
from app.database import get_db
from app.models import (
    AuthTenantRoleAssignment,
    Store,
    Tenant,
    TenantAuditLog,
    TenantMembership,
    UserIdentity,
)
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def catalog_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("foundation06") / "catalog.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


def tenant_context(engine, *, role: str = "tenant_owner"):
    suffix = uuid.uuid4().hex[:10]
    with Session(engine, expire_on_commit=False) as db:
        identity = UserIdentity(
            email=f"{suffix}@example.test",
            normalized_email=f"{suffix}@example.test",
            display_name=f"User {suffix}",
            status="active",
        )
        tenant = Tenant(name=f"Tenant {suffix}", slug=f"tenant-{suffix}", status="active")
        db.add_all([identity, tenant])
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Main",
            slug="main",
            status="active",
            currency_code="IRR",
        )
        membership = TenantMembership(
            user_id=identity.id,
            tenant_id=tenant.id,
            principal_type="user",
            principal_id=str(identity.id),
            status="active",
            all_store_access=True,
        )
        db.add_all([store, membership])
        db.flush()
        if role:
            db.add(
                AuthTenantRoleAssignment(
                    membership_id=membership.id,
                    role_code=role,
                    status="active",
                )
            )
        db.commit()
        principal = AuthenticatedPrincipal(
            user_id=identity.id,
            email=identity.email,
            display_name=identity.display_name,
            session_id=str(uuid.uuid4()),
            authenticated_at=datetime.now(UTC),
            platform_role_codes=(),
            tenant_memberships=(
                PrincipalMembership(
                    membership_id=membership.id,
                    tenant_id=tenant.id,
                    tenant_slug=tenant.slug,
                    status="active",
                    role_codes=(role,) if role else (),
                ),
            ),
        )
        return tenant, store, principal


def test_simple_product_is_atomic_and_supports_all_product_types(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        created = [
            service.create_product(
                name=name,
                slug=slug,
                product_type=product_type,
                status="active",
            )
            for name, slug, product_type in (
                ("Phone", "phone", "physical"),
                ("Guide", "guide", "digital"),
                ("Consultation", "consultation", "service"),
            )
        ]
        variants = list(
            db.scalars(
                select(Variant).where(
                    Variant.tenant_id == tenant.id,
                    Variant.product_id.in_([item.id for item in created]),
                )
            ).all()
        )
        skus = list(
            db.scalars(
                select(SKU).where(
                    SKU.tenant_id == tenant.id,
                    SKU.variant_id.in_([item.id for item in variants]),
                )
            ).all()
        )
        assert {item.product_type for item in created} == {"physical", "digital", "service"}
        assert len(variants) == len(skus) == 3
        assert {item.combination_key for item in variants} == {"default"}
        assert {item.code for item in skus} == {
            "PHONE-DEFAULT",
            "GUIDE-DEFAULT",
            "CONSULTATION-DEFAULT",
        }


def test_normalization_type_lifecycle_and_uniqueness(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        item = service.create_product(
            name="  Apple   iPhone  ",
            slug="iphone-15",
            product_type="PHYSICAL",
            barcode=" ",
        )
        assert item.name == "Apple iPhone" and item.product_type == "physical"
        sku = db.scalar(select(SKU).where(SKU.tenant_id == tenant.id))
        assert sku is not None and sku.barcode is None
        with pytest.raises(CatalogValidationError):
            service.create_product(name=" ", slug="blank", product_type="physical")
        with pytest.raises(CatalogValidationError):
            service.create_product(name="Bad", slug="bad", product_type="bundle")
        with pytest.raises(CatalogConflictError):
            service.create_product(name="Duplicate", slug="iphone-15", product_type="physical")
        service.create_brand(name="Acme", slug="acme")
        with pytest.raises(CatalogConflictError):
            service.create_brand(name="Duplicate Acme", slug="acme")
        archived_brand = service.create_brand(
            name="Archived Brand",
            slug="archived-brand",
            status="archived",
        )
        assert archived_brand.archived_at is not None


def test_variant_combination_is_canonical_and_duplicate_safe(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    assert canonical_combination_key([(2, 20), (1, 10)]) == canonical_combination_key(
        [(1, 10), (2, 20)]
    )
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        product = service.create_product(name="Shirt", slug="shirt", product_type="physical")
        color = service.create_attribute(name="Color", code="color")
        size = service.create_attribute(name="Size", code="size")
        blue = service.create_attribute_option(color.public_id, value="Blue")
        large = service.create_attribute_option(size.public_id, value="Large")
        service.set_product_attribute(product.public_id, color.public_id, attach=True, is_variant_defining=True)
        service.set_product_attribute(product.public_id, size.public_id, attach=True, is_variant_defining=True)
        first = service.create_variant(
            product.public_id,
            name="Blue Large",
            option_public_ids=[blue.public_id, large.public_id],
        )
        assert first.combination_key != "default"
        with pytest.raises(CatalogConflictError):
            service.create_variant(
                product.public_id,
                name="Same combination",
                option_public_ids=[large.public_id, blue.public_id],
            )


def test_attribute_rules_and_unsafe_removal(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    other_tenant, _other_store, _ = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        product = service.create_product(name="Bag", slug="bag", product_type="physical")
        material = service.create_attribute(name="Material", code="material")
        leather = service.create_attribute_option(material.public_id, value="Leather")
        service.set_product_attribute(product.public_id, material.public_id, attach=True, is_variant_defining=True)
        service.create_variant(product.public_id, option_public_ids=[leather.public_id])
        with pytest.raises(CatalogUnsafeOperationError):
            service.set_product_attribute(product.public_id, material.public_id, attach=False)
        foreign = CatalogService(db, tenant_id=other_tenant.id).create_attribute(
            name="Foreign", code="foreign"
        )
        with pytest.raises(CatalogNotFoundError):
            service.set_product_attribute(product.public_id, foreign.public_id, attach=True)


def test_category_hierarchy_prevents_cycles_and_duplicate_assignments(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        root = service.create_category(name="Root", slug="root")
        child = service.create_category(name="Child", slug="child", parent_public_id=root.public_id)
        with pytest.raises(CatalogValidationError):
            service.update_category(root.public_id, parent_public_id=child.public_id)
        product = service.create_product(name="Item", slug="item", product_type="physical")
        service.set_product_category(product.public_id, child.public_id, attach=True)
        service.set_product_category(product.public_id, child.public_id, attach=True)
        assert db.scalar(
            select(ProductCategory).where(
                ProductCategory.product_id == product.id,
                ProductCategory.category_id == child.id,
            )
        ) is not None


def test_brand_tag_media_and_audit(catalog_engine) -> None:
    tenant, _store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        brand = service.create_brand(name="Acme", slug="acme")
        tag = service.create_tag(name="Featured", slug="featured")
        product = service.create_product(name="Camera", slug="camera", product_type="physical")
        service.assign_brand(product.public_id, brand.public_id)
        service.set_product_tag(product.public_id, tag.public_id, attach=True)
        media = service.create_media_asset(
            storage_provider="external",
            storage_key="catalog/camera.jpg",
            original_filename="camera.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            status="ready",
        )
        archived_media = service.create_media_asset(
            storage_provider="external",
            storage_key="catalog/archived-camera.jpg",
            original_filename="archived-camera.jpg",
            mime_type="image/jpeg",
            file_size=128,
            status="archived",
        )
        with pytest.raises(CatalogNotFoundError):
            service.attach_media(
                owner_type="product",
                owner_public_id=product.public_id,
                media_public_id=archived_media.public_id,
            )
        service.attach_media(
            owner_type="product",
            owner_public_id=product.public_id,
            media_public_id=media.public_id,
            is_primary=True,
        )
        second_media = service.create_media_asset(
            storage_provider="external",
            storage_key="catalog/camera-detail.jpg",
            original_filename="camera-detail.jpg",
            mime_type="image/jpeg",
            file_size=512,
            status="ready",
        )
        db.add(
            ProductMedia(
                tenant_id=tenant.id,
                product_id=product.id,
                media_asset_id=second_media.id,
                role="gallery",
                is_primary=True,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        service.detach_media(
            owner_type="product",
            owner_public_id=product.public_id,
            media_public_id=media.public_id,
        )
        assert db.get(MediaAsset, media.id) is not None
        assert db.scalar(select(ProductMedia).where(ProductMedia.product_id == product.id)) is None
        actions = set(
            db.scalars(
                select(TenantAuditLog.action).where(TenantAuditLog.tenant_id == tenant.id)
            ).all()
        )
        assert {
            "catalog.product.created",
            "catalog.product.brand_changed",
            "catalog.media.attached",
            "catalog.media.detached",
        } <= actions


def test_price_and_availability_upsert_validate_state(catalog_engine) -> None:
    tenant, store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        product = service.create_product(name="Book", slug="book", product_type="physical")
        variant = service.list_variants(product.public_id)[0]
        sku = db.scalar(select(SKU).where(SKU.variant_id == variant.id))
        assert sku is not None
        price = service.upsert_price(
            store_public_id=store.public_id,
            sku_public_id=sku.public_id,
            currency="irr",
            price="125.10",
            compare_at_price="150",
        )
        updated = service.upsert_price(
            store_public_id=store.public_id,
            sku_public_id=sku.public_id,
            currency="IRR",
            price=Decimal("120"),
        )
        assert price.id == updated.id and updated.price == Decimal("120.00")
        with pytest.raises(CatalogValidationError):
            service.upsert_price(
                store_public_id=store.public_id,
                sku_public_id=sku.public_id,
                currency="IRR",
                price="100",
                compare_at_price="99",
            )
        availability = service.upsert_availability(
            store_public_id=store.public_id,
            sku_public_id=sku.public_id,
            availability_status="low_stock",
            quantity=2,
        )
        assert availability.quantity == 2
        with pytest.raises(CatalogValidationError):
            service.upsert_availability(
                store_public_id=store.public_id,
                sku_public_id=sku.public_id,
                availability_status="in_stock",
                quantity=0,
            )
        assert db.scalar(select(StorePrice).where(StorePrice.tenant_id == tenant.id)) is not None
        assert db.scalar(select(StoreAvailability).where(StoreAvailability.tenant_id == tenant.id)) is not None


def test_database_constraints_reject_duplicate_sku_and_negative_quantity(catalog_engine) -> None:
    tenant, store, _principal = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service = CatalogService(db, tenant_id=tenant.id)
        product = service.create_product(name="Watch", slug="watch", product_type="physical")
        variant = service.list_variants(product.public_id)[0]
        sku = db.scalar(select(SKU).where(SKU.variant_id == variant.id))
        assert sku is not None
        db.add(SKU(tenant_id=tenant.id, variant_id=variant.id, code=sku.code, status="active"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(
            StoreAvailability(
                tenant_id=tenant.id,
                store_id=store.id,
                sku_id=sku.id,
                availability_status="out_of_stock",
                quantity=-1,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_database_composite_foreign_keys_reject_cross_tenant_relationships(catalog_engine) -> None:
    tenant_a, _store_a, _ = tenant_context(catalog_engine)
    tenant_b, _store_b, _ = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        service_a = CatalogService(db, tenant_id=tenant_a.id)
        service_b = CatalogService(db, tenant_id=tenant_b.id)
        product_a = service_a.create_product(
            name="Tenant A Product", slug="tenant-a-product", product_type="physical"
        )
        brand_b = service_b.create_brand(name="Tenant B Brand", slug="tenant-b-brand")
        product_a.brand_id = brand_b.id
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_cross_tenant_resources_are_indistinguishable_from_missing(catalog_engine) -> None:
    tenant_a, store_a, _ = tenant_context(catalog_engine)
    tenant_b, store_b, _ = tenant_context(catalog_engine)
    with Session(catalog_engine) as db:
        a = CatalogService(db, tenant_id=tenant_a.id)
        b = CatalogService(db, tenant_id=tenant_b.id)
        product_b = b.create_product(name="Secret", slug="secret", product_type="physical")
        variant_b = b.list_variants(product_b.public_id)[0]
        sku_b = db.scalar(select(SKU).where(SKU.variant_id == variant_b.id))
        brand_b = b.create_brand(name="Secret Brand", slug="secret-brand")
        media_b = b.create_media_asset(
            storage_provider="external",
            storage_key="secret.jpg",
            original_filename="secret.jpg",
            mime_type="image/jpeg",
            file_size=1,
        )
        assert sku_b is not None
        operations = (
            lambda: a.get_product(product_b.public_id),
            lambda: a.update_product(product_b.public_id, name="Attack"),
            lambda: a.archive_product(product_b.public_id),
            lambda: a.assign_brand(
                a.create_product(name="Own", slug="own", product_type="physical").public_id,
                brand_b.public_id,
            ),
            lambda: a.upsert_price(
                store_public_id=store_a.public_id,
                sku_public_id=sku_b.public_id,
                currency="IRR",
                price=1,
            ),
            lambda: a.upsert_availability(
                store_public_id=store_b.public_id,
                sku_public_id=sku_b.public_id,
                availability_status="unavailable",
            ),
            lambda: a.attach_media(
                owner_type="product",
                owner_public_id=product_b.public_id,
                media_public_id=media_b.public_id,
            ),
        )
        for operation in operations:
            with pytest.raises(CatalogNotFoundError, match="resource not found"):
                operation()


@pytest.fixture
def catalog_api(catalog_engine):
    tenant, _store, principal = tenant_context(catalog_engine)
    app = FastAPI()
    app.include_router(router)

    def override_db():
        with Session(catalog_engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_authenticated_principal] = lambda: principal
    return TestClient(app), app, tenant, principal


def test_catalog_api_uses_public_ids_pagination_and_permissions(catalog_engine, catalog_api) -> None:
    client, app, tenant, _principal = catalog_api
    created = client.post(
        f"/api/v1/tenants/{tenant.public_id}/catalog/products",
        json={
            "name": "API Product",
            "slug": "api-product",
            "product_type": "service",
            "status": "active",
        },
    )
    assert created.status_code == 201
    assert "id" not in created.json() and "tenant_id" not in created.json()
    public_id = created.json()["public_id"]
    page = client.get(
        f"/api/v1/tenants/{tenant.public_id}/catalog/products?page=1&page_size=1"
    )
    assert page.status_code == 200
    assert page.json()["page_size"] == 1 and page.json()["total"] >= 1
    detail = client.get(
        f"/api/v1/tenants/{tenant.public_id}/catalog/products/{public_id}"
    )
    assert detail.status_code == 200 and detail.json()["public_id"] == public_id

    root = client.post(
        f"/api/v1/tenants/{tenant.public_id}/catalog/categories",
        json={"name": "Root", "slug": "api-root"},
    )
    assert root.status_code == 201
    for index in range(4):
        created_category = client.post(
            f"/api/v1/tenants/{tenant.public_id}/catalog/categories",
            json={
                "name": f"Child {index}",
                "slug": f"api-child-{index}",
                "parent_public_id": root.json()["public_id"],
            },
        )
        assert created_category.status_code == 201

    attribute = client.post(
        f"/api/v1/tenants/{tenant.public_id}/catalog/attributes",
        json={"name": "Color", "code": "api-color"},
    )
    assert attribute.status_code == 201
    for index in range(5):
        created_option = client.post(
            f"/api/v1/tenants/{tenant.public_id}/catalog/attributes/"
            f"{attribute.json()['public_id']}/options",
            json={"value": f"Color {index}"},
        )
        assert created_option.status_code == 201

    def select_count(path: str) -> tuple[int, object]:
        count = 0

        def count_selects(
            _connection,
            _cursor,
            statement,
            _parameters,
            _context,
            _executemany,
        ) -> None:
            nonlocal count
            if statement.lstrip().upper().startswith("SELECT"):
                count += 1

        event.listen(catalog_engine, "before_cursor_execute", count_selects)
        try:
            response = client.get(path)
        finally:
            event.remove(catalog_engine, "before_cursor_execute", count_selects)
        return count, response

    catalog_base = f"/api/v1/tenants/{tenant.public_id}/catalog"
    one_category_queries, one_category = select_count(
        f"{catalog_base}/categories?page=1&page_size=1"
    )
    all_category_queries, all_categories = select_count(
        f"{catalog_base}/categories?page=1&page_size=100"
    )
    assert one_category.status_code == all_categories.status_code == 200
    assert len(all_categories.json()["items"]) == 5
    assert all_category_queries <= one_category_queries + 1

    options_path = (
        f"{catalog_base}/attributes/{attribute.json()['public_id']}/options"
    )
    one_option_queries, one_option = select_count(
        f"{options_path}?page=1&page_size=1"
    )
    all_option_queries, all_options = select_count(
        f"{options_path}?page=1&page_size=100"
    )
    assert one_option.status_code == all_options.status_code == 200
    assert len(all_options.json()["items"]) == 5
    assert all_option_queries <= one_option_queries + 1

    denied_tenant, _store, denied_principal = tenant_context(catalog_engine, role="")
    app.dependency_overrides[require_authenticated_principal] = lambda: denied_principal
    denied = client.post(
        f"/api/v1/tenants/{denied_tenant.public_id}/catalog/products",
        json={"name": "Denied", "slug": "denied", "product_type": "physical"},
    )
    assert denied.status_code == 404


def test_api_hides_cross_tenant_existence(catalog_engine, catalog_api) -> None:
    client, app, tenant_a, principal_a = catalog_api
    tenant_b, _store, principal_b = tenant_context(catalog_engine)
    app.dependency_overrides[require_authenticated_principal] = lambda: principal_b
    created = client.post(
        f"/api/v1/tenants/{tenant_b.public_id}/catalog/products",
        json={"name": "Private", "slug": "private", "product_type": "digital"},
    )
    assert created.status_code == 201
    app.dependency_overrides[require_authenticated_principal] = lambda: principal_a
    guessed = client.get(
        f"/api/v1/tenants/{tenant_a.public_id}/catalog/products/{created.json()['public_id']}"
    )
    foreign_tenant = client.get(
        f"/api/v1/tenants/{tenant_b.public_id}/catalog/products/{created.json()['public_id']}"
    )
    missing = client.get(
        f"/api/v1/tenants/{tenant_a.public_id}/catalog/products/{uuid.uuid4()}"
    )
    assert guessed.status_code == foreign_tenant.status_code == missing.status_code == 404


def test_foundation06_migrates_from_previous_head(tmp_path: Path) -> None:
    path = tmp_path / "from-0005.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "0005_tenant_store_management")
    before = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        assert "catalog_offerings" not in set(inspect(before).get_table_names())
    finally:
        before.dispose()
    command.upgrade(config, "head")
    after = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        assert "catalog_offerings" in set(inspect(after).get_table_names())
    finally:
        after.dispose()
