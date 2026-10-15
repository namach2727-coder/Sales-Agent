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
