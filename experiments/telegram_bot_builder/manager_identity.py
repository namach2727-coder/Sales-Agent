"""Public-safe UAT-only check for the configured Telegram Manager Bot identity.

Read-only Telegram Bot API getMe. Never output credentials, numeric bot IDs,
raw upstream responses, or token-bearing URLs. A 5-minute per-instance cache
minimizes calls and prevents normal repeated page refreshes from spamming API.
"""
from __future__ import annotations
import hashlib
import time
from typing import Any

_cache: dict[str, Any] = {}

async def manager_identity_status(token: str, expected_username: str) -> dict[str, str]:
    if not token:
        return {"status": "missing"}
    if not expected_username or not expected_username.lstrip("@"):
        return {"status": "unavailable"}
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = time.monotonic()
    if (_cache.get("fingerprint") == fingerprint and
        _cache.get("expected") == expected_username.lower().lstrip("@") and
        now < _cache.get("until", 0)):
        return {"status": _cache["status"]}
    try:
        try:
            from experiments.telegram_bot_builder.manual_onboarding import validate_botfather_token
        except ModuleNotFoundError:
            from manual_onboarding import validate_botfather_token
        bot = await validate_botfather_token(token)
        status = "match" if bot["username"].casefold() == expected_username.lstrip("@").casefold() else "mismatch"
    except Exception:
        # This is a diagnostic only. Never propagate network exceptions whose URL
        # may contain the bot token. False availability is not a valid identity.
        status = "unavailable"
    _cache.update(fingerprint=fingerprint,
                  expected=expected_username.lower().lstrip("@"),
                  until=now + 300, status=status)
    return {"status": status}
