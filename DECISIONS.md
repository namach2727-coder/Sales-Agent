# DirectPilot Decisions

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

**Decision record (accepted by owner):** use PostgreSQL BYTEA for both new payment receipts and new product images. R2/S3 PR #33 is formally closed; no external Bucket, secrets, or payment subscriptions. Changed only by new explicit owner decision supported by measured cost/scale evidence. Keep a single linear Alembic chain and never auto-run UAT migration during live Production startup.


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

**Decision status:** Vercel has been chosen only as an isolated UAT trial, NOT as the approved end-state host. Preserve Docker provider-neutral plan pending serverless feasibility, commercial terms, object storage and operational acceptance. Production release is a distinct owner decision.


## 2026-10-14 — Final sync tooling merged; actual data transfer remains BLOCKED

- Backend PR #30 **MERGED** commit `3f07b16bd7ade6f065f3638417e5adc838f6f810`, latest CI run `38530717010` **4/4 PASS**, Python **941 passed / 7 skipped**. New operator-only `tools/production_final_sync.py`, `docs/runbooks/final_render_to_neon_sync_20261014.md` now in `backend-main`.
- Neon Production `directpilot_live` independently rechecked **0 tables / 0 sequences**; old restored `neondb` remains 82 tables/Alembic 0025; UAT untouched. Render authoritative source available, PostgreSQL inbound allowlist empty, Production API live, no maintenance. **NO fresh Render dump, restore, Production DB cutover or traffic interruption** occurred.
- Real final source sync **BLOCKED** until local operator Codex can access Render with scoped temporary /32 AND all writer/Meta+Payexa callback freeze/replay/independent encrypted recoverable backup are verified. Do NOT claim PR merge or empty DB means data parity or migrated subscriptions/orders. No dropping/cleaning existing databases.

---


## 2026-10-14 Controlled final synchronization decision

- Owner instruction to start final Render→Neon synchronization permits preparing a new non-destructive final DB. **`directpilot_live` CREATED EMPTY** in independent Neon Production; source Render remains authoritative; don't overwrite stale restored `neondb` or touch Neon UAT.
- Because hosted Render SQL is denied by the empty external allowlist, only a private workstation with scoped Render source access and existing secrets can export current data. Current connector cannot silently access it; do not reopen broad IP access.
- **Final dump and restore are BLOCKED** until ALL user/admin/Meta webhook/Payexa/worker writers are demonstrably frozen with durable callback replay, plus a verified independent encrypted recoverable source backup. No falsely reassuring "final sync completed" status.
- A successful freshly restored target does not approve API routing or Render decommission. Require exact 82-table or reviewed current source schema parity, critical content/financial validation, split-brain-safe rollback and distinct Production Go/No-Go.

---


## 2026-10-14 Architecture revision: Render-free DirectPilot

- Previous **DB-only Neon** plan is SUPERSEDED as the END STATE by owner's explicit direction: remove both Production and UAT Backend AND Render PostgreSQL. Neon remains database provider, not an app-secret store. Move API, restricted Meta gateway, private credentials, legacy media/receipts and custom domains to a new Docker-capable host outside Render.
- **No host/billing choice or live deployment has been authorized yet.** Prefer OCI Always Free VM IF VM allocation, account and payment verification are possible; alternatively discuss a modest paid Docker service. Don't claim any hosted app is deployed until verified by endpoint.
- Prepared provider-neutral `deploy/full-exit/compose.yaml`, Caddy, non-migrating fail-closed API entrypoint and exact-host target guard, all Git-only. Never start Production against old restored Neon `neondb`; Production final DB is still NOT CREATED. UAT has a separate Neon project and must remain isolated.
- Render secrets must be securely transferred to NEW BACKEND HOST, not Neon DB, without posting values; onrender.com Meta/OAuth/media/payment callback references require controlled update after new stable hostnames are validated. UAT-first staging, webhook hold/replay, fully protected backup, fresh sync/parity, rollback and explicit owner live-cutover plus Render deletion approval remain prerequisites.

---


## Render application secret preservation policy — 2026-10-14

- **DECISION:** migration is of Production PostgreSQL from Render to independent Neon; the running FastAPI backend remains on Render unless a separately approved architecture changes. Neon Production project currently has no Functions and is **not** a safe/general-purpose destination for app environment variables.
- Preserve all current Render Backend variables and their VALUES (including `APPLICATION_SECRET`, Instagram encryption, Meta OAuth/webhook, Payexa, session cookies and startup one-shot controls). Only an authorized, verified future **Render** `DATABASE_URL`/`DATABASE_URL_FILE` change should reference new final Neon DB after fresh synchronized restore and GO.
- No API env secret read or write capabilities are available via the current Render connector; do not dump secret values into chat, GitHub, SQL tables, screenshots or logs. Use private operator-controlled audit and names-only guard documented in `docs/runbooks/render_neon_environment_preservation.md`. No env copy or live Cutover occurred.

