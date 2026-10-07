"""Fail-closed relay for Meta webhook delivery between DirectPilot environments."""

from __future__ import annotations

import logging
from time import perf_counter
from urllib.parse import urlsplit

import httpx

from app.config import Settings


logger = logging.getLogger("sales_assistant.meta_relay")


class MetaRelayError(Exception):
    """Sanitized relay failure. Never carries webhook or credential content."""


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 1)


async def relay_instagram_webhook(
    settings: Settings,
    *,
    raw_body: bytes,
    signature: str,
    content_type: str | None,
    hub_delivery: str | None,
    meta_delivery_id: str | None,
) -> bool:
    """Relay a Meta-signed webhook to a fixed configured target.

    Returns False when relay mode is disabled. The caller must validate the
    original Meta signature before invoking this function. No retry is
    performed here; a non-2xx target response fails closed so Meta can retry
    the original delivery according to its own policy.
    """

    target = settings.meta_webhook_relay_target_url.strip()
    if not target:
        return False

    headers = {
        "content-type": (content_type or "application/json").split(";", 1)[0].strip()
        or "application/json",
        "x-hub-signature-256": signature,
    }
    if hub_delivery:
        headers["x-hub-delivery"] = hub_delivery
    if meta_delivery_id:
        headers["x-meta-delivery-id"] = meta_delivery_id

    started = perf_counter()
    target_host = urlsplit(target).hostname or "unknown"
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.meta_relay_timeout_seconds),
            follow_redirects=False,
        ) as client:
            response = await client.post(target, content=raw_body, headers=headers)
    except httpx.HTTPError as exc:
        logger.error(
            "Instagram webhook relay failed",
            extra={
                "event_code": "instagram.webhook.relay_failed",
                "target_host": target_host,
                "exception_class": type(exc).__name__,
                "elapsed_ms": _elapsed_ms(started),
            },
        )
        raise MetaRelayError("Instagram webhook relay failed") from exc

    if not 200 <= response.status_code < 300:
        logger.error(
            "Instagram webhook relay target rejected delivery",
            extra={
                "event_code": "instagram.webhook.relay_rejected",
                "target_host": target_host,
                "target_status": response.status_code,
                "elapsed_ms": _elapsed_ms(started),
            },
        )
        raise MetaRelayError("Instagram webhook relay failed")

    logger.info(
        "Instagram webhook relayed",
        extra={
            "event_code": "instagram.webhook.relay_succeeded",
            "target_host": target_host,
            "target_status": response.status_code,
            "elapsed_ms": _elapsed_ms(started),
        },
    )
    return True
