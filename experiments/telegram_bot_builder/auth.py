"""Strict Telegram Mini App authentication; trust only server-validated initData.

Official protocol: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class TelegramAuthError(ValueError):
    """Fixed public-safe categories only; never include input or secrets."""


@dataclass(frozen=True)
class TelegramPrincipal:
    user_id: int
    auth_date: int


def verify_init_data(raw_init_data: str, bot_token: str, *, now: int | None = None,
                     max_age_seconds: int = 3600) -> TelegramPrincipal:
    if not bot_token or not raw_init_data or len(raw_init_data) > 8192:
        raise TelegramAuthError("missing_init_data")
    try:
        items = parse_qsl(raw_init_data, strict_parsing=True, keep_blank_values=True,
                          max_num_fields=64)
    except ValueError as exc:
        raise TelegramAuthError("malformed_init_data") from exc
    keys = [key for key, _ in items]
    if len(keys) != len(set(keys)):
        raise TelegramAuthError("malformed_init_data")
    fields = dict(items)
    received_hash = fields.get("hash", "")
    if len(received_hash) != 64 or any(c not in "0123456789abcdefABCDEF" for c in received_hash):
        raise TelegramAuthError("malformed_init_data")
    # Telegram hash verification uses fields other than hash. The optional 'signature'
    # is used for third-party Ed25519 verification, not bot-token HMAC.
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()) if k not in {"hash", "signature"})
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash.lower(), expected):
        raise TelegramAuthError("invalid_signature")
    try:
        auth_date = int(fields["auth_date"])
        user = json.loads(fields["user"])
        user_id = user["id"]
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise TelegramAuthError("malformed_account") from exc
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise TelegramAuthError("malformed_account")
    timestamp = int(time.time() if now is None else now)
    if auth_date > timestamp + 30 or timestamp - auth_date > max_age_seconds or auth_date <= 0:
        raise TelegramAuthError("expired_auth_date")
    return TelegramPrincipal(user_id=user_id, auth_date=auth_date)
