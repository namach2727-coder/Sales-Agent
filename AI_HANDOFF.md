# DirectPilot AI Handoff

> **PRIMARY CROSS-CHAT CONTINUITY AUTHORITY**
>
> Read this file first in every new DirectPilot session.
> Chat history is not the project Source of Truth.
>
> Read order:
> 1. `AI_HANDOFF.md`
> 2. `PROJECT_ROADMAP.md`
> 3. `DECISIONS.md`
> 4. `CURRENT_STATE.md`
> 5. `NEXT_ACTIONS.md`
>
> Evidence rule: verified runtime/deployment state > deployed commit > repository source > continuity documents > old chat history.
> If evidence conflicts with a document, verify reality first and then correct the document.
>
> Last reconciled: 2026-10-07

## Current Production State

### Backend

- Repository: `namach2727-coder/Sales-Agent`
- Branch: `backend-main`
- Accepted runtime-code SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Current deployed Git SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Production Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Verified LIVE deployment: `dep-db33funavr4c739lm9v0`
- `APP_ENV=production`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration one-head/current-head verification: PASS
- Application startup: PASS
- Render auto-deploy: OFF
- GitHub CI for `91250140...`: test PASS, docker-build PASS, postgres-smoke PASS
- Production outbound safety guard is runtime-enforced: when `META_SEND_ENABLED=true`, `META_SEND_ALLOWED_ACCOUNT_IDS` must contain exactly one pilot account.

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- Production SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
- UAT SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
- Public Production domain: `https://directpilot.ir`
- Public UAT domain: `https://uat.directpilot.ir`
- Vercel Production status for current SHA: SUCCESS — Deployment has completed
- Authenticated Production smoke from the prior Auth/UX release: PASS.

## Current UAT State

### Backend

- Render service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Verified LIVE deployment: `dep-db33f1qd0e5s73f0bk00`
- Deployed SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- `APP_ENV=uat`: VERIFIED
- Database connectivity: PASS
- Migration/current-head verification: PASS
- Application startup: PASS

### Frontend

- UAT branch SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
- Vercel deployment for current UAT SHA completed successfully.
- Owner-confirmed UAT functional acceptance: PASS.

## Latest Release — SEO Phase 2

Status: **PRODUCTION PASS — VERCEL SUCCESS / LIVE ON-PAGE AUDIT CLEAN**

Accepted frontend:
`4a1f8bb1812ce942e055c7f2c810f7d719939ab8`

Scope:
- commercial title/description/H1 refinement,
- stronger dedicated landing pages for direct automation, comment automation and comment-to-DM,
- corrected trial messaging to the backend-authoritative 14-day / 3-automation Automation Trial,
- Pricing structured data,
- long-tail solution-page expansion,
- smart-direct article refreshed against real Search Console queries,
- Vercel Preview/UAT set to noindex with preview robots blocking and empty preview sitemap.

Search Console baseline before the release, settled through 2026-10-04:
- clicks: 14
- impressions: 315
- CTR: 4.44%
- average position: 40.30

Search Console priority URLs were already submitted/indexed and robots-allowed before release. The Production sitemap was resubmitted on 2026-10-07 and accepted by Search Console; indexing/ranking changes require a later Google recrawl and settled-data window.

Live Production on-page audit after SEO Phase 2: 5 priority pages audited; 0 critical, 0 high, 0 medium and 0 low issues. All 5 returned HTTP 200, were indexable and self-canonical, with structured data present.

## Previous Release — Authenticated Workspace UX + Account Security

Status: **PRODUCTION PASS**

Accepted backend:
`84b7df6196fe380fad21a3791e3160840c098602`

Accepted frontend:
`1f82494f87fe39f0fb2e22043adfd75f7735668c`

UAT acceptance PASS:

- Session persistence
- Auth routing
- Login CTA after auth
- Logout — customer
- Logout — admin
- Customer categorized navigation
- Admin categorized navigation
- Settings dirty state
- Account & Security
- Password change
- RTL desktop
- RTL mobile
- Regression smoke

Frontend validation before Production promotion:

- `npm test`: 156/156 PASS
- `npm run type-check`: PASS
- `npm run lint`: PASS
- `npm run build`: PASS
- diff check: PASS
- secret scan: PASS

Production smoke after deployment — owner confirmed PASS:

