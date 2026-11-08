"""Bounded, on-demand GSC preview. No metric storage, background jobs or CMS writes."""
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
import math
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update

from app.models import TenantAuditLog
from app.seo_growth.analysis import DailyMetric, QueryPageMetric, build_seo_report
from app.seo_growth.google_client import GoogleGscError
from app.seo_growth.models import SeoGoogleConnection, SeoSite
from app.seo_growth.security import SeoError
from app.seo_growth.service import SeoOnboardingService

WINDOW_DAYS = 28
QUERY_ROW_LIMIT = 500
MIN_INTERVAL_SECONDS = 60
MAX_ATTEMPTS_PER_DAY = 12


def _clock() -> datetime:
    return datetime.now(UTC)


def _count(value) -> int:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or int(value) != value or not 0 <= value <= 2**53 - 1):
        raise GoogleGscError("google_invalid_response")
    return int(value)


def _metrics(row: dict) -> tuple[int, int, float | None]:
    clicks, impressions = _count(row.get("clicks")), _count(row.get("impressions"))
    position = row.get("position")
    if clicks > impressions or isinstance(position, bool) or not isinstance(position, (int, float)) or not math.isfinite(position):
        raise GoogleGscError("google_invalid_response")
    if not 0 <= position <= 2**53 - 1 or (impressions > 0 and position == 0):
        raise GoogleGscError("google_invalid_response")
    return clicks, impressions, float(position) if impressions else None


def _rows(body: dict, *, dimensions: int, limit: int) -> list[dict]:
    if not isinstance(body, dict):
        raise GoogleGscError("google_invalid_response")
    rows = body.get("rows", [])
    if not isinstance(rows, list) or len(rows) > limit:
        raise GoogleGscError("google_invalid_response")
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("keys"), list)
                or len(row["keys"]) != dimensions or any(not isinstance(k, str) for k in row["keys"])):
            raise GoogleGscError("google_invalid_response")
    return rows


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
            and parsed.path.startswith(path) and (path.endswith("/") or parsed.path == path or parsed.path.startswith(path + "/")))
    except ValueError:
        return False


def preview_from_google(*, property_id: str, daily_body: dict, query_body: dict,
                        end_date: date, generated_at: datetime) -> dict:
    """Only date rows contribute totals; missing days remain null in each series."""
    current_start = end_date - timedelta(days=WINDOW_DAYS - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=WINDOW_DAYS - 1)
    daily = []
    queries = []
    try:
        if isinstance(daily_body, dict) and daily_body.get("responseAggregationType") not in {None, "byProperty"}:
            raise GoogleGscError("google_invalid_response")
        for row in _rows(daily_body, dimensions=1, limit=WINDOW_DAYS * 2):
            day = date.fromisoformat(row["keys"][0])
            if day.isoformat() != row["keys"][0] or not previous_start <= day <= end_date:
                raise ValueError("outside_requested_window")
            daily.append(DailyMetric(day, *_metrics(row)))
        for row in _rows(query_body, dimensions=2, limit=QUERY_ROW_LIMIT):
            query, page = row["keys"]
            if not query or len(query) > 300 or not _property_page(property_id, page):
                raise ValueError("invalid_query_page")
            queries.append(QueryPageMetric(query, page, *_metrics(row)))
        recent = build_seo_report(start_date=current_start, end_date=end_date,
            daily_rows=[r for r in daily if r.day >= current_start], query_page_rows=queries)
        prior = build_seo_report(start_date=previous_start, end_date=previous_end,
            daily_rows=[r for r in daily if r.day <= previous_end], query_page_rows=[])
        for report in (recent, prior):
            _count(report.total_clicks)
            _count(report.total_impressions)
    except (ValueError, TypeError, OverflowError):
        raise GoogleGscError("google_invalid_response") from None

    def period(report):
        by_day = {r.day: r for r in daily}
        series = []
        for i in range(WINDOW_DAYS):
            day = report.start_date + timedelta(days=i)
            row = by_day.get(day)
            series.append({"date": day.isoformat(), "clicks": row.clicks if row else None,
                "impressions": row.impressions if row else None,
                "ctr": row.clicks / row.impressions if row and row.impressions else None,
                "position": row.position if row else None})
        return {"start_date": report.start_date.isoformat(), "end_date": report.end_date.isoformat(),
            "observed_days": report.observed_days, "missing_dates": [d.isoformat() for d in report.missing_days],
            "coverage": report.coverage, "clicks": report.total_clicks if report.observed_days else None,
            "impressions": report.total_impressions if report.observed_days else None,
            "ctr": report.ctr, "position": report.weighted_position, "daily": series}

    complete = not recent.missing_days and not prior.missing_days
    def change(a, b):
        return round((a - b) / b * 100, 2) if complete and b > 0 else None
    return {"kind": "analysis_preview", "persistence": "response_only", "property_id": property_id,
        "source": "google_search_console", "data_state": "final", "search_type": "web",
        "timezone": "America/Los_Angeles", "generated_at": generated_at.isoformat(),
        "current": period(recent), "previous": period(prior),
        "comparison": {"status": "comparable" if complete else "incomplete_coverage",
            "clicks_change_percent": change(recent.total_clicks, prior.total_clicks),
            "impressions_change_percent": change(recent.total_impressions, prior.total_impressions),
            "ctr_change_percentage_points": round((recent.ctr - prior.ctr) * 100, 4)
                if complete and recent.ctr is not None and prior.ctr is not None else None,
            "position_change": round(recent.weighted_position - prior.weighted_position, 4)
                if complete and recent.weighted_position is not None and prior.weighted_position is not None else None},
        "opportunities": [asdict(o) for o in recent.opportunities],
        "query_sample": {"row_limit": QUERY_ROW_LIMIT, "received_rows": len(queries),
            "limit_reached": len(queries) == QUERY_ROW_LIMIT, "coverage": "google_top_rows_not_exhaustive"},
        "warnings": list(dict.fromkeys([*recent.warnings, *prior.warnings,
            "Daily totals cover reported date rows only. Missing rows are not inferred as zero.",
            "Period changes do not establish cause or control for seasonality or query mix."]))}


