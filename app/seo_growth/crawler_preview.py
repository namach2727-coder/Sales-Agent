"""Bounded same-host crawl preview orchestration over the hardened transport."""
from __future__ import annotations

from collections import deque
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin, urlsplit, urlunsplit

from app.seo_growth.crawler_policy import CrawlBudget, CrawlLimits, CrawlPolicyError
from app.seo_growth.crawler_security import (
    CrawlTargetError,
    crawl_path_in_scope,
    normalize_crawl_path_prefix,
    normalize_crawl_url,
)
from app.seo_growth.crawler_transport import (
    CrawlTransportError,
    FetchedHTMLPage,
    fetch_html_page,
)
from app.seo_growth.technical_audit import analyze_html


MAX_LINKS_PER_PAGE = 500
STOP_CODES = {
    "seo_crawler_page_budget_exceeded",
    "seo_crawler_host_page_budget_exceeded",
    "seo_crawler_time_budget_exceeded",
    "seo_crawler_total_byte_budget_exceeded",
}


class _AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = next((value for key, value in attrs if key.casefold() == "href"), None)
        if href and not href.lstrip().startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            if len(self.hrefs) < MAX_LINKS_PER_PAGE:
                self.hrefs.append(href.strip())


def _canonical_url(raw_url: str) -> str:
    target = normalize_crawl_url(raw_url)
    parsed = urlsplit(target.url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def _normalized_prefix(value: str) -> str:
    return normalize_crawl_path_prefix(value)


def _path_in_scope(path: str, prefix: str) -> bool:
    return crawl_path_in_scope(path, prefix)


def extract_crawl_links(
    html: str,
    page_url: str,
    *,
    allowed_path_prefix: str = "/",
) -> list[str]:
    """Extract unique same-origin HTTP(S) links, dropping query and fragment data."""
    prefix = _normalized_prefix(allowed_path_prefix)
    base = normalize_crawl_url(page_url)
    parser = _AnchorCollector()
    parser.feed(html[:2_000_000])
    parser.close()

    links: list[str] = []
    seen: set[str] = set()
    for href in parser.hrefs:
        try:
            candidate = _canonical_url(urljoin(base.url, href))
            target = normalize_crawl_url(candidate)
        except (CrawlTargetError, ValueError):
            continue
        if (target.scheme, target.hostname, target.port) != (
            base.scheme, base.hostname, base.port,
        ):
            continue
        parsed = urlsplit(candidate)
        if not _path_in_scope(parsed.path or "/", prefix):
            continue
        if candidate not in seen:
            seen.add(candidate)
            links.append(candidate)
    return links


FetchPage = Callable[..., FetchedHTMLPage]


def crawl_preview(
    seed_url: str,
    *,
    resolver,
    limits: CrawlLimits | None = None,
    allowed_path_prefix: str = "/",
    audit_callback: Callable[..., None] | None = None,
    before_page: Callable[[str, int], None] | None = None,
    fetch_page: FetchPage = fetch_html_page,
) -> dict:
    """Crawl a bounded same-host page graph and return deterministic observations.

    This function does not create a route, persist page observations, or change
    customer content. Lease acquisition, authority checks and audit persistence
    are supplied by the caller through callbacks.
    """
    seed = _canonical_url(seed_url)
    seed_target = normalize_crawl_url(seed)
    prefix = _normalized_prefix(allowed_path_prefix)
    if not _path_in_scope(urlsplit(seed).path or "/", prefix):
        raise CrawlTargetError("seo_crawler_seed_out_of_scope")

    budget = CrawlBudget(limits or CrawlLimits())
    queue = deque([(seed, 0)])
    queued = {seed}
    visited: set[str] = set()
    pages: list[dict] = []
    failures: list[dict] = []
    stop_reason: str | None = None

    while queue:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            # Enforce budgets before lease callbacks or transport invocation.
            budget.check_time()
            host = urlsplit(url).hostname
            if budget.pages >= budget.limits.max_pages:
                raise CrawlPolicyError("seo_crawler_page_budget_exceeded")
            if host and budget.pages_by_host.get(host, 0) >= budget.limits.max_pages_per_host:
                raise CrawlPolicyError("seo_crawler_host_page_budget_exceeded")
            if budget.total_bytes >= budget.limits.max_total_bytes:
                raise CrawlPolicyError("seo_crawler_total_byte_budget_exceeded")
        except CrawlPolicyError as exc:
            if exc.code in STOP_CODES:
                stop_reason = exc.code
                break
            failures.append({"url": url, "depth": depth, "error_code": exc.code})
            continue

        if before_page is not None:
            before_page(url, depth)
        try:
            fetch_kwargs = {
                "resolver": resolver,
                "budget": budget,
                "depth": depth,
                "audit_callback": audit_callback,
            }
            if fetch_page is fetch_html_page:
                fetch_kwargs["allowed_path_prefix"] = prefix
            page = fetch_page(url, **fetch_kwargs)
        except (CrawlPolicyError, CrawlTransportError, CrawlTargetError) as exc:
            code = exc.code
            failures.append({"url": url, "depth": depth, "error_code": code})
            if isinstance(exc, CrawlPolicyError) and code in STOP_CODES:
                stop_reason = code
                break
            continue

        final_url = _canonical_url(page.url)
        final_target = normalize_crawl_url(final_url)
        if (final_target.scheme, final_target.hostname, final_target.port) != (
            seed_target.scheme, seed_target.hostname, seed_target.port,
        ) or not _path_in_scope(urlsplit(final_url).path or "/", prefix):
            failures.append({
                "url": url,
                "depth": depth,
                "error_code": "seo_crawler_final_url_out_of_scope",
            })
            continue

        html = page.body.decode("utf-8", errors="replace")
        observation = analyze_html(html, final_url)
        pages.append({
            "url": final_url,
            "depth": depth,
            "status_code": page.status_code,
            "document_complete": observation["document_complete"],
            "title": observation["title"],
            "meta_description": observation["meta_description"],
            "canonical_url": observation["canonical_url"],
            "findings": observation["findings"],
            "source": observation["source"],
        })

        if depth >= budget.limits.max_depth:
            continue
        for link in extract_crawl_links(
            html, final_url, allowed_path_prefix=prefix,
        ):
            if link not in queued and link not in visited:
                queued.add(link)
                queue.append((link, depth + 1))

    if stop_reason is None and queue:
        stop_reason = "seo_crawler_page_budget_exceeded"
    if stop_reason:
        coverage = "truncated"
    elif not pages and failures:
        coverage = "failed"
    elif failures:
        coverage = "partial"
    else:
        coverage = "complete"

    return {
        "kind": "technical_crawl_preview",
        "seed_url": seed,
        "pages_crawled": len(pages),
        "pages_failed": len(failures),
        "coverage_status": coverage,
        "stop_reason": stop_reason,
        "pages": pages,
        "failures": failures,
        "limits": {
            "max_pages": budget.limits.max_pages,
            "max_depth": budget.limits.max_depth,
            "max_pages_per_host": budget.limits.max_pages_per_host,
            "max_total_bytes": budget.limits.max_total_bytes,
            "max_elapsed_seconds": budget.limits.max_elapsed_seconds,
        },
        "limitations": [
            "Only same-origin links within the configured path prefix are followed.",
            "Query strings and fragments are excluded from discovered crawl URLs.",
            "This preview does not execute JavaScript or establish Google indexing, rankings, traffic, or ranking impact.",
            "Page observations are returned only; durable page-report storage is not implemented.",
        ],
    }
