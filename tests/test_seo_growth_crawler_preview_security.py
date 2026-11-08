import pytest

from app.seo_growth.crawler_preview import crawl_preview, extract_crawl_links


def test_extract_crawl_links_rejects_encoded_dot_segment_traversal():
    links = extract_crawl_links(
        '<a href="/blog/%2e%2e/private">escape</a>'
        '<a href="/blog/%252e%252e/private">double escape</a>'
        '<a href="/blog/safe">safe</a>',
        "https://example.com/blog/",
        allowed_path_prefix="/blog",
    )
    assert links == ["https://example.com/blog/safe"]


def test_crawl_preview_rejects_encoded_path_traversal_seed():
    with pytest.raises(ValueError, match="seo_crawler_seed_out_of_scope"):
        crawl_preview(
            "https://example.com/blog/%2e%2e/private/",
            resolver=lambda _host, _port: ["93.184.216.34"],
            allowed_path_prefix="/blog",
        )
