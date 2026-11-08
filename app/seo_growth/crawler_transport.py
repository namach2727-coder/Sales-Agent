"""Pinned-IP HTTP transport for the SEO crawler.

This is a synchronous, GET-only transport. It never delegates hostname
resolution to an HTTP client: every TCP connection is opened to a validated
numeric IP, while HTTPS keeps certificate verification and SNI bound to the
canonical URL hostname. Redirects are manual and revalidated.
"""
from __future__ import annotations

from dataclasses import dataclass
import http.client
import socket
import ssl
import time
from typing import Callable
from urllib.parse import urlsplit, urlunsplit

from app.seo_growth.crawler_policy import (
    CrawlBudget,
    CrawlPolicyError,
    robots_allows,
    validate_html_response,
)
from app.seo_growth.crawler_security import (
    CrawlTarget,
    CrawlTargetError,
    Resolver,
    normalize_crawl_url,
    resolve_public_addresses,
    validate_redirect_target,
)


MAX_ROBOTS_BYTES = 512_000
CRAWLER_PRODUCT_TOKEN = "DirectPilotBot"
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class CrawlTransportError(RuntimeError):
    """A safe crawler transport operation failed."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class FetchedHTMLPage:
    url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    robots_url: str
    robots_status_code: int | None = None
    robots_bytes_received: int = 0
    page_bytes_received: int = 0
    duration_ms: int = 0


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection that connects to a prevalidated IP, never a hostname."""

    def __init__(
        self, target: CrawlTarget, pinned_ip: str, timeout: float,
        ssl_context: ssl.SSLContext | None,
    ) -> None:
        super().__init__(target.hostname, target.port, timeout=timeout)
        self._pinned_ip = pinned_ip
        self._ssl_context = ssl_context
        self._deadline = time.monotonic() + timeout

    def _remaining_timeout(self) -> float:
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise socket.timeout("crawler request deadline exceeded")
        return remaining

    def connect(self) -> None:
        remaining = self._remaining_timeout()
        sock = socket.create_connection((self._pinned_ip, self.port), remaining)
        try:
            sock.settimeout(self._remaining_timeout())
            if self._ssl_context is not None:
                sock = self._ssl_context.wrap_socket(sock, server_hostname=self.host)
            self.sock = sock
        except Exception:
            sock.close()
            raise

    def send(self, data) -> None:
        if self.sock is not None:
            self.sock.settimeout(self._remaining_timeout())
        super().send(data)


