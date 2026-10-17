"""Encrypt Telegram child-bot tokens using a dedicated TelBot-only Fernet key.

Never share this key with DirectPilot Instagram, client browsers, DB rows, logs or Git.
"""
from __future__ import annotations


class CredentialError(ValueError):
    pass


class TokenVault:
    def __init__(self, key: str) -> None:
        if not key:
            raise CredentialError("TelBot encryption key is not configured")
        try:
            from cryptography.fernet import Fernet
            self._vault = Fernet(key.encode("ascii"))
        except (ImportError, ValueError, TypeError) as exc:
            raise CredentialError("Invalid TelBot encryption configuration") from exc

    def encrypt(self, token: str) -> bytes:
        if not token or len(token) > 256 or "\n" in token:
            raise CredentialError("Invalid Telegram credential")
        return self._vault.encrypt(token.encode("utf-8"))

    def decrypt(self, encrypted: bytes) -> str:
        if not encrypted:
            raise CredentialError("No credential stored")
        try:
            from cryptography.fernet import InvalidToken
            return self._vault.decrypt(encrypted).decode("utf-8")
        except (InvalidToken, UnicodeError) as exc:
            raise CredentialError("Cannot decrypt Telegram credential") from exc
