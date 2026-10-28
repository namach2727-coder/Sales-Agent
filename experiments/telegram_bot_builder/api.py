"""DirectPilot TelBot -- isolated, fail-closed FastAPI UAT backend.

This module is not imported by the Instagram DirectPilot production app.
No external Telegram API calls, no bot-token or customer data in logs/responses.
API requires a dedicated UAT database URL and official Manager Bot token.
"""
from __future__ import annotations
from urllib.parse import quote

import hashlib
import json
import os
import secrets
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row

try:
    from experiments.telegram_bot_builder.auth import TelegramAuthError, TelegramPrincipal, verify_init_data, safe_initdata_shape, diagnose_ed25519, diagnose_hmac_mismatch
    from experiments.telegram_bot_builder.core import (check_webhook_secret, build_managed_bot_request_keyboard,
        parse_managed_bot_created)
except ModuleNotFoundError:
    # Standalone Vercel UAT packaging keeps these source files in the same root.
    from auth import TelegramAuthError, TelegramPrincipal, verify_init_data, safe_initdata_shape, diagnose_ed25519, diagnose_hmac_mismatch
    from core import (check_webhook_secret, build_managed_bot_request_keyboard,
        parse_managed_bot_created)


app = FastAPI(
    title="DirectPilot TelBot UAT API",
    version="0.1.0",
    docs_url=None, redoc_url=None, openapi_url=None,
)


def uat_host_failure_reason(db_url: str, expected: str) -> str | None:
    """Categorical, secret-free reason for rejecting a non-UAT URI."""
    from urllib.parse import urlsplit, parse_qs

    expected = expected.strip().lower()
    if not expected or "/" in expected or ":" in expected:
        return "uat_host_configuration_invalid"
    if db_url != db_url.strip():
        return "connection_string_has_extra_whitespace"
    try:
        uri = urlsplit(db_url)
        if uri.scheme not in ("postgres", "postgresql"):
            return "connection_string_format_invalid"
        if any(key in parse_qs(uri.query, keep_blank_values=True) for key in ("host", "hostaddr")):
            return "uri_host_override_disallowed"
        if not uri.hostname:
            return "connection_string_hostname_missing"
        if uri.hostname not in (expected, expected.replace("-pooler.", ".")):
            return "hostname_not_in_uat_allowlist"
        return None
    except ValueError:
        return "connection_string_malformed"


def is_uat_host(db_url: str, expected: str) -> bool:
    return uat_host_failure_reason(db_url, expected) is None


def get_connection():
    """Scoped database connection; no production fallback, rollback on exceptions."""
    url = os.getenv("TELBOT_UAT_DATABASE_URL", "")
    if not url or os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=503, detail="TelBot UAT database unavailable")
    endpoint_issue = uat_host_failure_reason(url, os.getenv("TELBOT_UAT_DB_HOST", ""))
    if endpoint_issue:
        raise HTTPException(status_code=503, detail=f"TelBot UAT database endpoint mismatch: {endpoint_issue}")
    try:
        with psycopg.connect(url, row_factory=dict_row, connect_timeout=5) as connection:
            if connection.info.dbname != "telbot" or connection.info.user not in ("telbot_ua_runtime", "telbot_owner"):
                raise HTTPException(status_code=503, detail="Wrong TelBot UAT database role")
            # A mistakenly supplied Production branch has no 0002 ledger; it must fail here.
            if not connection.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='telbot' AND table_name='manager_inbound_updates') AS is_uat"
            ).fetchone()["is_uat"]:
                raise HTTPException(status_code=503, detail="TelBot UAT schema unavailable")
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
        # Detailed categories are UAT-only and contain no user data or secret material.
        detail = str(exc) if os.getenv("TELBOT_ENV") == "uat" else "Invalid Telegram Mini App authentication"
        headers = None
        if os.getenv("TELBOT_ENV") == "uat":
            headers = {"X-TelBot-UAT-Auth-Shape": safe_initdata_shape(init_data or "")}
            if str(exc) == "invalid_signature":
                headers["X-TelBot-UAT-Ed25519"] = diagnose_ed25519(init_data or "", manager_token)
                headers["X-TelBot-UAT-HMAC-Diag"] = diagnose_hmac_mismatch(init_data or "", manager_token)
        raise HTTPException(status_code=401, detail=detail, headers=headers) from None


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


