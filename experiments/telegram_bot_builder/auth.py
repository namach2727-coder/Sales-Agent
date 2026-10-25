"""Strict Telegram Mini App authentication; trust only server-validated initData.

Official protocol: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations
import base64
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



def safe_initdata_shape(raw_init_data: str) -> str:
    """UAT-only coarse shape. Never return field values, hashes, IDs or timestamps."""
    if not raw_init_data or len(raw_init_data) > 8192:
        return "absent_or_oversize"
    try:
        items = parse_qsl(raw_init_data, strict_parsing=True, keep_blank_values=True,
                          max_num_fields=64)
    except ValueError:
        return "invalid_encoding"
    keys = [key for key, _ in items]
    if len(keys) != len(set(keys)):
        return "duplicate_fields"
    present = set(keys)
    # Explicitly allowlist indicators; no attacker-controlled strings in the result.
    return "q%d_c%d_s%d_u%d_a%d" % tuple(
        int(key in present) for key in
        ("query_id", "chat_instance", "signature", "user", "auth_date")
    )



_TELEGRAM_ED25519_PROD = bytes.fromhex(
    "e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d"
)

def diagnose_ed25519(raw: str, token: str) -> str:
    """Diagnostics only; never grants access and never exposes values."""
    if not raw or len(raw) > 8192:
        return "unavailable"
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        bot_id = token.split(":", 1)[0]
        if not bot_id.isascii() or not bot_id.isdecimal():
            return "unavailable"
        pairs = parse_qsl(raw, strict_parsing=True, keep_blank_values=True, max_num_fields=64)
        fields = dict(pairs)
        if len(fields) != len(pairs):
            return "unavailable"
        encoded = fields.get("signature", "")
        signature = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        if len(signature) != 64:
            return "unavailable"
        payload = str(int(bot_id)) + ":WebAppData\n" + "\n".join(
            f"{k}={v}" for k, v in sorted(fields.items()) if k not in ("hash", "signature")
        )
        Ed25519PublicKey.from_public_bytes(_TELEGRAM_ED25519_PROD).verify(
            signature, payload.encode("utf-8")
        )
        return "valid"
    except InvalidSignature:
        return "invalid"
    except (ValueError, TypeError, UnicodeError):
        return "unavailable"


def diagnose_hmac_mismatch(raw: str, token: str) -> str:
    """UAT-only classifications; never used to authenticate a caller."""
    if not token or not raw or len(raw) > 8192:
        return "unavailable"
    if token != token.strip():
        return "token_whitespace"
    try:
        pairs = parse_qsl(raw, strict_parsing=True, keep_blank_values=True, max_num_fields=64)
        fields = dict(pairs)
        if len(fields) != len(pairs):
            return "unavailable"
        received = fields.get("hash", "")
        if len(received) != 64 or any(c not in "0123456789abcdefABCDEF" for c in received):
            return "unavailable"
        secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        # Classify a common producer/consumer discrepancy without accepting it.
        check_with_signature = chr(10).join(
            f"{key}={value}" for key, value in sorted(fields.items()) if key != "hash"
        )
        alternative = hmac.new(secret, check_with_signature.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(received.lower(), alternative):
            return "signature_field_included"
        return "key_or_payload_mismatch"
    except (ValueError, TypeError, UnicodeError):
        return "unavailable"


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
