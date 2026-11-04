"""Google OAuth and Search Console provider adapter."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.config import Settings

logger = logging.getLogger("directpilot.seo.google")
GOOGLE_SCOPES = (
    "openid",
    "email",
    "https://www.googleapis.com/auth/webmasters.readonly",
)


class GoogleSeoProviderError(RuntimeError):
    def __init__(self, code: str = "google_provider_error") -> None:
        super().__init__("Google authorization or Search Console request failed")
        self.code = code


@dataclass(frozen=True, slots=True)
class GoogleOAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_in: int
    scopes: tuple[str, ...]
    subject: str
    email: str | None


@dataclass(frozen=True, slots=True)
class GoogleSite:
    site_url: str
    permission_level: str


class GoogleSeoProvider(Protocol):
    def authorization_url(self, state: str) -> str: ...
    def exchange_code(self, code: str) -> GoogleOAuthTokens: ...
    def list_sites(self, access_token: str) -> list[GoogleSite]: ...
    def refresh_access_token(self, refresh_token: str) -> str: ...
    def revoke(self, token: str) -> None: ...


class GoogleSearchConsoleClient:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    REVOKE_URL = "https://oauth2.googleapis.com/revoke"
    SITES_URL = "https://www.googleapis.com/webmasters/v3/sites"
    USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _config(self) -> tuple[str, str, str]:
        client_id = self.settings.google_oauth_client_id.strip()
        client_secret = self.settings.google_oauth_client_secret.get_secret_value().strip()
        redirect_uri = self.settings.google_oauth_redirect_uri.strip()
        if not client_id or not client_secret or not redirect_uri:
            raise GoogleSeoProviderError("google_oauth_not_configured")
        return client_id, client_secret, redirect_uri

    def authorization_url(self, state: str) -> str:
        client_id, _secret, redirect_uri = self._config()
        return self.AUTH_URL + "?" + urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        })

    def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            with httpx.Client(timeout=self.settings.seo_google_oauth_timeout_seconds) as client:
                response = client.request(method, url, **kwargs)
            if response.status_code < 200 or response.status_code >= 300:
                raise GoogleSeoProviderError("google_provider_rejected")
            payload = response.json()
            if not isinstance(payload, dict):
                raise GoogleSeoProviderError("google_invalid_response")
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise GoogleSeoProviderError("google_provider_unavailable") from exc

    def exchange_code(self, code: str) -> GoogleOAuthTokens:
        client_id, client_secret, redirect_uri = self._config()
        if not code or len(code) > 4096:
            raise GoogleSeoProviderError("google_invalid_authorization_response")
        payload = self._request("POST", self.TOKEN_URL, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise GoogleSeoProviderError("google_invalid_token_response")
        refresh_token = payload.get("refresh_token")
        scope_value = payload.get("scope", "")
        scopes = tuple(scope_value.split()) if isinstance(scope_value, str) else ()
        if "https://www.googleapis.com/auth/webmasters.readonly" not in scopes:
            raise GoogleSeoProviderError("google_required_scope_missing")
        identity = self._request("GET", self.USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}",
        })
        subject = identity.get("sub")
        email = identity.get("email")
        if not isinstance(subject, str) or not subject:
            raise GoogleSeoProviderError("google_identity_unavailable")
        return GoogleOAuthTokens(
            access_token=access_token,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            expires_in=int(payload.get("expires_in", 3600)),
            scopes=scopes,
            subject=subject,
            email=email if isinstance(email, str) else None,
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        client_id, client_secret, _redirect_uri = self._config()
        payload = self._request("POST", self.TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise GoogleSeoProviderError("google_refresh_failed")
        return access_token

    def list_sites(self, access_token: str) -> list[GoogleSite]:
        payload = self._request("GET", self.SITES_URL, headers={
            "Authorization": f"Bearer {access_token}",
        })
        entries = payload.get("siteEntry", [])
        if not isinstance(entries, list):
            raise GoogleSeoProviderError("google_invalid_sites_response")
        sites: list[GoogleSite] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            site_url = item.get("siteUrl")
            permission = item.get("permissionLevel")
            if isinstance(site_url, str) and isinstance(permission, str):
                sites.append(GoogleSite(site_url, permission))
        return sites

    def revoke(self, token: str) -> None:
        self._request("POST", self.REVOKE_URL, data={"token": token})
