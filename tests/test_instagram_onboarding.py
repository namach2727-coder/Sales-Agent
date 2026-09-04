from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.commerce.router import router as commerce_router
from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_channel.models import InstagramConnection, InstagramOAuthState
from app.instagram_onboarding.provider import (
    InstagramOAuthAccount,
    InstagramOAuthError,
    MetaInstagramOAuthClient,
)
from app.instagram_onboarding.router import get_instagram_oauth_provider, router
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


class FakeOAuthProvider:
    def __init__(self) -> None:
        self.states: list[str] = []
        self.codes: list[str] = []

    def authorization_url(self, state: str) -> str:
        self.states.append(state)
        return f"https://instagram.example/authorize?state={state}"

    def exchange(self, code: str) -> InstagramOAuthAccount:
        self.codes.append(code)
        suffix = code.replace("_", "-")
        return InstagramOAuthAccount(
            account_id=f"account-{suffix}",
            username=f"shop_{suffix}",
            access_token=f"test-token-{suffix}",
            token_type="bearer",
            expires_in=3600,
            scopes=(
                "instagram_business_basic",
                "instagram_business_manage_messages",
                "instagram_business_manage_comments",
            ),
        )


class _ProviderResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class _ProviderHttpClient:
    def __init__(self) -> None:
        self.profile_fields: str | None = None
        self.profile_calls = 0
        self.short_method: str | None = None
        self.long_method: str | None = None
        self.long_data: dict[str, object] | None = None

    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def post(self, url: str, **kwargs: object) -> _ProviderResponse:
        if not url.endswith("/oauth/access_token"):
            self.long_method = "POST"
            data = kwargs["data"]
            assert isinstance(data, dict)
            self.long_data = data
            return _ProviderResponse(
                {"access_token": "long-lived-token", "token_type": "bearer"}
            )
        self.short_method = "POST"
        return _ProviderResponse({"access_token": "short-lived-token"})

    def get(self, url: str, **kwargs: object) -> _ProviderResponse:
        params = kwargs["params"]
        assert isinstance(params, dict)
        self.profile_calls += 1
        self.profile_fields = str(params["fields"])
        return _ProviderResponse(
            {
                "id": "37910874415222854",
                "user_id": "17841434793560671",
                "username": "test_business",
                "account_type": "BUSINESS",
            }
        )


def test_meta_oauth_prefers_user_id_for_webhook_routing(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        meta_app_id="test-app-id",
        meta_app_secret="test-app-secret",
        meta_oauth_redirect_uri="https://api.example/callback",
    )
    http_client = _ProviderHttpClient()
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    account = MetaInstagramOAuthClient(settings).exchange("authorization-code")

    assert account.account_id == "17841434793560671"
    assert http_client.profile_fields == "id,user_id,username,account_type"
    assert http_client.short_method == "POST"
    assert http_client.long_method == "POST"
    assert http_client.long_data == {
        "grant_type": "ig_exchange_token",
        "client_secret": "test-app-secret",
        "access_token": "short-lived-token",
    }


def test_short_token_metadata_and_profile_probe_are_redacted(monkeypatch, caplog) -> None:
    http_client = _ScenarioHttpClient(
        short=_ProviderResponse(
            {
                "access_token": "IG-short-token-value",
                "user_id": "17841434793560671",
                "token_type": "bearer",
                "expires_in": 3600,
                "permissions": [
                    "instagram_business_basic",
                    "instagram_business_manage_messages",
                    "instagram_business_manage_comments",
                ],
            }
        )
    )
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        MetaInstagramOAuthClient(_oauth_settings()).exchange("authorization-code")

    assert "stage=short_token_metadata" in caplog.text
    assert "http_status=200" in caplog.text
    assert "access_token_present=true" in caplog.text
    assert "user_id_present=true" in caplog.text
    assert "token_type_present=true" in caplog.text
    assert "expires_in_present=true" in caplog.text
    assert "response_keys=access_token,expires_in,permissions,token_type,user_id" in caplog.text
    assert "stage=short_token_permissions" in caplog.text
    assert "permissions_present=true" in caplog.text
    assert "permission_count=3" in caplog.text
    assert "requested_permissions_all_present=true" in caplog.text
    assert "stage=short_token_profile_probe_unversioned profile_returned=true" in caplog.text
    assert "stage=short_token_profile_probe_versioned profile_returned=true" in caplog.text
    assert "stage=short_token_explicit_user_probe_unversioned" in caplog.text
    assert "stage=short_token_explicit_user_probe_versioned" in caplog.text
    assert http_client.profile_urls == [
        "https://graph.instagram.com/me",
        "https://graph.instagram.com/v24.0/me",
        "https://graph.instagram.com/17841434793560671",
        "https://graph.instagram.com/v24.0/17841434793560671",
        "https://graph.instagram.com/me",
    ]
    assert "id_present=true" in caplog.text
    assert "user_id_present=true" in caplog.text
    assert "username_present=true" in caplog.text
    assert "account_type=BUSINESS" in caplog.text
    assert "IG-short-token-value" not in caplog.text
    assert "17841434793560671" not in caplog.text
    assert "authorization-code" not in caplog.text
    assert "test-app-secret" not in caplog.text
    assert "profile-id" not in caplog.text


