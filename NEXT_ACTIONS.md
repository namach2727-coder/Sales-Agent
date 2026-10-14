# DirectPilot Next Actions

## 2026-10-14 — CANONICAL UAT DOMAIN RECONCILED: branch, API, database and rollback

**Permanent owner instruction: all UAT browser acceptance MUST use `https://uat.directpilot.ir`, not temporary Vercel Preview URLs.** Prior temporary Preview strategy has been superseded by owner directive to consolidate. User should not have to repeat this or the PostgreSQL BYTEA/no-R2/four-month historical receipt requirements in future chats.

**Frontend source-of-truth:** GitHub `namach2727-coder/directpilot-web`, branch **`UAT`**. Previously blocked archive/auth fix feature PR **#31 MERGED** after full CI SUCCESS (tests, type-check, lint, Next.js build); merge commit `35aed23845b950fa4ee4800a6453eba843ce1a6d`. The branch now contains admin customer/email/date archive search, preserved versions/timeline UI, improved immediate Login form and stale session race protection, and corrected public trial claims to match not-yet-confirmed catalog. Its rollback snapshot branch is `backup/uat-before-vercel-neon-sync-20261014` at SHA `a8764a7dc9b4144a0edbfa07afc8ca4bb3667864`.

**Domain/environment contract (READ BEFORE DEPLOYING):** Vercel Frontend project `directpilot-web` ID `prj_w46jn80pmeOpoIZ5KZmQiY7GfKDl`. Domain `uat.directpilot.ir` VERIFIED, Git Branch EXACT `UAT`, Preview target and no Production custom environment. Branch-specific Vercel Preview variables `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app` and `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir` (scope **only gitBranch=UAT**). Generic Preview, feature Preview and actual Frontend Production env vars are intentionally unchanged. Next.js routes `/api/v1/:path*` to standalone UAT backend with same-origin cookies. Do not configure domain on feature Preview or point canonical UAT to Render.

**Actual UAT frontend deployment:** UAT Git push automatically generated Vercel READY deployments; latest observed `dpl_73wqwyWzY2PAGB6D3H5gXrH1DqYw` SHA `fd23cc6c7855db7d485051bd434e4364704acbb8` READY, with Vercel alias `uat.directpilot.ir` confirmed pointing to this deployment. This post-merge commit only adds a read-only GitHub Actions domain-smoke workflow on top of the PR #31 merged code. Vercel Production `directpilot.ir` and `www.directpilot.ir` still bind the separate `main` deployment: DO NOT change those aliases or environment variables.

**Backend/Neon UAT:** standalone Vercel Backend project `directpilot-uat-api`, GitHub branch `migration/vercel-uat-fastapi-20261014`; live API `https://directpilot-uat-api.vercel.app`. Independent Neon project `round-shape-42044596`, main branch `br-autumn-rain-arxm147n`, database `neondb`, Alembic **`0027_traceable_receipt_versions`**. Real API GitHub Actions smoke previously PASS on `/ready` with `database:available, migration:current`, `/live` 200 and `/version` environment UAT. UAT database existing receipt blob backfill 2/2 matched, snapshot `snap-patient-dawn-arkxewpc` restored on independent rehearsal branch. Product image binary and receipt versions both use PostgreSQL BYTEA, no R2/S3.

**Evidence still OPEN:** New Github Actions `Official UAT Domain Smoke` checks 200 /login HTML, unauthenticated same-origin `/api/v1/auth/me` 401 JSON, versioned receipt API auth guard 401 (reject legacy Render 404), UAT Backend /ready and disallow indexing via /robots.txt. At this checkpoint this workflow is **running**, not a PASS. The user's actual browser UAT login/session/navigation/logout, admin receipt history by customer/date, actual dummy image upload/retrieval/delete/redeploy and historical versions must be tested after domain smoke. Check exact latest workflow results rather than relying on the checkpoint text. If domain smoke fails, investigate DNS/aliases/rewrites/routing first; avoid silent Production changes.

**Production firewall and final cutover:** Actual DirectPilot Production Render API/Postgres authoritative; Neon Production `directpilot_live` has not undergone fresh final migration. Real Production cutover requires source backup + independently restorable offsite copy, writer/Meta/Payexa webhook freeze & replay, fresh migration with business row/count/value parity, rollback drill, fully accepted UAT and explicit owner GO. Vercel Hobby's restrictions on commercial use must be resolved before routing paying customers. **Never claim UAT accepted solely from a Vercel READY status.**

