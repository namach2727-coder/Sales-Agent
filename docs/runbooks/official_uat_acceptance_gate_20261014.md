# DirectPilot — Official UAT acceptance gate (2026-10-14)

## Canonical topology and deployment

- Official UAT browser domain: **https://uat.directpilot.ir**. Frontend Vercel project **directpilot-web**, GitHub **namach2727-coder/directpilot-web**, branch **UAT**, deployed in Vercel Preview scope with domain pinned to UAT.
- Frontend GitHub merge PR **#31** SUCCESS; current expected Git branch and domain deployment: **08828ee1358ead2e9d81d2985fe2e4b07020e355**, Vercel **dpl_8J7NSmuGuBf8U8mxzX7JQXoVKEdj** READY. **Production** alias `directpilot.ir` is separate and points to **dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF** from `main`.
- Dedicated Vercel branch-scoped `UAT` Preview environment: `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app`; `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir`. Values re-read and compared; correct. Do not replace Production values or repoint the domain.
- Dedicated Backend Vercel project **directpilot-uat-api**, branch **migration/vercel-uat-fastapi-20261014**, separate GitHub repo **namach2727-coder/Sales-Agent**. Neon project **round-shape-42044596**, branch **br-autumn-rain-arxm147n**, DB `neondb`, Alembic **0027_traceable_receipt_versions**. Do not confuse its Vercel internal Production environment with DirectPilot commercial Production.

## CI and public routing evidence (PASS)

1. Frontend PR #31 GitHub Actions: **216 tests PASS**, TypeScript PASS, Lint PASS, Next build PASS. Source backup branch `backup/uat-before-vercel-neon-sync-20261014`, SHA `a8764a7dc9b4144a0edbfa07afc8ca4bb3667864`.
2. GitHub `Official UAT Domain Smoke` run **38565672177 PASS**: anonymous same-origin `GET /api/v1/auth/me` returns **401 JSON**; versioned receipt API `GET /api/v1/admin/payments/smoke-invalid/receipts` returns **401 JSON**; dedicated Backend `/ready` returns **200** with `status=ready`, `database=available`, `migration=current`.
3. GitHub `Official UAT HTTP Diagnostic` run **38565116215 PASS** observed `/login` and `/robots.txt` -> **HTTP 302 to `vercel.com/sso-api`** for unauthenticated CI clients, *not* public page availability. Vercel Authentication is in front of HTML pages. Do not disable protection, generate public bypass links or change firewall without owner's explicit approval. Correct browser test requires authorized Vercel account. Public robots/noindex remains unverified separately under that gate.
4. Independent read-only Neon UAT integrity checks: **2 existing manual payments, 2 receipt BYTEA current blobs, 2 preserved version-1 receipts; 2/2 original byte parity**. **No orphan/mismatched customer-order-store-tenant link, duplicate receipt version, invalid byte size/hash-length or missing backfill**. **8 receipt-history indexes**. PostgreSQL `product_media_assets.image_data` column exists; **zero product images** currently. Binary-storage round-trip and browser history workflow require UAT functional acceptance and should NOT be claimed PASS.
5. Neon UAT backup snapshot **snap-patient-dawn-arkxewpc** created pre-migration, restored independently into **br-spring-dream-arhxt1ji**, with 2/2 historical receipts compared; rehearsal migrations 0026+0027 passed before UAT update. This is same-provider snapshot proof, **not independent offsite backup nor guaranteed retention SLA**.

## Functional UAT acceptance — PENDING authorized browser tests

Use **https://uat.directpilot.ir** as the ONLY canonical acceptance address; old Vercel Preview feature domains are not production-like test targets. Log in to Vercel legitimately when redirected to SSO. Use only dummy/test data. Record PASS/FAIL and any screenshot errors.

- **[ ] Customer authentication**: UAT dummy user login, dashboard, refresh/session persistence, logout, denial when not authenticated; login CTA appears immediately (no blocking “بررسی حساب” spinner).
- **[ ] Admin authorization**: Admin login, payments page, filtering customer email/date, selection/preview of old and new receipt versions, audit timeline; a non-admin must get forbidden responses.
- **[ ] Four-month traceability**: Backend CI regression simulates 125 elapsed days and preserves both receipts across rejected re-upload, but browser UAT must still inspect an actual dummy payment history and older version after resubmission; do not approve real transfers.
- **[ ] Product media**: On UAT only, use a small synthetic JPEG through admin content studio, verify upload, private preview, redeploy/restart persistence and deletion; quota max 2 MiB/image and 50 MiB/store. No real Meta publishing.
- **[ ] Cross-module smoke**: Customer subscriptions, card display/copy, receipt upload and admin visibility, configured module gates, and login on mobile; do not change commercial pricing or active real customer plans.
- **[ ] Operational security**: Verify UAT browser cookies and front-end headers, no cross-tenant data, expected noindex once authenticated, backups and cost/usage before final UAT signoff.

## Final Production gate — NOT AUTHORIZED

Production `directpilot.ir` / `main` and Render source API/DB remain independent. The target Neon Production data have NOT been freshly synced. Never shut off Render or move Meta callbacks before explicit authorization, fresh independently restorable Production snapshot, writer and webhook freeze, final data migration/row counts/payment-value parity, recovery rehearsal, commercial Vercel plan-policy check, and documented GO/rollback. Vercel Hobby is not approved for commercial production use.

**Owner decisions to remember across all future chats:** keep canonical UAT on `uat.directpilot.ir`, all receipt versions and product images in PostgreSQL BYTEA (no R2/S3), receipt traceability by customer/order/payment for four months or longer, and maintain the five canonical files in order `AI_HANDOFF.md` -> `PROJECT_ROADMAP.md` -> `DECISIONS.md` -> `CURRENT_STATE.md` -> `NEXT_ACTIONS.md`.
