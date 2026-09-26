from __future__ import annotations

import httpx
import pytest

from app.commerce.kpay_provider import KPayClient, KPayCreateUnknown, KPayProviderError
from app.config import Settings


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.request = httpx.Request("POST", "https://kpay.website/api/v1/transactions/create")

    def json(self):
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("private provider body", request=self.request, response=httpx.Response(self.status_code, request=self.request))


class FakeClient:
    def __init__(self, responses=None, error=None) -> None:
        self.responses = list(responses or [])
        self.error = error
        self.calls = []

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        if self.error:
            raise self.error
        return self.responses.pop(0)

    def get(self, path, **kwargs):
        self.calls.append((path, kwargs))
        if self.error:
            raise self.error
        return self.responses.pop(0)


def settings(**changes) -> Settings:
    values = {
        "_env_file": None,
        "kpay_access_token": "fake-access-token",
        "kpay_shop_id": "fake-shop",
        "kpay_card_id": "fake-card",
        "kpay_callback_base_url": "https://directpilot.example",
    }
    values.update(changes)
    return Settings(**values)


def test_create_sends_exact_rial_amount_and_bearer_only_from_backend() -> None:
    client = FakeClient([FakeResponse({
        "id": "tx-1", "authority": "auth-1", "amount": 4_900_000,
        "final_amount": 4_900_000, "fee": 0, "status": "pending",
        "payment_url": "https://kpay.website/payment/auth-1",
    })])
    provider = KPayClient(settings(), client=client)
    result = provider.create_transaction(
        amount=4_900_000,
        callback_url="https://directpilot.example/api/v1/payments/kpay/callback/public-payment",
        description="DirectPilot AUTOMATION_V1",
        factor_number="public-payment",
    )
    path, request = client.calls[0]
    assert path == "/transactions/create"
    assert request["json"]["amount"] == result.amount == 4_900_000
    assert request["json"]["factor_number"] == "public-payment"
    assert request["headers"]["Authorization"] == "Bearer fake-access-token"
    assert "fake-access-token" not in repr(result)


def test_verify_auth_is_adapter_local_and_switchable() -> None:
    payload = {"id": "tx-1", "authority": "auth-1", "status": "pending", "amount": 4_900_000, "paid_at": None}
    authenticated = FakeClient([FakeResponse(payload)])
    KPayClient(settings(), client=authenticated).verify_transaction(authority="auth-1")
    assert "Authorization" in authenticated.calls[0][1]["headers"]
    unauthenticated = FakeClient([FakeResponse(payload)])
    KPayClient(settings(kpay_verify_send_auth=False), client=unauthenticated).verify_transaction(authority="auth-1")
    assert unauthenticated.calls[0][1]["headers"] == {}


def test_check_transaction_uses_documented_paid_boolean_and_is_adapter_local() -> None:
    payload = {"authority": "auth-1", "status": "any-provider-value", "is_paid": True}
    unauthenticated = FakeClient([FakeResponse(payload)])
    result = KPayClient(settings(), client=unauthenticated).check_transaction(authority="auth-1")
    assert result.is_paid is True
    assert result.status == "any-provider-value"
    assert unauthenticated.calls[0] == (
        "/transactions/check/auth-1", {"headers": {}},
    )

    authenticated = FakeClient([FakeResponse(payload)])
    KPayClient(settings(kpay_check_send_auth=True), client=authenticated).check_transaction(authority="auth-1")
    assert authenticated.calls[0][1]["headers"]["Authorization"] == "Bearer fake-access-token"


def test_check_transaction_rejects_non_boolean_paid_value() -> None:
    provider = KPayClient(settings(), client=FakeClient([FakeResponse({
        "authority": "auth-1", "status": "paid", "is_paid": "true",
    })]))
    with pytest.raises(KPayProviderError, match="check response is invalid"):
        provider.check_transaction(authority="auth-1")


def test_create_timeout_is_ambiguous_and_provider_errors_are_sanitized() -> None:
    request = httpx.Request("POST", "https://kpay.website/api/v1/transactions/create")
    provider = KPayClient(settings(), client=FakeClient(error=httpx.ReadTimeout("secret", request=request)))
    with pytest.raises(KPayCreateUnknown, match="result is unknown") as error:
        provider.create_transaction(amount=1, callback_url="https://directpilot.example/callback", description="safe", factor_number="safe")
    assert "secret" not in str(error.value)


def test_malformed_or_non_https_create_response_fails_closed() -> None:
    provider = KPayClient(settings(), client=FakeClient([FakeResponse({
        "id": "tx-1", "authority": "auth-1", "amount": 1,
        "final_amount": 1, "fee": 0, "status": "pending",
        "payment_url": "http://unsafe.example/payment",
    })]))
    with pytest.raises(KPayProviderError, match="response is invalid"):
        provider.create_transaction(amount=1, callback_url="https://directpilot.example/callback", description="safe", factor_number="safe")
