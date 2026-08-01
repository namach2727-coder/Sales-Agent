"""Synchronous Meta Graph adapter for one bound Instagram connection."""

from __future__ import annotations

from typing import Any

import httpx

from app.application.outbound import (
    OutboundAuthenticationError,
    OutboundDeliveryResult,
    OutboundInvalidResponseError,
    OutboundMessage,
    OutboundRateLimitError,
    OutboundRecipientUnavailableError,
    OutboundRejectedError,
    OutboundRequestError,
    OutboundTimeoutError,
    OutboundUnavailableError,
)
from app.config import Settings


class InstagramGraphSender:
    """Send text through Meta without logging or returning raw responses."""

    def __init__(
        self,
        *,
        base_url: str,
        api_version: str,
        timeout_seconds: float,
        access_token: str,
        sender_account_id: str,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version.strip().strip("/")
        self.timeout_seconds = timeout_seconds
        self._access_token = _credential(access_token)
        self._sender_account_id = _identifier(
            sender_account_id, "sender account"
        )
        self._client = client

    @property
    def send_url(self) -> str:
        return (
            f"{self.base_url}/{self.api_version}/"
            f"{self._sender_account_id}/messages"
        )

    def send(self, message: OutboundMessage) -> OutboundDeliveryResult:
        request = {
            "headers": {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            "json": {
                "recipient": {"id": message.recipient_external_id},
                "message": {"text": message.text},
            },
            "timeout": self.timeout_seconds,
        }
        try:
            if self._client is None:
                with httpx.Client() as client:
                    response = client.post(self.send_url, **request)
            else:
                response = self._client.post(self.send_url, **request)
        except httpx.TimeoutException as exc:
            raise OutboundTimeoutError("Instagram delivery timed out") from exc
        except httpx.HTTPError as exc:
            raise OutboundUnavailableError(
                "Instagram delivery is unavailable"
            ) from exc

        _raise_for_status(response)
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise OutboundInvalidResponseError(
                "Instagram returned an invalid response"
            ) from exc
        if not isinstance(payload, dict):
            raise OutboundInvalidResponseError(
                "Instagram returned an invalid response"
            )
        provider_message_id = payload.get("message_id")
        if not isinstance(provider_message_id, str) or not provider_message_id.strip():
            raise OutboundInvalidResponseError(
                "Instagram returned an invalid response"
            )
        return OutboundDeliveryResult(
            message_public_id=message.message_public_id,
            conversation_public_id=message.conversation_public_id,
            channel="instagram",
            provider="instagram",
            delivered=True,
            provider_message_id=provider_message_id.strip(),
        )


def build_instagram_graph_sender(
    settings: Settings,
    *,
    access_token: str,
    sender_account_id: str,
    client: Any | None = None,
) -> InstagramGraphSender:
    return InstagramGraphSender(
        base_url=settings.meta_graph_base_url,
        api_version=settings.meta_api_version,
        timeout_seconds=settings.instagram_outbound_timeout_seconds,
        access_token=access_token,
        sender_account_id=sender_account_id,
        client=client,
    )


def _raise_for_status(response: Any) -> None:
    status = getattr(response, "status_code", None)
    if not isinstance(status, int):
        raise OutboundInvalidResponseError(
            "Instagram returned an invalid response"
        )
    if 200 <= status < 300:
        return
    if status in {401, 403}:
        error = OutboundAuthenticationError("Instagram authentication failed")
    elif status == 404:
        error = OutboundRecipientUnavailableError(
            "Instagram recipient is unavailable"
        )
    elif status == 429:
        error = OutboundRateLimitError("Instagram rate limit reached")
    elif status >= 500:
        error = OutboundUnavailableError("Instagram delivery is unavailable")
    elif status in {409, 410}:
        error = OutboundRejectedError("Instagram rejected the message")
    elif status in {400, 405, 422}:
        error = OutboundRequestError("Instagram delivery request failed")
    else:
        error = OutboundRequestError("Instagram delivery request failed")
    raise error


def _credential(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 8192:
        raise OutboundAuthenticationError("Instagram authentication failed")
    return value.strip()


def _identifier(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > 200
        or "\n" in value
        or "\r" in value
    ):
        raise OutboundRequestError(f"Invalid Instagram {field}")
    return value.strip()
