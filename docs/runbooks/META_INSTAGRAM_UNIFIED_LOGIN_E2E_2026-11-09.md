# Meta Instagram Unified Login — Production Runbook & E2E Acceptance

**Last updated:** 2026-11-09  
**Repository:** `namach2727-coder/Sales-Agent`  
**Documentation branch:** `docs/meta-unified-login-e2e-20261109`  
**Runtime branch at observed deployment:** `feature/instagram-unified-login`  
**Backend Vercel project:** `directpilot-prod-api`

## 1. Meta application identity

| Setting | Verified value |
| --- | --- |
| Meta app display name | Direct Pilot |
| Meta App ID | `1889564582046419` |
| Login model | Instagram API — Unified Login |
| Meta API version | `v24.0` |
| Facebook Login for Business Configuration ID | `962123656629907` |
| OAuth callback | `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback` |
| Backend connect route | `POST /api/v1/integrations/instagram/connect` |
| Backend callback route | `GET /api/v1/integrations/instagram/callback` |
| Connection status route | `GET /api/v1/integrations/instagram/status` |
| Accounts route | `GET /api/v1/integrations/instagram/accounts` |
| Webhook receiver | `/api/v1/integrations/instagram/webhook` |

The Meta App ID is a public application identifier, not a credential. The App Secret, authorization codes, access tokens, encryption keys, webhook verify tokens, and customer data must never be written to repository documentation, source, issue comments, test fixtures, or logs.

## 2. Unified Login configuration

The intended Meta flow is **Instagram API with Unified Login**, configured through Facebook Login for Business. It is not the legacy Instagram Login flow.

Production Vercel variables observed for the backend:

| Variable | Expected / observed state | Handling |
| --- | --- | --- |
| `META_OAUTH_MODE` | `unified_login` | Plain setting |
| `META_OAUTH_CONFIG_ID` | `962123656629907` | Plain setting |
| `META_APP_ID` | App ID above; variable updated 2026-11-09 | Treat as app configuration |
| `META_APP_SECRET` | Secret variable updated 2026-11-09 | Never read back into logs/docs |
| `META_OAUTH_REDIRECT_URI` | Callback URL above | Sensitive variable in Vercel |
| `META_API_VERSION` | `v24.0` expected by current implementation | Verify before any future version change |
| `INSTAGRAM_TOKEN_ENCRYPTION_KEY` | Existing key must remain stable | Do not rotate: existing encrypted tokens could become unreadable |
| `META_SEND_ENABLED` | Observed `true` in Production | Do not perform outbound message tests without separate explicit authorization |
| `META_CONTENT_PUBLISH_ENABLED` | Observed `true` in Production | Do not publish content during onboarding tests |

The secret value itself is deliberately not recorded. The Vercel environment listing confirms a Production `META_APP_SECRET` variable exists and was updated at 2026-11-09 11:27 UTC; the provider value is encrypted/sensitive and was not independently compared to Meta's dashboard. The owner stated that the correct secret was then set. Do not claim cryptographic identity verification of the secret.

## 3. Permissions and account selection

The current Meta configuration requires the following scopes for the implemented messaging/comment workflow:

- `instagram_basic`
- `instagram_manage_messages`
- `instagram_manage_comments`

Ads and content-publishing permissions are optional and must not be requested or enabled unless the relevant feature is implemented and separately reviewed.

The backend discovers assigned Instagram assets using:

`GET /me/assigned_instagram_accounts?fields=id,username`

It paginates with a bounded safety limit and fails closed unless exactly one Instagram account is assigned. Multiple-account selection UX is not implemented; do not silently select the first account.

The implementation subscribes the selected account to `messages,comments` through `/{ig-user-id}/subscribed_apps`. This account-level subscription is distinct from Meta App Dashboard webhook callback verification and app-level field subscriptions.

## 4. OAuth lifecycle

