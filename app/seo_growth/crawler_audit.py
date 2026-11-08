"""Safe, tenant-scoped persistence helpers for crawler audit evidence.

Only URL origin/path fingerprints are retained. Query strings and fragments are
intentionally excluded because they can contain credentials or personal data.
"""
from __future__ import annotations

from datetime import timedelta
import hashlib
import re
import uuid
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.models import utc_now
from app.seo_growth.models import SeoCrawlAuditEvent
from app.seo_growth.crawler_security import normalize_crawl_url


_EVENT_KINDS = {"robots", "page"}
_OUTCOMES = {"allowed", "blocked", "fetched", "failed", "redirected"}
_ROBOTS_DECISIONS = {
    "allow", "disallow", "unavailable_allow", "unavailable_block", "not_checked",
}
_ERROR_CODE = re.compile(r"^[a-z0-9_]{1,80}$")


def url_audit_identity(raw_url: str) -> tuple[str, str]:
    """Return host and stable SHA-256 identity without query or fragment data."""
    target = normalize_crawl_url(raw_url)
    parsed = urlsplit(target.url)
    identity = f"{target.scheme}://{target.hostname}{parsed.path or '/'}"
    return target.hostname, hashlib.sha256(identity.encode("utf-8")).hexdigest()


def record_crawl_audit_event(
    db: Session,
    *,
    tenant_id: int,
    store_id: int,
    site_id: int,
    crawl_id: str,
    event_kind: str,
    outcome: str,
    raw_url: str,
    robots_decision: str = "not_checked",
    http_status: int | None = None,
    bytes_received: int = 0,
    duration_ms: int = 0,
    error_code: str | None = None,
    retention_days: int,
) -> SeoCrawlAuditEvent:
    """Stage one sanitized event; transaction ownership remains with the caller."""
    if any(type(value) is not int or value < 1 for value in (tenant_id, store_id, site_id)):
        raise ValueError("seo_crawler_audit_invalid_scope")
    try:
        normalized_crawl_id = str(uuid.UUID(crawl_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("seo_crawler_audit_invalid_crawl_id") from None
    if event_kind not in _EVENT_KINDS or outcome not in _OUTCOMES:
        raise ValueError("seo_crawler_audit_invalid_event")
    if robots_decision not in _ROBOTS_DECISIONS:
        raise ValueError("seo_crawler_audit_invalid_robots_decision")
    if http_status is not None and (
        type(http_status) is not int or not 100 <= http_status <= 599
    ):
        raise ValueError("seo_crawler_audit_invalid_http_status")
    if type(bytes_received) is not int or bytes_received < 0:
        raise ValueError("seo_crawler_audit_invalid_byte_count")
    if type(duration_ms) is not int or duration_ms < 0:
        raise ValueError("seo_crawler_audit_invalid_duration")
    if type(retention_days) is not int or not 1 <= retention_days <= 365:
        raise ValueError("seo_crawler_audit_invalid_retention")
    if error_code is not None and not _ERROR_CODE.fullmatch(error_code):
        raise ValueError("seo_crawler_audit_invalid_error_code")

    host, fingerprint = url_audit_identity(raw_url)
    created_at = utc_now()
    event = SeoCrawlAuditEvent(
        tenant_id=tenant_id,
        store_id=store_id,
        site_id=site_id,
        crawl_id=normalized_crawl_id,
        event_kind=event_kind,
        outcome=outcome,
        robots_decision=robots_decision,
        url_host=host,
        url_fingerprint=fingerprint,
        http_status=http_status,
        bytes_received=bytes_received,
        duration_ms=duration_ms,
        error_code=error_code,
        created_at=created_at,
        expires_at=created_at + timedelta(days=retention_days),
    )
    db.add(event)
    return event
