# SEO Growth F1 — pilot administration and prepared UAT migration

Owner-authorized development continuation, 2026-11-01. Backend DRAFT [PR #121](https://github.com/namach2727-coder/Sales-Agent/pull/121), branch `feature/seo-growth-commercial-foundation-20261101`; frontend DRAFT [PR #71](https://github.com/namach2727-coder/directpilot-web/pull/71), branch `docs/seo-growth-customer-portal-contract-20261101`. No merge, canonical UAT release, Production promotion, real customer grant, Google credential configuration or customer website edit is performed here. Previous onboarding evidence is retained in `SEO_GROWTH_F1_ONBOARDING_2026-11-01.md`.

## Implemented behavior

An authenticated `platform_super_admin` selects a customer workspace explicitly, reads the current pilot grant and usage, reviews bounded terms, then confirms an audited change. This is internal pilot access, separate from prices, orders and subscriptions.

- GET/POST `/api/v1/admin/seo/pilot-grants`. Scope uses `tenant_public_id` / `store_public_id`; POST also requires `enabled`, `expected_revision`, `duration_days`, `max_sites`, `max_connections`.
- The trusted platform role, the current active database assignment of that exact super-admin role, and current permission are required, including after the store lock. An operator permission cannot replace a revoked super-admin assignment. Customer ownership is insufficient. Body fields cannot override authority. Responses contain no Google credential or session data and use `Cache-Control: no-store`.
- Exact configured Origin and `X-CSRF-Token: seo` are required for writes. The marker is not a bearer credential. Strict payload validation rejects strings for booleans, unknown fields and out-of-range values.
- Access lasts 1–30 days, with 1–20 active sites and 1–10 Google connections. Issuance/renewal requires an active tenant/workspace and the backend feature flag. No automatic grants are seeded. Capacity cannot be reduced below current usage.
- Store locks serialize administrator changes and customer quota writes. Revision 0 creates; later writes require the current revision and return 409 for a stale review. Grant reads refresh ORM state, including the customer check after an in-flight Google request, so an older loaded grant cannot bypass a newly reduced capacity.
- `seo.pilot_access_granted` / `seo.pilot_access_disabled` append the actor and safe before/after terms to existing tenant audit history. Disabling remains available with the feature flag off. It denies subsequent customer SEO operations while retaining history and existing credentials; the customer can still explicitly disconnect and erase their credential. This administrative action does not revoke Google's consent.
- Frontend `/admin/seo-customers` uses the existing HttpOnly session and typed API, role-gated UI, explicit workspace selection and a separate confirmation. Requests capture the reviewed scope/revision, prevent duplicate submissions and do not retry mutations. A successful write remains successful if a secondary read fails; stale/uncertain results require a fresh read before another change.
- The existing private operator `/admin/seo` remains intact. Both SEO feature flags remain off by default; no prices, checkout, scheduled Google ingestion or CMS writes are introduced.

## Migration and entrypoint

New forward-only revision `0029_seo_pilot_revision` follows the published `0028_seo_google_onboarding`; it adds a non-null revision with server default 1 and a positive-value check. Existing pilot expiry, status and capacity are unchanged. A populated grant table blocks downgrade to prevent revision evidence loss. No previously published migration is edited.

The existing `api/index.py` contained literal backslash-n text instead of Python newlines and failed parsing. It now imports the ASGI application correctly; CI compiles `api` alongside `app`, `tools` and `tests`. A local actual entrypoint import verifies the customer callback and admin routes. A hosting build marked READY alone does not verify this entrypoint at runtime.

## Verification

- Final full backend suite: **1025 passed, 7 skipped, zero failures**.
- Final frontend full suite: **293 passed, zero failed**, including 3 rendered admin tests for role denial, explicit scope/confirmation, successful-write/failed-refresh and stale-revision handling. TypeScript, changed-file ESLint and the UAT-flag-enabled Next webpack build pass. Existing full-lint failure in unchanged `components/admin-seo.tsx:74` remains separate.
- SQLite migration policy/drift and base → head → base → head pass. A populated 0028 fixture upgrades to 0029 with the original terms intact and refuses destructive downgrade. Compilation/import checks pass.
- PostgreSQL 18.6: the exact 0027 → 0029 SQL succeeded on the prepared Neon temporary branch. All four tables are empty, revision defaults to 1 / NOT NULL / CHECK >= 1, and the site foreign key binds connection, tenant and store. A separate pre-migration checkpoint is readable at 0027 with SEO tables absent. The source UAT branch remains at 0027 with SEO tables absent.
- Two independent-Session regressions reproduced stale-capacity and revoked-super-admin fallback defects, then passed after the fixes. The capacity case simulates an in-flight provider response; the role case retains an operator permission after the exact super-admin role is revoked. It is not a real PostgreSQL multi-worker load test.
- Google consent, live customer scope/credential lifecycle, platform query-log redaction, proxy cookies, visual browser/mobile acceptance and production are not verified.

## Exact prepared UAT change — owner confirmation required

Reviewable SQL: [`../migrations/SEO_GROWTH_UAT_0027_TO_0029.sql`](../migrations/SEO_GROWTH_UAT_0027_TO_0029.sql).
SHA-256: `742134da2c68f564c789031b73b2a338eae1398f3d31350477c9db0492c0be9a`.
Exact connector completion values and read-only results: [`../migrations/SEO_GROWTH_UAT_0027_TO_0029_PREPARED.json`](../migrations/SEO_GROWTH_UAT_0027_TO_0029_PREPARED.json). No credentials are stored in either artifact.

| Item | Verified value |
|---|---|
| UAT project | `round-shape-42044596` / `directpilot-uat-v2` |
| Database / source branch | `neondb` / `br-spring-dream-arhxt1ji` |
| Source branch name | `production` **inside UAT project**; this is not the separate Production project |
| Prepared migration | `af53e764-685a-4146-97ba-8b81d9a1c279` |
| Temporary branch | `br-jolly-poetry-aroels8l`, verified head 0029 |
| Pre-migration checkpoint | `br-small-hat-ar1zf7mf`, parent LSN `0/3C1FDC8`, verified head 0027 |
| Separate Production project | `billowing-poetry-05589994`; not targeted |

The transaction locks `alembic_version`, asserts exactly one source head at 0027, creates the four additive SEO tables/indexes, adds grant revision, advances the head to 0029 and commits. It seeds no grant, customer, plan or price and contains no DROP/TRUNCATE/DELETE. The connector initially rejected a dollar-quoted guard; the reviewed SQL uses a single-statement revision assertion instead. Failed preparation left no extra branch. The checkpoint was created with the account's existing compute defaults after a suspend-interval override was rejected; no plan or quota was changed.

Before any source application: re-read the source head and prepared metadata, verify the SQL hash and checkpoint readability, and confirm recovery readiness. The project reports a six-hour history window; the retained checkpoint branch is readable and independent of subsequent source writes, but this is not a verified offsite backup or a destructive-restore rehearsal. Preserve it through UAT acceptance. Do not reset or downgrade a populated database.

The Neon `complete_database_migration` instruction is explicit: **"NEVER run autonomously; always ask the user first."** The repository's top continuity rule also says **"Never publish to Production, touch live data/secrets, or switch Meta/Telegram outbound functionality without specific owner approval."** Therefore the next source migration is prepared for review, not applied. After approval, pass the exact migration ID, SQL, database, project, parent and temporary branch values from the JSON to that tool with `apply_changes:true`. If rejected, ask/obtain confirmation to discard with `apply_changes:false`; do not silently delete branches. Completing the prepared migration deletes only its temporary branch; keep the recovery checkpoint until acceptance.

## Remaining gates and next action

1. Obtain the specific UAT migration decision; apply/discard only through the prepared connector flow, then re-read source schema and update the six release documents. This does not enable the service or authorize Production.
2. The UAT backend project is `directpilot-uat-api`; `APP_ENV=uat` is verified. Dedicated SEO environment names and the frontend build flag are absent. The connector did not return a readable UAT database URL, so mapping that secret to this Neon branch is not claimed; verify it privately before deploying the ORM.
3. Google Cloud Auth Clients returned "Site Unavailable" in this session browser, including one reload. No account failure, bot detection or global outage was established. No Google client or consent was configured. Plugin discovery found no demonstrated Google OAuth-client administration capability; no plugin or paid service was installed.
4. Configure a dedicated UAT Web OAuth client, callback/origin, privacy/consent and independent encryption key privately; retain `webmasters.readonly`. Proposed registration: Web application named `DirectPilot SEO Growth UAT`, exact redirect `https://uat.directpilot.ir/api/v1/seo/google/callback`, backend `SEO_FRONTEND_ORIGIN=https://uat.directpilot.ir`, and only the Search Console read scope `https://www.googleapis.com/auth/webmasters.readonly`. These are review values, not applied settings. Verify the actual UAT proxy/upstream and test-user consent setup before enabling. Validate proxy auth-query redaction before real consent.
5. Review/deploy the exact source to isolated UAT only when build capacity and configuration permit, then complete real Google and browser/mobile acceptance. Previous frontend feature previews were blocked by Vercel build-rate-limit. The new frontend code c42a8520ec0a0e254956f892c0049b72607a3665 web Preview is CANCELED by the existing Ignored Build Step (not a ready preview). Its separate automatic private GSC-MCP Preview is ERROR because that project expects docs/seo/gsc-mcp-service, absent on this older feature branch; the error does not establish a production outage. No manual retry loop or unrelated project-setting change is performed. Keep unrelated main/UAT website changes intact.
6. F2 data synchronization/reporting, F5 billing and approval/rollback CMS adapters remain separate work. No automatic SEO edits or ranking outcome is claimed.


## Exact published code and automatic build snapshot

Backend runtime code `862d37c955760073257a516ced18edea45b60d1b` and frontend code `c42a8520ec0a0e254956f892c0049b72607a3665` are published in the existing DRAFT PRs; 28 backend / 7 frontend Git blob hashes match tested source. All four GitHub jobs pass on exact runtime code: general test, PostgreSQL smoke, PostgreSQL18/Neon compatibility and Docker build. Final local full runs passed (1025 backend, 7 skipped; 293 frontend).

Backend automatic feature Preview `dpl_AWNk7ifD4bMuo7mg5ortQtrfN7x6` is READY for exact runtime code, target null. This is not canonical UAT, source database migration or real OAuth acceptance. The same source also auto-triggered an unrelated TelBot Preview, ERROR for an absent configured root. Frontend exact-code web Preview is CANCELED by the existing main/UAT-only ignore rule; its separate GSC-MCP Preview is ERROR for an absent configured root. Website deployment status is reported successful by GitHub, but details are inaccessible (404), so its target is not asserted. No project settings were changed to suppress these statuses.

Canonical web aliases were rechecked: directpilot.ir remains READY at main e12727f and uat.directpilot.ir remains READY at UAT eda6143. The subsequent documentation commit records these code/build observations. Both PRs remain DRAFT/unmerged; original UAT is still 0027, pending explicit migration confirmation. The current backend-main a810228df804976cbccfee39c961239001b422a6 adds only six brand-release documents; their parallel insertions are reconciled in a two-parent feature-branch documentation merge preserving both histories and the single mandatory top rule. Runtime code remains byte-identical to 862d37c. No PR merge or history rewrite is performed.
