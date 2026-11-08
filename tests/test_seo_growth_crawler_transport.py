import socket
import ssl

import pytest

from app.seo_growth.crawler_policy import CrawlBudget, CrawlLimits, CrawlPolicyError
from app.seo_growth.crawler_security import CrawlTargetError
from app.seo_growth.crawler_transport import (
    CrawlTransportError,
    _PinnedHTTPConnection,
    _request_with_redirects,
    fetch_html_page,
)


def _resolver(_hostname, _port):
    return ["93.184.216.34"]


def _fake_request(target, pinned_ip, *, timeout, max_body_bytes):
    if target.path_and_query == "/robots.txt":
        return 200, {"content-type": "text/plain"}, b"User-agent: *\nDisallow: /private", None
    return 200, {"content-type": "text/html"}, b"<html>ok</html>", None


def test_pinned_connection_opens_socket_to_numeric_ip_not_hostname(monkeypatch):
    calls = []
    class FakeSocket:
        def settimeout(self, timeout):
            pass
        def close(self):
            pass
    def fake_create_connection(address, timeout):
        calls.append((address, timeout))
        return FakeSocket()
    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    from app.seo_growth.crawler_security import normalize_crawl_url
    target = normalize_crawl_url("http://public.example.com/")
    connection = _PinnedHTTPConnection(target, "93.184.216.34", 3.0, None)
    connection.connect()
    assert len(calls) == 1
    assert calls[0][0] == ("93.184.216.34", 80)
    assert calls[0][1] == pytest.approx(3.0, abs=0.01)
    assert connection.sock is not None
    connection.close()


def test_pinned_https_keeps_original_hostname_as_tls_sni(monkeypatch):
    calls = []
    class FakeSocket:
        def settimeout(self, timeout):
            pass
        def close(self):
            pass
    class FakeContext:
        def wrap_socket(self, sock, *, server_hostname):
            calls.append(server_hostname)
            return sock
    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: FakeSocket())
    from app.seo_growth.crawler_security import normalize_crawl_url
    target = normalize_crawl_url("https://public.example.com/")
    connection = _PinnedHTTPConnection(target, "93.184.216.34", 3.0, FakeContext())
    connection.connect()
    assert calls == ["public.example.com"]
    connection.close()


def test_redirects_are_revalidated_and_connection_uses_redirect_ip():
    calls = []
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        calls.append((target.url, pinned_ip))
        if target.path_and_query == "/start":
            return 302, {"location": "/final"}, b"", "/final"
        return 200, {"content-type": "text/html"}, b"ok", None
    target, status, headers, body = _request_with_redirects(
        "https://first.example.com/start", resolver=_resolver,
        budget=CrawlBudget(), max_redirects=2, max_body_bytes=100,
        request_once=request_once,
    )
    assert status == 200
    assert target.url == "https://first.example.com/final"
    assert calls == [
        ("https://first.example.com/start", "93.184.216.34"),
        ("https://first.example.com/final", "93.184.216.34"),
    ]


def test_redirect_to_private_address_is_rejected():
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        return 302, {"location": "http://private.example.com/"}, b"", "http://private.example.com/"
    def resolver(hostname, port):
        return ["127.0.0.1"] if hostname == "private.example.com" else ["93.184.216.34"]
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        _request_with_redirects(
            "https://public.example.com/", resolver=resolver,
            budget=CrawlBudget(), max_redirects=2, max_body_bytes=100,
            request_once=request_once,
        )


def test_redirect_limit_is_enforced():
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        return 302, {"location": "/again"}, b"", "/again"
    with pytest.raises(CrawlTransportError, match="seo_crawler_redirect_limit_exceeded"):
        _request_with_redirects(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(), max_redirects=1, max_body_bytes=100,
            request_once=request_once,
        )


def test_fetch_checks_robots_before_requesting_page():
    requests = []
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        requests.append(target.path_and_query)
        return _fake_request(target, pinned_ip, timeout=timeout, max_body_bytes=max_body_bytes)
    with pytest.raises(CrawlTransportError, match="seo_crawler_robots_disallowed"):
        fetch_html_page(
            "https://public.example.com/private/page", resolver=_resolver,
            budget=CrawlBudget(), request_once=request_once,
        )
    assert requests == ["/robots.txt"]


def test_fetch_returns_html_after_robots_allows_it():
    requests = []
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        requests.append(target.path_and_query)
        return 200, {"content-type": "text/html"}, b"<html>ok</html>", None
    page = fetch_html_page(
        "https://public.example.com/", resolver=_resolver,
        budget=CrawlBudget(), request_once=request_once,
    )
    assert page.status_code == 200
    assert page.body == b"<html>ok</html>"
    assert requests == ["/robots.txt", "/"]



def test_fetch_emits_sanitized_robots_and_page_audit_events():
    events = []

    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 404, {}, b"", None
        return 200, {"content-type": "text/html"}, b"<html>ok</html>", None

    page = fetch_html_page(
        "https://public.example.com/catalog/item?session=secret",
        resolver=_resolver,
        budget=CrawlBudget(),
        request_once=request_once,
        audit_callback=lambda **event: events.append(event),
    )
    assert [event["event_kind"] for event in events] == ["robots", "page"]
    assert events[0]["outcome"] == "allowed"
    assert events[0]["robots_decision"] == "unavailable_allow"
    assert events[1]["outcome"] == "fetched"
    assert events[1]["robots_decision"] == "not_checked"
    assert all("secret" not in event["raw_url"] for event in events)
    assert page.robots_status_code == 404
    assert page.page_bytes_received == len(b"<html>ok</html>")