**Permanent cross-chat documents:** read `AI_HANDOFF.md` → `PROJECT_ROADMAP.md` → `DECISIONS.md` → `CURRENT_STATE.md` → `NEXT_ACTIONS.md`; these five are canonical, and this update supersedes previous notes saying the UAT domain still points to an old branch. Read live deployments and workflow statuses after them.

---


## 2026-10-14 — UAT login/account-check latency: isolated Preview UX fix

**Owner-reported problem:** On opening the new isolated receipt-history UAT frontend Preview, the Login area stayed on “بررسی حساب” / checking account for an unusually long time.

**Code diagnosis:** Public header `components/layout.tsx` rendered **only a spinner** until `useBrowserSession()` completed `GET /api/v1/auth/me`. The shared `lib/api/client.ts` READ policy allows 30s timeout and one safe retry with backoff, so slow/cold Backend/Neon or network could leave the Login CTA unavailable for roughly 60 seconds (upper bound, not a measured production latency). `components/portal.tsx` also hid the real Login form until the session check finished.

**Preview-only fix IMPLEMENTED:** Frontend GitHub repo `namach2727-coder/directpilot-web`, branch `feature/uat-payment-audit-history-20261014`, SHA `7a1ce4ba09d3edcaef88c2280823df3d1f11622f`. Public header immediately shows “ورود” and register CTA while the session check continues; actual Login form is usable during check and still redirects an already authenticated principal based on its server-verified role. In `lib/auth/browser-session.ts`, a monotonic session epoch prevents stale `/auth/me` from overwriting newer completed login/logout. **No authorization bypass, no token storage and no Production change.** Vercel Preview deployment `dpl_GWUMgWTf3cMcgbor6fdnPzTkjY6w` READY at `https://directpilot-3595ydido-mohcenp-9857s-projects.vercel.app`.

**Evidence boundaries:** GitHub Actions tested 215 frontend cases; 213 PASS including 3 new auth/UX tests, 2 FAIL are unchanged existing trial-commercial-copy tests (also failing in prior build). A Vercel READY build is verified, but actual user-perceived speed improvement and server `/auth/me` latency need browser/network timing confirmation. Do NOT claim backend cold start fixed. The UAT Backend `https://directpilot-uat-api.vercel.app` had previously passed /ready, /live, /version and Neon 0027 checks. UI improvement removes the blocking Login gate, not remote request time.

**Next:** User opens corrected isolated Preview in a fresh/incognito tab and checks whether the Login button/form appear immediately, authenticates with UAT customer/admin, verifies refresh/logout and expired-cookie behavior without regression. If submitting credentials is still slow, measure in DevTools Network `/api/v1/auth/login` and `/api/v1/auth/me` TTFB/cold start and evaluate Vercel Function/Neon performance separately before further changes. **Do not promote PR #31 to shared UAT or Production until accepted.**

**Permanent requirements remain unchanged:** PostgreSQL/Neon BYTEA for product images and every receipt version, customer receipt traceability for 4+ months, no R2/S3. Five canonical files must remain cross-chat current (`AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`). Production Render/Neon cutover remains blocked by source backup/freeze/parity/rollback and commercial hosting eligibility.

---


## 2026-10-14 — LIVE UAT VERCEL GIT/HEALTH PASSED (supersedes earlier deployment-blocked checkpoint)

**Verified technical deployment:** The owner connected GitHub `namach2727-coder/Sales-Agent` and corrected Vercel Production Branch Tracking **inside standalone UAT project only** to `migration/vercel-uat-fastapi-20261014`. Git push now triggers Vercel UAT production-target deployments; backend deployment `dpl_G8sFmEPDs5Lx7f1oaQwWmAZF1ywo` at commit `e8e4a1c07c02ff6b5cfc32090f719ce4aa68657b` verified READY, with Git source `migration/vercel-uat-fastapi-20261014`. This is *NOT* the commercial DirectPilot Production project.

**Independently executed real public HTTP checks:** GitHub Actions workflow `UAT Vercel API read-only smoke` job **PASS** against `https://directpilot-uat-api.vercel.app`: `/ready` returned `{"status":"ready","database":"available","migration":"current"}`; `/live` HTTP 200 `{"status":"alive"}`; `/version` HTTP 200 with `environment: uat`. This confirms API→Neon UAT migration 0027 basic connectivity, *not* full business workflows.

