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

from app.config import Settings, get_settings


router = APIRouter(tags=["instagram"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
SETUP_TEMPLATE_PATH = Path(__file__).resolve().parent / "static" / "instagram_setup.html"

ACCESS_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~+/=-]{20,4096}$")
APP_SECRET_PATTERN = re.compile(r"^[A-Fa-f0-9]{32,128}$")
IG_USER_ID_PATTERN = re.compile(r"^[0-9]{5,30}$")
VERIFY_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~:-]{20,200}$")
INVISIBLE_CHARACTERS = str.maketrans(
    "",
    "",
    "\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e"
    "\u2060\u2066\u2067\u2068\u2069\ufeff",
)

NONCE_TTL_SECONDS = 15 * 60
CSRF_COOKIE_NAME = "instagram_setup_session"
_setup_nonces: dict[str, float] = {}
_nonce_lock = threading.Lock()
_env_lock = threading.Lock()


def require_local_setup(request: Request, settings: Settings) -> None:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")

    client_host = request.client.host if request.client else ""
    try:
        is_loopback = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        is_loopback = False
    if not is_loopback:
        raise HTTPException(status_code=403, detail="Instagram setup is local-only")
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


def normalize_secret(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.translate(INVISIBLE_CHARACTERS).strip().strip("`\"'")


def validate_setup_payload(payload: object) -> tuple[str, str, str, str, bool]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Invalid Meta setup values")

    access_token = normalize_secret(payload.get("access_token"))
    app_secret = normalize_secret(payload.get("app_secret"))
    ig_user_id = normalize_secret(payload.get("ig_user_id"))
    verify_token = normalize_secret(payload.get("verify_token", ""))

    if access_token is None or not ACCESS_TOKEN_PATTERN.fullmatch(access_token):
        raise HTTPException(status_code=422, detail="Invalid Meta access token format")
    if app_secret is None or not APP_SECRET_PATTERN.fullmatch(app_secret):
        raise HTTPException(status_code=422, detail="Invalid Meta app secret format")
    if ig_user_id is None or not IG_USER_ID_PATTERN.fullmatch(ig_user_id):
        raise HTTPException(status_code=422, detail="Invalid Instagram account ID format")

    generated_verify_token = not verify_token
    if generated_verify_token:
        verify_token = secrets.token_urlsafe(32)
    if not VERIFY_TOKEN_PATTERN.fullmatch(verify_token):
        raise HTTPException(status_code=422, detail="Invalid webhook verify token format")

    return access_token, app_secret, ig_user_id, verify_token, generated_verify_token


def save_meta_settings(
    access_token: str,
    app_secret: str,
    ig_user_id: str,
    verify_token: str,
) -> None:
    values = {
        "META_ACCESS_TOKEN": access_token,
        "META_APP_SECRET": app_secret,
        "META_IG_USER_ID": ig_user_id,
        "META_VERIFY_TOKEN": verify_token,
    }
    save_dotenv_settings(values)


def save_dotenv_settings(values: dict[str, str]) -> None:
    with _env_lock:
        content = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
        updated = update_dotenv(content, values)
        temporary_path = ENV_PATH.with_name(f".{ENV_PATH.name}.{secrets.token_hex(8)}.tmp")
        try:
            with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, ENV_PATH)
        finally:
            temporary_path.unlink(missing_ok=True)


def require_valid_setup_submission(request: Request) -> None:
    origin = (request.headers.get("origin") or "").rstrip("/")
    if not origin or not hmac.compare_digest(origin, expected_origin(request)):
        raise HTTPException(status_code=403, detail="Invalid setup origin")
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site and fetch_site != "same-origin":
        raise HTTPException(status_code=403, detail="Invalid setup request context")

    setup_nonce = request.cookies.get(CSRF_COOKIE_NAME) or ""
    if not setup_nonce or not consume_setup_nonce(setup_nonce):
        raise HTTPException(status_code=403, detail="Setup page expired; reload it and try again")


@router.get("/instagram/setup", response_class=HTMLResponse, include_in_schema=False)
def instagram_setup_page(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    require_local_setup(request, settings)
    setup_nonce = create_setup_nonce()
    csp_nonce = secrets.token_urlsafe(24)
    html = SETUP_TEMPLATE_PATH.read_text(encoding="utf-8").replace(
        "__CSP_NONCE__", csp_nonce
    )
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
        secure=request.url.scheme == "https",
        path="/instagram/setup",
    )
    return response


@router.post("/instagram/setup", include_in_schema=False)
async def save_instagram_setup(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, bool | str]:
    require_local_setup(request, settings)
    require_valid_setup_submission(request)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid setup request") from None
    access_token, app_secret, ig_user_id, verify_token, generated = (
        validate_setup_payload(payload)
    )

    try:
        save_meta_settings(access_token, app_secret, ig_user_id, verify_token)
    except OSError:
        raise HTTPException(status_code=500, detail="Could not save local Meta settings") from None

    # Refresh the running process without returning or logging any submitted value.
    settings.meta_access_token = access_token
    settings.meta_app_secret = app_secret
    settings.meta_ig_user_id = ig_user_id
    settings.meta_verify_token = verify_token
    response.delete_cookie(CSRF_COOKIE_NAME, path="/instagram/setup")
    return {
        "ok": True,
        "message": "Meta settings were saved locally",
        "verify_token_generated": generated,
        "network_verification_performed": False,
    }


@router.post("/instagram/setup/verify-token", include_in_schema=False)
async def rotate_instagram_verify_token(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, bool | str]:
    require_local_setup(request, settings)
    require_valid_setup_submission(request)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid setup request") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Invalid setup values")

    verify_token = normalize_secret(payload.get("verify_token"))
    if verify_token is None or not VERIFY_TOKEN_PATTERN.fullmatch(verify_token):
        raise HTTPException(status_code=422, detail="Invalid webhook verify token format")

    try:
        save_dotenv_settings({"META_VERIFY_TOKEN": verify_token})
    except OSError:
        raise HTTPException(status_code=500, detail="Could not save local Meta settings") from None

    settings.meta_verify_token = verify_token
    response.delete_cookie(CSRF_COOKIE_NAME, path="/instagram/setup")
    return {
        "ok": True,
        "message": "Webhook verify token was updated locally",
    }
