"""Strict server-only Telegram Bot API retrieval of a managed child's credential.

No token in responses/logs; requires the manager bot's credentials.
Does not revoke tokens or set webhooks.
"""
from __future__ import annotations

import re
import httpx

_TOKEN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{25,200}$")


class ManagedCredentialError(ValueError):
    """Fixed safe categories, never include Telegram response or request URL."""


async def fetch_managed_bot_token(
    manager_token: str, child_bot_id: int, *, transport: httpx.AsyncBaseTransport | None = None
) -> str:
    if not isinstance(manager_token, str) or not _TOKEN.fullmatch(manager_token):
        raise ManagedCredentialError("manager_not_configured")
    if type(child_bot_id) is not int or child_bot_id <= 0:
        raise ManagedCredentialError("invalid_child_identity")
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8, connect=4), follow_redirects=False,
            trust_env=transport is None, transport=transport,
        ) as client:
            response = await client.post(
                "https://api.telegram.org/bot" + manager_token + "/getManagedBotToken",
                json={"user_id": child_bot_id},
            )
            if response.status_code != 200:
                raise ManagedCredentialError("manager_api_unavailable")
            payload = response.json()
            token = payload.get("result") if isinstance(payload, dict) and payload.get("ok") is True else None
            if not isinstance(token, str) or not _TOKEN.fullmatch(token):
                raise ManagedCredentialError("managed_token_unavailable")
            if int(token.split(":", 1)[0]) != child_bot_id:
                raise ManagedCredentialError("managed_token_identity_mismatch")
            return token
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        if isinstance(exc, ManagedCredentialError):
            raise
        raise ManagedCredentialError("manager_api_unavailable") from None
