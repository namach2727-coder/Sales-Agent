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
> Last SEO/frontend reconciliation: 2026-10-11. Other integration/runtime items retain their own separately verified checkpoints.

## UI / Branding Production Release — 2026-10-11 (LATEST FRONTEND CHECKPOINT)

- Release: frontend PR #9 (UAT humanized UI / SVG motion glyphs / animated vector D favicon / dashboard and admin presentation / sidebar nowrap). Merged to `main`; exact commit `f5f6a5399f938969b9307475eeed208f0e10988b`.
- Vercel Production deployment: `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` — **READY**; `https://directpilot.ir` and `https://www.directpilot.ir` resolve to this deployment (www redirects to apex; aliases have no error). [Vercel inspector](https://vercel.com/mohcenp-9857s-projects/directpilot-web/Ghi3KVJrDwpW1a1nABBDk2wztyBJ).
- GitHub `main` is identical to `f5f6a5399f938969b9307475eeed208f0e10988b` (ahead/behind 0/0); `UAT` remains separately at `dd9dee1f573151cd7507877aa9a868db467c95ba` with previously verified READY deployment `dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`.
- **Owner visual acceptance: PASS** on the live Production site after hard refresh, including tab favicon animation and dashboard layout (owner confirmed on 2026-10-11). This is not a new authenticated functional E2E, payment E2E, browser-matrix, or GA4 `sign_up` E2E acceptance.
- Scope discipline: Production GA4/SEO changes and `sign_up` / `signup_intent` instrumentation, 14-day trial copy and existing manual payment/card formatting were preserved while reconciling divergent UAT and `main`. No backend deploy, payment configuration, Meta, database, DNS or Vercel Authentication setting was changed for this release.
- Historical Vercel `api-deployments-free-per-day` limit and intermediate release-branch `module_not_found` previews did not affect the final READY Production deployment. Do not redeploy an intermediate `release/humanized-ui-uat-20261011` commit.
- Still open independently: GA4 `sign_up` genuine-registration delivery, post-recrawl SEO effects, Production database durability/backup-restore acceptance and any separately marked admin-plan feature retest. Do not claim those PASS from visual acceptance.

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
- Production SHA (verified Vercel READY and owner visual PASS 2026-10-11): `f5f6a5399f938969b9307475eeed208f0e10988b`
- UAT branch SHA (verified current 2026-10-11; separate preview environment): `dd9dee1f573151cd7507877aa9a868db467c95ba`
- Vercel Production: READY for the currently verified frontend SHA.
- Recent admin-plan UX fixes: preserve scroll across create/remount, prevent native validation scroll jumps, normalize internal plan code input to uppercase.
- Owner retest of the final plan-creation UX behavior: PENDING.
- Public Production domain: `https://directpilot.ir`
- Public UAT domain: `https://uat.directpilot.ir`
- Vercel Production status for current SHA: READY — `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ`
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

- UAT branch SHA: `dd9dee1f573151cd7507877aa9a868db467c95ba`
- UAT Vercel deployment `dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`: READY for this SHA.
- Owner-confirmed UAT functional acceptance: PASS.

## Latest GA4 + SEO Continuity Checkpoint — 2026-10-11

**Status: GA4 PAGE-VIEW DELIVERY AND REALTIME INGESTION PASS / KEY EVENT SIGNUP E2E OPEN / SEO IMPACT OPEN.**

- PR #6 — frontend `ae077e06915e5e280fbb5ff226ac5dd4d529891e`: consent-first GA4 tag, event bridge, limited sanitized marketing `page_view`, `signup_intent`, `pricing_plan_click`, `demo_start`, `blog_cta_click`, and `sign_up` after the backend register call succeeds; Production-only `NEXT_PUBLIC_GA_ID`, strict Preview/UAT isolation, privacy disclosure, CI tests and mobile Lighthouse workflow.
- PR #7 — frontend `31c348ab51c7dc6ae1d4c407c32da1c08a5b5c03`: corrected GA4 collection endpoint allowlists in Production CSP (no `unsafe-eval` and no ad tagging).
- PR #8 — frontend `d9a1a53a6171f3d417637d12cec66eed1832a07b`: repaired gtag.js queue compatibility by pushing JavaScript `arguments`, not spread Arrays, into `dataLayer`; shipped through tested PR with a narrowly justified lint exception.

- Historical GA4 PR #8 Production checkpoint (superseded by UI PR #9 above): `d9a1a53a6171f3d417637d12cec66eed1832a07b`; Vercel deployment `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` = **READY** (https://vercel.com/mohcenp-9857s-projects/directpilot-web/EnejDGuCcotpf4kQrSQk7pnPsyRw). This supersedes the earlier SEO PR #5 release `e527c8f7e47a3259457f4efd72ded588eb3e26b9` / `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2`; those older SHAs remain valid **historical** checkpoints only.
- GA4 Web Stream: `https://directpilot.ir`, `DirectPilot - Production Web`, Measurement ID `G-9D1Z7HDYVZ`, GA4 Property ID `558426868`, GA4 reporting timezone `Asia/Dubai`. Vercel `NEXT_PUBLIC_GA_ID` is set for **Production only**; a fresh Production build is READY.
- Browser verification on 2026-10-11 **after PR #8**: granted consent; gtag.js loaded; `dataLayer` contains `page_view`; request to `https://region1.google-analytics.com/g/collect` returned HTTP **204** with `en=page_view`. GA4 Realtime showed **one active user**, and `first_visit`, `session_start`, `page_view` each observed once. This establishes end-to-end **page-view event delivery and Realtime ingestion**, not all-event/real-signup acceptance.
- In GA4, `sign_up` is defined as a **Key Event** (code-based, no default monetary value, once per event). **The actual `sign_up` delivery after a successful backend registration has NOT been tested**; do not mark conversion E2E PASS or equate `signup_intent` with completed registration.
- GA4 is natively linked to Search Console Domain Property `directpilot.ir`, and GSC Wizard's GA4 connection is separately verified: `sc-domain:directpilot.ir` ↔ `properties/558426868` under `DirectPilot - Production`. GA4 reports and blended GSC+GA4 sections are visible.
- GSC Wizard reports through 2026-10-10 initially showed GA4 zeros because collection was first accepted on 2026-10-11. Respect settled-data lag (~1-3 days), the GA4 launch boundary, site/session definitions, user consent and small samples; **do not** read historical zero as malfunction or claim ranking/conversion uplift. Google Search Console clicks and GA4 sessions are not interchangeable.

- Existing weekly automation **«پایش هفتگی SEO و GA4 DirectPilot»** updated (ID `6acb649a476c8191895050914165ee85`), **enabled**, next intended run Monday 2026-10-12 at approximately 09:00 **Asia/Dubai**, `flexible_schedule`. It now checks settled 28-day SEO windows, 10 indexed URLs, queries/landing pages/cannibalization/sitemap, and GA4 sessions, landing pages, engagement, `signup_intent`, `sign_up` / Key Events, with post-activation/date-alignment safeguards. This is an automation-instructions update; it does not change site code or GA4 settings.
- This scheduled task's automation record currently reports `notifications_enabled=false` and `email_enabled=false`; delivery/notification permissions should be reviewed by the owner separately if push or email alerts are expected. Do not falsely claim notification delivery is enabled.

**Remaining SEO/measurement gates:** allow settled GA4 data after 2026-10-11, then verify Sessions / Page Views / Organic Search and event counts; run a controlled **successful** test registration and confirm `sign_up` in GA4 before declaring conversion PASS; compare GSC impressions/clicks/CTR/position on aligned post-recrawl windows; inspect the previously observed mobile homepage Lighthouse bottleneck (lab Performance 74, LCP ~2.74s, TBT ~974ms) separately from CrUX field vitals. Maintain the privacy consent gate, no personal data in analytics, no `unsafe-eval`, Production-only tagging, and unchanged backend/payment/Meta readiness gates.

## Earlier Verified SEO Releases — Phases 3-5 / 2026-10-11

Status: **PRODUCTION READY / LIVE ON-PAGE AUDIT PASS; SEARCH RANKING IMPACT OPEN**.

- PR #1 `a0d663a59421de0f96789dc2dcd5e51d981430f8`: auto-comment article content, `dateModified` / Open Graph / sitemap last-modified support.
- PR #2 `cbb7f74b9f21e9e61f78eaad11c89b9510631ad1`: blog hub guidance, FAQ and contextual navigation.
- PR #3 `3afdd4af2d75ab15abc975ba699c6f7b8fa4575a`: corrected shared trust copy from an inaccurate permanent-free-plan claim to the 14-day trial.
- PR #4 `d3227c949bd051713b6abede9c44499d898e187e`: expanded `/about` with genuine product approach, human handoff, trial transparency, security and links.
- PR #5 `e527c8f7e47a3259457f4efd72ded588eb3e26b9`: added commercial-intent guidance, FAQ and contextual links to `/instagram-direct-automation`, fixed bold-wrapped Markdown links in `/blog/instagram-smart-direct`, and added a clear article-to-service/demo CTA.

Verified Production deployment: frontend `main` SHA `e527c8f7e47a3259457f4efd72ded588eb3e26b9`, Vercel `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2` = READY. A live GSC Wizard on-page crawl on 2026-10-11 returned HTTP 200 / indexable / self-canonical / 0 issues for six pages: `/`, `/blog`, `/blog/instagram-auto-comment-reply`, `/about`, `/instagram-direct-automation`, `/blog/instagram-smart-direct`. Word/link changes: `/blog` 244->426 words, 39->44 internal links; `/about` 139->464 words, 30->36 links; service page 437->680 words, 39->40 links; smart-direct article 30->39 internal links. This proves live publishing and a clean technical audit, **not** a Google recrawl, new indexing event, or ranking/traffic uplift.

Pre-change Search Console context (2026-09-11 to 2026-10-08; not a post-change performance comparison): `/blog/instagram-smart-direct` 88 impressions / 2 clicks; `/instagram-direct-automation` 12 impressions / 1 click; `/instagram-comment-automation` 22 impressions / 1 click. Educational intent belongs with the blog article, commercial/product intent with the direct-automation landing page; pricing intent with `/pricing`.

Next SEO gate: let Google recrawl the changed URLs and accumulate a meaningful settled Search Console window; compare page+query impressions, clicks, CTR and average position against a date-aligned baseline. Check article -> service internal-link visibility and keep service/blog keyword ownership separate. Do not claim rank growth or repeat copy rewrites based only on immediate deployment data. Preserve Production-only indexing and UAT/Preview noindex.

Integration and payment readiness are separate from these public marketing-page changes. Do not equate a documentation-only commit in `Sales-Agent` with an application deployment.

## Previous SEO Foundation — Phase 2

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

Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E PASS**

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
- Controlled deterministic outbound E2E passed on 2026-10-11. Production send was returned to `META_SEND_ENABLED=false` after the test; the single-account allowlist remains configured.

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

## Historical Integration Resume Marker (2026-10-07)

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
OUTBOUND E2E PASS

OBSERVED_OUTBOUND_BLOCKER:
NONE FOR DETERMINISTIC META TRANSPORT
LLM FALLBACK CONFIGURATION REMAINS A SEPARATE OPEN GATE

PRODUCTION_DB:
FREE / EXPIRES 2026-11-02
DURABILITY: OPEN
BACKUP_RESTORE: OPEN

NEXT EXACT ACTION:
Prioritize Production database durability + backup/restore acceptance before real-customer onboarding. Verify Production LLM configuration separately afterward.
```



## Future Product Track — Telegram Bot Builder

- Parked idea: No-code AI Telegram Bot Builder / Managed Bots-based SaaS.
- Not part of current DirectPilot execution scope.
- Resume only after current Production readiness / Meta / durability gates are addressed.


## Admin Customer Automation Management — 2026-10-10

- Frontend Production/UAT SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- UAT Vercel build: SUCCESS.
- Production Vercel build: SUCCESS.
- Platform Admin can now open **Customers & Stores -> Manage Automation** for a store that has `instagram_automation`.
- The UI reuses the existing tenant/store-scoped AutomationRule API; no impersonation, cross-tenant bypass, or separate admin rule store was introduced.
- Platform authorization continues through the backend's existing `tenant.update` platform permission path.
- Admin can configure the actual customer/store rule fields: trigger location, match type, keywords/phrases, response text, priority and enabled state.
- Backend remains authoritative for capability and automation-limit enforcement.
- Owner Production functional acceptance: PASS for customer automation rule creation.
- Production pilot deterministic rule creation was confirmed and used successfully in controlled E2E.


## Controlled Production Outbound Gate — 2026-10-11
- Owner confirmed the deterministic pilot rule was created.
- The Production pilot Instagram connection was resolved from the authenticated scoped connection API.
- Production outbound restriction is now configured to exactly one pilot account.
- Production sending is enabled only under that single-account restriction.
- Guarded deployment: `dep-db5ihrg473hc73ba3be0` — LIVE.
- Runtime validation: production environment PASS, database connectivity PASS, migration head PASS, application startup PASS.
- Next action: send `قیمت` exactly once from the second Instagram account, then inspect deterministic match, one provider delivery, dedupe and echo suppression.


## Controlled Outbound Attempt 1 — Inconclusive (2026-10-11)
- The first pilot message was sent while the UAT relay service was redeploying.
- No new webhook/inbound event was observed in UAT or Production for that attempt.
- Automation matching and outbound delivery were therefore not evaluated.
- UAT relay startup then completed successfully. One clean retest is required.


## Controlled Production Outbound E2E — PASS (2026-10-11)

- Clean retest correlation: `eb5e69b7-2ebb-4daf-a487-c9cc2857ec43`.
- UAT relay: PASS.
- Production inbound received/account resolved/conversation reused/message persisted: PASS.
- Deterministic AutomationRule executed: PASS.
- Exactly one outbound started and exactly one outbound delivered: PASS.
- AI fallback did not start: PASS.
- No outbound failure observed: PASS.
- Provider-side follow-up webhook did not create a second send; self/echo event was ignored: PASS.
- No later outbound-start event appeared in the observation window: PASS.
- Post-test safety rollback deployment: `dep-db5illid0e5s73fju470` — LIVE.
- Production send returned to `META_SEND_ENABLED=false`.
- Meta Production controlled E2E is accepted as PASS.
- Remaining major readiness gates: Production database durability/backup-restore, Production LLM verification, payment-provider verification/acceptance, forgot-password provider.


## Meta Controlled E2E Final — 2026-10-11
- Controlled Production Meta E2E: PASS.
- Inbound routing/persistence: PASS.
- Deterministic automation response: PASS.
- Exactly one outbound delivery observed: PASS.
- AI fallback did not run: PASS.
- Echo/follow-up event did not create a second outbound: PASS.
- Production send was returned to disabled after the test.
- Post-test safety deployment: `dep-db5illid0e5s73fju470` — LIVE.
- Next major readiness blocker: Production database durability + backup/restore. Production LLM verification remains separate and OPEN.


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


## Production LLM Configuration Diagnosis — 2026-10-11

- Safe observability runtime: `398d6dc52e436f4db25f21b19e7dbca4bef10f3c`.
- CI: test PASS / docker-build PASS / postgres-smoke PASS.
- UAT deployment `dep-db5j4ebbc2fs73934e7g`: LIVE.
- Production deployment `dep-db5j5c7lk1mc73a6ofkg`: LIVE.
- UAT selected LLM: Groq, model `qwen/qwen3.6-27b`, credential configured.
- UAT readiness also shows OpenAI credential present, Groq credential present, and Groq model configured.
- Production selected LLM: OpenAI, model `gpt-5.6-sol`, credential NOT configured.
- Production readiness shows OpenAI credential=false, Groq credential=false, Groq model=false.
- Root cause of prior `llm_provider_configuration_error`: Production has no configured credential for the selected OpenAI provider.
- Do not copy UAT credentials into Production and do not expose any provider key in chat/logs.
- Do not copy the UAT Groq model blindly; its current support status must be verified before Production use.
- Next gate: securely provision a Production-specific LLM credential, then configure non-secret provider/model settings and run one controlled AI fallback E2E while Meta send is explicitly gated.


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


## Production AI Fallback E2E — PASS (2026-10-11)

- Controlled unmatched Instagram test reached Production through the UAT relay.
- Correlation: `3005f232-3fe2-4c8f-bb37-642c5b16a6d1`.
- Deterministic automation did not handle the message; AI fallback started.
- Groq request: PASS using `qwen/qwen3.8-27b`.
- Provider latency: 226 ms.
- Token evidence: input=425, output=63, total=488, finish_reason=stop.
- AI orchestration completed and assistant response was persisted before delivery.
- Exactly one outbound started and exactly one outbound delivered: PASS.
- No outbound failure, AI failure, duplicate second send, or echo loop observed.
- Provider/self follow-up inbound was ignored.
- AI request quota guard executed before the provider call; persisted assistant metadata carries token usage used by the server-authoritative usage summary. Exact aggregate counter was not independently queried because Production DB external access remains intentionally closed.
- Post-test `META_SEND_ENABLED=false` restored.
- Safety rollback deployment `dep-db5jm4nlk1mc73a8du40`: LIVE.
- Production LLM configuration + controlled AI fallback E2E are accepted as PASS.


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

## Production Manual Payment E2E — PASS / CLOSED (2026-10-11)

- Authoritative MVP payment path remains manual card transfer -> receipt upload -> Admin approval.
- UAT controlled E2E: PASS.
- Production frontend Trial/Billing visibility fix is live on `directpilot.ir`; final Production frontend commit `2e9122f2632972c118e98ad16a43d1c957ec446d` reached Vercel READY and owns the Production aliases.
- Controlled Production customer flow completed: paid plan selection -> destination card display/copy -> receipt upload -> guarded backend-authoritative approval.
- Runtime approval result: `payment_status=approved`, `order_status=paid`, `subscription_status=active`, `source=PURCHASED`.
- Activated entitlement snapshot: `AUTOMATION_V1`, `automation_limit=20`, `instagram_account_limit=1`, `duration_days=30`.
- Owner visually confirmed in Production UI that the payment is approved.
- First guarded Production approval attempt failed safely because the UAT email did not exist in Production; no commercial state changed in that failed attempt.
- Final approval used a strict unique-recent-receipt guard for `AUTOMATION_V1`; it aborts unless exactly one recent submitted manual payment matches.
- Approval one-shot flags were disabled after success.
- Production cleanup deployment `dep-db5p0nng0jfs73bign50`: LIVE; application startup complete; approval did not rerun.
- Production Manual Payment E2E gate is CLOSED/PASS. Do not reopen Payexa/KPay for this gate unless the owner explicitly changes payment strategy.


## 2026-10-12 — UAT Instagram isolated webhook test (pending CI)
- Owner constraint: one shared Meta App/configuration for UAT and Production. Do not modify Meta Developers callback, subscriptions, secrets, or production routing.
- Confirmed UAT `META_WEBHOOK_RELAY_TARGET_URL` points to Production (`https://directpilot-api.onrender.com/api/v1/integrations/instagram/webhook`); actual inbound deliveries must continue relay unchanged.
- Isolated Neon UAT has one active Instagram connection; OAuth browser redirect backend PR #6 merged as `eb97e540` and deployed LIVE to UAT (`dep-db6ane7avr4c73apac1g`). UAT CORS allowed origin set to `https://uat.directpilot.ir`. Production was not deployed.
- Offline regression added in `tests/test_instagram_webhook.py` on `test/isolated-uat-webhook-no-meta-changes-20261012`: invokes `InstagramWebhookIngestionService.ingest` against disposable local SQLite test DB, with relay disabled and outbound Meta sending disabled. This DOES NOT establish actual delivery from Meta to UAT nor write to UAT Neon. CI status pending.

## 2026-10-12 — UAT multi-month prepaid orders (implementation pending release)
- Independent UAT Neon confirmed one active default payment card (`payment_cards`: total=1, active_default=1); the missing-card issue no longer applies at DB level.
- Backend PR #8 (`feat/uat-multi-month-orders-20261012`): 1–12 months supported on paid 30-day plans; server calculates price and order duration from the plan, snapshots totals, and uses existing manual transfer/receipt approval. AI response/request/token allowances scale with prepaid months. CI / merge / UAT deploy require verification.
- Frontend PR #15 (`feat/uat-multi-month-checkout-20261012`): UAT-only selection for 1–12 months with preview, exact totals, 30 days/month, protection against reusing mismatched pending orders, and accessible RTL controls. Build status and UAT merge require verification.
- Example: 3 x Automation 490,000 toman => 1,470,000 toman, 90 days; no automatic charge or installment. Shared Meta settings and Production deployments remain untouched.

### Verified release progress — 2026-10-12 (supersedes pending statements above)
- Backend PR #8 merged at `b1a63ea9b601b784474a5fbd1a37ebd20f6f9028`; CI run #355: Python tests, Docker, PostgreSQL PASS. ONLY UAT Render deployment `dep-db6becvlk1mc73cksvi0` is LIVE on the merge commit; Production Render not deployed.
- Frontend PR #15 merged into UAT at `34b19e6e438ce8426ababea04839cf9a1984cd52`; Vercel reported Success. Browser purchase/receipt E2E is still unverified by owner.
- PR #16 restores earlier customer dashboard next-step and manual-payment guidance alongside monthly selector; Preview/build pending. Keep shared Meta untouched.

- Final UAT interface release: PR #16 merged at `8f083473` with Vercel Success; both month selection and dashboard/payment guidance retained. Browser three-month purchase/receipt E2E remains unverified; Production not deployed.


### UAT receipt preview update
- 2026-10-12 UAT receipt inline review: Backend PR #10 merged `c2eaf52d6d39d055782e1e56a79242948c07b349` (CI #383 PASS) and deployed ONLY to UAT Render `dep-db6bpsm7bikc73ca11i0` LIVE. Admin receipt route now uses inline disposition; same-origin framing restricted to authenticated receipt path. Frontend PR #17 merged to UAT `65c476ef563f8791054ddfe0578bc6667c8e3457`; Vercel release/build and manual receipt preview acceptance need verification. Production not deployed.
