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
- Accepted runtime-code SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- Continuity-document commits are newer on `backend-main`; they are documentation only and must not be described as deployed runtime code.
- Production Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Verified LIVE deployment: `dep-db2ufns9v7es73aarbg0`
- Deployment SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- `APP_ENV=production`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration one-head/current-head verification: PASS
- Application startup: PASS
- Render auto-deploy: OFF
- GitHub CI for `84b7df6...`: test PASS, docker-build PASS, postgres-smoke PASS

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- Production SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- UAT SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Public Production domain: `https://directpilot.ir`
- Public UAT domain: `https://uat.directpilot.ir`
- Vercel Production status for current SHA: SUCCESS — Deployment has completed
- Production SEO deployment status target reference:
  `https://vercel.com/mohcenp-9857s-projects/directpilot-web/4WadnbNq9X79RjTx8fANyZWuwN8g`
- Current canonical `dpl_...` Production deployment ID was not independently recovered in this checkpoint; do not invent one.
- Authenticated Production smoke from the prior Auth/UX release: PASS; not repeated for the SEO-only promotion because no auth/session behavior was changed.

### Database

- Production Render PostgreSQL: `directpilot-production-db`
- Database ID: `dpg-db0escm0tbcc73fhig2g-a`
- PostgreSQL: 16
- Status: AVAILABLE
- Plan: FREE
- Expires: `2026-11-02T11:59:46.610475Z`
- High availability: disabled
- Read replicas: none
- Latest file-recorded migration head: `0023`
- Deployed startup current-head verification: PASS
- Durability for real customers: OPEN

## Current UAT State

### Backend

- Render service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Verified LIVE deployment: `dep-db1mq5vavr4c73cmjgo0`
- Deployed SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- `APP_ENV=uat`: VERIFIED
- Database connectivity: PASS
- Migration/current-head verification: PASS
- Application startup: PASS

### Frontend

- UAT branch SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Vercel deployment for current UAT SHA completed successfully.
- Owner-confirmed UAT functional acceptance: PASS.

## Latest Release — SEO Phase 1

Status: **PRODUCTION DEPLOYED / VERCEL SUCCESS**

Accepted frontend:
`da73f8055f676aaa1a07901fe351d20f4455ad5a`

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

Status: **PARTIAL / BLOCKED_EXTERNAL / OWNER-DEFERRED**

- Shared Meta App pilot decision remains.
- Production OAuth redirect URI:
  `https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback`
- UAT OAuth redirect URI:
  `https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback`
- Production Meta variables were previously added without storing secret values in Git/docs.
- Real OAuth callback + live webhook/DM E2E acceptance remains OPEN.
- Owner explicitly paused Meta work. Do not resume unless explicitly requested.

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
- Remote `main` is authoritative at `da73f8055f676aaa1a07901fe351d20f4455ad5a`.
- The old workstation may still contain unrelated dirty work.
- Do not reset, clean, auto-stash, force-push, rebase or rewrite history automatically.
- Reconcile/preserve local-only work explicitly before old-laptop handoff.

## Next Exact Action

1. Address `PRODUCTION_DATABASE_DURABILITY` and `BACKUP_RESTORE_ACCEPTANCE` before real customers:
   - choose durable target,
   - obtain explicit owner approval for any paid infrastructure,
   - plan cutover,
   - establish backups,
   - verify restore.
2. Then/alongside, verify `PAYMENT_PROVIDER_ENVIRONMENT_SPLIT`.
3. Verify `LLM_ENVIRONMENT_VERIFICATION`.
4. Keep Meta work paused until explicit owner instruction.
5. Keep Forgot Password blocked until a verified recovery provider exists.

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
PRODUCTION_DATABASE_DURABILITY_AND_BACKUP_RESTORE

LATEST_RELEASE:
SEO_PHASE_1

LATEST_RELEASE_STATUS:
PRODUCTION DEPLOYED / VERCEL SUCCESS

PRODUCTION_BACKEND:
SHA: 84b7df6196fe380fad21a3791e3160840c098602
DEPLOYMENT: dep-db2ufns9v7es73aarbg0
STATUS: LIVE
APP_ENV: production
DB: PASS
MIGRATION: PASS
STARTUP: PASS

PRODUCTION_FRONTEND:
SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
BRANCH: main
VERCEL: SUCCESS
OWNER_SMOKE: PASS

UAT_BACKEND:
SHA: 84b7df6196fe380fad21a3791e3160840c098602
DEPLOYMENT: dep-db1mq5vavr4c73cmjgo0
STATUS: LIVE

UAT_FRONTEND:
SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
BRANCH: UAT
ACCEPTANCE: PASS

FORGOT_PASSWORD:
BLOCKED

META_E2E:
BLOCKED_EXTERNAL / DEFERRED

PRODUCTION_DB:
FREE / EXPIRES 2026-11-02
DURABILITY: OPEN
BACKUP_RESTORE: OPEN

NEXT EXACT ACTION:
Monitor the SEO Phase 1 release through the next settled Search Console window while keeping Production database durability + backup/restore as the blocking readiness gate before real-customer onboarding.
```
