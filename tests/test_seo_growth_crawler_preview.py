from types import SimpleNamespace

import pytest

from app.seo_growth.crawler_policy import CrawlBudget, CrawlLimits, CrawlPolicyError
from app.seo_growth.crawler_preview import crawl_preview, extract_crawl_links
from app.seo_growth.crawler_transport import CrawlTransportError


def _page(url, body):
    return SimpleNamespace(
        url=url,
        status_code=200,
        body=body.encode("utf-8"),
    )


def test_extract_crawl_links_keeps_only_same_origin_prefix_and_drops_query():
    html = """
    <a href="/blog/child?utm_source=secret#section">child</a>
    <a href="/blog/child">duplicate</a>
    <a href="/blogger/outside">outside prefix</a>
    <a href="https://other.example.com/blog/x">external host</a>
    <a href="mailto:test@example.com">email</a>
    """
    links = extract_crawl_links(
        html, "https://example.com/blog/", allowed_path_prefix="/blog",
    )
    assert links == ["https://example.com/blog/child"]


def test_crawl_preview_follows_bounded_same_host_graph_and_returns_page_findings():
    requested = []
    lease_checks = []

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        requested.append((url, depth))
        budget.record_page(url, depth=depth)
        body = (
            '<html><title>Home</title><h1>Home</h1>'
            '<a href="/blog/child?token=secret">child</a>'
            '<a href="https://other.example.com/blog/no">external</a></html>'
            if depth == 0 else
            '<html><title>Child</title><h1>Child</h1></html>'
        )
        budget.record_response_bytes(len(body.encode()))
        return _page(url, body)

    result = crawl_preview(
        "https://example.com/blog/?session=secret",
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(max_pages=5, max_depth=2),
        allowed_path_prefix="/blog",
        before_page=lambda url, depth: lease_checks.append((url, depth)),
        fetch_page=fetch_page,
    )
    assert requested == [
        ("https://example.com/blog/", 0),
        ("https://example.com/blog/child", 1),
    ]
    assert lease_checks == requested
    assert result["coverage_status"] == "complete"
    assert result["pages_crawled"] == 2
    assert result["pages"][0]["title"] == "Home"
    assert result["pages"][1]["title"] == "Child"
    assert "secret" not in result["seed_url"]


def test_crawl_preview_reports_partial_coverage_when_one_page_fails():
    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        budget.record_page(url, depth=depth)
        if depth == 1:
            raise CrawlTransportError("seo_crawler_network_request_failed")
        body = '<a href="/child">child</a>'
        return _page(url, body)

    result = crawl_preview(
        "https://example.com/",
        resolver=lambda _host, _port: ["93.184.216.34"],
        fetch_page=fetch_page,
    )
    assert result["coverage_status"] == "partial"
    assert result["pages_crawled"] == 1
    assert result["pages_failed"] == 1
    assert result["failures"][0]["error_code"] == "seo_crawler_network_request_failed"


def test_crawl_preview_stops_when_global_page_budget_is_reached():
    requested = []

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        requested.append(url)
        budget.record_page(url, depth=depth)
        return _page(url, '<a href="/next">next</a>')

    result = crawl_preview(
        "https://example.com/",
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(max_pages=1, max_depth=3),
        fetch_page=fetch_page,
    )
    assert requested == ["https://example.com/"]
    assert result["coverage_status"] == "truncated"
    assert result["stop_reason"] == "seo_crawler_page_budget_exceeded"


def test_crawl_preview_rejects_seed_outside_property_path():
    with pytest.raises(ValueError, match="seo_crawler_seed_out_of_scope"):
        crawl_preview(
            "https://example.com/private/",
            resolver=lambda _host, _port: ["93.184.216.34"],
            allowed_path_prefix="/public",
        )
