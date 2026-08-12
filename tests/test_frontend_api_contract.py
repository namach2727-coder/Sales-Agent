"""Regression checks for the public directpilot-web integration boundary."""

from pathlib import Path

from fastapi import FastAPI

from app.commerce.router import router as commerce_router
from app.instagram_onboarding.router import router as instagram_onboarding_router


ROOT = Path(__file__).resolve().parents[1]


EXPECTED_OPERATIONS = {
    ("POST", "/api/v1/auth/register"): 201,
    ("POST", "/api/v1/auth/login"): 200,
    ("POST", "/api/v1/auth/logout"): 200,
    ("GET", "/api/v1/auth/me"): 200,
    ("GET", "/api/v1/plans"): 200,
    ("POST", "/api/v1/orders"): 201,
    ("GET", "/api/v1/orders/me"): 200,
    ("GET", "/api/v1/orders/{order_public_id}"): 200,
    ("POST", "/api/v1/payments/card-transfer"): 201,
    ("POST", "/api/v1/payments/{payment_public_id}/receipt"): 200,
    ("GET", "/api/v1/payments/me"): 200,
    ("GET", "/api/v1/subscription/me"): 200,
    ("POST", "/api/v1/integrations/instagram/connect"): 200,
    ("GET", "/api/v1/integrations/instagram/callback"): 200,
    ("GET", "/api/v1/integrations/instagram/status"): 200,
    ("GET", "/api/v1/integrations/instagram/accounts"): 200,
}


def _contract_app() -> FastAPI:
    app = FastAPI()
    app.include_router(commerce_router)
    app.include_router(instagram_onboarding_router)
    return app


def test_directpilot_web_operations_and_success_statuses_are_stable() -> None:
    schema = _contract_app().openapi()
    for (method, path), expected_status in EXPECTED_OPERATIONS.items():
        operation = schema["paths"][path][method.casefold()]
        assert str(expected_status) in operation["responses"]


def test_receipt_upload_contract_is_raw_binary_not_multipart() -> None:
    operation = _contract_app().openapi()["paths"][
        "/api/v1/payments/{payment_public_id}/receipt"
    ]["post"]
    assert "requestBody" not in operation


def test_production_template_allows_only_directpilot_web_origin() -> None:
    values: dict[str, str] = {}
    for line in (ROOT / ".env.production.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value

    assert values["TRUSTED_HOSTS"] == "api.directpilot.ir"
    assert values["CORS_ALLOWED_ORIGINS"] == "https://directpilot.ir"
    assert "*" not in values["CORS_ALLOWED_ORIGINS"]
    assert values["FORCE_HTTPS"] == "true"
    assert values["SESSION_COOKIE_SECURE"] == "true"
    assert values["SESSION_COOKIE_SAMESITE"] == "lax"
