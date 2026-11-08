""""Network-independent crawl policy, robots decisions and resource budgets.

This module does not perform network I/O. The eventual transport must enforce
wire-byte and decoded-byte limits while streaming, use bounded timeouts, and
consult robots policy before requesting a page.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
import time
from typing import Callable, Mapping
from urllib.parse import urlsplit


class CrawlPolicyError(ValueError):
    """A crawl is outside its configured policy or resource budget."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CrawlLimits:
    max_pages: int = 100
    max_pages_per_host: int = 50
    max_depth: int = 3
    max_redirects: int = 5
    max_response_bytes: int = 2_000_000
    max_total_bytes: int = 20_000_000
    max_elapsed_seconds: float = 120.0
    request_timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        positive_ints = (
            self.max_pages, self.max_pages_per_host, self.max_response_bytes,
            self.max_total_bytes, self.max_redirects,
        )
        if any(type(value) is not int or value < 1 for value in positive_ints):
            raise CrawlPolicyError("seo_crawler_invalid_limits")
        if type(self.max_depth) is not int or self.max_depth < 0:
            raise CrawlPolicyError("seo_crawler_invalid_limits")
        if (not math.isfinite(self.max_elapsed_seconds)
                or not math.isfinite(self.request_timeout_seconds)
                or self.max_elapsed_seconds <= 0 or self.request_timeout_seconds <= 0
                or self.request_timeout_seconds > self.max_elapsed_seconds):
            raise CrawlPolicyError("seo_crawler_invalid_limits")
        if self.max_response_bytes > self.max_total_bytes:
            raise CrawlPolicyError("seo_crawler_invalid_limits")


@dataclass
class CrawlBudget:
    limits: CrawlLimits = field(default_factory=CrawlLimits)
    started_at: float = field(default_factory=time.monotonic)
    clock: Callable[[], float] = time.monotonic
    pages: int = 0
    total_bytes: int = 0
    pages_by_host: dict[str, int] = field(default_factory=dict)

    def check_time(self) -> None:
        if self.clock() - self.started_at >= self.limits.max_elapsed_seconds:
            raise CrawlPolicyError("seo_crawler_time_budget_exceeded")

    def record_page(self, url: str, *, depth: int) -> None:
        self.check_time()
        if type(depth) is not int or depth < 0 or depth > self.limits.max_depth:
            raise CrawlPolicyError("seo_crawler_depth_limit_exceeded")
        host = urlsplit(url).hostname
        if not host:
            raise CrawlPolicyError("seo_crawler_invalid_url")
        if self.pages >= self.limits.max_pages:
            raise CrawlPolicyError("seo_crawler_page_budget_exceeded")
        host_count = self.pages_by_host.get(host, 0)
        if host_count >= self.limits.max_pages_per_host:
            raise CrawlPolicyError("seo_crawler_host_page_budget_exceeded")
        self.pages += 1
        self.pages_by_host[host] = host_count + 1

    def record_response_bytes(self, byte_count: int) -> None:
        self.check_time()
        if type(byte_count) is not int or byte_count < 0:
            raise CrawlPolicyError("seo_crawler_invalid_byte_count")
        if byte_count > self.limits.max_response_bytes:
            raise CrawlPolicyError("seo_crawler_response_too_large")
        if self.total_bytes + byte_count > self.limits.max_total_bytes:
            raise CrawlPolicyError("seo_crawler_total_byte_budget_exceeded")
        self.total_bytes += byte_count


def validate_html_response(
    status_code: int, headers: Mapping[str, str], *, max_response_bytes: int,
) -> str:
    """Validate status, HTML media type and declared Content-Length, if present."""
    if type(status_code) is not int or status_code < 200 or status_code >= 300:
        raise CrawlPolicyError("seo_crawler_http_status_rejected")
    content_type = next(
        (value for key, value in headers.items() if key.lower() == "content-type"), ""
    )
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type not in {"text/html", "application/xhtml+xml"}:
        raise CrawlPolicyError("seo_crawler_content_type_rejected")
    raw_length = next(
        (value for key, value in headers.items() if key.lower() == "content-length"), None
    )
    if raw_length is not None:
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            raise CrawlPolicyError("seo_crawler_invalid_content_length") from None
        if length < 0:
            raise CrawlPolicyError("seo_crawler_invalid_content_length")
        if length > max_response_bytes:
            raise CrawlPolicyError("seo_crawler_response_too_large")
    return media_type


def _robots_rule_matches(pattern: str, path: str) -> bool:
    if not pattern:
        return False
    anchored = pattern.endswith("$")
    expression = re.escape(pattern[:-1] if anchored else pattern).replace(r"\\*", ".*")
    # re.escape does not escape '*' on all supported Python versions.
    expression = expression.replace(r"\\*", ".*").replace("*", ".*")
    return re.match("^" + expression + ("$" if anchored else ""), path) is not None


def _robots_groups(lines: list[str]) -> list[tuple[list[str], list[tuple[str, str]]]]:
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    saw_rule = False

    def finish() -> None:
        nonlocal agents, rules, saw_rule
        if agents:
            groups.append((agents, rules))
        agents, rules, saw_rule = [], [], False

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            if agents and saw_rule:
                finish()
            continue
        if ":" not in line:
            continue
        directive, value = (part.strip() for part in line.split(":", 1))
        directive = directive.lower()
        if directive == "user-agent" and value:
            if saw_rule:
                finish()
            agents.append(value.lower())
        elif directive in {"allow", "disallow"} and agents:
            saw_rule = True
            if value:
                rules.append((directive, value))
    finish()
    return groups


def robots_allows(
    *, robots_url: str, page_url: str, user_agent: str,
    status_code: int, body: bytes | None,
) -> bool:
    """Apply RFC-style longest-match Allow/Disallow rules, failing closed.

    404/410 mean no robots file. 401/403/429 and server errors block crawling.
    Matching groups are selected by the most specific user-agent token; wildcard
    applies only when no product-specific group matches. Equally specific rules
    prefer Allow.
    """
    if status_code in {404, 410}:
        return True
    if status_code in {401, 403, 429} or status_code >= 500 or status_code < 200:
        return False
    if status_code < 200 or status_code >= 300 or body is None:
        return False
    try:
        lines = body.decode("utf-8", errors="replace").splitlines()
        groups = _robots_groups(lines)
        agent = user_agent.strip().lower().split("/", 1)[0]
        matched: list[tuple[list[str], list[tuple[str, str]]]] = []
        specificity = 0
        for agents, rules in groups:
            score = max(
                (len(token) for token in agents if token != "*" and token in agent),
                default=0,
            )
            if score > specificity:
                specificity, matched = score, [(agents, rules)]
            elif score and score == specificity:
                matched.append((agents, rules))
        if not matched:
            matched = [(agents, rules) for agents, rules in groups if "*" in agents]
        parsed = urlsplit(page_url)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        applicable: list[tuple[int, bool]] = []
        for _agents, rules in matched:
            for directive, pattern in rules:
                if _robots_rule_matches(pattern, path):
                    applicable.append((len(pattern.encode("utf-8")), directive == "allow"))
        if not applicable:
            return True
        longest = max(length for length, _allow in applicable)
        return any(allow for length, allow in applicable if length == longest)
    except (UnicodeError, ValueError):
        return False
