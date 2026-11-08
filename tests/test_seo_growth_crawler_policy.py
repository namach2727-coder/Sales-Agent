import pytest

from app.seo_growth.crawler_policy import (
    CrawlBudget,
    CrawlLimits,
    CrawlPolicyError,
    robots_allows,
    validate_html_response,
)


def test_default_crawl_limits_are_bounded():
    limits = CrawlLimits()
    assert limits.max_pages == 100
    assert limits.max_depth == 3
    assert limits.max_redirects == 5
    assert limits.max_response_bytes < limits.max_total_bytes


@pytest.mark.parametrize("kwargs", [
    {"max_pages": 0}, {"max_depth": -1}, {"max_redirects": 0},
    {"max_response_bytes": 20, "max_total_bytes": 10},
    {"max_elapsed_seconds": 1, "request_timeout_seconds": 2},
])
def test_invalid_crawl_limits_are_rejected(kwargs):
    with pytest.raises(CrawlPolicyError, match="seo_crawler_invalid_limits"):
        CrawlLimits(**kwargs)


def test_page_budget_enforces_global_host_and_depth_limits():
    budget = CrawlBudget(CrawlLimits(max_pages=2, max_pages_per_host=1, max_depth=1))
    budget.record_page("https://a.example.com/", depth=0)
    with pytest.raises(CrawlPolicyError, match="seo_crawler_host_page_budget_exceeded"):
        budget.record_page("https://a.example.com/next", depth=1)
    budget.record_page("https://b.example.com/", depth=1)
    with pytest.raises(CrawlPolicyError, match="seo_crawler_page_budget_exceeded"):
        budget.record_page("https://c.example.com/", depth=0)


def test_depth_limit_rejects_before_incrementing_page_count():
    budget = CrawlBudget(CrawlLimits(max_depth=1))
    with pytest.raises(CrawlPolicyError, match="seo_crawler_depth_limit_exceeded"):
        budget.record_page("https://example.com/deep", depth=2)
    assert budget.pages == 0


def test_response_and_total_byte_budgets_are_enforced():
    budget = CrawlBudget(CrawlLimits(max_response_bytes=6, max_total_bytes=10))
    budget.record_response_bytes(6)
    budget.record_response_bytes(4)
    with pytest.raises(CrawlPolicyError, match="seo_crawler_response_too_large"):
        budget.record_response_bytes(7)
    with pytest.raises(CrawlPolicyError, match="seo_crawler_total_byte_budget_exceeded"):
        budget.record_response_bytes(1)


def test_elapsed_time_budget_is_enforced_with_injected_clock():
    now = [10.0]
    budget = CrawlBudget(
        CrawlLimits(max_elapsed_seconds=5, request_timeout_seconds=2),
        started_at=10.0, clock=lambda: now[0],
    )
    budget.record_page("https://example.com/", depth=0)
    now[0] = 15.0
    with pytest.raises(CrawlPolicyError, match="seo_crawler_time_budget_exceeded"):
        budget.record_page("https://example.com/next", depth=1)


def test_html_response_accepts_html_and_xhtml_only():
    assert validate_html_response(200, {"Content-Type": "text/html; charset=utf-8"},
                                  max_response_bytes=100) == "text/html"
    assert validate_html_response(200, {"content-type": "application/xhtml+xml"},
                                  max_response_bytes=100) == "application/xhtml+xml"


@pytest.mark.parametrize("status,headers,code", [
    (404, {"Content-Type": "text/html"}, "seo_crawler_http_status_rejected"),
    (200, {"Content-Type": "application/json"}, "seo_crawler_content_type_rejected"),
    (200, {"Content-Type": "text/html", "Content-Length": "101"}, "seo_crawler_response_too_large"),
    (200, {"Content-Type": "text/html", "Content-Length": "-1"}, "seo_crawler_invalid_content_length"),
    (200, {"Content-Type": "text/html", "Content-Length": "abc"}, "seo_crawler_invalid_content_length"),
])
def test_html_response_rejects_unsafe_or_unexpected_headers(status, headers, code):
    with pytest.raises(CrawlPolicyError, match=code):
        validate_html_response(status, headers, max_response_bytes=100)


def test_robots_parser_respects_disallow_and_allow_rules():
    body = b"User-agent: *\nDisallow: /private\nAllow: /private/public\n"
    assert not robots_allows(
        robots_url="https://example.com/robots.txt", page_url="https://example.com/private/a",
        user_agent="DirectPilotBot", status_code=200, body=body,
    )
    assert robots_allows(
        robots_url="https://example.com/robots.txt", page_url="https://example.com/private/public/a",
        user_agent="DirectPilotBot", status_code=200, body=body,
    )


@pytest.mark.parametrize("status,expected", [
    (404, True), (410, True), (401, False), (403, False),
    (429, False), (500, False), (503, False), (302, False),
])
def test_robots_fetch_failure_policy(status, expected):
    assert robots_allows(
        robots_url="https://example.com/robots.txt", page_url="https://example.com/",
        user_agent="DirectPilotBot", status_code=status, body=None,
    ) is expected


def test_robots_parser_uses_specific_agent_group_over_wildcard():
    body = (
        b"User-agent: *\nDisallow: /private\n"
        b"User-agent: DirectPilotBot\nAllow: /private/public\n"
    )
    assert robots_allows(
        robots_url="https://example.com/robots.txt",
        page_url="https://example.com/private/public/page",
        user_agent="DirectPilotBot/1.0",
        status_code=200,
        body=body,
    )
    assert not robots_allows(
        robots_url="https://example.com/robots.txt",
        page_url="https://example.com/private/public/page",
        user_agent="OtherCrawler",
        status_code=200,
        body=body,
    )


def test_robots_parser_supports_wildcard_and_end_anchor():
    body = b"User-agent: *\nDisallow: /*.pdf$\nAllow: /public/*.pdf$\n"
    assert not robots_allows(
        robots_url="https://example.com/robots.txt",
        page_url="https://example.com/files/report.pdf",
        user_agent="DirectPilotBot",
        status_code=200,
        body=body,
    )
    assert robots_allows(
        robots_url="https://example.com/robots.txt",
        page_url="https://example.com/public/report.pdf",
        user_agent="DirectPilotBot",
        status_code=200,
        body=body,
    )
