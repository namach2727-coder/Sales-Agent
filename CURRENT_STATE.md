# DirectPilot Current State

> Snapshot of verifiable current state. Read `AI_HANDOFF.md` first.
> Last SEO/frontend reconciliation: 2026-10-11; other system states have independent verification dates.

## Latest Verified Frontend Release — 2026-10-11

- **Status: PRODUCTION READY / OWNER VISUAL PASS.** Frontend PR #9 merged from selectively reconciled UAT UI into `main`; SHA `f5f6a5399f938969b9307475eeed208f0e10988b` (GitHub `main` matches); Vercel deployment `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` READY.
- `https://directpilot.ir` and `https://www.directpilot.ir` resolve to `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ`; no alias errors (www redirects to apex).
- Owner confirmed the animated favicon and dashboard layout visually on live Production after hard refresh. Authenticated end-to-end regressions, payment lifecycle and GA4 successful `sign_up` event were **not** re-tested by that confirmation.
- Release changes: motion SVG D tab icon, new glyph system, improved brand/landing/portal/admin layouts, sidebar wrap fix; preservation of Production GA4/SEO, 14-day trial, bank-card payment UX and signup tracking. No backend runtime, Render secrets, database, Meta, DNS or Vercel access-control changes.
- Separate UAT branch SHA `dd9dee1f573151cd7507877aa9a868db467c95ba`; UAT Vercel deployment `dpl_J3foazh8ogYg7suDPUuEzCr37mJJ` READY. Earlier `d9a1a53` / `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` are historical GA4 release evidence, not the live UI.
- Current risk gates remain: Production Postgres free expiry 2026-11-02 and unaccepted backup/restore, GA4 controlled registration E2E, SEO after recrawl, and distinct admin-plan UX retest.

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
- Production `main` deployed and verified at `f5f6a5399f938969b9307475eeed208f0e10988b` for UI PR #9 (with previously accepted GA4/SEO changes preserved).
- UAT current branch (independently verified): `dd9dee1f573151cd7507877aa9a868db467c95ba`; separate READY Vercel deployment `dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`.

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
- Current deployed frontend UI/GA4 SHA: `f5f6a5399f938969b9307475eeed208f0e10988b`.
- Vercel Production: READY; deployment ID `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ`.
- Vercel inspector: `https://vercel.com/mohcenp-9857s-projects/directpilot-web/Ghi3KVJrDwpW1a1nABBDk2wztyBJ`.
- Historical SEO Phase 2 production evidence remains recorded below; the current deployment above supersedes it.
- Historical authenticated Auth/UX Production smoke remains PASS from its earlier separately accepted release. UI PR #9 owner confirmation covers favicon/dashboard visual behavior only, not fresh authentication or commerce E2E.

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
- UAT branch SHA: `dd9dee1f573151cd7507877aa9a868db467c95ba`
- Vercel deployment status for this SHA: READY (`dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`).
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

- Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E PASS**.
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

## SEO Incremental Phases 3-5 — Historical Verified Production 2026-10-11

- PR #1 `a0d663a59421de0f96789dc2dcd5e51d981430f8`: auto-comment article content, `dateModified` / Open Graph / sitemap last-modified support.
- PR #2 `cbb7f74b9f21e9e61f78eaad11c89b9510631ad1`: blog hub guidance, FAQ and contextual navigation.
- PR #3 `3afdd4af2d75ab15abc975ba699c6f7b8fa4575a`: corrected shared trust copy from an inaccurate permanent-free-plan claim to the 14-day trial.
- PR #4 `d3227c949bd051713b6abede9c44499d898e187e`: expanded `/about` with genuine product approach, human handoff, trial transparency, security and links.
- PR #5 `e527c8f7e47a3259457f4efd72ded588eb3e26b9`: added commercial-intent guidance, FAQ and contextual links to `/instagram-direct-automation`, fixed bold-wrapped Markdown links in `/blog/instagram-smart-direct`, and added a clear article-to-service/demo CTA.