**Receipt archive UI:** A dedicated Vercel **Preview-only** Git-branch-scoped `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app` was added to frontend project `directpilot-web` only for `feature/uat-payment-audit-history-20261014`. A documentation-only Git push at frontend SHA `41ca3a4cf57c4025ef3c1e323b322a4664a988f2` triggers a fresh Preview build. Frontend PR `namach2727-coder/directpilot-web#31` is NOT merged. Do not assert the browser receipt-history UI is manually accepted until customer/admin smoke and safe dummy receipt version tests pass.

**Previous checkpoint saying deployment was blocked by Vercel 403 is superseded.** The Vercel connector still cannot fetch `/ready` or runtime logs due to authorization 403, but GitHub-hosted external HTTP smoke succeeded. Owner must not be asked to reconnect Git.

**Next gates:** confirm exact frontend Preview READY, then user-visible UAT browser tests of admin customer/email/date lookup, previous and current receipt versions, timeline, access denial; test dummy product image upload/preview/delete and redeploy persistence without real payments/Meta sends. Verify app/DB ownership, long-term retention policy and independent backups before treating UAT complete. UAT Neon before-migration snapshot `snap-patient-dawn-arkxewpc` had restore test passed; original UAT database is now Alembic 0027 with 2 historical receipts byte-parity checked.

**Permanent architecture:** PostgreSQL/Neon BYTEA only for receipt versions and product images (NO R2/S3); prior receipt versions must be retrievable four months later. Vercel Hobby is not an approved commercial Production solution; Render Production and authoritative Render DB, domain and Meta callbacks remain unchanged. Final Production transfer requires independently recoverable source backup, writer/webhook freeze, final fresh data migration, count/value parity, rollback and explicit GO.

---


## 2026-10-14 — UAT Git integration connected; branch tracking/deploy still blocked

