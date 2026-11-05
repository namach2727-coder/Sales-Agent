"""Explicit, bounded F2b Google Search Console ingestion.

No scheduler is registered. This module is reachable only through an authenticated,
CSRF-protected, feature-flagged user request.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import hashlib
import json
import math
import secrets
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.seo_growth.models import SeoGoogleConnection, SeoSite
from app.seo_growth.persistence import (
    SeoMetricCoverage, SeoPropertyDailyMetric, SeoQueryPageMetric, SeoSyncLease, SeoSyncRun,
)
from app.seo_growth.security import SeoError
from app.seo_growth.service import SeoOnboardingService
from app.seo_growth.google_client import GoogleGscError


MAX_SYNC_DAYS = 90
QUERY_PAGE_LIMIT = 500
LEASE_SECONDS = 300
FINAL_DATA_DELAY_DAYS = 3


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _property_page(property_id: str, page: str) -> bool:
    if not page or len(page) > 2048 or any(c.isspace() for c in page):
        return False
    try:
        parsed = urlsplit(page)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.port:
            return False
        if property_id.startswith("sc-domain:"):
            domain = property_id.removeprefix("sc-domain:")
            return parsed.hostname == domain or parsed.hostname.endswith("." + domain)
        prefix = urlsplit(property_id)
        path = prefix.path or "/"
        return (parsed.scheme == prefix.scheme and parsed.hostname == prefix.hostname
                and parsed.path.startswith(path)
                and (path.endswith("/") or parsed.path == path or parsed.path.startswith(path + "/")))
    except ValueError:
        return False


def _metric_values(row: dict) -> tuple[int, int, float | None, float | None]:
    clicks, impressions = row.get("clicks"), row.get("impressions")
    position = row.get("position")
    for value in (clicks, impressions):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 2**53 - 1:
            raise GoogleGscError("google_invalid_response")
    if clicks > impressions:
        raise GoogleGscError("google_invalid_response")
    if isinstance(position, bool) or not isinstance(position, (int, float)) or not math.isfinite(position) or position < 0:
        raise GoogleGscError("google_invalid_response")
    if impressions and position == 0:
        raise GoogleGscError("google_invalid_response")
    ctr = clicks / impressions if impressions else None
    return clicks, impressions, ctr, float(position) if impressions else None


def normalize_daily_rows(body: dict, *, start_date: date, end_date: date) -> list[dict]:
    if not isinstance(body, dict) or body.get("responseAggregationType") not in {None, "byProperty"}:
        raise GoogleGscError("google_invalid_response")
    rows = body.get("rows", [])
    if not isinstance(rows, list) or len(rows) > (end_date - start_date).days + 1:
        raise GoogleGscError("google_invalid_response")
    normalized = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("keys"), list) or len(row["keys"]) != 1:
            raise GoogleGscError("google_invalid_response")
        raw_day = row["keys"][0]
        try:
            metric_day = date.fromisoformat(raw_day)
        except (TypeError, ValueError):
            raise GoogleGscError("google_invalid_response") from None
        if metric_day.isoformat() != raw_day or not start_date <= metric_day <= end_date or metric_day in seen:
            raise GoogleGscError("google_invalid_response")
        seen.add(metric_day)
        clicks, impressions, ctr, position = _metric_values(row)
        normalized.append({"metric_date": metric_day, "clicks": clicks, "impressions": impressions,
                           "ctr": ctr, "position": position})
    return normalized


def normalize_query_page_rows(body: dict, *, property_id: str,
                              start_date: date, end_date: date) -> list[dict]:
    if not isinstance(body, dict):
        raise GoogleGscError("google_invalid_response")
    rows = body.get("rows", [])
    if not isinstance(rows, list) or len(rows) > QUERY_PAGE_LIMIT:
        raise GoogleGscError("google_invalid_response")
    normalized = []
    seen = set()
    for rank, row in enumerate(rows, start=1):
        if (not isinstance(row, dict) or not isinstance(row.get("keys"), list)
                or len(row["keys"]) != 2):
            raise GoogleGscError("google_invalid_response")
        query, page = row["keys"]
        if not isinstance(query, str) or not query or len(query) > 300 or not isinstance(page, str):
            raise GoogleGscError("google_invalid_response")
        if not _property_page(property_id, page):
            raise GoogleGscError("google_invalid_response")
        row_key = hashlib.sha256(json.dumps([query, page], ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        if row_key in seen:
            raise GoogleGscError("google_invalid_response")
        seen.add(row_key)
        clicks, impressions, ctr, position = _metric_values(row)
        normalized.append({"row_key": row_key, "query_text": query, "page_url": page,
            "clicks": clicks, "impressions": impressions, "ctr": ctr,
            "position": position, "sample_rank": rank})
    return normalized


def _scope(svc: SeoOnboardingService, site_public_id: str):
    if not svc.settings.seo_data_sync_enabled:
        raise SeoError("seo_sync_not_enabled", 403)
    svc._grant()
    site = svc.db.scalar(svc._sites().where(SeoSite.public_id == site_public_id))
    if site is None:
        raise SeoError("not_found", 404)
    connection = svc.db.scalar(svc._connections().where(SeoGoogleConnection.id == site.connection_id))
    if connection is None:
        raise SeoError("not_found", 404)
    if site.status != "connected":
        raise SeoError("seo_site_not_connected", 409)
    if connection.status != "connected" or not connection.encrypted_refresh_token:
        raise SeoError("seo_reauthorization_required", 409)
    if connection.key_version != svc.settings.seo_token_key_version:
        raise SeoError("seo_credential_unavailable", 503)
    return site, connection


def _current_scope(svc: SeoOnboardingService, site_public_id: str):
    svc._lock()
    svc.db.expire_all()
    current = SeoOnboardingService(svc.db, svc.settings, svc.principal,
        svc.scope.tenant_public_id, svc.scope.store_public_id, mutation=True, provider=svc._provider)
    return current, *_scope(current, site_public_id)


def _release_lease(svc: SeoOnboardingService, lease: SeoSyncLease, token: str) -> None:
    if lease.lease_token == token:
        lease.lease_token = None
        lease.lease_expires_at = None
        lease.cursor_json = None


def _upsert_daily(db, *, scope: dict, run_id: int, search_type: str,
                  start_date: date, end_date: date, rows: list[dict]) -> None:
    existing = db.scalars(select(SeoPropertyDailyMetric).where(
        SeoPropertyDailyMetric.tenant_id == scope["tenant_id"],
        SeoPropertyDailyMetric.store_id == scope["store_id"],
        SeoPropertyDailyMetric.site_id == scope["site_id"],
        SeoPropertyDailyMetric.search_type == search_type,
        SeoPropertyDailyMetric.metric_date >= start_date,
        SeoPropertyDailyMetric.metric_date <= end_date,
    )).all()
    by_day = {row.metric_date: row for row in existing}
    received_days = {row["metric_date"] for row in rows}
    # A successful replacement removes stale dates omitted by the provider response.
    for metric_day, old in by_day.items():
        if metric_day not in received_days:
            db.delete(old)
    for values in rows:
        target = by_day.get(values["metric_date"])
        if target is None:
            target = SeoPropertyDailyMetric(**scope, **values, search_type=search_type, source_run_id=run_id)
            db.add(target)
        else:
            for key, value in values.items():
                setattr(target, key, value)
            target.source_run_id = run_id
            target.updated_at = _now()


def _upsert_query_page(db, *, scope: dict, run_id: int, search_type: str,
                       start_date: date, end_date: date, rows: list[dict]) -> None:
    existing = db.scalars(select(SeoQueryPageMetric).where(
        SeoQueryPageMetric.tenant_id == scope["tenant_id"],
        SeoQueryPageMetric.store_id == scope["store_id"],
        SeoQueryPageMetric.site_id == scope["site_id"],
        SeoQueryPageMetric.search_type == search_type,
        SeoQueryPageMetric.start_date == start_date,
        SeoQueryPageMetric.end_date == end_date,
    )).all()
    by_key = {row.row_key: row for row in existing}
    for values in rows:
        target = by_key.get(values["row_key"])
        if target is None:
            target = SeoQueryPageMetric(**scope, source_run_id=run_id, search_type=search_type,
                start_date=start_date, end_date=end_date, **values)
            db.add(target)
        else:
            for key, value in values.items():
                setattr(target, key, value)
            target.source_run_id = run_id
            target.updated_at = _now()
    # A successful fresh response is the complete replacement for this bounded sample window.
    received = {row["row_key"] for row in rows}
    for key, old in by_key.items():
        if key not in received:
            db.delete(old)


def _coverage(db, *, scope: dict, run_id: int, search_type: str, dimension: str,
              start_date: date, end_date: date, rows_received: int,
              row_limit: int, status: str) -> None:
    existing = db.scalar(select(SeoMetricCoverage).where(
        SeoMetricCoverage.tenant_id == scope["tenant_id"],
        SeoMetricCoverage.store_id == scope["store_id"],
        SeoMetricCoverage.site_id == scope["site_id"],
        SeoMetricCoverage.search_type == search_type,
        SeoMetricCoverage.dimension == dimension,
        SeoMetricCoverage.start_date == start_date,
        SeoMetricCoverage.end_date == end_date,
    ))
    if existing is None:
        existing = SeoMetricCoverage(**scope, source_run_id=run_id, search_type=search_type,
            dimension=dimension, start_date=start_date, end_date=end_date,
            rows_received=rows_received, row_limit=row_limit, coverage_status=status, observed_at=_now())
        db.add(existing)
    else:
        existing.source_run_id = run_id
        existing.rows_received = rows_received
        existing.row_limit = row_limit
        existing.coverage_status = status
        existing.observed_at = _now()


def sync_site(svc: SeoOnboardingService, site_public_id: str,
              start_date: date, end_date: date) -> dict:
    """Run a user-requested bounded sync. No scheduler or implicit backfill."""
    if not isinstance(start_date, date) or not isinstance(end_date, date) or end_date < start_date:
        raise SeoError("seo_sync_invalid_window", 422)
    if (end_date - start_date).days + 1 > MAX_SYNC_DAYS:
        raise SeoError("seo_sync_window_too_large", 422)
    latest_final = datetime.now(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=FINAL_DATA_DELAY_DAYS)
    if end_date > latest_final:
        raise SeoError("seo_sync_data_not_final", 422)

    svc._lock()
    site, connection = _scope(svc, site_public_id)
    scope = {"tenant_id": svc.tenant, "store_id": svc.store, "site_id": site.id}
    lease = svc.db.scalar(select(SeoSyncLease).where(
        SeoSyncLease.tenant_id == svc.tenant, SeoSyncLease.store_id == svc.store,
        SeoSyncLease.site_id == site.id).with_for_update())
    if lease is None:
        lease = SeoSyncLease(**scope)
        svc.db.add(lease)
        svc.db.flush()
    now = _now()
    expires = _aware(lease.lease_expires_at)
    if lease.lease_token and expires and expires > now:
        raise SeoError("seo_sync_already_running", 409)
    lease_token = secrets.token_urlsafe(32)
    lease.lease_token = lease_token
    lease.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    run = SeoSyncRun(**scope, requested_by_user_id=svc.user, status="running", search_type="web",
        start_date=start_date, end_date=end_date, rows_received=0, created_at=now, started_at=now)
    svc.db.add(run)
    svc._audit("sync_started", site_public_id, details={"start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()})
    svc.db.commit()
    run_id = run.id
    ciphertext, granted_scope, property_id = connection.encrypted_refresh_token, connection.granted_scope, site.property_id
    try:
        provider = svc.provider
        refresh_token = svc._open(ciphertext, "refresh")
        tokens = provider.refresh_access_token(refresh_token=refresh_token, verified_scope=granted_scope)
        properties = provider.list_properties(access_token=tokens.access_token)
        if not any(p.site_url == property_id for p in properties):
            raise SeoError("seo_property_not_granted", 403)
        daily_body = provider.search_analytics(access_token=tokens.access_token, property_id=property_id,
            start_date=start_date, end_date=end_date, dimensions=("date",), row_limit=(end_date-start_date).days+1)
        query_body = provider.search_analytics(access_token=tokens.access_token, property_id=property_id,
            start_date=start_date, end_date=end_date, dimensions=("query", "page"), row_limit=QUERY_PAGE_LIMIT)
        daily_rows = normalize_daily_rows(daily_body, start_date=start_date, end_date=end_date)
        query_rows = normalize_query_page_rows(query_body, property_id=property_id,
            start_date=start_date, end_date=end_date)

        current, current_site, current_connection = _current_scope(svc, site_public_id)
        if (current_site.property_id != property_id or current_connection.id != connection.id
                or current_connection.encrypted_refresh_token != ciphertext):
            raise SeoError("seo_connection_changed", 409)
        lease_current = current.db.scalar(select(SeoSyncLease).where(
            SeoSyncLease.tenant_id == current.tenant, SeoSyncLease.store_id == current.store,
            SeoSyncLease.site_id == current_site.id).with_for_update())
        if lease_current is None or lease_current.lease_token != lease_token:
            raise SeoError("seo_sync_lease_lost", 409)

        _upsert_daily(current.db, scope=scope, run_id=run_id, search_type="web",
            start_date=start_date, end_date=end_date, rows=daily_rows)
        _upsert_query_page(current.db, scope=scope, run_id=run_id, search_type="web",
            start_date=start_date, end_date=end_date, rows=query_rows)
        daily_status = "empty" if not daily_rows else "complete"
        query_status = ("empty" if not query_rows else
                        "truncated" if len(query_rows) >= QUERY_PAGE_LIMIT else "complete")
        _coverage(current.db, scope=scope, run_id=run_id, search_type="web", dimension="date",
            start_date=start_date, end_date=end_date, rows_received=len(daily_rows),
            row_limit=(end_date-start_date).days+1, status=daily_status)
        _coverage(current.db, scope=scope, run_id=run_id, search_type="web", dimension="query_page",
            start_date=start_date, end_date=end_date, rows_received=len(query_rows),
            row_limit=QUERY_PAGE_LIMIT, status=query_status)
        run_record = current.db.get(SeoSyncRun, run_id)
        run_record.status = "succeeded"
        run_record.rows_received = len(daily_rows) + len(query_rows)
        run_record.completed_at = _now()
        _release_lease(current, lease_current, lease_token)
        current._audit("sync_completed", site_public_id, details={"run_id": run_id,
            "daily_rows": len(daily_rows), "query_page_rows": len(query_rows),
            "query_page_coverage": query_status})
        current.db.commit()
        return {"run_id": run_id, "status": "succeeded", "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(), "daily_rows": len(daily_rows),
            "query_page_rows": len(query_rows), "coverage": {"date": daily_status, "query_page": query_status}}
    except (SeoError, GoogleGscError) as exc:
        svc.db.rollback()
        run_record = svc.db.get(SeoSyncRun, run_id)
        lease_current = svc.db.scalar(select(SeoSyncLease).where(
            SeoSyncLease.tenant_id == svc.tenant, SeoSyncLease.store_id == svc.store,
            SeoSyncLease.site_id == site.id).with_for_update())
        if run_record:
            run_record.status = "failed"
            run_record.error_code = exc.code
            run_record.completed_at = _now()
        if lease_current:
            _release_lease(svc, lease_current, lease_token)
        svc._audit("sync_failed", site_public_id, details={"run_id": run_id, "code": exc.code})
        svc.db.commit()
        raise
    except Exception:
        svc.db.rollback()
        run_record = svc.db.get(SeoSyncRun, run_id)
        lease_current = svc.db.scalar(select(SeoSyncLease).where(
            SeoSyncLease.tenant_id == svc.tenant, SeoSyncLease.store_id == svc.store,
            SeoSyncLease.site_id == site.id).with_for_update())
        if run_record:
            run_record.status = "failed"
            run_record.error_code = "seo_sync_failed"
            run_record.completed_at = _now()
        if lease_current:
            _release_lease(svc, lease_current, lease_token)
        svc._audit("sync_failed", site_public_id, details={"run_id": run_id, "code": "seo_sync_failed"})
        svc.db.commit()
        raise SeoError("seo_sync_failed", 502) from None