Verified Production deployment: frontend `main` SHA `e527c8f7e47a3259457f4efd72ded588eb3e26b9`, Vercel `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2` = READY. A live GSC Wizard on-page crawl on 2026-10-11 returned HTTP 200 / indexable / self-canonical / 0 issues for six pages: `/`, `/blog`, `/blog/instagram-auto-comment-reply`, `/about`, `/instagram-direct-automation`, `/blog/instagram-smart-direct`. Word/link changes: `/blog` 244->426 words, 39->44 internal links; `/about` 139->464 words, 30->36 links; service page 437->680 words, 39->40 links; smart-direct article 30->39 internal links. This proves live publishing and a clean technical audit, **not** a Google recrawl, new indexing event, or ranking/traffic uplift.

Pre-change Search Console context (2026-09-11 to 2026-10-08; not a post-change performance comparison): `/blog/instagram-smart-direct` 88 impressions / 2 clicks; `/instagram-direct-automation` 12 impressions / 1 click; `/instagram-comment-automation` 22 impressions / 1 click. Educational intent belongs with the blog article, commercial/product intent with the direct-automation landing page; pricing intent with `/pricing`.

Ranking/click-through impact: **OPEN**, pending Google recrawl and a comparable settled Search Console window. Only marketing SEO and internal-link rendering were changed by PRs #1-#5; authenticated product flows were not reaccepted by this crawl.

## SEO Phase 6 / GA4 Tracking Acceptance — 2026-10-11

- PR #6 — frontend `ae077e06915e5e280fbb5ff226ac5dd4d529891e`: consent-first GA4 tag, event bridge, limited sanitized marketing `page_view`, `signup_intent`, `pricing_plan_click`, `demo_start`, `blog_cta_click`, and `sign_up` after the backend register call succeeds; Production-only `NEXT_PUBLIC_GA_ID`, strict Preview/UAT isolation, privacy disclosure, CI tests and mobile Lighthouse workflow.
- PR #7 — frontend `31c348ab51c7dc6ae1d4c407c32da1c08a5b5c03`: corrected GA4 collection endpoint allowlists in Production CSP (no `unsafe-eval` and no ad tagging).
- PR #8 — frontend `d9a1a53a6171f3d417637d12cec66eed1832a07b`: repaired gtag.js queue compatibility by pushing JavaScript `arguments`, not spread Arrays, into `dataLayer`; shipped through tested PR with a narrowly justified lint exception.

- Historical GA4 PR #8 Production checkpoint (now superseded by PR #9): `d9a1a53a6171f3d417637d12cec66eed1832a07b`; Vercel deployment `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` = **READY** (https://vercel.com/mohcenp-9857s-projects/directpilot-web/EnejDGuCcotpf4kQrSQk7pnPsyRw). This supersedes the earlier SEO PR #5 release `e527c8f7e47a3259457f4efd72ded588eb3e26b9` / `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2`; those older SHAs remain valid **historical** checkpoints only.
- GA4 Web Stream: `https://directpilot.ir`, `DirectPilot - Production Web`, Measurement ID `G-9D1Z7HDYVZ`, GA4 Property ID `558426868`, GA4 reporting timezone `Asia/Dubai`. Vercel `NEXT_PUBLIC_GA_ID` is set for **Production only**; a fresh Production build is READY.
- Browser verification on 2026-10-11 **after PR #8**: granted consent; gtag.js loaded; `dataLayer` contains `page_view`; request to `https://region1.google-analytics.com/g/collect` returned HTTP **204** with `en=page_view`. GA4 Realtime showed **one active user**, and `first_visit`, `session_start`, `page_view` each observed once. This establishes end-to-end **page-view event delivery and Realtime ingestion**, not all-event/real-signup acceptance.
- In GA4, `sign_up` is defined as a **Key Event** (code-based, no default monetary value, once per event). **The actual `sign_up` delivery after a successful backend registration has NOT been tested**; do not mark conversion E2E PASS or equate `signup_intent` with completed registration.
- GA4 is natively linked to Search Console Domain Property `directpilot.ir`, and GSC Wizard's GA4 connection is separately verified: `sc-domain:directpilot.ir` ↔ `properties/558426868` under `DirectPilot - Production`. GA4 reports and blended GSC+GA4 sections are visible.
- GSC Wizard reports through 2026-10-10 initially showed GA4 zeros because collection was first accepted on 2026-10-11. Respect settled-data lag (~1-3 days), the GA4 launch boundary, site/session definitions, user consent and small samples; **do not** read historical zero as malfunction or claim ranking/conversion uplift. Google Search Console clicks and GA4 sessions are not interchangeable.

