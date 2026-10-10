# DirectPilot Current State

> Snapshot of verifiable current state. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-10.

## Repository State

### Backend

- Repository: `namach2727-coder/Sales-Agent`
- Branch: `backend-main`
- Latest accepted deployed runtime-code commit: `91250140cccc7c9be9102c2d6e17e6775a836f24`.
- This runtime includes the Meta relay bridge and Production single-pilot send-allowlist guard.
- GitHub CI: test PASS, docker-build PASS, postgres-smoke PASS.
- Later docs-only commits must not be described as deployed application code unless Render evidence matches them.

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- Both remote branches point to `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.

## Production Backend

- Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Latest verified LIVE deployment ID: `dep-db33funavr4c739lm9v0`
- Deployed Git SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=production`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration one-head/current-head verification: PASS
- Application startup: PASS
- Render auto-deploy: OFF
- `META_SEND_ENABLED=false` remains in force.
- Runtime now requires exactly one `META_SEND_ALLOWED_ACCOUNT_IDS` entry if Production send is enabled.

## Production Frontend

- Public domain: `https://directpilot.ir`
- Production branch: `main`
- Deployed/accepted SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`
- Vercel GitHub status: SUCCESS — `Deployment has completed`
- Current Production SEO Phase 2 deployment status target reference:
  `https://vercel.com/mohcenp-9857s-projects/directpilot-web/9xEboR41X9yQmp6wz6Ux9XcPtWfD`
- A canonical `dpl_...` deployment ID was not independently recovered in this checkpoint; do not invent one.
- Auth/UX Production smoke from the previous release remains PASS. It was not repeated for this SEO-only promotion because no authentication/session behavior changed.

### Production Auth/UX Smoke — Owner Confirmed

- Customer login -> Dashboard: PASS
- Customer session persists across F5: PASS
- Authenticated `/login` -> Dashboard: PASS
- Customer categorized navigation: PASS
- Store Settings dirty-state behavior: PASS
- Customer Account & Security: PASS
- Customer logout/session revocation: PASS
- Platform Admin login -> `/admin`: PASS
- Admin session persists across F5: PASS
- Authenticated admin `/login` -> `/admin`: PASS
- Admin categorized navigation: PASS
- Admin Account & Security: PASS
- Admin logout/session revocation: PASS

## UAT Backend