def test_fetch_emits_blocked_robots_audit_before_rejecting_page():
    events = []
    requests = []

    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        requests.append(target.path_and_query)
        return 200, {}, b"User-agent: *\nDisallow: /private\n", None

    with pytest.raises(CrawlTransportError, match="seo_crawler_robots_disallowed"):
        fetch_html_page(
            "https://public.example.com/private/page",
            resolver=_resolver,
            budget=CrawlBudget(),
            request_once=request_once,
            audit_callback=lambda **event: events.append(event),
        )
    assert requests == ["/robots.txt"]
    assert len(events) == 1
    assert events[0]["outcome"] == "blocked"
    assert events[0]["robots_decision"] == "disallow"


def test_fetch_emits_failed_page_audit_when_html_status_is_rejected():
    events = []

    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 404, {}, b"", None
        return 503, {}, b"", None

    with pytest.raises(CrawlPolicyError, match="seo_crawler_http_status_rejected"):
        fetch_html_page(
            "https://public.example.com/",
            resolver=_resolver,
            budget=CrawlBudget(),
            request_once=request_once,
            audit_callback=lambda **event: events.append(event),
        )
    assert len(events) == 2
    assert events[1]["event_kind"] == "page"
    assert events[1]["outcome"] == "failed"
    assert events[1]["http_status"] == 503
    assert events[1]["error_code"] == "seo_crawler_http_status_rejected"


def test_fetch_rejects_compressed_content_without_decompression_budget():
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 404, {}, b"", None
        return 200, {
            "content-type": "text/html", "content-encoding": "gzip",
        }, b"x", None
    with pytest.raises(CrawlTransportError, match="seo_crawler_content_encoding_rejected"):
        fetch_html_page(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(), request_once=request_once,
        )


def test_dns_resolution_is_repeated_for_each_redirect_target():
    calls = []
    def resolver(hostname, port):
        calls.append((hostname, port))
        return ["93.184.216.34"]
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/":
            return 302, {"location": "/again"}, b"", "/again"
        return 200, {"content-type": "text/html"}, b"ok", None
    _request_with_redirects(
        "https://first.example.com/", resolver=resolver,
        budget=CrawlBudget(), max_redirects=2, max_body_bytes=100,
        request_once=request_once,
    )
    assert calls == [("first.example.com", 443), ("first.example.com", 443)]


def test_transport_does_not_send_page_request_when_robots_returns_server_error():
    requests = []
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        requests.append(target.path_and_query)
        return 503, {}, b"", None
    with pytest.raises(CrawlTransportError, match="seo_crawler_robots_disallowed"):
        fetch_html_page(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(), request_once=request_once,
        )
    assert requests == ["/robots.txt"]


def test_cross_origin_redirect_is_rejected_even_when_public():
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        return 302, {"location": "https://other.example.com/"}, b"", "https://other.example.com/"
    with pytest.raises(CrawlTransportError, match="seo_crawler_cross_origin_redirect_rejected"):
        _request_with_redirects(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(), max_redirects=2, max_body_bytes=100,
            request_once=request_once,
        )


def test_robots_body_counts_toward_total_crawl_byte_budget():
    limits = CrawlLimits(max_response_bytes=20, max_total_bytes=20)
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 200, {"content-type": "text/plain"}, b"User-agent: *\n", None
        return 200, {"content-type": "text/html"}, b"1234567", None
    with pytest.raises(CrawlPolicyError, match="seo_crawler_total_byte_budget_exceeded"):
        fetch_html_page(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(limits), request_once=request_once,
        )


def test_injected_transport_cannot_return_body_over_configured_cap():
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 404, {}, b"", None
        return 200, {"content-type": "text/html"}, b"x" * (max_body_bytes + 1), None
    with pytest.raises(CrawlTransportError, match="seo_crawler_response_too_large"):
        fetch_html_page(
            "https://public.example.com/", resolver=_resolver,
            budget=CrawlBudget(CrawlLimits(max_response_bytes=8, max_total_bytes=20)),
            request_once=request_once,
        )


def test_timeout_is_recomputed_before_each_pinned_ip_attempt():
    now = [0.0]
    timeouts = []
    def resolver(_hostname, _port):
        return ["93.184.216.34", "1.1.1.1"]
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        timeouts.append(timeout)
        if len(timeouts) == 1:
            now[0] += 3.0
            raise CrawlTransportError("seo_crawler_network_request_failed")
        return 200, {"content-type": "text/html"}, b"ok", None
    budget = CrawlBudget(
        CrawlLimits(max_elapsed_seconds=10, request_timeout_seconds=8),
        started_at=0.0, clock=lambda: now[0],
    )
    _request_with_redirects(
        "https://public.example.com/", resolver=resolver, budget=budget,
        max_redirects=0, max_body_bytes=100, request_once=request_once,
    )
    assert timeouts == [8, 7]