- Existing weekly automation **«پایش هفتگی SEO و GA4 DirectPilot»** updated (ID `6acb649a476c8191895050914165ee85`), **enabled**, next intended run Monday 2026-10-12 at approximately 09:00 **Asia/Dubai**, `flexible_schedule`. It now checks settled 28-day SEO windows, 10 indexed URLs, queries/landing pages/cannibalization/sitemap, and GA4 sessions, landing pages, engagement, `signup_intent`, `sign_up` / Key Events, with post-activation/date-alignment safeguards. This is an automation-instructions update; it does not change site code or GA4 settings.
- This scheduled task's automation record currently reports `notifications_enabled=false` and `email_enabled=false`; delivery/notification permissions should be reviewed by the owner separately if push or email alerts are expected. Do not falsely claim notification delivery is enabled.

- Indexing Tracker at last checkpoint: 10 indexed URLs with no active indexing errors; sitemap submission was accepted, but fresh Google recrawl of all modified URLs is not yet proven.
- Search Console's historical `Queries` vs `Google organic search traffic` pages can show different counts because query-row suppression, page-level aggregation and filtering differ. Do not treat them as mismatched GA4 conversions. GA4's 2026-10-11 launch and GSC Wizard reporting lag explain why previous 28-day GA4 reports displayed zero sessions.

**Remaining SEO/measurement gates:** allow settled GA4 data after 2026-10-11, then verify Sessions / Page Views / Organic Search and event counts; run a controlled **successful** test registration and confirm `sign_up` in GA4 before declaring conversion PASS; compare GSC impressions/clicks/CTR/position on aligned post-recrawl windows; inspect the previously observed mobile homepage Lighthouse bottleneck (lab Performance 74, LCP ~2.74s, TBT ~974ms) separately from CrUX field vitals. Maintain the privacy consent gate, no personal data in analytics, no `unsafe-eval`, Production-only tagging, and unchanged backend/payment/Meta readiness gates.

## Meta live inbound evidence

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


## Production Outbound Ready for Controlled E2E — 2026-10-11
- Pilot rule creation: owner confirmed.
- Single-account outbound restriction: configured for the connected Production pilot account.
- Restricted outbound: enabled.
- Deployment `dep-db5ihrg473hc73ba3be0`: LIVE.
- Production environment validation: PASS.
- Database connectivity: PASS.
- Migration head verification: PASS.
- Application startup: PASS.
- No outbound acceptance message has been sent yet in this checkpoint.


## Controlled Outbound Attempt 1 — 2026-10-11
- No inbound event from the first pilot message was observed in UAT or Production.
- The attempt overlapped UAT relay redeployment and is INCONCLUSIVE.
- UAT relay startup subsequently completed successfully.
- Restricted Production outbound remains ready for one clean retest.