def test_short_token_profile_probe_failure_does_not_abort_oauth(monkeypatch, caplog) -> None:
    http_client = _ScenarioHttpClient(
        profile_probe=_ProviderResponse(
            {
                "error": {
                    "type": "IGApiException",
                    "code": 100,
                    "message": "short token profile unavailable",
                }
            },
            status_code=400,
        )
    )
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        account = MetaInstagramOAuthClient(_oauth_settings()).exchange(
            "authorization-code"
        )

    assert account.account_id == "messaging-user-id"
    assert http_client.profile_calls == 3
    assert "stage=short_token_profile_probe" in caplog.text
    assert "http_status=400" in caplog.text
    assert "meta_error_type=IGApiException" in caplog.text
    assert "meta_error_code=100" in caplog.text
    assert "short token profile unavailable" in caplog.text
    assert "authorization-code" not in caplog.text
    assert "test-app-secret" not in caplog.text


def test_short_token_profile_probe_matrix_uses_configured_version(monkeypatch, caplog) -> None:
    http_client = _ScenarioHttpClient()
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        MetaInstagramOAuthClient(_oauth_settings(meta_api_version="v24.0")).exchange(
            "authorization-code"
        )

    assert http_client.profile_urls == [
        "https://graph.instagram.com/me",
        "https://graph.instagram.com/v24.0/me",
        "https://graph.instagram.com/me",
    ]
    assert "stage=short_token_profile_probe_unversioned" in caplog.text
    assert "stage=short_token_profile_probe_versioned" in caplog.text
    assert "api_version=NONE" in caplog.text
    assert "api_version=v24.0" in caplog.text
    assert "short_token_user_id_present=false" in caplog.text
    assert "short_token_explicit_user_probe" not in caplog.text


def test_short_token_profile_probe_versioned_failure_is_non_blocking(
    monkeypatch, caplog
) -> None:
    http_client = _ScenarioHttpClient(
        profile_versioned=_ProviderResponse(
            {
                "error": {
                    "type": "IGApiException",
                    "code": 100,
                    "message": "versioned profile unavailable",
                }
            },
            status_code=400,
        )
    )
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        account = MetaInstagramOAuthClient(_oauth_settings()).exchange(
            "authorization-code"
        )

    assert account.account_id == "messaging-user-id"
    assert http_client.profile_calls == 3
    assert "stage=short_token_profile_probe_versioned" in caplog.text
    assert "api_version=v24.0" in caplog.text
    assert "http_status=400" in caplog.text
    assert "meta_error_type=IGApiException" in caplog.text
    assert "meta_error_code=100" in caplog.text
    assert "versioned profile unavailable" in caplog.text
    assert "short-lived-token" not in caplog.text
    assert "authorization-code" not in caplog.text
    assert "test-app-secret" not in caplog.text


def test_short_token_explicit_user_probe_failure_is_non_blocking(
    monkeypatch, caplog
) -> None:
    http_client = _ScenarioHttpClient(
        short=_ProviderResponse(
            {
                "access_token": "short-lived-token",
                "user_id": "17841401850458391",
            }
        ),
        profile_explicit=_ProviderResponse(
            {
                "error": {
                    "type": "IGApiException",
                    "code": 100,
                    "message": "explicit profile unavailable",
                }
            },
            status_code=400,
        ),
    )
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        account = MetaInstagramOAuthClient(_oauth_settings()).exchange(
            "authorization-code"
        )

    assert account.account_id == "messaging-user-id"
    assert http_client.profile_calls == 5
    assert "stage=short_token_explicit_user_probe_unversioned" in caplog.text
    assert "http_status=400" in caplog.text
    assert "explicit profile unavailable" in caplog.text
    assert "17841401850458391" not in caplog.text
    assert "short-lived-token" not in caplog.text
    assert "authorization-code" not in caplog.text
    assert "test-app-secret" not in caplog.text


