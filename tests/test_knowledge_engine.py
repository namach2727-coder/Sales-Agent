from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy.orm import Session

from app.application.knowledge import (
    KnowledgeEngine,
    KnowledgeScopeNotFoundError,
)
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
from app.catalog_text import normalize_catalog_text
from app.database import SessionLocal
from app.infrastructure.database.repositories import KnowledgeRepository
from app.models import Store, Tenant


@pytest.fixture
def knowledge_scope():
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:12]
    tenant = Tenant(
        name=f"Knowledge tenant {suffix}",
        slug=f"knowledge-{suffix}",
        status="active",
    )
    db.add(tenant)
    db.flush()
    store = Store(
        tenant_id=tenant.id,
        name=f"Knowledge store {suffix}",
        slug="main",
        status="active",
        currency_code="IRR",
    )
    db.add(store)
    db.flush()
    try:
        yield SimpleNamespace(db=db, tenant=tenant, store=store)
    finally:
        db.rollback()
        db.close()


def _engine(db: Session) -> KnowledgeEngine:
    return KnowledgeEngine(KnowledgeRepository(db))


def _retrieve(scope, question: str, *, store: Store | None = None):
    selected_store = store or scope.store
    return _engine(scope.db).retrieve(
        tenant_public_id=scope.tenant.public_id,
        store_public_id=selected_store.public_id,
        customer_question=question,
    )


def _add_product(
    scope,
    *,
    name: str,
    code: str,
    price: str = "100000",
    quantity: int = 3,
    store: Store | None = None,
    with_color: bool = False,
):
    suffix = uuid.uuid4().hex[:10]
    product = Product(
        tenant_id=scope.tenant.id,
        name=name,
        slug=f"product-{suffix}",
        description=f"Description for {name}",
        short_description=f"Short {name}",
        product_type="physical",
        status="active",
    )
    scope.db.add(product)
    scope.db.flush()
    variant = Variant(
        tenant_id=scope.tenant.id,
        product_id=product.id,
        name="Default",
        combination_key=f"default-{suffix}",
        status="active",
    )
    scope.db.add(variant)
    scope.db.flush()
    sku = SKU(
        tenant_id=scope.tenant.id,
        variant_id=variant.id,
        code=code,
        status="active",
    )
    scope.db.add(sku)
    scope.db.flush()

    selected_store = store or scope.store
    scope.db.add_all(
        [
            StorePrice(
                tenant_id=scope.tenant.id,
                store_id=selected_store.id,
                sku_id=sku.id,
                currency=selected_store.currency_code,
                price=Decimal(price),
                is_active=True,
            ),
            StoreAvailability(
                tenant_id=scope.tenant.id,
                store_id=selected_store.id,
                sku_id=sku.id,
                availability_status=(
                    "out_of_stock" if quantity == 0 else "in_stock"
                ),
                quantity=quantity,
            ),
        ]
    )
    if with_color:
        attribute = Attribute(
            tenant_id=scope.tenant.id,
            name="رنگ",
            code=f"color-{suffix}",
            status="active",
        )
        scope.db.add(attribute)
        scope.db.flush()
        option = AttributeOption(
            tenant_id=scope.tenant.id,
            attribute_id=attribute.id,
            value="سرمه‌ای",
            normalized_value=f"navy-{suffix}",
            display_label="سرمه‌ای",
            status="active",
        )
        scope.db.add(option)
        scope.db.flush()
        scope.db.add(
            VariantOptionValue(
                tenant_id=scope.tenant.id,
                variant_id=variant.id,
                attribute_id=attribute.id,
                attribute_option_id=option.id,
            )
        )
    scope.db.flush()
    return product, variant, sku


def _published_fields() -> dict[str, object]:
    return {
        "status": "published",
        "published_at": datetime.now(UTC),
    }


def test_exact_product_match_returns_store_commerce_context(
    knowledge_scope,
) -> None:
    product, _variant, sku = _add_product(
        knowledge_scope,
        name="مانتو آریا",
        code="ARYA-NAVY-40",
        price="2450000",
        quantity=4,
        with_color=True,
    )

    context = _retrieve(knowledge_scope, "مانتو آریا")

    assert context.confidence == 1.0
    assert len(context.matched_products) == 1
    matched = context.matched_products[0]
    assert matched.public_id == product.public_id
    assert matched.match_type == "exact_name"
    assert matched.variants[0].options[0].value == "سرمه‌ای"
    sku_context = matched.variants[0].skus[0]
    assert sku_context.public_id == sku.public_id
    assert sku_context.price is not None
    assert sku_context.price.amount == Decimal("2450000.00")
    assert sku_context.price.currency == "IRR"
    assert sku_context.availability is not None
    assert sku_context.availability.quantity == 4
    assert "tenant_id" not in asdict(context)
    assert "store_id" not in asdict(context)


