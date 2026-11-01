"""Read-only Google Search Console API adapter for future multi-tenant SEO.

OAuth state, signed-in tenant authorization, encrypted refresh-token storage,
subscription checks, and customer property selection MUST be implemented by
the calling service before these provider methods are exposed over HTTP.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import base64
import hashlib
import re
import secrets
from typing import Any, Literal
from urllib.parse import urlencode, urlsplit, quote

import httpx

GSC_READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_GSC_API = "https://www.googleapis.com/webmasters/v3"
GOOGLE_URL_INSPECTION_API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
ALLOWED_DIMENSIONS = frozenset({"date", "query", "page", "country", "device", "searchAppearance"})
_DOMAIN_PROPERTY = re.compile(r"^sc-domain:(?:[a-z0-9-]+\.)+[a-z0-9-]{2,63}$", re.I)

class GoogleGscError(Exception):
    """Stable sanitized failure. Does not include credentials or Google error bodies."""
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

@dataclass(frozen=True)
class GoogleOAuthTokens:
    access_token: str
    expires_in: int
    refresh_token: str | None
    scope: str
    def __repr__(self) -> str:
        return "GoogleOAuthTokens(<redacted>)"

@dataclass(frozen=True)
class GoogleGscProperty:
    site_url: str
    permission_level: str

def create_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode()
    return verifier, challenge

def create_oauth_state() -> str:
    return secrets.token_urlsafe(32)

def validate_property_identifier(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048 or any(c.isspace() for c in value):
        raise ValueError("invalid_gsc_property")
    if _DOMAIN_PROPERTY.fullmatch(value):
        return value.lower()
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError("invalid_gsc_property")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("invalid_gsc_property")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("invalid_gsc_property") from None
    if port is not None or parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("invalid_gsc_property")
    return value

class GoogleSearchConsoleClient:
    """Google-only requests; never sends caller-supplied URLs to the HTTP client."""
    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str,
                 http_client: httpx.Client | None = None) -> None:
        parsed = urlsplit(redirect_uri)
        localhost = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
        if (not client_id or not client_secret or not redirect_uri
                or (parsed.scheme != "https" and not localhost)
                or not parsed.netloc or parsed.username or parsed.password or parsed.fragment):
            raise GoogleGscError("oauth_configuration_invalid")
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._http = http_client

    def authorization_url(self, *, state: str, code_challenge: str,
                          force_consent: bool = False) -> str:
        if len(state) < 32 or not re.fullmatch(r"[A-Za-z0-9_-]+", state):
            raise ValueError("invalid_oauth_state")
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", code_challenge):
            raise ValueError("invalid_pkce_challenge")
        data = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": GSC_READONLY_SCOPE,
            "access_type": "offline",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if force_consent:
            data["prompt"] = "consent"
        return GOOGLE_AUTH_URL + "?" + urlencode(data)

    def _request(self, method: Literal["GET", "POST"], url: str,
                 *, access_token: str | None = None, data: dict[str, Any] | None = None,
                 payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = "Bearer " + access_token
        # Never log URLs containing OAuth credentials, Google bodies or access tokens.
        try:
            if self._http is None:
                with httpx.Client(timeout=12, follow_redirects=False) as session:
                    response = session.request(method, url, headers=headers, data=data, json=payload)
            else:
                response = self._http.request(method, url, headers=headers, data=data, json=payload)
        except httpx.HTTPError:
            raise GoogleGscError("google_network_unavailable") from None
        codes = {401: "google_authorization_expired", 403: "google_access_denied_or_quota",
                 429: "google_rate_limited"}
        if response.status_code in codes:
            raise GoogleGscError(codes[response.status_code])
        if not response.is_success:
            raise GoogleGscError("google_provider_request_failed")
        try:
            body = response.json()
        except ValueError:
            raise GoogleGscError("google_invalid_response") from None
        if not isinstance(body, dict):
            raise GoogleGscError("google_invalid_response")
        return body

    @staticmethod
    def _tokens(body: dict[str, Any], *, existing_scope: str | None = None) -> GoogleOAuthTokens:
        access_token = body.get("access_token")
        scope = body.get("scope", existing_scope or "")
        expires = body.get("expires_in")
        refresh = body.get("refresh_token")
        if not isinstance(access_token, str) or not access_token:
            raise GoogleGscError("google_token_missing")
        if not isinstance(scope, str):
            raise GoogleGscError("google_invalid_response")
        if GSC_READONLY_SCOPE not in scope.split():
            raise GoogleGscError("google_readonly_scope_not_granted")
        if not isinstance(expires, int) or not 0 < expires <= 86400:
            raise GoogleGscError("google_token_expiry_invalid")
        if refresh is not None and (not isinstance(refresh, str) or not refresh):
            raise GoogleGscError("google_invalid_response")
        return GoogleOAuthTokens(access_token, expires, refresh, scope)

    def exchange_code(self, *, code: str, code_verifier: str) -> GoogleOAuthTokens:
        if not code or len(code) > 4096 or not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", code_verifier):
            raise ValueError("invalid_oauth_exchange")
        data = {"client_id": self._client_id, "client_secret": self._client_secret,
                "redirect_uri": self._redirect_uri, "code": code,
                "code_verifier": code_verifier, "grant_type": "authorization_code"}
        return self._tokens(self._request("POST", GOOGLE_TOKEN_URL, data=data))

    def refresh_access_token(self, *, refresh_token: str, verified_scope: str) -> GoogleOAuthTokens:
        if not refresh_token or len(refresh_token) > 4096:
            raise ValueError("invalid_refresh_token")
        if GSC_READONLY_SCOPE not in verified_scope.split():
            raise ValueError("unverified_gsc_scope")
        data = {"client_id": self._client_id, "client_secret": self._client_secret,
                "refresh_token": refresh_token, "grant_type": "refresh_token"}
        # Google refresh responses may omit scope. It was verified at original consent.
        return self._tokens(self._request("POST", GOOGLE_TOKEN_URL, data=data), existing_scope=verified_scope)

    def list_properties(self, *, access_token: str) -> list[GoogleGscProperty]:
        entries = self._request("GET", GOOGLE_GSC_API + "/sites", access_token=access_token).get("siteEntry", [])
        if not isinstance(entries, list):
            raise GoogleGscError("google_invalid_response")
        result = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            if item.get("permissionLevel") not in {"siteOwner", "siteFullUser", "siteRestrictedUser"}:
                continue
            try:
                identifier = validate_property_identifier(item.get("siteUrl"))
            except (ValueError, TypeError):
                continue
            result.append(GoogleGscProperty(identifier, item["permissionLevel"]))
        return result

    def search_analytics(self, *, access_token: str, property_id: str,
                         start_date: date, end_date: date, dimensions: tuple[str, ...] = ("date",),
                         row_limit: int = 1000) -> dict[str, Any]:
        if end_date < start_date or (end_date - start_date).days > 365:
            raise ValueError("invalid_date_range")
        if not isinstance(row_limit, int) or not 1 <= row_limit <= 25000:
            raise ValueError("invalid_row_limit")
        if not dimensions or any(x not in ALLOWED_DIMENSIONS for x in dimensions) or len(set(dimensions)) != len(dimensions):
            raise ValueError("invalid_dimensions")
        site = validate_property_identifier(property_id)
        url = GOOGLE_GSC_API + "/sites/" + quote(site, safe="") + "/searchAnalytics/query"
        body = {"startDate": start_date.isoformat(), "endDate": end_date.isoformat(),
                "dimensions": list(dimensions), "rowLimit": row_limit}
        return self._request("POST", url, access_token=access_token, payload=body)

    def inspect_url(self, *, access_token: str, property_id: str, inspection_url: str) -> dict[str, Any]:
        site = validate_property_identifier(property_id)
        parsed = urlsplit(inspection_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.fragment
                or any(c.isspace() for c in inspection_url)):
            raise ValueError("invalid_inspection_url")
        if site.startswith("sc-domain:"):
            domain = site.removeprefix("sc-domain:")
            if parsed.hostname != domain and not parsed.hostname.endswith("." + domain):
                raise ValueError("url_not_in_property")
        else:
            prefix = urlsplit(site)
            try:
                inspection_port = parsed.port
            except ValueError:
                raise ValueError("invalid_inspection_url") from None
            if (parsed.scheme != prefix.scheme or parsed.hostname != prefix.hostname
                    or inspection_port != prefix.port):
                raise ValueError("url_not_in_property")
            path_prefix = prefix.path or "/"
            # Site URL-prefix properties include protocol/host and optional
            # subpath. Reject host spoofing and sibling paths.
            if (not parsed.path.startswith(path_prefix)
                    or (not path_prefix.endswith("/")
                        and parsed.path != path_prefix
                        and not parsed.path.startswith(path_prefix + "/"))):
                raise ValueError("url_not_in_property")
        return self._request("POST", GOOGLE_URL_INSPECTION_API, access_token=access_token,
                             payload={"inspectionUrl": inspection_url, "siteUrl": site})
