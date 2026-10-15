# DirectPilot Current State

## 2026-10-15 — MOBILE UX / NAVIGATION REWORK MERGED IN OFFICIAL UAT

**Owner requirement for ALL future DirectPilot chats:** Mobile navigation must have obvious **بازگشت/بستن**, never trap customer/admin in a menu or long form; all changes are developed and tested on canonical **`https://uat.directpilot.ir`**, NOT abandoned temporary Preview URLs. Check latest real deployment and browser acceptance, don't ask owner to re-explain mobile requirements. Production is strictly separate.

**Code/CI DONE:** Frontend `namach2727-coder/directpilot-web` UAT branch, PR **#32 MERGED** SHA **`dad3a3790246f96fbbe760d26e2415afd0a45851`**. Shared customer/admin mobile navigation now has labeled menu toggle, independent visible close, Back to overview/home, Escape/outside tap/history dismiss and current section label. Public full-screen menu has fixed visible Back and proper scroll/focus/route restoration. Login/register/billing payment pages share back destinations; long automation editing modal has top Back; error page has home return. Touch targets and iOS safe areas improved. PR final feature SHA `176dbeb712e780aa1ce0b8630745da18f4025039` passed **223/223 tests, TypeScript, ESLint, Next build**. Backup branch `backup/uat-before-mobile-navigation-20261015` retains previous UAT source.

**Deployment VERIFIED:** Vercel official UAT `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` READY at SHA `dad3a379...`; alias `uat.directpilot.ir` points to that deployment, while Production `directpilot.ir` still points to `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF`. Domain Smoke run `38709714205` PASS, HTTP Diagnostic run `38709713924` PASS. Latest UAT merge quality workflow run `38709714016` was running at this checkpoint: verify status; do not falsely claim final UAT browser acceptance.

**Still OPEN:** Actual mobile Safari/Chrome visual, tap/Back, VoiceOver and customer/admin usability signoff behind Vercel SSO; test 320/360/375/390/768px, long scroll modal, checkout/receipt journey and role guards. Source code+automated tests do NOT prove polished mobile experience on a real handset. Additional dashboard/payment information architecture redesign is a separate measured UX phase. Exact checklist: `docs/runbooks/uat_mobile_frontend_ux_audit_20261015.md`.

**Permanent nonnegotiable architecture remains:** PostgreSQL/Neon BYTEA stores receipts and product images, no R2/S3; all receipt versions traceable by customer/order/payment for 4+ months with backups. Production Render/Neon cutover still requires independent backups, freeze/replay, parity, rollback, commercial hosting decision, and separate owner GO. Five-file cross-chat read order: `AI_HANDOFF.md` → `PROJECT_ROADMAP.md` → `DECISIONS.md` → `CURRENT_STATE.md` → `NEXT_ACTIONS.md`.

---


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

**Reality distinction:** Payment receipt BYTEA is already in deployed code; the new product-image BYTEA code exists ONLY on GitHub PR #34 (pending). UAT Neon is still `0025_trial_three_days` until a separately verified migration changes it. Existing isolated Vercel preview/customer/admin smoke PASS is not evidence that the new image bytes can already be uploaded.


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

**Verified distinction:** a READY deployment exists for Vercel UAT, while older Function invocation failures were observed. There is no verified healthy Vercel UAT application or successful Neon UAT API readiness call yet.


## 2026-10-14 — Final sync tooling merged; actual data transfer remains BLOCKED

- Backend PR #30 **MERGED** commit `3f07b16bd7ade6f065f3638417e5adc838f6f810`, latest CI run `38530717010` **4/4 PASS**, Python **941 passed / 7 skipped**. New operator-only `tools/production_final_sync.py`, `docs/runbooks/final_render_to_neon_sync_20261014.md` now in `backend-main`.
- Neon Production `directpilot_live` independently rechecked **0 tables / 0 sequences**; old restored `neondb` remains 82 tables/Alembic 0025; UAT untouched. Render authoritative source available, PostgreSQL inbound allowlist empty, Production API live, no maintenance. **NO fresh Render dump, restore, Production DB cutover or traffic interruption** occurred.
- Real final source sync **BLOCKED** until local operator Codex can access Render with scoped temporary /32 AND all writer/Meta+Payexa callback freeze/replay/independent encrypted recoverable backup are verified. Do NOT claim PR merge or empty DB means data parity or migrated subscriptions/orders. No dropping/cleaning existing databases.

