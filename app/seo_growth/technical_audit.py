"""Deterministic, network-free technical observations from one HTML document.

This module deliberately performs no HTTP requests. Fetching customer-supplied URLs
belongs to a separate SSRF-hardened crawler layer.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


MAX_HTML_CHARS = 2_000_000


def _text(value: str) -> str:
    return " ".join(value.split())


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.title_depth = 0
        self.h1_parts: list[str] = []
        self.h1_depth = 0
        self.h1_values: list[str] = []
        self.description: str | None = None
        self.canonical: str | None = None
        self.robots: set[str] = set()
        self.language: str | None = None
        self.image_count = 0
        self.images_missing_alt = 0
        self.internal_links = 0
        self.external_links = 0
        self.heading_levels: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): value for key, value in attrs}
        tag = tag.casefold()
        if tag == "html" and values.get("lang"):
            self.language = values["lang"].strip()[:35] or None
        elif tag == "title":
            self.title_depth += 1
        elif tag == "h1":
            self.heading_levels.append(1)
            self.h1_depth += 1
            self.h1_parts = []
        elif tag in {"h2", "h3", "h4", "h5", "h6"}:
            self.heading_levels.append(int(tag[1]))
        elif tag == "meta":
            name = (values.get("name") or "").strip().casefold()
            if name == "description" and self.description is None:
                self.description = _text(values.get("content") or "") or None
            elif name == "robots":
                self.robots.update(
                    token.strip().casefold()
                    for token in (values.get("content") or "").split(",")
                    if token.strip()
                )
        elif tag == "link":
            rel = {part.casefold() for part in (values.get("rel") or "").split()}
            if "canonical" in rel and self.canonical is None:
                self.canonical = values.get("href")
        elif tag == "img":
            self.image_count += 1
            if values.get("alt") is None or not values.get("alt", "").strip():
                self.images_missing_alt += 1
        elif tag == "a":
            href = (values.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                return
            if self._same_host(href):
                self.internal_links += 1
            else:
                parsed = urlsplit(href)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    self.external_links += 1

    def _same_host(self, href: str) -> bool:
        # The base origin is attached by analyze_html before parsing.
        base = getattr(self, "_base_url", "")
        target = urlsplit(urljoin(base, href))
        origin = urlsplit(base)
        return bool(target.hostname and origin.hostname and
                    target.hostname.casefold() == origin.hostname.casefold())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        elif tag == "h1" and self.h1_depth:
            self.h1_depth -= 1
            value = _text("".join(self.h1_parts))
            if value:
                self.h1_values.append(value[:500])
            self.h1_parts = []

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if self.h1_depth:
            self.h1_parts.append(data)


def analyze_html(html: str, page_url: str, *, truncated: bool = False) -> dict:
    """Return page-level observations; never claims Google index or ranking state."""
    if not isinstance(html, str):
        raise ValueError("html must be text")
    parsed_url = urlsplit(page_url)
    if (parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname
            or parsed_url.username or parsed_url.password):
        raise ValueError("page_url must be an absolute HTTP(S) URL without credentials")
    if len(html) > MAX_HTML_CHARS:
        html = html[:MAX_HTML_CHARS]
        truncated = True

    parser = _DocumentParser()
    parser._base_url = page_url
    parser.feed(html)
    parser.close()

    title = _text("".join(parser.title_parts)) or None
    description = parser.description
    canonical = urljoin(page_url, parser.canonical) if parser.canonical else None
    findings: list[dict] = []

    def add(code: str, severity: str, evidence: str, recommendation: str) -> None:
        findings.append({"code": code, "severity": severity,
                         "evidence": evidence, "recommendation": recommendation})

    if not title:
        add("missing_title", "high", "No non-empty title element was found.",
            "Add a concise, page-specific title element.")
    if not description:
        add("missing_meta_description", "medium", "No non-empty meta description was found.",
            "Add a useful, page-specific meta description.")
    if len(parser.h1_values) == 0:
        add("missing_h1", "medium", "No non-empty H1 heading was found.",
            "Add one descriptive primary heading when appropriate for the page.")
    elif len(parser.h1_values) > 1:
        add("multiple_h1", "low", f"{len(parser.h1_values)} non-empty H1 headings were found.",
            "Review the heading outline and use headings that reflect the page structure.")
    if parser.image_count and parser.images_missing_alt:
        add("images_missing_alt", "medium",
            f"{parser.images_missing_alt} of {parser.image_count} images have missing or empty alt attributes.",
            "Add meaningful alternative text to informative images; keep decorative images appropriately empty.")
    if "noindex" in parser.robots:
        add("robots_noindex", "high", "The page HTML includes a robots noindex directive.",
            "Confirm that excluding this page from search is intentional.")
    if truncated:
        add("html_truncated", "info", "The HTML input was truncated before analysis completed.",
            "Re-fetch within the crawler's bounded response-size policy before treating counts as complete.")

    return {
        "kind": "technical_page_observation",
        "page_url": page_url,
        "document_complete": not truncated,
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": description,
        "meta_description_length": len(description) if description else 0,
        "canonical_url": canonical,
        "language": parser.language,
        "robots_directives": sorted(parser.robots),
        "h1_count": len(parser.h1_values),
        "h1_headings": parser.h1_values,
        "heading_levels": parser.heading_levels,
        "image_count": parser.image_count,
        "images_missing_alt": parser.images_missing_alt,
        "internal_links": parser.internal_links,
        "external_links": parser.external_links,
        "findings": findings,
        "source": "html_document",
        "limitations": [
            "HTML observations do not establish Google indexing, rankings, traffic, or ranking impact.",
            "This parser does not fetch URLs, execute JavaScript, inspect CSS, or evaluate rendered layout.",
        ],
    }