- Customer login -> Dashboard
- Customer F5/session persistence
- Authenticated `/login` -> Dashboard
- Customer navigation
- Settings dirty state
- Customer Account & Security
- Customer logout/session revocation
- Platform Admin login -> `/admin`
- Admin F5/session persistence
- Authenticated admin `/login` -> `/admin`
- Admin navigation
- Admin Account & Security
- Admin logout/session revocation

Still not PASS:

- Forgot Password: BLOCKED — no verified recovery delivery provider
- Meta E2E: BLOCKED_EXTERNAL / owner-deferred

## Verified Authentication Contract

- Browser auth uses the server-authoritative HttpOnly session contract.
- Valid sessions persist across normal refresh/navigation and restore through `/auth/me`.
- Authenticated customer landing route: `/dashboard`.
- Authenticated platform-admin landing route: `/admin`.
- Unauthenticated protected routes redirect to `/login`.
- Login CTA is hidden after authentication.
- Customer/admin logout revokes backend session state.
- Password change requires current password, enforces backend policy and revokes all sessions.
- Session listing/revoke APIs do not expose raw session tokens.
- Forgot-password recovery must not be implemented until a verified delivery provider and secure recovery-token lifecycle exist.

## Commercial Scope

Production sale scope remains only:

`AUTOMATION_V1`

Verified public policy:

- Price: 4,900,000 IRR
- Duration: 30 days
- Automation limit: 20
- Instagram account limit: 1
- AI reply limit: 0

Trials:

- `AUTOMATION_TRIAL`: active, not purchasable
- `AI_ASSISTANT_TRIAL`: active, not purchasable

Do not publish paid `AI_ASSISTANT_V1` without a new explicit product decision and verified source/runtime change.

## Environment Separation

Status: **PASS — DO NOT REBUILD**

- Production and UAT have separate domains.
- Separate Render backend services.
- Separate `APP_ENV`.
- Separate backend upstream routing.
- Separate databases.
- Same-origin browser API remains `/api/v1/*`.
- Existing environment separation should only be revisited if new regression evidence appears.

## Meta / OAuth

Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E OPEN**

- Owner-approved UAT -> Production Meta relay remains the pilot workaround while Meta Developer settings are inaccessible.
- Production OAuth through the relay: PASS.
- UAT webhook relay -> Production: PASS.
- Production inbound routing, account resolution, conversation creation, message persistence and webhook processing: PASS.
- The live test message `قیمت` reached Production but matched no deterministic AutomationRule; AI fallback then failed with `llm_provider_configuration_error`.
- This is not a Meta transport failure. Production LLM verification remains a separate gate.
- Current accepted backend runtime is `91250140...` in both UAT and Production.
- Production deployment `dep-db33funavr4c739lm9v0`: LIVE; APP_ENV/DB/migration/startup PASS.
- UAT deployment `dep-db33f1qd0e5s73f0bk00`: LIVE; APP_ENV/DB/migration/startup PASS.
- Production outbound remains fail-closed with `META_SEND_ENABLED=false`.
- Runtime now refuses Production startup with send enabled unless `META_SEND_ALLOWED_ACCOUNT_IDS` contains exactly one pilot Instagram account.
- Do not copy UAT encrypted token rows or the UAT encryption key into Production.
- Next gate: create/enable one deterministic `DM_KEYWORD` exact-match rule for `قیمت`, identify and configure exactly the connected pilot account in the send allowlist, then enable Production send only for one controlled outbound E2E.

## Current Priority / Blocker

No release blocker remains for the Authenticated Workspace UX release.

The highest-priority Production readiness blocker is database durability:

- Current Production Free PostgreSQL expires `2026-11-02`.
- Do not onboard real customers before durable database + backup/restore acceptance.
- No paid infrastructure change without explicit owner approval.

Other open gates:

- `PAYMENT_PROVIDER_ENVIRONMENT_SPLIT`
- `LLM_ENVIRONMENT_VERIFICATION`
- real payment-provider acceptance
- Forgot Password recovery provider
- Meta E2E when owner resumes Meta work

## Local Workstation Safety

Important known frontend local state:

- During release preparation, local-only commit `4733d9a7f8b942486ca221c1dba1564e6cb34d2b` was accidentally created on the old workstation's local `main`.
- It was NOT pushed.
- Remote `main` is authoritative at `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`.
- The old workstation may still contain unrelated dirty work.
- Do not reset, clean, auto-stash, force-push, rebase or rewrite history automatically.
- Reconcile/preserve local-only work explicitly before old-laptop handoff.

## Next Exact Action