def _request_once(
    target: CrawlTarget, pinned_ip: str, *, timeout: float, max_body_bytes: int,
) -> tuple[int, dict[str, str], bytes, str | None]:
    context = ssl.create_default_context() if target.scheme == "https" else None
    connection = _PinnedHTTPConnection(target, pinned_ip, timeout, context)
    host_header = f"[{target.hostname}]" if ":" in target.hostname else target.hostname
    headers = {
        "Host": host_header,
        "User-Agent": "DirectPilotBot/1.0 (+https://directpilot.ir/bot)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    try:
        connection.request("GET", target.path_and_query, headers=headers)
        if connection.sock is not None:
            connection.sock.settimeout(connection._remaining_timeout())
        response = connection.getresponse()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        location = response.getheader("Location")
        if status in REDIRECT_STATUSES and location:
            return status, response_headers, b"", location
        encoding = response_headers.get("content-encoding", "identity").strip().lower()
        if encoding not in {"", "identity"}:
            raise CrawlTransportError("seo_crawler_content_encoding_rejected")
        raw_length = response_headers.get("content-length")
        if raw_length is not None:
            try:
                declared_length = int(raw_length)
            except ValueError:
                raise CrawlTransportError("seo_crawler_invalid_content_length") from None
            if declared_length < 0:
                raise CrawlTransportError("seo_crawler_invalid_content_length")
            if declared_length > max_body_bytes:
                raise CrawlTransportError("seo_crawler_response_too_large")
        body = bytearray()
        while True:
            if connection.sock is not None:
                connection.sock.settimeout(connection._remaining_timeout())
            chunk = response.read(min(64 * 1024, max_body_bytes + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > max_body_bytes:
                raise CrawlTransportError("seo_crawler_response_too_large")
        return status, response_headers, bytes(body), location
    except CrawlTransportError:
        raise
    except socket.timeout:
        raise CrawlTransportError("seo_crawler_time_budget_exceeded") from None
    except (OSError, http.client.HTTPException, ssl.SSLError):
        raise CrawlTransportError("seo_crawler_network_request_failed") from None
    finally:
        connection.close()


RequestOnce = Callable[..., tuple[int, dict[str, str], bytes, str | None]]


def _request_with_redirects(
    raw_url: str, *, resolver: Resolver,
    budget: CrawlBudget, max_redirects: int, max_body_bytes: int,
    request_once: RequestOnce = _request_once,
) -> tuple[CrawlTarget, int, dict[str, str], bytes]:
    if type(max_redirects) is not int or max_redirects < 0 or max_redirects > budget.limits.max_redirects:
        raise CrawlPolicyError("seo_crawler_invalid_limits")
    target = normalize_crawl_url(raw_url)
    addresses = resolve_public_addresses(target, resolver=resolver)
    redirects = 0
    while True:
        budget.check_time()
        last_error: Exception | None = None
        result = None
        for address in addresses:
            budget.check_time()
            elapsed = budget.clock() - budget.started_at
            timeout = min(
                budget.limits.request_timeout_seconds,
                budget.limits.max_elapsed_seconds - elapsed,
            )
            if timeout <= 0:
                raise CrawlPolicyError("seo_crawler_time_budget_exceeded")
            try:
                result = request_once(
                    target, address, timeout=timeout, max_body_bytes=max_body_bytes,
                )
                break
            except CrawlTransportError as exc:
                last_error = exc
                if exc.code != "seo_crawler_network_request_failed":
                    raise
        if result is None:
            if last_error is not None:
                raise last_error
            raise CrawlTransportError("seo_crawler_network_request_failed")
        status, headers, body, location = result
        if status not in REDIRECT_STATUSES or not location:
            encoding = headers.get("content-encoding", "identity").strip().lower()
            if encoding not in {"", "identity"}:
                raise CrawlTransportError("seo_crawler_content_encoding_rejected")
            raw_length = headers.get("content-length")
            if len(body) > max_body_bytes:
                raise CrawlTransportError("seo_crawler_response_too_large")
            if raw_length is not None:
                try:
                    declared_length = int(raw_length)
                except (TypeError, ValueError):
                    raise CrawlTransportError("seo_crawler_invalid_content_length") from None
                if declared_length < 0:
                    raise CrawlTransportError("seo_crawler_invalid_content_length")
                if declared_length > max_body_bytes:
                    raise CrawlTransportError("seo_crawler_response_too_large")
            return target, status, headers, body
        if redirects >= max_redirects:
            raise CrawlTransportError("seo_crawler_redirect_limit_exceeded")
        try:
            next_target, next_addresses = validate_redirect_target(
                target.url, location, resolver=resolver,
            )
        except CrawlTargetError:
            raise
        if (next_target.scheme, next_target.hostname, next_target.port) != (
            target.scheme, target.hostname, target.port,
        ):
            raise CrawlTransportError("seo_crawler_cross_origin_redirect_rejected")
        target, addresses = next_target, next_addresses
        redirects += 1


def fetch_html_page(
    raw_url: str, *,
    resolver: Resolver,
    budget: CrawlBudget,
    depth: int = 0,
    request_once: RequestOnce = _request_once,
    audit_callback: Callable[..., None] | None = None,
) -> FetchedHTMLPage:
    """Fetch one public HTML page after robots checks and all resource controls.

    DNS resolution is injected. The transport pins every connection to the
    validated address. An optional callback receives sanitized event fields;
    it is expected to persist them synchronously when audit is mandatory.
    """
    target = normalize_crawl_url(raw_url)
    budget.record_page(target.url, depth=depth)
    parsed = urlsplit(target.url)
    robots_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    robots_started = budget.clock()
    try:
        robots_target, robots_status, _robots_headers, robots_body = _request_with_redirects(
            robots_url, resolver=resolver, budget=budget,
            max_redirects=budget.limits.max_redirects,
            max_body_bytes=min(MAX_ROBOTS_BYTES, budget.limits.max_response_bytes),
            request_once=request_once,
        )
    except (CrawlPolicyError, CrawlTargetError, CrawlTransportError) as exc:
        if audit_callback is not None:
            audit_callback(
                event_kind="robots", outcome="failed", raw_url=robots_url,
                robots_decision="unavailable_block", http_status=None,
                bytes_received=0,
                duration_ms=max(0, int((budget.clock() - robots_started) * 1000)),
                error_code=exc.code,
            )
        raise

    robots_allowed = robots_allows(
        robots_url=robots_url, page_url=target.url, user_agent=CRAWLER_PRODUCT_TOKEN,
        status_code=robots_status, body=robots_body,
    )
    if robots_status in {404, 410}:
        robots_decision = "unavailable_allow"
    elif robots_status < 200 or robots_status >= 300 or robots_body is None:
        robots_decision = "unavailable_block"
    else:
        robots_decision = "allow" if robots_allowed else "disallow"
    robots_duration_ms = max(0, int((budget.clock() - robots_started) * 1000))
    try:
        budget.record_response_bytes(len(robots_body))
    except CrawlPolicyError as exc:
        if audit_callback is not None:
            audit_callback(
                event_kind="robots", outcome="failed", raw_url=robots_url,
                robots_decision=robots_decision, http_status=robots_status,
                bytes_received=len(robots_body), duration_ms=robots_duration_ms,
                error_code=exc.code,
            )
        raise
    if audit_callback is not None:
        audit_callback(
            event_kind="robots",
            outcome="allowed" if robots_allowed else "blocked",
            raw_url=robots_url,
            robots_decision=robots_decision,
            http_status=robots_status,
            bytes_received=len(robots_body),
            duration_ms=robots_duration_ms,
            error_code=None,
        )
    if not robots_allowed:
        raise CrawlTransportError("seo_crawler_robots_disallowed")

    page_started = budget.clock()
    status: int | None = None
    body = b""
    try:
        final_target, status, headers, body = _request_with_redirects(
            target.url, resolver=resolver, budget=budget,
            max_redirects=budget.limits.max_redirects,
            max_body_bytes=budget.limits.max_response_bytes,
            request_once=request_once,
        )
        validate_html_response(
            status, headers, max_response_bytes=budget.limits.max_response_bytes,
        )
        budget.record_response_bytes(len(body))
        budget.check_time()
    except (CrawlPolicyError, CrawlTargetError, CrawlTransportError) as exc:
        if audit_callback is not None:
            audit_callback(
                event_kind="page", outcome="failed", raw_url=target.url,
                robots_decision="not_checked", http_status=status,
                bytes_received=len(body),
                duration_ms=max(0, int((budget.clock() - page_started) * 1000)),
                error_code=exc.code,
            )
        raise

    page_duration_ms = max(0, int((budget.clock() - page_started) * 1000))
    if audit_callback is not None:
        audit_callback(
            event_kind="page", outcome="fetched", raw_url=final_target.url,
            robots_decision="not_checked", http_status=status,
            bytes_received=len(body), duration_ms=page_duration_ms,
            error_code=None,
        )
    return FetchedHTMLPage(
        url=final_target.url,
        status_code=status,
        headers=headers,
        body=body,
        robots_url=robots_target.url,
        robots_status_code=robots_status,
        robots_bytes_received=len(robots_body),
        page_bytes_received=len(body),
        duration_ms=robots_duration_ms + page_duration_ms,
    )
