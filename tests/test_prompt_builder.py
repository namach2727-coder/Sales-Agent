from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.application.knowledge import (
    AvailabilityContext,
    BusinessProfileContext,
    BusinessRuleContext,
    FAQContext,
    KnowledgeContext,
    KnowledgeSnippetContext,
    MatchedProductContext,
    PriceContext,
    SkuContext,
    VariantContext,
    VariantOptionContext,
)
from app.application.prompts import (
    PromptBuilder,
    PromptBuilderValidationError,
    PromptConversationMessage,
    PromptPackage,
)


CONVERSATION_ID = "00000000-0000-4000-8000-000000000001"


def _knowledge(
    *,
    conversation_public_id: str | None = CONVERSATION_ID,
    products: tuple[MatchedProductContext, ...] = (),
    faq: tuple[FAQContext, ...] = (),
    profile: BusinessProfileContext | None = None,
    rules: tuple[BusinessRuleContext, ...] = (),
    snippets: tuple[KnowledgeSnippetContext, ...] = (),
    confidence: float = 0.0,
) -> KnowledgeContext:
    return KnowledgeContext(
        matched_products=products,
        faq=faq,
        business_profile=profile,
        business_rules=rules,
        knowledge_snippets=snippets,
        confidence=confidence,
        conversation_public_id=conversation_public_id,
    )


def _profile(
    *,
    public_id: str = "00000000-0000-4000-8000-000000000010",
    display_name: str = "فروشگاه آریا",
) -> BusinessProfileContext:
    return BusinessProfileContext(
        public_id=public_id,
        display_name=display_name,
        business_category="fashion",
        description="فروش پوشاک ایرانی",
        support_phone="02100000000",
        support_email="support@example.test",
        website_url="https://example.test",
        address_text="تهران",
        working_hours_text="شنبه تا چهارشنبه",
    )


def _product(
    *,
    public_id: str = "00000000-0000-4000-8000-000000000020",
    name: str = "مانتو آریا",
    confidence: float = 0.95,
    price: str = "2450000",
) -> MatchedProductContext:
    return MatchedProductContext(
        public_id=public_id,
        name=name,
        description=f"توضیحات {name}",
        short_description=f"خلاصه {name}",
        product_type="physical",
        match_type="name",
        confidence=confidence,
        variants=(
            VariantContext(
                public_id=f"{public_id[:-1]}1",
                name="سرمه‌ای - ۴۰",
                options=(
                    VariantOptionContext(
                        attribute_public_id=f"{public_id[:-1]}2",
                        attribute_code="color",
                        attribute_name="رنگ",
                        option_public_id=f"{public_id[:-1]}3",
                        value="navy",
                        display_label="سرمه‌ای",
                    ),
                ),
                skus=(
                    SkuContext(
                        public_id=f"{public_id[:-1]}4",
                        code=f"SKU-{public_id[-2:]}",
                        barcode=None,
                        price=PriceContext(
                            currency="IRR",
                            amount=Decimal(price),
                            compare_at_amount=None,
                        ),
                        availability=AvailabilityContext(
                            status="in_stock",
                            quantity=3,
                        ),
                    ),
                ),
            ),
        ),
    )


def _message(
    *,
    public_id: str,
    minute: int,
    text: str,
    direction: str = "inbound",
    conversation_public_id: str = CONVERSATION_ID,
) -> PromptConversationMessage:
    return PromptConversationMessage(
        public_id=public_id,
        conversation_public_id=conversation_public_id,
        direction=direction,
        content_type="text",
        text=text,
        occurred_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC)
        + timedelta(minutes=minute),
    )


def _build(
    knowledge: KnowledgeContext,
    *,
    messages: tuple[PromptConversationMessage, ...] = (),
    latest: str = "قیمت مانتو چنده؟",
    conversation_public_id: str = CONVERSATION_ID,
):
    return PromptBuilder().build(
        knowledge_context=knowledge,
        conversation_public_id=conversation_public_id,
        recent_messages=messages,
        latest_customer_message=latest,
        preferred_language="fa-IR",
    )


