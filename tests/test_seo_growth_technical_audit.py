import pytest

from app.seo_growth.technical_audit import analyze_html


def test_extracts_core_page_metadata_and_structure():
    html = """
    <html lang="fa-IR"><head><title>صفحه خدمات</title>
    <meta name="description" content="توضیح صفحه">
    <link rel="canonical" href="/services/">
    <meta name="robots" content="index,follow">
    </head><body><h1>خدمات اصلی</h1><h2>جزئیات</h2>
    <img src="/a.jpg" alt="تصویر محصول"><img src="/b.jpg">
    <a href="/about">درباره</a><a href="https://outside.example/path">خارجی</a>
    <a href="mailto:test@example.com">ایمیل</a></body></html>
    """
    result = analyze_html(html, "https://example.com/services")
    assert result["title"] == "صفحه خدمات"
    assert result["meta_description"] == "توضیح صفحه"
    assert result["canonical_url"] == "https://example.com/services/"
    assert result["language"] == "fa-IR"
    assert result["h1_count"] == 1
    assert result["heading_levels"] == [2]
    assert result["image_count"] == 2
    assert result["images_missing_alt"] == 1
    assert result["internal_links"] == 1
    assert result["external_links"] == 1
    assert result["robots_directives"] == ["follow", "index"]


def test_reports_missing_metadata_and_noindex_as_evidence_findings():
    result = analyze_html(
        '<html><head><meta name="robots" content="noindex,nofollow"></head>'
        '<body><h1></h1><img src="/x"></body></html>',
        "https://example.com/",
    )
    codes = {item["code"] for item in result["findings"]}
    assert {"missing_title", "missing_meta_description", "missing_h1",
            "images_missing_alt", "robots_noindex"} <= codes


def test_multiple_h1_is_observation_not_a_blocking_error():
    result = analyze_html("<h1>One</h1><h1>Two</h1>", "https://example.com/")
    finding = next(item for item in result["findings"] if item["code"] == "multiple_h1")
    assert finding["severity"] == "low"
    assert result["h1_count"] == 2


def test_truncated_input_is_explicitly_marked():
    result = analyze_html("<title>partial</title>", "https://example.com/", truncated=True)
    assert result["document_complete"] is False
    assert any(item["code"] == "html_truncated" for item in result["findings"])


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "file:///etc/passwd", "https://user:pass@example.com/",
    "/relative/path", "ftp://example.com/",
])
def test_rejects_invalid_page_url(url):
    with pytest.raises(ValueError):
        analyze_html("<title>x</title>", url)


def test_rejects_non_text_html():
    with pytest.raises(ValueError):
        analyze_html(b"<title>x</title>", "https://example.com/")