## Controlled Meta Outbound E2E — PASS (2026-10-11)
- Clean retest reached Production through the UAT relay.
- Inbound routing and persistence: PASS.
- Deterministic automation handling: PASS.
- One outbound delivery observed: PASS.
- AI fallback did not start: PASS.
- No second outbound was observed after the provider/self follow-up event: PASS.
- Production send was disabled again after acceptance.
- Post-test safety deployment `dep-db5illid0e5s73fju470`: LIVE.
- Current top readiness blocker: Production database durability + backup/restore.
- Production LLM environment verification remains OPEN separately.


## Production DB Durability Assessment — 2026-10-11
- Current Production Postgres is Free, expires 2026-11-02, has no managed backups/PITR, no HA, no replicas, and an empty external IP allowlist.
- Seven-day metrics show very low Pilot load: CPU ~0.007 cores, memory roughly 40-60 MB, active connections peak 6.
- Recommended minimum paid target: Render Postgres `0.1c-256mb` with current storage kept minimal.
- Expected base compute cost: about $6/month; 1 GB storage included, additional Postgres storage is billed separately.
- Paid Render Postgres enables PITR; on a Hobby workspace the recovery window is 3 days. On-demand logical exports are available for paid instances and retained for 7 days.
- Compute-plan change requires brief database downtime.
- Paid infrastructure change remains blocked until explicit owner approval.


## Production DB Upgrade Decision — 2026-10-11
- Owner explicitly deferred the paid Production Postgres upgrade for now.
- Do not change the current Free Production database plan or incur paid infrastructure cost without a new explicit approval.
- Current risk remains accepted temporarily: Free Production Postgres expires 2026-11-02 and does not satisfy durability/backup-restore acceptance.
- Real-customer onboarding remains blocked by Production database durability until this decision is revisited.


## Production LLM State — 2026-10-11

- Diagnosis: PASS.
- Production AI execution readiness: BLOCKED.
- Backend runtime SHA: `398d6dc52e436f4db25f21b19e7dbca4bef10f3c`.
- UAT deployment: `dep-db5j4ebbc2fs73934e7g` LIVE.
- Production deployment: `dep-db5j5c7lk1mc73a6ofkg` LIVE.
- UAT: provider=Groq; configured credential/model present.
- Production: provider=OpenAI; model=`gpt-5.6-sol`; OpenAI credential absent.
- Production alternative readiness: Groq credential absent and Groq model absent.
- Prior `llm_provider_configuration_error` is therefore explained by missing Production selected-provider credentials before any provider request.
- Production environment/DB/migration/application startup remain PASS.
- Meta send remains disabled after the completed Meta E2E.


## Groq Model Support Check — 2026-10-11
- UAT currently selects `qwen/qwen3.6-27b`.
- Official Groq deprecation guidance says `qwen/qwen3.6-27b` was deprecated for Free/Developer usage on 2026-09-14.
- Direct replacement: `qwen/qwen3.8-27b`.
- Do not copy the deprecated UAT model into Production.
- If Production Groq is approved, target `qwen/qwen3.8-27b` with existing guardrails `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, and `GROQ_REASONING_EFFORT=none`.
- Production still requires its own securely provisioned `GROQ_API_KEY`; never copy or expose the UAT credential.


## Production Groq Configuration Activated — 2026-10-11
- Production LLM provider is now `groq`.
- Production model is `qwen/qwen3.8-27b`.
- Groq credential presence: verified true through sanitized startup metadata; secret value was never logged or copied.
- Guardrails: `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, `GROQ_REASONING_EFFORT=none`.
- Production environment, DB connectivity, migration head and application startup: PASS.
- LLM configuration deployment `dep-db5jh9lckfvc73aekfbg`: LIVE.
- Restricted Meta-send test deployment `dep-db5ji6ss728c73823a50`: LIVE.
- Meta send is enabled only under the existing single-pilot account allowlist for one controlled AI fallback E2E.
- Next: send one deliberately unmatched pilot message and verify Groq request completion, assistant persistence, exactly one outbound delivery, quota accounting, dedupe and no echo loop.


## Production AI Fallback — PASS (2026-10-11)

