"""UAT-only manual BotFather bot connection.

User owns the BotFather token; Telegram getMe validates it server-side.
Never disclose, log or return the token. No setWebhook or outbound messages.
"""
from __future__ import annotations

import re
import logging
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException

# Bot API places the credential in the URL path; suppress httpx/httpcore request URL logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

try:
    from experiments.telegram_bot_builder.vault import TokenVault
except ModuleNotFoundError:
    from vault import TokenVault


_TOKEN_RE = re.compile(r"^[1-9][0-9]{4,19}:[A-Za-z0-9_-]{20,180}$")


async def verified_identity(token: str, *, transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    """getMe is read-only. All failures are classified without credential echo."""
    if not _TOKEN_RE.fullmatch(token):
        raise HTTPException(status_code=422, detail="Invalid Telegram bot token format")
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(6, connect=3), follow_redirects=False,
            transport=transport, trust_env=transport is None,
        ) as client:
            # Bot API requires the credential within the HTTPS URL path.
            # Never log, redirect, or propagate the URL from an exception.
            response = await client.get("https://api.telegram.org/bot" + token + "/getMe")
        if response.status_code in (401, 403, 404):
            raise HTTPException(status_code=422, detail="Telegram bot token rejected")
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Telegram validation unavailable")
        data = response.json()
        user = data.get("result") if isinstance(data, dict) and data.get("ok") is True else None
        if not isinstance(user, dict) or user.get("is_bot") is not True:
            raise HTTPException(status_code=422, detail="Telegram bot token rejected")
        number, username = user.get("id"), user.get("username")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise HTTPException(status_code=502, detail="Invalid Telegram identity response")
        if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
            raise HTTPException(status_code=502, detail="Invalid Telegram identity response")
        display = user.get("first_name")
        if not isinstance(display, str) or not display.strip():
            display = username
        return {"telegram_bot_id": number, "username": username, "display_name": display[:120]}
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Telegram validation unavailable") from None
    except (ValueError, TypeError):
        raise HTTPException(status_code=502, detail="Invalid Telegram identity response") from None


async def manual_connect(
    *,
    db: Any,
    tenant_id: UUID,
    owner_telegram_user_id: int,
    token: str,
    encryption_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    """Validate and encrypt; unique Telegram ID prevents cross-tenant claims."""
    vault = TokenVault(encryption_key)
    identity = await verified_identity(token, transport=transport)
    ciphertext = vault.encrypt(token)
    row = db.execute(
        """INSERT INTO telbot.bots
           (tenant_id,telegram_bot_id,username,display_name,
            owner_telegram_user_id,credential_ciphertext,
            credential_key_version,status)
           VALUES (%s,%s,%s,%s,%s,%s,1,'pending')
           ON CONFLICT (telegram_bot_id) DO NOTHING
           RETURNING id,username,status""",
        (
            tenant_id, identity["telegram_bot_id"], identity["username"],
            identity["display_name"], owner_telegram_user_id, ciphertext,
        ),
    ).fetchone()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bot already connected")
    db.execute(
        """INSERT INTO telbot.audit_events
           (tenant_id,bot_id,actor_telegram_user_id,event_type,metadata)
           VALUES (%s,%s,%s,'manual_bot_connected',%s::jsonb)""",
        (tenant_id, row["id"], owner_telegram_user_id, '{"method":"botfather","status":"pending"}'),
    )
    db.commit()
    return {
        "id": str(row["id"]),
        "username": identity["username"],
        "status": "pending",
        "webhook_registered": False,
        "message_sending_enabled": False,
    }
