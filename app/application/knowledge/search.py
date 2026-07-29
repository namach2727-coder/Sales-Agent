"""Deterministic text matching for the MVP Knowledge Engine."""

from __future__ import annotations

from dataclasses import dataclass

from app.catalog_text import normalize_catalog_text


@dataclass(frozen=True, slots=True)
class Match:
    confidence: float
    match_type: str


def normalize_customer_question(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("customer question must be text")
    if len(value) > 2_000:
        raise ValueError("customer question is too long")
    normalized = normalize_catalog_text(value)
    if not normalized:
        raise ValueError("customer question cannot be blank")
    return normalized


def match_product(
    normalized_question: str,
    *,
    name: str,
    sku_codes: tuple[str, ...],
) -> Match | None:
    normalized_name = normalize_catalog_text(name)
    normalized_skus = tuple(
        item
        for item in (
            normalize_catalog_text(code) for code in sku_codes
        )
        if item
    )
    if normalized_question == normalized_name:
        return Match(1.0, "exact_name")
    if normalized_question in normalized_skus:
        return Match(1.0, "exact_sku")
    if any(_phrase_present(normalized_question, sku) for sku in normalized_skus):
        return Match(0.98, "sku")
    if _phrase_present(normalized_question, normalized_name):
        return Match(0.95, "name")
    if _all_meaningful_tokens_present(
        normalized_question,
        normalized_name,
    ):
        return Match(0.85, "normalized_name")
    return None


def match_knowledge_record(
    normalized_question: str,
    *,
    primary_text: str,
    keywords: tuple[str, ...] = (),
    secondary_texts: tuple[str, ...] = (),
) -> Match | None:
    normalized_primary = normalize_catalog_text(primary_text)
    if normalized_question == normalized_primary:
        return Match(1.0, "exact")
    if _phrase_present(normalized_question, normalized_primary):
        return Match(0.92, "phrase")

    normalized_keywords = tuple(
        normalized
        for normalized in (
            normalize_catalog_text(keyword) for keyword in keywords
        )
        if normalized
    )
    if any(
        _phrase_present(normalized_question, keyword)
        for keyword in normalized_keywords
    ):
        return Match(0.82, "keyword")

    for secondary in secondary_texts:
        normalized_secondary = normalize_catalog_text(secondary)
        if _phrase_present(normalized_question, normalized_secondary):
            return Match(0.75, "related_text")

    if _token_overlap(normalized_question, normalized_primary) >= 0.6:
        return Match(0.65, "normalized_tokens")
    return None


def _phrase_present(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    padded_text = f" {text} "
    return f" {phrase} " in padded_text


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in value.split()
        if len(token) >= 2
    }


def _all_meaningful_tokens_present(question: str, candidate: str) -> bool:
    candidate_tokens = _meaningful_tokens(candidate)
    if not candidate_tokens:
        return False
    return candidate_tokens.issubset(_meaningful_tokens(question))


def _token_overlap(question: str, candidate: str) -> float:
    candidate_tokens = _meaningful_tokens(candidate)
    if not candidate_tokens:
        return 0.0
    return len(
        candidate_tokens & _meaningful_tokens(question)
    ) / len(candidate_tokens)