---


## NEON FREE / MAINTENANCE PRECONDITIONS — 2026-10-14

- Observed independent Neon Free API counters `compute_time_seconds=1746` and `active_time_seconds=6888`. Equivalent **~0.485 CU-hour only as a provisional estimate**, not a settled provider Console quota invoice nor measured customer traffic. Free 100 CU-hour/month; monitor actual burn and idle/cold starts before Production GO.
- **Maintenance cannot be authorized just from a finished Runbook.** A comprehensive, reversible write barrier and durable Meta webhook + Payexa callback preservation/replay must first be implemented, tested and explicitly approved. Existing code paths can write or trigger outbound sends; a static maintenance page or returning arbitrary errors is not sufficient.
- Adopt `docs/runbooks/neon_free_usage_and_maintenance_plan.md` as proposed go/no-go, staged freeze and recovery plan. T+90 checkpoint/120-minute maximum is a planning budget, **not a booked outage**. Owner must approve date, maintenance risk and a *separate* actual Production cutover. No live Render/Neon/UAT/Meta changes authorized.

---


## ACCEPTED PREFLIGHT EVIDENCE — 2026-10-14 (ACTIVE)

- Accept **operator-reported PASS** for the actual restored Neon Production SQLAlchemy/psycopg + TLS + PostgreSQL-server-enforced READ ONLY preflight using the guarded tool. Hosted Neon SQL independently matched the 82/76/522/427 database objects, Alembic 0025 and key commerce/trial aggregate integrity. This **closes only the read-only connectivity/integrity gate**; it does not constitute full live API or production auth/Meta/payment E2E acceptance.
- Keep Production on Render; maintain UAT separation. **Explicit new approval** required for controlled maintenance and any future final database creation, write freeze, restore or Production DATABASE_URL cutover.
- Neon Free provider returned **nonzero compute_time_seconds=1746 / active_time_seconds=6888**. Treat those as preliminary provider counters, not as measured billed CU-hour capacity. Preserve mandatory measured usage, cold start, side-effect-safe rollback, independent protected backup and final fresh data parity requirements.

---


## CUTOVER SAFETY DECISION — 2026-10-14 (ACTIVE)

