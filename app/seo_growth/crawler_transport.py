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


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection that connects to a prevalidated IP, never a hostname."""

    def __init__(
        self, target: CrawlTarget, pinned_ip: str, timeout: float,
        ssl_context: ssl.SSLContext | None,
    ) -> None:
        super().__init__(target.hostname, target.port, timeout=timeout)
        self._pinned_ip = pinned_ip
        self._ssl_context = ssl_context

    def connect(self) -> None:
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        try:
            if self._ssl_context is not None:
                sock = self._ssl_context.wrap_socket(sock, server_hostname=self.host)
            self.sock = sock
        except Exception:
            sock.close()
            raise


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
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CrawlTransportError("seo_crawler_time_budget_exceeded")
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read(min(64 * 1024, max_body_bytes + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > max_body_bytes:
                raise CrawlTransportError("seo_crawler_response_too_large")
        return status, response_headers, bytes(body), location
    except CrawlTransportError:
        raise
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
        elapsed = budget.clock() - budget.started_at
        timeout = min(
            budget.limits.request_timeout_seconds,
            budget.limits.max_elapsed_seconds - elapsed,
        )
        if timeout <= 0:
            raise CrawlPolicyError("seo_crawler_time_budget_exceeded")
        last_error: Exception | None = None
        result = None
        for address in addresses:
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
    resolver: Callable[[str, int], object],
    budget: CrawlBudget,
    user_agent: str = "DirectPilotBot",
    depth: int = 0,
    request_once: RequestOnce = _request_once,
) -> FetchedHTMLPage:
    """Fetch one public HTML page after robots checks and all resource controls.

    DNS resolution is injected. The transport pins every connection to the
    validated address. This function is not wired to a public API endpoint.
    """
    target = normalize_crawl_url(raw_url)
    budget.record_page(target.url, depth=depth)
    parsed = urlsplit(target.url)
    robots_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    robots_target, robots_status, _robots_headers, robots_body = _request_with_redirects(
        robots_url, resolver=resolver, budget=budget,
        max_redirects=budget.limits.max_redirects,
        max_body_bytes=min(MAX_ROBOTS_BYTES, budget.limits.max_response_bytes),
        request_once=request_once,
    )
    budget.record_response_bytes(len(robots_body))
    if not robots_allows(
        robots_url=robots_url, page_url=target.url, user_agent=user_agent,
        status_code=robots_status, body=robots_body,
    ):
        raise CrawlTransportError("seo_crawler_robots_disallowed")

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
    return FetchedHTMLPage(
        url=final_target.url, status_code=status, headers=headers,
        body=body, robots_url=robots_target.url,
    )