- Production provider: Groq.
- Production model: `qwen/qwen3.8-27b`.
- Production Groq credential presence: verified configured without revealing the secret.
- Controlled AI fallback correlation: `3005f232-3fe2-4c8f-bb37-642c5b16a6d1`.
- Groq completion: PASS, latency 226 ms, 425 input / 63 output / 488 total tokens.
- AI orchestration + assistant persistence: PASS.
- Meta outbound: exactly one start / one delivery / zero failures.
- Duplicate second send: not observed.
- Echo/self follow-up: ignored.
- Quota guard executed; token metadata is persisted for usage aggregation. Exact aggregate counter not independently queried because Production DB external access remains closed.
- Post-test send state: disabled.
- Post-test deployment `dep-db5jm4nlk1mc73a8du40`: LIVE.
- Production LLM configuration verification and AI fallback acceptance: PASS.


## Payexa Environment Split Verification — 2026-10-11

- Safe Payexa runtime observability SHA: `b7c510912a6b5bb13c736192e390bce44a3dcb61`.
- CI for the observability change: test PASS / docker-build PASS / postgres-smoke PASS.
- Initial UAT runtime was incorrectly configured against Production Payexa: base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, credential present. This environment-split finding was FAIL and was corrected immediately.
- UAT is now isolated to Payexa Sandbox: base `https://sandbox.pexn.ir`, callback base `https://uat.directpilot.ir`, sandbox credential configured. Deployment `dep-db5k0pcs728c7383hnh0`: LIVE. UAT Payexa environment split: PASS.
- Initial Production Payexa state was fail-closed: sandbox/default base, empty callback, no credential.
- Production non-secret Payexa configuration is now base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, timeout 15s, while Production credential remains absent. Deployment `dep-db5k2e142hec7398l0h0`: LIVE.
- Production Payexa environment structure is therefore correct but provider execution remains intentionally BLOCKED until a Production-specific `PAYEXA_API_KEY` is provisioned securely.
- Current frontend checkout intentionally does not invoke Payexa; manual card transfer remains the primary checkout path. Payexa source/routes and result page remain present.
- Real-provider acceptance is NOT PASS. It requires Production credential provisioning, Payexa-side verification/approval of the DirectPilot callback site/domain as applicable, and a controlled transaction path.
- Never copy UAT credentials into Production, expose provider secrets in chat/logs, or blindly retry ambiguous create operations.

- Payment-provider environment split: PASS after UAT correction.
- Production Payexa credential readiness: BLOCKED/MISSING.
- Production Payexa real transaction acceptance: OPEN.


## Authoritative Payment Flow Correction — 2026-10-11

