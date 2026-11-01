"""Authenticated encryption bound to the tenant, store, user and secret purpose."""
import hashlib
import json
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings


class SeoError(Exception):
    def __init__(self, code: str, status: int = 400):
        self.code, self.status = code, status
        super().__init__(code)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def frontend_origin(settings: Settings, *, require_callback: bool = True) -> str:
    value = settings.seo_frontend_origin.rstrip("/")
    parsed = urlsplit(value)
    local = settings.app_env in {"development", "test"} and parsed.hostname in {"localhost", "127.0.0.1", "testserver"}
    if (not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password
            or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))):
        raise SeoError("seo_configuration_required", 503)
    if not require_callback:
        return value
    # The session cookie must survive Google's top-level redirect. Callback is
    # same-origin through the existing /api proxy, never a browser backend URL.
    callback = urlsplit(settings.seo_google_redirect_uri)
    if (callback.scheme != parsed.scheme or callback.netloc != parsed.netloc
            or callback.path != "/api/v1/seo/google/callback" or callback.query or callback.fragment):
        raise SeoError("seo_configuration_required", 503)
    if settings.session_cookie_samesite != "lax":
        raise SeoError("seo_configuration_required", 503)
    return value


class SeoCipher:
    def __init__(self, settings: Settings):
        try:
            self._cipher = Fernet(settings.seo_token_encryption_key.get_secret_value().encode("ascii"))
        except (ValueError, UnicodeError):
            raise SeoError("seo_configuration_required", 503) from None
        self.version = settings.seo_token_key_version
        if not self.version or len(self.version) > 30:
            raise SeoError("seo_configuration_required", 503)

    def encrypt(self, value: str, *, tenant: int, store: int, user: int, purpose: str) -> str:
        payload = json.dumps([self.version, tenant, store, user, purpose, value], separators=(",", ":"))
        return self._cipher.encrypt(payload.encode()).decode("ascii")

    def decrypt(self, value: str, *, tenant: int, store: int, user: int, purpose: str) -> str:
        try:
            payload = json.loads(self._cipher.decrypt(value.encode("ascii")))
            if not isinstance(payload, list) or len(payload) != 6 or payload[:5] != [self.version, tenant, store, user, purpose]:
                raise ValueError()
            if not isinstance(payload[5], str) or not payload[5]:
                raise ValueError()
            return payload[5]
        except (InvalidToken, ValueError, TypeError, UnicodeError):
            raise SeoError("seo_credential_unavailable", 503) from None
