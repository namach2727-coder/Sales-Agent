"""URL and DNS preflight primitives for the future SEO crawler.

This module performs no socket or HTTP operations. DNS resolution is injected
so a caller can provide a bounded resolver. It does not fetch URLs. A future
transport must connect directly to one of the returned validated IP addresses
(while preserving the original Host and TLS SNI) and revalidate every redirect.
Do not pass the hostname to a client that performs a fresh DNS lookup.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from typing import Callable, Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit


MAX_CRAWL_URL_LENGTH = 2048
NAT64_PREFIXES = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("64:ff9b:1::/48"))
DEFAULT_PORTS = {"http": 80, "https": 443}
BLOCKED_SUFFIXES = (
    ".localhost", ".local", ".internal", ".lan", ".home",
    ".test", ".invalid", ".example", ".onion",
)


class CrawlTargetError(ValueError):
    """A URL or resolved address is not eligible for a public crawl."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    scheme: str
    hostname: str
    port: int
    path_and_query: str


Resolver = Callable[[str, int], Iterable[str]]


def _is_public_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Python's is_global can be True for multicast ranges; those are never
    # valid unicast crawl destinations.
    if (not address.is_global or address.is_private or address.is_multicast
            or address.is_unspecified or address.is_loopback or address.is_link_local
            or address.is_reserved):
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if (address.ipv4_mapped is not None or address.sixtofour is not None
                or address.teredo is not None
                or any(address in prefix for prefix in NAT64_PREFIXES)):
            return False
    return True


def normalize_crawl_url(raw_url: str) -> CrawlTarget:
    """Normalize an HTTP(S) URL without resolving or fetching it."""
    if (not isinstance(raw_url, str) or not raw_url
            or len(raw_url) > MAX_CRAWL_URL_LENGTH
            or any(ord(char) < 32 or char.isspace() for char in raw_url)):
        raise CrawlTargetError("seo_crawler_invalid_url")
    try:
        parsed = urlsplit(raw_url)
        scheme = parsed.scheme.lower()
        if scheme not in DEFAULT_PORTS:
            raise CrawlTargetError("seo_crawler_invalid_scheme")
        if parsed.username is not None or parsed.password is not None:
            raise CrawlTargetError("seo_crawler_url_credentials_rejected")
        hostname = parsed.hostname
        if not hostname or "%" in hostname:
            raise CrawlTargetError("seo_crawler_invalid_host")
        explicit_port = parsed.port
    except CrawlTargetError:
        raise
    except ValueError:
        raise CrawlTargetError("seo_crawler_invalid_url") from None

    default_port = DEFAULT_PORTS[scheme]
    port = explicit_port if explicit_port is not None else default_port
    if port != default_port:
        raise CrawlTargetError("seo_crawler_port_rejected")

    if hostname.endswith(".."):
        raise CrawlTargetError("seo_crawler_invalid_host")
    hostname = hostname[:-1] if hostname.endswith(".") else hostname
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            hostname = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError:
            raise CrawlTargetError("seo_crawler_invalid_host") from None
        labels = hostname.split(".")
        if (len(hostname) > 253 or len(labels) < 2
                or any(not label or len(label) > 63
                       or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
                       for label in labels)
                or all(label.isdigit() for label in labels)
                or hostname == "localhost"
                or any(hostname.endswith(suffix) for suffix in BLOCKED_SUFFIXES)):
            raise CrawlTargetError("seo_crawler_unsafe_host")
        authority = hostname
    else:
        if not _is_public_address(address):
            raise CrawlTargetError("seo_crawler_unsafe_ip")
        hostname = address.compressed
        authority = f"[{hostname}]" if address.version == 6 else hostname

    path = parsed.path or "/"
    canonical_url = urlunsplit((scheme, authority, path, parsed.query, ""))
    if len(canonical_url) > MAX_CRAWL_URL_LENGTH:
        raise CrawlTargetError("seo_crawler_invalid_url")
    return CrawlTarget(
        url=canonical_url,
        scheme=scheme,
        hostname=hostname,
        port=port,
        path_and_query=path + (f"?{parsed.query}" if parsed.query else ""),
    )


def validate_resolved_addresses(addresses: Iterable[str]) -> tuple[str, ...]:
    """Reject empty, malformed, or mixed public/non-public DNS answers."""
    normalized: set[str] = set()
    try:
        for raw in addresses:
            address = ipaddress.ip_address(raw)
            if "%" in raw or not _is_public_address(address):
                raise CrawlTargetError("seo_crawler_unsafe_ip")
            normalized.add(address.compressed)
    except CrawlTargetError:
        raise
    except (TypeError, ValueError):
        raise CrawlTargetError("seo_crawler_invalid_dns_answer") from None
    if not normalized:
        raise CrawlTargetError("seo_crawler_dns_empty")
    return tuple(sorted(normalized))


def resolve_public_addresses(target: CrawlTarget, *, resolver: Resolver) -> tuple[str, ...]:
    """Re-normalize the URL before DNS so caller-supplied fields cannot bypass policy."""
    target = normalize_crawl_url(target.url)
    try:
        address = ipaddress.ip_address(target.hostname)
    except ValueError:
        try:
            answers = resolver(target.hostname, target.port)
        except OSError:
            raise CrawlTargetError("seo_crawler_dns_resolution_failed") from None
    else:
        answers = (address.compressed,)
    return validate_resolved_addresses(answers)


def validate_redirect_target(
    base_url: str, location: str, *, resolver: Resolver,
) -> tuple[CrawlTarget, tuple[str, ...]]:
    """Resolve a redirect relative to the current URL and revalidate its DNS."""
    if not isinstance(location, str) or not location or len(location) > MAX_CRAWL_URL_LENGTH:
        raise CrawlTargetError("seo_crawler_invalid_redirect")
    base = normalize_crawl_url(base_url)
    target = normalize_crawl_url(urljoin(base.url, location))
    addresses = resolve_public_addresses(target, resolver=resolver)
    return target, addresses
