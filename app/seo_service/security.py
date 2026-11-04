"""Dedicated encryption and OAuth state helpers for Google Search Console."""

from __future__ import annotations

import base64
import hashlib
import secrets

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings


class SeoCredentialConfigurationError(ValueError):
    pass


class SeoTokenCipher:
    def __init__(self, key: str) -> None:
        try:
            decoded = base64.urlsafe_b64decode(key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise SeoCredentialConfigurationError("SEO token encryption is not configured") from exc
        if len(decoded) != 32 or len(key) != 44:
            raise SeoCredentialConfigurationError("SEO token encryption is not configured")
        self._fernet = Fernet(key.encode("ascii"))

    @classmethod
    def from_settings(cls, settings: Settings) -> "SeoTokenCipher":
        return cls(settings.seo_google_token_encryption_key.get_secret_value().strip())

    def encrypt(self, value: str) -> str:
        if not value or len(value) > 8192:
            raise ValueError("invalid Google credential")
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeEncodeError, ValueError) as exc:
            raise SeoCredentialConfigurationError("Google credential could not be decrypted") from exc


def new_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def state_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
