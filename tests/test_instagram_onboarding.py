from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.commerce.router import router as commerce_router
from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_channel.models import InstagramConnection, InstagramOAuthState
from app.instagram_onboarding.provider import InstagramOAuthAccount
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


def test_connect_requires_active_entitlement(onboarding_api) -> None:
    client, _engine, fake = onboarding_api
    _register(client, "blocked")
    result = client.post(
        "/api/v1/integrations/instagram/connect", headers=_login(client, "blocked")
    )
    assert result.status_code == 403
    assert result.json()["detail"]["code"] == "instagram_entitlement_required"
    assert fake.states == []


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
