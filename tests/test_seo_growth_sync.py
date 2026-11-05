from datetime import date

import pytest

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
