# DirectPilot Next Actions

## Immediate environment safety actions — 2026-10-14

1. **DO NOT copy Render app variables to Neon PostgreSQL.** Neon currently hosts database only; Render remains the API execution environment. Keep every existing Render `APP_ENV`, `APPLICATION_SECRET`, Meta, Instagram token encryption, payment, auth, AI, callback and startup flag intact.
2. **CI-check/merge PR #28** offline names-only guard and guide; do not deploy or change Render Environment Variables. Review `docs/runbooks/render_neon_environment_preservation.md`.
3. **Privately inventory current Render environment variable NAMES** on trusted operator workstation/UI (no values shared). Compare against proposed Render post-cutover inventory using `python -m tools.render_env_key_audit --render-keys <private-names-file> --proposed-render-keys <private-names-file>`. Guard ensures no existing key name deleted; secret VALUE continuity needs separate trusted private review.
4. **Prerequisite gates** before the ONLY future Render DB URL change: safe Meta/Payexa webhook replay + all-writer freeze, independent protected backup, fresh dump after freeze, approved separate empty final Neon DB, full table/business parity, split-brain rollback, and explicit live Production owner GO.
5. No UAT change, Neon DB creation, Render variable write or live cutover until separately authorized. Source Render PostgreSQL Free expiry 2026-11-02 remains P0.

---


## 2026-10-14 EXECUTION PRIORITIES — Neon capacity and safe maintenance (LATEST)

**COMPLETED:** Neon API metering baseline `compute_time_seconds=1746`, `active_time_seconds=6888`; provisional ~0.485 CU-hour **not Console billed**. Idle→active read-only query succeeded (~6.65s connector round trip, not actual API cold-start). Backend write/callback inventory documented; operation-only plan created in `docs/runbooks/neon_free_usage_and_maintenance_plan.md`. Production/UAT untouched and no maintenance scheduled.

1. **P0 — build/test safe freeze-before-maintenance prerequisite.** Both Instagram webhook POST paths and Payexa GET/POST callbacks must be safely held/preserved/replayed with idempotency and no double customer replies/payments. Cover registration/login session writes, orders, receipt submission, admin approvals, workers, schedulers, token refresh and startup migration/seed/payment flags. Existing full freeze/replay implementation is NOT proven. Do not proceed relying on maintenance banner/provider retry guesses.
2. **P0 — verify Neon Free capacity from actual Neon Console quota counter** across representative periods and capture post-wakeup p95/p99 Backend latency using isolated traffic. API sample ~0.485 CU-hour estimate alone does not prove under-100 monthly CU-hour production usage. Free-plan quota exhaustion can stop compute.
3. **P0 — independently restorable protected offsite backup** and key/receipt continuity. Previous owner waiver of encryption was *only* for isolated restore rehearsal. No scheduled Neon snapshots reported.
4. **P0 — select maintenance date/time and impact after above PASS.** Proposed controlled write pause ≤120 min with T+90 Go/No-Go is a draft only; business owner must authorize exact window/possible customer messaging separately. Secure export path with short-lived source /32 if needed and revoke.
5. **P0 — final fresh Render dump/restoration with frozen writers.** Prepare separately approved new EMPTY Neon destination (proposed `directpilot_live` still uncreated), guarded restore revision, all-table counts + critical content parity, Meta/payment event watermark and reverse/split-brain rollback.
6. **HARD STOP:** no Production `DATABASE_URL` changes, real messages/payment activity, scheduled downtime, migrations, UAT data movements or Neon new final DB without the respective scoped owner go/no-go.

Internal target Oct 25, Render database expires Nov 2; protect customers/data above schedule speed.

---


## CURRENT PRIORITY ACTIONS — 2026-10-14 (after operator's Neon preflight PASS)

**Completed:** REAL Neon restored Production SQLAlchemy/psycopg/TLS/server-enforced READ ONLY preflight **PASS per owner/Codex**, hosted Neon SQL schema and 14 subscriptions/15 orders/1 payment checks independently PASS; three trial plans all 3 days; Render inbound IP allowlist=0. **Do not repeat `python -m tools.neon_readonly_preflight` as an outstanding gate unless the target/credentials/code materially change.**