---


## 2026-10-14 Live state after final-sync initiation

- New Neon Production database `directpilot_live` CREATED by connected Neon action, owner `neondb_owner` on project `billowing-poetry-05589994`; independent read-only SQL verified `0` application tables and `0` sequences. This is the planned EMPTY fresh final data target; **NO data imported**.
- Existing Production rehearsal `neondb` remains 82 tables/Alembic 0025 from Oct 13, stale vs current Render. Neon UAT independent, untouched.
- Render Production PG remains AVAILABLE, external allowlist `[]`, expiry 2026-11-02; hosted SQL query failed because no inbound IP can be allowlisted for remote connector. Both Render FastAPI services LIVE, no deployment, no maintenance window and no DATABASE_URL changed.
- `tools/production_final_sync.py` + `docs/runbooks/final_render_to_neon_sync_20261014.md` prepared for locally controlled operator fresh frozen pg_dump, protected backup, empty Neon restore and independent reconciliation. **NO final dump or restore performed; writer freeze and event hold/replay unproven.**

---


## 2026-10-14 CURRENT STATE: full-Render-exit preparation

- Owner's target is zero Render resources, not just PostgreSQL cutover. Render currently still hosts 2 Free Web Services (Production `directpilot-api`, UAT `directpilot-uat-api`) and 1 Free Production PostgreSQL expiring 2026-11-02, with no Render KV.
- Neon Production old snapshot `billowing-poetry-05589994/neondb` still contains 82 tables and is NOT in live sync. New final Production `directpilot_live` is proposed but does not exist; Neon UAT separate `round-shape-42044596/neondb`. Prod and UAT must move to external Docker-backed compute with secure env and persistent volumes.
- Git-only portable host deployment draft `deploy/full-exit/compose.yaml`, Caddy, safe no-auto-migration entrypoint and target validation tests created. Operator still must choose host (OCI VM vs paid managed/VPS), set up account, transfer real Render secrets PRIVATELY, and approve staged UAT/Production cutovers. **No new host provisioned, no Production/UAT service migrated and no Render shutdown/deletion.**
- Vercel frontend currently outside Render; Hobby commercial-use terms and possible paid upgrade should be reviewed separately.

---


## 2026-10-14 Latest Render/Neon variable status

- Render Production backend `directpilot-api` remains the runtime; service `autoDeploy=no` and currently NOT in maintenance. Render service API exposes environment metadata but NOT a list of key/value secrets. **No Render secret values have been copied or moved**.
- Neon `billowing-poetry-05589994` contains only PostgreSQL `neondb` (stale restored snapshot); Neon platform Functions tool reports unavailable. Backend application secrets belong in Render, not Neon.
- A names-only preservation script and guide were prepared on an isolated GitHub PR #28, pending CI/merge at creation. Validation of *values* is not possible from current connector; requires secure private Render operator route. Production `DATABASE_URL` remains unchanged. No UAT/Meta/payment changes or Cutover.

---


## 2026-10-14 CONFIRMED CAPACITY AND MAINTENANCE READINESS

- Independent Neon project `billowing-poetry-05589994` Free `free_v3`: provider `compute_time_seconds=1746`, `active_time_seconds=6888`, current period 2026-10-12T06:36Z–2026-11-01T00:00Z. Derived tentative 0.485 CU-hour (0.485% of Free 100 CU-hour allocation); Console bill/usage NOT verified and live load NOT measured.
- Neon PG18.6 restored `neondb` 82 tables/Alembic 0025; compute endpoint observed idle and resumed on read-only SELECT (~6.65s end-to-end connector latency, not Backend latency). Pooler off, min 0.25/max 2 CU. Zero saved/scheduled Neon snapshots on readback, protected off-provider backup OPEN.
- Render Production HTTP metrics requested over 24h returned empty series (not proof of zero requests); DB active connection hourly samples 0–2. Source DB AVAILABLE, zero inbound /32 rules, expires Nov 2. Production and UAT live connections untouched.
- Backend audit reveals both Instagram webhook POST paths, Payexa callback GET/POST, signup/order/receipt/payment writers, automatic migration on start and possible one-shot startup mutation flags. **Comprehensive reversible freeze + durable replay NOT VERIFIED**. Proposed maintenance plan stored at `docs/runbooks/neon_free_usage_and_maintenance_plan.md`; no window booked; no cutover or deployment.

