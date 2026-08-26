"""Provider boundary for official Instagram Login OAuth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.config import Settings


INSTAGRAM_LOGIN_SCOPES = (
    "instagram_business_basic",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments",
)


class InstagramOAuthError(Exception):
    """Sanitized provider failure; response bodies are deliberately discarded."""


@dataclass(frozen=True, slots=True)
class InstagramOAuthAccount:
    account_id: str
    username: str | None
    access_token: str
    token_type: str
    expires_in: int | None
    scopes: tuple[str, ...]


class InstagramOAuthProvider(Protocol):
    def authorization_url(self, state: str) -> str: ...

    def exchange(self, code: str) -> InstagramOAuthAccount: ...


class MetaInstagramOAuthClient:
    """Small synchronous adapter for Instagram API with Instagram Login."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _configuration(self) -> tuple[str, str, str]:
        app_id = self.settings.meta_app_id.strip()
        app_secret = self.settings.meta_app_secret.strip()
        redirect_uri = self.settings.meta_oauth_redirect_uri.strip()
        if not app_id or not app_secret or not redirect_uri:
            raise InstagramOAuthError("Instagram onboarding is not configured")
        return app_id, app_secret, redirect_uri

    def authorization_url(self, state: str) -> str:
        app_id, _secret, redirect_uri = self._configuration()
        query = urlencode(
            {
                "client_id": app_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": ",".join(INSTAGRAM_LOGIN_SCOPES),
                "state": state,
            }
        )
        return f"{self.settings.meta_oauth_authorize_url.rstrip('/')}?{query}"

    def exchange(self, code: str) -> InstagramOAuthAccount:
        app_id, app_secret, redirect_uri = self._configuration()
        normalized_code = code.strip()
        if not normalized_code or len(normalized_code) > 4096:
            raise InstagramOAuthError("Invalid authorization response")
        timeout = httpx.Timeout(self.settings.meta_oauth_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                short_response = client.post(
                    self.settings.meta_oauth_token_url,
                    data={
                        "client_id": app_id,
                        "client_secret": app_secret,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                        "code": normalized_code,
                    },
                )
                short_response.raise_for_status()
                short_payload = short_response.json()
                short_token = str(short_payload.get("access_token") or "").strip()
                if not short_token:
                    raise InstagramOAuthError("Meta returned no access token")

                long_response = client.get(
                    f"{self.settings.meta_graph_base_url}/access_token",
                    params={
                        "grant_type": "ig_exchange_token",
                        "client_secret": app_secret,
                        "access_token": short_token,
                    },
                )
                long_response.raise_for_status()
                long_payload = long_response.json()
                access_token = str(long_payload.get("access_token") or "").strip()
                if not access_token:
                    raise InstagramOAuthError("Meta returned no long-lived token")

                profile_response = client.get(
                    f"{self.settings.meta_graph_base_url}/me",
                    params={
                        "fields": "id,user_id,username,account_type",
                        "access_token": access_token,
                    },
                )
                profile_response.raise_for_status()
                profile = profile_response.json()
        except InstagramOAuthError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise InstagramOAuthError("Instagram authorization failed") from exc

        account_id = str(profile.get("user_id") or profile.get("id") or "").strip()
        if not account_id:
            raise InstagramOAuthError("Meta returned no Instagram account")
        expires_value = long_payload.get("expires_in")
        expires_in = int(expires_value) if isinstance(expires_value, int) else None
        username_value = profile.get("username")
        username = str(username_value).strip() if username_value else None
        return InstagramOAuthAccount(
            account_id=account_id,
            username=username,
            access_token=access_token,
            token_type=str(long_payload.get("token_type") or "bearer"),
            expires_in=expires_in,
            scopes=INSTAGRAM_LOGIN_SCOPES,
        )