- Current DirectPilot payment architecture is **manual card transfer with admin approval**, not Payexa.
- Customer selects a paid plan and receives the configured payment-card details from DirectPilot.
- Customer transfers the exact amount using any banking method outside DirectPilot.
- Customer uploads a JPEG/PNG/PDF receipt from the customer panel.
- Backend validates the receipt and persists the receipt bytes plus metadata in PostgreSQL (`receipt_data`, content type, size, SHA-256), then changes payment status to `submitted` and order status to `payment_submitted`.
- Platform Admin reviews submitted payments in Admin -> Payments, can securely view the receipt, and chooses Approve or Reject.
- Approve is backend-authoritative: it row-locks/checks optimistic revision, marks payment `approved`, marks order `paid`, creates/activates the subscription, applies plan/module entitlements and writes an audit record atomically.
- Reject returns the order to `pending` and records the rejection reason without deleting the payment.
- UAT frontend currently contains this complete customer + admin flow and its Vercel deployment is SUCCESS at frontend UAT SHA `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Backend manual flow is present and deployed from `backend-main`; current CI remains PASS.
- Payexa/KPay routes are preserved only as non-primary/deferred integration code. They are **not** part of the current customer checkout path and are **not** a Production-readiness gate for the current payment process.
- Do not request or provision Payexa credentials unless the owner explicitly decides to re-open automated payment-gateway work.
- Current payment readiness should be evaluated against manual-card-transfer E2E and admin approval, not Payexa acceptance.

- UAT manual payment flow: SOURCE/DEPLOYMENT VERIFIED.
- Production manual-payment acceptance: requires current Production configuration/receipt/admin approval E2E verification.
- Payexa: DEFERRED / NOT CURRENT CHECKOUT.


## Production Manual Payment E2E Readiness — 2026-10-11

- Authoritative payment path remains manual card transfer + customer receipt upload + Admin approval.
- Frontend Production `main` is one commit ahead of UAT but has no payment/checkout/admin-payment differences from UAT. Production Vercel status is SUCCESS.
- Safe manual-payment readiness probe SHA: `c05669d3448ea3f6f151bb73a22db5dcfffcf7b7`.
- CI: test PASS / docker-build PASS / postgres-smoke PASS.
- UAT deployment `dep-db5kjhnlot8c73f9ueb0`: LIVE; runtime readiness `active_cards=1 active_default_cards=1` => PASS.
- Production deployment `dep-db5kkhid0e5s73fq7h90`: LIVE; runtime readiness `active_cards=0 active_default_cards=0` => BLOCKED.
- Production cannot create a manual payment until an Admin configures at least one active default payment card.
- No card number/account data was logged or copied from UAT. Do not fabricate, infer, or transfer banking details across environments.
- Once a real Production destination card is configured by an authorized Admin, run controlled E2E: paid-plan order -> show card -> upload test receipt -> Admin reviews receipt -> Admin approves -> verify payment approved, order paid, subscription active and module entitlements applied.

- Manual payment Production E2E: BLOCKED only on missing active/default Production payment card.


## Production Payment Card Form Reset Incident — FIXED (2026-10-11)

- User hit frontend error while creating the first Production payment card: `Cannot read properties of null (reading 'reset')`.
- Root cause was frontend-only: `createCard()` called `event.currentTarget.reset()` after an awaited API request. The React form event's `currentTarget` was no longer reliable at that point.
- Fix: capture the HTML form element before the async boundary, build `FormData` from that stable reference, and call `formElement.reset()` after the successful request.
- A regression test now requires the stable form reference and forbids async use of `event.currentTarget.reset()`.
- UAT fix SHA `910bd2b0add605ab926e08ab18be444431c0a134`: Vercel SUCCESS.
- Production runtime fix SHA `2f0ba54287e04ad8d7f5d747d2adcefdfd25bbbf`: Vercel SUCCESS.
- Production test-only follow-up SHA `a8e90d3aa1112dd2e577ee82c452ecb421668618` adds the regression test; runtime behavior is unchanged from the successful runtime-fix commit.
- Because the failing `reset()` statement executes only after `await adminPaymentsApi.createCard(...)` resolves, the backend card-create request had already succeeded before this UI exception. Do not ask the user to re-enter the same card blindly; first refresh/reload the Admin Payments view and confirm the created card is present.
- Production DB remains externally closed; no banking details were queried, logged or exposed.

- Production manual-payment UI card-create reset bug: FIXED/DEPLOYED.
- Backend card creation occurred before the frontend reset exception; UI reload confirmation remains the immediate check before continuing E2E.


## Payment Card Display Readability Fix — 2026-10-11

- Admin payment-card rows previously rendered bank name, account holder and card number as adjacent inline text, producing unreadable output such as `بانکنام صاحب حساب5859...`.
- Frontend now renders bank/label, account holder and card number on separate lines.
- Card numbers are formatted visually in four-digit groups and rendered LTR for readability; stored card data is unchanged.
- UAT frontend SHA `61ef804dba0c03e14eb6e26308a05e63e2ed2ae2`: Vercel SUCCESS.
- Production frontend SHA `b5b7d1e5fbeef6622dcbe8c105caeb17b41df0fb`: Vercel SUCCESS.
- Regression coverage added for separated metadata layout and grouped card-number rendering.


## Customer Card Copy Action — 2026-10-11

- Customer manual-payment page now exposes a dedicated **Copy card number** action beside the destination card.
- Copy behavior first uses the modern Clipboard API and falls back to a temporary readonly textarea + `execCommand("copy")` for broader mobile-browser compatibility.
- The copied value is normalized to digits/no spaces before being written to the clipboard.
- Successful copy changes the button label to `کپی شد ✓` and shows the status message `شماره کارت در کلیپ‌بورد کپی شد.`.
- Mobile layout makes the copy button full-width below the card row for easier tapping.
- UAT frontend SHA `1e33cda4e572d1eac44608e1b57a6674a99ca18f`: Vercel SUCCESS.
- Production frontend SHA `cc924aa651069682e903ae236fd061e002288bbb`: Vercel SUCCESS.
- Regression coverage added for Clipboard API, mobile fallback, normalized card value, button feedback and mobile layout.


## Production Manual Payment Card Readiness — PASS (2026-10-11)

- Production backend deployment `dep-db5m7m7lot8c73fesnug`: LIVE.
- Safe startup readiness reports `active_cards=1 active_default_cards=1`.
- Production manual-payment destination card configuration is therefore READY.
- Customer manual-payment flow can now proceed to controlled E2E: paid plan order -> display destination card -> test card-copy action -> upload test receipt -> Admin review -> Approve -> verify payment approved, order paid, subscription active and entitlements updated.


## Customer Billing Discoverability Fix — 2026-10-11

- Verified the customer billing flow exists in Production source and is rendered by AuthenticatedShell on both desktop and mobile as `اشتراک و پرداخت`.
- Root UX gap: the customer Overview page had no direct CTA into billing, making the payment flow easy to miss even though the section and routes existed.
- Added a prominent primary action `مشاهده پلن‌ها و پرداخت` to the customer Overview quick-actions card, linking directly to `/dashboard?section=billing`.
- UAT frontend SHA `eccb29022e81141bd90b9abf77c019f018889d8c`: Vercel SUCCESS.
- Production frontend SHA `cd9d3e5f10a97fd2edc9b6fb2d8ee34e87575030`: Vercel SUCCESS.
- Existing billing logic, order creation, checkout, manual card-transfer payment and receipt upload routes were unchanged.

## Production Manual Payment E2E — PASS (2026-10-11)

- Production manual card-transfer checkout is now end-to-end accepted.
- Customer completed card display/copy and receipt upload.
- Backend-authoritative approval completed with:
  - payment `approved`
  - order `paid`
  - subscription `active`
  - source `PURCHASED`
  - `AUTOMATION_V1`
  - automation limit 20
  - Instagram account limit 1
  - duration 30 days
- Production UI confirmation by owner: PASS.
- Production frontend Trial/Billing fix: Vercel READY at `2e9122f2632972c118e98ad16a43d1c957ec446d`.
- Guarded approval runtime commit: `421d157fc85549ae238c72f553d68ac8e3bd85ae`.
- Cleanup deployment `dep-db5p0nng0jfs73bign50`: LIVE with the approval flag disabled.
- Manual Payment Production E2E is no longer an open blocker.


## 2026-10-12 — Instagram UAT checkpoint
- Owner-created test customer passed manual admin-denial test; one connected Instagram account visible in UAT and one active connection in isolated Neon.
- Backend OAuth callback redirect PR #6 merged as `eb97e540` and UAT Render deploy `dep-db6ane7avr4c73apac1g` confirmed LIVE. `CORS_ALLOWED_ORIGINS` added to UAT as `https://uat.directpilot.ir`.
- UAT `META_WEBHOOK_RELAY_TARGET_URL` targets Production; UAT Neon showed zero webhook deliveries at last check. This is consistent with relay behavior, not an independently verified Meta delivery.
- Offline ingestion regression in `tests/test_instagram_webhook.py` is prepared on a testing branch; CI and merge not yet verified. No real webhook sent; Production and Meta config unchanged.

