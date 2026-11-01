from datetime import date
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.seo_growth.google_client import (
    GSC_READONLY_SCOPE,
    GOOGLE_AUTH_URL,
    GoogleSearchConsoleClient,
    GoogleGscError,
    create_pkce_pair,
    create_oauth_state,
    validate_property_identifier,
)

def client(handler):
    transport = httpx.MockTransport(handler)
    return GoogleSearchConsoleClient(
        client_id="test-public-client", client_secret="test-secret",
        redirect_uri="https://uat.directpilot.ir/api/v1/seo/google/callback",
        http_client=httpx.Client(transport=transport),
    )

def test_google_oauth_pkce_readonly_fixed_redirect():
    c = client(lambda req: httpx.Response(500))
    verifier, challenge = create_pkce_pair()
    state = create_oauth_state()
    assert len(verifier) >= 43
    assert len(challenge) == 43
    u = urlsplit(c.authorization_url(state=state, code_challenge=challenge))
    p = parse_qs(u.query)
    assert f"{u.scheme}://{u.netloc}{u.path}" == GOOGLE_AUTH_URL
    assert p["scope"] == [GSC_READONLY_SCOPE]
    assert p["redirect_uri"] == ["https://uat.directpilot.ir/api/v1/seo/google/callback"]
    assert p["code_challenge_method"] == ["S256"]
    assert p["access_type"] == ["offline"]
    with pytest.raises(ValueError, match="invalid_oauth_state"):
        c.authorization_url(state="bad", code_challenge=challenge)

def test_code_exchange_never_exposes_provider_secrets():
    verifier, _ = create_pkce_pair()
    def handler(req):
        assert req.url.host == "oauth2.googleapis.com"
        fields = parse_qs(req.content.decode())
        assert fields["code_verifier"] == [verifier]
        assert fields["grant_type"] == ["authorization_code"]
        return httpx.Response(200, json={
            "access_token": "private-access-token", "refresh_token": "private-refresh-token",
            "expires_in": 3600, "scope": GSC_READONLY_SCOPE,
        })
    result = client(handler).exchange_code(code="opaque", code_verifier=verifier)
    assert result.refresh_token == "private-refresh-token"
    assert "private" not in repr(result)

    def denied(req):
        return httpx.Response(403, text="Do not leak this private-access-token")
    with pytest.raises(GoogleGscError) as err:
        client(denied).exchange_code(code="opaque", code_verifier=verifier)
    assert err.value.code == "google_access_denied_or_quota"
    assert "private" not in str(err.value)

def test_scope_cannot_be_granted_implicitly():
    verifier, _ = create_pkce_pair()
    def denied_scope(req):
        return httpx.Response(200, json={"access_token":"opaque", "expires_in":3600, "scope":"openid email"})
    with pytest.raises(GoogleGscError, match="scope_not_granted"):
        client(denied_scope).exchange_code(code="opaque", code_verifier=verifier)

def test_refresh_retains_only_previously_verified_scope():
    def handler(req):
        assert b"grant_type=refresh_token" in req.content
        return httpx.Response(200, json={"access_token":"rotated", "expires_in":3599})
    c = client(handler)
    result = c.refresh_access_token(refresh_token="encrypted-at-rest", verified_scope=GSC_READONLY_SCOPE)
    assert result.access_token == "rotated"
    assert result.scope == GSC_READONLY_SCOPE
    with pytest.raises(ValueError, match="unverified_gsc_scope"):
        c.refresh_access_token(refresh_token="opaque", verified_scope="openid")

def test_refresh_cannot_override_explicit_downgrade():
    def handler(req):
        return httpx.Response(200, json={"access_token":"opaque", "expires_in":3599,"scope":"openid"})
    with pytest.raises(GoogleGscError, match="scope_not_granted"):
        client(handler).refresh_access_token(refresh_token="opaque", verified_scope=GSC_READONLY_SCOPE)

def test_only_verified_sites_from_user_google_grants():
    def handler(req):
        assert req.url.host == "www.googleapis.com"
        assert req.headers["authorization"] == "Bearer allowed"
        return httpx.Response(200, json={"siteEntry":[
            {"siteUrl":"sc-domain:example.org","permissionLevel":"siteOwner"},
            {"siteUrl":"https://www.example.org/","permissionLevel":"siteRestrictedUser"},
            {"siteUrl":"sc-domain:unverified.org","permissionLevel":"siteUnverifiedUser"},
            {"siteUrl":"http://localhost:5000/","permissionLevel":"siteOwner"},
        ]})
    sites = client(handler).list_properties(access_token="allowed")
    assert [x.site_url for x in sites] == ["sc-domain:example.org", "https://www.example.org/"]

def test_gsc_query_always_uses_fixed_google_api_and_validated_dimensions():
    def handler(req):
        assert req.url.host == "www.googleapis.com"
        assert req.url.path.endswith("/searchAnalytics/query")
        assert "sc-domain%3Aexample.org" in str(req.url)
        assert req.headers["authorization"] == "Bearer allowed"
        assert '"dimensions":["date"]' in req.content.decode()
        return httpx.Response(200, json={"rows":[{"keys":["2026-10-30"],"clicks":1,"impressions":20}]})
    c = client(handler)
    response = c.search_analytics(
        access_token="allowed", property_id="sc-domain:example.org",
        start_date=date(2026,10,25), end_date=date(2026,10,31),
    )
    assert len(response["rows"]) == 1
    with pytest.raises(ValueError):
        c.search_analytics(access_token="allowed", property_id="http://127.0.0.1:5000/",
                           start_date=date(2026,10,25),end_date=date(2026,10,31))
    with pytest.raises(ValueError, match="invalid_dimensions"):
        c.search_analytics(access_token="allowed", property_id="sc-domain:example.org",
                           start_date=date(2026,10,25),end_date=date(2026,10,31),
                           dimensions=("arbitrary",))

def test_inspection_is_readonly_and_stays_within_site():
    def handler(req):
        assert req.url.host == "searchconsole.googleapis.com"
        assert req.url.path.endswith("index:inspect")
        return httpx.Response(200, json={"inspectionResult":{"indexStatusResult":{"verdict":"PASS"}}})
    c = client(handler)
    response = c.inspect_url(
        access_token="allowed", property_id="sc-domain:example.org",
        inspection_url="https://blog.example.org/page",
    )
    assert response["inspectionResult"]["indexStatusResult"]["verdict"] == "PASS"
    with pytest.raises(ValueError, match="url_not_in_property"):
        c.inspect_url(access_token="allowed", property_id="sc-domain:example.org",
                      inspection_url="https://example.org.attacker.test/page")

@pytest.mark.parametrize("site_url", [
    "javascript:alert(1)", "https://user:pass@example.org/",
    "http://localhost:3000/", "sc-domain:bad host",
    "https://example.org/?secret=x", "https://example.org/#frag", "ftp://example.org/",
])
def test_site_identifier_rejects_unsupported(site_url):
    with pytest.raises(ValueError, match="invalid_gsc_property"):
        validate_property_identifier(site_url)

def test_network_and_malformed_google_responses_fail_closed():
    def offline(req):
        raise httpx.ConnectError("secret",request=req)
    with pytest.raises(GoogleGscError,match="google_network_unavailable"):
        client(offline).list_properties(access_token="opaque")
    with pytest.raises(GoogleGscError,match="google_invalid_response"):
        client(lambda req: httpx.Response(200,text="not json")).list_properties(access_token="opaque")