class ManagedBotRequestInput(BaseModel):
    suggested_name: str = Field(min_length=1, max_length=64)
    suggested_username: str | None = Field(default=None, max_length=32)


def require_owner(db: Any, tenant: UUID, actor: TelegramPrincipal) -> None:
    """An editor/viewer must never enrol a new child bot."""
    row = db.execute(
        """SELECT tu.role FROM telbot.tenant_users tu
           JOIN telbot.tenants t ON t.id=tu.tenant_id
           WHERE tu.tenant_id=%s AND tu.telegram_user_id=%s
             AND tu.role='owner' AND tu.status='active' AND t.status='active'""",
        (tenant, actor.user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Tenant owner required")


@app.post("/api/v1/tenants/{tenant_id}/managed-bot-requests", status_code=201)
def request_managed_bot(
    tenant_id: UUID, body: ManagedBotRequestInput, actor: Principal, db: Db,
) -> dict[str, Any]:
    """Create one 15-minute request, NOT a Telegram bot or sent message.

    The reply_markup must later be delivered by the authenticated Manager Bot
    to the same Telegram user via the official Bot API. No live send here.
    """
    require_owner(db, tenant_id, actor)
    try:
        keyboard = build_managed_bot_request_keyboard(
            1, suggested_name=body.suggested_name,
            suggested_username=body.suggested_username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid managed bot details") from exc
    # Per-owner transaction lock prevents two ambiguous outstanding requests
    # across tenants, and is also acquired while matching Telegram updates.
    db.execute("SELECT pg_advisory_xact_lock(%s)", (actor.user_id,))
    existing = db.execute(
        """SELECT id FROM telbot.managed_bot_requests
           WHERE owner_telegram_user_id=%s AND status='pending'
             AND expires_at>now() LIMIT 1""",
        (actor.user_id,),
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Pending bot request already exists")
    request_id = secrets.randbelow(2**31 - 1) + 1
    saved = db.execute(
        """INSERT INTO telbot.managed_bot_requests
           (tenant_id,request_id,owner_telegram_user_id,expires_at)
           VALUES (%s,%s,%s,now()+interval '15 minutes')
           ON CONFLICT (tenant_id,request_id) DO NOTHING
           RETURNING id,request_id,expires_at""",
        (tenant_id, request_id, actor.user_id),
    ).fetchone()
    if not saved:
        raise HTTPException(status_code=409, detail="Request conflict; retry")
    db.commit()
    keyboard["keyboard"][0][0]["request_managed_bot"]["request_id"] = request_id
    return {
        "id": saved["id"], "request_id": request_id,
        "expires_at": saved["expires_at"], "delivery_status": "user_confirmation_required",
        "creation_url": (
            "https://t.me/newbot/DirectPilotManagerBot/"
            + quote(body.suggested_username or "")
            + "?name=" + quote(body.suggested_name.strip())
        ),
        "reply_markup": keyboard,
    }


@app.post("/api/v1/tenants/{tenant_id}/managed-bot-requests/{request_id}/send-keyboard")
async def send_managed_bot_keyboard(
    tenant_id: UUID, request_id: int, actor: Principal, db: Db,
) -> dict[str, str]:
    """Send official reply-keyboard creation request in the manager's private chat."""
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat" or not 0 < request_id < 2**31:
        raise HTTPException(status_code=404, detail="Not found")
    ticket = db.execute(
        """SELECT request_id FROM telbot.managed_bot_requests
           WHERE tenant_id=%s AND request_id=%s AND owner_telegram_user_id=%s
             AND status='pending' AND expires_at>now()""",
        (tenant_id, request_id, actor.user_id),
    ).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending request not found")
    token = os.getenv("TELBOT_MANAGER_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="Manager bot unavailable")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=httpx.Timeout(8, connect=4),
                                     follow_redirects=False) as client:
            response = await client.post(
                "https://api.telegram.org/bot" + token + "/sendMessage",
                json={
                    "chat_id": actor.user_id,
                    "text": "برای ساخت ربات اختصاصی، دکمه زیر را داخل همین چت بزن.",
                    "reply_markup": {
                        "keyboard": [[{
                            "text": "Create Bot",
                            "request_managed_bot": {"request_id": request_id},
                        }]],
                        "resize_keyboard": True, "one_time_keyboard": True,
                    },
                },
            )
            payload = response.json() if response.status_code == 200 else {}
            if not isinstance(payload, dict) or payload.get("ok") is not True:
                raise HTTPException(status_code=503, detail="Manager message unavailable")
    except HTTPException:
        raise
    except Exception:
        # Never echo Telegram HTTP errors: the request URL contains the manager token.
        raise HTTPException(status_code=503, detail="Manager message unavailable") from None
    return {"status": "sent_in_private_chat"}


class SelfTenantInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


@app.get("/api/v1/me/tenants")
def my_tenants(actor: Principal, db: Db) -> list[dict[str, Any]]:
    """Only the caller's active Telegram tenant memberships."""
    return db.execute(
        """SELECT t.id,t.display_name,tu.role FROM telbot.tenant_users tu
           JOIN telbot.tenants t ON t.id=tu.tenant_id
           WHERE tu.telegram_user_id=%s AND tu.status='active' AND t.status='active'
           ORDER BY t.created_at LIMIT 20""", (actor.user_id,),
    ).fetchall()


@app.post("/api/v1/me/tenants", status_code=201)
def create_my_tenant(
    body: SelfTenantInput, actor: Principal, db: Db,
) -> dict[str, Any]:
    """Explicit owner-initiated UAT tenant bootstrap; at most one per user."""
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    name = body.display_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Tenant name required")
    # Serialize concurrent creation for one Telegram account.
    db.execute("SELECT pg_advisory_xact_lock(%s)", (actor.user_id,))
    owner = db.execute(
        """SELECT tu.tenant_id FROM telbot.tenant_users tu
           JOIN telbot.tenants t ON t.id=tu.tenant_id
           WHERE tu.telegram_user_id=%s AND tu.role='owner'
             AND tu.status='active' AND t.status='active' LIMIT 1""",
        (actor.user_id,),
    ).fetchone()
    if owner:
        raise HTTPException(status_code=409, detail="Telegram account already has a tenant")
    created = db.execute(
        """INSERT INTO telbot.tenants (display_name) VALUES (%s)
           RETURNING id,display_name,status""", (name,),
    ).fetchone()
    db.execute(
        """INSERT INTO telbot.tenant_users(tenant_id,telegram_user_id,role)
           VALUES (%s,%s,'owner')""",
        (created["id"], actor.user_id),
    )
    db.commit()
    return {"id":str(created["id"]), "display_name":created["display_name"], "role":"owner"}


class ManualBotConnectInput(BaseModel):
    bot_token: str


@app.post("/api/v1/tenants/{tenant_id}/bots/connect-manual", status_code=201)
async def connect_manual_bot(
    tenant_id: UUID, body: ManualBotConnectInput, actor: Principal, db: Db,
) -> dict[str, Any]:
    """Add owner-provided BotFather child bot as pending; never set a webhook."""
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    from fastapi import status
    try:
        from experiments.telegram_bot_builder.vault import TokenVault, CredentialError
        from experiments.telegram_bot_builder.manual_onboarding import (
            BotTokenValidationError, validate_botfather_token,
        )
    except ModuleNotFoundError:
        from vault import TokenVault, CredentialError
        from manual_onboarding import BotTokenValidationError, validate_botfather_token
    try:
        # Fail closed before contacting Telegram if encryption is unavailable.
        vault = TokenVault(os.getenv("TELBOT_TOKEN_FERNET_KEY", ""))
        encrypted = vault.encrypt(body.bot_token)
    except CredentialError:
        raise HTTPException(status_code=503, detail="Bot credential encryption unavailable") from None
    try:
        bot = await validate_botfather_token(body.bot_token)
    except BotTokenValidationError as exc:
        code = exc.code if exc.code in (
            "invalid_token_format", "token_rejected", "telegram_unavailable",
            "telegram_invalid_identity",
        ) else "telegram_unavailable"
        raise HTTPException(status_code=422 if code in (
            "invalid_token_format", "token_rejected", "telegram_invalid_identity",
        ) else 503, detail=code) from None
    # Preserve global unique telegram_bot_id: do not transfer a claimed bot between tenants.
    try:
        row = db.execute(
            """INSERT INTO telbot.bots
              (tenant_id,telegram_bot_id,username,display_name,owner_telegram_user_id,
               credential_ciphertext,credential_key_version,status)
              VALUES (%s,%s,%s,%s,%s,%s,1,'pending')
              ON CONFLICT (telegram_bot_id) DO NOTHING
              RETURNING id,username,status""",
            (tenant_id,bot["telegram_bot_id"],bot["username"],bot["display_name"],
             actor.user_id,encrypted),
        ).fetchone()
        if not row:
            db.rollback()
            raise HTTPException(status_code=409, detail="Bot already connected")
        db.execute(
            """INSERT INTO telbot.audit_events
              (tenant_id,bot_id,actor_telegram_user_id,event_type,metadata)
              VALUES (%s,%s,%s,'bot.manual_connect_pending','{}'::jsonb)""",
            (tenant_id,row["id"],actor.user_id),
        )
        db.commit()
    except psycopg.errors.UniqueViolation:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bot already connected") from None
    return {"id": str(row["id"]), "username": row["username"], "status": "pending"}


@app.post("/api/v1/tenants/{tenant_id}/bots/{bot_id}/prepare-managed-credential")
async def prepare_managed_credential(
    tenant_id: UUID, bot_id: UUID, actor: Principal, db: Db,
) -> dict[str, str]:
    """UAT: fetch managed token on server only; never send credential to browser."""
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    try:
        from experiments.telegram_bot_builder.vault import TokenVault, CredentialError
        from experiments.telegram_bot_builder.managed_credentials import (
            fetch_managed_bot_token, ManagedCredentialError,
        )
    except ModuleNotFoundError:
        from vault import TokenVault, CredentialError
        from managed_credentials import fetch_managed_bot_token, ManagedCredentialError
    try:
        vault = TokenVault(os.getenv("TELBOT_TOKEN_FERNET_KEY", ""))
    except CredentialError:
        raise HTTPException(status_code=503, detail="Bot credential encryption unavailable") from None
    # A claimed, owner-matched bot is mandatory. No manual bots, no cross-tenant reads.
    bot = db.execute(
        """SELECT telegram_bot_id,credential_ciphertext FROM telbot.bots
           WHERE id=%s AND tenant_id=%s AND owner_telegram_user_id=%s
             AND managed_request_id IS NOT NULL AND status='pending'
           FOR UPDATE""",
        (bot_id, tenant_id, actor.user_id),
    ).fetchone()
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    if bot["credential_ciphertext"] is not None:
        db.commit()
        return {"status": "credential_stored"}
    try:
        token = await fetch_managed_bot_token(
            os.getenv("TELBOT_MANAGER_TOKEN", ""), bot["telegram_bot_id"]
        )
        ciphertext = vault.encrypt(token)
        del token
    except ManagedCredentialError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except CredentialError:
        raise HTTPException(status_code=503, detail="Bot credential encryption unavailable") from None
    db.execute(
        """UPDATE telbot.bots SET credential_ciphertext=%s,credential_key_version=1
           WHERE id=%s AND tenant_id=%s AND owner_telegram_user_id=%s
             AND managed_request_id IS NOT NULL AND status='pending'
             AND credential_ciphertext IS NULL""",
        (ciphertext, bot_id, tenant_id, actor.user_id),
    )
    db.commit()
    return {"status": "credential_stored"}


@app.get("/api/v1/tenants/{tenant_id}/managed-bot-requests")
def list_managed_bot_requests(
    tenant_id: UUID, actor: Principal, db: Db,
) -> list[dict[str, Any]]:
    require_owner(db, tenant_id, actor)
    return db.execute(
        """SELECT id,request_id,status,requested_at,expires_at,fulfilled_at
           FROM telbot.managed_bot_requests
           WHERE tenant_id=%s AND owner_telegram_user_id=%s
           ORDER BY requested_at DESC LIMIT 30""",
        (tenant_id, actor.user_id),
    ).fetchall()


class DraftInput(BaseModel):
    greeting: str = Field(min_length=1, max_length=4096)
    fallback_reply: str = Field(min_length=1, max_length=4096)


@app.get("/telbot")
def telbot_ui():
    """Serve only the isolated UAT Telegram Mini App."""
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(
        Path(__file__).resolve().parent / "web" / "index.html",
        headers={
            "Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; script-src 'self' https://telegram.org; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'self' https://web.telegram.org; form-action 'none'",
        },
    )


@app.get("/telbot/app.js")
def telbot_ui_script():
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(
        Path(__file__).resolve().parent / "web" / "app.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/telbot/style.css")
def telbot_ui_style():
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(
        Path(__file__).resolve().parent / "web" / "style.css",
        media_type="text/css",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "live", "service": "directpilot-telbot-uat"}


@app.get("/api/v1/uat/manager-identity")
async def manager_identity_diagnostic() -> dict[str, str]:
    """Read-only UAT support probe. Returns status only, never bot IDs or secrets."""
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    try:
        from experiments.telegram_bot_builder.manager_identity import manager_identity_status
    except ModuleNotFoundError:
        from manager_identity import manager_identity_status
    return await manager_identity_status(
        token=os.getenv("TELBOT_MANAGER_TOKEN", ""),
        expected_username="DirectPilotManagerBot",
    )


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
        """SELECT id, telegram_bot_id, username, display_name, status, created_at,
                    (managed_request_id IS NOT NULL) AS is_managed,
                    (credential_ciphertext IS NOT NULL) AS credential_ready
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


async def _manager_webhook_api(method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """UAT-only manager API; never include secret-bearing URLs or upstream errors in responses."""
    token = os.getenv("TELBOT_MANAGER_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="Manager bot not configured")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=4), follow_redirects=False) as client:
            response = await client.post("https://api.telegram.org/bot" + token + "/" + method, json=body or {})
            if response.status_code != 200:
                raise ValueError("telegram_unavailable")
            data = response.json()
            if data.get("ok") is not True:
                raise ValueError("telegram_not_ok")
            return data
    except Exception:
        raise HTTPException(status_code=503, detail="Telegram manager API unavailable") from None


@app.get("/api/v1/tenants/{tenant_id}/uat/manager-webhook")
async def get_manager_webhook_diagnostic(
    tenant_id: UUID, actor: Principal, db: Db,
) -> dict[str, Any]:
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    data = await _manager_webhook_api("getWebhookInfo")
    info = data.get("result") or {}
    expected = "https://directpilot-telbot-uat-api.vercel.app/api/v1/webhooks/manager"
    updates = info.get("allowed_updates")
    return {
        "configured_for_uat": info.get("url") == expected,
        "allowed_managed_bot": isinstance(updates, list) and "managed_bot" in updates,
        "allowed_message": isinstance(updates, list) and "message" in updates,
        "allowed_updates_default": updates is None,
        "pending_delivery_count": int(info.get("pending_update_count") or 0),
        "delivery_error_present": bool(info.get("last_error_date")),
        "webhook_present": bool(info.get("url")),
    }


@app.post("/api/v1/tenants/{tenant_id}/uat/manager-webhook/repair")
async def repair_manager_webhook(
    tenant_id: UUID, actor: Principal, db: Db,
) -> dict[str, str]:
    """Explicit UAT owner action; preserve queued updates; never affect another bot."""
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    secret = os.getenv("TELBOT_MANAGER_WEBHOOK_SECRET", "")
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret):
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    info = (await _manager_webhook_api("getWebhookInfo")).get("result") or {}
    current = info.get("url") or ""
    expected = "https://directpilot-telbot-uat-api.vercel.app/api/v1/webhooks/manager"
    if current and current != expected:
        # Never silently hijack a manager bot webhook owned by another environment.
        raise HTTPException(status_code=409, detail="Manager bot webhook points to a different endpoint")
    await _manager_webhook_api("setWebhook", {
        "url": expected, "secret_token": secret,
        "allowed_updates": ["message", "managed_bot"],
        "drop_pending_updates": False,
    })
    return {"status": "registered_for_uat"}


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
    # Durable receipt comes before any linking; duplicated updates never relink.
    inserted = db.execute(
        """INSERT INTO telbot.manager_inbound_updates(telegram_update_id,event_type)
             VALUES (%s,%s) ON CONFLICT (telegram_update_id) DO NOTHING
             RETURNING id""",
        (update["update_id"], event_type),
    ).fetchone()
    if not inserted:
        db.commit()
        return {"acknowledged": True, "duplicate": True}
    linked = False
    created = parse_managed_bot_created(update)
    if created is not None:
        # Telegram's managed_bot update contains owner and bot, but NO
        # request_id. Require exactly one unexpired pending request for that
        # owner across all tenants, otherwise deliberately do not link.
        db.execute("SELECT pg_advisory_xact_lock(%s)", (created.owner_user_id,))
        pending = db.execute(
            """SELECT r.id,r.tenant_id FROM telbot.managed_bot_requests r
               JOIN telbot.tenant_users tu
                 ON tu.tenant_id=r.tenant_id
                AND tu.telegram_user_id=r.owner_telegram_user_id
               JOIN telbot.tenants t ON t.id=r.tenant_id
               WHERE r.owner_telegram_user_id=%s AND r.status='pending'
                 AND r.expires_at>now() AND tu.role='owner'
                 AND tu.status='active' AND t.status='active'
               ORDER BY r.requested_at DESC LIMIT 2 FOR UPDATE OF r""",
            (created.owner_user_id,),
        ).fetchall()
        if len(pending) == 1:
            ticket = pending[0]
            display_name = (created.bot_username or
                            f"Telegram Bot {created.bot_id}")[:120]
            bot = db.execute(
                """INSERT INTO telbot.bots
                   (tenant_id,telegram_bot_id,username,display_name,
                    owner_telegram_user_id,managed_request_id,status)
                   VALUES (%s,%s,%s,%s,%s,%s,'pending')
                   ON CONFLICT (telegram_bot_id) DO NOTHING RETURNING id""",
                (ticket["tenant_id"], created.bot_id, created.bot_username,
                 display_name, created.owner_user_id, ticket["id"]),
            ).fetchone()
            if bot:
                db.execute(
                    """UPDATE telbot.managed_bot_requests
                       SET status='fulfilled',fulfilled_at=now()
                       WHERE id=%s AND tenant_id=%s AND status='pending'""",
                    (ticket["id"], ticket["tenant_id"]),
                )
                linked = True
    db.execute(
        """UPDATE telbot.manager_inbound_updates
           SET processing_status=%s,processed_at=now() WHERE id=%s""",
        ("processed" if linked else "ignored", inserted["id"]),
    )
    db.commit()
    # No getManagedBotToken, webhook registration or activation until the
    # dedicated secrets and Manager Bot have passed live UAT acceptance.
    return {"acknowledged": True, "duplicate": False}


@app.post("/api/v1/tenants/{tenant_id}/bots/{bot_id}/activate-managed")
async def activate_managed_bot(
    tenant_id: UUID, bot_id: UUID, actor: Principal, db: Db,
) -> dict[str, str]:
    """Owner-authorized UAT-only activation after Telegram registration verification."""
    require_owner(db, tenant_id, actor)
    if os.getenv("TELBOT_ENV") != "uat":
        raise HTTPException(status_code=404, detail="Not found")
    bot = db.execute(
        """SELECT telegram_bot_id,credential_ciphertext,status,webhook_secret_digest
           FROM telbot.bots WHERE id=%s AND tenant_id=%s
             AND owner_telegram_user_id=%s AND managed_request_id IS NOT NULL
           FOR UPDATE""",
        (bot_id, tenant_id, actor.user_id),
    ).fetchone()
    if not bot:
        raise HTTPException(status_code=404, detail="Managed bot not found")
    if bot["status"] == "active":
        return {"status": "active"}
    if bot["status"] != "pending" or bot["credential_ciphertext"] is None:
        raise HTTPException(status_code=409, detail="Managed bot is not ready")
    try:
        from experiments.telegram_bot_builder.vault import TokenVault, CredentialError
    except ModuleNotFoundError:
        from vault import TokenVault, CredentialError
    try:
        token = TokenVault(os.getenv("TELBOT_TOKEN_FERNET_KEY", "")).decrypt(
            bytes(bot["credential_ciphertext"])
        )
    except CredentialError:
        raise HTTPException(status_code=503, detail="Managed credential unavailable") from None
    import httpx
    import re
    from secrets import token_urlsafe
    webhook_secret = token_urlsafe(32)
    expected_url = (
        "https://directpilot-telbot-uat-api.vercel.app/api/v1/webhooks/bots/"
        + str(bot["telegram_bot_id"])
    )
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=4),
                                     follow_redirects=False) as client:
            identity = await client.post("https://api.telegram.org/bot" + token + "/getMe")
            if identity.status_code != 200 or not identity.json().get("ok"):
                raise ValueError("invalid_bot")
            observed = identity.json().get("result") or {}
            if observed.get("id") != bot["telegram_bot_id"]:
                raise ValueError("bot_identity_mismatch")
            current = await client.post("https://api.telegram.org/bot" + token + "/getWebhookInfo")
            if current.status_code != 200 or not current.json().get("ok"):
                raise ValueError("webhook_unavailable")
            existing_url = (current.json().get("result") or {}).get("url", "")
            if existing_url and existing_url != expected_url:
                raise HTTPException(status_code=409, detail="Child bot webhook belongs to another endpoint")
            registered = await client.post(
                "https://api.telegram.org/bot" + token + "/setWebhook",
                json={"url": expected_url, "secret_token": webhook_secret,
                      "allowed_updates": ["message"], "drop_pending_updates": False},
            )
            if registered.status_code != 200 or registered.json().get("ok") is not True:
                raise ValueError("webhook_registration_failed")
            verified = await client.post("https://api.telegram.org/bot" + token + "/getWebhookInfo")
            if verified.status_code != 200 or not verified.json().get("ok") or (
                verified.json().get("result") or {}
            ).get("url") != expected_url:
                raise ValueError("webhook_verification_failed")
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=503, detail="Managed bot activation unavailable") from None
    finally:
        del token
    db.execute(
        """UPDATE telbot.bots SET webhook_secret_digest=%s,status='active',updated_at=now()
           WHERE id=%s AND tenant_id=%s AND owner_telegram_user_id=%s AND status='pending'""",
        (hashlib.sha256(webhook_secret.encode()).digest(), bot_id, tenant_id, actor.user_id),
    )
    db.commit()
    return {"status": "active"}


@app.post("/api/v1/webhooks/bots/{telegram_bot_id}")
async def child_webhook(telegram_bot_id: int, request: Request, db: Db) -> dict[str, bool]:
    if telegram_bot_id <= 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot = db.execute(
        """SELECT id,tenant_id,webhook_secret_digest,credential_ciphertext FROM telbot.bots
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
    if inserted is not None:
        try:
            from .reply_runtime import process_reply
        except ImportError:
            from reply_runtime import process_reply
        update["_bot_id"] = telegram_bot_id
        await process_reply(db, bot, update, inserted["id"])
    return {"acknowledged": True, "duplicate": inserted is None}