- Adopt the reviewed `docs/runbooks/production_neon_cutover.md` (backend PR #26 merged `9ba207da2c5b18bf77003fd7e9b409ac69533f08`, 4/4 CI PASS) as the **planning guide**, NOT approval for live DB, secret or infrastructure changes.
- Rehearsal `neondb` is an old PostgreSQL 18 production copy. Never overwrite it or switch the app to it directly. Proposed `directpilot_live` is an **uncreated** empty final destination; create only after explicit operator approval and scoped restore review.
- A **fresh consistent dump while all writes/Meta/payment webhooks are controlled** is mandatory, with row parity and reverse/recovery plan. Do not roll back by merely reverting DATABASE_URL after Neon accepts writes.
- Neon lists **zero snapshots and zero scheduled snapshots**, so off-provider protected backup/restore proof remains a pre-cutover requirement. Owner's earlier plaintext encryption waiver applies only to rehearsal. Read-only actual customer data tests only; no Meta/payment side effects.
- Render inbound database allowlist independently verified empty; preserve this security posture until a time-limited scoped source backup window is separately approved.

---


## ACTIVE DECISIONS — 2026-10-13 (latest; supersedes conflicting older entries)

1. **Database continuity priority P0.** Render Free Production PostgreSQL `dpg-db0escm0tbcc73fhig2g-a` expires **2026-11-02T11:59:46Z**; target a safe, verified migration by Oct 25. A deadline does not waive backups, data parity, rollback or explicit approval.
2. **Separate Neon Production and UAT permanently.** Neon Production `billowing-poetry-05589994` / `neondb` (PG18.6) contains a **restored point-in-time copy**, not an authoritative live synchronized source. Neon UAT `round-shape-42044596` must never be mixed/copied over Production.
3. **Isolated restore accepted as evidence, not as cutover approval.** Neon shows 82 tables, 76 sequences, 522 indexes, 427 source-compatible constraints; PG18 adds 689 catalog NOT NULL constraints. Migration `0025_trial_three_days`, three trial plans 3 days. Operator reports exact 82-table row-count parity with original snapshot. Final source delta/write-freeze is mandatory before live switchover.
4. **Owner's encryption deferral is narrowly scoped.** Owner temporarily waived encrypted backup as a condition of **isolated restore rehearsal only** to move faster. Plaintext backup on C:/D: is still a security/durability exposure. Do NOT construe this as approval to operate Production without an independent protected/restorable backup.
5. **No side effects while testing copied Production customer data.** Use only SELECT/read-only SQLAlchemy preflight against restored Neon, no real signups/payments/Meta sends/cron or app startup migrations. Synthetic write/auth/transaction tests run only on disposable PostgreSQL 18 CI databases. `tools/neon_readonly_preflight.py` requires exact Neon hostname and server-enforced read-only session; real workstation execution is pending.
6. **Neon Free capacity remains conditional.** Free 100 CU-hour/month; configured 0.25–2 CU, default idle suspension, no pooler. Do not infer 0 cost from provider API's current zero compute counter; confirm settled billing/usage and test cold wake. `/live` is safe health endpoint; avoid unnecessary frequent `/ready` polling. Evaluate smaller SQLAlchemy pools only through tested, approved configuration.
7. **No automatic Production deployment or DATABASE_URL change.** Backend CI PR #24 (`dab43e7`) and #25 (`f5b6f98`) merged with all 4 jobs PASS (905 tests passed / 7 skipped in latest CI). Render Production + UAT remain LIVE at `bfe67fd`, autoDeploy OFF. Frontend Production `/solutions` verified READY at `79b8fad`.
8. **Cutover requires a separate explicit approval**, final write freeze/snapshot/delta validation, preserved payment/receipt/order/idempotency state, safe Meta webhook replay, rollback tested against post-switch writes, and alerts. Do not roll back by merely reverting DATABASE_URL after new writes without data reconciliation.
9. **Render Production inbound access now CLOSED (verified 2026-10-14):** direct Render PostgreSQL inventory reports `ipAllowList=[]` (zero rules). Do not reopen `0.0.0.0/0`; any future source access requires explicit approval, /32-only scope and timely revocation.

---


> Read after `AI_HANDOFF.md` and `PROJECT_ROADMAP.md`.
> Last SEO decision reconciliation: 2026-10-11; other decisions retain their independent checkpoints.
> These decisions remain fixed unless new verified technical or product evidence justifies a change.

## Continuity and Evidence

- `AI_HANDOFF.md` is the primary cross-chat continuity authority.
- Chat history is not the project Source of Truth.
- Read continuity files in this order:
  1. `AI_HANDOFF.md`
  2. `PROJECT_ROADMAP.md`
  3. `DECISIONS.md`
  4. `CURRENT_STATE.md`
  5. `NEXT_ACTIONS.md`
- Evidence precedence is: verified runtime/deployment evidence > deployed commit > repository source > continuity documents > old chat history.
- Never mark PASS/DONE without evidence.
- Repository HEAD and deployed runtime commit are separate facts.
- Documentation-only commits must never be described as deployed runtime code.
- After a meaningful Production release, update the five continuity files only after Production verification passes.

## 2026-10-11 — Frontend UI and Animated Branding Release Decision (ACCEPTED)

- **Accept Production frontend PR #9:** UAT-origin humanized UI, motion glyphs, vector animated D tab favicon, dashboard/admin visual improvements, responsive sidebar single-line navigation and related copy/presentation improvements. GitHub `main` SHA `f5f6a5399f938969b9307475eeed208f0e10988b`; Vercel Production `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` **READY**, aliased to `directpilot.ir` and `www.directpilot.ir`.
- **Acceptance evidence:** owner confirmed favicon animation and dashboard/layout look correct in live Production Chrome after hard refresh; record **VISUAL PASS**. Prior Auth/UX evidence is retained separately. Do not elevate this to new full authenticated session, payment, Meta or GA4 registration E2E PASS.
- **Release discipline:** branch history diverged; resolve with selective UAT-to-`main` changes while preserving Production GA4/SEO events, trial truthfulness, manual bank-card/payment fixes and backend-owned entitlements. No changes to database, backend runtime, secrets, Vercel Authentication or DNS were authorized or needed.
- **No immediate additional redeploy:** intermittent Vercel daily build quota and `module_not_found` on a non-final preview commit were superseded by the final `main` Production READY deployment. Never attempt to promote intermediate `release/humanized-ui-uat-20261011` commit `8208b27`.
- **Unchanged gates:** real `sign_up` event E2E delivery, search ranking impact, database durability/backup-restore (free DB expiry 2026-11-02), and explicitly open admin-plan behavior retest remain pending until their own verification.

## Architecture

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL.
- Keep a Modular Monolith for MVP; do not introduce microservices opportunistically.
- Official Meta APIs only.
- Tenant/store isolation is mandatory and server-side.
- Browser API traffic remains same-origin under `/api/v1/*`.
- Cloud backend selection remains server-side through `DIRECTPILOT_API_UPSTREAM`; never expose backend secrets through `NEXT_PUBLIC_*`.
- Public UUID-style IDs remain API boundaries; internal numeric IDs are persistence details.
- Migrations are additive/forward-only unless an explicit migration plan says otherwise.
- Do not add unnecessary frontend catch-all proxies, serverless functions, or polling.

## Runtime Precedence and AI

```text
Human Takeover
  -> Story-specific Automation [future]
  -> General Deterministic Automation
  -> AI Assistant fallback
```

- Human Takeover suppresses both automation and AI.
- Exact deterministic automation matches perform ZERO LLM, PromptBuilder, knowledge retrieval, or AI usage.
- AI execution requires entitlement.
- Preserve deduplication, echo prevention, and loop protection.
- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256` unless a separately justified change is approved.

## Authentication and Session UX

- Authentication state is server-authoritative.
- Browser auth uses the existing HttpOnly session-cookie contract; do not move auth tokens into localStorage or sessionStorage.
- A valid session must survive normal refresh/navigation and be restored through `/auth/me`; repeatedly asking for a password while the server session is valid is not an accepted UX.
- Authenticated customer routing resolves to `/dashboard`; authenticated platform administrators resolve to `/admin`.
- Unauthenticated protected customer/admin routes must redirect to `/login` without loops.
- Login CTA must not remain visible after authentication.
- Customer and platform-admin workspaces must expose a real backend logout action.
- Authenticated password change requires the current password, enforces backend policy, and revokes all sessions.
- Session-management UI must never expose raw session tokens.
- Forgot-password/self-service recovery remains BLOCKED until a verified email/SMS recovery delivery provider and secure token lifecycle exist. Do not ship a fake or UI-only reset flow.

## Frontend Release Discipline

- UX/Auth changes are accepted in UAT before Production promotion.
- Promotion should use the exact UAT-approved change set; do not insert unrelated feature changes between UAT acceptance and Production.
- The accepted Frontend UX/Auth release is `1f82494f87fe39f0fb2e22043adfd75f7735668c`.
- The accepted Backend Auth/Session release is `84b7df6196fe380fad21a3791e3160840c098602`.
- UAT and Production smoke evidence must be kept distinct; an untested criterion is NOT_TESTED/BLOCKED, not FAIL.

## Commerce

- Backend is authoritative for plan, entitlement, payment, subscription, and activation state.
- Frontend/browser state must never activate a subscription.
- Activation uses immutable purchase/order snapshots.
- Never blindly retry an ambiguous external-provider write.
- Current verified V1 sale scope is `AUTOMATION_V1`.
- `AUTOMATION_TRIAL` and `AI_ASSISTANT_TRIAL` are trials and are not purchasable.
- Legacy FREE/TRIAL/START/PRO plans are not public purchasable plans.
- Do not publish a paid AI Assistant plan unless a new explicit product decision and verified source/runtime change establishes it.
- Payment-provider source/routes are not equivalent to real provider acceptance.

## Environment and Infrastructure

- UAT/Production environment separation is complete and must not be rebuilt without regression evidence.
- Production and UAT use independent runtime configuration/secrets.
- Render backend auto-deploy remains OFF.
- No paid infrastructure/resource may be created without explicit owner approval.
- Current Free Production PostgreSQL is pilot infrastructure only; real-customer durability requires replacement/upgrade plus backup/restore acceptance.
- Production database external access controls must not be weakened merely for inspection.

## Security and Operations

- Never write secret values to Git, chat, logs, screenshots, or frontend public variables.
- Credential documentation records names, locations, and verification status only.
- Production administrator bootstrap/reset credentials remain outside Git and logs.
- Preserve unrelated local dirty work. Never reset, clean, auto-stash, force-push, rebase published history, or rewrite history automatically.
- A Git push is not deployment acceptance; correlate each deployed runtime with its exact commit SHA and verify runtime evidence.

## Shared Meta App Pilot Decision

- For the current pilot, Production and UAT may use the same Meta App credentials.
- Meta Developer settings are currently inaccessible to the owner; therefore the approved pilot workaround is a guarded UAT -> Production relay bridge.
- The provider-facing OAuth redirect intentionally remains the already-registered UAT callback:
  `https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production OAuth requests use that same provider redirect but prefix newly generated state with `production.`.
- UAT may relay only callbacks whose state matches the configured `production.` prefix to:
  `https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production owns and consumes its own OAuth state and stores its own encrypted token/connection; UAT must never consume/copy Production OAuth state or encrypted connection rows.
- UAT webhook relay may be enabled only after Production OAuth has established the matching Production connection.
- Webhook relay must validate the original Meta HMAC signature before forwarding, preserve exact raw bytes/signature/delivery identifiers, avoid internal retries, and fail closed so Meta can retry.
- Production must not have relay targets configured; validated Production settings reject that topology to prevent relay loops.
- Production `META_SEND_ENABLED` remains false until inbound routing is proven and the pilot account allowlist is explicitly restricted.
- Production runtime now enforces the pilot restriction at startup: if `META_SEND_ENABLED=true`, `META_SEND_ALLOWED_ACCOUNT_IDS` must contain exactly one account. Zero or multiple entries are invalid.
- Secret values stay outside Git/chat/logs/docs. Production and UAT retain independent `INSTAGRAM_TOKEN_ENCRYPTION_KEY` values.
- If the owner later regains Meta Developer access, the preferred steady-state design is direct Production callback/webhook registration; the relay is a controlled pilot bridge, not a permanent architectural requirement.
- If simultaneous independent live webhook delivery is required in both environments, use separate Meta Apps rather than broad relay/multiplexing.

## SEO and Search Indexing

- Production `https://directpilot.ir` is the only indexable DirectPilot web environment.
- Vercel Preview/UAT must remain `noindex, nofollow`; preview robots must block crawling and preview sitemap output must remain empty.
- SEO copy must match backend-authoritative product facts. Do not advertise “Free Forever” while the active Automation trial is 14 days with up to 3 automations and one Instagram account.
- Prefer optimizing pages already receiving Search Console impressions before creating large volumes of new content.
- Keep one primary commercial owner per important keyword cluster to reduce cannibalization.
- Search Console deployment acceptance and ranking acceptance are separate: successful deployment does not imply immediate recrawl or ranking improvement.
- The baseline for SEO Phase 1 is the settled 28-day period through 2026-10-04: 14 clicks, 315 impressions, 4.44% CTR, average position 40.30.
- SEO Phase 2 accepted SHA is `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`; historical live Production audit was clean on five priority SEO pages.
- 2026-10-11 SEO PR #1-#5 historical publication checkpoint: frontend SHA `e527c8f7e47a3259457f4efd72ded588eb3e26b9` at Vercel `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2` (READY at the time); six marketing URLs were audited with 0 SEO issues. PR #8 then advanced Production to SHA `d9a1a53a6171f3d417637d12cec66eed1832a07b`, Vercel `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` READY (historical). **Current Production** is accepted PR #9 `f5f6a5399f938969b9307475eeed208f0e10988b` / `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` READY.
- Keep the educational query cluster (e.g. «دایرکت هوشمند چیست») centered on `/blog/instagram-smart-direct`; the product/service cluster (e.g. «دایرکت هوشمند اینستاگرام», «دایرکت اتوماتیک») on `/instagram-direct-automation`, with contextual two-way navigation, not duplicate commercial landing pages.
- Any marketing copy about free access must reflect the verified 14-day trial, not a permanent free plan. Do not claim guaranteed conversions, customers, security certifications or ranking improvement without evidence.
- Fix article internal-link rendering when bold Markdown encloses an internal link; ensure relevant next-step links are clickable and visible in rendered HTML. Preserve existing canonicals, URL ownership, semantic content and Preview/UAT noindex protections.
- Evaluate SEO changes through fresh settled GSC data after recrawl; six pages with 0 technical findings and Vercel READY prove release health, **not** Google ranking uplift.
- GA4 measurement is Production-only and **consent-gated**; do not load its script before user opt-in, send PII, invoice/order identifiers or payment details, or enable `unsafe-eval` as an analytics workaround. Preview/UAT remain analytics-free. Keep manual sanitized page views and avoid duplicated history-based pageview collection.
- `sign_up` is the **only configured signup-completion Key Event**; `signup_intent` is a click-intent signal. Record sign_up only after successful backend registration, and do not assign a default cash value to trial signup. Do not assert E2E delivery until a successful controlled registration appears in GA4.
- GA4 and Search Console integration has two separate links: the native Google-side Search Console Domain Property connection and the GSC Wizard GA4 OAuth/property connection. Both are verified for `DirectPilot - Production` / `properties/558426868` / `sc-domain:directpilot.ir` on 2026-10-11. GA4 page_view HTTP 204 + Realtime event confirms ingestion, **not** form conversion or historical GA4 collection.
- For reporting, require matched settled comparison windows and respect the GA4 launch date (2026-10-11), Google recrawl timing, small samples, consent and differing metric definitions. Never infer rank growth, successful registration, payment or revenue from page-view activity alone.
- Retain the existing weekly SEO task (Monday 09:00 Asia/Dubai flexible), upgraded to SEO + GA4; monitor 10 URLs, keyword clusters, sessions and verified Key Events. It reports findings but must not mutate code, billing, site settings or assets on its own.

- OAuth relay is now the accepted pilot workaround when Meta Developer access is unavailable: Production creates the OAuth state, Meta returns to the already-registered UAT callback, and UAT relays only the Production-prefixed state to the Production callback.
- Webhook relay activation is a separate gate and must not be enabled until Production OAuth connection is verified.
- Production outbound remains fail-closed until the account allowlist is explicitly constrained and controlled E2E is ready.

- Production OAuth through the relay bridge is accepted based on live provider evidence; do not require Meta Developer access for this pilot path unless the existing registered callback changes.
- Webhook relay is now enabled UAT -> Production, but Production sending stays disabled until inbound routing and dedupe are verified.

- A live inbound event through the relay bridge is accepted as Production inbound PASS when relay, account resolution, persistence and webhook processing all complete without warning/error; this was satisfied on 2026-10-07.
- For the first Production outbound E2E, use a deterministic AutomationRule rather than AI fallback. AI fallback remains blocked until Production LLM configuration is separately verified.
- Never enable `META_SEND_ENABLED=true` with an empty send allowlist because the current sender treats an empty allowlist as unrestricted.


## Future Product Scope

- Telegram No-Code AI Bot Builder / Managed Bots is an accepted future exploration track.
- It is explicitly outside the current DirectPilot execution scope.
- Do not divert current Production readiness, Meta outbound E2E, database durability, payment or LLM verification work to implement it opportunistically.


## Platform Admin Customer Automation

- Platform Admin customer automation management belongs under **Admin -> Customers & Stores**, scoped to the selected tenant/store.
- Reuse the same AutomationRule domain/service/API used by the customer workspace; do not create a second provider-only rule model or duplicate runtime.
- Platform access must use the existing explicit platform permission path in `resolve_authorized_context`; do not use impersonation or weaken tenant/store isolation.
- The Admin UI may expose the rule builder only when the selected store has the `instagram_automation` effective capability.
- Backend capability and automation-limit checks remain authoritative even when the Platform Admin UI displays an estimated/current limit.


## Controlled Production Outbound
- The first Production outbound test may run only with the single pilot-account restriction active.
- Use one deterministic `قیمت` message from the second Instagram account.
- If routing, duplicate handling, account restriction, or echo behavior differs from expectation, disable Production send immediately before further investigation.


## Controlled Outbound Retest Rule
- If a pilot message produces no inbound webhook at either relay or Production, do not classify automation/outbound as failed.
- After relay health is restored, perform exactly one clean retest before changing rule logic or outbound configuration.


## Meta Controlled E2E Acceptance — 2026-10-11
- Accept Production deterministic Meta outbound E2E as PASS based on runtime evidence.
- Acceptance requires one inbound event, one deterministic response delivery, no AI fallback, no duplicate second send, and no echo loop; all were satisfied in the clean retest.
- Production send is returned to disabled after the test.
- Do not reopen Meta transport work without regression evidence.
- Production database durability/backup-restore is the next highest-priority real-customer readiness gate.


## Production DB Durability Assessment — 2026-10-11
- Current Production Postgres is Free, expires 2026-11-02, has no managed backups/PITR, no HA, no replicas, and an empty external IP allowlist.
- Seven-day metrics show very low Pilot load: CPU ~0.007 cores, memory roughly 40-60 MB, active connections peak 6.
- Recommended paid target: Render Postgres `0.1c-256mb` with current storage kept minimal.
- Expected base compute cost: about $6/month; 1 GB storage included, additional Postgres storage is billed separately.
- Paid Render Postgres enables PITR; on a Hobby workspace the recovery window is 3 days. On-demand logical exports are available for paid instances and retained for 7 days.
- Compute-plan change requires brief database downtime.
- Paid infrastructure change remains blocked until explicit owner approval.


## Production DB Upgrade Decision — 2026-10-11
- Owner explicitly deferred the paid Production Postgres upgrade for now.
- Do not change the current Free Production database plan or incur paid infrastructure cost without a new explicit approval.
- Current risk remains accepted temporarily: Free Production Postgres expires 2026-11-02 and does not satisfy durability/backup-restore acceptance.
- Real-customer onboarding remains blocked by Production database durability until this decision is revisited.


## LLM Production Configuration — 2026-10-11

- Treat LLM diagnosis as PASS but Production LLM readiness as BLOCKED until a Production-specific provider credential exists.
- Never copy UAT LLM secrets into Production and never request/paste provider secrets in chat.
- Selected-provider/model/credential-presence may be logged only as sanitized metadata; credential values must never be logged.
- Production currently selects OpenAI but has no OpenAI credential; Groq credential/model are also absent.
- Before selecting Groq for Production, use a currently supported Groq model rather than blindly mirroring UAT configuration.
- Preserve deterministic-first execution: a matched AutomationRule performs zero LLM work.


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


## Production AI Fallback Acceptance — 2026-10-11

- Accept Production Groq AI fallback E2E as PASS.
- Approved Production runtime: `LLM_PROVIDER=groq`, model `qwen/qwen3.8-27b`, context 4096, max output 256, reasoning effort none.
- Keep provider credentials environment-specific and secret; never copy UAT credentials into Production or expose keys in logs/chat.
- Controlled acceptance requires one provider request, assistant persistence, exactly one Meta delivery, no provider/outbound failure, and no duplicate/echo loop; all were satisfied.
- Keep `META_SEND_ENABLED=false` outside explicitly controlled pilot tests until broader Production-send policy is approved.
- Server-authoritative quota guard remains part of the AI path; do not weaken it for testing.


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

- Decision: keep Production Payexa fail-closed without a credential until explicit merchant credential provisioning is complete.
- Decision: UAT must use only Payexa Sandbox and its sandbox credential; it must never point at Production Payexa.
- Decision: do not expose Payexa checkout broadly until controlled acceptance is complete.


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

- Decision: manual card transfer + Admin approval is the authoritative MVP payment method.
- Decision: Payexa is parked/deferred and must not block MVP Production readiness.


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

- Decision: Production banking destination data must be explicitly configured by an authorized Admin; never copy UAT financial details automatically or use synthetic card data.


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

- Decision: never rely on a React SyntheticEvent/currentTarget after an async boundary; capture required DOM references synchronously before awaiting.


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

## Decision — Manual Card Transfer Accepted for Production MVP (2026-10-11)

- The Production MVP payment acceptance gate is satisfied by manual card transfer + receipt upload + Admin/backend-authoritative approval.
- Controlled Production E2E completed successfully through payment approval, paid order, active `AUTOMATION_V1` subscription and entitlement activation.
- Owner visually confirmed the approved payment in Production.
- Payexa/KPay remain deferred and are not required for MVP payment readiness.
- Do not substitute or reopen an automated gateway unless the owner explicitly changes this product decision.


## 2026-10-12 — Shared Meta remains immutable during UAT tests
- Owner decision: UAT and Production must share existing Meta App configuration. Never change Meta callback URL, subscriptions or shared settings to conduct UAT tests.
- Current UAT webhook relay forwards Meta-signed payloads to Production. Preserve it; no real messages or webhook POST probes as part of the offline isolation test.
- Safe validation is a pure local test of existing ingestion service with ephemeral SQLite database, disabled outbound Meta sending, and no relay calls. Not a substitute for Meta E2E delivery evidence.

## 2026-10-12 — Prepaid subscription period rules
- Customer may prepay 1–12 months only for paid plans with an authoritative 30-day base duration. Price = plan price × selected months; duration = 30 × months days. No discounts, recurring charge or installment scheduling.
- Backend is authoritative: frontend quote is informational; order and payment snapshots drive the actual charged amount and activated term. AI period request/reply/token allowances scale to total purchased period; Automation rule limit remains unchanged.
- Keep existing manual card-to-card receipt upload and admin verification; no changes to shared Meta configuration or Production releases.

### UAT deployment evidence — 2026-10-12
- The prepaid pricing/duration policy above has shipped to UAT backend (`b1a63ea9`, Render LIVE) and UAT frontend (`34b19e6e`, Vercel Success); no Production deployment. Manual three-month E2E remains pending; do not conflate green CI with payment acceptance.

### Final UAT release verification — 2026-10-12
- Multi-month checkout and reconciled dashboard/payment UX are merged into UAT at `8f083473`, Vercel Success. Manual full payment validation pending; shared Meta and Production unchanged.


### UAT receipt preview update
- 2026-10-12 Decision: admin should inspect uploaded manual payment receipts inside UAT review page without mandatory downloads. Preserve authenticated PAYMENT_READ guard, no-store/same-origin embedding policy restricted to receipt route, and separate explicit admin approval. Download/new tab only fallback, not default.


### 2026-10-12 UAT compact payment UI
- 2026-10-12 customer UI policy: following confirmed payment, display authoritative active subscription/active product plan(s); purchase CTA in active subscription section is labelled `ارتقا پلن`. Admin payment details are compact; natural-sized image receipts and a bounded PDF viewer reduce whitespace without changing payment approval workflow or authorization.


### Production promotion preflight (2026-10-12)
- 2026-10-12 Production promotion policy: owner authorized transition from approved isolated UAT. Do not bulk copy UAT PostgreSQL into Production; migrate schema and approved reference catalog only, do not transfer test identities, payment receipts, cards, sessions or Instagram tokens. Preserve Production frontend GA4/SEO/security changes, existing shared Meta app/webhook routing and existing operational payment data. Do not release while frontend draft PR #19 has conflicts or Production DB backup/compatibility unverified.


## 2026-10-12 — Controlled promotion decision (latest)
- User authorized UAT-accepted changes for Production, including multi-month prepaid periods and UX. Backend deployment is approved and LIVE; frontend PR #20 merged after independent CI, but deployed Vercel status is not yet verified.
- Preserve consent-gated Production GA4 and SEO; Trial homepage still truthfully says 14 days, UAT-only 3-day admin commercial policy must not modify Production. Keep shared Meta app, relay, outbound guard and credentials untouched.
- Product price, active/purchasable AI status must be server-authoritative. Paid `AI_ASSISTANT_V1` is a desired Production rollout item but remains pending until Production catalog access and safe backup/reconciliation are available; never copy UAT tenant, payment card, receipt, token, or authentication data.


## Production promotion policy — 2026-10-12 owner instruction
- Owner approves deploying accepted UAT multi-month prepaid plans, secure inline/fit receipt preview, compact admin payment details, active product names and `ارتقا پلن` CTA into Production. Preserve manually approved card-transfer processing, original Production customer data, GA4/SEO/CSP and shared Meta routing.
- The explicitly approved UAT paid AI product terms are IRR 6,900,000 / 30 days, 1,000 requests, 1,000 replies, one Instagram account, `ai_assistant` + `knowledge_base`. Automation remains IRR 4,900,000 / 30 days, 20 automation rules and one Instagram account. Prepaid price and duration scale by 1–12 periods on server; no recurring charge or discounts.
- Production AI catalog rollout is additive/idempotent: insert only if missing, never overwrite existing administrator-defined plan, customer/receipt data, subscriptions or historical snapshots. Production trial period stays 14 days (do not copy UAT-only trial-duration experiments).
- No paid Render database upgrade, network exposure, bulk Neon import or Meta send-settings changes. Production database durability and verified off-host backup are separately OPEN.


## Approved paid AI plan now published — 2026-10-12
- UAT-approved commercial policy is released by additive migration 0024, not by copying the Neon UAT database. `AI_ASSISTANT_V1` is publicly purchasable at IRR 6,900,000/30d with 1,000 reply and AI-request limits and one Instagram account. `AUTOMATION_V1` continues IRR 4,900,000/30d with 20 automation rules.
- UAT and Production both use backend commit `90aea1e9`, and independent Production public API acceptance PASS (GitHub Actions `38275924090`). Existing Production customers/cards/receipts, UAT-only trial changes and Meta settings untouched.
- Frontend status remains source merged and CI green, not Vercel-runtime verified; paid database upgrade remains deferred, with backup/restore gate OPEN.


### Mobile login overlay hotfix — 2026-10-12
- 2026-10-12 Mobile navigation accessibility decision: close mobile overlay on every anchor activation, make hidden overlay inert, size for dynamic viewport and iOS safe-area; preserve GA4/SEO/CSP and all auth/Meta/payment API behavior. Release as UAT-first frontend-only hotfix; browser behavior and Vercel live deployment require separate independent verification.


### Customer Dashboard UAT UX (2026-10-12)
- 2026-10-12 Customer dashboard UX policy: online/live conversations are no longer displayed or navigable in the customer's authenticated dashboard; this is a frontend surface removal only, not data loss, API deletion or shared Meta change. Keep product-specific Automation and AI configuration/entitlements. Show authoritative billing and connection status only; pending/unknown API reads must not be represented as inactive subscriptions/disconnected Instagram or encourage duplicate payment. Prioritize unfinished/submitted payment, then missing subscription, missing Instagram, then business setup. Make mobile links accessible and dismiss account menu after navigation. Apply UAT-first until visual acceptance before Production.


### Customer Inbox follow-up — 2026-10-12
- 2026-10-12 Clarification of customer conversation removal: not sufficient to hide sidebar/route. UI acceptance requires removing actual InboxPanel presentation code from client bundle while preserving backend records and APIs; implemented UAT PR #24. Keep Production unchanged pending UAT Vercel deployment and manual acceptance.


### 2026-10-13 decisions: trials and solutions
- All new free trials for TRIAL, AUTOMATION_TRIAL and AI_ASSISTANT_TRIAL use 3 calendar days; existing subscriptions and order duration snapshots must never be retroactively shortened or rewritten. Authoritative migration is 0025_trial_three_days, Backend bfe67fd.
- Free-trial public copy should communicate exactly 3 days; avoid 14-day and 24-day claims, while presenting a direct accurate expiry in authenticated subscription view.
- Solutions marketing must be industry-neutral. Use online stores, clothing, beauty services and education as practical examples rather than making online retail the umbrella audience.
- Promotions between UAT and Production should be selective, gated by CI and live Vercel READY with alias SHA, preserving GA4, SEO, payments and backend Meta interfaces.


### Production Solutions promotion verified — 2026-10-13
- Frontend PR #29 merged at commit `79b8fad33b72e350b644162f69439d8c3e777471`; Production CI PASS; Vercel deployment `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP` READY and aliases `directpilot.ir`, `www.directpilot.ir` active. General `/solutions` page and links promoted from UAT selectively, with shops/services/education/salons only as examples. Existing 3-day trial copy, SEO, GA4 and payment flows preserved. This supersedes earlier notes stating generic Solutions Production promotion pending.
