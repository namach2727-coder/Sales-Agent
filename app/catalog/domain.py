"""Transport-independent validation for the lean business catalog."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import re
import unicodedata


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SKU_PATTERN = re.compile(r"^[A-Z0-9]+(?:[._-][A-Z0-9]+)*$")
LIFECYCLE_STATUSES = frozenset({"draft", "active", "inactive", "archived"})
PRODUCT_TYPES = frozenset({"physical", "digital", "service"})
AVAILABILITY_STATUSES = frozenset(
    {"in_stock", "low_stock", "out_of_stock", "preorder", "unavailable"}
)


class CatalogError(Exception):
    code = "catalog_error"


class CatalogValidationError(CatalogError):
    code = "validation_error"


class CatalogConflictError(CatalogError):
    code = "conflict"


class CatalogNotFoundError(CatalogError):
    code = "not_found"


class CatalogUnsafeOperationError(CatalogError):
    code = "unsafe_operation"


def normalize_name(value: str, *, field: str = "name", maximum: int = 200) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    if not normalized:
        raise CatalogValidationError(f"{field} cannot be blank")
    if len(normalized) > maximum:
        raise CatalogValidationError(f"{field} is too long")
    return normalized


def normalize_optional_text(value: str | None, *, maximum: int | None = None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized:
        return None
    if maximum is not None and len(normalized) > maximum:
        raise CatalogValidationError("text is too long")
    return normalized


def normalize_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    if not 1 <= len(normalized) <= 100 or SLUG_PATTERN.fullmatch(normalized) is None:
        raise CatalogValidationError("slug must contain lowercase letters, numbers and single hyphens")
    return normalized


def normalize_code(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    if not 1 <= len(normalized) <= 100 or CODE_PATTERN.fullmatch(normalized) is None:
        raise CatalogValidationError("code contains unsupported characters")
    return normalized


def normalize_sku(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().upper()
    if not 1 <= len(normalized) <= 100 or SKU_PATTERN.fullmatch(normalized) is None:
        raise CatalogValidationError("SKU code contains unsupported characters")
    return normalized


def normalize_barcode(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).strip()
    return normalized or None


def normalize_lifecycle(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in LIFECYCLE_STATUSES:
        raise CatalogValidationError("invalid lifecycle status")
    return normalized


def normalize_product_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in PRODUCT_TYPES:
        raise CatalogValidationError("invalid product type")
    return normalized


def normalize_option_value(value: str) -> tuple[str, str]:
    display = normalize_name(value, field="option value")
    return display, display.casefold()


def canonical_combination_key(pairs: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> str:
    if not pairs:
        return "default"
    if len({attribute_id for attribute_id, _ in pairs}) != len(pairs):
        raise CatalogValidationError("variant cannot contain two options for one attribute")
    canonical = "|".join(f"{attribute_id}:{option_id}" for attribute_id, option_id in sorted(pairs))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def normalize_currency(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha() or not normalized.isascii():
        raise CatalogValidationError("currency must be a three-letter ISO-style code")
    return normalized


def normalize_money(value: Decimal | int | str, *, field: str) -> Decimal:
    try:
        normalized = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise CatalogValidationError(f"{field} must be a decimal amount") from exc
    if normalized < 0:
        raise CatalogValidationError(f"{field} cannot be negative")
    return normalized


def validate_price(price: Decimal, compare_at_price: Decimal | None) -> None:
    if price < 0:
        raise CatalogValidationError("price cannot be negative")
    if compare_at_price is not None and compare_at_price < price:
        raise CatalogValidationError("compare_at_price cannot be less than price")


def validate_availability(status: str, quantity: int | None) -> tuple[str, int | None]:
    normalized = status.strip().lower()
    if normalized not in AVAILABILITY_STATUSES:
        raise CatalogValidationError("invalid availability status")
    if quantity is not None and quantity < 0:
        raise CatalogValidationError("quantity cannot be negative")
    if quantity == 0 and normalized == "in_stock":
        raise CatalogValidationError("zero quantity cannot be in stock")
    return normalized, quantity


def default_sku_code(slug: str) -> str:
    """Generate the documented deterministic SKU for a simple product."""

    return normalize_sku(f"{normalize_slug(slug).replace('-', '_')}-DEFAULT")