- **Owner-confirmed screenshot PASS:** Existing Vercel project `directpilot-uat-api` (project `prj_Kt665OcJisA7WMTA2YnGi7KSyT3b`, team `mohcenp-9857s-projects`, Hobby) is NOW connected in Project Settings → Git to GitHub `namach2727-coder/Sales-Agent`; do not advise user to connect it again.
- Vercel team member `mohcenp-9857` is OWNER. Git integration is no longer missing.
- **Deployment remains BLOCKED:** Latest observed deployment `dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR` is READY from *old* API commit `c05a5a76def84b9495bf1b361f910a9194d58a59`. Post-connection new API deployment request for exact UAT commit `96611ce1500936b10d5836185a5d14c78b886035` returned HTTP 403 forbidden. No new Git-triggered backend deployment has appeared. READY on old code is not UAT acceptance.
- **Immediate human UI gate:** open `https://vercel.com/mohcenp-9857s-projects/directpilot-uat-api/settings/environments` → Production → Branch Tracking, inspect and set this *UAT-only project's* production branch to `migration/vercel-uat-fastapi-20261014` and Save (not `main` or `backend-main`). This “Production” is internal to isolated UAT project, **NOT** commercial DirectPilot Production. If a Create Deployment button becomes visible after Git connection, use exact branch and commit, and inspect project/env target before publishing. User should report screenshot; after correct tracking, push reviewed UAT-only commit or trigger dashboard deployment.
- **Important:** Vercel Backend UAT env vars are currently targeted to that UAT project's Vercel Production environment; preview deployments must not be assumed to include those vars. Before deployment, verify `DATABASE_URL` is UAT Neon `round-shape-42044596` / `neondb`, never Render Production or Neon Production. Do not disclose values or secrets.
- **Already verified:** independent Neon UAT `round-shape-42044596`, `br-autumn-rain-arxm147n`, `neondb` now Alembic `0027_traceable_receipt_versions`; 2 existing receipts copied, 2/2 parity; pre-migration snapshot `snap-patient-dawn-arkxewpc` restored to test branch. Backend UAT code on branch SHA `96611ce...`, has migration-compatible code, CI passed. None of this proves deployed API matches schema until Vercel moves to that SHA and `/ready` validates.
- **Keep owner architecture requirements across chats:** PostgreSQL BYTEA for all current product images and manual payment receipts; complete customer-level receipt traceability including all versions after rejected reuploads and 4+ months; NO R2/S3. Five-file canonical read order: `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. Do not ask owner to restate. Production Render and its authoritative DB remain untouched; do NOT cut over Production before full UAT acceptance, source freeze, final backup, replay/parity, rollback and explicit GO. Vercel Hobby has commercial-use restrictions.

---


## 2026-10-14 — NEW VERIFIED CHECKPOINT: Neon UAT migrated, Vercel deployment BLOCKED

**Permanent owner-approved design:** PostgreSQL/Neon BYTEA stores BOTH manual-payment receipt evidence and product images. No R2/S3. Receipts must be queryable by customer/order/payment at least four months later and retain all earlier uploads after a rejected replacement. These are non-negotiable cross-chat decisions; do not ask the owner to repeat them.

**SUCCESS — Real independent Neon UAT:** project `round-shape-42044596`, main branch `br-autumn-rain-arxm147n`, database `neondb`, advanced from Alembic `0025_trial_three_days` to `0027_traceable_receipt_versions` in a single controlled SQL transaction reproducing additive Alembic 0026 + 0027. Added `product_media_assets.image_data BYTEA` and `manual_payment_receipt_versions` with six indexes and checksum/identity metadata. Non-destructive backfill copied 2/2 existing receipts into version 1 with identical bytes and SHA-256. On UAT before change, payment rows=2, blob rows=2, product media=0. NOT Production.

**SUCCESS — Backup/restore rehearsal:** Neon snapshot `snap-patient-dawn-arkxewpc` (`uat-pre-0026-0027-20261014`) created from UAT branch before migration. Restored into independent `br-spring-dream-arhxt1ji` and verified 2/2 payment receipt bytes and `0025`; applied same additive schema on the restored copy first and verified `0027` and 2/2 byte-level parity. Snapshot restore is a same-provider recovery test, **NOT** an independent encrypted off-provider backup or proof of four-month retention policy.

**SUCCESS — GitHub code:** backend image PR #34 and receipt traceability PR #36 passed four CI jobs each (Python, Docker, PostgreSQL 17 smoke, PostgreSQL 18 compatibility). Both merged **ONLY into branch `migration/vercel-uat-fastapi-20261014`**, HEAD `96611ce1500936b10d5836185a5d14c78b886035`, *not* `backend-main` or Render Production. Frontend PR #31 in `namach2727-coder/directpilot-web` contains archive/admin UI but remains open; isolated preview exists without E2E against updated API.

**BLOCKED — Vercel UAT runtime:** standalone Vercel project `directpilot-uat-api` ID `prj_Kt665OcJisA7WMTA2YnGi7KSyT3b` latest inspected deployment still **`dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR` (READY) from OLD commit `c05a5a76def84b9495bf1b361f910a9194d58a59`**. Both production-target (UAT project only) and preview-target create_deployment calls returned **HTTP 403** forbidden. Merging to linked Git branch did NOT automatically create a deployment at time of check. IMPORTANT: a READY OLD deployment is not a passing new backend; after UAT DB moved to 0027, old API may report `/ready` migration mismatch. **Do not claim UAT transfer or functionality complete or begin Production cutover.**

**Next exact action to clear gate:** owner/Vercel account holder must use `https://vercel.com/mohcenp-9857s-projects/directpilot-uat-api/deployments` → Create Deployment, select **branch `migration/vercel-uat-fastapi-20261014` and exact commit `96611ce1500936b10d5836185a5d14c78b886035`**, choose intended isolated UAT production environment; verify no environment variable points to Production Neon/Render DB. If blocked, inspect Vercel Git integration and Hobby owner/commit-author deployment authorization, do not bypass permissions. Deploy only after reviewing connected source and environment. Verify `/ready` reports `migration=current`, actual deployment SHA and database. Then use isolated frontend archive Preview, small dummy product image upload/preview/delete, dummy receipt replace/retrieve both versions, admin customer/date search, event timeline, auth/RBAC, session, persist across redeploy; Meta/payments should not perform real actions.

**Production hard stop:** production Render backend/source DB remains authoritative; no fresh production snapshot/export-to-Neon-final, writer/webhook freeze, source-vs-target parity or production rollback testing confirmed. Production Neon `directpilot_live` should not be treated as restored and Production domains or Meta callbacks must NOT move until independent explicit GO. Hobby Vercel terms restrict commercial use; resolve hosting policy and costs before real revenue traffic.

