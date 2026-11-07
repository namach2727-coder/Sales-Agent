"""Read-only reports and sync history from persisted, tenant-scoped GSC evidence."""
from datetime import UTC, date, datetime, timedelta
from dataclasses import asdict
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.seo_growth.analysis import DailyMetric, QueryPageMetric, build_seo_report
from app.seo_growth.models import SeoSite
from app.seo_growth.persistence import (
    SeoMetricCoverage, SeoPropertyDailyMetric, SeoQueryPageMetric, SeoSyncRun,
)
from app.seo_growth.reporting import WINDOW_DAYS, _eligible, _locked_current_scope
from app.seo_growth.security import SeoError
from app.seo_growth.service import SeoOnboardingService
from app.seo_growth.sync import _scope


def sync_history(svc: SeoOnboardingService, site_public_id: str, *, limit: int = 20,
                 offset: int = 0) -> dict:
    if not svc.settings.seo_data_sync_enabled:
        raise SeoError("seo_sync_not_enabled", 403)
    site, _connection = _scope(svc, site_public_id)
    base = select(SeoSyncRun).where(
        SeoSyncRun.tenant_id == svc.tenant,
        SeoSyncRun.store_id == svc.store,
        SeoSyncRun.site_id == site.id,
    )
    total = svc.db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = list(svc.db.scalars(base.order_by(
        SeoSyncRun.created_at.desc(), SeoSyncRun.id.desc()
    ).limit(limit).offset(offset)))
    run_ids = [row.id for row in rows]
    coverage_rows = list(svc.db.scalars(select(SeoMetricCoverage).where(
        SeoMetricCoverage.tenant_id == svc.tenant,
        SeoMetricCoverage.store_id == svc.store,
        SeoMetricCoverage.site_id == site.id,
        SeoMetricCoverage.source_run_id.in_(run_ids),
    ).order_by(SeoMetricCoverage.source_run_id, SeoMetricCoverage.dimension))) if run_ids else []
    coverage_by_run: dict[int, list[dict]] = {}
    for coverage in coverage_rows:
        coverage_by_run.setdefault(coverage.source_run_id, []).append({
            "dimension": coverage.dimension,
            "start_date": coverage.start_date.isoformat(),
            "end_date": coverage.end_date.isoformat(),
            "status": coverage.coverage_status,
            "rows_received": coverage.rows_received,
            "row_limit": coverage.row_limit,
        })
    latest = svc.db.scalar(base.where(
        SeoSyncRun.status == "succeeded"
    ).order_by(SeoSyncRun.completed_at.desc(), SeoSyncRun.id.desc()).limit(1))
    return {
        "items": [{
            "run_id": row.id,
            "status": row.status,
            "search_type": row.search_type,
            "start_date": row.start_date.isoformat(),
            "end_date": row.end_date.isoformat(),
            "rows_received": row.rows_received,
            "error_code": row.error_code,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "coverage": coverage_by_run.get(row.id, []),
        } for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "latest_successful_sync_at": latest.completed_at.isoformat() if latest and latest.completed_at else None,
    }


def _period(*, start: date, end: date, rows: list[DailyMetric], query_rows: list[QueryPageMetric]):
    report = build_seo_report(start_date=start, end_date=end,
        daily_rows=rows, query_page_rows=query_rows)
    by_day = {row.day: row for row in rows}
    daily = []
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        row = by_day.get(day)
        daily.append({
            "date": day.isoformat(),
            "clicks": row.clicks if row else None,
            "impressions": row.impressions if row else None,
            "ctr": row.clicks / row.impressions if row and row.impressions else None,
            "position": row.position if row else None,
        })
    return report, {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "observed_days": report.observed_days,
        "missing_dates": [item.isoformat() for item in report.missing_days],
        "coverage": report.coverage,
        "clicks": report.total_clicks if report.observed_days else None,
        "impressions": report.total_impressions if report.observed_days else None,
        "ctr": report.ctr,
        "position": report.weighted_position,
        "daily": daily,
    }


def persisted_analysis(svc: SeoOnboardingService, site_public_id: str) -> dict:
    if not svc.settings.seo_data_sync_enabled:
        raise SeoError("seo_sync_not_enabled", 403)
    if not svc.settings.seo_analysis_preview_enabled:
        raise SeoError("seo_analysis_not_enabled", 403)
    svc = _locked_current_scope(svc)
    site, _connection = _eligible(svc, site_public_id)
    end = datetime.now(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=3)
    current_start = end - timedelta(days=WINDOW_DAYS - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=WINDOW_DAYS - 1)

    daily_rows = list(svc.db.scalars(select(SeoPropertyDailyMetric).where(
        SeoPropertyDailyMetric.tenant_id == svc.tenant,
        SeoPropertyDailyMetric.store_id == svc.store,
        SeoPropertyDailyMetric.site_id == site.id,
        SeoPropertyDailyMetric.search_type == "web",
        SeoPropertyDailyMetric.metric_date >= previous_start,
        SeoPropertyDailyMetric.metric_date <= end,
    ).order_by(SeoPropertyDailyMetric.metric_date)))
    daily = [DailyMetric(row.metric_date, row.clicks, row.impressions,
        float(row.position) if row.position is not None else None) for row in daily_rows]
    current_daily = [row for row in daily if current_start <= row.day <= end]
    previous_daily = [row for row in daily if previous_start <= row.day <= previous_end]

    query_coverage = svc.db.scalar(select(SeoMetricCoverage).where(
        SeoMetricCoverage.tenant_id == svc.tenant,
        SeoMetricCoverage.store_id == svc.store,
        SeoMetricCoverage.site_id == site.id,
        SeoMetricCoverage.search_type == "web",
        SeoMetricCoverage.dimension == "query_page",
        SeoMetricCoverage.start_date == current_start,
        SeoMetricCoverage.end_date == end,
    ))
    query_rows = []
    if query_coverage and query_coverage.coverage_status in {"complete", "truncated", "empty"}:
        stored = svc.db.scalars(select(SeoQueryPageMetric).where(
            SeoQueryPageMetric.tenant_id == svc.tenant,
            SeoQueryPageMetric.store_id == svc.store,
            SeoQueryPageMetric.site_id == site.id,
            SeoQueryPageMetric.search_type == "web",
            SeoQueryPageMetric.start_date == current_start,
            SeoQueryPageMetric.end_date == end,
        ).order_by(SeoQueryPageMetric.sample_rank)).all()
        query_rows = [QueryPageMetric(row.query_text, row.page_url, row.clicks,
            row.impressions, float(row.position) if row.position is not None else None)
            for row in stored]

    recent, current = _period(start=current_start, end=end, rows=current_daily, query_rows=query_rows)
    prior, previous = _period(start=previous_start, end=previous_end, rows=previous_daily, query_rows=[])
    complete = not recent.missing_days and not prior.missing_days

    def change(a, b):
        return round((a - b) / b * 100, 2) if complete and b > 0 else None

    latest = svc.db.scalar(select(SeoSyncRun).where(
        SeoSyncRun.tenant_id == svc.tenant,
        SeoSyncRun.store_id == svc.store,
        SeoSyncRun.site_id == site.id,
        SeoSyncRun.status == "succeeded",
    ).order_by(SeoSyncRun.completed_at.desc(), SeoSyncRun.id.desc()).limit(1))
    query_status = query_coverage.coverage_status if query_coverage else "unknown"
    warnings = [*recent.warnings, *prior.warnings,
        "Property totals are calculated only from persisted daily property metrics.",
        "Query/page rows are a bounded sample and are never used to calculate property totals.",
        "Period changes do not establish cause or control for seasonality or query mix."]
    if query_status == "truncated":
        warnings.append("The query/page sample reached its row limit and is not exhaustive.")
    if query_status == "unknown":
        warnings.append("No successful query/page sample exists for the current reporting window.")
    return {
        "kind": "persisted_analysis",
        "persistence": "database",
        "property_id": site.property_id,
        "source": "google_search_console",
        "data_state": "final",
        "search_type": "web",
        "timezone": "America/Los_Angeles",
        "generated_at": datetime.now(UTC).isoformat(),
        "last_successful_sync_at": latest.completed_at.isoformat() if latest and latest.completed_at else None,
        "current": current,
        "previous": previous,
        "comparison": {
            "status": "comparable" if complete else "incomplete_coverage",
            "clicks_change_percent": change(recent.total_clicks, prior.total_clicks),
            "impressions_change_percent": change(recent.total_impressions, prior.total_impressions),
            "ctr_change_percentage_points": round((recent.ctr - prior.ctr) * 100, 4)
                if complete and recent.ctr is not None and prior.ctr is not None else None,
            "position_change": round(recent.weighted_position - prior.weighted_position, 4)
                if complete and recent.weighted_position is not None and prior.weighted_position is not None else None,
        },
        "opportunities": [asdict(item) for item in recent.opportunities],
        "query_sample": {
            "row_limit": query_coverage.row_limit if query_coverage else 500,
            "received_rows": query_coverage.rows_received if query_coverage else 0,
            "limit_reached": query_status == "truncated",
            "coverage": query_status,
            "window_start_date": current_start.isoformat(),
            "window_end_date": end.isoformat(),
        },
        "warnings": list(dict.fromkeys(warnings)),
    }
