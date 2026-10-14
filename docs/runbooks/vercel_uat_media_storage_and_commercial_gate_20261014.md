# DirectPilot — Vercel UAT Auth Acceptance and Media / Commercial Gates (2026-10-14)

## Verified or operator-confirmed
- Vercel UAT API project `directpilot-uat-api`, latest observed API deployment `dpl_EdLHatmBs6GKyDeiMaAWFyCfpmmR`, READY; frontend isolated preview `dpl_CEnKE8Fh98HpnsPfsFwMz7yzhnzY`, READY. Both independent of the live Render services.
- The owner reported browser PASS for UAT customer login, session persistence after refresh, navigation, logout, unauthenticated-route protection, admin login, admin payment listing and viewing existing receipts in the isolated preview. This is **operator-reported manual UAT**, not a captured automated E2E test.
- `/ready` response reported by owner: `{"status":"ready","database":"available","migration":"current"}`. Direct read-only Neon UAT verification: database `neondb`, migration `0025_trial_three_days`, 82 tables.
- Neon UAT direct read-only SQL: 2 manual payment rows; 2 receipt records with `receipt_storage_key` and binary `receipt_data`, 0 legacy file-only receipts, 0 `product_media_assets` rows. Code `CommerceService.submit_receipt` writes new receipts into PostgreSQL and admin receipt endpoint reads `receipt_data` first. **New upload E2E, limits and cold-start retest are still OPEN**.

## Functional blocker: product images
- `app/media_storage.py` currently saves uploaded manager JPEGs to `MEDIA_STORAGE_ROOT` on a local filesystem and public signed `/media/publish/{asset_id}` uses `FileResponse` from the same filesystem.
- Vercel Functions' filesystem is read-only except temporary `/tmp` (up to 500 MB); temporary writes do not provide cross-deployment or cross-instance durable media. Current 0 UAT product media records means no assets need migrating there, **not** that upload is accepted.
- Backend currently permits up to 8 MiB decoded JPEG encoded in a JSON/base64 data URL, while Vercel Functions' request payload cap is 4.5 MB. Existing media uploads can fail before entering the API handler. Avoid hiding/truncating failures.
- Requires approved persistent object storage, preferably private S3-compatible bucket (e.g., Cloudflare R2 Standard after account/billing activation) with scoped credentials, tenant namespacing, integrity metadata, signed public link logic, safe deletion, lifecycle and backup. No bucket, credentials, deployment, production media cutover or cost commitment has occurred.
- Do NOT store potentially large growing product media inside Neon Free 1 GiB PostgreSQL without capacity decision and retention/size quota, and do not enable uploads into ephemeral disk as a substitute for object storage.

## Commercial/hosting blocker
- Vercel official Hobby plan policy restricts Hobby to non-commercial personal use (as documented in 2026). The current UAT experiment validates technical feasibility only; **it does not authorize paid/customer-facing Production service on Hobby**.
- Options before Production: suitable paid commercial Vercel tier with explicit operating budget, or a commercially suitable Docker backend host (including vetted Always Free where actually available and terms permit). Review Neon compute/storage quota under representative traffic, background workers and Meta callbacks independently.
- Cloudflare R2 Standard free tier currently 10 GB-month, 1M Class A, 10M Class B monthly, but requires R2 subscription/checkout; overages may be billed. Treat it as a candidate, not an active configured provider.
- Official source pages: https://vercel.com/docs/plans/hobby , https://vercel.com/docs/functions/limitations , https://vercel.com/docs/functions/runtimes , https://developers.cloudflare.com/r2/pricing/ , https://developers.cloudflare.com/r2/get-started/

## Required next acceptance tests / exit gates
1. Non-destructive UAT admin RBAC denial for non-admin where safe; distinguish user-observed PASS from logged HTTP evidence.
2. Isolated non-payable UAT test of submitting a **dummy** receipt, reviewing it with admin and viewing after a fresh deployment/cold instance; never approve a real transaction or contact Meta.
3. Review in UAT only: image object-storage adapter implementation, 4.5 MB request limit, upload validation, signed media link and expiry, deletion, auth/tenant isolation, cost/quota and observability. Configure only after provider and secret approval.
4. Validate safe and durable Meta webhook delivery/ack/replay and Payexa callback idempotency without real customer messages/payments, including serverless timeout and scheduled/long-running task requirements.
5. Independently qualify a commercially permitted hosting plan with persistent media, reliability, DR and budget; decide Vercel vs portable Docker host.
6. **Production hard stop:** current Render source remains authoritative. No automatic production DB switch, backup overwrite, final sync claim, DNS/Meta callback change or Render retirement before fresh consistent source export under proven writer/event freeze, encrypted restorable offsite backup, whole-table/business parity, reversibility and separate owner GO. Preserve Render through acceptance.

## Evidence boundaries
- Source: backend migration branch `migration/vercel-uat-fastapi-20261014`, and front-end branch-scoped preview `uat/vercel-api-isolated-preview-20261014`.
- `READY` is a deployment state, not proof of end-to-end business functionality or production suitability.
- Secrets, personal financial data and actual receipt bytes are excluded from this runbook.