**Five-file read order:** `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. Keep these in sync as each gate clears.

---


## 2026-10-14 — PERMANENT OWNER REQUIREMENT: receipt traceability after four months

**Cross-chat non-negotiable acceptance criterion:** Admin must be able to identify **every manual transfer receipt belonging to a particular customer**, retrieve the original image/PDF even **four months or more** after upload, identify the associated tenant/customer/order/payment, original submission time, checksum, approval/rejection sequence and acting administrator, and retrieve **earlier receipt versions after rejection and replacement**. Customer data and payment history MUST NOT be automatically overwritten or purged. This is a distinct requirement from image storage, but both rely on **PostgreSQL/Neon BYTEA**. **Never suggest R2/S3**, the owner has explicitly declined those providers.

**Current deployed implementation:** `manual_payments` already keeps the current `receipt_data BYTEA`, `receipt_sha256`, `receipt_size`, `receipt_content_type`, customer `user_id`, `tenant_id`, `order_id`, timestamps and status; `commerce_audit_logs` records status transitions. However, **after rejected re-upload the previous file is overwritten**, and the admin UI has no historical by-customer/date search. Existing receipts are not automatically deleted based on age, but a four-month availability SLA is **NOT YET VERIFIED** without independent restorable backups.

**Pending UAT implementation:** Backend stacked PR **#36** (based on PostgreSQL-image feature PR **#34**, neither deployed) introduces additive Alembic **`0027_traceable_receipt_versions`** after 0026: one preserved binary receipt and SHA-256 per upload, backfills existing PostgreSQL receipts as version 1, tracks customer/tenant/order/payment IDs and upload timestamp, admin `payment.read`-protected history/download/audit endpoints and customer-email/date history search. No existing receipt bytes are deleted. Backend regression tests simulate review 125 days after upload. This is PR/code-only until CI, independent UAT backup, migration and browser acceptance are verified.

**Long-term policy:** no automatic deletion or age-based purge of payment receipts or related payment/audit/order records. Minimum user expectation is 4 months; **12-month retention is the proposed operating baseline**, subject to data-protection requirements and explicit product policy; actual secure retention/recovery requires tested encrypted off-provider backups, restore drills, access control, capacity budgeting, and validated search UI. Never claim a 12-month guarantee on Neon Free without recovery evidence.

**Roadmap priority:** CI and code review PR #34 then #36 → protected recoverable Neon UAT backup → additive UAT migrations 0026 and 0027 in order → isolated Vercel UAT deployment → dummy receipt create/reject/re-upload → owner/admin search by email/date → download old/new versions with hashes and event timeline → simulated four-month-old record test and restart/redeploy durability. Do not touch Render/Production or Meta sends and do not bypass Production write freeze/backup/parity/rollback/GO.

**Mandatory cross-chat read order:** `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. Reuse this requirement and current PR/migration status rather than asking the owner to restate it.

---


## 2026-10-14 — PERMANENT OWNER DECISION / CROSS-CHAT HANDOFF: PostgreSQL media, not R2

**READ FIRST in EVERY DirectPilot chat before recommending storage or continuing migration. The owner has repeatedly confirmed this; do NOT ask them to explain or approve this architecture again.**

