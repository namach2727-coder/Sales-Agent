from types import SimpleNamespace

from app.seo_growth.crawler_policy import CrawlLimits
from app.seo_growth.crawler_preview import crawl_preview


def _page(url: str, body: bytes = b'<html><a href="/next">next</a></html>'):
    return SimpleNamespace(url=url, status_code=200, body=body)


def test_crawl_preview_stops_before_callbacks_when_host_budget_is_exhausted():
    requested = []
    lease_checks = []

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        requested.append(url)
        budget.record_page(url, depth=depth)
        return _page(url)

    result = crawl_preview(
        "https://example.com/",
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(max_pages=5, max_pages_per_host=1, max_depth=3),
        before_page=lambda url, depth: lease_checks.append((url, depth)),
        fetch_page=fetch_page,
    )

    assert requested == ["https://example.com/"]
    assert lease_checks == [("https://example.com/", 0)]
    assert result["coverage_status"] == "truncated"
    assert result["stop_reason"] == "seo_crawler_host_page_budget_exceeded"
    assert result["pages_crawled"] == 1
    assert result["pages_failed"] == 0



def test_crawl_preview_stops_before_callbacks_when_total_byte_budget_is_exhausted():
    requested = []
    lease_checks = []

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        requested.append(url)
        budget.record_page(url, depth=depth)
        budget.record_response_bytes(10)
        return _page(url)

    result = crawl_preview(
        "https://example.com/",
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(
            max_pages=5, max_pages_per_host=5, max_depth=3,
            max_response_bytes=10, max_total_bytes=10,
        ),
        before_page=lambda url, depth: lease_checks.append((url, depth)),
        fetch_page=fetch_page,
    )

    assert requested == ["https://example.com/"]
    assert lease_checks == [("https://example.com/", 0)]
    assert result["coverage_status"] == "truncated"
    assert result["stop_reason"] == "seo_crawler_total_byte_budget_exceeded"
    assert result["pages_crawled"] == 1
    assert result["pages_failed"] == 0



def test_crawl_preview_marks_link_discovery_cap_as_truncated():
    seed = "https://example.com/"
    links_html = "<html>" + "".join(
        f'<a href="/page-{index}">page</a>' for index in range(501)
    ) + "</html>"
    requested = []

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        requested.append(url)
        budget.record_page(url, depth=depth)
        body = links_html.encode() if url == seed else b"<html></html>"
        return _page(url, body)

    result = crawl_preview(
        seed,
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(
            max_pages=600, max_pages_per_host=600, max_depth=1,
        ),
        fetch_page=fetch_page,
    )

    assert len(requested) == 501
    assert result["link_discovery_truncated"] is True
    assert result["coverage_status"] == "truncated"
    assert result["stop_reason"] == "seo_crawler_link_budget_exceeded"
    assert result["limits"]["max_links_per_page"] == 500


def test_crawl_preview_redacts_query_and_fragment_from_canonical_url():
    seed = "https://example.com/"
    html = (
        '<html><head><link rel="canonical" '
        'href="https://example.com/clean?token=private#section"></head></html>'
    )

    def fetch_page(url, *, resolver, budget, depth, audit_callback):
        budget.record_page(url, depth=depth)
        return _page(url, html.encode())

    result = crawl_preview(
        seed,
        resolver=lambda _host, _port: ["93.184.216.34"],
        limits=CrawlLimits(max_pages=1, max_depth=0),
        fetch_page=fetch_page,
    )

    assert result["pages"][0]["canonical_url"] == "https://example.com/clean"
    assert "private" not in str(result)
    assert "#section" not in str(result)