class _ScenarioHttpClient:
    def __init__(
        self,
        *,
        short: _ProviderResponse | Exception | None = None,
        long: _ProviderResponse | Exception | None = None,
        profile: _ProviderResponse | Exception | None = None,
        profile_probe: _ProviderResponse | Exception | None = None,
        profile_versioned: _ProviderResponse | Exception | None = None,
        profile_explicit: _ProviderResponse | Exception | None = None,
        profile_explicit_versioned: _ProviderResponse | Exception | None = None,
    ) -> None:
        self.short = short or _ProviderResponse({"access_token": "short-lived-token"})
        self.long = long or _ProviderResponse(
            {"access_token": "long-lived-token", "token_type": "bearer"}
        )
        self.profile = profile or _ProviderResponse(
            {
                "id": "profile-id",
                "user_id": "messaging-user-id",
                "username": "test_business",
                "account_type": "BUSINESS",
            }
        )
        self.profile_probe = profile_probe
        self.profile_versioned = profile_versioned
        self.profile_explicit = profile_explicit
        self.profile_explicit_versioned = profile_explicit_versioned
        self.profile_calls = 0
        self.profile_urls: list[str] = []
        self.short_method: str | None = None
        self.long_method: str | None = None
        self.long_data: dict[str, object] | None = None

    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    @staticmethod
    def _result(value: _ProviderResponse | Exception) -> _ProviderResponse:
        if isinstance(value, Exception):
            raise value
        return value

    def post(self, url: str, **kwargs: object) -> _ProviderResponse:
        if not url.endswith("/oauth/access_token"):
            self.long_method = "POST"
            data = kwargs.get("data")
            if isinstance(data, dict):
                self.long_data = data
            return self._result(self.long)
        self.short_method = "POST"
        return self._result(self.short)

    def get(self, url: str, **_kwargs: object) -> _ProviderResponse:
        self.profile_calls += 1
        self.profile_urls.append(url)
        if self.profile_calls == 1 and self.profile_probe is not None:
            return self._result(self.profile_probe)
        if self.profile_calls == 2 and self.profile_versioned is not None:
            return self._result(self.profile_versioned)
        if self.profile_calls == 3 and self.profile_explicit is not None:
            return self._result(self.profile_explicit)
        if self.profile_calls == 4 and self.profile_explicit_versioned is not None:
            return self._result(self.profile_explicit_versioned)
        return self._result(self.profile)


def _oauth_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "meta_app_id": "test-app-id",
        "meta_app_secret": "test-app-secret",
        "meta_oauth_redirect_uri": "https://api.example/callback",
    }
    values.update(overrides)
    return Settings(**values)


def test_meta_oauth_configuration_error_has_stable_code(caplog) -> None:
    client = MetaInstagramOAuthClient(_oauth_settings(meta_app_secret=""))
    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        with pytest.raises(InstagramOAuthError) as raised:
            client.authorization_url("state")

    assert raised.value.code == "oauth_configuration_error"
    assert "meta_app_secret_configured=False" in caplog.text
    assert "test-app-secret" not in caplog.text


