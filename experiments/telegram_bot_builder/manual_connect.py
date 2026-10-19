"""Manual BotFather bot onboarding, isolated to TelBot UAT.

This module never registers a webhook, sends a Telegram message, or logs a token.
"""
from __future__ import annotations

import re
from typing import Any
import httpx
from fastapi import HTTPException

_TOKEN_PATTERN = re.compile(r"^[0-9]{5,16}:[A-Za-z0-9_-]{20,150}$")


async def validate_botfather_token(token: str, transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    """Read-only getMe. Returned data never includes credentials or raw API errors."""
    if not _TOKEN_PATTERN.fullmatch(token):
        raise HTTPException(status_code=422, detail="Invalid Telegram bot token format")
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(6.0, connect=4.0),
            follow_redirects=False,
            transport=transport,
            trust_env=transport is None,
        ) as client:
            response = await client.get("https://api.telegram.org/bot" + token + "/getMe")
        if response.status_code in (401, 403):
            raise HTTPException(status_code=422, detail="Telegram rejected bot credential")
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Telegram identity validation unavailable")
        obj = response.json()
        bot = obj.get("result") if isinstance(obj, dict) and obj.get("ok") is True else None
        if not isinstance(bot, dict) or bot.get("is_bot") is not True:
            raise HTTPException(status_code=422, detail="Invalid Telegram bot identity")
        telegram_id = bot.get("id")
        username = bot.get("username")
        if (type(telegram_id) is not int or telegram_id <= 0
                or not isinstance(username, str)
                or not username.lower().endswith("bot")
                or len(username) > 32):
            raise HTTPException(status_code=422, detail="Invalid Telegram bot identity")
        name = str(bot.get("first_name") or username).strip()[:120] or username
        return {"telegram_bot_id": telegram_id, "username": username, "display_name": name}
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        # HTTPX exceptions may include the token-containing request URL. Never propagate.
        raise HTTPException(status_code=503, detail="Telegram identity validation unavailable") from None
