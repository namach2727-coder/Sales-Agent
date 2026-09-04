"""Provider boundary for official Instagram Login OAuth."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from time import perf_counter
from typing import Callable, Protocol
from urllib.parse import urlencode, urlsplit

import httpx

from app.config import Settings


logger = logging.getLogger("sales_assistant.instagram_oauth")
_SENSITIVE_TEXT = re.compile(
    r"(?i)\b(?:access[_ -]?token|client[_ -]?secret|authorization(?:[_ -]?code)?|code)\b"
)
_SENSITIVE_VALUE = re.compile(
    r"(?i)\b(?:access[_ -]?token|client[_ -]?secret|authorization(?:[_ -]?code)?|code)\b"
    r"(?:\s*[:=]\s*|\s+)(?:bearer\s+)?\S+"
)


INSTAGRAM_LOGIN_SCOPES = (
    "instagram_business_basic",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments",
)


class InstagramOAuthError(Exception):
    """Sanitized provider failure with a stable, non-sensitive error code."""

    def __init__(self, message: str, *, code: str = "instagram_provider_error") -> None:
        super().__init__(message)
        self.code = code


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
            logger.warning(
                "instagram_oauth stage=configuration meta_app_id_configured=%s "
                "meta_app_secret_configured=%s redirect_uri_configured=%s "
                "redirect_uri=%s exception_class=%s",
                bool(app_id),
                bool(app_secret),
                bool(redirect_uri),
                _safe_message(redirect_uri) if redirect_uri else "<missing>",
                "InstagramOAuthError",
                extra={"event_code": "instagram.oauth.configuration_failed"},
            )
            raise InstagramOAuthError(
                "Instagram onboarding is not configured",
                code="oauth_configuration_error",
            )
        logger.info(
            "instagram_oauth stage=configuration meta_app_id_configured=true "
            "meta_app_secret_configured=true redirect_uri_configured=true "
            "redirect_uri=%s exception_class=-",
            _safe_message(redirect_uri),
            extra={"event_code": "instagram.oauth.configuration"},
        )
        return app_id, app_secret, redirect_uri

    def _request_stage(
        self,
        *,
        stage: str,
        method: str,
        url: str,
        request: Callable[[], httpx.Response],
        log_success: bool = True,
        api_version: str | None = None,
    ) -> httpx.Response:
        started = perf_counter()
        hostname = urlsplit(url).hostname or "unknown"
        try:
            response = request()
        except httpx.HTTPError as exc:
            _log_stage(
                stage=stage,
                hostname=hostname,
                method=method,
                status=None,
                error_type=None,
                error_code=None,
                message=None,
                exception_class=type(exc).__name__,
                elapsed_ms=_elapsed_ms(started),
                api_version=api_version,
            )
            raise InstagramOAuthError(
                "Instagram provider network failure",
                code="instagram_provider_network_error",
            ) from exc

        if not 200 <= response.status_code < 300:
            error_type, error_code, message = _meta_error_details(response)
            _log_stage(
                stage=stage,
                hostname=hostname,
                method=method,
                status=response.status_code,
                error_type=error_type,
                error_code=error_code,
                message=message,
                exception_class="HTTPStatusError",
                elapsed_ms=_elapsed_ms(started),
                api_version=api_version,
            )
            raise InstagramOAuthError(
                "Instagram provider rejected the request",
                code=_classify_provider_error(stage, error_type, error_code, message),
            )

        if log_success:
            _log_stage(
                stage=stage,
                hostname=hostname,
                method=method,
                status=response.status_code,
                error_type=None,
                error_code=None,
                message=None,
                exception_class=None,
                elapsed_ms=_elapsed_ms(started),
                api_version=api_version,
            )
        return response

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
            raise InstagramOAuthError(
                "Invalid authorization response",
                code="oauth_provider_rejected",
            )
        timeout = httpx.Timeout(self.settings.meta_oauth_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                short_response = self._request_stage(
                    stage="oauth_token_exchange",
                    method="POST",
                    url=self.settings.meta_oauth_token_url,
                    request=lambda: client.post(
                        self.settings.meta_oauth_token_url,
                        data={
                            "client_id": app_id,
                            "client_secret": app_secret,
                            "grant_type": "authorization_code",
                            "redirect_uri": redirect_uri,
                            "code": normalized_code,
                        },
                    ),
                )
                try:
                    short_payload = short_response.json()
                except (ValueError, TypeError) as exc:
                    _log_stage(
                        stage="oauth_token_exchange",
                        hostname=urlsplit(self.settings.meta_oauth_token_url).hostname
                        or "unknown",
                        method="POST",
                        status=short_response.status_code,
                        error_type=None,
                        error_code=None,
                        message=None,
                        exception_class=type(exc).__name__,
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid token response",
                        code="oauth_token_exchange_failed",
                    ) from exc
                if not isinstance(short_payload, dict):
                    _log_stage(
                        stage="oauth_token_exchange",
                        hostname=urlsplit(self.settings.meta_oauth_token_url).hostname
                        or "unknown",
                        method="POST",
                        status=short_response.status_code,
                        error_type=None,
                        error_code=None,
                        message="Meta returned a non-object token response",
                        exception_class="TypeError",
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid token response",
                        code="oauth_token_exchange_failed",
                    )
                _log_short_token_metadata(short_payload, short_response.status_code)
                short_user_id = str(short_payload.get("user_id") or "").strip()
                _log_short_token_user_id_presence(bool(short_user_id))
                short_token = str(short_payload.get("access_token") or "").strip()
                if not short_token:
                    _log_stage(
                        stage="oauth_token_exchange",
                        hostname=urlsplit(self.settings.meta_oauth_token_url).hostname
                        or "unknown",
                        method="POST",
                        status=short_response.status_code,
                        error_type=None,
                        error_code=None,
                        message="Meta returned no access token",
                        exception_class="InstagramOAuthError",
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned no access token",
                        code="oauth_token_exchange_failed",
                    )

                _log_short_token_permissions(short_payload)
                short_profile_url = f"{self.settings.meta_graph_base_url}/me"
                _probe_short_token_profile(
                    self,
                    client,
                    short_token=short_token,
                    url=short_profile_url,
                    api_version=None,
                    stage="short_token_profile_probe_unversioned",
                )
                graph_api_version = self.settings.meta_api_version.strip().strip("/")
                if graph_api_version:
                    versioned_profile_url = (
                        f"{self.settings.meta_graph_base_url}/{graph_api_version}/me"
                    )
                    _probe_short_token_profile(
                        self,
                        client,
                        short_token=short_token,
                        url=versioned_profile_url,
                        api_version=graph_api_version,
                        stage="short_token_profile_probe_versioned",
                    )
                if short_user_id:
                    explicit_profile_url = (
                        f"{self.settings.meta_graph_base_url}/{short_user_id}"
                    )
                    _probe_short_token_profile(
                        self,
                        client,
                        short_token=short_token,
                        url=explicit_profile_url,
                        api_version=None,
                        stage="short_token_explicit_user_probe_unversioned",
                    )
                    if graph_api_version:
                        versioned_explicit_profile_url = (
                            f"{self.settings.meta_graph_base_url}/{graph_api_version}/"
                            f"{short_user_id}"
                        )
                        _probe_short_token_profile(
                            self,
                            client,
                            short_token=short_token,
                            url=versioned_explicit_profile_url,
                            api_version=graph_api_version,
                            stage="short_token_explicit_user_probe_versioned",
                        )

                long_url = f"{self.settings.meta_graph_base_url}/access_token"
                long_response = self._request_stage(
                    stage="long_lived_token_exchange",
                    method="POST",
                    url=long_url,
                    request=lambda: client.post(
                        long_url,
                        data={
                            "grant_type": "ig_exchange_token",
                            "client_secret": app_secret,
                            "access_token": short_token,
                        },
                    ),
                )
                try:
                    long_payload = long_response.json()
                except (ValueError, TypeError) as exc:
                    _log_stage(
                        stage="long_lived_token_exchange",
                        hostname=urlsplit(long_url).hostname or "unknown",
                        method="POST",
                        status=long_response.status_code,
                        error_type=None,
                        error_code=None,
                        message=None,
                        exception_class=type(exc).__name__,
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid long-lived token response",
                        code="oauth_token_exchange_failed",
                    ) from exc
                if not isinstance(long_payload, dict):
                    _log_stage(
                        stage="long_lived_token_exchange",
                        hostname=urlsplit(long_url).hostname or "unknown",
                        method="POST",
                        status=long_response.status_code,
                        error_type=None,
                        error_code=None,
                        message="Meta returned a non-object long-lived token response",
                        exception_class="TypeError",
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid long-lived token response",
                        code="oauth_token_exchange_failed",
                    )
                access_token = str(long_payload.get("access_token") or "").strip()
                if not access_token:
                    _log_stage(
                        stage="long_lived_token_exchange",
                        hostname=urlsplit(long_url).hostname or "unknown",
                        method="POST",
                        status=long_response.status_code,
                        error_type=None,
                        error_code=None,
                        message="Meta returned no long-lived token",
                        exception_class="InstagramOAuthError",
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned no long-lived token",
                        code="oauth_token_exchange_failed",
                    )

                profile_url = f"{self.settings.meta_graph_base_url}/me"
                profile_response = self._request_stage(
                    stage="instagram_profile_lookup",
                    method="GET",
                    url=profile_url,
                    request=lambda: client.get(
                        profile_url,
                        params={
                            "fields": "id,user_id,username,account_type",
                            "access_token": access_token,
                        },
                    ),
                )
                try:
                    profile = profile_response.json()
                except (ValueError, TypeError) as exc:
                    _log_stage(
                        stage="instagram_profile_lookup",
                        hostname=urlsplit(profile_url).hostname or "unknown",
                        method="GET",
                        status=profile_response.status_code,
                        error_type=None,
                        error_code=None,
                        message=None,
                        exception_class=type(exc).__name__,
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid Instagram profile response",
                        code="instagram_profile_lookup_failed",
                    ) from exc
                if not isinstance(profile, dict):
                    _log_stage(
                        stage="instagram_profile_lookup",
                        hostname=urlsplit(profile_url).hostname or "unknown",
                        method="GET",
                        status=profile_response.status_code,
                        error_type=None,
                        error_code=None,
                        message="Meta returned a non-object Instagram profile response",
                        exception_class="TypeError",
                        elapsed_ms=0.0,
                    )
                    raise InstagramOAuthError(
                        "Meta returned an invalid Instagram profile response",
                        code="instagram_profile_lookup_failed",
                    )
        except InstagramOAuthError:
            raise
        except (ValueError, TypeError) as exc:
            raise InstagramOAuthError(
                "Instagram authorization failed",
                code="oauth_provider_rejected",
            ) from exc

        account_id = str(profile.get("user_id") or profile.get("id") or "").strip()
        if not account_id:
            _log_stage(
                stage="instagram_profile_lookup",
                hostname=urlsplit(self.settings.meta_graph_base_url).hostname
                or "unknown",
                method="GET",
                status=profile_response.status_code,
                error_type=None,
                error_code=None,
                message="missing Instagram account identifier",
                exception_class="InstagramOAuthError",
                elapsed_ms=0.0,
            )
            raise InstagramOAuthError(
                "Meta returned no Instagram account",
                code="instagram_profile_lookup_failed",
            )
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


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 1)


def _safe_message(value: object | None) -> str:
    if value is None:
        return "-"
    text = " ".join(str(value).split())
    text = _SENSITIVE_VALUE.sub("[redacted]", text)
    text = _SENSITIVE_TEXT.sub("[redacted]", text)
    return text[:200] or "-"


def _meta_error_details(
    response: httpx.Response,
) -> tuple[str | None, str | None, str | None]:
    try:
        payload = response.json()
    except (ValueError, TypeError):
        return None, None, None
    if not isinstance(payload, dict):
        return None, None, None
    error = payload.get("error")
    if isinstance(error, dict):
        error_type = error.get("type") or error.get("error_type")
        error_code = error.get("code") or error.get("error_code")
        message = error.get("message") or error.get("error_message")
    else:
        error_type = payload.get("error_type")
        error_code = payload.get("error_code") or payload.get("code")
        message = payload.get("error_message") or payload.get("message")
    return (
        _scalar_text(error_type),
        _scalar_text(error_code),
        _scalar_text(message),
    )


def _scalar_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:200] or None


def _classify_provider_error(
    stage: str,
    error_type: str | None,
    error_code: str | None,
    message: str | None,
) -> str:
    haystack = " ".join(
        value.casefold() for value in (error_type, error_code, message) if value
    )
    if "redirect_uri" in haystack or "redirect uri" in haystack:
        return "oauth_redirect_uri_mismatch"
    if "invalid client" in haystack or "client_id" in haystack or "client secret" in haystack:
        return "oauth_invalid_client"
    if stage == "instagram_profile_lookup":
        return "instagram_profile_lookup_failed"
    return "oauth_provider_rejected"


def _log_stage(
    *,
    stage: str,
    hostname: str,
    method: str,
    status: int | None,
    error_type: str | None,
    error_code: str | None,
    message: str | None,
    exception_class: str | None,
    elapsed_ms: float,
    api_version: str | None = None,
) -> None:
    log = logger.warning if exception_class else logger.info
    log(
        "instagram_oauth stage=%s destination_host=%s method=%s http_status=%s "
        "meta_error_type=%s meta_error_code=%s meta_message=%s exception_class=%s "
        "elapsed_ms=%s api_version=%s",
        stage,
        hostname,
        method,
        status if status is not None else "none",
        _safe_message(error_type),
        _safe_message(error_code),
        _safe_message(message),
        exception_class or "-",
        elapsed_ms,
        api_version or "NONE",
        extra={"event_code": f"instagram.oauth.{stage}"},
    )


def _log_short_token_metadata(payload: dict[str, object], status: int) -> None:
    token_value = payload.get("access_token")
    token_text = token_value.strip() if isinstance(token_value, str) else ""
    logger.info(
        "instagram_oauth stage=short_token_metadata http_status=%s "
        "access_token_present=%s token_length=%s user_id_present=%s "
        "token_type_present=%s expires_in_present=%s response_keys=%s",
        status,
        _bool_text(bool(token_text)),
        len(token_text),
        _bool_text(_field_present(payload, "user_id")),
        _bool_text(_field_present(payload, "token_type")),
        _bool_text(_field_present(payload, "expires_in")),
        _safe_response_keys(payload),
        extra={"event_code": "instagram.oauth.short_token_metadata"},
    )


def _log_short_token_user_id_presence(present: bool) -> None:
    logger.info(
        "instagram_oauth stage=short_token_user_id short_token_user_id_present=%s",
        _bool_text(present),
        extra={"event_code": "instagram.oauth.short_token_user_id"},
    )


def _log_short_token_permissions(payload: dict[str, object]) -> None:
    raw_permissions = payload.get("permissions")
    permissions_present = raw_permissions is not None
    permission_names: set[str] = set()
    if isinstance(raw_permissions, (list, tuple, set)):
        permission_names = {
            value.strip()
            for value in raw_permissions
            if isinstance(value, str) and value.strip()
        }
        permission_count = len(raw_permissions)
    elif isinstance(raw_permissions, str):
        permission_names = {
            value.strip()
            for value in raw_permissions.split(",")
            if value.strip()
        }
        permission_count = len(permission_names)
    else:
        permission_count = 0
    requested_permissions_all_present = set(INSTAGRAM_LOGIN_SCOPES).issubset(
        permission_names
    )
    logger.info(
        "instagram_oauth stage=short_token_permissions permissions_present=%s "
        "permission_count=%s requested_permissions_all_present=%s",
        _bool_text(permissions_present),
        permission_count,
        _bool_text(requested_permissions_all_present),
        extra={"event_code": "instagram.oauth.short_token_permissions"},
    )


def _probe_short_token_profile(
    oauth_client: MetaInstagramOAuthClient,
    client: httpx.Client,
    *,
    short_token: str,
    url: str,
    api_version: str | None,
    stage: str,
) -> None:
    probe_started = perf_counter()
    try:
        response = oauth_client._request_stage(
            stage=stage,
            method="GET",
            url=url,
            request=lambda: client.get(
                url,
                params={
                    "fields": "id,user_id,username,account_type",
                    "access_token": short_token,
                },
            ),
            log_success=False,
            api_version=api_version,
        )
    except InstagramOAuthError:
        # These probes are diagnostics only and must never block OAuth.
        return

    try:
        payload = response.json()
    except (ValueError, TypeError) as exc:
        _log_stage(
            stage=stage,
            hostname=urlsplit(url).hostname or "unknown",
            method="GET",
            status=response.status_code,
            error_type=None,
            error_code=None,
            message=None,
            exception_class=type(exc).__name__,
            elapsed_ms=_elapsed_ms(probe_started),
            api_version=api_version,
        )
        return
    if not isinstance(payload, dict):
        _log_stage(
            stage=stage,
            hostname=urlsplit(url).hostname or "unknown",
            method="GET",
            status=response.status_code,
            error_type=None,
            error_code=None,
            message="Meta returned a non-object Instagram profile response",
            exception_class="TypeError",
            elapsed_ms=_elapsed_ms(probe_started),
            api_version=api_version,
        )
        return
    _log_short_token_profile_probe(payload, stage=stage, api_version=api_version)


def _log_short_token_profile_probe(
    payload: dict[str, object], *, stage: str, api_version: str | None
) -> None:
    account_type = payload.get("account_type")
    if isinstance(account_type, str):
        normalized_type = account_type.strip().upper()
    else:
        normalized_type = ""
    if normalized_type not in {"BUSINESS", "CREATOR"}:
        normalized_type = "OTHER" if normalized_type else "MISSING"
    logger.info(
        "instagram_oauth stage=%s profile_returned=true "
        "id_present=%s user_id_present=%s username_present=%s account_type=%s "
        "api_version=%s",
        stage,
        _bool_text(_field_present(payload, "id")),
        _bool_text(_field_present(payload, "user_id")),
        _bool_text(_field_present(payload, "username")),
        normalized_type,
        api_version or "NONE",
        extra={"event_code": f"instagram.oauth.{stage}"},
    )


def _field_present(payload: dict[str, object], name: str) -> bool:
    value = payload.get(name)
    if value is None:
        return False
    return not isinstance(value, str) or bool(value.strip())


def _safe_response_keys(payload: dict[str, object]) -> str:
    keys: list[str] = []
    for key in payload:
        text = str(key)
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", text):
            keys.append(text)
        else:
            keys.append("<redacted>")
    return ",".join(sorted(keys)) or "-"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
