"""Internal orchestration for consent-gated, leased SEO crawl previews.

This module intentionally exposes no HTTP route. Callers must provide a persisted
consent check and an explicit audit retention period before any network work.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy.orm import Session

from app.seo_growth.crawl_leases import (
    CrawlLeaseGrant,
    acquire_crawl_lease,
    release_crawl_lease,
    renew_crawl_lease,
)
from app.seo_growth.crawler_audit import record_crawl_audit_event
from app.seo_growth.crawler_policy import CrawlLimits
from app.seo_growth.crawler_preview import crawl_preview
from app.seo_growth.crawler_security import (
    CrawlTargetError,
    crawl_path_in_scope,
    normalize_crawl_path_prefix,
    normalize_crawl_url,
)
from app.seo_growth.models import SeoGoogleConnection, SeoSite


class CrawlOrchestrationError(ValueError):
    """A crawl cannot proceed because consent or site authority is invalid."""

    def __init__(self, code: str, status: int = 409):
        self.code = code
        self.status = status
        super().__init__(code)


def _property_path_scope(property_id: str, seed_url: str) -> tuple[str, str]:
    """Validate a seed URL against a Search Console domain or URL-prefix property."""
    if not isinstance(property_id, str) or not property_id.strip():
        raise CrawlOrchestrationError("seo_crawler_invalid_site_property", 400)
    try:
        seed = normalize_crawl_url(seed_url)
    except (CrawlTargetError, ValueError):
        raise CrawlOrchestrationError("seo_crawler_invalid_seed_url", 400) from None

    raw_property = property_id.strip()
    if raw_property.casefold().startswith("sc-domain:"):
        domain_value = raw_property.split(":", 1)[1].strip()
        try:
            domain = normalize_crawl_url(f"https://{domain_value}/")
        except (CrawlTargetError, ValueError):
            raise CrawlOrchestrationError("seo_crawler_invalid_site_property", 400) from None
        if domain.path_and_query != "/":
            raise CrawlOrchestrationError("seo_crawler_invalid_site_property", 400)
        if seed.hostname != domain.hostname and not seed.hostname.endswith("." + domain.hostname):
            raise CrawlOrchestrationError("seo_crawler_site_scope_mismatch", 403)
        return seed.url, "/"

    try:
        prop = normalize_crawl_url(raw_property)
        prefix = normalize_crawl_path_prefix(urlsplit(prop.url).path or "/")
    except (CrawlTargetError, ValueError):
        raise CrawlOrchestrationError("seo_crawler_invalid_site_property", 400) from None

    if (seed.scheme, seed.hostname, seed.port) != (prop.scheme, prop.hostname, prop.port):
        raise CrawlOrchestrationError("seo_crawler_site_scope_mismatch", 403)
    if not crawl_path_in_scope(urlsplit(seed.url).path or "/", prefix):
        raise CrawlOrchestrationError("seo_crawler_site_scope_mismatch", 403)
    return seed.url, prefix


def _assert_site_connected(
    db: Session, *, tenant_id: int, store_id: int, site_id: int,
) -> tuple[SeoSite, SeoGoogleConnection]:
    site = db.get(SeoSite, site_id)
    if (
        site is None or site.tenant_id != tenant_id or site.store_id != store_id
        or site.status != "connected"
    ):
        raise CrawlOrchestrationError("seo_crawler_site_not_connected", 403)
    connection = db.get(SeoGoogleConnection, site.connection_id)
    if (
        connection is None or connection.tenant_id != tenant_id
        or connection.store_id != store_id or connection.status != "connected"
    ):
        raise CrawlOrchestrationError("seo_crawler_google_connection_not_active", 403)
    return site, connection


def run_crawl_preview(
    db: Session,
    *,
    tenant_id: int,
    store_id: int,
    site_id: int,
    seed_url: str,
    consent_check: Callable[[], bool],
    retention_days: int,
    resolver: Callable[[str, int], list[str]],
    limits: CrawlLimits | None = None,
    crawl_id: str | None = None,
    lease_seconds: int = 180,
    max_concurrent_per_tenant: int = 1,
    fetch_page: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run one bounded crawl with consent rechecks, distributed lease and durable audit.

    The caller owns authentication and supplies a consent_check backed by a
    persisted, revocable site-level consent record. Audit retention is mandatory
    and deliberately has no default. Page observations remain in-memory until a
    separately approved persistence/retention design is implemented.
    """
    if not callable(consent_check):
        raise CrawlOrchestrationError("seo_crawler_consent_check_required", 400)
    if type(retention_days) is not int or not 1 <= retention_days <= 365:
        raise CrawlOrchestrationError("seo_crawler_invalid_retention", 400)
    if not consent_check():
        raise CrawlOrchestrationError("seo_crawler_consent_required", 403)

    site, _connection = _assert_site_connected(
        db, tenant_id=tenant_id, store_id=store_id, site_id=site_id,
    )
    canonical_seed, path_prefix = _property_path_scope(site.property_id, seed_url)
    crawl_id = crawl_id or str(uuid4())
    host = urlsplit(canonical_seed).hostname
    if not host:
        raise CrawlOrchestrationError("seo_crawler_invalid_seed_url", 400)

    grant = acquire_crawl_lease(
        db,
        tenant_id=tenant_id,
        store_id=store_id,
        site_id=site_id,
        host=host,
        crawl_id=crawl_id,
        lease_seconds=lease_seconds,
        max_concurrent_per_tenant=max_concurrent_per_tenant,
    )
    db.commit()

    current_grant: CrawlLeaseGrant = grant

    def before_page(_url: str, _depth: int) -> None:
        nonlocal current_grant
        if not consent_check():
            raise CrawlOrchestrationError("seo_crawler_consent_revoked", 403)
        _assert_site_connected(
            db, tenant_id=tenant_id, store_id=store_id, site_id=site_id,
        )
        current_grant = renew_crawl_lease(
            db, current_grant, lease_seconds=lease_seconds,
        )
        db.commit()

    def audit_callback(**event: Any) -> None:
        record_crawl_audit_event(
            db,
            tenant_id=tenant_id,
            store_id=store_id,
            site_id=site_id,
            crawl_id=current_grant.crawl_id,
            retention_days=retention_days,
            **event,
        )
        db.commit()

    kwargs: dict[str, Any] = {
        "resolver": resolver,
        "limits": limits or CrawlLimits(),
        "allowed_path_prefix": path_prefix,
        "before_page": before_page,
        "audit_callback": audit_callback,
    }
    if fetch_page is not None:
        kwargs["fetch_page"] = fetch_page

    try:
        result = crawl_preview(canonical_seed, **kwargs)
    except Exception:
        db.rollback()
        try:
            release_crawl_lease(db, current_grant)
            db.commit()
        except Exception:
            db.rollback()
        raise
    else:
        db.rollback()
        release_crawl_lease(db, current_grant)
        db.commit()
        return {"crawl_id": current_grant.crawl_id, **result}