def _eligible(svc: SeoOnboardingService, site_public_id: str):
    if not svc.settings.seo_analysis_preview_enabled:
        raise SeoError("seo_analysis_not_enabled", 403)
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


def _locked_current_scope(svc: SeoOnboardingService) -> SeoOnboardingService:
    # Authority can change while waiting for another worker's store lock.
    svc._lock()
    svc.db.expire_all()
    return SeoOnboardingService(svc.db, svc.settings, svc.principal, svc.scope.tenant_public_id,
        svc.scope.store_public_id, mutation=True, provider=svc._provider)


def analysis_preview(svc: SeoOnboardingService, site_public_id: str) -> dict:
    svc = _locked_current_scope(svc)
    site, connection = _eligible(svc, site_public_id)
    provider = svc.provider
    token = svc._open(connection.encrypted_refresh_token, "refresh")
    connection_id, ciphertext = connection.id, connection.encrypted_refresh_token
    granted_scope = connection.granted_scope
    property_id = site.property_id
    clock = _clock()
    attempts = select(TenantAuditLog).where(TenantAuditLog.tenant_id == svc.tenant,
        TenantAuditLog.store_id == svc.store, TenantAuditLog.action == "seo.analysis_preview_started")
    last = svc.db.scalar(attempts.with_only_columns(TenantAuditLog.created_at).order_by(TenantAuditLog.id.desc()).limit(1))
    count = svc.db.scalar(attempts.with_only_columns(func.count()).where(TenantAuditLog.created_at >= clock - timedelta(days=1)))
    if (last and (last.replace(tzinfo=UTC) if last.tzinfo is None else last) > clock - timedelta(seconds=MIN_INTERVAL_SECONDS)) or count >= MAX_ATTEMPTS_PER_DAY:
        raise SeoError("seo_analysis_rate_limited", 429)
    svc._audit("analysis_preview_started", site_public_id)
    svc.db.commit()  # Consume quota before Google; no lock held across HTTP.
    try:
        tokens = provider.refresh_access_token(refresh_token=token, verified_scope=granted_scope)
        properties = provider.list_properties(access_token=tokens.access_token)
        if not any(p.site_url == property_id for p in properties):
            raise SeoError("seo_property_not_granted", 403)
        end = clock.astimezone(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=3)
        start = end - timedelta(days=WINDOW_DAYS * 2 - 1)
        daily = provider.search_analytics(access_token=tokens.access_token, property_id=property_id,
            start_date=start, end_date=end, dimensions=("date",), row_limit=WINDOW_DAYS * 2)
        queries = provider.search_analytics(access_token=tokens.access_token, property_id=property_id,
            start_date=end - timedelta(days=WINDOW_DAYS - 1), end_date=end,
            dimensions=("query", "page"), row_limit=QUERY_ROW_LIMIT)
        report = preview_from_google(property_id=property_id, daily_body=daily, query_body=queries,
            end_date=end, generated_at=clock)
        current = _locked_current_scope(svc)
        current_site, current_connection = _eligible(current, site_public_id)
        if (current_site.property_id != property_id or current_connection.id != connection_id
                or current_connection.encrypted_refresh_token != ciphertext):
            raise SeoError("seo_connection_changed", 409)
        current._audit("analysis_preview_completed", site_public_id)
        current.db.commit()
        return report
    except (SeoError, GoogleGscError) as exc:
        svc.db.rollback()
        if exc.code == "google_authorization_expired":
            svc.db.execute(update(SeoGoogleConnection).where(SeoGoogleConnection.id == connection_id,
                SeoGoogleConnection.tenant_id == svc.tenant, SeoGoogleConnection.store_id == svc.store,
                SeoGoogleConnection.user_id == svc.user, SeoGoogleConnection.status == "connected",
                SeoGoogleConnection.encrypted_refresh_token == ciphertext).values(status="reauthorization_required"))
        svc._audit("analysis_preview_failed", site_public_id, details={"code": exc.code})
        svc.db.commit()
        raise
