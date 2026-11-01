from datetime import date, timedelta
import pytest

from app.seo_growth.analysis import DailyMetric, QueryPageMetric, build_seo_report

def test_real_directpilot_sample_has_unknown_seventh_day():
    rows = [
        DailyMetric(date(2026, 10, 25), 1, 5, 5.0),
        DailyMetric(date(2026, 10, 26), 1, 4, 40.75),
        DailyMetric(date(2026, 10, 27), 0, 6, 33.83),
        DailyMetric(date(2026, 10, 28), 0, 1, 10.0),
        DailyMetric(date(2026, 10, 29), 1, 37, 27.05),
        DailyMetric(date(2026, 10, 30), 0, 1, 9.0),
    ]
    report = build_seo_report(
        start_date=date(2026, 10, 25), end_date=date(2026, 10, 31),
        daily_rows=rows, query_page_rows=[],
    )
    assert report.total_clicks == 3
    assert report.total_impressions == 54
    assert report.ctr == pytest.approx(3 / 54)
    assert report.weighted_position == pytest.approx(26.12648148)
    assert report.observed_days == 6
    assert report.missing_days == (date(2026, 10, 31),)
    assert report.coverage == "missing_date_rows"
    assert any("unknown" in warning for warning in report.warnings)

def test_query_rows_are_not_summed_into_site_totals():
    d = date(2026, 10, 30)
    report = build_seo_report(
        start_date=d, end_date=d,
        daily_rows=[DailyMetric(d, 12, 100, 9.0)],
        query_page_rows=[QueryPageMetric("best widget", "https://example.org/a", 1, 400, 10.5)],
    )
    assert (report.total_clicks, report.total_impressions) == (12, 100)
    assert len(report.opportunities) == 1
    assert report.opportunities[0].kind == "snippet_review"
    assert report.opportunities[0].action_mode == "proposal_only"
    assert not hasattr(report.opportunities[0], "predicted_clicks")

def test_low_sample_does_not_claim_opportunity_or_position():
    d = date(2026, 10, 30)
    report = build_seo_report(
        start_date=d, end_date=d, daily_rows=[],
        query_page_rows=[QueryPageMetric("test", "https://example.org/", 0, 8, 11)],
    )
    assert report.opportunities == ()
    assert report.ctr is None
    assert report.weighted_position is None

def test_duplicate_date_is_rejected():
    d = date(2026, 10, 30)
    with pytest.raises(ValueError, match="duplicate"):
        build_seo_report(start_date=d, end_date=d,
                         daily_rows=[DailyMetric(d, 1, 10, 3), DailyMetric(d, 1, 10, 3)],
                         query_page_rows=[])

@pytest.mark.parametrize("clicks,impressions,position", [
    (-1, 5, 8), (7, 5, 8), (1, -1, 8), (1, 5, float("nan")), (1, 5, 0), (True, 5, 8),
])
def test_invalid_metrics_rejected(clicks, impressions, position):
    d = date(2026, 10, 30)
    with pytest.raises(ValueError):
        build_seo_report(start_date=d, end_date=d,
                         daily_rows=[DailyMetric(d, clicks, impressions, position)],
                         query_page_rows=[])

def test_review_priority_is_evidence_not_predicted_uplift():
    d = date(2026, 10, 30)
    report = build_seo_report(
        start_date=d, end_date=d, daily_rows=[DailyMetric(d, 5, 900, 18)],
        query_page_rows=[
            QueryPageMetric("low-ctr", "https://example.org/a", 2, 200, 9),
            QueryPageMetric("intent", "https://example.org/b", 4, 300, 25),
            QueryPageMetric("onpage", "https://example.org/c", 4, 80, 18),
        ],
    )
    assert [x.kind for x in report.opportunities] == [
        "intent_review", "snippet_review", "onpage_review",
    ]
    assert all(x.action_mode == "proposal_only" for x in report.opportunities)
    assert report.coverage == "complete_date_rows"

def test_position_undefined_if_any_impression_weight_lacks_position():
    d = date(2026, 10, 30)
    report = build_seo_report(start_date=d, end_date=d + timedelta(days=1),
                              daily_rows=[DailyMetric(d, 1, 10, 10),
                                          DailyMetric(d + timedelta(days=1), 1, 10, None)],
                              query_page_rows=[])
    assert report.weighted_position is None
