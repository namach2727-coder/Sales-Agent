# DirectPilot AI Handoff

## 2026-10-14 — FINAL TECHNICAL UAT CHECKPOINT: domain/API/Neon PASS, browser signoff PENDING

**Canonical UAT ONLY:** `https://uat.directpilot.ir` (Frontend Vercel Preview, GitHub `directpilot-web` branch `UAT`), deployment `dpl_8J7NSmuGuBf8U8mxzX7JQXoVKEdj` READY at SHA `08828ee1358ead2e9d81d2985fe2e4b07020e355`. **Production `directpilot.ir` remains `main` on separate deployment**. UAT branch-only Preview env has `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app` and `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir`; values verified, Production vars unchanged.

**PASS:** Frontend PR #31 full CI 216 tests + TS + lint + Next.js build. `Official UAT Domain Smoke` run `38565672177` PASS, anonymously checks /auth/me 401 JSON, upgraded receipt history endpoint 401 JSON, Backend /ready=200 database=available migration=current. Neon independent UAT PostgreSQL project `round-shape-42044596`, database `neondb`, Alembic `0027_traceable_receipt_versions`. **Data: 2 current receipt blobs, 2 historical version-1 copies (2/2 parity), 0 orphaned/mismatched links, 0 duplicate versions, 0 invalid evidence, 0 missing backfills; 8 receipt history indexes.** Product image BYTEA column exists; 0 stored images. Pre-migration Neon snapshot `snap-patient-dawn-arkxewpc` was restore-tested on a separate branch. No independent offsite backup SLA proven.

**IMPORTANT BROWSER GATE:** Unauthenticated external `GET /login` and `/robots.txt` on `uat.directpilot.ir` returned HTTP 302 → `vercel.com/sso-api`: Vercel Deployment Protection/SSO covers UAT HTML. This is not a failed rewrite, and the public API auth paths remain protected. **Do not disable Vercel SSO or bypass security without explicit owner permission**. Authorized browser with legitimate Vercel sign-in must verify Login responsiveness, customer/Admin login & session/logout, customer/date payment archive, receipt version review and actions, role restrictions, dummy image upload/preview/delete/redeploy. No real transfer approval or Meta sends. Status remains **TECHNICALLY READY FOR AUTHORIZED UAT BROWSER TESTING**, **NOT BUSINESS ACCEPTED**.

**Single operational runbook with complete evidence, ownership, test checklist and hard Production gate:** `docs/runbooks/official_uat_acceptance_gate_20261014.md`. Read it before next action. Retain owner requirements: canonical UAT domain; PostgreSQL BYTEA for all product images and versions of manual payment receipts, searchable after 4+ months; no R2/S3. Source rollback frontend `backup/uat-before-vercel-neon-sync-20261014` and Neon UAT snapshot retained. Production Render/Neon cutover is UNAUTHORIZED until independent backup, writer/webhook freeze, final sync/parity, rollback, commercial hosting terms and owner GO. Cross-chat file order remains `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`.

---


## 2026-10-14 — OFFICIAL UAT ROUTING SMOKE PASS; Vercel SSO HTML GATE OPEN

**Read this checkpoint before UAT testing.** GitHub Actions `Official UAT Domain Smoke` run **38565672177 PASS** against `https://uat.directpilot.ir` (commit `08828ee1358ead2e9d81d2985fe2e4b07020e355`). It independently verified: same-origin `GET /api/v1/auth/me` without credentials returns **401 JSON**; upgraded versioned receipt endpoint `GET /api/v1/admin/payments/smoke-invalid/receipts` returns **401 JSON** (so the official domain routes to the new Backend, not the old Render API); and `https://directpilot-uat-api.vercel.app/ready` returns **200 with database=available, migration=current**.

**Verified separate diagnostic** GitHub Actions run **38565116215 PASS** (job 115855706729) showed public DNS resolved, `/api/v1/auth/me` 401 JSON, new archive endpoint 401 JSON, Backend /ready 200, but GET `/login` and `/robots.txt` on canonical UAT were **HTTP 302 redirect to `https://vercel.com/sso-api`**. **Vercel Authentication protects UAT HTML pages** for non-Vercel-authenticated external clients; it is not a DNS, Next.js rewrite, Backend API or Neon migration error. Original naive HTTP smoke failed because its redirect-following client interpreted the Vercel SSO page as an API response, not because Backend returned anonymous 200. The current smoke intentionally validates expected SSO protection and tests API routes independently. It prints `page access=vercel-sso-protected`, so **UAT browser UI is NOT independently verified** and public robots/noindex cannot be asserted without a reviewer session.