1. **P0 — real Neon Free capacity:** provider now returns `compute_time_seconds=1746` and `active_time_seconds=6888`, not a verified billed CU-hour measure. Collect Neon Console consumption and trend over representative idle/active intervals, test autosuspend/cold-wake/connection handling and documented fallback before deciding Free is production-ready.
2. **P0 — protected independent backup:** preserve Oct 13 original and checksum; secure and independently test encrypted offsite recoverable fresh Render backup. Owner's no-encryption waiver was explicitly limited to the isolated rehearsal.
3. **P0 — owner-approved maintenance window and freeze contract:** read `docs/runbooks/production_neon_cutover.md`; agree on source write freeze (including signups, manual payments, approvals, Meta callbacks, workers), safe receipt/webhook replay/retention and exact acceptance criteria. Obtain separate explicit approval before modifications.
4. **P0 — final snapshot/restore/parity:** plan new **empty** Neon Production DB (proposed `directpilot_live`, not created yet); prepare safe reviewed restore CLI for that exact named target, fresh verified consistent Render backup during freeze, 82-table counts and finance/subscription/receipt/token metadata reconciliation, explicit abort triggers.
5. **P0 — rollback and go/no-go:** define split-brain prevention, backward replay for events after Neon writes, observation period and recovery drill; show owner the reviewed schedule and receive distinct live Cutover approval. **Do not** change Render Production `DATABASE_URL` or touch UAT before that.

**Deadline:** Render Free PostgreSQL source expires Nov 2 2026; internal target October 25; preserve data-integrity gates despite time pressure.

---


## EXECUTION QUEUE UPDATE — 2026-10-14 (LATEST)

**P0 deadline:** avoid Render Free PostgreSQL expiry `2026-11-02T11:59:46Z`; target controlled completion by Oct 25 without waiving data safety.

