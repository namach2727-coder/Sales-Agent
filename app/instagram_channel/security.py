"""Credential encryption and Meta webhook authenticity checks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from typing import Protocol

from app.config import Settings
from app.instagram_channel.exceptions import (
    InstagramCredentialConfigurationError,
    InstagramChannelValidationError,
    InstagramWebhookSecurityError,
)


META_SIGNATURE_PATTERN = re.compile(r"^sha256=([0-9a-fA-F]{64})$")


class TokenCipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str: ...


def valid_fernet_key(value: str) -> bool:
    try:
        decoded = base64.b64decode(
            value.encode("ascii"), altchars=b"-_", validate=True
        )
    except (UnicodeEncodeError, ValueError):
        return False
    return len(decoded) == 32 and len(value) == 44


class FernetTokenCipher:
    """Small replaceable authenticated-encryption boundary."""

    def __init__(self, key: str) -> None:
        if not valid_fernet_key(key):
            raise InstagramCredentialConfigurationError(
                "Instagram token encryption is not configured"
            )
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:  # pragma: no cover - deployment dependency guard
            raise InstagramCredentialConfigurationError(
                "Instagram token encryption dependency is unavailable"
            ) from exc
        self._fernet = Fernet(key.encode("ascii"))

    @classmethod
    def from_settings(cls, settings: Settings) -> "FernetTokenCipher":
        key = settings.instagram_token_encryption_key.get_secret_value().strip()
        return cls(key)

    def encrypt(self, plaintext: str) -> str:
        value = plaintext.strip()
        if not value or len(value) > 8192:
            raise InstagramChannelValidationError("Invalid Instagram credential")
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except Exception as exc:
            raise InstagramCredentialConfigurationError(
                "Instagram credential could not be decrypted"
            ) from exc


def verify_subscription(
    *,
    mode: str | None,
    challenge: str | None,
    supplied_token: str | None,
    configured_token: str,
) -> str:
    expected = configured_token.strip()
    if not expected:
        raise InstagramWebhookSecurityError(
            "Webhook verification is not configured"
        )
    if mode != "subscribe" or not challenge or not supplied_token:
        raise InstagramWebhookSecurityError("Invalid webhook verification request")
    if not hmac.compare_digest(supplied_token, expected):
        raise InstagramWebhookSecurityError("Invalid webhook verification request")
    return challenge


def verify_meta_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str,
) -> None:
    secret = app_secret.strip()
    if not secret:
        raise InstagramWebhookSecurityError("Webhook signature is not configured")
    match = META_SIGNATURE_PATTERN.fullmatch(signature_header or "")
    if match is None:
        raise InstagramWebhookSecurityError("Invalid webhook signature")
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(match.group(1).lower(), expected):
        raise InstagramWebhookSecurityError("Invalid webhook signature")
