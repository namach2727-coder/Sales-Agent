# SEO Growth F1 — customer onboarding implementation and release gates

> Current continuation: **0029 + pilot administration implemented; temporary PostgreSQL migration verified; source UAT still 0027 and awaiting an explicit migration decision.** See [the current pilot runbook](SEO_GROWTH_F1_PILOT_ADMIN_2026-11-01.md). The sections below preserve the earlier onboarding-only checkpoint and its then-current validation/hosting observations; claims of no admin or no PostgreSQL rehearsal are historical.

## Earlier onboarding checkpoint (preserved history)

2026-11-01. Owner-authorized development continuation. **DRAFT Backend PR #121 and Frontend PR #71; neither merged nor deployed by this task.** This supersedes the F0-only status in the original foundation proposal. The product remains a pilot implementation, not a commercially available service.

## Implemented customer story

Existing DirectPilot login → choose an authorized tenant and workspace (without consulting Instagram subscriptions) → explicit read-only Google consent → same-origin callback → select an actual Google-granted Search Console property → retain the site in this workspace → explicitly disconnect a site or its Google connection.

- Python/FastAPI modular monolith and existing RBAC are preserved. No new service, cloud resource or paid provider.
- A distinct expiring `seo_access_grants` record is required for each workspace. It controls max sites (1–20) and max Google connections (1–10). There is no automatic grant from Instagram, catalog change, price, subscription activation or public grant-administration endpoint. Pilot grant administration is a remaining review/setup item.
- Four additive tables: `seo_access_grants`, `seo_oauth_attempts`, `seo_google_connections`, `seo_sites`. Proposed Alembic head `0028_seo_google_onboarding`, parent `0027_traceable_receipt_versions`. No seeded grants, customers, plans or prices. Populated SEO tables block destructive downgrade. Historical orders, receipts, media and memberships are preserved.
- Public connection/site IDs are opaque UUIDs. Composite foreign keys bind stores to tenants and sites to the exact connection scope. Normal-user cross-scope access returns non-disclosing 404. Connection credentials belong to the connecting user within that workspace; a colleague's credential cannot be selected by guessing its ID.

## Actual HTTP contract

Let `P=/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/seo`.

| Method | Route | Result / gate |
|---|---|---|
| GET | `P/status` | Enabled/configured/access flags, own sanitized connection, max sites |
| POST | `P/google/connect` | Existing authentication, authorized scope, explicit SEO grant, CSRF; short-lived Google URL and expiry |
| GET | `/api/v1/seo/google/callback` | Original authenticated session, one-use state, PKCE; fixed 303 to `/dashboard/seo` with status and authorized opaque scope |
| GET | `P/google/{connection_public_id}/properties` | Refresh credential server-side; Google's current authorized site IDs and permissions |
| POST | `P/sites` | `connection_public_id` and selected `property_id`; Google access rechecked before quota-locked persistence |
| GET | `P/sites?limit=20&offset=0` | Bounded workspace-scoped site list; limit max 100 |
| POST | `P/sites/{site_public_id}/disconnect` | Authorized explicit local stop; audit; no Google grant revocation |
| POST | `P/google/{connection_public_id}/disconnect` | Delete stored credential, cancel attempts, pause linked sites; optional `revoke_google` |

Errors retain the existing `{detail:{code,message}}` shape. API responses expose no refresh/access credential, verifier or raw OAuth code. Site `sync_status` is explicitly `not_started`; there are no invented metrics, successful-sync dates or ranking forecasts. The earlier unscoped frontend contract remains a historical proposal, not the route implementation.

## Security and lifecycle

- OAuth state is stored only as SHA-256; encrypted PKCE plus session digest bind the attempt to tenant/store/user and the originating session. State expires in ten minutes. Five starts per user/workspace per ten minutes; quota/start writes use a store-row lock.
- The callback performs an atomic compare-and-set and **commits consumption before Google exchange**. Failure, timeout and replay cannot reuse the state. Starting over or disconnecting cancels prior attempts, including an in-progress exchange. Final persistence checks cancellation, scope and entitlement again.
- Dedicated Fernet key, explicit key version and encrypted payload context bind every secret to tenant/store/user/purpose. Access tokens stay transient. Missing refresh consent never reuses an old account's credential. Reconnecting marks old sites disconnected until explicit Google-verified selection.
- The callback is a fixed same-origin `/api/v1/seo/google/callback` through the existing API proxy. Cookie SameSite=Lax is required for Google's top-level return. Frontend origin is configuration, never derived from a caller's Host or return URL.
- Browser mutations require exact configured Origin plus `X-CSRF-Token: seo`; existing CORS rules apply. The header is a non-secret custom-request marker, not a bearer token. No browser credential storage is added.
- Provider calls target fixed Google hosts. No arbitrary website crawl or user-provided URL fetch is implemented. Google-granted site access is not described as ownership for full/restricted users.
- Local disconnect remains available after pilot expiry, feature disabling or missing OAuth/key configuration (while authenticated scope and trusted frontend Origin remain required). Stored refresh credentials are erased. Google revocation is optional, reports `revoked` / `unconfirmed` / `not_requested`, and the UI warns that revocation may affect other DirectPilot connections for the same Google account.
- Callback responses are no-store/no-referrer and auth query values are removed before app-server access logging. Existing application logging suppresses HTTP/token URLs. **Reverse-proxy/platform auth-route query redaction remains a release gate**, not a claimed verification.
- Key rotation currently fails closed on version mismatch. A multi-key re-encryption operation, automated retained-data deletion and general OAuth-attempt retention tooling are not implemented; review before public scale. Used/cancelled PKCE ciphertext is removed immediately; no raw token appears in audit.

