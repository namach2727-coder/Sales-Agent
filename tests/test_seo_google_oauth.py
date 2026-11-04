from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet

from app.config import Settings
from app.seo_service.provider import (
    GOOGLE_SCOPES,
    GoogleSearchConsoleClient,
    GoogleSeoProviderError,
)
from app.seo_service.security import SeoCredentialConfigurationError, SeoTokenCipher, state_digest


def test_google_refresh_token_cipher_round_trip_isolated():
    key = Fernet.generate_key().decode("ascii")
    cipher = SeoTokenCipher(key)
    encrypted = cipher.encrypt("refresh-token-secret")
    assert encrypted != "refresh-token-secret"
    assert cipher.decrypt(encrypted) == "refresh-token-secret"


def test_google_token_cipher_rejects_invalid_key():
    with pytest.raises(SeoCredentialConfigurationError):
        SeoTokenCipher("not-a-fernet-key")


def test_oauth_state_digest_is_one_way_and_deterministic():
    state = "random-browser-state-value"
    assert state_digest(state) == state_digest(state)
    assert state_digest(state) != state


def test_google_authorization_url_requests_read_only_search_console_scope():
    settings = Settings(
        google_oauth_client_id="client-id",
        google_oauth_client_secret="client-secret",
        google_oauth_redirect_uri="https://api.example.test/api/v1/seo/google/callback",
    )
    url = GoogleSearchConsoleClient(settings).authorization_url("opaque-state")
    query = parse_qs(urlsplit(url).query)
    assert query["state"] == ["opaque-state"]
    assert query["access_type"] == ["offline"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == [" ".join(GOOGLE_SCOPES)]
    assert "https://www.googleapis.com/auth/webmasters.readonly" in query["scope"][0]
    assert "webmasters" not in query["scope"][0].replace(
        "https://www.googleapis.com/auth/webmasters.readonly", ""
    )


def test_google_oauth_provider_fails_closed_without_credentials():
    provider = GoogleSearchConsoleClient(Settings())
    with pytest.raises(GoogleSeoProviderError) as exc:
        provider.authorization_url("state")
    assert exc.value.code == "google_oauth_not_configured"
