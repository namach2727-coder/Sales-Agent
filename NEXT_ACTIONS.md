# DirectPilot Next Actions

> Execution queue. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-07.

## P0 — UX/Auth Production Promotion

Status: **PASS**

### Verified — Do Not Repeat Without Regression Evidence

- Production backend deployed to `84b7df6196fe380fad21a3791e3160840c098602`.
- Production Render deployment `dep-db2ufns9v7es73aarbg0`: LIVE.
- `APP_ENV=production`: PASS.
- Production PostgreSQL connectivity: PASS.
- Migration current-head verification: PASS.
- Application startup: PASS.
- Production frontend `main` advanced by fast-forward to `1f82494f87fe39f0fb2e22043adfd75f7735668c`.
- Vercel status for the Production SHA: SUCCESS / Deployment completed.
- Owner-confirmed Production customer and admin smoke: PASS.
- UAT acceptance for the same release: PASS.
- Frontend exact-candidate validation: 156/156 tests PASS, type-check PASS, lint PASS, build PASS, diff check PASS, secret scan PASS.
- Backend GitHub CI: test PASS, docker-build PASS, postgres-smoke PASS.
- Forgot Password remains BLOCKED.
- Meta E2E remains BLOCKED_EXTERNAL / deferred.
- No Production Meta/payment/database/environment-variable configuration was changed during the promotion.

P0 is closed.

## P1 — SEO Phase 2 Measurement & Authority

Status: **PRODUCTION PASS — MEASUREMENT OPEN**

- Production/UAT frontend SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`.
- Vercel Production deployment: SUCCESS.
- Live Production audit: five priority pages, 0 critical/high/medium/low issues.
- Keep Preview/UAT non-indexable.
- Do not make daily SEO rewrites based on immature data.
- Re-check after Google has recrawled changed pages and a meaningful settled window exists.
- Compare against baseline: 14 clicks / 315 impressions / 4.44% CTR / avg position 40.30.
- Priority query themes: ربات دایرکت هوشمند اینستاگرام، قیمت دایرکت هوشمند اینستاگرام، آموزش دایرکت هوشمند، پاسخ خودکار به کامنت اینستاگرام، اتوماسیون دایرکت اینستاگرام.
- Next growth action: earn relevant editorial links and publish supporting content that links internally to the commercial owner pages.

## P1 — Production Database Durability Before Real Customers

Status: **OPEN — PRIORITY**

Current Production PostgreSQL:

- Database: `directpilot-production-db`
- ID: `dpg-db0escm0tbcc73fhig2g-a`
- Plan: FREE
- Expiry: `2026-11-02T11:59:46.610475Z`
- HA: disabled
- Read replicas: none

Required before real-customer onboarding:

1. Choose a durable Production database plan/target.
2. Obtain explicit owner approval before any paid infrastructure change.
3. Define migration/cutover procedure.
4. Establish backup policy.
5. Execute and verify a restore test.
6. Record RPO/RTO expectations appropriate for the pilot.
7. Keep Production/UAT databases isolated.
8. Do not weaken external access controls merely for inspection.

Do not mark `PRODUCTION_DATABASE_DURABILITY` or `BACKUP_RESTORE_ACCEPTANCE` PASS until runtime evidence exists.

## P1 — Payment Provider Environment Verification

Status: **OPEN**

- Verify UAT sandbox vs Production provider base URLs.
- Verify callback bases by environment.
- Verify provider credentials/configuration without printing secret values.
- Preserve backend-authoritative payment/subscription activation.
- Never blindly retry ambiguous provider writes.
- Keep real provider transaction acceptance as a separate gate from route/source presence.
- Do not alter Production commercial scope: only `AUTOMATION_V1` is currently verified as purchasable.

## P1 — LLM Environment Verification

Status: **OPEN**

- Verify provider/model configuration independently by environment.
- Verify keys remain backend-only.
- Preserve:
  - `GROQ_CONTEXT_LENGTH=4096`
  - `GROQ_MAX_OUTPUT_TOKENS=256`
- Confirm deterministic exact-match automation still performs ZERO AI work.

## P1 — Meta / OAuth

Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS — OUTBOUND E2E OPEN**

Verified:
- Production OAuth through the UAT relay: PASS.
- UAT webhook relay: PASS.
- Production inbound account/store resolution, conversation creation, persistence and processing: PASS.
- Backend safety runtime `91250140...` is LIVE in UAT (`dep-db33f1qd0e5s73f0bk00`) and Production (`dep-db33funavr4c739lm9v0`).
- GitHub CI for this runtime: test PASS, docker-build PASS, postgres-smoke PASS.
- Production `META_SEND_ENABLED=false`.
- Production environment validation now requires exactly one `META_SEND_ALLOWED_ACCOUNT_IDS` entry whenever send is enabled.

Observed blocker:
- `قیمت` matched no deterministic Production AutomationRule.
- AI fallback failed with `llm_provider_configuration_error`.
- This does not invalidate Meta transport/inbound acceptance.

Next exact steps:
1. In Production, create/enable a harmless deterministic rule:
   - `trigger_type=DM_KEYWORD`
   - `match_type=EXACT`
   - keyword `قیمت`
   - `action_type=SEND_MESSAGE`
   - fixed non-sensitive reply
2. Resolve the connected pilot `instagram_account_id` through the authenticated tenant/store Instagram connection read API. Do not open the Production DB external allowlist.
3. Set `META_SEND_ALLOWED_ACCOUNT_IDS` to exactly that one ID while `META_SEND_ENABLED=false`.
4. Verify the resulting Production deployment remains healthy.
5. Set `META_SEND_ENABLED=true`.
6. From the second Instagram account, send `قیمت` exactly once.
7. Verify deterministic match, exactly one provider delivery, dedupe and no own-message echo loop.
8. Return `META_SEND_ENABLED=false` immediately if routing, account restriction or echo behavior differs from expectation.
9. Verify Production LLM separately before any AI-fallback acceptance test.

Do not:
- enable Production send before the deterministic rule and one-account allowlist are ready,
- configure zero or multiple Production allowlist entries,
- copy UAT encrypted token rows or encryption key,
- weaken Production DB networking for inspection,
- treat the current LLM configuration error as a Meta transport failure.

## P1 — Forgot Password / Recovery

Status: **BLOCKED**

- No verified recovery delivery provider exists.
- Do not ship a fake or frontend-only recovery flow.
- Before implementation, select and verify an email/SMS delivery provider, secure single-use recovery token lifecycle, expiry, replay prevention, audit behavior and session-revocation policy.

## P1 — Local Workstation Reconciliation

Status: **OPEN**

Before old-laptop handoff:

- Preserve all unrelated dirty frontend/backend work.
- Do not use `git reset --hard`, `git clean`, force push, auto-stash or history rewrite.
- Reconcile the old frontend local-only `4733d9a...` commit against authoritative remote `main=4a1f8bb...`.
- Confirm all required local-only environment files/data are securely migrated or reproducible without exposing secret values.
- Prefer fresh SSH credentials on the replacement machine; revoke old-device credentials after successful migration.

## P2 — Payment Acceptance

- Run a controlled real provider acceptance only after environment configuration is verified.
- Validate callback authenticity, idempotency, duplicate-callback behavior and ambiguous-result handling.
- Review high-risk card/payment data handling before real-customer launch.

## P2 — Future Product Work

Story Product Automation remains deferred until Production durability and current integration/payment readiness gates are closed.

Do not implement Story Product Automation opportunistically during readiness work.
