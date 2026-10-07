from __future__ import annotations

import asyncio

import httpx
import pytest

from app.config import Settings
from app.infrastructure.integrations.meta_relay import (
    MetaRelayError,
    relay_instagram_webhook,
)


class _RelayResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _RelayClient:
    def __init__(self, recorder: dict[str, object], status_code: int) -> None:
        self.recorder = recorder
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(self, url: str, **kwargs: object) -> _RelayResponse:
        self.recorder["url"] = url
        self.recorder["content"] = kwargs.get("content")
        self.recorder["headers"] = kwargs.get("headers")
        return _RelayResponse(self.status_code)


def test_meta_relay_target_requires_plain_https_url() -> None:
    for value in (
        "http://prod.example/webhook",
        "https://user:pass@prod.example/webhook",
        "https://prod.example/webhook?token=secret",
    ):
        with pytest.raises(ValueError):
            Settings(_env_file=None, meta_webhook_relay_target_url=value)


def test_webhook_relay_preserves_exact_signed_body_and_delivery_headers(
    monkeypatch,
) -> None:
    recorder: dict[str, object] = {}
    monkeypatch.setattr(
        "app.infrastructure.integrations.meta_relay.httpx.AsyncClient",
        lambda **_kwargs: _RelayClient(recorder, 200),
    )
    settings = Settings(
        _env_file=None,
        meta_webhook_relay_target_url=(
            "https://directpilot-api.onrender.com/api/v1/integrations/instagram/webhook"
        ),
    )
    body = b'{"object":"instagram","entry":[]}'

    relayed = asyncio.run(
        relay_instagram_webhook(
            settings,
            raw_body=body,
            signature="sha256=" + ("a" * 64),
            content_type="application/json; charset=utf-8",
            hub_delivery="delivery-1",
            meta_delivery_id="meta-delivery-1",
        )
    )

    assert relayed is True
    assert recorder["url"] == settings.meta_webhook_relay_target_url
    assert recorder["content"] == body
    assert recorder["headers"] == {
        "content-type": "application/json",
        "x-hub-signature-256": "sha256=" + ("a" * 64),
        "x-hub-delivery": "delivery-1",
        "x-meta-delivery-id": "meta-delivery-1",
    }


def test_webhook_relay_fails_closed_without_internal_retry(monkeypatch) -> None:
    recorder: dict[str, object] = {}
    monkeypatch.setattr(
        "app.infrastructure.integrations.meta_relay.httpx.AsyncClient",
        lambda **_kwargs: _RelayClient(recorder, 503),
    )
    settings = Settings(
        _env_file=None,
        meta_webhook_relay_target_url=(
            "https://directpilot-api.onrender.com/api/v1/integrations/instagram/webhook"
        ),
    )

    with pytest.raises(MetaRelayError):
        asyncio.run(
            relay_instagram_webhook(
                settings,
                raw_body=b"{}",
                signature="sha256=" + ("b" * 64),
                content_type="application/json",
                hub_delivery=None,
                meta_delivery_id=None,
            )
        )


def test_webhook_relay_is_disabled_without_target() -> None:
    settings = Settings(_env_file=None)
    assert (
        asyncio.run(
            relay_instagram_webhook(
                settings,
                raw_body=b"{}",
                signature="sha256=" + ("c" * 64),
                content_type="application/json",
                hub_delivery=None,
                meta_delivery_id=None,
            )
        )
        is False
    )