---


## CURRENT CHECKPOINT — 2026-10-14 — REAL NEON SQLALCHEMY PREFLIGHT PASSED

- Actual restored Production `billowing-poetry-05589994/neondb` read-only tool PASS, **reported by operator/Codex** from trusted workstation using clean backend SHA `860aae65b843de2e4361c7158f35ea0fc563f005`, SQLAlchemy 2.0.41 / psycopg 3.2.9 / Alembic 1.16.5, valid host and TLS with server-enforced read-only transactions; no Production/UAT modification per report.
- Hosted direct Neon SQL independently confirmed 82 tables / 76 sequences / 522 indexes / 427 source constraints, zero invalid indexes or unvalidated constraints, revision `0025_trial_three_days`, subscriptions 14, subscription orders 15, payments 1, orphan refs or invalid periods 0, all three trial codes 3 days. No direct hosted rerun of the owner's Python/SQLAlchemy process.
- Neon Free compute project counters now **1746 compute seconds and 6888 active seconds** (not confirmed billing units). Cutover target is still an old Oct 13 snapshot. Render source AVAILABLE, inbound IP rules empty, expiration **Nov 2**. Neon Free capacity, independent protected backup, fresh write-frozen final source copy and reversible cutover remain OPEN. No Production DATABASE_URL change.

---


## LATEST VERIFIED STATE — 2026-10-14 (authoritative)

- Render Production PostgreSQL Free: AVAILABLE, zero external inbound allowlist rules, expires `2026-11-02T11:59:46.610475Z`. Production Backend still serves Render deployment `dep-db6tq6vf3r2c73ch03bg` at `bfe67fd`; UAT remains separately LIVE at `dep-db6tpcff3r2c73cgtb30`. No Neon cutover or new Render deploy.
- Independent Neon Production `billowing-poetry-05589994/neondb`, PostgreSQL 18.6: 82 tables, Alembic `0025_trial_three_days`, 0 invalid indexes. Neon saved snapshots=0 and snapshot schedule empty. One manual payment's 40,139-byte receipt blob is stored inline, with storage-key reference; no data values printed.
- Backend cutover runbook PR #26 merged at `9ba207da2c5b18bf77003fd7e9b409ac69533f08`; GitHub Actions latest doc PR CI `38514922043` all 4 jobs PASS. **This is a Git documentation release**, not a runtime feature release.
- Real restored-Neon SQLAlchemy read-only CLI, Neon Free CU-hour/idle-wake test, protected offsite backup, fresh final sync and rollback acceptance remain OPEN. Proposed future fresh destination `directpilot_live` does NOT exist. Site must stay on Render until explicit cutover approval.

---


## CURRENT VERIFIED SYSTEM SNAPSHOT — 2026-10-13 (authoritative)

**Production is still on Render PostgreSQL. There has been NO live Neon cutover.** Older sections below are dated historical observations; when conflicting, use this verified snapshot.