def test_sku_match_is_deterministic_and_normalized(knowledge_scope) -> None:
    product, _variant, _sku = _add_product(
        knowledge_scope,
        name="کفش بهار",
        code="SHOE-1403-42",
    )

    context = _retrieve(
        knowledge_scope,
        "لطفاً قیمت shoe 1403 42 را بگویید",
    )

    assert [item.public_id for item in context.matched_products] == [
        product.public_id
    ]
    assert context.matched_products[0].match_type == "sku"
    assert context.matched_products[0].confidence == 0.98


def test_unknown_product_returns_empty_product_matches(
    knowledge_scope,
) -> None:
    _add_product(
        knowledge_scope,
        name="پیراهن تابستانی",
        code="SHIRT-01",
    )

    context = _retrieve(knowledge_scope, "آیا دوچرخه موجود دارید؟")

    assert context.matched_products == ()
    assert context.confidence == 0.0


def test_multiple_products_are_ranked_deterministically(
    knowledge_scope,
) -> None:
    first, _variant, _sku = _add_product(
        knowledge_scope,
        name="مانتو آریا",
        code="ARYA-01",
    )
    second, _variant, _sku = _add_product(
        knowledge_scope,
        name="کفش بهار",
        code="BAHAR-01",
    )

    context = _retrieve(
        knowledge_scope,
        "قیمت مانتو آریا و کفش بهار چنده؟",
    )

    assert {item.public_id for item in context.matched_products} == {
        first.public_id,
        second.public_id,
    }
    assert all(
        item.confidence == 0.95 for item in context.matched_products
    )


def test_tenant_isolation_rejects_cross_tenant_store(
    knowledge_scope,
) -> None:
    suffix = uuid.uuid4().hex[:12]
    other_tenant = Tenant(
        name=f"Other {suffix}",
        slug=f"other-{suffix}",
        status="active",
    )
    knowledge_scope.db.add(other_tenant)
    knowledge_scope.db.flush()
    other_store = Store(
        tenant_id=other_tenant.id,
        name="Other store",
        slug="main",
        status="active",
        currency_code="IRR",
    )
    knowledge_scope.db.add(other_store)
    knowledge_scope.db.flush()

    with pytest.raises(KnowledgeScopeNotFoundError):
        _engine(knowledge_scope.db).retrieve(
            tenant_public_id=knowledge_scope.tenant.public_id,
            store_public_id=other_store.public_id,
            customer_question="هر سوالی",
        )


def test_tenant_catalog_rows_never_cross_scope(knowledge_scope) -> None:
    suffix = uuid.uuid4().hex[:12]
    other_tenant = Tenant(
        name=f"Other catalog {suffix}",
        slug=f"other-catalog-{suffix}",
        status="active",
    )
    knowledge_scope.db.add(other_tenant)
    knowledge_scope.db.flush()
    product = Product(
        tenant_id=other_tenant.id,
        name="محصول محرمانه",
        slug=f"secret-{suffix}",
        product_type="physical",
        status="active",
    )
    knowledge_scope.db.add(product)
    knowledge_scope.db.flush()

    context = _retrieve(knowledge_scope, "محصول محرمانه")

    assert context.matched_products == ()


