import hashlib
import hmac
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.instagram import get_fresh_settings
from app.public_instagram_gateway import app


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/demo",
        "/products",
        "/faqs",
        "/leads",
        "/orders",
        "/chat",
        "/admin",
        "/admin/api/state",
        "/static/admin.js",
        "/static/admin_modules.js",
        "/admin/api/module-marketplace",
        "/instagram/status",
        "/instagram/setup",
        "/telegram/status",
        "/integrations/manychat/instagram",
        "/webhooks/instagram/",
    ],
)
def test_gateway_exposes_no_non_webhook_paths(path: str) -> None:
    with TestClient(app) as client:
        response = client.get(path, follow_redirects=False)

    assert response.status_code == 404


@pytest.mark.parametrize("path", ["/privacy", "/data-deletion"])
def test_gateway_exposes_public_legal_pages(path: str) -> None:
    with TestClient(app) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_gateway_verifies_meta_challenge(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "meta_verify_token", "gateway-verify-token")

    app.dependency_overrides[get_fresh_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            accepted = client.get(
                "/webhooks/instagram",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "gateway-verify-token",
                    "hub.challenge": "gateway-challenge",
                },
            )
            rejected = client.get(
                "/webhooks/instagram",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong-token",
                    "hub.challenge": "gateway-challenge",
                },
            )
    finally:
        app.dependency_overrides.pop(get_fresh_settings, None)

    assert accepted.status_code == 200
    assert accepted.text == "gateway-challenge"
    assert rejected.status_code == 403


def test_gateway_enforces_meta_post_signature(monkeypatch) -> None:
    settings = get_settings()
    secret = "gateway-app-secret"
    monkeypatch.setattr(settings, "meta_app_secret", secret)
    monkeypatch.setattr(settings, "meta_signature_required", True)
    body = json.dumps(
        {"object": "instagram", "entry": []}, separators=(",", ":")
    ).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    with TestClient(app) as client:
        accepted = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"x-hub-signature-256": f"sha256={signature}"},
        )
        rejected = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"x-hub-signature-256": "sha256=invalid"},
        )

    assert accepted.status_code == 200
    assert accepted.json() == {
        "status": "ok",
        "received": 0,
        "processed": 0,
        "duplicates": 0,
        "failed": 0,
    }
    assert rejected.status_code == 401


def test_safe_access_log_never_records_query_secrets(monkeypatch) -> None:
    settings = get_settings()
    secret_token = "must-not-appear-in-access-log"
    monkeypatch.setattr(settings, "meta_verify_token", "expected-token")
    log_path = Path("logs/instagram_gateway_access.log")
    before = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    app.dependency_overrides[get_fresh_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            response = client.get(
                "/webhooks/instagram",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": secret_token,
                    "hub.challenge": "secret-challenge",
                },
            )
    finally:
        app.dependency_overrides.pop(get_fresh_settings, None)

    assert response.status_code == 403
    after = log_path.read_text(encoding="utf-8")
    new_log = after[len(before) :]
    assert "GET /webhooks/instagram 403" in new_log
    assert secret_token not in new_log
    assert "secret-challenge" not in new_log
