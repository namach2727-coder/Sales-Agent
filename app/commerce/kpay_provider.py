"""Isolated, secret-safe KPay HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from app.config import Settings


class KPayError(Exception):
    """Safe provider error. Messages never include provider payloads or secrets."""


class KPayConfigurationError(KPayError):
    pass


class KPayProviderError(KPayError):
    pass


class KPayCreateUnknown(KPayError):
    pass


@dataclass(frozen=True, slots=True)
class KPayCreateResult:
    transaction_id: str
    authority: str
    amount: int
    final_amount: int
    fee: int
    status: str
    payment_url: str


@dataclass(frozen=True, slots=True)
class KPayVerifyResult:
    transaction_id: str
    authority: str
    status: str
    amount: int
    paid_at: datetime | None


@dataclass(frozen=True, slots=True)
class KPayCheckResult:
    authority: str
    status: str
    is_paid: bool


class KPayProvider(Protocol):
    def create_transaction(
        self, *, amount: int, callback_url: str, description: str,
        factor_number: str,
    ) -> KPayCreateResult: ...

    def verify_transaction(self, *, authority: str) -> KPayVerifyResult: ...

    def check_transaction(self, *, authority: str) -> KPayCheckResult: ...


class KPayClient:
    code = "kpay"

    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        token = settings.kpay_access_token.get_secret_value().strip()
        shop_id = settings.kpay_shop_id.get_secret_value().strip()
        card_id = settings.kpay_card_id.get_secret_value().strip()
        base_url = settings.kpay_base_url.rstrip("/")
        if not all((token, shop_id, card_id, base_url)):
            raise KPayConfigurationError("KPay is not configured")
        if urlparse(base_url).scheme != "https":
            raise KPayConfigurationError("KPay base URL must use HTTPS")
        self._token = token
        self._shop_id = shop_id
        self._card_id = card_id
        self._fee_side = settings.kpay_fee_side
        self._verify_send_auth = settings.kpay_verify_send_auth
        self._check_send_auth = settings.kpay_check_send_auth
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(settings.kpay_timeout_seconds),
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def create_transaction(
        self, *, amount: int, callback_url: str, description: str,
        factor_number: str,
    ) -> KPayCreateResult:
        try:
            response = self._client.post(
                "/transactions/create",
                headers=self._auth_headers(),
                json={
                    "shop_id": self._shop_id,
                    "card_id": self._card_id,
                    "amount": amount,
                    "callback_url": callback_url,
                    "description": description,
                    "factor_number": factor_number,
                    "fee_side": self._fee_side,
                },
            )
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise KPayCreateUnknown("KPay create result is unknown") from exc
        except httpx.HTTPStatusError as exc:
            raise KPayProviderError("KPay rejected transaction creation") from exc
        payload = self._json_object(response)
        try:
            result = KPayCreateResult(
                transaction_id=self._required_text(payload, "id"),
                authority=self._required_text(payload, "authority"),
                amount=self._integer(payload, "amount"),
                final_amount=self._integer(payload, "final_amount"),
                fee=self._integer(payload, "fee"),
                status=self._required_text(payload, "status"),
                payment_url=self._required_https_url(payload, "payment_url"),
            )
        except (TypeError, ValueError) as exc:
            raise KPayProviderError("KPay create response is invalid") from exc
        return result

    def verify_transaction(self, *, authority: str) -> KPayVerifyResult:
        headers = self._auth_headers() if self._verify_send_auth else {}
        try:
            response = self._client.post(
                "/transactions/verify",
                headers=headers,
                json={"authority": authority},
            )
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise KPayProviderError("KPay verification is temporarily unavailable") from exc
        except httpx.HTTPStatusError as exc:
            raise KPayProviderError("KPay rejected transaction verification") from exc
        payload = self._json_object(response)
        try:
            return KPayVerifyResult(
                transaction_id=self._required_text(payload, "id"),
                authority=self._required_text(payload, "authority"),
                status=self._required_text(payload, "status"),
                amount=self._integer(payload, "amount"),
                paid_at=self._optional_datetime(payload.get("paid_at")),
            )
        except (TypeError, ValueError) as exc:
            raise KPayProviderError("KPay verify response is invalid") from exc

    def check_transaction(self, *, authority: str) -> KPayCheckResult:
        headers = self._auth_headers() if self._check_send_auth else {}
        try:
            response = self._client.get(
                f"/transactions/check/{authority}", headers=headers,
            )
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise KPayProviderError("KPay payment check is temporarily unavailable") from exc
        except httpx.HTTPStatusError as exc:
            raise KPayProviderError("KPay rejected payment check") from exc
        payload = self._json_object(response)
        try:
            is_paid = payload.get("is_paid")
            if not isinstance(is_paid, bool):
                raise TypeError("is_paid")
            return KPayCheckResult(
                authority=self._required_text(payload, "authority"),
                status=self._required_text(payload, "status"),
                is_paid=is_paid,
            )
        except (TypeError, ValueError) as exc:
            raise KPayProviderError("KPay check response is invalid") from exc

    @staticmethod
    def _json_object(response: Any) -> dict[str, Any]:
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise KPayProviderError("KPay response is invalid") from exc
        if not isinstance(payload, dict):
            raise KPayProviderError("KPay response is invalid")
        return payload

    @staticmethod
    def _required_text(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(key)
        return value.strip()

    @staticmethod
    def _integer(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(key)
        return value

    @classmethod
    def _required_https_url(cls, payload: dict[str, Any], key: str) -> str:
        value = cls._required_text(payload, key)
        if urlparse(value).scheme != "https":
            raise ValueError(key)
        return value

    @staticmethod
    def _optional_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("paid_at")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
