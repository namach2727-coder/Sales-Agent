from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher, Type
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.authentication.router import router
from app.config import Settings, get_settings
from app.database import get_db
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


@pytest.fixture
def api_context(tmp_path: Path):
    path = tmp_path / "api-auth.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    passwords = PasswordService(
        hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID)
    )
    with Session(engine, expire_on_commit=False) as db:
        first = AuthenticationService(db, password_service=passwords).create_user(
            email="api@example.com", display_name="API User", password=PASSWORD
        )
    with Session(engine, expire_on_commit=False) as db:
        second = AuthenticationService(db, password_service=passwords).create_user(
            email="other@example.com", display_name="Other User", password=PASSWORD
        )
    settings = Settings(
        _env_file=None,
        database_url=str(engine.url),
        session_cookie_secure=False,
        authentication_enabled=True,
    )
    app = FastAPI()
    app.include_router(router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(app), engine, first, second
    engine.dispose()


def login(client: TestClient, email="api@example.com") -> dict:
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()


def test_login_me_and_session_list_are_sanitized(api_context) -> None:
    client, _engine, user, _other = api_context
    payload = login(client)
    token = payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["principal"]["user_id"] == user.id
    text = str(payload).casefold()
    assert "password_hash" not in text and PASSWORD not in text and "token_hash" not in text
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["email"] == "api@example.com"
    sessions = client.get("/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert "token_hash" not in sessions.text and token not in sessions.text


def test_login_failure_is_generic_for_unknown_and_wrong_password(api_context) -> None:
    client, *_ = api_context
    responses = [
        client.post("/auth/login", json={"email": "api@example.com", "password": "wrong password value"}),
        client.post("/auth/login", json={"email": "missing@example.com", "password": "wrong password value"}),
    ]
    assert [item.status_code for item in responses] == [401, 401]
    assert responses[0].json() == responses[1].json() == {
        "detail": {"code": "invalid_credentials", "message": "Invalid credentials"}
    }


def test_missing_and_malformed_token_are_rejected(api_context) -> None:
    client, *_ = api_context
    client.cookies.clear()
    missing = client.get("/auth/me")
    malformed = client.get("/auth/me", headers={"Authorization": "Basic value"})
    assert missing.status_code == malformed.status_code == 401


def test_logout_revokes_current_session_and_clears_cookie(api_context) -> None:
    client, *_ = api_context
    token = login(client)["access_token"]
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_user_can_revoke_own_session_but_not_another_users(api_context) -> None:
    client, _engine, _user, _other = api_context
    first = login(client)
    client.cookies.clear()
    second = login(client, "other@example.com")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    denied = client.delete(
        f"/auth/sessions/{second['principal']['session_id']}/revoke",
        headers=first_headers,
    )
    assert denied.status_code == 404
    allowed = client.delete(
        f"/auth/sessions/{first['principal']['session_id']}/revoke",
        headers=first_headers,
    )
    assert allowed.status_code == 200 and allowed.json()["status"] == "revoked"


def test_client_supplied_role_headers_do_not_grant_access(api_context) -> None:
    client, *_ = api_context
    token = login(client)["access_token"]
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Role": "platform_super_admin",
            "X-Tenant-Id": "999",
            "X-Permission": "platform.access_manage",
        },
    )
    assert response.status_code == 200
    assert "platform_super_admin" not in response.text