@pytest.mark.parametrize(
    ("stage", "response", "expected_code"),
    [
        (
            "short",
            _ProviderResponse({}),
            "oauth_token_exchange_failed",
        ),
        (
            "short",
            _ProviderResponse(
                {
                    "error": {
                        "type": "OAuthException",
                        "code": 190,
                        "message": "Invalid client secret",
                    }
                },
                status_code=400,
            ),
            "oauth_invalid_client",
        ),
        (
            "short",
            _ProviderResponse(
                {
                    "error": {
                        "type": "OAuthException",
                        "code": 100,
                        "message": "redirect_uri mismatch",
                    }
                },
                status_code=400,
            ),
            "oauth_redirect_uri_mismatch",
        ),
        (
            "short",
            _ProviderResponse(
                {
                    "error": {
                        "type": "OAuthException",
                        "code": 999,
                        "message": "permission denied",
                    }
                },
                status_code=403,
            ),
            "oauth_provider_rejected",
        ),
        (
            "long",
            _ProviderResponse(
                {
                    "error": {
                        "type": "IGApiException",
                        "code": 100,
                        "message": "long-lived exchange rejected",
                    }
                },
                status_code=400,
            ),
            "oauth_provider_rejected",
        ),
        (
            "profile",
            _ProviderResponse(
                {
                    "error": {
                        "type": "OAuthException",
                        "code": 10,
                        "message": "profile unavailable",
                    }
                },
                status_code=403,
            ),
            "instagram_profile_lookup_failed",
        ),
    ],
)
def test_meta_oauth_provider_errors_are_classified_and_redacted(
    monkeypatch,
    caplog,
    stage: str,
    response: _ProviderResponse,
    expected_code: str,
) -> None:
    kwargs = {stage: response}
    http_client = _ScenarioHttpClient(**kwargs)
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        with pytest.raises(InstagramOAuthError) as raised:
            MetaInstagramOAuthClient(_oauth_settings()).exchange(
                "authorization-code"
            )

    assert raised.value.code == expected_code
    expected_stage = {
        "short": "oauth_token_exchange",
        "long": "long_lived_token_exchange",
        "profile": "instagram_profile_lookup",
    }[stage]
    assert f"stage={expected_stage}" in caplog.text
    assert "test-app-secret" not in caplog.text
    assert "authorization-code" not in caplog.text

    if stage == "long":
        assert http_client.long_method == "POST"
        assert http_client.long_data == {
            "grant_type": "ig_exchange_token",
            "client_secret": "test-app-secret",
            "access_token": "short-lived-token",
        }


def test_meta_oauth_network_errors_are_classified_and_logged(monkeypatch, caplog) -> None:
    request = httpx.Request("POST", "https://api.instagram.com/oauth/access_token")
    http_client = _ScenarioHttpClient(
        short=httpx.ConnectError("network", request=request)
    )
    monkeypatch.setattr(
        "app.instagram_onboarding.provider.httpx.Client",
        lambda **_kwargs: http_client,
    )

    with caplog.at_level(logging.INFO, logger="sales_assistant.instagram_oauth"):
        with pytest.raises(InstagramOAuthError) as raised:
            MetaInstagramOAuthClient(_oauth_settings()).exchange("authorization-code")

    assert raised.value.code == "instagram_provider_network_error"
    assert "destination_host=api.instagram.com" in caplog.text
    assert "exception_class=ConnectError" in caplog.text
    assert "authorization-code" not in caplog.text


@pytest.fixture
def onboarding_api(tmp_path: Path):
    database = tmp_path / "onboarding.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    settings = Settings(
        _env_file=None,
        database_url=str(engine.url),
        session_cookie_secure=False,
        meta_app_id="test-app-id",
        meta_app_secret="test-app-secret",
        meta_oauth_redirect_uri="https://api.example/callback",
        instagram_token_encryption_key=Fernet.generate_key().decode("ascii"),
        cors_allowed_origins=["https://web.example"],
    )
    fake = FakeOAuthProvider()
    app = FastAPI()
    app.include_router(commerce_router)
    app.include_router(router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_instagram_oauth_provider] = lambda: fake
    yield TestClient(app), engine, fake
    engine.dispose()


def _register(client: TestClient, name: str) -> dict:
    result = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{name}@example.com",
            "password": PASSWORD,
            "display_name": f"Customer {name}",
            "tenant_name": f"Tenant {name}",
            "tenant_slug": f"tenant-{name}",
            "store_name": f"Store {name}",
            "store_slug": f"store-{name}",
        },
    )
    assert result.status_code == 201
    return result.json()


def _login(client: TestClient, name: str) -> dict[str, str]:
    result = client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": PASSWORD},
    )
    assert result.status_code == 200
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def _trial_entitlement(client: TestClient, headers: dict[str, str]) -> None:
    existing = client.get("/api/v1/subscription/me", headers=headers)
    if existing.status_code == 200 and existing.json() and existing.json()["plan_code"] == "TRIAL":
        return
    plan = next(item for item in client.get("/api/v1/plans").json() if item["code"] == "TRIAL")
    result = client.post(
        "/api/v1/orders", headers=headers, json={"plan_public_id": plan["public_id"]}
    )
    assert result.status_code == 201
    assert result.json()["status"] == "paid"


def _start(client: TestClient, headers: dict[str, str]) -> str:
    result = client.post("/api/v1/integrations/instagram/connect", headers=headers)
    assert result.status_code == 200, result.text
    return parse_qs(urlsplit(result.json()["authorization_url"]).query)["state"][0]


