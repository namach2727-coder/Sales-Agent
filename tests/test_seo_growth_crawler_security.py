import pytest

from app.seo_growth.crawler_security import (
    CrawlTargetError,
    normalize_crawl_url,
    resolve_public_addresses,
    validate_redirect_target,
    validate_resolved_addresses,
)


def test_normalize_url_canonicalizes_scheme_host_default_port_and_fragment():
    target = normalize_crawl_url("HTTPS://Example.COM:443/a/b?x=1#section")
    assert target.url == "https://example.com/a/b?x=1"
    assert target.scheme == "https"
    assert target.hostname == "example.com"
    assert target.port == 443
    assert target.path_and_query == "/a/b?x=1"


def test_normalize_url_converts_idn_hostname_to_ascii():
    target = normalize_crawl_url("https://bücher.example.com/")
    assert target.hostname == "xn--bcher-kva.example.com"


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "data:text/html,hi", "ftp://example.com/file",
    "//example.com/path", "https://user:secret@example.com/",
    "https://example.com:8443/", "http://example.com:443/", "https://example.com:0/",
    "https://localhost/", "https://admin/", "https://service.internal/",
    "https://printer.local/", "https://test.invalid/", "https://example.test/",
    "https://bad_host.example.com/", "https://127.1/",
    "https://example.com/a b", "https://example.com/\nheader",
])
def test_unsafe_or_ambiguous_urls_are_rejected(url):
    with pytest.raises(CrawlTargetError):
        normalize_crawl_url(url)


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://10.0.0.8/", "http://172.16.0.1/",
    "http://192.168.1.1/", "http://169.254.169.254/",
    "http://0.0.0.0/", "http://224.0.0.1/",
    "http://[::1]/", "http://[fc00::1]/", "http://[fe80::1]/",
    "http://[::]/", "http://[ff02::1]/",
    "http://[2002:7f00:1::]/", "http://[64:ff9b::7f00:1]/",
    "http://[64:ff9b:1::7f00:1]/", "http://[::ffff:7f00:1]/",
])
def test_ip_literal_targets_must_be_global_unicast(url):
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        normalize_crawl_url(url)


def test_public_ip_literals_are_normalized_and_ipv6_is_bracketed():
    v4 = normalize_crawl_url("https://93.184.216.34:443/path")
    v6 = normalize_crawl_url("https://[2606:4700:4700::1111]/")
    assert v4.url == "https://93.184.216.34/path"
    assert v6.url == "https://[2606:4700:4700::1111]/"


def test_dns_answer_requires_every_address_to_be_public():
    assert validate_resolved_addresses(["93.184.216.34", "2606:4700:4700::1111"]) == (
        "2606:4700:4700::1111", "93.184.216.34",
    )
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        validate_resolved_addresses(["93.184.216.34", "127.0.0.1"])
    with pytest.raises(CrawlTargetError, match="seo_crawler_dns_empty"):
        validate_resolved_addresses([])
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        validate_resolved_addresses(["224.0.0.1"])
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        validate_resolved_addresses(["ff02::1"])


def test_dns_resolution_uses_injected_resolver_and_returns_pinned_addresses():
    target = normalize_crawl_url("https://public.example.com/path")
    calls = []
    def resolver(hostname, port):
        calls.append((hostname, port))
        return ["93.184.216.34"]
    assert resolve_public_addresses(target, resolver=resolver) == ("93.184.216.34",)
    assert calls == [("public.example.com", 443)]


def test_dns_failure_and_malformed_answers_fail_closed():
    target = normalize_crawl_url("https://public.example.com/")
    def failed(_hostname, _port):
        raise OSError("synthetic DNS failure")
    with pytest.raises(CrawlTargetError, match="seo_crawler_dns_resolution_failed"):
        resolve_public_addresses(target, resolver=failed)
    with pytest.raises(CrawlTargetError, match="seo_crawler_invalid_dns_answer"):
        validate_resolved_addresses(["not-an-ip"])


def test_redirect_is_resolved_and_public_ip_validation_is_repeated():
    calls = []
    def resolver(hostname, port):
        calls.append((hostname, port))
        return ["93.184.216.34"]
    target, addresses = validate_redirect_target(
        "https://public.example.com/old", "../new",
        resolver=resolver,
    )
    assert target.url == "https://public.example.com/new"
    assert addresses == ("93.184.216.34",)
    assert calls == [("public.example.com", 443)]


def test_redirect_to_private_or_unsupported_target_is_rejected():
    def resolver(hostname, port):
        return ["127.0.0.1"] if hostname == "internal.example.com" else ["93.184.216.34"]
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        validate_redirect_target("https://public.example.com/", "https://internal.example.com/admin", resolver=resolver)
    with pytest.raises(CrawlTargetError):
        validate_redirect_target("https://public.example.com/", "javascript:alert(1)", resolver=resolver)

 
def test_url_errors_keep_specific_security_codes():
    with pytest.raises(CrawlTargetError, match="seo_crawler_invalid_scheme"):
        normalize_crawl_url("ftp://example.com/file")
    with pytest.raises(CrawlTargetError, match="seo_crawler_url_credentials_rejected"):
        normalize_crawl_url("https://user:secret@example.com/")


def test_resolver_revalidates_url_instead_of_trusting_forged_target_fields():
    from app.seo_growth.crawler_security import CrawlTarget
    forged = CrawlTarget(
        url="http://127.0.0.1/", scheme="https",
        hostname="93.184.216.34", port=443, path_and_query="/",
    )
    with pytest.raises(CrawlTargetError, match="seo_crawler_unsafe_ip"):
        resolve_public_addresses(
            forged, resolver=lambda _hostname, _port: ["93.184.216.34"],
        )


def test_resolver_uses_normalized_url_hostname_not_mutable_target_fields():
    from app.seo_growth.crawler_security import CrawlTarget
    target = CrawlTarget(
        url="https://public.example.com/path", scheme="https",
        hostname="127.0.0.1", port=443, path_and_query="/",
    )
    calls = []
    def resolver(hostname, port):
        calls.append((hostname, port))
        return ["93.184.216.34"]
    assert resolve_public_addresses(target, resolver=resolver) == ("93.184.216.34",)
    assert calls == [("public.example.com", 443)]