def test_prompt_generation_uses_profile_rules_language_and_latest_message(
) -> None:
    rule = BusinessRuleContext(
        public_id="00000000-0000-4000-8000-000000000030",
        code="returns",
        policy_type="returns",
        title="شرایط مرجوعی",
        content="مرجوعی تا هفت روز امکان‌پذیر است.",
        confidence=0.9,
    )

    package = _build(
        _knowledge(
            profile=_profile(),
            rules=(rule,),
            confidence=0.9,
        ),
        latest="شرایط مرجوعی چیست؟",
    )

    assert isinstance(package, PromptPackage)
    assert "Preferred language: fa-IR" in package.system_prompt
    assert "Store identity: فروشگاه آریا" in package.system_prompt
    assert "شرایط مرجوعی" in package.system_prompt
    assert "مرجوعی تا هفت روز" in package.system_prompt
    assert package.user_prompt.endswith("شرایط مرجوعی چیست؟")
    assert package.metadata.business_rule_public_ids == (rule.public_id,)


def test_ordering_is_deterministic_for_all_repeated_inputs() -> None:
    alpha = _product(
        public_id="00000000-0000-4000-8000-000000000041",
        name="محصول الف",
        confidence=0.8,
    )
    beta = _product(
        public_id="00000000-0000-4000-8000-000000000042",
        name="محصول ب",
        confidence=0.9,
    )
    faq_a = FAQContext(
        public_id="00000000-0000-4000-8000-000000000043",
        question="پرسش الف",
        answer="پاسخ الف",
        confidence=0.7,
    )
    faq_b = FAQContext(
        public_id="00000000-0000-4000-8000-000000000044",
        question="پرسش ب",
        answer="پاسخ ب",
        confidence=0.9,
    )
    early = _message(
        public_id="00000000-0000-4000-8000-000000000045",
        minute=1,
        text="اول",
    )
    late = _message(
        public_id="00000000-0000-4000-8000-000000000046",
        minute=2,
        text="دوم",
        direction="outbound",
    )
    one = _build(
        _knowledge(
            products=(alpha, beta),
            faq=(faq_a, faq_b),
            confidence=0.9,
        ),
        messages=(late, early),
    )
    two = _build(
        _knowledge(
            products=(beta, alpha),
            faq=(faq_b, faq_a),
            confidence=0.9,
        ),
        messages=(early, late),
    )

    assert one == two
    assert one.user_prompt.index("اول") < one.user_prompt.index("دوم")
    assert one.user_prompt.index("محصول ب") < one.user_prompt.index(
        "محصول الف"
    )
    assert one.user_prompt.index("پرسش ب") < one.user_prompt.index(
        "پرسش الف"
    )


def test_matched_product_price_stock_variants_and_sku_are_included() -> None:
    product = _product()

    package = _build(
        _knowledge(products=(product,), confidence=product.confidence)
    )

    assert product.name in package.user_prompt
    assert "SKU-20" in package.user_prompt
    assert "2450000 IRR" in package.user_prompt
    assert "in_stock; quantity=3" in package.user_prompt
    assert "Option رنگ: سرمه‌ای" in package.user_prompt
    assert package.metadata.product_public_ids == (product.public_id,)


def test_faq_and_knowledge_snippets_are_included() -> None:
    faq = FAQContext(
        public_id="00000000-0000-4000-8000-000000000050",
        question="هزینه ارسال چقدر است؟",
        answer="ارسال رایگان است.",
        confidence=0.8,
    )
    snippet = KnowledgeSnippetContext(
        public_id="00000000-0000-4000-8000-000000000051",
        slug="size-guide",
        entry_type="instruction",
        title="راهنمای سایز",
        content="دور سینه را اندازه بگیرید.",
        confidence=0.75,
    )

    package = _build(
        _knowledge(
            faq=(faq,),
            snippets=(snippet,),
            confidence=0.8,
        )
    )

    assert faq.question in package.user_prompt
    assert faq.answer in package.user_prompt
    assert snippet.title in package.user_prompt
    assert snippet.content in package.user_prompt
    assert package.metadata.faq_public_ids == (faq.public_id,)
    assert package.metadata.knowledge_snippet_public_ids == (
        snippet.public_id,
    )