1. In Production, create/enable one deterministic AutomationRule:
   - trigger: `DM_KEYWORD`
   - match: `EXACT`
   - keyword: `قیمت`
   - action: `SEND_MESSAGE`
   - harmless fixed reply
2. Resolve the connected Production pilot Instagram account ID through an authenticated tenant/store connection read; do not weaken the Production DB external allowlist.
3. Set `META_SEND_ALLOWED_ACCOUNT_IDS` to exactly that one account while keeping `META_SEND_ENABLED=false`.
4. Verify Production starts cleanly with the restricted allowlist.
5. Set `META_SEND_ENABLED=true`, send `قیمت` once from the second Instagram account, and verify deterministic match, one provider delivery, dedupe and no own-message echo loop.
6. Immediately return `META_SEND_ENABLED=false` if routing, allowlist or echo behavior is not exactly as expected.
7. Separately address `PRODUCTION_DATABASE_DURABILITY` / `BACKUP_RESTORE_ACCEPTANCE` before onboarding real customers.

## Important Constraints

- Never expose secret values.
- Never claim deployment, migration, API, database, feature or payment acceptance without evidence.
- Do not repeat PASS/VERIFIED work without regression evidence or a related change.
- Render backend auto-deploy is OFF; Git push does not equal backend deployment.
- Documentation-only commits are not runtime deployments.
- No paid infrastructure/resource without explicit owner approval.
- Preserve unrelated local dirty work.
- Official Meta APIs only.
- Tenant isolation is mandatory.
- Backend remains authoritative for payments, entitlements and subscription state.
- No blind retry of ambiguous external-provider writes.

## Decisions That Must Not Be Revisited

- Modular Monolith for MVP.
- Human Takeover suppresses automation and AI.
- Deterministic exact match performs ZERO LLM/PromptBuilder/knowledge/AI work.
- AI execution requires entitlement.
- Backend-authoritative commerce/subscription activation.
- Immutable purchase/order snapshots.
- No blind retry of ambiguous external-provider writes.
- UAT/Production environment separation is complete.
- Current V1 sale scope is Automation V1.
- Production Free PostgreSQL is pilot infrastructure only.

## Current Resume Marker

```text
PROJECT: DirectPilot
DATE: 2026-10-07

ACTIVE_WORKSTREAM:
META_PRODUCTION_OUTBOUND_E2E

READINESS_BLOCKER:
PRODUCTION_DATABASE_DURABILITY_AND_BACKUP_RESTORE

LATEST_BACKEND_SAFETY_RELEASE:
PRODUCTION_SINGLE_PILOT_SEND_ALLOWLIST_GUARD

LATEST_RELEASE_STATUS:
UAT PASS / PRODUCTION LIVE / CI PASS / OUTBOUND E2E OPEN

PRODUCTION_BACKEND:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
DEPLOYMENT: dep-db33funavr4c739lm9v0
STATUS: LIVE
APP_ENV: production
DB: PASS
MIGRATION: PASS
STARTUP: PASS
META_SEND_ENABLED: false
SEND_GUARD: EXACTLY_ONE_PILOT_REQUIRED_WHEN_ENABLED

PRODUCTION_FRONTEND:
SHA: 4a1f8bb1812ce942e055c7f2c810f7d719939ab8
BRANCH: main
VERCEL: SUCCESS
OWNER_SMOKE: PASS

UAT_BACKEND:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
DEPLOYMENT: dep-db33f1qd0e5s73f0bk00
STATUS: LIVE

UAT_FRONTEND:
SHA: 4a1f8bb1812ce942e055c7f2c810f7d719939ab8
BRANCH: UAT
ACCEPTANCE: PASS

META_E2E:
PRODUCTION OAUTH PASS
INBOUND RELAY PASS
OUTBOUND E2E OPEN

OBSERVED_OUTBOUND_BLOCKER:
NO DETERMINISTIC RULE FOR قیمت
LLM FALLBACK CONFIGURATION ERROR

PRODUCTION_DB:
FREE / EXPIRES 2026-11-02
DURABILITY: OPEN
BACKUP_RESTORE: OPEN

NEXT EXACT ACTION:
Create/enable the Production DM_KEYWORD EXACT rule for قیمت with a harmless fixed reply. Then resolve the connected pilot instagram_account_id through the authenticated tenant/store API, configure exactly that one ID in META_SEND_ALLOWED_ACCOUNT_IDS while send stays disabled, and only then run one controlled outbound E2E.
```