## 2026-10-12 — Prepaid multi-month UI / UAT checkpoint
- Confirmed isolated Neon UAT has one active default payment card; user previously saw no-active-card error because table was empty before the new card was added.
- Backend multi-month order feature is implemented in unmerged PR #8 (CI pending at this checkpoint). Frontend month selector and checkout totals implemented in unmerged PR #15 (Vercel Preview check pending at this checkpoint).
- Neither change has been deployed to UAT as of this checkpoint. Production untouched. Acceptance tests must establish 3-month total and 90-day entitlement after approved receipt.

### Latest verified multi-month release — 2026-10-12
- UAT Neon: 1 active default bank card (read-only count verification).
- Backend PR #8: merged `b1a63ea9`, GitHub CI #355 PASS, manual Render UAT deploy `dep-db6becvlk1mc73cksvi0` LIVE (matching commit); no Production deploy.
- Frontend PR #15: merged `34b19e6e` to UAT, Vercel status Success. PR #16 dashboard/billing UX reconciliation Preview pending.
- Browser test of choosing and paying for 3 months, receipt submission, and confirming 90-day subscription is not yet performed.

### UAT interface release closure — 2026-10-12
- PR #16 merged to UAT at commit `8f083473` with Vercel Success. Backend UAT `dep-db6becvlk1mc73cksvi0` LIVE. Manual 3-month payment E2E still pending; Production unchanged.


