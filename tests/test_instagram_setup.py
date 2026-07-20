import time

from fastapi.testclient import TestClient

from app import instagram_setup
from app.main import app, settings


LOCAL_ORIGIN = "http://127.0.0.1:8000"
FAKE_ACCESS_TOKEN = "IGAA" + ("A" * 60)
FAKE_APP_SECRET = "a1" * 16
FAKE_IG_USER_ID = "17841400000000001"
FAKE_VERIFY_TOKEN = "pytest-webhook-verify-token-2026"


def setup_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "access_token": FAKE_ACCESS_TOKEN,
        "app_secret": FAKE_APP_SECRET,
        "ig_user_id": FAKE_IG_USER_ID,
        "verify_token": FAKE_VERIFY_TOKEN,
    }
    payload.update(overrides)
    return payload


def configure_test_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(instagram_setup, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "meta_access_token", "")
    monkeypatch.setattr(settings, "meta_app_secret", "")
    monkeypatch.setattr(settings, "meta_ig_user_id", "")
    monkeypatch.setattr(settings, "meta_verify_token", "")
    with instagram_setup._nonce_lock:
        instagram_setup._setup_nonces.clear()


def test_local_meta_setup_saves_atomically_preserves_env_and_redacts_values(
    monkeypatch, tmp_path
) -> None:
    configure_test_paths(monkeypatch, tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "APP_NAME=Keep Me\n"
        "META_ACCESS_TOKEN=old-value\n"
        "META_ACCESS_TOKEN=duplicate-value\n"
        "UNRELATED_SETTING=preserved\n",
        encoding="utf-8",
    )

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        page = client.get("/instagram/setup")
        response = client.post(
            "/instagram/setup",
            json=setup_payload(),
            headers={"origin": LOCAL_ORIGIN, "sec-fetch-site": "same-origin"},
        )
        status_response = client.get("/instagram/status")

    assert page.status_code == 200
    assert page.text.count('type="password"') == 2
    assert page.headers["cache-control"] == "no-store"
    assert page.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert FAKE_ACCESS_TOKEN not in page.text
    assert FAKE_APP_SECRET not in page.text
    assert FAKE_VERIFY_TOKEN not in page.text

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "Meta settings were saved locally",
        "verify_token_generated": False,
        "network_verification_performed": False,
    }
    assert FAKE_ACCESS_TOKEN not in response.text
    assert FAKE_APP_SECRET not in response.text
    assert FAKE_VERIFY_TOKEN not in response.text
    assert FAKE_ACCESS_TOKEN not in status_response.text
    assert FAKE_APP_SECRET not in status_response.text
    assert FAKE_VERIFY_TOKEN not in status_response.text

    saved = env_path.read_text(encoding="utf-8")
    assert "APP_NAME=Keep Me" in saved
    assert "UNRELATED_SETTING=preserved" in saved
    assert saved.count("META_ACCESS_TOKEN=") == 1
    assert f"META_ACCESS_TOKEN={FAKE_ACCESS_TOKEN}" in saved
    assert f"META_APP_SECRET={FAKE_APP_SECRET}" in saved
    assert f"META_IG_USER_ID={FAKE_IG_USER_ID}" in saved
    assert f"META_VERIFY_TOKEN={FAKE_VERIFY_TOKEN}" in saved
    assert not list(tmp_path.glob(".*.tmp"))


def test_meta_setup_ui_generates_copyable_verify_token_and_has_secret_toggles(
    monkeypatch, tmp_path
) -> None:
    configure_test_paths(monkeypatch, tmp_path)

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        page = client.get("/instagram/setup")

    assert page.status_code == 200
    assert 'id="verify-token" type="text"' in page.text
    assert "ساخت و کپی Verify Token" in page.text
    assert "crypto.getRandomValues" in page.text
    assert "navigator.clipboard.writeText" in page.text
    assert "setFreshVerifyToken();" in page.text
    assert page.text.count('class="toggle-secret"') == 2
    assert 'data-target="access-token"' in page.text
    assert 'data-target="app-secret"' in page.text
    assert FAKE_VERIFY_TOKEN not in page.text


