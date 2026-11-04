# Google Search Console OAuth — Phase 1 Runbook

Date: 2026-11-04
Status: implemented on `feature/seo-service-foundation-20261104`; not deployed.

## Scope

This runbook covers only the first customer-facing Google connection flow. It does not enable Search Analytics ingestion, technical crawling, recommendations, CMS changes, or paid plans.

## Environment configuration

Set these values in the target backend environment's secret manager (Render environment settings for the deployed service):

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`
- `SEO_GOOGLE_TOKEN_ENCRYPTION_KEY`

Optional tuning:
- `SEO_GOOGLE_OAUTH_STATE_TTL_MINUTES` (default 10; accepted 2–30)
- `SEO_GOOGLE_OAUTH_TIMEOUT_SECONDS` (default 20; accepted 1–60)

Generate a dedicated Fernet key in a trusted local environment:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use a unique key for SEO. Do not reuse `INSTAGRAM_TOKEN_ENCRYPTION_KEY`, commit the generated value, paste it into tickets, or include it in logs. Back up the key in the approved secrets vault: losing it makes stored Google refresh tokens undecryptable.

## Google Cloud OAuth client

1. Use a Google Cloud project owned by DirectPilot.
2. Configure the OAuth consent screen and required audience/test users according to the release environment.
3. Create an OAuth client of type Web application.
4. Add the exact callback URI configured in `GOOGLE_OAUTH_REDIRECT_URI` to Authorized redirect URIs.
5. The initial requested scopes are `openid`, `email`, and `https://www.googleapis.com/auth/webmasters.readonly`.
6. Keep the OAuth client secret in the deployment secret manager only.

Do not enable this in Production before security review, Google consent-screen verification requirements are resolved, and UAT acceptance is recorded.

## API contract

All customer endpoints require the existing authenticated DirectPilot session.

- `POST /api/v1/seo/google/connect`: returns a Google authorization URL and state expiry. Requires active `seo_site_limit >= 1` entitlement.
- `GET /api/v1/seo/google/callback?code=...&state=...`: requires the same authenticated DirectPilot user who initiated the flow.
- `GET /api/v1/seo/google/status`: safe connection status; remains available after entitlement expiry so customers can understand and disconnect their connection.
- `GET /api/v1/seo/google/properties`: lists only properties returned by Google and requires an active SEO entitlement.
- `POST /api/v1/seo/google/properties/refresh`: refreshes the access token and re-discovers accessible properties.
- `POST /api/v1/seo/google/properties/select`: body contains the provider-issued `property_public_id`; arbitrary property URLs are not accepted.
- `DELETE /api/v1/seo/google/connection`: revokes the remote grant where possible and always clears the locally stored encrypted refresh token.

## Entitlement

The service deliberately fails closed unless the active tenant/store subscription has integer `limits_json.seo_site_limit >= 1`. Existing plans and trials are not modified by this feature. Do not grant entitlement until the owner approves price, trial, property limits, audit quotas, and retention policy.

## UAT acceptance checklist

- [ ] Configure UAT-only Google OAuth client and a newly generated SEO Fernet key.
- [ ] Verify exact redirect URI in Google Cloud and UAT service configuration.
- [ ] Provision a test tenant/store with a temporary reviewed `seo_site_limit` entitlement.
- [ ] Connect a test Google account with at least one Search Console property.
- [ ] Confirm property URI and permission level exactly match Google's `sites.list` response.
- [ ] Confirm the refresh token is ciphertext in the database and is never returned by API.
- [ ] Confirm callback fails for a different DirectPilot user, expired state, replayed state, and invalid state.
- [ ] Confirm tenant A cannot read or select tenant B's property public ID.
- [ ] Confirm revoked Google access changes connection status to `reauthorization_required` after property refresh.
- [ ] Confirm disconnect clears the stored token and removes cached properties even if Google's revoke endpoint is unavailable.
- [ ] Confirm no Google OAuth code, state, access token, refresh token, or client secret appears in logs.
- [ ] Record migration, CI, API, and manual browser evidence before UAT acceptance.

## Rollback

Do not run a production downgrade as a routine rollback. Migration `0028_seo_google_connections` creates customer credential and property tables; preserve evidence and use the approved data-retention procedure. Disable customer routes/entitlements first, revoke grants as appropriate, and obtain explicit approval before any destructive schema operation.