1. An authenticated tenant user calls `POST /connect`.
2. Backend creates a cryptographically random state, stores its digest, and binds it to tenant/store/user with a short expiry.
3. Browser is redirected to Facebook OAuth with `client_id`, `config_id`, exact `redirect_uri`, `response_type=code`, and state.
4. Meta returns the authorization code and state to the registered callback.
5. Backend consumes state exactly once and exchanges the code at `GET https://graph.facebook.com/v24.0/oauth/access_token`, supplying App ID, App Secret, exact redirect URI and code.
6. Backend discovers the assigned Instagram account(s), validates exactly one, and subscribes that account to messages/comments.
7. The token is encrypted using the existing `INSTAGRAM_TOKEN_ENCRYPTION_KEY` and persisted with tenant/store ownership.
8. Browser callback redirects to `/settings/integrations/instagram?instagram=connected` on success, or a sanitized error code on failure.

Do not use legacy endpoints or exchanges: `instagram.com/oauth/authorize`, `api.instagram.com/oauth/access_token`, `graph.instagram.com`, or `ig_exchange_token`.

## 5. Incident history and observed recovery

- Earlier authorization URL exposed the wrong `client_id=4496311907256141`, while the expected Direct Pilot App ID was `1889564582046419`. Production `META_APP_ID` was updated.
- A subsequent callback reached Meta token exchange but Meta returned HTTP 400 / `OAuthException` / code `1`; the UI surfaced `unified_token_exchange_failed`.
- Owner then configured the missing `META_APP_SECRET` in Vercel Production. Vercel environment metadata confirms the variable's `updatedAt` changed to 2026-11-09 11:27 UTC.
- The first deployment visible immediately after the secret update predated the environment change. Owner then redeployed the backend.
- Production deployment observed after the secret update: `dpl_Dp2k4zi2abSZqdzR6Z67NVX36ypY`, READY, Production, branch `feature/instagram-unified-login`, commit `973839d28e569362aa528579db028a693151dd5b`.
- The owner completed the Meta login flow and supplied a screenshot showing the success message **«اتصال اینستاگرام با موفقیت تأیید شد.»** This is evidence of a successful browser OAuth callback path, but does not by itself prove persisted connection status, webhook delivery, token refresh/lifecycle, or messaging/comment automation.

## 6. Automated test evidence and known CI blocker

Workflow: `.github/workflows/instagram-unified-login.yml`

For deployed source commit `973839d28e569362aa528579db028a693151dd5b`:

- **Instagram Unified Login Tests:** GitHub Actions run `42586571895`, conclusion **SUCCESS**. Dependency install, compile check, and focused `tests/test_instagram_unified_login.py` + `tests/test_instagram_onboarding.py` passed.
- **General CI:** run `42586571875`, conclusion **FAILURE**. PostgreSQL smoke, PostgreSQL 18 compatibility, and Docker build jobs passed. The general pytest job failed during collection because `tests/test_seo_growth_crawler_preview.py` imports missing module `app.seo_growth.crawler_policy`. This is a repository-wide/pre-existing unrelated collection blocker in this branch; do not label the full suite green.

Focused tests cover authorization URL construction without legacy scopes, token exchange/account discovery, webhook subscription headers/fields, multiple-account fail-closed behavior, and compensating webhook unsubscribe. They use mocked Meta HTTP responses; they are not a live Meta integration test.

## 7. End-to-end acceptance matrix

| Layer | Test | Current evidence | Status |
| --- | --- | --- | --- |
| Meta OAuth consent | User completes Meta login and returns to DirectPilot | Owner screenshot displays success message | PASS — user-observed |
| App ID | Authorization URL uses `1889564582046419` | Previous wrong value identified; live URL after redeploy not independently captured | NEEDS LIVE RECHECK |
| Secret | Production variable exists and was updated | Vercel metadata confirms sensitive variable update; value intentionally unreadable | CONFIGURED, value not independently verified |
| Deployment | New Production deployment includes intended source after secret update | Deployment `dpl_Dp2k4zi2abSZqdzR6Z67NVX36ypY` READY | PASS |
| Health | `GET /ready` | HTTP 200; database available; migration current (observed after prior deployment; repeat after latest redeploy) | RECHECK |
| Persisted account | Authenticated `GET /status` and `GET /accounts` | Not yet inspected after user success | PENDING |
| Refresh persistence | Refresh dashboard, re-read status | Not yet inspected | PENDING |
| Tenant isolation | Different tenant cannot read another tenant's connection | Automated service/security tests need review and live multi-tenant test account | PENDING |
| Webhook configuration | Dashboard callback verification + app-level `messages`/`comments` subscriptions + per-account subscription | Code subscribes account; Meta dashboard state not independently verified | PENDING |
| Inbound DM | Send a controlled test DM from an authorized test account and inspect inbound event + persistence | Not yet performed | PENDING |
| Inbound comment | Create a controlled comment on an authorized test media item and inspect event + persistence | Not yet performed | PENDING |
| Automation reply | Validate dry-run/disabled path first; send only after explicit approval | Production send/publish flags observed true; no outbound test authorized | BLOCKED — explicit approval required |
| Token security | Confirm token stored encrypted and never exposed to frontend/logs | Code path uses encryption; live DB row not inspected in this test pass | PENDING |
| Disconnect/revoke | Disconnect and verify local cleanup and Meta subscription reconciliation | Not yet tested | PENDING |
| Token expiry/revocation | Confirm clear status and reauthorization path | Not yet tested | PENDING |