| Area | Current verified status |
| --- | --- |
| Production Backend | Render `directpilot-api` LIVE `dep-db6tq6vf3r2c73ch03bg` code `bfe67fd79fb738027444fdead68b940d19b71f82` (`autoDeploy=no`) |
| UAT Backend | Render `directpilot-uat-api` LIVE `dep-db6tpcff3r2c73cgtb30`, same code SHA, `autoDeploy=no`; isolated Neon UAT unchanged |
| Frontend Production | `directpilot.ir` Vercel READY `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP`, commit `79b8fad33b72e350b644162f69439d8c3e777471`; industry-neutral `/solutions` live |
| Render Production DB | Free PostgreSQL 16, **available**, expires **2026-11-02T11:59:46.610475Z**; live authoritative DB |
| Neon Production rehearsal | Project `billowing-poetry-05589994`, PG18.6, DB `neondb`, ~17 MB, **82 tables / 76 sequences / 522 indexes / 427 source constraints**, Alembic `0025_trial_three_days`. PostgreSQL18 adds 689 NOT NULL catalog constraints |
| Restore data parity | 82/82 table count comparison **PASS per operator's private Codex report**; agent independently queried target schema but **not** all original live source rows |
| Neon integrity | Three trial plans all 3 days; no invalid/unchecked FK/index, orphan subscription/order/payment links, or invalid subscription periods in read-only checks |
| Latest CI | Backend PR #24 `dab43e7` and #25 `f5b6f98` merged; CI `38401718878` all 4 jobs PASS, **905 passed, 7 skipped**. Git `backend-main` can be newer than LIVE Render SHA |
| Neon compute | Free `free_v3`, 0.25–2 CU, provider-default suspend, pooler disabled, **100 CU-hour/month** limit. Provider API returned zero usage despite DB activity: **real burn UNKNOWN** |
| App connection tests | Disposable PG18 SQLAlchemy/read-only preflight PASS in CI; **real Neon restored-data SQLAlchemy workstation preflight NOT YET RUN** |
| Backup | Original 557942-byte Render dump SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a` verified by owner; independent encrypted offsite copy and real rollback acceptance **OPEN** |
| Render DB inbound ACL | **CLOSED / PASS:** independent Render API verification on 2026-10-14 returned `ipAllowList=[]`, zero external inbound rules; previous discrepancy resolved. |
| Cutover readiness | BLOCKED: true fresh snapshot/delta, write freeze/webhook replay, rollback rehearsal, independent protected backup, actual usage validation, explicit approval |

**No Production/UAT database records, Meta settings, payment flows, Render environment variables or live services were modified by PR #24/#25 and ensuing read-only audit.** Last confirmed Render health-check is `/live` for both Backend services (does not open a DB connection); `/ready` does.

---


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


## Most recent Production code and catalog checkpoint — 2026-10-12
- Backend `directpilot-api` Render deployment `dep-db6fr2bl550s73esrnh0`: LIVE, SHA `043d37ff6d514a46eef33770cf86f4892f7f00e8`. Production APP_ENV, PostgreSQL connectivity, current Alembic head and application startup PASS. Startup logs: payment_cards active=1, active_default=1.
- Frontend `main`: PR #20 merged at `06ebe316e5193f111ebd4b0733ee85c406d0a56e`; 210 tests, TS, lint and build PASS on release candidate. Reconciled multi-month checkout, secure receipt rendering, compact admin facts and active-plan upgrades; retained GA4 and SEO. **Vercel live deployed SHA remains UNVERIFIED** due insufficient plugin project permission.
- UAT independent Neon: active/purchasable `AI_ASSISTANT_V1` price IRR 6,900,000 with 30 days/1,000 AI requests+replies, active/purchasable `AUTOMATION_V1` price IRR 4,900,000 with 30 days. Production AI row read-only verification unavailable; additive schema/data PR #15 pending CI/deployment at this checkpoint. Existing Production operational DB not replaced.
- Previous free database expiry 2026-11-02 and missing validated backup/restore remain unresolved per owner-deferral. No Prod Meta configuration change.


## Latest verified Production state — 2026-10-12 16:12 UTC
- Backend Production Render `directpilot-api`: LIVE deployment `dep-db6gco59fdbs7382opb0`, commit `90aea1e925219056a9347f344fa020e6b7b6a744`. Alembic upgraded from 0023 to 0024 and current head verified; startup and Postgres connectivity PASS. Manual payment readiness active=1/default=1.
- Backend UAT Render `directpilot-uat-api`: LIVE deployment `dep-db6gbobbc2fs73c1r860` on same SHA, current head PASS. Isolated UAT Neon readback confirms original AI and Automation rows unchanged and no duplicates.
- Paid Production public catalog: PASS in read-only GitHub Actions run `38275924090`; `AI_ASSISTANT_V1` IRR 6,900,000/30 days, request+reply 1,000; `AUTOMATION_V1` IRR 4,900,000/30 days, automation cap 20. Both are advertised as active/purchasable.
- Frontend `main` code release PR #20 merged at `06ebe316e5193f111ebd4b0733ee85c406d0a56e` with 210 tests, TS/lint/build PASS. **Vercel live deployment is still UNVERIFIED** due lack of connector project permission. No new GA4/SEO/Meta configuration changes.
- Production Free PostgreSQL expiry 2026-11-02; durability/backup restore remains owner-deferred and OPEN.


### Mobile login overlay hotfix — 2026-10-12
- 2026-10-12 Mobile login hotfix: UAT frontend PR #21 merged at 041b3ccdb4b188a46178153d62b44b239d557837, UAT Customer Journey Quality PASS. Production frontend PR #22 merged to main at 69632c8a6e0bb1ba66933d3f8b8167823fb6bcf9, Production promotion validation PASS. Root cause identified in source: open mobile panel not closed when clicking login; revised to dismiss, inert when hidden, 100dvh and safe-area. Live Vercel deployment and interactive mobile acceptance UNVERIFIED due connector project access. No Production backend/DB/Meta change.


### Customer Dashboard UAT UX (2026-10-12)
- 2026-10-12 Customer dashboard redesign: Frontend `UAT` merge `00d29a8952c867be0c0b33c5619962b4c97478f3` from PR #23; CI run `38281718727` PASS (tests/type-check/lint/build). New compact task-first overview, contextual shortcuts, three meaningful status tiles, correct unknown/loading error handling and mobile navigation dismiss. Removed customer Inbox menu/quick CTA and direct `section=inbox` route. Backend conversation data, APIs and Meta untouched. UAT actual browser visual deployment acceptance unverified and Production frontend unchanged.


### Customer Inbox follow-up — 2026-10-12
- 2026-10-12 UAT online conversations screen removal: frontend PR #24 merged UAT SHA `16e2547d0b5d2815209bcba931cf76b52afbc7dc`, CI `38285210154` PASS. Prior PR #23 only removed menu/router links; stale InboxPanel JSX persisted and now fully removed in PR #24. Production remains unchanged. Vercel UAT deployment and browser acceptance pending due plugin 403.


### Release reconciliation — 2026-10-13
- Frontend Production main 6f383fc3193f86888199d6faf06d8e93b83cb248 and UAT fb340b724eba13bf5c8225272bd69667c0659143: Vercel domains directpilot.ir and uat.directpilot.ir both READY, verified.
- Backend backend-main bfe67fd79fb738027444fdead68b940d19b71f82: Render Production and UAT LIVE. Alembic 0025_trial_three_days changes catalog duration to 3 for TRIAL, AUTOMATION_TRIAL and AI_ASSISTANT_TRIAL; existing subscription expiry and order snapshots preserved. Neon UAT catalog SELECT confirmed 3; Production DB direct SQL blocked by IP allowlist; migration deployment LIVE.
- 14-day legacy trial marketing claims replaced by 3-day text in both frontends; no 24-day claims found in audited marketing source. Frontend PRs #27, #28 merged; backend PR #22 merged.
- UAT /solutions now uses cross-industry examples and main nav points to /solutions. Production Solutions general-page promotion is distinct follow-up pending confirmation; do not assume it is live.


### Production Solutions promotion verified — 2026-10-13
- Frontend PR #29 merged at commit `79b8fad33b72e350b644162f69439d8c3e777471`; Production CI PASS; Vercel deployment `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP` READY and aliases `directpilot.ir`, `www.directpilot.ir` active. General `/solutions` page and links promoted from UAT selectively, with shops/services/education/salons only as examples. Existing 3-day trial copy, SEO, GA4 and payment flows preserved. This supersedes earlier notes stating generic Solutions Production promotion pending.
