"""DirectPilot TelBot -- isolated, fail-closed FastAPI UAT backend.

This module is not imported by the Instagram DirectPilot production app.
No external Telegram API calls, no bot-token or customer data in logs/responses.
API requires a dedicated UAT database URL and official Manager Bot token.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row

from experiments.telegram_bot_builder.auth import TelegramAuthError, TelegramPrincipal, verify_init_data
from experiments.telegram_bot_builder.core import check_webhook_secret


app = FastAPI(
    title="DirectPilot TelBot UAT API",
    version="0.1.0",
    docs_url=None, redoc_url=None, openapi_url=None,
)


def get_connection():
    """Scoped database connection; no production fallback, rollback on exceptions."""
    url = os.getenv("TELBOT_UAT_DATABASE_URL", "")
    if not url or os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=503, detail="TelBot UAT database unavailable")
    try:
        with psycopg.connect(url, row_factory=dict_row, connect_timeout=5) as connection:
            if connection.info.dbname != "telbot":
                raise HTTPException(status_code=503, detail="Wrong TelBot database")
            yield connection
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="TelBot UAT database unavailable") from exc


Db = Annotated[Any, Depends(get_connection)]


def authenticate(
    init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
) -> TelegramPrincipal:
    manager_token = os.getenv("TELBOT_MANAGER_TOKEN", "")
    if not manager_token:
        raise HTTPException(status_code=503, detail="Telegram login not configured")
    try:
        return verify_init_data(init_data or "", manager_token)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=401, detail="Invalid Telegram Mini App authentication") from exc


Principal = Annotated[TelegramPrincipal, Depends(authenticate)]


def require_member(db: Any, tenant: UUID, actor: TelegramPrincipal, *, write: bool = False) -> None:
    row = db.execute(
        """SELECT tu.role FROM telbot.tenant_users tu
             JOIN telbot.tenants t ON t.id=tu.tenant_id
             WHERE tu.tenant_id=%s AND tu.telegram_user_id=%s
               AND tu.status='active' AND t.status='active'""",
        (tenant, actor.user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Tenant membership required")
    if write and row["role"] not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor membership required")


def require_bot(db: Any, tenant: UUID, bot_id: UUID) -> dict[str, Any]:
    row = db.execute(
        """SELECT id,telegram_bot_id,username,display_name,status
             FROM telbot.bots
             WHERE tenant_id=%s AND id=%s AND status<>'revoked'""",
        (tenant, bot_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bot not found")
    return row


class DraftInput(BaseModel):
    greeting: str = Field(min_length=1, max_length=4096)
    fallback_reply: str = Field(min_length=1, max_length=4096)


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "live", "service": "directpilot-telbot-uat"}


@app.get("/ready")
def ready(db: Db) -> dict[str, str]:
    version = db.execute(
        "SELECT version FROM telbot.schema_migrations ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if not version or version["version"] != "0002_webhook_auth":
        raise HTTPException(status_code=503, detail="TelBot schema not ready")
    if not os.getenv("TELBOT_MANAGER_TOKEN") or not os.getenv("TELBOT_MANAGER_WEBHOOK_SECRET"):
        raise HTTPException(status_code=503, detail="Telegram manager not configured")
    return {"status": "ready", "database": "available", "migration": "current"}


@app.get("/api/v1/tenants/{tenant_id}/bots")
def list_bots(tenant_id: UUID, actor: Principal, db: Db) -> list[dict[str, Any]]:
    require_member(db, tenant_id, actor)
    rows = db.execute(
        """SELECT id, telegram_bot_id, username, display_name, status, created_at
             FROM telbot.bots WHERE tenant_id=%s AND status<>'revoked'
             ORDER BY created_at DESC LIMIT 100""", (tenant_id,),
    ).fetchall()
    return rows


@app.get("/api/v1/tenants/{tenant_id}/bots/{bot_id}/config")
def get_published_config(
    tenant_id: UUID, bot_id: UUID, actor: Principal, db: Db,
) -> dict[str, Any]:
    require_member(db, tenant_id, actor)
    require_bot(db, tenant_id, bot_id)
    row = db.execute(
        """SELECT id,version,greeting,fallback_reply,published_at
             FROM telbot.configuration_versions
             WHERE tenant_id=%s AND bot_id=%s AND state='published' LIMIT 1""",
        (tenant_id, bot_id),
    ).fetchone()
    if not row:
        return {"published": None, "rules": []}
    rules = db.execute(
        """SELECT keyword, match_mode,response_text,priority FROM telbot.reply_rules
             WHERE tenant_id=%s AND configuration_id=%s AND enabled=true
             ORDER BY priority ASC LIMIT 100""",
        (tenant_id, row["id"]),
    ).fetchall()
    return {"published": row, "rules": rules}


@app.post("/api/v1/tenants/{tenant_id}/bots/{bot_id}/configs", status_code=201)
def create_draft(
    tenant_id: UUID, bot_id: UUID, body: DraftInput, actor: Principal, db: Db,
) -> dict[str, Any]:
    require_member(db, tenant_id, actor, write=True)
    if not body.greeting.strip() or not body.fallback_reply.strip():
        raise HTTPException(status_code=422, detail="Message cannot be blank")
    # Lock bot row to serialize version allocation among concurrent editors.
    row = db.execute(
        """SELECT id FROM telbot.bots WHERE tenant_id=%s AND id=%s
             AND status<>'revoked' FOR UPDATE""", (tenant_id, bot_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bot not found")
    next_version = db.execute(
        """SELECT COALESCE(MAX(version),0)+1 AS n FROM telbot.configuration_versions
             WHERE bot_id=%s""", (bot_id,),
    ).fetchone()["n"]
    new = db.execute(
        """INSERT INTO telbot.configuration_versions
             (tenant_id,bot_id,version,greeting,fallback_reply,created_by_telegram_user_id)
             VALUES (%s,%s,%s,%s,%s,%s) RETURNING id,version,state""",
        (tenant_id, bot_id, next_version, body.greeting, body.fallback_reply, actor.user_id),
    ).fetchone()
    db.commit()
    return new


@app.post("/api/v1/tenants/{tenant_id}/bots/{bot_id}/configs/{config_id}/publish")
def publish_draft(
    tenant_id: UUID, bot_id: UUID, config_id: UUID, actor: Principal, db: Db,
) -> dict[str, Any]:
    require_member(db, tenant_id, actor, write=True)
    # Lock at bot level: prevents concurrent publish/create races.
    bot = db.execute(
        """SELECT id FROM telbot.bots WHERE tenant_id=%s AND id=%s
             AND status<>'revoked' FOR UPDATE""", (tenant_id, bot_id),
    ).fetchone()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    row = db.execute(
        """SELECT id,state,version FROM telbot.configuration_versions
             WHERE tenant_id=%s AND bot_id=%s AND id=%s FOR UPDATE""",
        (tenant_id, bot_id, config_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    if row["state"] != "draft":
        raise HTTPException(status_code=409, detail="Only draft configuration can be published")
    db.execute(
        """UPDATE telbot.configuration_versions SET state='archived'
             WHERE tenant_id=%s AND bot_id=%s AND state='published'""",
        (tenant_id, bot_id),
    )
    db.execute(
        """UPDATE telbot.configuration_versions SET state='published',published_at=now()
             WHERE id=%s AND tenant_id=%s AND bot_id=%s""",
        (config_id, tenant_id, bot_id),
    )
    db.commit()
    return {"id": str(config_id), "version": row["version"], "state": "published"}


async def parse_update(request: Request) -> dict[str, Any]:
    # Limit size before loading into memory. Telegram update_id is per-bot unique.
    if request.headers.get("content-length"):
        try:
            if int(request.headers["content-length"]) > 65536:
                raise HTTPException(status_code=413, detail="Telegram update too large")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid request size")
    data = await request.body()
    if len(data) > 65536:
        raise HTTPException(status_code=413, detail="Telegram update too large")
    try:
        update = json.loads(data)
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram update") from exc
    if not isinstance(update, dict):
        raise HTTPException(status_code=400, detail="Invalid Telegram update")
    update_id = update.get("update_id")
    if not isinstance(update_id, int) or isinstance(update_id, bool) or update_id < 0:
        raise HTTPException(status_code=400, detail="Missing update ID")
    return update


@app.post("/api/v1/webhooks/manager")
async def manager_webhook(request: Request, db: Db) -> dict[str, bool]:
    expected = os.getenv("TELBOT_MANAGER_WEBHOOK_SECRET", "")
    supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not check_webhook_secret(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook signature")
    update = await parse_update(request)
    event_type = "managed_bot" if ("managed_bot" in update or
        isinstance(update.get("message"), dict) and "managed_bot_created" in update["message"]
    ) else "other"
    # Durable, idempotent receipt; managed-bot linking and Bot API calls remain disabled
    # until BotFather manager is configured and owner authorization is tested.
    inserted = db.execute(
        """INSERT INTO telbot.manager_inbound_updates(telegram_update_id,event_type)
             VALUES (%s,%s) ON CONFLICT (telegram_update_id) DO NOTHING
             RETURNING id""",
        (update["update_id"], event_type),
    ).fetchone()
    db.commit()
    return {"acknowledged": True, "duplicate": inserted is None}


@app.post("/api/v1/webhooks/bots/{telegram_bot_id}")
async def child_webhook(telegram_bot_id: int, request: Request, db: Db) -> dict[str, bool]:
    if telegram_bot_id <= 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot = db.execute(
        """SELECT id,tenant_id,webhook_secret_digest FROM telbot.bots
             WHERE telegram_bot_id=%s AND status='active'""",
        (telegram_bot_id,),
    ).fetchone()
    if not bot or not bot["webhook_secret_digest"]:
        raise HTTPException(status_code=404, detail="Bot not found")
    supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not supplied or len(supplied) > 256:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook signature")
    if not check_webhook_secret(supplied, supplied):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook signature")
    import hmac
    expected_digest = bytes(bot["webhook_secret_digest"])
    if not hmac.compare_digest(expected_digest, hashlib.sha256(supplied.encode()).digest()):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook signature")
    update = await parse_update(request)
    message = update.get("message")
    text = message.get("text") if isinstance(message, dict) else None
    text = text[:4096] if isinstance(text, str) else None
    inserted = db.execute(
        """INSERT INTO telbot.inbound_updates(tenant_id,bot_id,telegram_update_id,incoming_text)
             VALUES (%s,%s,%s,%s) ON CONFLICT (bot_id,telegram_update_id) DO NOTHING
             RETURNING id""",
        (bot["tenant_id"], bot["id"], update["update_id"], text),
    ).fetchone()
    db.commit()
    # No automated sending here: awaiting explicit live integration acceptance.
    return {"acknowledged": True, "duplicate": inserted is None}
