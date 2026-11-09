# Instagram onboarding — Meta Unified Login

## Production target configuration

The DirectPilot Meta app uses **Instagram API (Unified Login)** through a Facebook Login for Business configuration. This is not the legacy Instagram Login flow and must not use `instagram.com/oauth/authorize`, `api.instagram.com/oauth/access_token`, `graph.instagram.com`, or the Instagram Login long-lived-token exchange.

Meta configuration currently registered for DirectPilot:
- Configuration ID: `962123656629907`
- OAuth redirect URI: `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`
- Backend callback route: `/api/v1/integrations/instagram/callback`
- Required configuration permissions for the current messaging/comment scope: `instagram_basic`, `instagram_manage_messages`, `instagram_manage_comments`
- Optional permissions visible in the Meta configuration: ads and content publishing. Do not request or enable them unless the corresponding product feature is implemented and reviewed.

## Runtime configuration

Set these variables in the target Vercel environment before enabling Unified Login:

- `META_OAUTH_MODE=unified_login`
- `META_OAUTH_CONFIG_ID=962123656629907`
- `META_APP_ID` — Meta App ID
- `META_APP_SECRET` — Meta App Secret (sensitive)
- `META_OAUTH_REDIRECT_URI=https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`
- `META_API_VERSION=v24.0`
- Existing `INSTAGRAM_TOKEN_ENCRYPTION_KEY` must remain unchanged and valid.

Never paste access tokens, app secrets, or encryption keys into chat, source control, issue trackers, or logs. Do not replace the encryption key on an existing database: doing so makes previously encrypted customer tokens unreadable.

## Unified Login flow

1. Authenticated customer requests an Instagram connection. Backend creates a cryptographically random state, stores only its digest, and binds it to tenant/store/user with a short expiry.
2. Browser is redirected to Facebook OAuth with `client_id`, `config_id`, `redirect_uri`, `response_type=code`, and the state. The permission and asset selection are controlled by the saved Meta configuration; do not add legacy Instagram Login scopes.
3. Meta redirects to the registered backend callback. Backend consumes state exactly once before exchanging the authorization code.
4. Backend exchanges the code at `GET https://graph.facebook.com/{version}/oauth/access_token` using app credentials and the exact redirect URI.
5. Backend discovers granted Instagram assets through `GET /me/assigned_instagram_accounts?fields=id,username`, following cursor pagination with a hard safety limit.
6. Current onboarding contract supports one Instagram account per connection. Zero or multiple accounts fail closed with explicit sanitized error codes; never silently select the first asset.
7. The returned System User token is stored using the existing Fernet encryption and tenant/store ownership checks. It is not exchanged using Instagram Login's `ig_exchange_token` flow.
8. Webhook receiver remains `/api/v1/integrations/instagram/webhook`. Dashboard callback verification and per-account Graph API subscription are separate operations.

## Webhook status and safety

- Dashboard callback verification confirms only that Meta can verify the receiver.
- App-level field subscriptions and per-account `/{ig-user-id}/subscribed_apps` are separate.
- This provider revision does not claim that per-account subscription has succeeded; that must be implemented/verified before accepting live inbound events.
- Outbound sending remains disabled by default (`META_SEND_ENABLED=false`). Do not enable globally as part of OAuth migration.

## Migration and rollback

- Keep `META_OAUTH_MODE=instagram_login` until the Unified Login code has passed automated tests and a real test-account round trip.
- Enable `unified_login` only in a controlled deployment after validating the Meta configuration and account assignment.
- Rollback: set `META_OAUTH_MODE=instagram_login` and redeploy. Do not delete encrypted connection rows or rotate the Fernet key.
- Existing Instagram Login connections must not be assumed compatible with Unified Login tokens. Treat token provenance as a migration concern and test existing connection operations separately.

## Current implementation limits / next validation

- One assigned Instagram account is supported per onboarding operation. Multiple assets need an explicit account-selection UX and server-side selection token before support is enabled.
- This revision discovers and stores the token/account. Per-account webhook subscription and diagnostics remain a required follow-up before production messaging is considered ready.
- Meta App Review / advanced access may be required for customers outside app roles during live use.
