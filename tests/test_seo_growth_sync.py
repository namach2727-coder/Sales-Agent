from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.config import Settings
from app.seo_growth.persistence import (
    SeoMetricCoverage, SeoPropertyDailyMetric, SeoQueryPageMetric, SeoSyncRun,
)
from test_seo_growth_onboarding import api, connected, env, prefix
from app.seo_growth.sync import _upsert_daily
from app.seo_growth.google_client import GoogleGscError
from app.seo_growth.sync import (
    normalize_daily_rows,
    normalize_query_page_rows,
)


def test_daily_normalization_keeps_property_totals_independent_and_validates_window():
    rows = normalize_daily_rows(
        {"responseAggregationType": "byProperty", "rows": [
            {"keys": ["2026-10-01"], "clicks": 12, "impressions": 100,
             "ctr": 0.12, "position": 4.5},
            {"keys": ["2026-10-02"], "clicks": 0, "impressions": 0,
             "ctr": 0, "position": 0},
        ]},
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 2),
    )
    assert len(rows) == 2
    assert rows[0] == {
        "metric_date": date(2026, 10, 1), "clicks": 12, "impressions": 100,
        "ctr": 0.12, "position": 4.5,
    }
    assert rows[1]["ctr"] is None and rows[1]["position"] is None


@pytest.mark.parametrize("body", [
    {"responseAggregationType": "byPage", "rows": []},
    {"rows": [{"keys": ["2026-09-30"], "clicks": 1, "impressions": 2, "position": 1}]},
    {"rows": [{"keys": ["2026-10-01"], "clicks": 3, "impressions": 2, "position": 1}]},
    {"rows": [{"keys": ["2026-10-01"], "clicks": True, "impressions": 2, "position": 1}]},
    {"rows": [{"keys": ["2026-10-01"], "clicks": 1, "impressions": 2, "position": float("nan")}]},
])
def test_daily_normalization_rejects_invalid_or_non_property_rows(body):
    with pytest.raises(GoogleGscError):
        normalize_daily_rows(body, start_date=date(2026, 10, 1), end_date=date(2026, 10, 2))


def test_query_page_normalization_hashes_rows_deterministically_and_checks_property():
    body = {"rows": [
        {"keys": ["keyword one", "https://example.com/blog/a"],
         "clicks": 4, "impressions": 20, "ctr": 0.2, "position": 2.5},
    ]}
    args = {"property_id": "sc-domain:example.com",
            "start_date": date(2026, 10, 1), "end_date": date(2026, 10, 7)}
    first = normalize_query_page_rows(body, **args)
    second = normalize_query_page_rows(body, **args)
    assert first == second
    assert len(first[0]["row_key"]) == 64
    assert first[0]["sample_rank"] == 1


@pytest.mark.parametrize("page", [
    "https://attacker.example/blog/a",
    "https://example.com.evil.test/blog/a",
    "https://user:pass@example.com/blog/a",
    "javascript:alert(1)",
])
def test_query_page_normalization_rejects_pages_outside_property(page):
    with pytest.raises(GoogleGscError):
        normalize_query_page_rows(
            {"rows": [{"keys": ["query", page], "clicks": 1, "impressions": 2, "position": 1}]},
            property_id="sc-domain:example.com",
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 7),
        )


def test_query_page_normalization_rejects_duplicate_rows():
    row = {"keys": ["query", "https://example.com/a"], "clicks": 1,
           "impressions": 2, "position": 1}
    with pytest.raises(GoogleGscError):
        normalize_query_page_rows(
            {"rows": [row, row]}, property_id="sc-domain:example.com",
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 7),
        )



def test_f2b_sync_feature_flag_is_off_by_default():
    assert Settings(_env_file=None).seo_data_sync_enabled is False