def test_meta_setup_generates_hidden_verify_token_when_blank(monkeypatch, tmp_path) -> None:
    configure_test_paths(monkeypatch, tmp_path)

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        client.get("/instagram/setup")
        response = client.post(
            "/instagram/setup",
            json=setup_payload(verify_token=""),
            headers={"origin": LOCAL_ORIGIN},
        )

    assert response.status_code == 200
    assert response.json()["verify_token_generated"] is True
    verify_line = next(
        line
        for line in (tmp_path / ".env").read_text(encoding="utf-8").splitlines()
        if line.startswith("META_VERIFY_TOKEN=")
    )
    assert len(verify_line) >= 50
    assert verify_line.removeprefix("META_VERIFY_TOKEN=") not in response.text


def test_meta_setup_is_local_development_only(monkeypatch, tmp_path) -> None:
    configure_test_paths(monkeypatch, tmp_path)

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("192.0.2.10", 50000),
    ) as remote_client:
        remote_response = remote_client.get("/instagram/setup")

    with TestClient(
        app,
        base_url="http://example.test:8000",
        client=("127.0.0.1", 50000),
    ) as wrong_host_client:
        wrong_host_response = wrong_host_client.get("/instagram/setup")

    monkeypatch.setattr(settings, "app_env", "production")
    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as production_client:
        production_response = production_client.get("/instagram/setup")

    assert remote_response.status_code == 403
    assert wrong_host_response.status_code == 403
    assert production_response.status_code == 404
    assert not (tmp_path / ".env").exists()


def test_meta_setup_nonce_is_one_time_and_origin_is_required(monkeypatch, tmp_path) -> None:
    configure_test_paths(monkeypatch, tmp_path)

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        client.get("/instagram/setup")
        nonce = client.cookies.get(instagram_setup.CSRF_COOKIE_NAME)
        rejected = client.post(
            "/instagram/setup",
            json=setup_payload(),
            headers={"origin": "https://evil.example"},
        )
        accepted = client.post(
            "/instagram/setup",
            json=setup_payload(),
            headers={"origin": LOCAL_ORIGIN},
        )
        reused = client.post(
            "/instagram/setup",
            json=setup_payload(),
            headers={
                "origin": LOCAL_ORIGIN,
                "cookie": f"{instagram_setup.CSRF_COOKIE_NAME}={nonce}",
            },
        )

    assert rejected.status_code == 403
    assert accepted.status_code == 200
    assert reused.status_code == 403


def test_meta_setup_rejects_expired_session(monkeypatch, tmp_path) -> None:
    configure_test_paths(monkeypatch, tmp_path)

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        client.get("/instagram/setup")
        nonce = client.cookies.get(instagram_setup.CSRF_COOKIE_NAME)
        with instagram_setup._nonce_lock:
            instagram_setup._setup_nonces[nonce] = time.monotonic() - 1
        response = client.post(
            "/instagram/setup",
            json=setup_payload(),
            headers={"origin": LOCAL_ORIGIN},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Setup page expired; reload it and try again"
    assert not (tmp_path / ".env").exists()


def test_meta_setup_validation_never_reflects_submitted_values(monkeypatch, tmp_path) -> None:
    configure_test_paths(monkeypatch, tmp_path)
    submitted = {
        "access_token": "LEAK-META-ACCESS-TOKEN",
        "app_secret": "LEAK-META-APP-SECRET",
        "ig_user_id": "not-a-number",
        "verify_token": "LEAK-META-VERIFY-TOKEN",
    }

    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("127.0.0.1", 50000),
    ) as client:
        client.get("/instagram/setup")
        response = client.post(
            "/instagram/setup",
            json=submitted,
            headers={"origin": LOCAL_ORIGIN},
        )

    assert response.status_code == 422
    for value in submitted.values():
        assert value not in response.text
    assert not (tmp_path / ".env").exists()