### UAT receipt preview update
- 2026-10-12 UAT payment preview checkpoint: Backend PR #10 CI PASS and Render UAT deploy `dep-db6bpsm7bikc73ca11i0` LIVE on `c2eaf52d`. Frontend PR #17 merged to UAT commit `65c476ef`; browser preview and PDF behavior manual confirmation pending. No Production deploy.


### 2026-10-12 UAT compact payment UI
- 2026-10-12 frontend UAT PR #18 merged at `1cae8c088542ff7ce6612c76705e3c670d223f74`. Compact admin payment details, image/PDF receipt sizing, active plan names and upgrade-only CTA are present in UAT source. Merged deployment status and manual visual tests not yet verified at this checkpoint; Production unchanged.


### Production promotion preflight (2026-10-12)
- 2026-10-12 Production preflight: UAT customer/admin interface accepted by owner. Production NOT UPDATED by this release. Render `directpilot-api`: last LIVE `421d157f`, Auto Deploy OFF; backend-main 41 commits ahead. Frontend `UAT...main`: diverged; UAT 83 commits ahead, main 20 commits ahead in reverse; PR #19 draft mergeable=false. Neon connector exposes isolated UAT project only, not verified Production database. Production schema/catalog promotion requires separate safe DB access/backup review.


## 2026-10-12 — Actual Production release status (latest; supersedes older statuses)
- UAT owner acceptance PASS.
- Backend PROD Render `dep-db6fr2bl550s73esrnh0`, SHA `043d37ff`: LIVE. APP_ENV production, DB connect, Alembic head, startup PASS. Schema migration file diff: NONE.
- Frontend PROD `main` PR #20 merged at `06ebe316e5193f111ebd4b0733ee85c406d0a56e`; CI #38271830924 PASS (210 tests; type-check; lint; build); domain Vercel READY/alias NOT VERIFIED due project 403/404 and absence from linkedProjects. Direct UAT PR #19 superseded/closed.
- Production data catalog `AI_ASSISTANT_V1` existence UNVERIFIED and no production data change performed; UAT paid AI is not a Production entitlement. Manual payment in Production had prior approved E2E PASS. No Meta/settings changes.
- DB Free expiration 2026-11-02 and unverified backup/restore remain OPEN.
