"""Structured, deterministic business context retrieval without AI."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json

from app.application.knowledge.search import (
    Match,
    match_knowledge_record,
    match_product,
    normalize_customer_question,
)
from app.business_knowledge.models import (
    BusinessFAQ,
    BusinessKnowledgeEntry,
    BusinessPolicy,
)
from app.business_knowledge.industry import (
    CUSTOMER_PROVENANCE,
    INDUSTRY_SECTION_LABELS,
    INDUSTRY_PROFILE_SLUG,
    SYSTEM_PROVENANCE,
    allowed_business_types,
    get_industry_schema,
    industry_readiness,
)
from app.infrastructure.database.repositories.knowledge_repository import (
    CatalogProductSnapshot,
    KnowledgeRepository,
)


class KnowledgeEngineError(Exception):
    code = "knowledge_engine_error"


class KnowledgeEngineValidationError(KnowledgeEngineError):
    code = "validation_error"


class KnowledgeScopeNotFoundError(KnowledgeEngineError):
    code = "scope_not_found"


@dataclass(frozen=True, slots=True)
class PriceContext:
    currency: str
    amount: Decimal
    compare_at_amount: Decimal | None


@dataclass(frozen=True, slots=True)
class AvailabilityContext:
    status: str
    quantity: int | None


@dataclass(frozen=True, slots=True)
class VariantOptionContext:
    attribute_public_id: str
    attribute_code: str
    attribute_name: str
    option_public_id: str
    value: str
    display_label: str | None


@dataclass(frozen=True, slots=True)
class SkuContext:
    public_id: str
    code: str
    barcode: str | None
    price: PriceContext | None
    availability: AvailabilityContext | None


@dataclass(frozen=True, slots=True)
class VariantContext:
    public_id: str
    name: str | None
    options: tuple[VariantOptionContext, ...]
    skus: tuple[SkuContext, ...]


@dataclass(frozen=True, slots=True)
class MatchedProductContext:
    public_id: str
    name: str
    description: str | None
    short_description: str | None
    product_type: str
    variants: tuple[VariantContext, ...]
    match_type: str
    confidence: float


@dataclass(frozen=True, slots=True)
class FAQContext:
    public_id: str
    question: str
    answer: str
    confidence: float


@dataclass(frozen=True, slots=True)
class BusinessProfileContext:
    public_id: str
    display_name: str
    business_category: str | None
    description: str | None
    support_phone: str | None
    support_email: str | None
    website_url: str | None
    address_text: str | None
    working_hours_text: str | None


@dataclass(frozen=True, slots=True)
class IndustryAttributeContext:
    key: str
    value: str | tuple[str, ...]
    provenance: str
    label: str | None = None
    section: str | None = None
    value_type: str = "text"


@dataclass(frozen=True, slots=True)
class IndustryProfileContext:
    public_id: str
    industry_code: str
    subcategory: str | None
    attributes: tuple[IndustryAttributeContext, ...]
    provenance: str
    industry_label: str | None = None
    business_type: str = "mixed"
    required_minimum: tuple[str, ...] = ()
    recommended: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    missing_required: tuple[str, ...] = ()
    completion_percent: int = 0
    minimum_met: bool = False
    safety_rules: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BusinessRuleContext:
    public_id: str
    code: str
    policy_type: str
    title: str
    content: str
    confidence: float


@dataclass(frozen=True, slots=True)
class KnowledgeSnippetContext:
    public_id: str
    slug: str
    entry_type: str
    title: str
    content: str
    confidence: float


@dataclass(frozen=True, slots=True)
class KnowledgeContext:
    matched_products: tuple[MatchedProductContext, ...]
    faq: tuple[FAQContext, ...]
    business_profile: BusinessProfileContext | None
    business_rules: tuple[BusinessRuleContext, ...]
    knowledge_snippets: tuple[KnowledgeSnippetContext, ...]
    confidence: float
    conversation_public_id: str | None = None
    industry_profile: IndustryProfileContext | None = None


class KnowledgeEngine:
    """Retrieve a bounded public context snapshot for one store."""

    def __init__(
        self,
        repository: KnowledgeRepository,
        *,
        result_limit: int = 5,
    ) -> None:
        if not 1 <= result_limit <= 20:
            raise KnowledgeEngineValidationError(
                "result_limit must be between 1 and 20"
            )
        self.repository = repository
        self.result_limit = result_limit

    def retrieve(
        self,
        *,
        tenant_public_id: str,
        store_public_id: str,
        customer_question: str,
        conversation_public_id: str | None = None,
    ) -> KnowledgeContext:
        tenant_key = _public_identifier(
            tenant_public_id,
            field="tenant_public_id",
        )
        store_key = _public_identifier(
            store_public_id,
            field="store_public_id",
        )
        conversation_key = (
            _public_identifier(
                conversation_public_id,
                field="conversation_public_id",
            )
            if conversation_public_id is not None
            else None
        )
        try:
            question = normalize_customer_question(customer_question)
        except ValueError as exc:
            raise KnowledgeEngineValidationError(str(exc)) from exc

        scope = self.repository.resolve_active_scope(
            tenant_public_id=tenant_key,
            store_public_id=store_key,
        )
        if scope is None:
            raise KnowledgeScopeNotFoundError(
                "active tenant/store scope was not found"
            )
        snapshot = self.repository.load_snapshot(scope)

        products = self._products(question, snapshot.products)
        faq = self._faq(question, snapshot.faqs)
        rules = self._rules(question, snapshot.policies)
        snippets = self._snippets(question, snapshot.entries)
        industry_profile = self._industry_profile(snapshot.entries)
        profile = (
            BusinessProfileContext(
                public_id=snapshot.profile.public_id,
                display_name=snapshot.profile.display_name,
                business_category=snapshot.profile.business_category,
                description=snapshot.profile.description,
                support_phone=snapshot.profile.support_phone,
                support_email=snapshot.profile.support_email,
                website_url=snapshot.profile.website_url,
                address_text=snapshot.profile.address_text,
                working_hours_text=snapshot.profile.working_hours_text,
            )
            if snapshot.profile is not None
            else None
        )
        confidences = [
            *(item.confidence for item in products),
            *(item.confidence for item in faq),
            *(item.confidence for item in rules),
            *(item.confidence for item in snippets),
        ]
        return KnowledgeContext(
            matched_products=products,
            faq=faq,
            business_profile=profile,
            business_rules=rules,
            knowledge_snippets=snippets,
            confidence=max(confidences, default=0.0),
            conversation_public_id=conversation_key,
            industry_profile=industry_profile,
        )

    @staticmethod
    def _industry_profile(
        items: tuple[BusinessKnowledgeEntry, ...],
    ) -> IndustryProfileContext | None:
        item = next(
            (entry for entry in items if entry.slug == INDUSTRY_PROFILE_SLUG),
            None,
        )
        if item is None:
            return None
        try:
            payload = json.loads(item.content)
            code = str(payload["industry_code"])
            schema = get_industry_schema(code)
            if schema is None:
                return None
            attributes = payload["attributes"]
            provenance = str(payload.get("provenance", CUSTOMER_PROVENANCE))
            subcategory = payload.get("subcategory")
            business_type = str(payload.get("business_type") or schema.business_type)
            if (
                not isinstance(attributes, dict)
                or provenance not in {CUSTOMER_PROVENANCE, SYSTEM_PROVENANCE}
                or (
                    subcategory is not None
                    and str(subcategory) not in schema.subcategories
                )
                or business_type not in allowed_business_types(schema)
            ):
                return None
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            return None
        fields = {field.key: field for field in schema.fields}
        readiness = industry_readiness(
            schema.code,
            attributes,
            str(subcategory) if subcategory is not None else None,
        )
        values: list[IndustryAttributeContext] = []
        for key in sorted(attributes):
            field = fields.get(key)
            if field is None:
                continue
            value = attributes[key]
            if isinstance(value, list):
                value = tuple(str(part) for part in value if str(part).strip())
            elif not isinstance(value, str):
                continue
            if value:
                values.append(
                    IndustryAttributeContext(
                        key=key,
                        value=value,
                        provenance=provenance,
                        label=field.label,
                        section=INDUSTRY_SECTION_LABELS.get(
                            field.section, field.section
                        ),
                        value_type=field.value_type,
                    )
                )
        return IndustryProfileContext(
            public_id=item.public_id,
            industry_code=schema.code,
            subcategory=str(subcategory) if subcategory is not None else None,
            attributes=tuple(values),
            provenance=provenance,
            industry_label=schema.label,
            business_type=business_type,
            required_minimum=readiness.required_minimum,
            recommended=readiness.recommended,
            optional=readiness.optional,
            missing_required=readiness.missing_required,
            completion_percent=readiness.completion_percent,
            minimum_met=readiness.minimum_met,
            safety_rules=schema.safety_rules,
        )

    def _products(
        self,
        question: str,
        products: tuple[CatalogProductSnapshot, ...],
    ) -> tuple[MatchedProductContext, ...]:
        matches: list[tuple[Match, CatalogProductSnapshot]] = []
        for product in products:
            sku_codes = tuple(
                sku.code
                for variant in product.variants
                for sku in variant.skus
            )
            match = match_product(
                question,
                name=product.name,
                sku_codes=sku_codes,
            )
            if match is not None:
                matches.append((match, product))
        matches.sort(
            key=lambda item: (
                -item[0].confidence,
                item[1].name.casefold(),
                item[1].public_id,
            )
        )
        return tuple(
            self._product_context(product, match)
            for match, product in matches[: self.result_limit]
        )

    def _faq(
        self,
        question: str,
        items: tuple[BusinessFAQ, ...],
    ) -> tuple[FAQContext, ...]:
        matches = []
        for item in items:
            match = match_knowledge_record(
                question,
                primary_text=item.normalized_question,
                keywords=tuple(item.keywords),
            )
            if match is not None:
                matches.append((match, item))
        matches.sort(
            key=lambda value: (
                -value[0].confidence,
                value[1].priority,
                value[1].public_id,
            )
        )
        return tuple(
            FAQContext(
                public_id=item.public_id,
                question=item.question,
                answer=item.answer,
                confidence=match.confidence,
            )
            for match, item in matches[: self.result_limit]
        )

    def _rules(
        self,
        question: str,
        items: tuple[BusinessPolicy, ...],
    ) -> tuple[BusinessRuleContext, ...]:
        matches = []
        for item in items:
            match = match_knowledge_record(
                question,
                primary_text=item.title,
                keywords=(item.code, item.policy_type),
                secondary_texts=(item.content,),
            )
            if match is not None:
                matches.append((match, item))
        matches.sort(
            key=lambda value: (
                -value[0].confidence,
                value[1].priority,
                value[1].public_id,
            )
        )
        return tuple(
            BusinessRuleContext(
                public_id=item.public_id,
                code=item.code,
                policy_type=item.policy_type,
                title=item.title,
                content=item.content,
                confidence=match.confidence,
            )
            for match, item in matches[: self.result_limit]
        )

    def _snippets(
        self,
        question: str,
        items: tuple[BusinessKnowledgeEntry, ...],
    ) -> tuple[KnowledgeSnippetContext, ...]:
        matches = []
        for item in items:
            match = match_knowledge_record(
                question,
                primary_text=item.title,
                keywords=tuple(item.keywords),
                secondary_texts=(item.slug, item.content),
            )
            if match is not None:
                matches.append((match, item))
        matches.sort(
            key=lambda value: (
                -value[0].confidence,
                value[1].priority,
                value[1].public_id,
            )
        )
        return tuple(
            KnowledgeSnippetContext(
                public_id=item.public_id,
                slug=item.slug,
                entry_type=item.entry_type,
                title=item.title,
                content=item.content,
                confidence=match.confidence,
            )
            for match, item in matches[: self.result_limit]
        )

    @staticmethod
    def _product_context(
        product: CatalogProductSnapshot,
        match: Match,
    ) -> MatchedProductContext:
        return MatchedProductContext(
            public_id=product.public_id,
            name=product.name,
            description=product.description,
            short_description=product.short_description,
            product_type=product.product_type,
            variants=tuple(
                VariantContext(
                    public_id=variant.public_id,
                    name=variant.name,
                    options=tuple(
                        VariantOptionContext(
                            attribute_public_id=option.attribute_public_id,
                            attribute_code=option.attribute_code,
                            attribute_name=option.attribute_name,
                            option_public_id=option.option_public_id,
                            value=option.value,
                            display_label=option.display_label,
                        )
                        for option in variant.options
                    ),
                    skus=tuple(
                        SkuContext(
                            public_id=sku.public_id,
                            code=sku.code,
                            barcode=sku.barcode,
                            price=(
                                PriceContext(
                                    currency=sku.price.currency,
                                    amount=sku.price.price,
                                    compare_at_amount=(
                                        sku.price.compare_at_price
                                    ),
                                )
                                if sku.price is not None
                                else None
                            ),
                            availability=(
                                AvailabilityContext(
                                    status=sku.availability.status,
                                    quantity=sku.availability.quantity,
                                )
                                if sku.availability is not None
                                else None
                            ),
                        )
                        for sku in variant.skus
                    ),
                )
                for variant in product.variants
            ),
            match_type=match.match_type,
            confidence=match.confidence,
        )


def _public_identifier(value: str, *, field: str) -> str:
    if not isinstance(value, str):
        raise KnowledgeEngineValidationError(f"invalid {field}")
    normalized = value.strip()
    if not normalized or len(normalized) > 100:
        raise KnowledgeEngineValidationError(f"invalid {field}")
    if any(ord(character) < 32 for character in normalized):
        raise KnowledgeEngineValidationError(f"invalid {field}")
    return normalized
