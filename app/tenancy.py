from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import Store, StoreInstagramConnection


STORE_SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
CORRELATION_ID_HEADER = "x-correlation-id"
INACTIVE_STORE_STATUSES = frozenset({"deleted", "disabled", "suspended"})
RESERVED_STORE_SLUGS = {
    "admin",
    "api",
    "app",
    "auth",
    "docs",
    "health",
    "internal",
    "login",
    "logout",
    "static",
    "media",
    "openapi",
    "public",
    "system",
    "webhook",
    "webhooks",
    "www",
}


class TenantResolutionSource(str, Enum):
    SUBDOMAIN = "subdomain"
    CONNECTOR = "connector"
    SESSION = "session"
    EXPLICIT_INTERNAL = "explicit_internal"
    DEVELOPMENT_DEFAULT = "development_default"


class TenantActorType(str, Enum):
    USER = "user"
    CONNECTOR = "connector"
    SYSTEM = "system"
    ANONYMOUS = "anonymous"


class TenantConnectorType(str, Enum):
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    MANYCHAT = "manychat"


@dataclass(frozen=True, slots=True)
class TenantActor:
    id: str | None
    type: TenantActorType
    role: str | None = None

    def to_safe_dict(self) -> dict[str, str | None]:
        return {"id": self.id, "type": self.type.value, "role": self.role}


@dataclass(frozen=True, slots=True)
class TenantConnector:
    type: TenantConnectorType | None = None
    connection_id: int | None = None
    account_id: str | None = None

    def to_safe_dict(self) -> dict[str, str | int | None]:
        return {
            "type": self.type.value if self.type else None,
            "connection_id": self.connection_id,
            "account_id": self.account_id,
        }


@dataclass(frozen=True, slots=True)
class TenantContext:
    store_id: int
    store_slug: str
    store_status: str
    resolution_source: TenantResolutionSource
    actor: TenantActor
    membership_id: int | None
    connector: TenantConnector
    correlation_id: str
    is_default_fallback: bool = False

    def __post_init__(self) -> None:
        if not self.correlation_id:
            raise ValueError("correlation_id is required")

    def to_safe_dict(self) -> dict[str, Any]:
        """Return credential-free primitives suitable for structured logs."""

        return {
            "store_id": self.store_id,
            "store_slug": self.store_slug,
            "store_status": self.store_status,
            "resolution_source": self.resolution_source.value,
            "actor": self.actor.to_safe_dict(),
            "membership_id": self.membership_id,
            "connector": self.connector.to_safe_dict(),
            "correlation_id": self.correlation_id,
            "is_default_fallback": self.is_default_fallback,
        }


class TenantResolutionError(Exception):
    """Base domain error; route adapters decide what is safe to disclose."""


class UnknownTenantError(TenantResolutionError):
    pass


class InactiveTenantError(TenantResolutionError):
    pass


class UnknownConnectorAccountError(TenantResolutionError):
    pass


class AmbiguousTenantMappingError(TenantResolutionError):
    pass


class InvalidTenantHostError(TenantResolutionError):
    pass


class UntrustedExplicitTenantError(TenantResolutionError):
    pass


class SessionTenantResolutionUnavailableError(TenantResolutionError):
    pass


def tenant_resolution_http_exception(error: TenantResolutionError) -> HTTPException:
    """Translate domain failures without confirming that a hidden store exists."""

    if isinstance(error, UntrustedExplicitTenantError):
        return HTTPException(status_code=403, detail="Tenant selection is not allowed")
    if isinstance(error, SessionTenantResolutionUnavailableError):
        return HTTPException(status_code=503, detail="Tenant session resolution is unavailable")
    return HTTPException(status_code=404, detail="Tenant could not be resolved")


def normalize_correlation_id(value: str | None = None) -> str:
    candidate = (value or "").strip()
    if candidate and CORRELATION_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def correlation_id_from_request(request: Request) -> str:
    return normalize_correlation_id(request.headers.get(CORRELATION_ID_HEADER))


def normalize_store_slug(value: str) -> str:
    slug = value.strip().lower()
    if (
        not STORE_SLUG_PATTERN.fullmatch(slug)
        or "--" in slug
        or slug in RESERVED_STORE_SLUGS
    ):
        raise ValueError(
            "ساب‌دامنه باید فقط شامل حروف انگلیسی کوچک، عدد یا خط تیره باشد."
        )
    return slug


def _hostname_from_host_header(host: str) -> str:
    raw_host = host.strip().lower()
    if (
        not raw_host
        or len(raw_host) > 255
        or any(character in raw_host for character in ("\r", "\n", "/", "\\", " "))
    ):
        return ""
    if raw_host.startswith("[") and "]" in raw_host:
        hostname = raw_host[1 : raw_host.index("]")]
    elif raw_host.count(":") == 1:
        hostname = raw_host.rsplit(":", 1)[0]
    else:
        hostname = raw_host
    return hostname.rstrip(".")


def parse_tenant_slug(host: str, settings: Settings) -> str | None:
    hostname = _hostname_from_host_header(host)
    if hostname in {"localhost", "127.0.0.1", "::1", "testserver", "testclient"}:
        return "default" if settings.app_env == "development" else None
    if hostname.endswith(".localhost") and settings.app_env == "development":
        candidate = hostname[: -len(".localhost")]
        if "." not in candidate:
            try:
                return normalize_store_slug(candidate)
            except ValueError:
                return None
    base = settings.tenant_base_domain.strip().lower().strip(".")
    if base and hostname.endswith(f".{base}"):
        candidate = hostname[: -(len(base) + 1)]
        if candidate and "." not in candidate:
            try:
                return normalize_store_slug(candidate)
            except ValueError:
                return None
    return None