- Render service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Verified LIVE deployment ID: `dep-db33f1qd0e5s73f0bk00`
- Deployed SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=uat`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration/current-head verification: PASS
- Application startup: PASS
- Auto-deploy: OFF

## UAT Frontend and Acceptance

- Public domain: `https://uat.directpilot.ir`
- UAT branch SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`
- Vercel deployment status for this SHA: SUCCESS.
- Prior Auth/UX UAT functional acceptance: PASS. SEO Phase 1 content/UAT review was accepted by the owner for Production promotion.

Accepted UAT criteria:

- Session persistence: PASS
- Auth routing: PASS
- Login CTA after auth: PASS
- Customer logout: PASS
- Admin logout: PASS
- Customer navigation: PASS
- Admin navigation: PASS
- Settings dirty state: PASS
- Account Security: PASS
- Password change: PASS
- RTL desktop: PASS
- RTL mobile: PASS
- Regression smoke: PASS
- Forgot Password: BLOCKED — no verified recovery delivery provider
- Meta E2E: BLOCKED_EXTERNAL / intentionally deferred

Frontend exact-candidate validation before promotion:

- `npm test`: PASS — 156/156
- `npm run type-check`: PASS
- `npm run lint`: PASS
- `npm run build`: PASS
- diff check: PASS
- secret scan: PASS

## Production Database

- Render database: `directpilot-production-db`
- ID: `dpg-db0escm0tbcc73fhig2g-a`
- PostgreSQL: 16
- Status: AVAILABLE
- Plan: FREE
- Expires: `2026-11-02T11:59:46.610475Z`
- High availability: disabled
- Read replicas: none
- External IP allowlist is empty.
- Latest file-recorded migration head: `0023`.
- Deployed startup verifies current migration head.
- Do not weaken the database IP allowlist merely to inspect SQL.
- This database is pilot infrastructure only; real-customer durability remains OPEN.

## Commercial Catalog

Current verified policy:

- `AUTOMATION_V1`: active + purchasable, 4,900,000 IRR, 30 days, automation limit 20, Instagram account limit 1, AI reply limit 0.
- `AUTOMATION_TRIAL`: active trial, not purchasable.
- `AI_ASSISTANT_TRIAL`: active trial, not purchasable.
- Legacy FREE/TRIAL/START/PRO plans: not public purchasable plans.
- No paid `AI_ASSISTANT_V1` is part of the current verified Production sale scope.
- UAT may retain stale/test `AI_ASSISTANT_V1` data; it must not be propagated to Production.

## Authentication / Account Security

The accepted backend release `84b7df6...` adds/validates:

- authenticated password change,
- current-password verification,
- password-policy enforcement,
- all-session revocation after successful password change,
- public session listing,
- own-session revocation,
- no raw session token exposure.

The accepted frontend release exposes categorized authenticated customer/admin workspaces, session-aware routing/CTA behavior, logout, Account & Security, and Settings dirty-state behavior.

Forgot Password remains BLOCKED until a verified recovery provider exists. No fake recovery flow is accepted.

## Environment Separation

Status: PASS.

- Production and UAT remain separate by domain, Render service, `APP_ENV`, backend upstream and database.
- Do not repeat environment-separation work without regression evidence.
- Same-origin browser API contract remains `/api/v1/*`.

## Meta / OAuth

- Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E OPEN**.
- Production OAuth through the owner-approved UAT relay bridge: PASS.
- UAT webhook relay to Production: PASS.
- Production inbound account routing, conversation creation, inbound persistence and webhook processing: PASS.
- Live message `قیمت` did not match a deterministic rule; AI fallback failed with `llm_provider_configuration_error`.
- Production outbound remained disabled; this was not a Meta transport failure.
- Current backend runtime in UAT and Production: `91250140...`.
- Production: `dep-db33funavr4c739lm9v0` LIVE with APP_ENV/DB/migration/startup PASS.
- UAT: `dep-db33f1qd0e5s73f0bk00` LIVE with APP_ENV/DB/migration/startup PASS.
- Production send safety is fail-closed: enabling send requires exactly one pilot account in `META_SEND_ALLOWED_ACCOUNT_IDS`.
- Do not weaken Production database networking to discover the account ID; use the authenticated tenant/store Instagram connection API.
- Next exact gate: deterministic `DM_KEYWORD` exact-match `قیمت` rule + exactly one pilot allowlist entry + one controlled outbound E2E.

## LLM / Payment Verification

- LLM environment verification remains OPEN.
- Payment-provider environment separation/verification remains OPEN.
- Real provider transaction acceptance remains a separate gate from source/route presence.

## Local Working-Tree Safety

- The old frontend workstation may still contain unrelated dirty work.
- During promotion, a local-only commit `4733d9a7f8b942486ca221c1dba1564e6cb34d2b` was accidentally created on local `main` and was NOT pushed.
- Remote `main` is authoritative at `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Do not reset/clean/force the old local checkout; reconcile or preserve dirty work explicitly before laptop handoff/migration.

## SEO Phase 1

- Frontend candidate/deployed SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`.
- UAT Vercel deployment: SUCCESS.
- Production Vercel deployment after fast-forwarding `main`: SUCCESS.
- Production Search Console property: `sc-domain:directpilot.ir`.
- Baseline settled through 2026-10-04: 14 clicks, 315 impressions, CTR 4.44%, average position 40.30.
- Priority observed opportunities include `/blog/instagram-smart-direct`, `/pricing`, `/instagram-comment-automation`, `/instagram-direct-automation`, `/free-instagram-automation`, and `/comment-to-direct`.
- Priority URLs inspected before release were submitted/indexed, robots allowed, fetch successful.
- Production sitemap was resubmitted to Search Console on 2026-10-07; submission accepted with zero warnings/errors at submission time.
- Search Console recrawl and ranking movement are pending by nature and must not be marked PASS immediately after deployment.
- Preview/UAT indexing isolation is implemented: non-production metadata noindex/nofollow, preview robots disallow all, preview sitemap empty.

## SEO Phase 2

- Frontend SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159` on both Production and UAT.
- Vercel Production and UAT exact-SHA deployments: SUCCESS.
- Live Production audit on five priority SEO pages: 0 critical/high/medium/low issues.
- All five pages return HTTP 200, are indexable and self-canonical, have one H1 and valid structured data.
- Ranking/CTR impact remains OPEN until Google recrawls and later Search Console data settles.

### Meta live inbound evidence

- Live inbound test at 2026-10-07T11:31Z: PASS through UAT -> Production relay.
- Production account scope resolved, conversation created, inbound message persisted, webhook accepted and processing completed.
- No warning/error in the processing window.
- Deterministic automation did not match `قیمت`; AI fallback failed with `llm_provider_configuration_error`.
- No outbound provider delivery occurred; Production sending remains disabled.
- Dedupe/echo protection still requires a controlled outbound/retry observation before full Meta E2E PASS.


## Frontend Admin Plan UX — 2026-10-10

- Production/UAT source SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Vercel Production: SUCCESS.
- Fixed plan-creation scroll preservation across form remount.
- Native browser scroll-to-invalid behavior disabled for plan creation; validation errors stay inline.
- Internal plan codes are normalized to uppercase while typing and again in the payload.
- Owner retest: PENDING.


## Admin Customer Automation Management — 2026-10-10

- Frontend Production/UAT SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- UAT Vercel build: SUCCESS.
- Production Vercel build: SUCCESS.
- Admin -> Customers & Stores now allows Platform Super Admin to select an automation-capable store and open **Manage Automation**.
- The panel manages the real tenant/store AutomationRules: trigger, match type, phrases/keywords, response, priority and enabled state.
- Existing scoped backend authorization is reused; no new backend runtime deployment was required.
- Backend remains authoritative for entitlement and rule-count limits.
- Production owner functional retest: PENDING.
