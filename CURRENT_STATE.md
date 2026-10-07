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
  `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
- Current frontend commit message: `seo: complete article author organization schema`
- Current frontend includes the previously accepted Auth/UX release plus SEO Phase 1 and SEO Phase 2.

## Production Backend

- Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Latest verified LIVE deployment ID: `dep-db32beom7kps73cpcf50`
- Deployed Git SHA: `b6962c6701897ece4ee4fdda5ffcf7f2ec67da3a`
- Accepted runtime-code SHA: `b8f945db18b45e8ac1f3a8fe0bfda790b12015ab`.
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
- Deployed/accepted SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
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
- Verified LIVE deployment ID: `dep-db31uljncjis73e6gq90`
- Deployed SHA: `b8f945db18b45e8ac1f3a8fe0bfda790b12015ab`
- Status: LIVE
- `APP_ENV=uat`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration/current-head verification: PASS
- Application startup: PASS
- Auto-deploy: OFF

## UAT Frontend and Acceptance

- Public domain: `https://uat.directpilot.ir`
- UAT branch SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`
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

- Status: IN PROGRESS — RELAY BRIDGE DEPLOYED / PRODUCTION OAUTH NEXT.
- Owner approved the relay workaround because Meta Developer configuration is inaccessible.
- Shared Meta App values were copied by the owner from UAT to Production without exposing values in chat; secret readback is not available through the connector.
- Relay runtime SHA: `b8f945db18b45e8ac1f3a8fe0bfda790b12015ab`.
- CI: 871 passed / 7 skipped; docker-build PASS; postgres-smoke PASS.
- UAT deployment `dep-db31uljncjis73e6gq90`: LIVE; APP_ENV/DB/migration/startup PASS.
- Production deployment `dep-db31vu60tbcc738ee1dg`: LIVE; APP_ENV/DB/migration/startup PASS.
- Production uses the already-registered UAT provider redirect URI and prefixes OAuth state with `production.`.
- UAT OAuth relay target points to the Production callback and accepts only `production.` state.
- UAT webhook relay code is deployed, but its target is empty; existing UAT webhook processing continues until Production OAuth succeeds.
- Production relay targets are empty, preventing relay loops.
- Production outbound remains `META_SEND_ENABLED=false`.
- Production DB external allowlist remains untouched/empty.
- Next user action: Production dashboard -> Instagram -> official connection. After success, enable UAT webhook relay and verify inbound routing before any controlled outbound send.

## LLM / Payment Verification

- LLM environment verification remains OPEN.
- Payment-provider environment separation/verification remains OPEN.
- Real provider transaction acceptance remains a separate gate from source/route presence.

## Local Working-Tree Safety

- The old frontend workstation may still contain unrelated dirty work.
- During promotion, a local-only commit `4733d9a7f8b942486ca221c1dba1564e6cb34d2b` was accidentally created on local `main` and was NOT pushed.
- Remote `main` is authoritative at `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`.
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

- Frontend SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8` on both Production and UAT.
- Vercel Production and UAT exact-SHA deployments: SUCCESS.
- Live Production audit on five priority SEO pages: 0 critical/high/medium/low issues.
- All five pages return HTTP 200, are indexable and self-canonical, have one H1 and valid structured data.
- Ranking/CTR impact remains OPEN until Google recrawls and later Search Console data settles.