1. **NEXT ON TRUSTED LAPTOP:** check out latest `backend-main`; run `python -m tools.neon_readonly_preflight` and enter Neon direct restored-Production URL only into hidden local prompt. Share sanitized status, not credentials. SQLAlchemy real-data check NOT yet executed.
2. **NEXT PROVIDER USAGE:** obtain two Neon Console CU-hour readings across representative awake/idle period, verify pause/wake and cumulative usage. API reports zero compute seconds despite queries and is **not** reliable proof of capacity; plan Free quota alerts/fallback.
3. **NEXT RESILIENCE:** protect an independent encrypted restorable backup of active Render; Neon project has no saved snapshots and no snapshot schedule. Confirm no legacy receipt objects live outside PostgreSQL (one current inline receipt blob confirmed).
4. **NEXT CUTOVER PLANNING:** use merged `docs/runbooks/production_neon_cutover.md` (PR #26 `9ba207da`, CI 4/4 PASS). Approve controlled write/webhook/payment freeze, final fresh pg_dump, restored count parity, then a **new empty final DB** in independent Neon Production (proposed `directpilot_live`, **not created**, requires explicit approval). Test rollback and idempotent replay.
5. **P0 GO/NO-GO:** do not change Production DATABASE_URL, reboot apps with hidden seed/bootstrap flags, start Meta sends, merge UAT data or close DR gate until requirements PASS and owner separately approves. Render DB inbound IP rules currently empty (PASS); reopen only limited /32 during owner-approved source export and revoke afterward.

---


## EXECUTION QUEUE — 2026-10-13 (LATEST; supersedes older dated TODOs)

**P0 / Deadline:** Render Production Free PostgreSQL expiry **2026-11-02T11:59:46Z**. Internal goal **Oct 25**; prioritize resilient cutover with zero unacknowledged missing records over marketing tasks. No Production database cutover is approved yet.

1. **CLOSED — Render ACL mismatch (verified 2026-10-14):** independent Render API now returns `ipAllowList=[]` (zero temporary /32 inbound rules). No further network action; do NOT allow `0.0.0.0/0`. Only reopen time-limited /32 access if explicitly necessary/approved.
2. **P0 — complete actual restored-copy ORM read-only preflight:** from trusted local Backend repo (`backend-main`) run `python -m tools.neon_readonly_preflight`; privately enter independent Neon Production **DIRECT** connection URL for project `billowing-poetry-05589994` / `neondb`. No API startup, background workers, migrations, seeds, Meta, payments or writes. Return sanitized `NEON_READONLY_PREFLIGHT: PASS/FAIL` and counts. The tool/CI smoke are implemented and PASS, but laptop execution on the restored target is **NOT YET VERIFIED**.
3. **P0 — validate Free Neon CU consumption and sleep/wakeup:** Neon Free 100 CU-hour/month, 0.25–2 CU, idle suspend default, pooler off. Check Neon Console usage/quotas (API reporting 0 does NOT verify zero burn), log initial and subsequent CU-hour counters after representative idle/limited traffic, instrument alerts around ~70%/90%, validate wake latency and retry/backoff. Render `/live` health path already avoids DB queries; do not poll `/ready` so frequently it keeps Neon awake. Test conservative app pool settings **only** in isolated environment first.
4. **P0 — durable independent recoverable backup:** 2026-10-13 original PG custom dump verified by operator; **plaintext on unencrypted C:/D:, physical independence uncertain**, encrypted offsite copy OPEN. Owner deferred encryption for restore rehearsal ONLY. Secure an independent offline/encrypted recoverable copy and test extraction/checksum/restore. Never share dump, password or customer data in GitHub/chat.
5. **P0 — schedule controlled final sync:** since restored Neon is a point-in-time copy, agree on maintenance window and freeze writes, pause/queue or replay Meta webhooks and payment approvals safely; take **fresh consistent Render snapshot or verified delta**, re-reconcile all tables including orders, payments, customers, sessions, subscriptions and IDs. Preserve original backup and audit trail; avoid duplicate/replayed side effects.
6. **P0 — rehearsal of rollback with split-brain protection:** test how to return to Render or forward-recover safely after Neon writes. Do not treat DB URL reversal as safe once target accepts new writes; record clear abort conditions, time owner and measured RPO/RTO.
7. **P0 — explicit go/no-go:** only after steps 2–6 PASS, present operator a complete cutover plan and obtain separate explicit Production approval. Then set authorized Production backend DB URL only; monitor readiness/logs, authentication, subscriptions, payment receipts, inbox/Meta business functionality. Do not make UAT share data with Production.
8. **P1 — post-cutover reliability:** daily encrypted backups with tested restore, provider usage alerts, customer/GA4 conversion follow-up, admin/payment flows and 3-day new-trial expiry checks.

**Completed, no need to redo:** isolated Neon restore (82 tables, PG18.6, Alembic 0025; row-count equality reported PASS), PR #24 PG18 CI + PR #25 guarded read-only tool merged, latest CI `38401718878` **4/4 PASS / 905 tests passed / 7 skipped**, frontend `/solutions` LIVE READY. Both Backend Render services still LIVE on code `bfe67fd`; new repository-only checks were not deployed.

**SECURITY:** backups are sensitive, credentials must be requested only locally; neither UAT nor the live Render API should ever be pointed to the Neon restored copy until go/no-go approval.

---


> Execution queue. Read `AI_HANDOFF.md` first.
> Last SEO action reconciliation: 2026-10-11; other workstreams retain separately tracked readiness gates.

## P0 — Humanized UI / Motion Branding Production Release — CLOSED (2026-10-11)

**Status: PASS for deployment and owner-confirmed visual scope.** Frontend PR #9 merged to `main` SHA `f5f6a5399f938969b9307475eeed208f0e10988b`; Vercel Production `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` READY, both `directpilot.ir` and `www.directpilot.ir` correctly aliased, no alias error. GitHub `main` commit matched the deployment. The owner checked the live Production favicon motion and dashboard layout after hard refresh and approved both.

- Scope released: UAT-origin humanized product/marketing/admin UI, SVG motion glyphs, crisp animated D favicon, sidebar label-nowrap fix; Production GA4/SEO and signup events, 14-day trial messaging and manual card-transfer fixes preserved.
- No additional Redeploy or intermediate `release/humanized-ui-uat-20261011`-branch build is needed. Older preview `module_not_found` and Vercel free build quota issues are not failures of final `main` READY.
- No backend, DB, Meta, DNS, production payment settings or Vercel Authentication changes were made in this release.
- Remaining **separate verification**: full fresh authenticated customer/admin flows if changed or regression suspected; real GA4 `sign_up` E2E; post-recrawl SEO effects; specifically open admin-plan flow retest; Production DB durability and backup/restore before real customers. Owner visual PASS does not close those.
- UAT SHA `dd9dee1f573151cd7507877aa9a868db467c95ba` remains separate with READY deployment `dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`.

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

## P1 — SEO / GA4 Phases 3-8 Complete — Conversion E2E & Measurement OPEN

Status: **SEO PR #1-#5 MERGED / GA4 PR #6-#8 MERGED / FRONTEND PRODUCTION READY / GA4 PAGE_VIEW DELIVERY + REALTIME PASS / sign_up E2E UNVERIFIED / SEO RANKING EFFECT OPEN.**

- PR #6 — frontend `ae077e06915e5e280fbb5ff226ac5dd4d529891e`: consent-first GA4 tag, event bridge, limited sanitized marketing `page_view`, `signup_intent`, `pricing_plan_click`, `demo_start`, `blog_cta_click`, and `sign_up` after the backend register call succeeds; Production-only `NEXT_PUBLIC_GA_ID`, strict Preview/UAT isolation, privacy disclosure, CI tests and mobile Lighthouse workflow.
- PR #7 — frontend `31c348ab51c7dc6ae1d4c407c32da1c08a5b5c03`: corrected GA4 collection endpoint allowlists in Production CSP (no `unsafe-eval` and no ad tagging).
- PR #8 — frontend `d9a1a53a6171f3d417637d12cec66eed1832a07b`: repaired gtag.js queue compatibility by pushing JavaScript `arguments`, not spread Arrays, into `dataLayer`; shipped through tested PR with a narrowly justified lint exception.

- Historical GA4 PR #8 Production checkpoint (current UI release is PR #9 above): `d9a1a53a6171f3d417637d12cec66eed1832a07b`; Vercel deployment `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` = **READY** (https://vercel.com/mohcenp-9857s-projects/directpilot-web/EnejDGuCcotpf4kQrSQk7pnPsyRw). This supersedes the earlier SEO PR #5 release `e527c8f7e47a3259457f4efd72ded588eb3e26b9` / `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2`; those older SHAs remain valid **historical** checkpoints only.
- GA4 Web Stream: `https://directpilot.ir`, `DirectPilot - Production Web`, Measurement ID `G-9D1Z7HDYVZ`, GA4 Property ID `558426868`, GA4 reporting timezone `Asia/Dubai`. Vercel `NEXT_PUBLIC_GA_ID` is set for **Production only**; a fresh Production build is READY.
- Browser verification on 2026-10-11 **after PR #8**: granted consent; gtag.js loaded; `dataLayer` contains `page_view`; request to `https://region1.google-analytics.com/g/collect` returned HTTP **204** with `en=page_view`. GA4 Realtime showed **one active user**, and `first_visit`, `session_start`, `page_view` each observed once. This establishes end-to-end **page-view event delivery and Realtime ingestion**, not all-event/real-signup acceptance.
- In GA4, `sign_up` is defined as a **Key Event** (code-based, no default monetary value, once per event). **The actual `sign_up` delivery after a successful backend registration has NOT been tested**; do not mark conversion E2E PASS or equate `signup_intent` with completed registration.
- GA4 is natively linked to Search Console Domain Property `directpilot.ir`, and GSC Wizard's GA4 connection is separately verified: `sc-domain:directpilot.ir` ↔ `properties/558426868` under `DirectPilot - Production`. GA4 reports and blended GSC+GA4 sections are visible.
- GSC Wizard reports through 2026-10-10 initially showed GA4 zeros because collection was first accepted on 2026-10-11. Respect settled-data lag (~1-3 days), the GA4 launch boundary, site/session definitions, user consent and small samples; **do not** read historical zero as malfunction or claim ranking/conversion uplift. Google Search Console clicks and GA4 sessions are not interchangeable.

- Existing weekly automation **«پایش هفتگی SEO و GA4 DirectPilot»** updated (ID `6acb649a476c8191895050914165ee85`), **enabled**, next intended run Monday 2026-10-12 at approximately 09:00 **Asia/Dubai**, `flexible_schedule`. It now checks settled 28-day SEO windows, 10 indexed URLs, queries/landing pages/cannibalization/sitemap, and GA4 sessions, landing pages, engagement, `signup_intent`, `sign_up` / Key Events, with post-activation/date-alignment safeguards. This is an automation-instructions update; it does not change site code or GA4 settings.
- This scheduled task's automation record currently reports `notifications_enabled=false` and `email_enabled=false`; delivery/notification permissions should be reviewed by the owner separately if push or email alerts are expected. Do not falsely claim notification delivery is enabled.

### Exact next SEO / Analytics actions

1. **First settled GA4 reports (after 2026-10-11):** inspect GSC Wizard Analytics Overview / Channels / Landing Pages / Events for Sessions, Active Users, Page Views, Engagement and Organic Search; if first data is missing because of a 1-3 day reporting delay, check on a later settled day instead of calling the setup broken.
2. **Controlled conversion E2E:** after obtaining a safe test account/registration path, complete one genuine successful backend registration and confirm `sign_up` appears once in GA4 Realtime/Events/Key Events. Do not generate real customers or trigger paid billing solely to inflate conversions; report BLOCKED if no safe test path exists.
3. **Organic search attribution:** for `/`, `/blog/instagram-smart-direct`, `/instagram-direct-automation`, `/instagram-comment-automation`, `/pricing`, `/about`, compare separate GSC clicks/impressions/CTR/position with GA4 landings/sessions only in correctly defined comparable ranges. Watch cannibalization for Direct/Comment query clusters and indexing status for 10 tracked URLs.
4. **Post-release SEO effect:** do not claim improvement until Google has recrawled the modified pages and two comparable settled windows exist. Historical property-wide settled GSC baseline through 2026-10-04 was 14 clicks / 315 impressions / CTR 4.44% / average position 40.30; historical 2026-09-11—2026-10-08 page query snapshots: smart-direct article 88 impressions / 2 clicks, service 12 / 1, comment service 22 / 1. Windows are not interchangeable.
5. **Performance follow-up:** investigate homepage mobile Lighthouse lab bottleneck (Performance 74, LCP 2.74s, TBT 974ms) with profiler and a fresh controlled run before optimization; maintain separate CrUX field assessment. Avoid repeated SEO copy changes without evidence.
6. **Reporting automation:** weekly SEO+GA4 schedule now Monday 09:00 Asia/Dubai; notifications/email flags currently disabled in automation metadata and may require account-level enabling. Existing other legacy SEO schedules were not modified in this update.

No changes to payment settlement, manual card-transfer acceptance, Meta sending, backend readiness or database durability arise from GA4 measurement; these remain distinct workstreams.

## P0 — Admin Customer Automation Acceptance

Status: **DEPLOYED / OWNER RETEST PENDING**

- Production/UAT frontend SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- UAT Vercel: SUCCESS.
- Production Vercel: SUCCESS.
- In Production Admin -> Customers & Stores:
  1. select the pilot customer/store,
  2. click **Manage Automation**,
  3. verify fields for trigger location, match type, phrase/keyword, response, priority and enabled state,
  4. create the deterministic rule for `قیمت`,
  5. verify it appears in the selected store's rule list.
- Do not mark PASS until owner confirms the live Production behavior.

## P0 — Frontend Admin Plan UX Retest

Status: **DEPLOYED / OWNER RETEST PENDING**

- Production and UAT source SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Vercel Production deployment: SUCCESS.
- Verify on Production that:
  - clicking `ساخت پلن` does not jump the page,
  - invalid input stays inline without browser scroll-to-invalid,
  - typing `Test_1` normalizes to `TEST_1`.
- Do not mark PASS until owner confirms the live behavior.

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

Status: **PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E PASS**

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
1. In Production Admin -> Customers & Stores, select the pilot customer/store and use **Manage Automation** to create/enable a harmless deterministic rule:
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


## P3 — Future Product Track

### Telegram No-Code AI Bot Builder

Status: **PARKED**

- Preserve as a future product concept.
- Candidate foundation: Telegram Managed Bots + shared multi-tenant runtime.
- Do not implement during current DirectPilot Production readiness work.


## Immediate Action — Controlled Meta Outbound E2E
1. From the second Instagram account, send `قیمت` exactly once to the Production pilot account.
2. Do not send a second message or retry manually.
3. Inspect Production logs for deterministic rule handling and provider delivery.
4. Verify exactly one outbound response, no AI fallback, no duplicate send and no own-message echo loop.
5. If any invariant fails, disable Production send before further diagnosis.


## Immediate Retest
1. Send the configured pilot keyword exactly once now that the UAT relay is fully started.
2. Do not manually retry again after that message.
3. Inspect UAT relay and Production logs for inbound, deterministic match, outbound delivery, dedupe and echo suppression.


## Meta Controlled E2E — COMPLETED
Status: **PASS**
- Deterministic Meta path passed end-to-end in Production.
- Exactly one outbound delivery observed.
- AI fallback did not run.
- No duplicate second send or echo loop observed.
- Production send was returned to disabled after acceptance.
- Do not repeat this milestone unless regression evidence appears.

## Current Highest Priority
1. Production database durability and backup/restore acceptance before real-customer onboarding.
2. Production LLM provider/model verification.
3. Payment-provider environment verification and real-provider acceptance.
4. Forgot-password recovery provider selection/verification.


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


## Production LLM — Next Action

Status: **BLOCKED ON SECURE PRODUCTION CREDENTIAL**

Verified:
- Runtime/provider diagnosis: PASS.
- UAT LLM config presence: PASS.
- Production selected-provider credential: MISSING.
- Production Groq credential/model: MISSING.
- Backend health: PASS.
- No secret exposure: PASS.

Next:
1. Add a Production-specific LLM API credential securely in Render; do not paste it into chat.
2. After credential provisioning, configure the selected provider/model using non-secret environment settings.
3. Verify startup metadata and provider connectivity.
4. Run one controlled unmatched Instagram message so AI fallback executes once.
5. Verify AI completion, one outbound delivery, no duplicate/echo loop, quota accounting, and no secret/prompt leakage in logs.


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


## Production LLM / AI Fallback — COMPLETED

Status: **PASS**

- Production Groq configuration: PASS.
- Supported model `qwen/qwen3.8-27b`: PASS.
- Controlled unmatched Instagram -> AI -> Meta E2E: PASS.
- One Groq request / one completion / one Meta delivery.
- No AI failure, outbound failure, duplicate send, or echo loop.
- Meta send returned to disabled after acceptance.
- Do not repeat this milestone unless regression evidence appears.

Remaining readiness priorities:
1. Production DB durability + backup/restore remains OPEN but owner-deferred.
2. Payment-provider environment and real-provider acceptance.
3. Forgot-password verified delivery provider.
4. Broader Production Meta-send policy/customer rollout only after remaining readiness gates.


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

## Immediate Payment Actions
1. Add the Production-specific `PAYEXA_API_KEY` directly in Render for `directpilot-api`; never paste the value into chat.
2. Confirm `directpilot.ir` is verified/allowed as the callback site/domain in the Payexa merchant panel.
3. Re-verify sanitized Production startup metadata shows credential_configured=true.
4. Build/enable one controlled Payexa checkout acceptance path without changing backend-authoritative subscription activation.
5. Run sandbox acceptance first if needed, then one controlled Production provider transaction; verify callback, server-side verify, idempotency, duplicate callback behavior, ambiguous-create handling and subscription activation.


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

## Current Payment Next Action
1. Verify Production has an active/default payment card configured.
2. Verify customer Production checkout shows that card.
3. Run one controlled manual payment E2E: create paid order -> show card -> upload test receipt -> Admin sees submitted payment/receipt -> Admin approves -> order becomes paid -> subscription/entitlements update.
4. Verify reject/resubmit path separately if needed.
5. Do not pursue Payexa unless the owner explicitly reopens automated gateway work.


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

## Immediate manual-payment action
1. In Production Admin -> Payments -> Payment Cards, create/activate the intended real destination card and make it default.
2. Re-run safe readiness check and require `active_default_cards=1`.
3. Execute the controlled manual payment E2E and close the payment gate only after subscription/entitlement verification.


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

## Immediate payment continuation
1. Refresh Production Admin -> Payments.
2. Confirm the just-created card is visible and marked active/default.
3. Do not create a duplicate card if it is already present.
4. Continue the controlled manual-payment E2E after confirmation.


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

## Manual Payment Follow-up — Gate Closed (2026-10-11)

- Production Manual Payment E2E is PASS and requires no further acceptance work unless a regression is reported.
- Do not create additional test purchases or rerun one-shot approval helpers without a new controlled-test reason.
- Keep Payexa/KPay deferred unless explicitly reopened by the owner.
- Preserve payment-card configuration and receipt/audit history.
- Next Production-readiness work should move to remaining non-payment items. Production DB durability remains owner-deferred; do not upgrade or spend without explicit approval.


## 2026-10-12 — UAT webhook isolation next actions
1. Run CI for the offline regression test (`tests/test_instagram_webhook.py`) and fix any failure before merge.
2. Verify regression locally/CI only: disposable SQLite, no production calls, no Meta traffic, no UAT Neon writes.
3. After merge, read-only review Render UAT event logs / Neon counts; live Meta delivery and automated replies remain NOT VERIFIED.
4. Do not change Meta Developers settings, shared app OAuth/webhook configuration, or existing Production-bound webhook relay; seek explicit approval before any real delivery test.

## 2026-10-12 — Release multi-month card-transfer purchase to UAT
1. Confirm backend PR #8 CI including order snapshot/payment amount/90-day approval; resolve any failures before merge.
2. Merge backend PR #8 after CI; manually deploy ONLY directpilot-uat-api; verify Render LIVE commit and /ready; Production auto deploy stays off.
3. Confirm frontend PR #15 Preview build and test; merge to branch UAT after backend is live; verify uat.directpilot.ir targets the new commit (not Production).
4. Owner UAT: choose 3 months for Automation; verify IRR 14,700,000, 90 days, correct active payment card, upload receipt and admin approval; check effective subscription expiry.
5. Reconcile final CI / deployment status in all five continuity docs. Keep Meta shared and untouched.

### Release update — 2026-10-12
- Completed: Backend #8 CI PASS, merged/deployed ONLY to Render UAT (LIVE); Frontend #15 merged to UAT, Vercel Success.
- Await PR #16 Preview before merging to UAT. Then request owner to open UAT billing, select 3 months Automation, verify 1,470,000 toman and 90 days and card copy; no money transfer required for quote verification.
- Separate supervised manual receipt/payment approval E2E remains pending. Confirm subscription end date and AI aggregate quota before any Production promotion. Keep Meta settings fixed.

- Final UI gate: PR #16 merged into UAT at `8f083473`; Vercel Success. Manual 3-month order verification remains open.


### UAT receipt preview update
- 2026-10-12 Receipt preview acceptance: confirm Vercel Preview Success on UAT commit `65c476ef`, open UAT admin Payments, select submitted receipt, verify JPG/PNG and PDF appear inline without automatic download, ensure approve/reject still work; cross-check 401/403 access and iframe same-origin restriction. Production untouched.


### 2026-10-12 UAT compact payment UI
- 2026-10-12 UAT acceptance: verify frontend merge `1cae8c08` Vercel Success and `uat.directpilot.ir` alias. In Admin Payments confirm compact facts, JPG/PNG natural image dimensions and bounded PDF viewer, approve/reject unchanged. In customer Billing confirm paid plan is visible and only `ارتقا پلن` button wording appears in active-plan upgrade offers. No Production promotion.


### Production promotion preflight (2026-10-12)
- 2026-10-12 Next release tasks: Resolve production-only 20 frontend commits vs 83 UAT commits under PR #19 and safeguard GA4/CSP. Verify Production DATABASE_URL target without disclosing it, obtain read-only schema/plan comparison and predeployment backup/rollback. Avoid data copy from UAT. Ensure AI_ASSISTANT_V1 and AUTOMATION_V1 production catalog states only after safe read-only inspection. After CI and DB preflight, deploy Backend Production then Frontend Production; run smoke tests and rollback if failed. Current status: production rollout not executed.


## 2026-10-12 — Finalize Production promotion
1. Verify new `directpilot.ir` Vercel deployment matches `main` SHA `06ebe316e5193f111ebd4b0733ee85c406d0a56e` (PR #20). Vercel connector cannot list current project; check Vercel team dashboard or CLI; do not claim READY from Git merge alone.
2. Production smoke: customer login/session, select 3 months Automation price IRR 14,700,000 and 90 days, customer card display/copy, admin inline receipt JPG/PNG/PDF sizing, approve/reject, active-plan detail and «ارتقا پلن» CTA. Do not create new real payments just for analytics.
3. Read-only verify Production plan catalog, confirm `AUTOMATION_V1` and whether `AI_ASSISTANT_V1` exists/active/purchasable; securely add only approved reference plan if missing, preserving existing accounts, payments and cards. No direct SQL access via hosted Render MCP due empty external allowlist; do not relax access rules.
4. Establish verified backup/restore before any new Production DB mutation/plan seed or schema changes; current FREE Postgres expires 2026-11-02, cost upgrade deferred by owner.
5. After evidence, update continuity docs again with exact Vercel ID/Production catalog acceptance. Preserve GA4, SEO, Meta shared relay and production data isolation.


## Next Production promotion actions — 2026-10-12
1. Finish Backend PR #15 CI for safe `0024_ai_assistant_v1_catalog` (Postgres smoke, Docker, comprehensive Python tests); confirm existing UAT AI row is untouched in a UAT dry-run deploy, then manually deploy migration to Production and verify `Alembic current head` + plan catalog readback without exposing DB.
2. Reauthorize/extend Vercel connection to actual `directpilot-web` project/team or have owner provide verified Vercel Production deployment status matching `main` SHA `06ebe316`. Do not equate GitHub merge + CI to READY deploy.
3. Confirm Production public/admin plan catalog lists Automation + paid AI separately with correct 30-day prices/limits; verify three-month Automation quote IRR 14,700,000 and 90-day snapshot and AI paid option without creating duplicate/real payment needlessly.
4. Smoke-test Prod login/session, admin payment receipt inline preview, active subscription labels/upgrade CTA and GA4 consent-first events. Do not change shared Meta OAuth/webhook/relay or trigger real Instagram messages.
5. Production Free Postgres has no accepted off-host backup/restore and expires 2026-11-02; preserve owner-deferred paid-upgrade decision and keep real-customer durability gate OPEN. Update these five files after actual rollout with exact commit/deploy IDs and outcomes.


## Remaining Production promotion gates — 2026-10-12
1. COMPLETED: paid AI plan migrated 0024 in UAT and Production; exact Render deployment IDs and independent Production public catalog PASS are in CURRENT_STATE.md. Do not re-run database migration or seed changes needlessly.
2. Verify Vercel Production deploy/alias `directpilot.ir` READY and deployed commit `06ebe316e5193f111ebd4b0733ee85c406d0a56e`. Current Vercel plugin lacks project authorization; owner may need to grant access to `directpilot-web` under their Vercel team. GitHub merge/CI is not proof of live deployment.
3. Authenticated Production customer + admin smoke: compact payment facts, image/PDF receipt fit and no forced download, active plan names, `ارتقا پلن`, paid AI visible in billing, 1–12 month prepaid selection and 3-month Automation quote IRR 14,700,000/90 days. Avoid test payment transfers and duplicate creation unless specifically authorized.
4. Preserve Production marketing GA4 consent/SEO and shared Meta routing without changes. Production manual payment active default card exists. No customer/receipt/card/token transfer from Neon.
5. Free PostgreSQL plan expires 2026-11-02 and has no accepted off-host backup restore; paid infrastructure upgrade remains owner-deferred and no real customer durability acceptance claimed.


### Mobile login overlay hotfix — 2026-10-12
- 2026-10-12 Mobile login final acceptance: check Production Vercel deployment is READY with main SHA 69632c8a6e0bb1ba66933d3f8b8167823fb6bcf9; test https://directpilot.ir on iPhone Safari/mobile Chrome: menu -> ورود must close menu and display /login; test tapping logo, keyboard/Escape close and safe-area. If unable to confirm runtime, do NOT mark bug fully resolved. Previous backend and AI catalog PASS remain valid.


### Customer Dashboard UAT UX (2026-10-12)
- 2026-10-12 Customer dashboard visual acceptance: verify UAT Vercel READY deploy at merge SHA `00d29a89` (Vercel connector may lack permission). Test desktop and mobile overview, current active paid plan, empty trial or unpaid customer, one submitted/pending payment, Instagram connecting and unknown API cases. Confirm customer `گفت‌وگوها` menu and quick link absent; direct `/dashboard?section=inbox` returns overview, not conversation UI. Confirm responsive quick links and mobile section menu closes after click. No deletion of stored conversation records. Once owner approves, selectively promote Frontend PR #23 features to Production while retaining GA4/SEO/CSP; Backend/DB/Meta not part of this UX release.


### Customer Inbox follow-up — 2026-10-12
- HIGH PRIORITY UAT: Open Vercel `directpilot-web` Deployments and verify latest READY Preview for branch `UAT` has SHA `16e2547d0b5d2815209bcba931cf76b52afbc7dc`. Existing UAT domain is associated with UAT branch, but connected Vercel API returns 403/404 and cannot verify deployments. If absent, trigger deployment from the latest UAT branch (do NOT redeploy an older SHA). Open UAT customer dashboard in a fresh tab, verify no online conversations UI or `section=inbox`, and report screenshot if still visible. Backend customer conversations remain preserved.


### Next actions after 2026-10-13 verified deployments
- HIGH: Selectively promote generic /solutions marketing landing and top navigation from UAT to Production; avoid copying the entire UAT catch-all page over Production SEO/three-day copy. Require Production CI PASS and Vercel READY.
- QA: Create new isolated UAT registration; verify both free plan product families activate for exactly 3 days, and prior subscriptions retain current_period_end. Avoid modifying historical customer records.
- Verify Production migration 0025 status through approved secure DB path if available; Render database external read-only connector is blocked by empty IP allowlist. Backend Production deploy LIVE.
- Conduct marketing /features, /solutions, /demo mobile and desktop acceptance. Existing verified SHAs: frontend Production 6f383fc, UAT fb340b7, backend bfe67fd. Previous UAT Vercel 403 limitation is resolved.


### Production Solutions promotion verified — 2026-10-13
- Frontend PR #29 merged at commit `79b8fad33b72e350b644162f69439d8c3e777471`; Production CI PASS; Vercel deployment `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP` READY and aliases `directpilot.ir`, `www.directpilot.ir` active. General `/solutions` page and links promoted from UAT selectively, with shops/services/education/salons only as examples. Existing 3-day trial copy, SEO, GA4 and payment flows preserved. This supersedes earlier notes stating generic Solutions Production promotion pending.
