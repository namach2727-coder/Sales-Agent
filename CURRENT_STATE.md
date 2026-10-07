# DirectPilot Current State

> Snapshot of verifiable current state. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-07.

## Repository State

### Backend

- Repository: `namach2727-coder/Sales-Agent`
- Branch: `backend-main`
- Latest accepted runtime-code commit: `84b7df6196fe380fad21a3791e3160840c098602`
- Continuity-document commits are newer on `backend-main`; they must not be described as deployed application code.
- Commit message: `feat(auth): add secure password and session management`
- GitHub CI for this commit: `test` PASS, `docker-build` PASS, `postgres-smoke` PASS.

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- Both remote branches currently point to the accepted Frontend release:
  `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Commit message: `fix: stabilize UAT release candidate`
- This release contains the accepted authenticated-workspace redesign plus the two-file stabilization fix.

## Production Backend

- Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Latest verified LIVE deployment ID: `dep-db2ufns9v7es73aarbg0`
- Deployed Git SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- Status: LIVE
- `APP_ENV=production`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration one-head/current-head verification: PASS
- Application startup: PASS
- Render auto-deploy: OFF
- No Meta/payment/database/environment-variable changes were made as part of this Production promotion.

## Production Frontend

- Public domain: `https://directpilot.ir`
- Production branch: `main`
- Deployed/accepted SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Vercel GitHub status: SUCCESS — `Deployment has completed`
- Current Production SEO deployment status target reference:
  `https://vercel.com/mohcenp-9857s-projects/directpilot-web/4WadnbNq9X79RjTx8fANyZWuwN8g`
- A canonical `dpl_...` deployment ID was not independently recovered in this checkpoint; do not invent one.
- Owner-confirmed Production smoke after deployment: PASS.

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
- Verified LIVE deployment ID: `dep-db1mq5vavr4c73cmjgo0`
- Deployed SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- Status: LIVE
- `APP_ENV=uat`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration/current-head verification: PASS
- Application startup: PASS
- Auto-deploy: OFF

## UAT Frontend and Acceptance

- Public domain: `https://uat.directpilot.ir`
- UAT branch SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Vercel deployment status for this SHA: SUCCESS.
- Owner-confirmed UAT functional acceptance: PASS.

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

- Status: PARTIAL / BLOCKED_EXTERNAL.
- Shared Meta App pilot decision remains in force.
- Production and UAT use environment-specific OAuth redirect URIs.
- Production Meta variables were previously configured without documenting secret values.
- Real OAuth callback + webhook/DM E2E remains OPEN externally.
- Owner explicitly paused Meta work. Do not resume unless explicitly requested.

## LLM / Payment Verification

- LLM environment verification remains OPEN.
- Payment-provider environment separation/verification remains OPEN.
- Real provider transaction acceptance remains a separate gate from source/route presence.

## Local Working-Tree Safety

- The old frontend workstation may still contain unrelated dirty work.
- During promotion, a local-only commit `4733d9a7f8b942486ca221c1dba1564e6cb34d2b` was accidentally created on local `main` and was NOT pushed.
- Remote `main` is authoritative at `da73f8055f676aaa1a07901fe351d20f4455ad5a`.
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