def _strict_store_by_slug(db: Session, slug: str) -> Store:
    store = db.scalar(select(Store).where(Store.slug == slug))
    if store is None:
        raise UnknownTenantError
    if store.status in INACTIVE_STORE_STATUSES:
        raise InactiveTenantError
    return store


def _context(
    store: Store,
    *,
    source: TenantResolutionSource,
    correlation_id: str | None,
    actor: TenantActor,
    connector: TenantConnector | None = None,
    membership_id: int | None = None,
    is_default_fallback: bool = False,
) -> TenantContext:
    return TenantContext(
        store_id=store.id,
        store_slug=store.slug,
        store_status=store.status,
        resolution_source=source,
        actor=actor,
        membership_id=membership_id,
        connector=connector or TenantConnector(),
        correlation_id=normalize_correlation_id(correlation_id),
        is_default_fallback=is_default_fallback,
    )


def resolve_tenant_from_host(
    db: Session,
    host: str,
    settings: Settings,
    *,
    correlation_id: str | None = None,
) -> TenantContext:
    hostname = _hostname_from_host_header(host)
    if not hostname:
        raise InvalidTenantHostError
    slug = parse_tenant_slug(host, settings)
    if not slug:
        raise InvalidTenantHostError
    store = _strict_store_by_slug(db, slug)
    is_development_default = (
        settings.app_env == "development"
        and slug == "default"
        and hostname in {"localhost", "127.0.0.1", "::1", "testserver", "testclient"}
    )
    return _context(
        store,
        source=(
            TenantResolutionSource.DEVELOPMENT_DEFAULT
            if is_development_default
            else TenantResolutionSource.SUBDOMAIN
        ),
        correlation_id=correlation_id,
        actor=TenantActor(id=None, type=TenantActorType.ANONYMOUS),
        is_default_fallback=is_development_default,
    )


def resolve_tenant_from_request(
    request: Request,
    db: Session,
    settings: Settings,
) -> TenantContext:
    """Resolve only from Host; query, body and tenant-like headers are ignored."""

    return resolve_tenant_from_host(
        db,
        request.headers.get("host", ""),
        settings,
        correlation_id=correlation_id_from_request(request),
    )


def resolve_instagram_tenant(
    db: Session,
    account_id: str,
    settings: Settings,
    *,
    correlation_id: str | None = None,
    allow_development_default_fallback: bool = False,
) -> TenantContext:
    normalized_account_id = account_id.strip()
    if not normalized_account_id:
        raise UnknownConnectorAccountError
    connections = list(
        db.scalars(
            select(StoreInstagramConnection)
            .options(joinedload(StoreInstagramConnection.store))
            .where(StoreInstagramConnection.ig_user_id == normalized_account_id)
        ).all()
    )
    if len(connections) > 1:
        raise AmbiguousTenantMappingError
    if connections:
        connection = connections[0]
        if connection.status != "active":
            raise UnknownConnectorAccountError
        store = connection.store
        if store is None:
            raise UnknownTenantError
        if store.status in INACTIVE_STORE_STATUSES:
            raise InactiveTenantError
        return _context(
            store,
            source=TenantResolutionSource.CONNECTOR,
            correlation_id=correlation_id,
            actor=TenantActor(
                id=normalized_account_id,
                type=TenantActorType.CONNECTOR,
                role="instagram_webhook",
            ),
            connector=TenantConnector(
                type=TenantConnectorType.INSTAGRAM,
                connection_id=connection.id,
                account_id=normalized_account_id,
            ),
        )
    if (
        allow_development_default_fallback
        and settings.app_env == "development"
        and settings.meta_ig_user_id.strip() == normalized_account_id
    ):
        store = _strict_store_by_slug(db, "default")
        return _context(
            store,
            source=TenantResolutionSource.DEVELOPMENT_DEFAULT,
            correlation_id=correlation_id,
            actor=TenantActor(
                id=normalized_account_id,
                type=TenantActorType.CONNECTOR,
                role="instagram_webhook",
            ),
            connector=TenantConnector(
                type=TenantConnectorType.INSTAGRAM,
                account_id=normalized_account_id,
            ),
            is_default_fallback=True,
        )
    raise UnknownConnectorAccountError


def resolve_explicit_internal_tenant(
    db: Session,
    store_slug: str,
    *,
    trusted: bool,
    correlation_id: str | None = None,
    actor_id: str | None = None,
) -> TenantContext:
    if not trusted:
        raise UntrustedExplicitTenantError
    try:
        normalized_slug = normalize_store_slug(store_slug)
    except ValueError as exc:
        raise UnknownTenantError from exc
    store = _strict_store_by_slug(db, normalized_slug)
    return _context(
        store,
        source=TenantResolutionSource.EXPLICIT_INTERNAL,
        correlation_id=correlation_id,
        actor=TenantActor(id=actor_id, type=TenantActorType.SYSTEM),
    )


def resolve_session_tenant(*_: Any, **__: Any) -> TenantContext:
    raise SessionTenantResolutionUnavailableError


# Backward-compatible wrappers used by the current MVP. They intentionally keep
# their historical HTTP behavior until routes migrate to TenantContext.
def store_by_slug(db: Session, slug: str) -> Store:
    store = db.scalar(select(Store).where(Store.slug == slug))
    if store is None or store.status in {"deleted", "disabled"}:
        raise HTTPException(status_code=404, detail="فروشگاه پیدا نشد.")
    return store


def tenant_store_from_request(
    request: Request,
    db: Session,
    settings: Settings,
) -> Store:
    slug = parse_tenant_slug(request.headers.get("host", ""), settings)
    if not slug:
        raise HTTPException(status_code=404, detail="فروشگاه این دامنه پیدا نشد.")
    return store_by_slug(db, slug)