1. **SINGLE APPROVED FILE STORAGE DESIGN:** store customer payment receipts AND product images durably in PostgreSQL (separate Neon databases for UAT and Production), with `BYTEA`/SQLAlchemy `LargeBinary` and database metadata. Payment receipts ALREADY use `manual_payments.receipt_data` (Alembic `0022_durable_receipt_blob`). The new *product-image* column `product_media_assets.image_data` is being implemented in isolated UAT feature PR **#34**, Alembic additive migration `0026_durable_product_media` (parent `0025_trial_three_days`). **This product-image code/migration is NOT deployed or applied to Neon UAT/Production until separately verified.**
2. **DO NOT PROPOSE CLOUD STORAGE:** Cloudflare R2, S3, object buckets, new billing accounts, API keys or third-party media hosts are NOT part of the owner's chosen design. Prior R2 PR **#33 CLOSED WITHOUT MERGE** as superseded. Reconsider a different storage provider ONLY if the owner explicitly reverses this decision, or measured capacity forces presenting a choice; do not silently switch implementation.
3. **MEDIA BEHAVIOR (PR #34 pending):** JPEG size capped at **2 MiB decoded** and **50 MiB active-image budget per store** to control Neon storage and fit serverless JSON/base64 request limits; DB bytes stored atomically with `ProductMediaAsset`, deferred ORM loading for normal lists, authenticated admin preview and HMAC/expiry-protected public GET, protected deletion clears blob; existing legacy local-file-only rows preserved for controlled inventory/backfill. No external storage credentials. Distinguish current deployed code (still legacy local image disk) from pending PR.
4. **COST / TECHNICAL CONSTRAINTS:** Neon Free storage/compute, growth from JPEG `BYTEA`, backups/restore, network and Vercel Function 4.5 MB request-body limit MUST be checked under real usage. 2 MiB cap is a safety assumption, not proof of production capacity. Vercel Hobby commercial-use restrictions and long-running Meta/webhook tasks remain separate architecture gates.
5. **VERIFIED UAT STATUS as of this checkpoint:** isolated Vercel FastAPI and Preview connected to independent Neon UAT, owner-reported PASS for customer login, session persistence, navigation, logout, unauthorized access prevention, admin login, reading existing payments/receipts; `/ready` owner-reported ready/database available/migration current at revision `0025_trial_three_days`, 82 tables. Two UAT receipts have non-null `receipt_data`; 0 legacy file-only receipts, 0 UAT product images at last read-only check. Fresh receipt upload and new product-media UAT end-to-end still OPEN.
6. **ENVIRONMENT SAFETY:** Production Render APIs and authoritative PostgreSQL remain untouched. Separate independent Neon Production `directpilot_live` final target exists EMPTY and is NOT yet freshly synced; old Production `neondb` is stale rehearsal. A controlled real Production cutover requires tested all-writer freeze and Meta/Payexa webhook durable replay, fresh consistent Render dump, protected encrypted independently restorable backup, table/business parity, rollback, and distinct owner GO. Render database Free expiry **2026-11-02** is a priority, NOT permission to skip safety.
7. **HOW TO CONTINUE WITHOUT RE-EXPLANATION:** read `AI_HANDOFF.md` → `PROJECT_ROADMAP.md` → `DECISIONS.md` → `CURRENT_STATE.md` → `NEXT_ACTIONS.md`, then inspect **actual** GitHub PR #34 CI/deployed commit, Neon revision and Vercel runtime. Never infer successful runtime from PR creation/build READY alone. Prefer making scoped changes yourself via available connected tools; protect secrets and real accounts.

**Next immediate task:** CI review for PR #34 → review UAT-only backup → additive Neon UAT migration 0026 (not yet applied) → deploy isolated UAT API → dummy image upload/preview/signed-link/delete/redeploy durability tests; Meta sends and Production remain unchanged.

---

**Exact next work without asking user to repeat architecture:** check PR #34 GitHub CI and fix any failures; maintain isolated UAT scope; secure restorable Neon UAT snapshot/backup, stage additive schema 0026, verify upload/read/download/delete on dummy JPEGs and validate API cold-start; measure Neon storage/compute; only then discuss broader UAT/Production host and preserved Render final-sync safety gates. Do NOT open R2 sign-up or ask for R2 credentials.


## 2026-10-14 — UAT Admin/Receipts acceptance and remaining Media/Commercial gates

- **USER-REPORTED MANUAL UAT PASS:** isolated Vercel frontend/backend with independent Neon UAT: customer login, session persistence, navigation, logout, unauthenticated access restriction, admin login, admin payment list and existing receipt viewing. This is NOT automated end-to-end evidence or Production acceptance.
- **DIRECT NEON UAT READ-ONLY CHECK:** 82 public tables; Alembic `0025_trial_three_days`; 2 manual payments, both with durable `receipt_data` stored in PostgreSQL; 0 legacy file-only receipts; 0 product media assets. New receipt upload/persistence across redeploys has NOT been tested.
- **P0 MEDIA BLOCKER:** `app/media_storage.py` saves product images to local filesystem; Vercel Functions only permit transient `/tmp`, unsuitable for long-term assets. Image upload allows 8 MiB JPEG inside base64 JSON, while Vercel Function payloads are limited to 4.5 MB. Need object storage and compatible upload architecture before enabling image publish on the new host.
- **P0 COMMERCIAL BLOCKER:** official Vercel Hobby policy is personal/non-commercial; technical UAT success does NOT qualify a paid SaaS Production workload for the free plan. Evaluate permissible paid Vercel hosting versus commercially suitable portable Docker host. Cloudflare R2 Standard free quota is a candidate, not provisioned or approved; account/billing setup, object-storage integration and usage ceilings are OPEN.
- Full checklist/runbook: `docs/runbooks/vercel_uat_media_storage_and_commercial_gate_20261014.md`. Keep Render Production/UAT APIs and authoritative Render Production PostgreSQL untouched; separate final source write-freeze, event replay, encrypted recoverable backup, fresh Neon final restore, parity, rollback and owner GO remain mandatory.

---


## 2026-10-14 — Isolated Vercel UAT auth and receipt durability acceptance

- Operator tested customer account against isolated frontend preview `dpl_CEnKE8Fh98HpnsPfsFwMz7yzhnzY` (READY), wired with branch-scoped `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app` to API `dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR` and independent Neon UAT.
- **USER-REPORTED PASS:** customer Login, session persistence after refresh, navigation, Logout and unauthenticated access rejection. These are manual browser acceptance results, not separately captured backend request logs or automated tests.
- **Neon UAT direct read-only SELECT PASS:** `manual_payments` count=2; receipt rows with both storage key and bytea `receipt_data`=2; file-only legacy receipts=0; `product_media_assets`=0. Backend `CommerceService.submit_receipt` stores receipt bytes in PostgreSQL and the admin receipt endpoint serves those bytes, while product-image media writes local files (`app/media_storage.py`) and is NOT serverless-durable.
- **OPEN:** UAT admin read-only/RBAC smoke; real UAT receipt upload/retrieval/restart test without payment approval; media persistent object-storage redesign; Meta webhooks, callback behavior, signed assets, cold-wake/capacity and explicit Vercel commercial suitability. All Production final source backup/freeze/replay/parity/GO gates remain unchanged. Preserve both Render services until accepted replacement.

---


## 2026-10-14 — Vercel UAT API migration checkpoint (runtime acceptance OPEN)

- Scope: isolated UAT experiment only, NOT a Production cutover or a change to the full-Render-exit objective. The earlier Docker-host recommendation remains an alternative; a Vercel Functions backend is under evaluation, NOT yet accepted as a durable commercial Production architecture.
- Source: backend `namach2727-coder/Sales-Agent`, branch `migration/vercel-uat-fastapi-20261014`, commit `c05a5a76def84b9495bf1b361f910a9194d58a59`; an `api/index.py` ASGI entrypoint imports `app.main:app`. This change is isolated and not merged to `backend-main`.
- Vercel project `directpilot-uat-api`, ID `prj_Kt665OcJisA7WMTA2YnGi7KSyT3b`, is independent from the existing `directpilot-web` frontend. Redeploy `dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR` reports READY (build/deployment only), not runtime or DB readiness. Project's Vercel target is labeled `production` but contains UAT configuration; this is NOT DirectPilot live Production.
- Names-only Vercel environment inventory independently checked: `DATABASE_URL` (sensitive), `APP_ENV=uat`, `DEBUG=false`, `APPLICATION_SECRET` (sensitive), `INSTAGRAM_TOKEN_ENCRYPTION_KEY` (sensitive), `TRUSTED_HOSTS`, `FORCE_HTTPS=true`, `LEGACY_ADMIN_ADAPTER_ENABLED=false`, `CORS_ALLOWED_ORIGINS`. UAT secret *values*, URL correctness, Render↔Vercel parity and successful app decryption have NOT been independently verified. No secret values are recorded in these documents.
- On prior redeploy `dpl_5xAzCx6otghdXgXET5JnXyQJvthA`, browser requests to `/live` and `/ready` returned `500 FUNCTION_INVOCATION_FAILED` with request IDs `fra1::bv4nk-1791966084654-c376ac9837af` and `fra1::gznj8-1791966090412-cebb7c848b9b`. This is confirmed failure for that earlier deployment; the latest redeploy's endpoint outcomes are NOT verified. Vercel Runtime Logs and error clusters returned 403; root cause remains UNCONFIRMED. Missing required UAT env settings on prior deployment were a plausible cause, not a demonstrated stack trace.
- Important code compatibility risks requiring explicit UAT tests: Vercel Function lifecycle versus Docker entrypoint's check/migrate/startup behavior; database pool connections and Neon cold wake; receipt/media files under local filesystem (ephemeral functions); signed public media; auth cookies, CORS, trusted hosts, Meta OAuth/webhooks, payment callbacks, encryption key continuity. No real outbound Meta sends or payment approvals during infrastructure smoke. Ensure no double writers / split brain.
- Current status: `BUILD READY`; `/live` UNKNOWN on latest deployment; `/ready` UNKNOWN; auth/payment/media/Meta E2E BLOCKED; Production unchanged; both Render APIs remain live; Render Production DB is still authoritative. Do not claim UAT PASS or retire Render. Immediate next: capture sanitized latest runtime HTTP response/logs through authorized dashboard/CLI, verify configuration, safely test `/live`, `/ready` and UAT-only auth/payment without external side effects; select persistent storage and commercial-suitable compute, then update acceptance gate.

---

**Prioritized execution:** (1) latest UAT deployment log/HTTP triage; (2) safe app boot and Neon readiness; (3) separate UAT login/session/receipt-storage/Meta webhook dry-run and rollback checks; (4) only then decide Vercel Functions suitability versus Docker host; (5) continue independently the Render Production final-freeze/backup/restore blockers. No live Production cutover.


## 2026-10-14 — Final sync tooling merged; actual data transfer remains BLOCKED

- Backend PR #30 **MERGED** commit `3f07b16bd7ade6f065f3638417e5adc838f6f810`, latest CI run `38530717010` **4/4 PASS**, Python **941 passed / 7 skipped**. New operator-only `tools/production_final_sync.py`, `docs/runbooks/final_render_to_neon_sync_20261014.md` now in `backend-main`.
- Neon Production `directpilot_live` independently rechecked **0 tables / 0 sequences**; old restored `neondb` remains 82 tables/Alembic 0025; UAT untouched. Render authoritative source available, PostgreSQL inbound allowlist empty, Production API live, no maintenance. **NO fresh Render dump, restore, Production DB cutover or traffic interruption** occurred.
- Real final source sync **BLOCKED** until local operator Codex can access Render with scoped temporary /32 AND all writer/Meta+Payexa callback freeze/replay/independent encrypted recoverable backup are verified. Do NOT claim PR merge or empty DB means data parity or migrated subscriptions/orders. No dropping/cleaning existing databases.

---


## 2026-10-14 NEXT ACTIONS: complete actual final synchronization, do not claim done early

**Completed:** non-destructive independent Neon Production `directpilot_live` created, verified EMPTY; old production rehearsal `neondb` and UAT preserved. New guarded operator CLI and `docs/runbooks/final_render_to_neon_sync_20261014.md` prepared (review/CI pending).

1. **CRITICAL first:** implement and prove durable Meta **both** webhook path + Payexa callback store/replay, stop all signup/session/order/receipt/admin and worker writers, and account for in-flight activity without false 2xx acknowledgments or split-brain.
2. **On authorized private Windows workstation:** with trusted /32 Render allowlist temporarily reopened only for backup and private source URL, use `tools/production_final_sync.py` to take fresh consistent pg_dump **AFTER** verified freeze. User must re-authorize actual outage/maintenance window separately. Hosted Render MCP is blocked by currently empty allowlist.
3. **Protect recoverability:** encrypted off-provider verified backup AND successful test restoration into disposable target, verify SHA256, no customer data or credentials in chat/GitHub.
4. **Guarded restore:** only into newly created currently-empty independent Neon `directpilot_live`; NEVER into old `neondb` or UAT. Dump must be fresh (<2h) with manifest; single transaction no-clean/no-overwrite.
5. **Independent reconciliation:** source vs restored target ALL tables, counts, critical content fingerprints, subscriptions/orders/manual receipts, Meta/Payexa event IDs and token encryption continuity; rollback rehearsal. Fix any mismatches BEFORE opening writes.
6. **Later explicit GO:** relocate Production FastAPI off Render, update secure env/Meta/DNS/callback URLs and switch live production to final fresh Neon DB; then retire Render services only after acceptance. Render expiry 2026-11-02 is not permission to lose data.

---


## 2026-10-14 FULL RENDER EXIT — executive work queue

1. **Immediately choose a non-Render Docker host for 2 Backend environments:** OCI Always Free VM if account/payment verification and regional capacity work, or owner-approved paid Railway/VPS. This decision is essential; hosted tools cannot provision an unconnected provider account automatically.
2. **After provider selection, provision a SECRET-FREE isolated stage first.** Review `docs/runbooks/full_render_exit_20261014.md` and `deploy/full-exit/compose.yaml`. Build the immutable Python Docker image, configure HTTPS, separate Production/UAT hostnames, and verify UAT-only DB startup against independent Neon UAT; META_SEND off. Do not use existing local Postgres/Ollama Compose.
3. **Securely migrate Render Web Service ENV values to the new Backend host**, not into Neon PG. Current Render connector does not expose secret values. Operator must transfer privately, preserving crypto keys, sessions, bank/payment settings and public Meta OAuth relay state, and fix Render-host callback URLs only after verified destination. No secret value in GitHub/chat.
4. **Implement/test durable event freeze for Meta webhook routes and Payexa callbacks**, no duplicated messages/payments; maintain signed media and receipt volumes, tenant session continuity and out-of-provider encrypted DR backup.
5. **Finalize database migration:** freeze all writes, export FRESH Render PG16 snapshot, restore verified new EMPTY `directpilot_live` in independent Neon Production, compare all tables, records and finance/watermarks, prove rollback.
6. **Separate owner Go/No-Go:** production app hostname/DNS and Meta/Payexa callback update, switch Production API to fresh Neon DB, observe login/orders/receipts, confirm Neon capacity then retire both Render APIs and Render PG AFTER acceptance and retention. Do NOT delete now.

Render PG expires November 2; internal readiness target October 25. Current status preparation only, no new provider account or deployment.

---


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
