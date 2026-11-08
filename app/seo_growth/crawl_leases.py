"""Distributed crawler lease claims for tenant quotas and per-host politeness."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import ipaddress
import secrets
import uuid
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Tenant
from app.seo_growth.crawler_security import CrawlTargetError, normalize_crawl_url
from app.seo_growth.models import SeoCrawlLease, SeoSite


class CrawlLeaseError(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


@dataclass(frozen=True)
class CrawlLeaseGrant:
    host: str
    crawl_id: str
    lease_token: str
    expires_at: datetime


def _utc(value: datetime | None) -> datetime:
    result = value or datetime.now(UTC)
    return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)


def _host(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 260:
        raise CrawlLeaseError("seo_crawler_invalid_host", 400)
    candidate = value
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        if ":" in value:
            raise CrawlLeaseError("seo_crawler_invalid_host", 400) from None
    else:
        candidate = f"[{address.compressed}]" if address.version == 6 else address.compressed
    try:
        target = normalize_crawl_url(f"https://{candidate}/")
    except CrawlTargetError:
        raise CrawlLeaseError("seo_crawler_invalid_host", 400) from None
    if target.path_and_query != "/":
        raise CrawlLeaseError("seo_crawler_invalid_host", 400)
    parsed = urlsplit(target.url)
    return parsed.hostname or target.hostname


def acquire_crawl_lease(
    db: Session,
    *,
    tenant_id: int,
    store_id: int,
    site_id: int,
    host: str,
    crawl_id: str,
    lease_seconds: int = 180,
    max_concurrent_per_tenant: int = 1,
    now: datetime | None = None,
) -> CrawlLeaseGrant:
    """Claim one host globally and enforce a tenant-wide active crawl ceiling.

    The tenant row lock serializes quota checks across the tenant's stores.
    A unique host constraint plus a savepoint resolves cross-tenant first-claim
    races. The caller owns the surrounding transaction and must commit it.
    """
    if any(type(value) is not int or value < 1 for value in (tenant_id, store_id, site_id)):
        raise CrawlLeaseError("seo_crawler_invalid_scope", 400)
    if type(lease_seconds) is not int or not 30 <= lease_seconds <= 600:
        raise CrawlLeaseError("seo_crawler_invalid_lease_duration", 400)
    if type(max_concurrent_per_tenant) is not int or not 1 <= max_concurrent_per_tenant <= 5:
        raise CrawlLeaseError("seo_crawler_invalid_tenant_limit", 400)
    try:
        normalized_crawl_id = str(uuid.UUID(crawl_id))
    except (TypeError, ValueError, AttributeError):
        raise CrawlLeaseError("seo_crawler_invalid_crawl_id", 400) from None

    canonical_host = _host(host)
    current = _utc(now)
    expires = current + timedelta(seconds=lease_seconds)

    tenant = db.scalar(
        select(Tenant.id).where(Tenant.id == tenant_id).with_for_update()
    )
    if tenant is None:
        raise CrawlLeaseError("seo_crawler_invalid_scope", 404)
    site = db.scalar(
        select(SeoSite.id).where(
            SeoSite.id == site_id,
            SeoSite.tenant_id == tenant_id,
            SeoSite.store_id == store_id,
            SeoSite.status == "connected",
        ).with_for_update()
    )
    if site is None:
        raise CrawlLeaseError("seo_site_not_connected", 404)

    active_count = db.scalar(
        select(func.count()).select_from(SeoCrawlLease).where(
            SeoCrawlLease.tenant_id == tenant_id,
            SeoCrawlLease.lease_expires_at > current,
        )
    ) or 0
    if active_count >= max_concurrent_per_tenant:
        raise CrawlLeaseError("seo_crawler_tenant_concurrency_limit", 429)

    existing = db.scalar(
        select(SeoCrawlLease).where(
            SeoCrawlLease.host == canonical_host,
        ).with_for_update()
    )
    token = secrets.token_hex(32)
    if existing is not None:
        if _utc(existing.lease_expires_at) > current:
            raise CrawlLeaseError("seo_crawler_host_busy", 409)
        existing.tenant_id = tenant_id
        existing.store_id = store_id
        existing.site_id = site_id
        existing.crawl_id = normalized_crawl_id
        existing.lease_token = token
        existing.lease_expires_at = expires
        existing.created_at = current
        db.flush()
        return CrawlLeaseGrant(canonical_host, normalized_crawl_id, token, expires)

    lease = SeoCrawlLease(
        tenant_id=tenant_id,
        store_id=store_id,
        site_id=site_id,
        host=canonical_host,
        crawl_id=normalized_crawl_id,
        lease_token=token,
        lease_expires_at=expires,
        created_at=current,
    )
    try:
        with db.begin_nested():
            db.add(lease)
            db.flush()
    except IntegrityError:
        # A different tenant may have inserted the same host after our read.
        raced = db.scalar(
            select(SeoCrawlLease).where(
                SeoCrawlLease.host == canonical_host,
            ).with_for_update()
        )
        if raced is None or _utc(raced.lease_expires_at) > current:
            raise CrawlLeaseError("seo_crawler_host_busy", 409) from None
        raced.tenant_id = tenant_id
        raced.store_id = store_id
        raced.site_id = site_id
        raced.crawl_id = normalized_crawl_id
        raced.lease_token = token
        raced.lease_expires_at = expires
        raced.created_at = current
        db.flush()
    return CrawlLeaseGrant(canonical_host, normalized_crawl_id, token, expires)


def renew_crawl_lease(
    db: Session,
    grant: CrawlLeaseGrant,
    *,
    lease_seconds: int = 180,
    now: datetime | None = None,
) -> CrawlLeaseGrant:
    if type(lease_seconds) is not int or not 30 <= lease_seconds <= 600:
        raise CrawlLeaseError("seo_crawler_invalid_lease_duration", 400)
    current = _utc(now)
    lease = db.scalar(
        select(SeoCrawlLease).where(
            SeoCrawlLease.host == grant.host,
            SeoCrawlLease.crawl_id == grant.crawl_id,
            SeoCrawlLease.lease_token == grant.lease_token,
            SeoCrawlLease.lease_expires_at > current,
        ).with_for_update()
    )
    if lease is None:
        raise CrawlLeaseError("seo_crawler_lease_lost", 409)
    lease.lease_expires_at = current + timedelta(seconds=lease_seconds)
    db.flush()
    return CrawlLeaseGrant(
        grant.host, grant.crawl_id, grant.lease_token, lease.lease_expires_at
    )


def release_crawl_lease(db: Session, grant: CrawlLeaseGrant) -> bool:
    lease = db.scalar(
        select(SeoCrawlLease).where(
            SeoCrawlLease.host == grant.host,
            SeoCrawlLease.crawl_id == grant.crawl_id,
            SeoCrawlLease.lease_token == grant.lease_token,
        ).with_for_update()
    )
    if lease is None:
        return False
    db.delete(lease)
    db.flush()
    return True
