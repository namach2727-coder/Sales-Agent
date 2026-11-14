"""Meta Instagram API with Unified Login provider.

Uses Facebook Login for Business configuration and system-user access tokens.
Legacy Instagram Login remains available through the existing adapter.
"""
from __future__ import annotations

import logging
from time import perf_counter
from urllib.parse import urlencode, urlsplit

import httpx

from app.config import Settings
from app.instagram_onboarding.provider import InstagramOAuthAccount, InstagramOAuthError

logger = logging.getLogger("sales_assistant.instagram_unified_oauth")


class MetaUnifiedInstagramOAuthClient:
    """Unified Login adapter; never logs authorization codes or access tokens."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _config(self) -> tuple[str, str, str, str]:
        app_id = self.settings.meta_app_id.strip()
        app_secret = self.settings.meta_app_secret.strip()
        redirect_uri = self.settings.meta_oauth_redirect_uri.strip()
        config_id = self.settings.meta_oauth_config_id.strip()
        if not all((app_id, app_secret, redirect_uri, config_id)):
            raise InstagramOAuthError(
                "Instagram Unified Login is not fully configured",
                code="oauth_configuration_error",
            )
        parsed = urlsplit(redirect_uri)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise InstagramOAuthError(
                "Instagram redirect URI must be a plain HTTPS URL",
                code="oauth_configuration_error",
            )
        return app_id, app_secret, redirect_uri, config_id

    def authorization_url(self, state: str) -> str:
        app_id, _secret, redirect_uri, config_id = self._config()
        query = urlencode({
            "client_id": app_id,
            "config_id": config_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "override_default_response_type": "true",
        })
        return f"https://www.facebook.com/{self.settings.meta_api_version.strip('/')}/dialog/oauth?{query}"

    def subscribe_webhooks(self, account: InstagramOAuthAccount) -> None:
        """Subscribe an already-authorized Instagram asset to inbound events."""
        self._config()
        # The token is intentionally supplied only by the in-memory account
        # returned from this OAuth exchange; it is never logged.
        token = account.access_token
        base = f"https://graph.facebook.com/{self.settings.meta_api_version.strip('/')}"
        timeout = httpx.Timeout(self.settings.meta_oauth_timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            started = perf_counter()
            try:
                response = client.post(
                    f"{base}/{account.account_id}/subscribed_apps",
                    data={"subscribed_fields": "messages,comments"},
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.HTTPError as exc:
                logger.warning("instagram_unified stage=webhook_subscription status=network_error")
                raise InstagramOAuthError(
                    "Meta webhook subscription request failed",
                    code="unified_webhook_subscription_network_error",
                ) from exc
            if not 200 <= response.status_code < 300:
                try:
                    payload = response.json()
                    error = payload.get("error", {}) if isinstance(payload, dict) else {}
                    error_code = error.get("code") if isinstance(error, dict) else None
                    error_type = error.get("type") if isinstance(error, dict) else None
                except (ValueError, TypeError):
                    error_code, error_type = None, None
                logger.warning(
                    "instagram_unified stage=webhook_subscription status=%s error_type=%s error_code=%s elapsed_ms=%.1f",
                    response.status_code, str(error_type)[:80], str(error_code)[:40],
                    (perf_counter()-started)*1000,
                )
                raise InstagramOAuthError(
                    "Meta rejected the Instagram webhook subscription",
                    code="unified_webhook_subscription_failed",
                )
            try:
                payload = response.json()
            except (ValueError, TypeError) as exc:
                raise InstagramOAuthError(
                    "Meta returned an invalid webhook subscription response",
                    code="unified_webhook_subscription_invalid_response",
                ) from exc
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise InstagramOAuthError(
                    "Meta did not confirm the Instagram webhook subscription",
                    code="unified_webhook_subscription_unconfirmed",
                )
            logger.info(
                "instagram_unified stage=webhook_subscription status=%s elapsed_ms=%.1f",
                response.status_code, (perf_counter()-started)*1000,
            )

    def unsubscribe_webhooks(self, account: InstagramOAuthAccount) -> None:
        """Compensate a successful subscription when local persistence fails."""
        self._config()
        base = f"https://graph.facebook.com/{self.settings.meta_api_version.strip('/')}"
        timeout = httpx.Timeout(self.settings.meta_oauth_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.delete(
                    f"{base}/{account.account_id}/subscribed_apps",
                    headers={"Authorization": f"Bearer {account.access_token}"},
                )
        except httpx.HTTPError as exc:
            logger.error("instagram_unified stage=webhook_compensation status=network_error")
            raise InstagramOAuthError(
                "Meta webhook subscription compensation failed",
                code="unified_webhook_compensation_network_error",
            ) from exc
        if not 200 <= response.status_code < 300:
            logger.error(
                "instagram_unified stage=webhook_compensation status=%s",
                response.status_code,
            )
            raise InstagramOAuthError(
                "Meta rejected webhook subscription compensation",
                code="unified_webhook_compensation_failed",
            )
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise InstagramOAuthError(
                "Meta returned an invalid webhook compensation response",
                code="unified_webhook_compensation_invalid_response",
            ) from exc
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise InstagramOAuthError(
                "Meta did not confirm webhook subscription compensation",
                code="unified_webhook_compensation_unconfirmed",
            )
        logger.info("instagram_unified stage=webhook_compensation status=confirmed")

    def exchange(self, code: str) -> InstagramOAuthAccount:
        app_id, app_secret, redirect_uri, _config_id = self._config()
        normalized_code = code.strip()
        if not normalized_code or len(normalized_code) > 4096:
            raise InstagramOAuthError("Invalid authorization response", code="oauth_provider_rejected")

        base = f"https://graph.facebook.com/{self.settings.meta_api_version.strip('/')}"
        timeout = httpx.Timeout(self.settings.meta_oauth_timeout_seconds)

        def request(client: httpx.Client, stage: str, url: str, **kwargs):
            started = perf_counter()
            try:
                response = client.request(**kwargs, url=url)
            except httpx.HTTPError as exc:
                logger.warning("instagram_unified stage=%s host=%s status=network_error elapsed_ms=%.1f", stage, urlsplit(url).hostname, (perf_counter()-started)*1000)
                raise InstagramOAuthError("Meta provider network failure", code="instagram_provider_network_error") from exc
            if not 200 <= response.status_code < 300:
                try:
                    payload = response.json()
                    err = payload.get("error", {}) if isinstance(payload, dict) else {}
                    err_code = err.get("code") if isinstance(err, dict) else None
                    err_type = err.get("type") if isinstance(err, dict) else None
                except (ValueError, TypeError):
                    err_code, err_type = None, None
                logger.warning("instagram_unified stage=%s host=%s status=%s error_type=%s error_code=%s", stage, urlsplit(url).hostname, response.status_code, str(err_type)[:80], str(err_code)[:40])
                raise InstagramOAuthError("Meta rejected the Unified Login request", code=f"unified_{stage}_failed")
            logger.info("instagram_unified stage=%s host=%s status=%s elapsed_ms=%.1f", stage, urlsplit(url).hostname, response.status_code, (perf_counter()-started)*1000)
            try:
                result = response.json()
            except (ValueError, TypeError) as exc:
                raise InstagramOAuthError("Meta returned an invalid response", code=f"unified_{stage}_invalid_response") from exc
            if not isinstance(result, dict):
                raise InstagramOAuthError("Meta returned an invalid response", code=f"unified_{stage}_invalid_response")
            return result

        with httpx.Client(timeout=timeout) as client:
            token_payload = request(
                client, "token_exchange", f"{base}/oauth/access_token",
                method="GET",
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "redirect_uri": redirect_uri,
                    "code": normalized_code,
                },
            )
            token = str(token_payload.get("access_token") or "").strip()
            if not token:
                raise InstagramOAuthError("Meta returned no access token", code="unified_token_missing")
            token_type = str(token_payload.get("token_type") or "bearer")
            expires_value = token_payload.get("expires_in")
            expires_in = int(expires_value) if isinstance(expires_value, (int, float)) else None

            accounts: list[dict] = []
            after: str | None = None
            seen_cursors: set[str] = set()
            for _ in range(100):
                params = {"fields": "id,username", "limit": "100"}
                if after:
                    params["after"] = after
                page = request(
                    client, "account_discovery", f"{base}/me/assigned_instagram_accounts",
                    method="GET", params=params, headers={"Authorization": f"Bearer {token}"},
                )
                data = page.get("data")
                if not isinstance(data, list):
                    raise InstagramOAuthError("Meta returned an invalid account list", code="unified_account_discovery_invalid")
                accounts.extend(item for item in data if isinstance(item, dict) and item.get("id"))
                paging = page.get("paging") if isinstance(page.get("paging"), dict) else {}
                cursors = paging.get("cursors") if isinstance(paging.get("cursors"), dict) else {}
                next_after = cursors.get("after")
                if not data or not next_after:
                    break
                next_after = str(next_after)
                if next_after == after or next_after in seen_cursors:
                    raise InstagramOAuthError("Meta returned a repeated pagination cursor", code="unified_account_pagination_invalid")
                seen_cursors.add(next_after)
                after = next_after
            else:
                raise InstagramOAuthError("Instagram account discovery exceeded the safety limit", code="unified_account_discovery_limit")

            unique = {str(item["id"]): item for item in accounts}
            if len(unique) != 1:
                code_name = "unified_no_instagram_accounts" if not unique else "unified_multiple_instagram_accounts"
                raise InstagramOAuthError(
                    "Select exactly one Instagram account in the Meta business configuration before connecting",
                    code=code_name,
                )
            account_id, profile = next(iter(unique.items()))
            username = str(profile.get("username") or "").strip() or None

            # The System User token is already the credential used for Graph API.
            # Do not perform Instagram Login's long-lived-token exchange.
            return InstagramOAuthAccount(
                account_id=account_id,
                username=username,
                access_token=token,
                token_type=token_type,
                expires_in=expires_in,
                scopes=(),
            )