def test_daily_window_replacement_removes_stale_dates_and_is_idempotent():
    engine = create_engine("sqlite://")
    tables = [SeoSyncRun.__table__, SeoPropertyDailyMetric.__table__]
    Base.metadata.create_all(engine, tables=tables)
    scope = {"tenant_id": 11, "store_id": 21, "site_id": 31}
    with Session(engine) as db:
        db.add_all([
            SeoSyncRun(id=1, **scope, status="succeeded", search_type="web",
                start_date=date(2026, 10, 1), end_date=date(2026, 10, 2)),
            SeoSyncRun(id=2, **scope, status="running", search_type="web",
                start_date=date(2026, 10, 1), end_date=date(2026, 10, 2)),
            SeoPropertyDailyMetric(**scope, metric_date=date(2026, 10, 1), search_type="web",
                clicks=5, impressions=20, ctr=0.25, position=2.0, source_run_id=1),
            SeoPropertyDailyMetric(**scope, metric_date=date(2026, 10, 2), search_type="web",
                clicks=7, impressions=30, ctr=0.233333, position=3.0, source_run_id=1),
        ])
        db.commit()
        _upsert_daily(db, scope=scope, run_id=2, search_type="web",
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 2),
            rows=[{"metric_date": date(2026, 10, 1), "clicks": 8, "impressions": 40,
                   "ctr": 0.2, "position": 1.5}])
        db.commit()
        rows = db.scalars(select(SeoPropertyDailyMetric).order_by(SeoPropertyDailyMetric.metric_date)).all()
        assert len(rows) == 1
        assert rows[0].metric_date == date(2026, 10, 1)
        assert rows[0].clicks == 8
        assert rows[0].source_run_id == 2
    engine.dispose()


SYNC_HEADERS = {"Origin": "https://customer.example", "X-CSRF-Token": "seo"}


def test_sync_keeps_56_day_property_totals_and_28_day_query_sample_aligned(env, api):
    env["settings"].seo_data_sync_enabled = True
    env["settings"].seo_analysis_preview_enabled = True
    connection = connected(env)
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    end = datetime.now(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=3)
    current_start = end - timedelta(days=27)
    full_start = end - timedelta(days=55)
    calls = []

    def analytics(**kwargs):
        calls.append(kwargs)
        if kwargs["dimensions"] == ("date",):
            return {"rows": [
                {"keys": [(kwargs["start_date"] + timedelta(days=i)).isoformat()],
                 "clicks": 1, "impressions": 10, "position": 5.0}
                for i in range((kwargs["end_date"] - kwargs["start_date"]).days + 1)
            ]}
        return {"rows": [{
            "keys": ["sample query", "https://example.com/page"],
            "clicks": 2, "impressions": 20, "position": 3.0,
        }]}

    env["fake"].search_analytics = analytics
    endpoint = prefix(env) + f"/sites/{site.public_id}/sync"
    response = api.post(endpoint, headers=SYNC_HEADERS, json={
        "start_date": full_start.isoformat(), "end_date": end.isoformat(),
        "query_page_start_date": current_start.isoformat(),
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["start_date"], body["end_date"]) == (full_start.isoformat(), end.isoformat())
    assert body["query_page_window"] == {"start_date": current_start.isoformat(), "end_date": end.isoformat()}
    assert [call["dimensions"] for call in calls] == [("date",), ("query", "page")]
    assert (calls[0]["start_date"], calls[0]["end_date"]) == (full_start, end)
    assert (calls[1]["start_date"], calls[1]["end_date"]) == (current_start, end)

    coverage = list(env["db"].scalars(select(SeoMetricCoverage).order_by(SeoMetricCoverage.dimension)))
    date_coverage = next(row for row in coverage if row.dimension == "date")
    query_coverage = next(row for row in coverage if row.dimension == "query_page")
    assert (date_coverage.start_date, date_coverage.end_date) == (full_start, end)
    assert (query_coverage.start_date, query_coverage.end_date) == (current_start, end)
    stored_query = env["db"].scalar(select(SeoQueryPageMetric))
    assert (stored_query.start_date, stored_query.end_date) == (current_start, end)

    report = api.get(prefix(env) + f"/sites/{site.public_id}/analysis")
    assert report.status_code == 200, report.text
    assert report.json()["comparison"]["status"] == "comparable"
    assert report.json()["query_sample"]["coverage"] == "complete"
    assert report.json()["query_sample"]["window_start_date"] == current_start.isoformat()

    history = api.get(prefix(env) + f"/sites/{site.public_id}/sync-runs")
    assert history.status_code == 200, history.text
    history_coverage = history.json()["items"][0]["coverage"]
    assert {item["dimension"]: item["start_date"] for item in history_coverage} == {
        "date": full_start.isoformat(), "query_page": current_start.isoformat(),
    }


def test_sync_rejects_query_sample_windows_over_28_days_before_provider_calls(env, api):
    env["settings"].seo_data_sync_enabled = True
    connection = connected(env)
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    end = datetime.now(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=3)
    start = end - timedelta(days=55)
    response = api.post(prefix(env) + f"/sites/{site.public_id}/sync", headers=SYNC_HEADERS, json={
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "query_page_start_date": start.isoformat(),
    })
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "seo_sync_query_window_too_large"
    assert env["fake"].exchange_calls == 0