def test_store_isolation_returns_only_selected_store_price_and_stock(
    knowledge_scope,
) -> None:
    product, _variant, sku = _add_product(
        knowledge_scope,
        name="کت زمستانی",
        code="COAT-01",
        price="3100000",
        quantity=2,
    )
    second_store = Store(
        tenant_id=knowledge_scope.tenant.id,
        name="Branch",
        slug=f"branch-{uuid.uuid4().hex[:8]}",
        status="active",
        currency_code="IRR",
    )
    knowledge_scope.db.add(second_store)
    knowledge_scope.db.flush()
    knowledge_scope.db.add_all(
        [
            StorePrice(
                tenant_id=knowledge_scope.tenant.id,
                store_id=second_store.id,
                sku_id=sku.id,
                currency="IRR",
                price=Decimal("3700000"),
                is_active=True,
            ),
            StoreAvailability(
                tenant_id=knowledge_scope.tenant.id,
                store_id=second_store.id,
                sku_id=sku.id,
                availability_status="low_stock",
                quantity=1,
            ),
        ]
    )
    knowledge_scope.db.flush()

    main = _retrieve(knowledge_scope, product.name)
    branch = _retrieve(
        knowledge_scope,
        product.name,
        store=second_store,
    )

    main_sku = main.matched_products[0].variants[0].skus[0]
    branch_sku = branch.matched_products[0].variants[0].skus[0]
    assert main_sku.price is not None
    assert main_sku.price.amount == Decimal("3100000.00")
    assert main_sku.availability is not None
    assert main_sku.availability.quantity == 2
    assert branch_sku.price is not None
    assert branch_sku.price.amount == Decimal("3700000.00")
    assert branch_sku.availability is not None
    assert branch_sku.availability.quantity == 1


def test_published_business_profile_is_returned(knowledge_scope) -> None:
    profile = BusinessProfile(
        tenant_id=knowledge_scope.tenant.id,
        store_id=knowledge_scope.store.id,
        display_name="فروشگاه نمونه",
        business_category="fashion",
        description="پوشاک ایرانی",
        support_phone="02100000000",
        working_hours_text="شنبه تا چهارشنبه",
        **_published_fields(),
    )
    knowledge_scope.db.add(profile)
    knowledge_scope.db.flush()

    context = _retrieve(knowledge_scope, "ساعت کاری")

    assert context.business_profile is not None
    assert context.business_profile.public_id == profile.public_id
    assert context.business_profile.display_name == "فروشگاه نمونه"
    assert context.business_profile.working_hours_text == "شنبه تا چهارشنبه"


def test_relevant_published_faq_is_returned(knowledge_scope) -> None:
    faq = BusinessFAQ(
        tenant_id=knowledge_scope.tenant.id,
        store_id=knowledge_scope.store.id,
        question="هزینه ارسال چقدر است؟",
        normalized_question=normalize_catalog_text(
            "هزینه ارسال چقدر است؟"
        ),
        answer="ارسال رایگان است.",
        keywords=["ارسال", "هزینه ارسال"],
        priority=10,
        **_published_fields(),
    )
    draft = BusinessFAQ(
        tenant_id=knowledge_scope.tenant.id,
        store_id=knowledge_scope.store.id,
        question="ارسال فوری دارید؟",
        normalized_question=normalize_catalog_text(
            "ارسال فوری دارید؟"
        ),
        answer="این پاسخ نباید منتشر شود.",
        keywords=["ارسال فوری"],
        status="draft",
    )
    knowledge_scope.db.add_all([faq, draft])
    knowledge_scope.db.flush()

    context = _retrieve(knowledge_scope, "هزینه ارسال چقدره؟")

    assert [item.public_id for item in context.faq] == [faq.public_id]
    assert context.faq[0].answer == "ارسال رایگان است."


def test_relevant_business_rules_and_knowledge_are_returned(
    knowledge_scope,
) -> None:
    policy = BusinessPolicy(
        tenant_id=knowledge_scope.tenant.id,
        store_id=knowledge_scope.store.id,
        code="returns",
        policy_type="returns",
        title="شرایط مرجوعی",
        content="کالا تا هفت روز قابل مرجوعی است.",
        priority=10,
        **_published_fields(),
    )
    entry = BusinessKnowledgeEntry(
        tenant_id=knowledge_scope.tenant.id,
        store_id=knowledge_scope.store.id,
        slug="size-guide",
        entry_type="instruction",
        title="راهنمای انتخاب سایز",
        content="دور سینه را اندازه بگیرید.",
        keywords=["سایز", "اندازه"],
        priority=10,
        **_published_fields(),
    )
    knowledge_scope.db.add_all([policy, entry])
    knowledge_scope.db.flush()

    context = _retrieve(
        knowledge_scope,
        "شرایط مرجوعی و راهنمای سایز چیست؟",
    )

    assert [item.public_id for item in context.business_rules] == [
        policy.public_id
    ]
    assert [item.public_id for item in context.knowledge_snippets] == [
        entry.public_id
    ]
    assert context.business_rules[0].content.startswith("کالا")
    assert context.knowledge_snippets[0].entry_type == "instruction"
