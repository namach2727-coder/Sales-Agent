> **2026-10-26 TelBot UAT release blocker:** PR #89 native Telegram managed-creation deep link fix merged into isolated branch as `274fa3a70fe2c37428a55084af6d6466c044b39f` with 3/3 CI PASS. Vercel status for `directpilot-telbot-uat-api` returned FAILURE with `upgradeToPro=build-rate-limit` (team build rate limit), so **DO NOT report deployed**, ready, or UAT accepted. Existing UAT remains on preceding deployed commit until a verifiable successful deploy of exact SHA. Do not retry builds in a loop or change Production. Next: after build capacity is available, redeploy and verify exact GitHub commit status/alias; then owner opens Mini App and tests creation native Telegram link. Telegram Bot Management Mode and live managed bot creation remain unverified. Prior customer screenshot documented generic bot preview instead of creation prompt. No bot tokens exposed.


> **2026-10-25 / TELBOT STATUS UPDATE — current checkpoint**

## TelBot UAT — verified progress snapshot (2026-10-25)

- **Scope:** isolated `feature/telegram-managed-bots-spike-20261017` / `directpilot-telbot-uat-api`; no approval or release of Instagram DirectPilot Production, no Neon schema change, no bot-token rotation.
- **User-observed evidence:** Mini App launched via the `Open TelBot` button in `@DirectPilotManagerBot`; menu URL `https://directpilot-telbot-uat-api.vercel.app/telbot`. Identity endpoint returned `status: match` (getMe bot identity, not signed-login success).
- **Defects and resolutions:** blank/invalid login surfaced as `invalid_signature` (PR #76/#77). PR #78 diagnostic metadata caused HTTP 500 via missing standalone fallback import `safe_initdata_shape`; Vercel ASGI traceback at Oct 25 18:03:29 established root cause, PR #80 fixed; user later confirmed original 401 returned with `q1_c0_s1_u1_a1`.
- **Strong authentication evidence:** user-reported `Ed25519: valid` (PR #81); Telegram data is authentically signed for configured manager bot ID, but bot-token HMAC still fails. This does **not** authorize login. `chat_instance` absence in `q1_c0_s1_u1_a1` is not itself failure.
- **PR lineage (TelBot isolated branch, no Instagram Production promotion):** #76 `aa7f5139` safe auth error categories; #77 `da094da4` preserve signature detail; #78 `bb9c0ed8` safe envelope shape; #79 `53f80cbd` HTTP categorization; #80 `5cfb8f3c` Vercel fallback import hotfix; #81 `a22a1e86` independent Ed25519 diagnosis; #82 `7cf35fe3` safe HMAC mismatch categorization. All associated PR CI gates observed PASS before merging each.
- **PR #82 release status as checked:** 3/3 GitHub Actions PASS; merged to isolated TelBot branch at `7cf35fe37f5e5cb1775d145b5c8de32eb68f6438`; Vercel `directpilot-telbot-uat-api` status **PENDING** at documentation time: https://vercel.com/mohcenp-9857s-projects/directpilot-telbot-uat-api/3fYUjWZ3Loen3dtTVPEBtxTZYhNb . Do not claim UAT READY, auth PASS, or PROD deployed from CI/merge alone.
- **Next gates:** verify this exact SHA is READY on TelBot UAT domain; user launches fresh Mini App and supplies safe HMAC category (`token_whitespace`, `signature_field_included`, `key_or_payload_mismatch`, or `unavailable`). Then identify real bot-token revision vs HMAC input divergence; correct cause without bypassing HMAC. Require protected `/api/v1/me/tenants` HTTP 200, session/navigation and tenant flow PASS before further rollout.
- **Risks:** Vercel connector runtime logs and project details returned 403/404 despite visible GitHub-linked deployments. Owner supplied ASGI traceback; do not treat missing logs as clean. Do not expose `initData`, bot tokens, signature bytes, user IDs, or connection strings.

**Scope boundary:** This file governs Instagram DirectPilot manual card-transfer payment, not TelBot manager auth. The TelBot login investigation creates no payment-flow change or sign-off.

---

# DirectPilot — Manual Card-Transfer Payment Flow (Current)

**Updated:** 2026-10-15. **Canonical release status:** [docs/releases/RELEASE_REGISTER.md](docs/releases/RELEASE_REGISTER.md). **Original 2026-10-15 version preserved exactly:** [history/PAYMENT_FLOW.md](docs/runbooks/history/20261015_pre_release_register/PAYMENT_FLOW.md).

## Contract — customer

1. Registration/authentication via UAT `https://uat.directpilot.ir`; plan data **only** from Backend `GET /api/v1/plans` and `saas_plans`. Legacy `FREE` is inactive; `TRIAL` is not trial eligible; the two eligible specialized Trial plans last **3 days**. Only active, purchasable catalog rows can be bought.
2. Select a paid plan. For price `>0` and `duration_days=30`, choose **1..12** months; client sends `{plan_public_id, months}`. Backend stores **price and duration snapshot**, rejects invalid months and computes payable amount. See [UAT billing acceptance](docs/runbooks/uat_customer_billing_acceptance_20261015.md).
3. A manual-card-transfer order displays the **configured** card owner/number and clipboard copy action; showing the card does **not** transfer money automatically. Customer sends money externally and uploads JPEG/PNG/PDF receipt, with server-side file type, size, user/tenant/order and payment-state validation.
4. Backend stores current receipt `manual_payments.receipt_data BYTEA` + metadata and SHA-256. **In UAT after migration 0027** each re-upload also creates a preserved `manual_payment_receipt_versions` row with independently retrievable original bytes, version, customer, order, tenant and store links. The original is never overwritten in the version table.
5. Platform admin requires `payment.read` for image/PDF and history, `payment.manage` to approve/reject. Approval/rejection is audited. Approval grants entitlement based on order snapshot. The receipt is private; no general public media URL.
6. Admin UAT can search receipts by customer email and date range, compare versions and review action history. Four-month retention and off-provider restore **remain acceptance gates**, not guaranteed by schema alone.

## Environment distinction

| Item | Official UAT | Production |
|---|---|---|
| Frontend | `uat.directpilot.ir`, Branch UAT | `directpilot.ir`, Branch main |
| API/database | Vercel `directpilot-uat-api` + Neon `neondb`, Alembic 0027 | Render API/database remains source of truth |
| Card copy, initial receipt preview, multi-month checkout | Code present, automatic tests PASS; business/browser E2E PENDING | Source code present in actual deployed Frontend SHA; real production payment verification **not done in this documentation audit** |
| Historical versions and signed traceability | B#36/F#31 UAT code/DB deployed; 2/2 backfill PASS | **NOT DEPLOYED / NOT VERIFIED** |
| Images products | B#34: PostgreSQL BYTEA column, UAT tests pending | No Product media cutover |

**Never recommend R2/S3 without explicit Owner reversal.** Legacy on-disk fallback is a compatibility mechanism only while original files exist; it is not durable on serverless platforms.

**Physical receipt upload caveat:** configured max receipt file size (historically 5MiB) may exceed Vercel request body transport limits; test size and error handling before production release. **Never assume a browser-ready receipt preview proves successful file upload or long-term retention.**

**Evidence and acceptance:** [release register](docs/releases/RELEASE_REGISTER.md), [payment/customer runbook](docs/runbooks/uat_customer_billing_acceptance_20261015.md), [historical unmodified previous flow](docs/runbooks/history/20261015_pre_release_register/PAYMENT_FLOW.md).

**Hard stop:** no Production schema, customer money/receipt approval, account status, DNS, webhook, Render/Neon or Vercel Production deployment change without independently reviewed authorization and Production backup/cutover GO.