def test_registration_provides_active_trial_entitlement(onboarding_api) -> None:
    client, _engine, fake = onboarding_api
    _register(client, "blocked")
    result = client.post(
        "/api/v1/integrations/instagram/connect", headers=_login(client, "blocked")
    )
    assert result.status_code == 200
    assert fake.states


def test_official_flow_uses_existing_connection_and_never_exposes_token(onboarding_api) -> None:
    client, engine, fake = onboarding_api
    created = _register(client, "connected")
    headers = _login(client, "connected")
    _trial_entitlement(client, headers)
    state = _start(client, headers)
    result = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "connected"},
    )
    assert result.status_code == 200, result.text
    assert result.json()["tenant_public_id"] == created["tenant_public_id"]
    assert result.json()["store_public_id"] == created["store_public_id"]
    assert result.json()["status"] == "active"
    assert "token" not in result.text.casefold()
    with Session(engine) as db:
        rows = list(db.scalars(select(InstagramConnection)).all())
        assert len(rows) == 1
        assert rows[0].encrypted_access_token
        assert rows[0].encrypted_access_token != "test-token-connected"
    accounts = client.get("/api/v1/integrations/instagram/accounts", headers=headers)
    assert accounts.status_code == 200
    assert accounts.json()[0]["connection_public_id"] == result.json()["connection_public_id"]
    assert fake.codes == ["connected"]


def test_oauth_state_is_single_use(onboarding_api) -> None:
    client, _engine, _fake = onboarding_api
    _register(client, "replay")
    headers = _login(client, "replay")
    _trial_entitlement(client, headers)
    state = _start(client, headers)
    first = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "replay"},
    )
    assert first.status_code == 200
    replay = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "replay-again"},
    )
    assert replay.status_code == 400
    assert replay.json()["detail"]["code"] == "invalid_oauth_state"


def test_expired_oauth_state_is_rejected_before_provider_call(onboarding_api) -> None:
    client, engine, fake = onboarding_api
    _register(client, "expired")
    headers = _login(client, "expired")
    _trial_entitlement(client, headers)
    state = _start(client, headers)
    with Session(engine) as db, db.begin():
        item = db.scalar(
            select(InstagramOAuthState).where(
                InstagramOAuthState.state_digest
                == hashlib.sha256(state.encode("utf-8")).hexdigest()
            )
        )
        assert item is not None
        item.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    result = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "expired"},
    )
    assert result.status_code == 400
    assert fake.codes == []


def test_accounts_are_strictly_tenant_isolated(onboarding_api) -> None:
    client, _engine, _fake = onboarding_api
    _register(client, "first")
    first_headers = _login(client, "first")
    _trial_entitlement(client, first_headers)
    state = _start(client, first_headers)
    assert client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "first"},
    ).status_code == 200

    _register(client, "second")
    second_headers = _login(client, "second")
    _trial_entitlement(client, second_headers)
    assert client.get(
        "/api/v1/integrations/instagram/accounts", headers=second_headers
    ).json() == []
    first_status = client.get(
        "/api/v1/integrations/instagram/status", headers=first_headers
    ).json()
    assert first_status["connected_accounts"] == 1


def test_browser_callback_redirects_to_trusted_frontend_without_token(onboarding_api) -> None:
    client, _engine, _fake = onboarding_api
    _register(client, "browser-success")
    headers = _login(client, "browser-success")
    _trial_entitlement(client, headers)
    state = _start(client, headers)
    result = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": state, "code": "browser-success"},
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert result.status_code == 303
    assert result.headers["location"] == (
        "https://web.example/settings/integrations/instagram?instagram=connected"
    )
    assert "token" not in result.headers["location"].casefold()


def test_browser_callback_failure_redirects_with_stable_safe_code(onboarding_api) -> None:
    client, _engine, _fake = onboarding_api
    result = client.get(
        "/api/v1/integrations/instagram/callback",
        params={"state": "unknown-state", "code": "unused"},
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert result.status_code == 303
    assert result.headers["location"] == (
        "https://web.example/settings/integrations/instagram"
        "?instagram=error&code=invalid_oauth_state"
    )


def test_callback_rejects_caller_controlled_redirect_target(onboarding_api) -> None:
    client, _engine, _fake = onboarding_api
    result = client.get(
        "/api/v1/integrations/instagram/callback",
        params={
            "state": "unknown-state",
            "code": "unused",
            "redirect_uri": "https://attacker.example/steal",
        },
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert result.status_code == 400
    assert result.json()["detail"]["code"] == "unsupported_redirect_target"
