from __future__ import annotations

import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.tenancy import RESERVED_STORE_SLUGS, normalize_store_slug


DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
LOCALE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
CURRENCY = re.compile(r"^[A-Z]{3}$")


class TenantManagementError(Exception):
    pass


class ValidationError(TenantManagementError):
    pass


class ConflictError(TenantManagementError):
    pass


class ResourceNotFoundError(TenantManagementError):
    pass


class InvalidTransitionError(TenantManagementError):
    pass


class AccessDeniedError(TenantManagementError):
    pass


def normalize_name(value: str) -> str:
    result = " ".join(value.split())
    if len(result) < 2 or len(result) > 200:
        raise ValidationError("name must contain between 2 and 200 characters")
    return result


def normalize_slug(value: str) -> str:
    try:
        return normalize_store_slug(value)
    except ValueError as exc:
        raise ValidationError("slug is invalid or reserved") from exc


def normalize_subdomain(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    result = value.strip().lower().rstrip(".")
    if result in RESERVED_STORE_SLUGS or DOMAIN_LABEL.fullmatch(result) is None:
        raise ValidationError("subdomain is invalid or reserved")
    return result


def normalize_custom_domain(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    raw = value.strip().lower().rstrip(".")
    if any(item in raw for item in ("://", "/", "\\", "@", ":")) or len(raw) > 253:
        raise ValidationError("custom domain must be a hostname only")
    try:
        ascii_domain = raw.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValidationError("custom domain is invalid") from exc
    labels = ascii_domain.split(".")
    if len(labels) < 2 or any(DOMAIN_LABEL.fullmatch(label) is None for label in labels):
        raise ValidationError("custom domain is invalid")
    return ascii_domain


def normalize_store_settings(timezone: str, locale: str, currency_code: str) -> tuple[str, str, str]:
    timezone = timezone.strip()
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError("timezone is unknown") from exc
    locale = locale.strip()
    currency_code = currency_code.strip().upper()
    if LOCALE.fullmatch(locale) is None:
        raise ValidationError("locale is invalid")
    if CURRENCY.fullmatch(currency_code) is None:
        raise ValidationError("currency code is invalid")
    return timezone, locale, currency_code
