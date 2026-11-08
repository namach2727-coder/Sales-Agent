from types import SimpleNamespace

from app.seo_growth.crawler_policy import CrawlLimits
from app.seo_growth.crawler_preview import crawl_preview


def _page(url: str):
    return SimpleNamespace(
        url=url,
        status_code=200,
        body=b'<html><a href="/next">next</a></html>',
    )


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