## 8. Safe comprehensive test sequence

### Phase A — read-only Production checks
- Verify current Vercel Production deployment ID, branch, commit and timestamp.
- Call `GET /ready`; require HTTP 200, database available, migration current.
- With an authenticated owner browser session, call `GET /status` and `GET /accounts`; verify one account, expected username, active status, token_configured=true, and account_limit/entitlement.
- Refresh dashboard and repeat status check.
- Confirm the account belongs to the expected tenant/store; do not expose tokens or full internal IDs in screenshots.

### Phase B — Meta webhook configuration
- In Meta App Dashboard, verify callback URL and verify-token configuration, then verify app-level `messages` and `comments` fields are subscribed.
- Verify the selected Instagram account's subscription to `messages,comments`.
- Do not expose verify tokens. A successful OAuth callback does not prove webhook setup or delivery.

### Phase C — controlled inbound tests
- Use only a designated test Instagram account and test media.
- Send one test DM and one test comment from a separate authorized tester account.
- Verify Meta webhook delivery, HTTP 2xx acknowledgement, normalized event persistence, deduplication, tenant/store routing and no cross-tenant visibility.
- Confirm event timestamps and sender/account identifiers are normalized correctly.
- Do not trigger outbound auto-replies in this phase.

### Phase D — outbound behavior (separate authorization gate)
- Production currently reports `META_SEND_ENABLED=true` and `META_CONTENT_PUBLISH_ENABLED=true`. Keep both operationally unused during this pass.
- First inspect rule state and use a dry-run or mocked provider test.
- Before any real reply or content publication, obtain explicit owner approval specifying test account, exact message/content, destination and permitted action.
- Verify rate limits, idempotency, loop/echo suppression, entitlement, human takeover, audit record, and failure handling before enabling any customer-facing automation.

### Phase E — negative and lifecycle tests
- Unauthenticated status/accounts/connect requests must be rejected.
- Invalid, expired, replayed, or tenant-mismatched state must fail closed.
- Zero or multiple assigned Instagram accounts must not create a connection.
- Meta token-exchange or subscription errors must leave no active local connection; compensating unsubscribe must be attempted if persistence fails after subscription.
- Disconnect/revocation must reconcile local status and Meta subscription without leaking token material.

## 9. Operational safety and rollback

- Never log or commit App Secret, OAuth code, access token, webhook verify token, database credentials or encryption keys.
- Never rotate `INSTAGRAM_TOKEN_ENCRYPTION_KEY` on an existing database without a controlled re-encryption migration.
- Keep customer tokens server-side and encrypted.
- Keep tenant/store ownership checks on every account/status/webhook operation.
- Do not test outbound sending or publishing merely because the feature flags are true.
- Roll back only through the reviewed prior Production deployment and a separately approved action; do not change OAuth mode or credentials casually.
- Meta App Review / advanced access may be required for external customers beyond app roles. Verify current Meta access level and business verification before onboarding general customers.

## 10. Next exact checks

1. Recheck current Production deployment and `/ready`.
2. Have the owner open the authenticated Instagram integration page; inspect `GET /status` and `GET /accounts` responses without sharing secrets.
3. Verify the account remains connected after browser refresh.
4. Verify webhook configuration and account-level subscription in Meta.
5. Run one inbound DM and one inbound comment using test identities; confirm database persistence and tenant isolation.
6. Keep real outbound replies/content publication disabled during testing until a separate explicit authorization is recorded.