## Configuration — names only

Backend defaults off. Configure only in a dedicated UAT secret store; never copy the operator service-account JSON or production secrets into this module.

| Setting | Purpose |
|---|---|
| `SEO_GROWTH_ENABLED` | Default false; explicit pilot feature gate |
| `SEO_GOOGLE_CLIENT_ID` | Dedicated Google Web OAuth client |
| `SEO_GOOGLE_CLIENT_SECRET` | Backend secret, separate per environment |
| `SEO_GOOGLE_REDIRECT_URI` | Exact registered same-origin callback URI above |
| `SEO_FRONTEND_ORIGIN` | Exact UAT origin; HTTPS except local development tests |
| `SEO_TOKEN_ENCRYPTION_KEY` | Independent Fernet key, backend secret |
| `SEO_TOKEN_KEY_VERSION` | Explicit current key version, default v1 |
| `NEXT_PUBLIC_SEO_GROWTH_ENABLED` | Frontend non-secret build flag, default false; scope to reviewed UAT only |

No provider secrets, environment changes, database writes or Google consent were performed by this task. The tests generate their own synthetic secret material in disposable databases.

## Verification evidence

- Original F0 tests rerun: 29 passed. Final focused SEO tests including F1: **60 passed**. Coverage includes session/user/state binding, expiry, durable replay denial across DB sessions, cancelled in-flight exchange, rate limits, site grant/quota, cross-scope denial, revoked versus transient Google errors, reconnect, disconnect with expired entitlement or missing OAuth/key settings, CSRF, duplicate callback parameters and credential-free responses/audit.
- Full backend regression before the final two cleanup/parameter cases: **1003 passed, 7 skipped**. Final full-source run is recorded in the final verification line below; skipped PostgreSQL tests are not claimed as PostgreSQL acceptance.
- Migration policy: one linear head, fresh temporary SQLite upgrade, drift and base→head→base→head PASS. Thirty focused migration/deployment checks PASS. All new PostgreSQL DDL compiles. Derived schema deltas: four tables, four sequences, 22 indexes and 23 constraints; CI disposable-schema expectations updated accordingly. No actual Neon or PostgreSQL migration occurred here.
- Frontend: **290 tests passed**, including rendered React onboarding/property selection and successful-write/failed-refresh handling; TypeScript and changed-file ESLint PASS. Standard `next build --webpack` PASS with default-disabled flag and UAT-enabled flag. Local production HTTP `/dashboard/seo` returns 200 with noindex/nofollow and the anonymous account-check shell.
- Full frontend lint has one **pre-existing error in unchanged `components/admin-seo.tsx:74`**, plus existing warnings. Operator SEO code was intentionally left intact. This task does not claim whole-repository lint PASS.
- Real Google OAuth, Google account switching, provider revocation, proxy cookie behavior, browser/mobile visuals, live PostgreSQL concurrency, cloud UAT and production are **not verified**. Google data is synthetic; the rendered UI test is not a real browser or Google session.

## Remaining release work

1. Review both DRAFT PRs and the pilot-grant administration policy/tooling. Public commercial billing remains F5.
2. Configure dedicated UAT Google OAuth/consent and API access, registered callback, privacy/data-use disclosure and independent token key privately. Check Google's verification requirements for the selected public-use scopes before external onboarding.
3. Verify UAT identity, backup/restore readiness and migration plan; explicitly authorize any populated-environment migration. Apply reviewed schema only to isolated UAT, then deploy backend and frontend with UAT-scoped flags. Do not merge the entire frontend UAT branch into Production.
4. Real customer acceptance: log in, connect correct Google account, deny/retry consent, inspect authorized properties, select one, reload and verify isolation, disconnect, revoke and reconnect. Verify mobile navigation/selectors, keyboard focus and mutation/timeout states.
5. Scheduled ingestion and evidence-aware reporting remain F2. No metric-summary/opportunity route is implemented here. CMS preview/approval/rollback remains a separate authorized future adapter; no customer website is edited by GSC onboarding.

Official sources checked for this implementation:
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/webmaster-tools/v1/sites/list

## Final verification

Latest broad backend regression: **1004 passed, 7 skipped, one configuration-template test failed** because the new empty SEO settings had not been mirrored into `.env.dev.example`. The dev template was corrected without changing runtime code. The complete configuration-profile suite was then rerun: **14 passed, zero failed**. Final focused SEO suite: **60 passed**. No known backend failure remains from these checks; do not describe the latest broad invocation as a zero-failure run. A new exact-commit CI result is separate evidence.


## Post-push hosting snapshot

Code SHA a941ee8903341a5d4974723202f95e1dbaf2e2b4 automatically produced Vercel backend Preview dpl_8dyA8f6J5pEqm33FQaN5G2am71HH, READY, feature ref, target null. This was automatic Git integration, not an explicit release or real API/DB/OAuth acceptance. Frontend code SHA 4226e0fe02283514db3584e819c3718b87f8e7d3 preview builds are blocked by Vercel build-rate-limit. Canonical frontend aliases are on independent existing main e12727f and UAT eda6143, not the F1 UI. No production promotion or live database/env change was performed. Remote intended-file blob hashes matched the local tested source (30 backend / 14 frontend). GitHub mergeability reports dirty despite a verified clean native merge-tree from the current backend base; review this hosted-state inconsistency before any future merge.
