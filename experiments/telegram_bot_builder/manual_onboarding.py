"""Manual BotFather token onboarding for isolated TelBot UAT.

No webhook registration or outbound messaging. Never log or return tokens.
"""
from __future__ import annotations
import re
from typing import Any
import httpx

_TOKEN_PATTERN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{25,200}$")

class BotTokenValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

async def validate_botfather_token(
    token: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> dict[str, Any]:
    if not isinstance(token, str) or not _TOKEN_PATTERN.fullmatch(token):
        raise BotTokenValidationError("invalid_token_format")
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8, connect=4), follow_redirects=False,
            transport=transport, trust_env=transport is None,
        ) as client:
            response = await client.get("https://api.telegram.org/bot" + token + "/getMe")
            if response.status_code in (401, 403):
                raise BotTokenValidationError("token_rejected")
            if response.status_code != 200:
                raise BotTokenValidationError("telegram_unavailable")
            payload = response.json()
            bot = payload.get("result") if isinstance(payload, dict) and payload.get("ok") is True else None
            if not isinstance(bot, dict) or bot.get("is_bot") is not True:
                raise BotTokenValidationError("telegram_invalid_identity")
            bot_id = bot.get("id")
            username = bot.get("username")
            if not isinstance(bot_id, int) or isinstance(bot_id, bool) or bot_id <= 0 or not isinstance(username, str):
                raise BotTokenValidationError("telegram_invalid_identity")
            return {"telegram_bot_id": bot_id, "username": username, "display_name": str(bot.get("first_name") or username)[:120]}
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        # Exceptions may contain the full URL with the credential: never propagate.
        raise BotTokenValidationError("telegram_unavailable") from None