**Security rule:** DO NOT disable Vercel SSO / Deployment Protection globally, open a public alias bypass, share credentials, or loosen customer/receipt access just to make unauthenticated bots return 200. Owner approval is required before changing access policy. Authorized reviewer should open `https://uat.directpilot.ir/login` while authenticated to Vercel and test customer/admin login, session persistence, Logout, receipt history by email/date/versions and product image storage. If Vercel redirects to SSO, complete legitimate Vercel login. No real payment approval or Meta send in smoke. If owner explicitly requests unauthenticated public UAT, evaluate **alias-only** access change and its risk, never Production protections.

**Current source:** Frontend repo `namach2727-coder/directpilot-web` branch `UAT` (PR #31 merged with entire CI pass), custom branch-specific Vercel Preview env `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app`, `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir`; official custom domain alias follows Branch UAT. Backend Vercel `directpilot-uat-api`, GitHub migration branch; independent Neon UAT `neondb` head `0027_traceable_receipt_versions`. Old `UAT` source rollback branch `backup/uat-before-vercel-neon-sync-20261014`. No R2/S3: receipts and product JPEGs live in PostgreSQL BYTEA; ensure receipt versions are traceable four+ months and backups independently recoverable.

**Production still blocked:** Actual Production `directpilot.ir` / `main` and Render authoritative DB, real Meta/Payexa callbacks and domains were NOT changed. Independent final backup/restore, writers/webhook freeze and replay, fresh Production migration/parity, commercial host suitability, rollback and explicit GO remain pending. These five canonical files must be read/reconciled at the start of every DirectPilot chat without reasking owner.

---


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

**Cross-chat trigger:** whenever the owner says “continue DirectPilot” or “keep the five files/roadmap updated,” this permanent decision and the five-file read order are binding; do not propose R2 and do not conflate Docker fallback, Render Production, Neon UAT or PR-only work.


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


## 2026-10-14 — Vercel API UAT checkpoint (not accepted)

- Isolated Vercel project `directpilot-uat-api` (`prj_Kt665OcJisA7WMTA2YnGi7KSyT3b`) deployed from migration branch `migration/vercel-uat-fastapi-20261014`, commit `c05a5a76def84b9495bf1b361f910a9194d58a59`, via `api/index.py` ASGI shim. Latest redeploy `dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR` reports READY, but runtime `/live` and `/ready` remain unverified. Earlier redeploy returned 500 FUNCTION_INVOCATION_FAILED; Runtime Logs access returned 403, so root cause is unknown.
- Vercel UAT environment keys registered: DATABASE_URL, APPLICATION_SECRET, INSTAGRAM_TOKEN_ENCRYPTION_KEY (sensitive), APP_ENV=uat, DEBUG=false, TRUSTED_HOSTS, FORCE_HTTPS=true, LEGACY_ADMIN_ADAPTER_ENABLED=false, CORS_ALLOWED_ORIGINS. Values and end-to-end compatibility not verified.
- Render Production remains authoritative; no Production cutover, data restore, Meta/payment change or Render shutdown. Evaluate Vercel serverless runtime, persistent private receipts/media, encryption, auth, webhook callbacks and paid-use terms before approval. Existing Production final fresh Render sync and freeze/replay/backup/rollback gates remain mandatory.

---

## 2026-10-14 — Final sync tooling merged; actual data transfer remains BLOCKED

- Backend PR #30 **MERGED** commit `3f07b16bd7ade6f065f3638417e5adc838f6f810`, latest CI run `38530717010` **4/4 PASS**, Python **941 passed / 7 skipped**. New operator-only `tools/production_final_sync.py`, `docs/runbooks/final_render_to_neon_sync_20261014.md` now in `backend-main`.
- Neon Production `directpilot_live` independently rechecked **0 tables / 0 sequences**; old restored `neondb` remains 82 tables/Alembic 0025; UAT untouched. Render authoritative source available, PostgreSQL inbound allowlist empty, Production API live, no maintenance. **NO fresh Render dump, restore, Production DB cutover or traffic interruption** occurred.
- Real final source sync **BLOCKED** until local operator Codex can access Render with scoped temporary /32 AND all writer/Meta+Payexa callback freeze/replay/independent encrypted recoverable backup are verified. Do NOT claim PR merge or empty DB means data parity or migrated subscriptions/orders. No dropping/cleaning existing databases.

---


## LATEST 2026-10-14 — FINAL SOURCE→NEON SYNC REQUEST / TARGET CREATED / RESTORE BLOCKED

- Owner authorized starting final synchronization. **Non-destructive Neon action COMPLETED:** Created new empty database `directpilot_live` inside independent Neon Production project `billowing-poetry-05589994`, branch `br-winter-water-argmnyru`, owner `neondb_owner`; direct query verified **0 public base tables / 0 sequences**. Existing `neondb` Production rehearsal (82 tables, stale Oct 13 snapshot) and independent Neon UAT untouched.
- **LIVE Render source is still authoritative and writable**: `directpilot-production-db` available, external allowlist empty; hosted Render query rejected because connector has no allowlistable IP. Hosted assistant has NO access to local Codex Windows dump/source secrets or executable remote Render shell. **NO fresh dump, final restore, source data movement, maintenance window, or live cutover performed.**
- New strictly scoped operator-only helper `tools/production_final_sync.py` and runbook `docs/runbooks/final_render_to_neon_sync_20261014.md` prepared on PR under review. Requires actual all-writer/Meta/Payexa durable freeze, independent encrypted offsite restore-tested backup, fresh ≤2h Render dump, hash/manifest verification, exact new Neon host+DB and single-transaction no-clean restore **ONLY if target empty**; no automatic production DATABASE_URL switch. This is NOT executable through hosted tools.
- **P0 BLOCK:** No tested durable full source-write/webhook/payment freeze/replay. Do not perform an alleged "final sync" with active source writers or abandon late orders. Local Codex/operator action, approved maintenance, /32 Render source access and complete parity+rollback required. Keep both Render APIs LIVE and preserve full-Render-exit objective.

---


## NEW OWNER SCOPE — 2026-10-14: FULL EXIT FROM RENDER, NOT DATABASE-ONLY

- **Owner explicitly wants NOTHING on Render** after the expiry window. Do not interpret prior DB-only migration policy as the final architecture. Render inventory: two Free web services `directpilot-api` and `directpilot-uat-api`, plus one Free Production PostgreSQL DB expiring 2026-11-02. No Render KV resources.
- Target: Production & UAT Dockerized FastAPI on independent non-Render provider (HOST **NOT YET SELECTED**), each with restricted Meta webhook gateway, private secrets, TLS, persistent media/legacy receipt storage; existing independent Neon Production/UAT projects for databases, Vercel frontend stays outside Render subject to Hobby commercial-plan policy review.
- Prepared portable templates: `deploy/full-exit/compose.yaml`, `deploy/full-exit/Caddyfile`, `scripts/deployment/portable-entrypoint.sh`, `tools/full_render_exit_guard.py` and offline tests. Guard rejects Render source, old Production rehearsal Neon `neondb`, cross-environment DB hosts, unsafe startup one-shot writers, disabled TLS. No runtime provisioning/deployment or DNS/Meta variable transfer performed.
- Deployment choice: Oracle Always Free VM (if account/card/region/compute available) versus approved modest-cost Docker host (Railway/VPS); Northflank Free Sandbox explicitly not for Production. Until operator picks host and obtains account access, no real provisioning possible.
- **Hard gates:** secrets need PRIVATE export from Render into the NEW BACKEND host (not Neon Postgres). Rewrite stale onrender.com callback/OAuth/media host values only with verified new public hostname and partner registration. UAT first, then secure Production final write-freeze/fresh source snapshot/Neon final DB/Meta-payment replay, and separately approved live cutover; retain Render until tested acceptance. Do not stop services now.

---


## LATEST — 2026-10-14 Render→Neon environment variable transfer request

- **Architecture VERIFIED:** `directpilot-api` still runs FastAPI on Render. Neon project `billowing-poetry-05589994` has PostgreSQL `neondb` and no available platform Functions. **Neon is NOT a destination for all Render API env vars**; copying Meta, signing, token encryption and payment secrets into Neon database/project settings is neither supported nor needed for the DB-only migration.
- Connected Render `get_service` supplies an `environmentId`, but no environment keys/values or secure export/list action. **No Render secret values were read, copied, modified, or exposed.** Retain all existing Render variables; at a separately approved cutover, change ONLY the controlled `DATABASE_URL`/`DATABASE_URL_FILE` to the new fresh Neon final DB, NOT old `neondb`.
- PR #28 (pending CI/merge when this branch prepared) introduces offline names-only guard `tools/render_env_key_audit.py`, tests, and `docs/runbooks/render_neon_environment_preservation.md`. It blocks missing key names, rejects `KEY=value` inputs and cannot claim secret VALUE parity.
- No Production/UAT environment, database, Meta, API service, or customer data changes were made. Final fresh snapshot, webhook freeze/replay, DR and owner go/no-go still apply.

---


## LATEST — 2026-10-14 Neon Free metering / cutover write-freeze discovery

- **Capacity inspection:** Neon independent Production project `billowing-poetry-05589994`, Free 100 CU-hour/month. Read-only project API `compute_time_seconds=1746`, `active_time_seconds=6888`; inferred 0.485 CU-hour (0.485% of quota) **only if compute seconds represent CU-weighted seconds**, not console-billed/representative Production use. 0.25–2 CU autoscaling, Free idle suspension. Endpoint observed `idle`; read-only SELECT woke to `active` (~6.65s total hosted connector request, not customer SLA). HTTP demand metrics for source Render returned empty series, so cannot extrapolate customer load. At 0.25 CU always-on, 30 days could use ~180 CU-hour; Free is not proven viable for Production.
- **P0 cutover blocker discovered in live Backend code:** Two Instagram POST webhook endpoints, GET/POST Payexa callback, commerce/admin signup/order/receipt/payment writers; Docker entrypoint runs Alembic on every startup. No proven complete write-freeze with durable external webhook/callback queue/replay is implemented or verified. Do not treat frontend maintenance banner, Meta sending disabled, or normal 503 retry as proof of zero event loss.
- **New operations plan:** `docs/runbooks/neon_free_usage_and_maintenance_plan.md` (owner date/time and separate Cutover authorization PENDING). Proposed 120-minute controlled pause with T+90 go/no-go only after tested freeze/replay, protected independently restorable backup, console usage evidence and final target restore compatibility. **No window scheduled; no database/app/Neon/Meta changes executed.**
- Database remains Render Production available with zero external inbound rules; restored Neon `neondb` 82 tables/Alembic 0025 is stale snapshot. Actual restored Neon SQLAlchemy READ ONLY test PASS per operator. Secure off-provider backup, quota under real traffic, fresh final snapshot/delta, split-brain rollback and owner approval remain OPEN. Render Free source expires 2026-11-02.

---


## LATEST VERIFIED MIGRATION CHECKPOINT — 2026-10-14 / ACTUAL NEON SQLALCHEMY READ-ONLY PASS

- **Owner/Codex operator report:** `DIRECTPILOT_NEON_READONLY_PREFLIGHT` **PASS** on actual restored Neon Production `billowing-poetry-05589994` / direct host `ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech` / `neondb`: SQLAlchemy 2.0.41, psycopg 3.2.9, Alembic 1.16.5; TLS, PostgreSQL 18, DB target identity and **server-enforced READ ONLY**. The owner retained dirty local work safely and used clean `backend-main` snapshot SHA `860aae65b843de2e4361c7158f35ea0fc563f005`. No API, Meta, payment or worker side effects.
- **Independent Neon SQL cross-check by hosted connector:** 82 tables, 76 sequences, 522 indexes, 427 source-compatible constraints; zero invalid indexes or unvalidated constraints; migration `0025_trial_three_days`; subscription count=14, subscription orders=15, manual payments=1, invalid commerce relations and subscription periods=0; `TRIAL`, `AUTOMATION_TRIAL`, `AI_ASSISTANT_TRIAL` each 3 days. Actual SQLAlchemy/TLS read-only enforcement was verified on operator workstation, NOT re-executed by hosted agent.
- **Neon usage changed:** project `describe_project` now reports `compute_time_seconds=1746`, `active_time_seconds=6888` (previously both zero). Do not interpret raw counters as billed CU-hour consumption; Neon Free burn, autosuspend, cold start and production load suitability are **UNVERIFIED**.
- **Render security:** Render Production database still AVAILABLE, `ipAllowList=[]`, expiry `2026-11-02T11:59:46.610475Z`. **NO cutover.**
- **Next P0 gates:** owner-controlled independent encrypted/offsite recoverable backup (plaintext exception was only for rehearsal); actual Neon Free quota measurement; separate cutover maintenance-window approval and write/webhook/payment freeze, fresh authoritative `pg_dump` to a **separately approved new EMPTY final Neon database**, verified parity and rollback/split-brain plan. Follow `docs/runbooks/production_neon_cutover.md`, not historical stale TODOs.

---


## NEWEST HANDOFF — 2026-10-14 (supersedes prior dated pre-cutover checkpoints)

- **P0 Render PostgreSQL Free expires 2026-11-02T11:59:46Z.** Render Production DB AVAILABLE, external inbound `ipAllowList=[]` independently verified; Production/UAT Backend still LIVE on `bfe67fd`, autoDeploy OFF; **NO Neon live cutover**.
- Restored independent Neon Production `billowing-poetry-05589994/neondb`: PostgreSQL 18.6, 82 tables, Alembic `0025_trial_three_days`, no invalid indexes, snapshot from Oct 13. The old restore is **NOT continuously synced** to Render.
- **New operational runbook:** `docs/runbooks/production_neon_cutover.md`, merged backend PR #26 at `9ba207da2c5b18bf77003fd7e9b409ac69533f08`; CI `38514922043` 4/4 PASS. Proposed extra empty `directpilot_live` target is NOT created; separate approval required. No runtime deploy.
- Neon list_snapshots empty, automatic snapshot schedule empty. One restored manual payment has 40,139-byte inline PostgreSQL receipt data; auth/Meta token encryption compatibility remains untested in isolated app. Plaintext backup/out-of-provider protected recovery remains open.
- **NEXT:** workstation run `python -m tools.neon_readonly_preflight` using privately entered direct Neon URL; measure actual Free CU consumption/cold-wake; protect independent restorable backup; agree write/webhook freeze/final fresh dump and end-to-end rollback plan. Explicit go/no-go before any real Production DATABASE_URL change.

---


## LATEST VERIFIED CONTINUITY — 2026-10-13 (read before historical checkpoints)

**Priority P0:** Render Production PostgreSQL Free expiry **2026-11-02T11:59:46Z**; aim to complete a measured, reversible Neon cutover by **Oct 25**. **NO Production database cutover authorized or performed.** Older notes below describing 14-day trials, pending /solutions, no Render backup, Neon target empty, or backend repository SHA as a deployed service are historical/superseded where contradicted by this checkpoint.

- **Actual runtime:** Render Production `directpilot-api` deployment `dep-db6tq6vf3r2c73ch03bg` LIVE, UAT `dep-db6tpcff3r2c73cgtb30` LIVE, both backend code `bfe67fd79fb738027444fdead68b940d19b71f82`, both `autoDeploy=no`. Do not confuse newer docs/CI commits on `backend-main` with live Backend deployment.
- **Frontend:** Production `directpilot.ir` Vercel READY commit `79b8fad33b72e350b644162f69439d8c3e777471` / `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP`; cross-industry `/solutions` is LIVE; UAT branch has its own READY release. Trial marketing shows **3 days**.
- **Neon restored Production copy:** Project `billowing-poetry-05589994`, branch `production`, DB `neondb`, PostgreSQL **18.6**, **82 tables / 76 sequences / 522 indexes / 427 original constraints**, plus 689 PG18 NOT NULL catalog constraints, `alembic_version=0025_trial_three_days`. Exact 82-table row-count equality with Render source reported PASS by owner/Codex; independent Neon SQL confirms schema/migration and zero invalid constraints/indexes, but cannot independently re-query all original source rows. Snapshot is from 2026-10-13 10:42:36 UTC; no continuous replication, so a final fresh backup/delta with write freeze is mandatory.
- **Verified compatibility:** backend PR #24 merged `dab43e76c07a94bd39f949efd90e3bd62b24b2f9` (disposable PostgreSQL 18 app startup/migration/auth/transaction testing); PR #25 merged `f5b6f98f23bf3a02f77a631ded7e2fa7faa2c94c` (guarded SQLAlchemy read-only preflight tool). CI run `38401718878`: 4/4 jobs PASS, 905 Python tests PASS, 7 skipped. **Real restored-Neon SQLAlchemy preflight on laptop is NOT YET RUN:** `python -m tools.neon_readonly_preflight`, private direct DB URL entered locally, never in chat.
- **Read-only Neon business checks:** three trial plan codes have `duration_days=3`; no invalid subscription periods, orphan tenant subscriptions, orphan order plan refs or orphan manual payment order refs. Do not send real Meta messages, approve payments, start schedulers or use live API against this copy.
- **Compute and durability:** Neon Free 100 CU-hour/month, 1 GiB storage, 0.25–2 CU, provider-default idle suspend, pooler currently disabled. Render app `/live` health-check does not query DB; `/ready` does. Neon API's 0 consumed compute seconds is NOT a reliable capacity measurement. Test actual sleeping/cold-start, connections and quota before cutover. Existing 557942-byte PostgreSQL dump and matching SHA256 manifest were operator-verified; encryption deferred *for rehearsal only*, no accepted independent encrypted offsite recovery copy.
- **Render network ACL CLOSED — independently verified 2026-10-14:** Render Production PostgreSQL `ipAllowList=[]` (zero inbound IP rules). Previous 2026-10-13 discrepancy resolved; do not reopen access unless a time-limited, explicitly authorized backup/source audit requires it.
- **NEXT decision:** close DR/offsite recovery, real read-only app preflight, compute usage, final snapshot/delta and row reconciliation, webhook/write freeze, tested rollback/split-brain plan; then request separate explicit live cutover approval. NEVER repoint Production or UAT as a consequence of a CI/docs commit.

---


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


### 2026-10-12 UAT compact payment UI
- UAT interface PR #18 merged to UAT commit `1cae8c088542ff7ce6612c76705e3c670d223f74` on 2026-10-12. Changes: compact admin payment facts, receipt images rendered at intrinsic dimensions (PDF bounded viewer), current active subscription product names, and paid-customer CTA explicitly `ارتقا پلن`. Vercel merged-commit deploy/manual visual acceptance pending. No backend/Meta/Production deployment.


### Production promotion preflight (2026-10-12)
- 2026-10-12 Production promotion request: owner accepted all UAT tests and requests UI, database schema/catalog, and backend production rollout. NOT deployed. Production backend Render `directpilot-api` autoDeploy=no and latest verified live commit `421d157f`; UAT/backend-main is 41 commits ahead. Frontend `UAT` and `main` diverged (83 ahead, 20 behind), production promotion draft PR #19 has merge conflicts. Production `main` includes GA4 and security CSP customizations: preserve these. UAT Neon is separate and MUST NOT be copied wholesale to Production; existing customer data, receipts, payments, sessions, Instagram connections, and payment-card data stay in their respective environments. Production DB backup and compatibility must be verified before migrations; read-only production DB visibility has not been established.


## 2026-10-12 — Production commerce promotion (newest verified checkpoint)
- UAT business/visual acceptance: owner PASS for multi-month purchase, no-download inline receipt, compact admin review, customer active-plan + «ارتقا پلن» UI.
- Production backend: `directpilot-api` manual Render deploy `dep-db6fr2bl550s73esrnh0` LIVE, SHA `043d37ff6d514a46eef33770cf86f4892f7f00e8`. Environment=production, PostgreSQL connectivity PASS, Alembic current-head PASS, application startup PASS. Compared to previous live `421d157f`, no Alembic revision files changed (no new schema migrations).
- Production frontend: selective GA4/SEO-safe promotion PR #20 MERGED to main SHA `06ebe316e5193f111ebd4b0733ee85c406d0a56e`; candidate CI workflow #38271830924 PASS: 210/210 Node tests + type-check/lint/build. Production Vercel deployment/alias still UNVERIFIED: Vercel connector project not linked (linkedProjects=[]), list/get returned 403/404; GitHub merged-commit Vercel status absent. Do not claim Production frontend READY until separate Vercel inspection.
- Conflicting wholesale UAT PR #19 CLOSED as superseded; main-only Production GA4 sign_up/demo_start, CSP, SEO and 14-day trial copy deliberately preserved.
- Production catalog/data: NO UAT database copy, no plan-row mutation. Paid `AI_ASSISTANT_V1` exists in isolated UAT Neon but has NOT been proven inserted/active in Production PostgreSQL. Production Free DB has no verified backup/restore and external SQL is blocked. Need authorized read-only catalog/backup route, then explicit idempotent paid AI plan setup.
- Existing Production card-transfer acceptance, bank card and Meta relay preserved; shared Meta app untouched, no UAT customer/token/payment data migrated. Prod Free PostgreSQL expiry recorded as 2026-11-02. 


## Latest Production promotion evidence — 2026-10-12 (authoritative over earlier pending checkpoints)
- Owner approved the UAT payment, multi-month, active-plan upgrade label and fitted receipt UI and requested Production promotion.
- Backend Production Render `directpilot-api` deployment `dep-db6fr2bl550s73esrnh0` is LIVE on backend-main `043d37ff6d514a46eef33770cf86f4892f7f00e8`. Logs verify APP_ENV=production, Postgres connectivity PASS, Alembic current head, startup PASS; active/default manual payment cards each 1. Shared Meta app, routing and environment variables untouched.
- Frontend selective, non-conflicting PR #20 merged into Production `main` as `06ebe316e5193f111ebd4b0733ee85c406d0a56e`. GitHub Actions validated 210 tests, type-check, lint and build PASS; GA4 signup/demo instrumentation, SEO and Production CSP retained. Conflicting UAT-direct PR #19 closed. **Vercel Production deployment of the merge SHA is NOT independently confirmed:** connector lacks the linked project/team authorization. GitHub merge is not proof of live deployment.
- Isolated Neon UAT contains `AUTOMATION_V1` (IRR 4,900,000/30d) and `AI_ASSISTANT_V1` (IRR 6,900,000/30d, 1,000 AI requests and 1,000 replies), both active and purchasable. Production paid-AI row not yet verified. Idempotent additive migration PR #15 is under CI; it preserves existing rows and UAT test data stays isolated. Do not claim PROD AI sale PASS until migration deployed and readback verified.
- Production database remains Render Free, with no accepted backup/restore and documented expiry 2026-11-02; owner previously deferred paid upgrade. No infra upgrade or bulk UAT DB copy is authorized.


## Final additive AI catalog rollout — 2026-10-12 (supersedes earlier pending)
- Backend PR #15 merged at `90aea1e925219056a9347f344fa020e6b7b6a744`; CI Python test, Docker and PostgreSQL smoke PASS. Added Alembic `0024_ai_assistant_v1_catalog` to insert approved paid AI row only when absent, preserving all pre-existing rows and historical snapshots.
- UAT Render deploy `dep-db6gbobbc2fs73c1r860` is LIVE matching that SHA, Alembic head PASS. Isolated Neon readback PASS: exactly one `AI_ASSISTANT_V1` and one `AUTOMATION_V1`, both unchanged, active and purchasable, original prices/limits intact.
- Production Render deploy `dep-db6gco59fdbs7382opb0` is LIVE matching the same SHA, Postgres connectivity, Alembic upgrade 0023->0024, current head and app startup PASS; `manual payment readiness active_cards=1 active_default_cards=1`.
- Independent read-only Production public `/api/v1/plans` test in GitHub Actions run `38275924090` PASS. It verifies Automation IRR 4,900,000/30d/20 rules and AI Assistant IRR 6,900,000/30d/1,000 replies and requests, both active in the purchasable public catalog. No customer/receipt/card/token data copied from UAT; shared Meta settings unchanged.
- Frontend PR #20 Production `main` merge remains `06ebe316e5193f111ebd4b0733ee85c406d0a56e` with 210 tests, type-check, lint, build PASS, but Vercel deployment SHA/readiness remains UNVERIFIED due connector project-access denial. Do not claim frontend runtime promotion PASS until separately confirmed.
- No paid DB upgrade or verified off-host backup. Render Free Postgres expiry 2026-11-02 durability risk remains owner-deferred.


### Mobile login overlay hotfix — 2026-10-12
- 2026-10-12 Mobile Production login hotfix: users reported that tapping «ورود» in mobile Production did not open the login screen. Frontend inspection found the full-screen mobile menu was not dismissed when a link was activated, potentially covering the navigated page. Applied delegated anchor click close + inert when closed + 100dvh/scroll and iOS safe-area. UAT PR #21 merged at 041b3ccdb4b188a46178153d62b44b239d557837; CI quality PASS after aligning outdated UAT commerce tests and restoring payment account-number visibility. Production PR #22 merged to `main` at 69632c8a6e0bb1ba66933d3f8b8167823fb6bcf9; Production promotion validation PASS (tests, type-check, lint, build). Vercel linked-project access unavailable: deployed Production SHA and actual mobile browser acceptance UNVERIFIED. Backend, PostgreSQL, Meta, GA4/SEO and payments unchanged in Production by this hotfix.


### Customer Dashboard UAT UX (2026-10-12)
- 2026-10-12 Customer dashboard UAT redesign: Frontend PR #23 merged into `UAT` at `00d29a8952c867be0c0b33c5619962b4c97478f3`. UAT Customer Journey Quality run `38281718727` PASS (unit tests, TypeScript, lint, Next build). New task-first customer overview: prioritized actionable next step, 3 authoritative service status tiles, entitled product shortcuts, mobile viewport/accessibility refinements and mobile section menu auto-close. The customer Inbox/online conversation display is removed from all customer navigable routes/sidebar/quick links, including `?section=inbox` fallback to overview. Existing inbox backend API, stored conversations, and public marketing demo were not deleted. Explicitly distinguish unknown subscription/Instagram read failures from disconnected/no subscription; disable paid-plan purchase if subscription fetch failed; retry essential reads rather than just optional reads. **Production frontend NOT changed in this UAT iteration** and browser-level UAT visual acceptance/deploy status not independently verified.


### Customer Inbox follow-up — 2026-10-12
- 2026-10-12 Correction to previous Inbox removal claim: UAT customer Inbox sidebar/route was hidden in PR #23, BUT the `InboxPanel` JSX and live conversation renderer remained compiled in `components/final-uat.tsx`. Explicit user report confirmed conversations still visible on UAT. Follow-up frontend PR #24 merged at `16e2547d0b5d2815209bcba931cf76b52afbc7dc`. It removes the full ~10k-character InboxPanel implementation and all inbox imports and presentation, tightens CustomerWorkspaceSection to business/ai/automation, and changes tests to require no customer conversation renderer. UAT CI `38285210154` PASS (tests, type-check, lint, Next build). Backend conversation data/APIs, Meta, Production unchanged. **Vercel UAT deployed commit/alias is UNVERIFIED:** connector authorization lacks project/deployment rights (403), and account sign-in alone does not prove code deployed. Do NOT mark real-browser fix complete until Vercel `uat.directpilot.ir` branch UAT READY commit `16e2547d` and user confirms no Inbox.


### Release handoff — 2026-10-13
- Verified Backend backend-main bfe67fd79fb738027444fdead68b940d19b71f82 LIVE on both Render UAT and Production. Migration 0025_trial_three_days changes TRIAL, AUTOMATION_TRIAL, AI_ASSISTANT_TRIAL plan catalog duration to 3 for future activations; existing subscription expiry/order snapshots preserved. Neon UAT query returned 3 for all three; Production direct SQL inaccessible via Render IP allowlist.
- Verified frontend Production 6f383fc3193f86888199d6faf06d8e93b83cb248 READY at directpilot.ir and UAT fb340b724eba13bf5c8225272bd69667c0659143 READY at uat.directpilot.ir. Production trial copy updated from 14 to 3 days; reviewed source showed no 24-day trial claims.
- UAT has industry-neutral /solutions landing with online shops, services, salons, education as examples. Promotion of this general landing to Production remains a separate controlled frontend change until READY.
- Previously noted Vercel connector 403 issue resolved: use project ID prj_w46jn80pmeOpoIZ5KZmQiY7GfKDl WITHOUT team slug.


### Production Solutions promotion verified — 2026-10-13
- Frontend PR #29 merged at commit `79b8fad33b72e350b644162f69439d8c3e777471`; Production CI PASS; Vercel deployment `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP` READY and aliases `directpilot.ir`, `www.directpilot.ir` active. General `/solutions` page and links promoted from UAT selectively, with shops/services/education/salons only as examples. Existing 3-day trial copy, SEO, GA4 and payment flows preserved. This supersedes earlier notes stating generic Solutions Production promotion pending.
