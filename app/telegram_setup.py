import hmac
import ipaddress
import os
import re
import secrets
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.telegram import TelegramAPIError, TelegramClient


router = APIRouter(tags=["telegram"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"
SETUP_TEMPLATE_PATH = Path(__file__).resolve().parent / "static" / "telegram_setup.html"

TOKEN_PATTERN = re.compile(r"^[0-9]{5,20}:[A-Za-z0-9._~-]{10,200}$")
TOKEN_SEARCH_PATTERN = re.compile(
    r"(?:https://api\.telegram\.org/bot|\bbot)?"
    r"([0-9]{5,20}:[A-Za-z0-9._~-]{10,200})",
    flags=re.IGNORECASE,
)
INVISIBLE_CHARACTERS = str.maketrans(
    "",
    "",
    "\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e"
    "\u2060\u2066\u2067\u2068\u2069\ufeff",
)
DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)
NONCE_TTL_SECONDS = 15 * 60
_setup_nonces: dict[str, float] = {}
_nonce_lock = threading.Lock()
_env_lock = threading.Lock()
CSRF_COOKIE_NAME = "telegram_setup_nonce"


class TelegramSetupRequest(BaseModel):
    token: str = Field(min_length=20, max_length=1000)
    setup_nonce: str = Field(min_length=20, max_length=200)


def require_local_setup(request: Request, settings: Settings) -> None:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    client_host = request.client.host if request.client else ""
    try:
        is_loopback = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        is_loopback = False
    if not is_loopback:
        raise HTTPException(status_code=403, detail="Telegram setup is local-only")
    if request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise HTTPException(status_code=403, detail="Invalid local setup host")


def expected_origin(request: Request) -> str:
    host = request.headers.get("host", "")
    return f"{request.url.scheme}://{host}".rstrip("/")


def create_setup_nonce() -> str:
    now = time.monotonic()
    nonce = secrets.token_urlsafe(32)
    with _nonce_lock:
        expired = [key for key, expiry in _setup_nonces.items() if expiry <= now]
        for key in expired:
            _setup_nonces.pop(key, None)
        _setup_nonces[nonce] = now + NONCE_TTL_SECONDS
    return nonce


def consume_setup_nonce(supplied: str) -> bool:
    now = time.monotonic()
    with _nonce_lock:
        expiry = _setup_nonces.pop(supplied, None)
    return expiry is not None and expiry > now


def update_dotenv(content: str, values: dict[str, str]) -> str:
    written: set[str] = set()
    output: list[str] = []
    for line in content.splitlines():
        key, separator, _ = line.partition("=")
        if separator and key in values:
            if key not in written:
                output.append(f"{key}={values[key]}")
                written.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in written:
            output.append(f"{key}={value}")
    return "\n".join(output).rstrip() + "\n"


def normalize_bot_token(value: str) -> str | None:
    cleaned = value.translate(INVISIBLE_CHARACTERS).translate(DIGIT_TRANSLATION).strip()
    cleaned = cleaned.strip("`\"'")
    if TOKEN_PATTERN.fullmatch(cleaned):
        return cleaned
    matches = TOKEN_SEARCH_PATTERN.findall(cleaned)
    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) == 1:
        return unique_matches[0]
    return None


def save_telegram_settings(token: str, webhook_secret: str) -> None:
    with _env_lock:
        if ENV_PATH.exists():
            content = ENV_PATH.read_text(encoding="utf-8")
        elif ENV_EXAMPLE_PATH.exists():
            content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
        else:
            content = ""

        updated = update_dotenv(
            content,
            {
                "TELEGRAM_BOT_TOKEN": token,
                "TELEGRAM_WEBHOOK_SECRET": webhook_secret,
                "TELEGRAM_SEND_ENABLED": "true",
                "TELEGRAM_POLLING_ENABLED": "true",
            },
        )
        temporary_path = ENV_PATH.with_name(f".{ENV_PATH.name}.{secrets.token_hex(8)}.tmp")
        try:
            with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, ENV_PATH)
        finally:
            temporary_path.unlink(missing_ok=True)


@router.get("/telegram/setup", response_class=HTMLResponse, include_in_schema=False)
def telegram_setup_page(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    require_local_setup(request, settings)
    setup_nonce = create_setup_nonce()
    csp_nonce = secrets.token_urlsafe(24)
    html = SETUP_TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("__SETUP_NONCE__", setup_nonce).replace("__CSP_NONCE__", csp_nonce)
    response = HTMLResponse(html)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        f"style-src 'nonce-{csp_nonce}'; script-src 'nonce-{csp_nonce}'; "
        "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        setup_nonce,
        max_age=NONCE_TTL_SECONDS,
        httponly=True,
        samesite="strict",
        path="/telegram/setup",
    )
    return response


@router.post("/telegram/setup", include_in_schema=False)
async def save_telegram_setup(
    payload: TelegramSetupRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, bool | str]:
    require_local_setup(request, settings)
    origin = (request.headers.get("origin") or "").rstrip("/")
    if not origin or not hmac.compare_digest(origin, expected_origin(request)):
        raise HTTPException(status_code=403, detail="Invalid setup origin")
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site and fetch_site != "same-origin":
        raise HTTPException(status_code=403, detail="Invalid setup request context")
    cookie_nonce = request.cookies.get(CSRF_COOKIE_NAME) or ""
    if not cookie_nonce or not hmac.compare_digest(cookie_nonce, payload.setup_nonce):
        raise HTTPException(status_code=403, detail="Invalid setup confirmation")
    if not consume_setup_nonce(payload.setup_nonce):
        raise HTTPException(status_code=403, detail="Setup page expired; reload it and try again")

    token = normalize_bot_token(payload.token)
    if token is None:
        raise HTTPException(status_code=422, detail="Invalid Telegram bot token format")

    candidate_settings = settings.model_copy(deep=True)
    candidate_settings.telegram_bot_token = token
    bot: dict = {}
    token_verified = False
    try:
        bot = await TelegramClient(candidate_settings).get_me()
        token_verified = True
    except TelegramAPIError as exc:
        # A network/sandbox failure is not evidence that the token is invalid.
        # Explicit Bot API rejections still stop the save.
        if str(exc).startswith("Telegram API error:"):
            raise HTTPException(
                status_code=422,
                detail="Telegram rejected this token. Generate a new token in BotFather.",
            ) from None

    webhook_secret = secrets.token_urlsafe(32)
    try:
        save_telegram_settings(token, webhook_secret)
    except OSError:
        raise HTTPException(status_code=500, detail="Could not save local Telegram settings") from None

    # Refresh the already-running local app without returning or logging either secret.
    settings.telegram_bot_token = token
    settings.telegram_webhook_secret = webhook_secret
    settings.telegram_send_enabled = True
    settings.telegram_polling_enabled = True
    response.delete_cookie(CSRF_COOKIE_NAME, path="/telegram/setup")
    return {
        "ok": True,
        "message": "Telegram settings were saved locally",
        "ready_to_start": True,
        "bot_username": str(bot.get("username") or ""),
        "token_verified": token_verified,
    }
