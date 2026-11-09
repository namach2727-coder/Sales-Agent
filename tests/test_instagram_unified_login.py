from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from app.config import Settings
from app.instagram_onboarding.unified_provider import MetaUnifiedInstagramOAuthClient


class Response:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class Client:
    def __init__(self, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if url.endswith("/subscribed_apps"):
            return Response({"success": True})
        raise AssertionError(f"Unexpected endpoint: {url}")

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url.endswith("/oauth/access_token"):
            return Response({"access_token": "system-user-token", "token_type": "bearer"})
        if url.endswith("/me/assigned_instagram_accounts"):
            return Response({"data": [{"id": "17841400000000000", "username": "directpilot_test"}]})
        raise AssertionError(f"Unexpected endpoint: {url}")


def unified_settings(**overrides):
    values = {
        "meta_oauth_mode": "unified_login",
        "meta_oauth_config_id": "962123656629907",
        "meta_app_id": "app-id",
        "meta_app_secret": "app-secret",
        "meta_oauth_redirect_uri": "https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback",
        "meta_api_version": "v24.0",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_unified_authorization_uses_config_id_without_legacy_scopes():
    client = MetaUnifiedInstagramOAuthClient(unified_settings())
    url = client.authorization_url("opaque-state")
    query = parse_qs(urlsplit(url).query)

    assert url.startswith("https://www.facebook.com/v24.0/dialog/oauth?")
    assert query["client_id"] == ["app-id"]
    assert query["config_id"] == ["962123656629907"]
    assert query["redirect_uri"] == ["https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback"]
    assert query["state"] == ["opaque-state"]
    assert "scope" not in query


def test_unified_exchange_discovers_single_assigned_instagram_account(monkeypatch):
    fake = Client()
    monkeypatch.setattr(
        "app.instagram_onboarding.unified_provider.httpx.Client",
        lambda **kwargs: fake,
    )

    account = MetaUnifiedInstagramOAuthClient(unified_settings()).exchange("auth-code")

    assert account.account_id == "17841400000000000"
    assert account.username == "directpilot_test"
    assert account.access_token == "system-user-token"
    assert account.expires_in is None
    assert account.scopes == ()
    assert [call[1].rsplit("/", 1)[-1] for call in fake.calls] == [
        "access_token",
        "assigned_instagram_accounts",
    ]

    MetaUnifiedInstagramOAuthClient(unified_settings()).subscribe_webhooks(account)
    assert fake.calls[2][0] == "POST"
    assert fake.calls[2][2]["data"]["subscribed_fields"] == "messages,comments"
    assert fake.calls[2][2]["headers"]["Authorization"] == "Bearer system-user-token"
    token_request = fake.calls[0][2]
    assert token_request["params"]["client_secret"] == "app-secret"
    assert token_request["params"]["code"] == "auth-code"
    assert fake.calls[1][2]["headers"]["Authorization"] == "Bearer system-user-token"


def test_unified_exchange_fails_closed_for_multiple_accounts(monkeypatch):
    class MultipleClient(Client):
        def request(self, method, url, **kwargs):
            self.calls.append((method, url, kwargs))
            if url.endswith("/oauth/access_token"):
                return Response({"access_token": "system-user-token"})
            return Response({"data": [
                {"id": "17841400000000001", "username": "one"},
                {"id": "17841400000000002", "username": "two"},
            ]})

    fake = MultipleClient()
    monkeypatch.setattr(
        "app.instagram_onboarding.unified_provider.httpx.Client",
        lambda **kwargs: fake,
    )

    from app.instagram_onboarding.provider import InstagramOAuthError
    import pytest

    with pytest.raises(InstagramOAuthError) as exc:
        MetaUnifiedInstagramOAuthClient(unified_settings()).exchange("auth-code")
    assert exc.value.code == "unified_multiple_instagram_accounts"
