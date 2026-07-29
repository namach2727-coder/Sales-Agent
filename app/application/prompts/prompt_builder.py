"""Deterministic construction of provider-agnostic prompt packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable

from app.application.knowledge import (
    BusinessProfileContext,
    BusinessRuleContext,
    FAQContext,
    KnowledgeContext,
    KnowledgeSnippetContext,
    MatchedProductContext,
    SkuContext,
    VariantContext,
)


MESSAGE_DIRECTIONS = frozenset({"inbound", "outbound", "system"})


class PromptBuilderError(Exception):
    code = "prompt_builder_error"


class PromptBuilderValidationError(PromptBuilderError):
    code = "validation_error"


@dataclass(frozen=True, slots=True)
class PromptConversationMessage:
    """Public-only conversation history consumed by the prompt builder."""

    public_id: str
    conversation_public_id: str
    direction: str
    content_type: str
    text: str | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class PromptMetadata:
    """Traceable public references without persistence identifiers."""

    conversation_public_id: str
    preferred_language: str | None
    knowledge_confidence: float
    business_profile_public_id: str | None
    product_public_ids: tuple[str, ...]
    faq_public_ids: tuple[str, ...]
    business_rule_public_ids: tuple[str, ...]
    knowledge_snippet_public_ids: tuple[str, ...]
    recent_message_public_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PromptPackage:
    """Portable input for a future LLM adapter."""

    system_prompt: str
    user_prompt: str
    metadata: PromptMetadata


class PromptBuilder:
    """Render scoped knowledge and conversation state without provider logic."""

    def build(
        self,
        *,
        knowledge_context: KnowledgeContext,
        conversation_public_id: str,
        recent_messages: Iterable[PromptConversationMessage],
        latest_customer_message: str,
        preferred_language: str | None = None,
    ) -> PromptPackage:
        conversation_key = _public_identifier(
            conversation_public_id,
            field="conversation_public_id",
        )
        language = _optional_single_line(
            preferred_language,
            field="preferred_language",
            maximum=32,
        )
        latest_message = _required_text(
            latest_customer_message,
            field="latest_customer_message",
            maximum=10_000,
        )
        _validate_knowledge_scope(knowledge_context, conversation_key)
        _validate_knowledge_public_ids(knowledge_context)
        messages = _validated_messages(
            recent_messages,
            conversation_public_id=conversation_key,
        )
        products = _ordered_products(knowledge_context.matched_products)
        faqs = _ordered_faqs(knowledge_context.faq)
        rules = _ordered_rules(knowledge_context.business_rules)
        snippets = _ordered_snippets(
            knowledge_context.knowledge_snippets
        )

        return PromptPackage(
            system_prompt=_system_prompt(
                profile=knowledge_context.business_profile,
                rules=rules,
                preferred_language=language,
            ),
            user_prompt=_user_prompt(
                messages=messages,
                products=products,
                faqs=faqs,
                snippets=snippets,
                latest_customer_message=latest_message,
            ),
            metadata=PromptMetadata(
                conversation_public_id=conversation_key,
                preferred_language=language,
                knowledge_confidence=knowledge_context.confidence,
                business_profile_public_id=(
                    knowledge_context.business_profile.public_id
                    if knowledge_context.business_profile is not None
                    else None
                ),
                product_public_ids=tuple(
                    product.public_id for product in products
                ),
                faq_public_ids=tuple(item.public_id for item in faqs),
                business_rule_public_ids=tuple(
                    item.public_id for item in rules
                ),
                knowledge_snippet_public_ids=tuple(
                    item.public_id for item in snippets
                ),
                recent_message_public_ids=tuple(
                    message.public_id for message in messages
                ),
            ),
        )


def _system_prompt(
    *,
    profile: BusinessProfileContext | None,
    rules: tuple[BusinessRuleContext, ...],
    preferred_language: str | None,
) -> str:
    lines = [
        "SALES_ASSISTANT_CONTEXT",
        "Use only the supplied business context for business-specific facts.",
        (
            f"Preferred language: {preferred_language}"
            if preferred_language is not None
            else (
                "Preferred language: not specified; follow the language of "
                "the latest customer message."
            )
        ),
        (
            "Communication tone: follow supplied business rules; otherwise "
            "remain clear, respectful, and factual."
        ),
        "",
        "BUSINESS_PROFILE",
    ]
    lines.extend(_profile_lines(profile))
    lines.extend(["", "BUSINESS_RULES"])
    if not rules:
        lines.append("(none supplied)")
    else:
        for index, rule in enumerate(rules, start=1):
            lines.extend(
                [
                    (
                        f"{index}. [{_single_line(rule.policy_type)} / "
                        f"{_single_line(rule.code)}] "
                        f"{_single_line(rule.title)}"
                    ),
                    _indented(rule.content),
                ]
            )
    return "\n".join(lines)


def _profile_lines(
    profile: BusinessProfileContext | None,
) -> list[str]:
    if profile is None:
        return ["(not supplied)"]
    fields = [
        ("Public ID", profile.public_id),
        ("Store identity", profile.display_name),
        ("Business category", profile.business_category),
        ("Description", profile.description),
        ("Support phone", profile.support_phone),
        ("Support email", profile.support_email),
        ("Website", profile.website_url),
        ("Address", profile.address_text),
        ("Working hours", profile.working_hours_text),
    ]
    return [
        f"{label}: {_single_line(value)}"
        for label, value in fields
        if value is not None and value.strip()
    ]


def _user_prompt(
    *,
    messages: tuple[PromptConversationMessage, ...],
    products: tuple[MatchedProductContext, ...],
    faqs: tuple[FAQContext, ...],
    snippets: tuple[KnowledgeSnippetContext, ...],
    latest_customer_message: str,
) -> str:
    lines = ["CONVERSATION_HISTORY"]
    if not messages:
        lines.append("(none supplied)")
    else:
        for index, message in enumerate(messages, start=1):
            content = (
                message.text
                if message.text is not None
                else f"[{message.content_type}]"
            )
            lines.extend(
                [
                    (
                        f"{index}. {_utc_iso(message.occurred_at)} "
                        f"[{message.direction}/{message.content_type}]"
                    ),
                    _indented(content),
                ]
            )

    lines.extend(["", "MATCHED_PRODUCTS"])
    if not products:
        lines.append("(none supplied)")
    else:
        for index, product in enumerate(products, start=1):
            lines.extend(_product_lines(index, product))

    lines.extend(["", "RELEVANT_FAQ"])
    if not faqs:
        lines.append("(none supplied)")
    else:
        for index, item in enumerate(faqs, start=1):
            lines.extend(
                [
                    f"{index}. Question: {_single_line(item.question)}",
                    f"   Answer: {_indented(item.answer, prefix='   ')}",
                ]
            )

    lines.extend(["", "KNOWLEDGE_SNIPPETS"])
    if not snippets:
        lines.append("(none supplied)")
    else:
        for index, item in enumerate(snippets, start=1):
            lines.extend(
                [
                    (
                        f"{index}. [{_single_line(item.entry_type)}] "
                        f"{_single_line(item.title)}"
                    ),
                    _indented(item.content),
                ]
            )

    lines.extend(
        [
            "",
            "LATEST_CUSTOMER_MESSAGE",
            _clean_multiline(latest_customer_message),
        ]
    )
    return "\n".join(lines)


def _product_lines(
    index: int,
    product: MatchedProductContext,
) -> list[str]:
    lines = [
        (
            f"{index}. {_single_line(product.name)} "
            f"(public_id={product.public_id}, "
            f"match={product.match_type}, "
            f"confidence={product.confidence:.2f})"
        )
    ]
    if product.short_description:
        lines.append(
            f"   Short description: {_single_line(product.short_description)}"
        )
    if product.description:
        lines.append(
            f"   Description: {_indented(product.description, prefix='')}"
        )
    if not product.variants:
        lines.append("   Variants: (none supplied)")
        return lines
    lines.append("   Variants:")
    for variant in _ordered_variants(product.variants):
        variant_name = (
            _single_line(variant.name)
            if variant.name is not None
            else "unnamed"
        )
        lines.append(
            f"   - {variant_name} (public_id={variant.public_id})"
        )
        for option in sorted(
            variant.options,
            key=lambda item: (
                item.attribute_code.casefold(),
                item.value.casefold(),
                item.option_public_id,
            ),
        ):
            label = option.display_label or option.value
            lines.append(
                f"     Option {_single_line(option.attribute_name)}: "
                f"{_single_line(label)}"
            )
        if not variant.skus:
            lines.append("     SKUs: (none supplied)")
        for sku in sorted(
            variant.skus,
            key=lambda item: (item.code.casefold(), item.public_id),
        ):
            lines.extend(_sku_lines(sku))
    return lines


def _sku_lines(sku: SkuContext) -> list[str]:
    lines = [
        f"     SKU {_single_line(sku.code)} (public_id={sku.public_id})"
    ]
    if sku.price is None:
        lines.append("       Price: not supplied")
    else:
        value = (
            f"{_decimal(sku.price.amount)} "
            f"{_single_line(sku.price.currency)}"
        )
        if sku.price.compare_at_amount is not None:
            value += (
                f"; compare_at={_decimal(sku.price.compare_at_amount)} "
                f"{_single_line(sku.price.currency)}"
            )
        lines.append(f"       Price: {value}")
    if sku.availability is None:
        lines.append("       Availability: not supplied")
    else:
        quantity = (
            "not supplied"
            if sku.availability.quantity is None
            else str(sku.availability.quantity)
        )
        lines.append(
            "       Availability: "
            f"{_single_line(sku.availability.status)}; "
            f"quantity={quantity}"
        )
    return lines


def _validated_messages(
    messages: Iterable[PromptConversationMessage],
    *,
    conversation_public_id: str,
) -> tuple[PromptConversationMessage, ...]:
    if isinstance(messages, (str, bytes)):
        raise PromptBuilderValidationError(
            "recent_messages must be an iterable of prompt messages"
        )
    try:
        candidates = tuple(messages)
    except TypeError as exc:
        raise PromptBuilderValidationError(
            "recent_messages must be an iterable of prompt messages"
        ) from exc

    validated: list[PromptConversationMessage] = []
    seen_public_ids: set[str] = set()
    for message in candidates:
        if not isinstance(message, PromptConversationMessage):
            raise PromptBuilderValidationError(
                "recent_messages contains an invalid item"
            )
        public_id = _public_identifier(
            message.public_id,
            field="message_public_id",
        )
        message_conversation_id = _public_identifier(
            message.conversation_public_id,
            field="message_conversation_public_id",
        )
        if message_conversation_id != conversation_public_id:
            raise PromptBuilderValidationError(
                "conversation message is outside the requested conversation"
            )
        if public_id in seen_public_ids:
            raise PromptBuilderValidationError(
                "recent_messages contains duplicate public identifiers"
            )
        seen_public_ids.add(public_id)
        direction = _required_single_line(
            message.direction,
            field="message_direction",
            maximum=20,
        )
        if direction not in MESSAGE_DIRECTIONS:
            raise PromptBuilderValidationError(
                "message_direction is invalid"
            )
        content_type = _required_single_line(
            message.content_type,
            field="message_content_type",
            maximum=30,
        )
        text = (
            _required_text(
                message.text,
                field="message_text",
                maximum=10_000,
            )
            if message.text is not None
            else None
        )
        occurred_at = _aware_datetime(
            message.occurred_at,
            field="message_occurred_at",
        )
        validated.append(
            PromptConversationMessage(
                public_id=public_id,
                conversation_public_id=message_conversation_id,
                direction=direction,
                content_type=content_type,
                text=text,
                occurred_at=occurred_at,
            )
        )
    return tuple(
        sorted(
            validated,
            key=lambda item: (
                item.occurred_at.astimezone(UTC),
                item.public_id,
            ),
        )
    )


def _validate_knowledge_scope(
    context: KnowledgeContext,
    conversation_public_id: str,
) -> None:
    if not isinstance(context, KnowledgeContext):
        raise PromptBuilderValidationError(
            "knowledge_context is invalid"
        )
    if (
        context.conversation_public_id is not None
        and _public_identifier(
            context.conversation_public_id,
            field="knowledge_conversation_public_id",
        )
        != conversation_public_id
    ):
        raise PromptBuilderValidationError(
            "knowledge context is outside the requested conversation"
        )


def _validate_knowledge_public_ids(context: KnowledgeContext) -> None:
    if context.business_profile is not None:
        _public_identifier(
            context.business_profile.public_id,
            field="business_profile_public_id",
        )
    for product in context.matched_products:
        _public_identifier(
            product.public_id,
            field="product_public_id",
        )
        for variant in product.variants:
            _public_identifier(
                variant.public_id,
                field="variant_public_id",
            )
            for option in variant.options:
                _public_identifier(
                    option.attribute_public_id,
                    field="attribute_public_id",
                )
                _public_identifier(
                    option.option_public_id,
                    field="option_public_id",
                )
            for sku in variant.skus:
                _public_identifier(
                    sku.public_id,
                    field="sku_public_id",
                )
    for item in context.faq:
        _public_identifier(item.public_id, field="faq_public_id")
    for item in context.business_rules:
        _public_identifier(
            item.public_id,
            field="business_rule_public_id",
        )
    for item in context.knowledge_snippets:
        _public_identifier(
            item.public_id,
            field="knowledge_snippet_public_id",
        )


def _ordered_products(
    values: tuple[MatchedProductContext, ...],
) -> tuple[MatchedProductContext, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -item.confidence,
                item.name.casefold(),
                item.public_id,
            ),
        )
    )


def _ordered_variants(
    values: tuple[VariantContext, ...],
) -> tuple[VariantContext, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                (item.name or "").casefold(),
                item.public_id,
            ),
        )
    )


def _ordered_faqs(
    values: tuple[FAQContext, ...],
) -> tuple[FAQContext, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -item.confidence,
                item.question.casefold(),
                item.public_id,
            ),
        )
    )


def _ordered_rules(
    values: tuple[BusinessRuleContext, ...],
) -> tuple[BusinessRuleContext, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -item.confidence,
                item.policy_type.casefold(),
                item.code.casefold(),
                item.public_id,
            ),
        )
    )


def _ordered_snippets(
    values: tuple[KnowledgeSnippetContext, ...],
) -> tuple[KnowledgeSnippetContext, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -item.confidence,
                item.title.casefold(),
                item.public_id,
            ),
        )
    )


def _public_identifier(value: str, *, field: str) -> str:
    return _required_single_line(value, field=field, maximum=100)


def _optional_single_line(
    value: str | None,
    *,
    field: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    return _required_single_line(value, field=field, maximum=maximum)


def _required_single_line(
    value: str,
    *,
    field: str,
    maximum: int,
) -> str:
    normalized = _required_text(value, field=field, maximum=maximum)
    if "\n" in normalized:
        raise PromptBuilderValidationError(f"{field} must be one line")
    return normalized


def _required_text(
    value: str,
    *,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise PromptBuilderValidationError(f"{field} must be text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise PromptBuilderValidationError(f"{field} cannot be blank")
    if len(normalized) > maximum:
        raise PromptBuilderValidationError(f"{field} is too long")
    if any(
        ord(character) < 32 and character not in "\n\t"
        for character in normalized
    ):
        raise PromptBuilderValidationError(
            f"{field} contains control characters"
        )
    return normalized


def _aware_datetime(value: datetime, *, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise PromptBuilderValidationError(
            f"{field} must be timezone-aware"
        )
    return value


def _single_line(value: str) -> str:
    return " ".join(_clean_multiline(value).splitlines())


def _clean_multiline(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _indented(value: str, *, prefix: str = "   ") -> str:
    return ("\n" + prefix).join(
        line.strip() for line in _clean_multiline(value).splitlines()
    )


def _utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _decimal(value: Decimal) -> str:
    return format(value, "f")
