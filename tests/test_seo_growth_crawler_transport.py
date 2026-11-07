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
    assert calls == [(("93.184.216.34", 80), 3.0)]
    assert connection.sock is not None
    connection.close()


def test_pinned_https_keeps_original_hostname_as_tls_sni(monkeypatch):
    calls = []
    class FakeSocket:
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
    limits = CrawlLimits(max_response_bytes=100, max_total_bytes=10)
    def request_once(target, pinned_ip, *, timeout, max_body_bytes):
        if target.path_and_query == "/robots.txt":
            return 200, {"content-type": "text/plain"}, b"User-agent: *", None
        return 200, {"content-type": "text/html"}, b"ok", None
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