def test_conversation_history_is_sorted_and_included() -> None:
    first = _message(
        public_id="00000000-0000-4000-8000-000000000060",
        minute=1,
        text="سلام",
    )
    second = _message(
        public_id="00000000-0000-4000-8000-000000000061",
        minute=2,
        text="سلام، چطور کمکتان کنم؟",
        direction="outbound",
    )

    package = _build(
        _knowledge(),
        messages=(second, first),
    )

    assert package.user_prompt.index("سلام\n") < package.user_prompt.index(
        "سلام، چطور"
    )
    assert package.metadata.recent_message_public_ids == (
        first.public_id,
        second.public_id,
    )


def test_empty_knowledge_produces_a_valid_factual_package() -> None:
    package = _build(_knowledge(), latest="سلام")

    assert "BUSINESS_PROFILE\n(not supplied)" in package.system_prompt
    assert "BUSINESS_RULES\n(none supplied)" in package.system_prompt
    assert package.user_prompt.count("(none supplied)") == 4
    assert package.metadata.product_public_ids == ()
    assert package.metadata.faq_public_ids == ()
    assert package.metadata.business_profile_public_id is None
    assert package.metadata.knowledge_confidence == 0.0


def test_tenant_isolation_rejects_cross_conversation_knowledge() -> None:
    other_conversation = "00000000-0000-4000-8000-000000000070"
    context = _knowledge(
        conversation_public_id=other_conversation,
        profile=_profile(display_name="فروشگاه tenant دیگر"),
    )

    with pytest.raises(
        PromptBuilderValidationError,
        match="knowledge context is outside",
    ):
        _build(context)


def test_store_isolation_rejects_cross_conversation_history() -> None:
    foreign_message = _message(
        public_id="00000000-0000-4000-8000-000000000071",
        minute=1,
        text="پیام فروشگاه دیگر",
        conversation_public_id=(
            "00000000-0000-4000-8000-000000000072"
        ),
    )

    with pytest.raises(
        PromptBuilderValidationError,
        match="outside the requested conversation",
    ):
        _build(_knowledge(), messages=(foreign_message,))


def test_builder_is_stateless_across_isolated_store_contexts() -> None:
    builder = PromptBuilder()
    first = builder.build(
        knowledge_context=_knowledge(
            profile=_profile(display_name="فروشگاه اول"),
            products=(
                _product(
                    name="محصول فروشگاه اول",
                    public_id="00000000-0000-4000-8000-000000000080",
                ),
            ),
        ),
        conversation_public_id=CONVERSATION_ID,
        recent_messages=(),
        latest_customer_message="قیمت؟",
    )
    second_conversation = "00000000-0000-4000-8000-000000000081"
    second = builder.build(
        knowledge_context=_knowledge(
            conversation_public_id=second_conversation,
            profile=_profile(
                public_id="00000000-0000-4000-8000-000000000082",
                display_name="فروشگاه دوم",
            ),
            products=(
                _product(
                    name="محصول فروشگاه دوم",
                    public_id="00000000-0000-4000-8000-000000000083",
                ),
            ),
        ),
        conversation_public_id=second_conversation,
        recent_messages=(),
        latest_customer_message="قیمت؟",
    )

    assert "فروشگاه دوم" not in first.system_prompt
    assert "محصول فروشگاه دوم" not in first.user_prompt
    assert "فروشگاه اول" not in second.system_prompt
    assert "محصول فروشگاه اول" not in second.user_prompt


def test_metadata_is_immutable_public_only_and_provider_agnostic() -> None:
    product = _product()
    message = _message(
        public_id="00000000-0000-4000-8000-000000000090",
        minute=1,
        text="سلام",
    )
    package = _build(
        _knowledge(
            profile=_profile(),
            products=(product,),
            confidence=0.95,
        ),
        messages=(message,),
    )

    metadata = asdict(package.metadata)
    identifier_fields = {
        key: value
        for key, value in metadata.items()
        if key.endswith("_public_id") or key.endswith("_public_ids")
    }
    for value in identifier_fields.values():
        values = value if isinstance(value, tuple) else (value,)
        assert all(
            item is None or (isinstance(item, str) and "-" in item)
            for item in values
        )
    assert not any(
        key in metadata
        for key in (
            "tenant_id",
            "store_id",
            "conversation_id",
            "product_id",
            "model",
            "temperature",
            "token_limit",
        )
    )
    assert {item.name for item in fields(PromptPackage)} == {
        "system_prompt",
        "user_prompt",
        "metadata",
    }
    with pytest.raises(FrozenInstanceError):
        package.metadata.conversation_public_id = "changed"
