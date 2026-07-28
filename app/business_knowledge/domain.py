"""Transport-independent rules for store-scoped business knowledge."""

from __future__ import annotations

from collections.abc import Iterable
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


KNOWLEDGE_STATUSES = frozenset({"draft", "published", "archived"})
POLICY_TYPES = frozenset(
    {
        "shipping",
        "returns",
        "refunds",
        "payment",
        "warranty",
        "service",
        "privacy",
        "custom",
    }
)
ENTRY_TYPES = frozenset({"fact", "instruction", "reference", "custom"})
READABLE_STORE_STATUSES = frozenset({"onboarding", "active", "suspended"})
WRITABLE_STORE_STATUSES = frozenset({"onboarding", "active"})

CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HTML_PATTERN = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")
EXECUTABLE_PATTERN = re.compile(
    r"(?:javascript|vbscript|data)\s*:", re.IGNORECASE
)


class BusinessKnowledgeError(Exception):
    code = "business_knowledge_error"


class BusinessKnowledgeValidationError(BusinessKnowledgeError):
    code = "validation_error"


class BusinessKnowledgeConflictError(BusinessKnowledgeError):
    code = "conflict"


class BusinessKnowledgeNotFoundError(BusinessKnowledgeError):
    code = "not_found"


class BusinessKnowledgeStaleWriteError(BusinessKnowledgeError):
    code = "stale_write"


class BusinessKnowledgeInvalidTransitionError(BusinessKnowledgeError):
    code = "invalid_transition"


class BusinessKnowledgeStoreStateError(BusinessKnowledgeError):
    code = "inactive_scope"


def _nfkc(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def reject_markup(value: str) -> None:
    if "\x00" in value or HTML_PATTERN.search(value) or EXECUTABLE_PATTERN.search(value):
        raise BusinessKnowledgeValidationError(
            "HTML and executable markup are not allowed"
        )


def normalize_display_text(
    value: str,
    *,
    field: str,
    maximum: int,
) -> str:
    normalized = " ".join(_nfkc(value).split())
    if not normalized:
        raise BusinessKnowledgeValidationError(f"{field} cannot be blank")
    reject_markup(normalized)
    if len(normalized) > maximum:
        raise BusinessKnowledgeValidationError(f"{field} is too long")
    return normalized


def normalize_optional_display_text(
    value: str | None,
    *,
    field: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    normalized = " ".join(_nfkc(value).split())
    if not normalized:
        return None
    reject_markup(normalized)
    if len(normalized) > maximum:
        raise BusinessKnowledgeValidationError(f"{field} is too long")
    return normalized


def normalize_content(
    value: str,
    *,
    field: str,
    maximum: int = 20_000,
) -> str:
    normalized = _nfkc(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise BusinessKnowledgeValidationError(f"{field} cannot be blank")
    reject_markup(normalized)
    if len(normalized) > maximum:
        raise BusinessKnowledgeValidationError(f"{field} is too long")
    return normalized


def normalize_optional_content(
    value: str | None,
    *,
    field: str,
    maximum: int = 20_000,
) -> str | None:
    if value is None:
        return None
    normalized = _nfkc(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return None
    reject_markup(normalized)
    if len(normalized) > maximum:
        raise BusinessKnowledgeValidationError(f"{field} is too long")
    return normalized


def normalize_code(value: str) -> str:
    normalized = _nfkc(value).strip().lower()
    if not 1 <= len(normalized) <= 100 or CODE_PATTERN.fullmatch(normalized) is None:
        raise BusinessKnowledgeValidationError("invalid policy code")
    return normalized


def normalize_slug(value: str) -> str:
    normalized = _nfkc(value).strip().lower()
    if not 1 <= len(normalized) <= 100 or SLUG_PATTERN.fullmatch(normalized) is None:
        raise BusinessKnowledgeValidationError(
            "slug must contain lowercase letters, numbers and single hyphens"
        )
    return normalized


def normalize_policy_type(value: str) -> str:
    normalized = _nfkc(value).strip().lower()
    if normalized not in POLICY_TYPES:
        raise BusinessKnowledgeValidationError("invalid policy type")
    return normalized


def normalize_entry_type(value: str) -> str:
    normalized = _nfkc(value).strip().lower()
    if normalized not in ENTRY_TYPES:
        raise BusinessKnowledgeValidationError("invalid entry type")
    return normalized


def normalize_status(value: str) -> str:
    normalized = _nfkc(value).strip().lower()
    if normalized not in KNOWLEDGE_STATUSES:
        raise BusinessKnowledgeValidationError("invalid knowledge status")
    return normalized


def normalize_priority(value: int) -> int:
    if value < 0 or value > 10_000:
        raise BusinessKnowledgeValidationError(
            "priority must be between 0 and 10000"
        )
    return value


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _nfkc(value).strip().casefold()
    if not normalized:
        return None
    if len(normalized) > 320 or EMAIL_PATTERN.fullmatch(normalized) is None:
        raise BusinessKnowledgeValidationError("invalid support email")
    return normalized


def normalize_url(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _nfkc(value).strip()
    if not normalized:
        return None
    if len(normalized) > 2048:
        raise BusinessKnowledgeValidationError("website URL is too long")
    reject_markup(normalized)
    parsed = urlsplit(normalized)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise BusinessKnowledgeValidationError("invalid website URL")
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def _ascii_digits(value: str) -> str:
    converted: list[str] = []
    for character in _nfkc(value):
        if character.isdecimal():
            converted.append(str(unicodedata.digit(character)))
        else:
            converted.append(character)
    return "".join(converted)


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _ascii_digits(value).strip()
    if not normalized:
        return None
    leading_plus = normalized.startswith("+")
    if "+" in normalized[1:]:
        raise BusinessKnowledgeValidationError("invalid support phone")
    digits = re.sub(r"[\s().-]", "", normalized[1:] if leading_plus else normalized)
    if not digits.isdigit() or not 7 <= len(digits) <= 20:
        raise BusinessKnowledgeValidationError("invalid support phone")
    return f"+{digits}" if leading_plus else digits


def normalize_keywords(
    values: Iterable[str],
    *,
    maximum_count: int = 25,
    maximum_length: int = 100,
) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str):
            raise BusinessKnowledgeValidationError("keywords must be strings")
        value = normalize_display_text(
            raw,
            field="keyword",
            maximum=maximum_length,
        )
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(value)
        if len(normalized) > maximum_count:
            raise BusinessKnowledgeValidationError("too many keywords")
    return normalized


def normalize_question(value: str) -> tuple[str, str]:
    display = normalize_display_text(value, field="question", maximum=500)
    return display, display.casefold()


def validate_transition(current: str, target: str) -> str:
    current_status = normalize_status(current)
    target_status = normalize_status(target)
    allowed = {
        "draft": {"published", "archived"},
        "published": {"draft", "archived"},
        "archived": {"draft"},
    }
    if target_status not in allowed[current_status]:
        raise BusinessKnowledgeInvalidTransitionError(
            f"cannot transition from {current_status} to {target_status}"
        )
    return target_status
