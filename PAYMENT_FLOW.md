> **2026-10-26 — TELBOT MANAGED CREDENTIAL PREPARATION (UAT-only, new PR, release pending)**
>
> **Prior milestone:** PR #86 merged `e00f61034fe05577125603f737aa886f84ad6f80` after 3/3 CI PASS. Vercel TelBot UAT deployment check SUCCESS. Owner has previously verified login and workspace creation, but has **NOT** yet user-tested new managed bot creation. No Production TelBot or Instagram release approved.
>
> **New implementation:** After owner confirms a Telegram Managed Bot using official deep link, existing manager webhook stores a tenant-bound pending record. On subsequently loading the UAT Mini App bot list, the owner session triggers backend-only `POST /api/v1/tenants/{tenant_id}/bots/{bot_id}/prepare-managed-credential`. Endpoint enforces Mini App HMAC, tenant owner role, exact bot/tenant/Telegram owner ID, `managed_request_id` presence, `pending` status, dedicated Fernet key availability and row lock. Calls Telegram Bot API `getManagedBotToken(user_id=<managed bot id>)` over server-side HTTPS, checks returned token bot ID, encrypts it using `TELBOT_TOKEN_FERNET_KEY`, persists ciphertext, never returns the token, and is idempotent on stored credentials. The user does not enter BotFather token. This phase **does not register webhooks, send messages or activate bot**.
>
> **Safety/acceptance:** Offline mocked tests for token API identity, failure sanitization, owner/tenant isolation and encrypted idempotent storage; do not log raw credentials. New PR's CI, merge SHA, Vercel deployed SHA, Bot Management Mode eligibility, real managed creation, Telegram token fetch, persistent tenant row and user UAT acceptance are **PENDING** unless confirmed by release evidence. Failed retrieval remains `pending` and is retried on future UAT page load (not looped indefinitely). Follow-up milestone: child webhook configuration and staged activation only after explicit acceptance. Support-only legacy manual token endpoint is not in customer UI. Historical evidence preserved.

> **2026-10-25 — TELBOT MANAGED-BOT SELF-SERVICE IMPLEMENTATION (PR #86, UAT-only; verify CI/deployment before accepting)**
>
> **Owner decision:** Customers must NOT use BotFather to copy/paste an API token. Primary onboarding is official Telegram managed-bot creation via `https://t.me/newbot/DirectPilotManagerBot/<suggested_username>?name=<URL-encoded name>`, after owner creates a TelBot workspace. Telegram requires user confirmation; automated creation without consent is not supported. Official references: https://core.telegram.org/api/bots/managed-bots and https://core.telegram.org/bots/features#managed-bots.
>
> **PR #86 scope:** UAT Mini App now collects display name and bot username, POSTs to existing owner-only `/api/v1/tenants/{tenant_id}/managed-bot-requests`, receives a short-lived request and a safe creation URL, and shows explicit Telegram confirmation link. No customer API token input or frontend credential persistence. Existing manager webhook's `managed_bot` event logic links the new bot to the matching sole unexpired request as `pending`. Legacy manual token endpoint is retained strictly as backend support fallback, not exposed in customer UI. Existing 15-minute TTL / per-owner uniqueness / tenant ownership / webhook signature / dedupe guard remain.
>
> **Important capability boundary:** A successful Telegram managed-bot creation event stores identity and pending bot record. Automatic `getManagedBotToken` retrieval and secure background management are NOT implemented or accepted by this UI change; production rollout and messaging/webhooks remain blocked pending service credential handling, tests, and owner approval. Manager Bot Management Mode must be enabled in BotFather and validated live.
>
> **Evidence and rollout gates:** PR #84 HMAC sign-in fix previously deployed UAT and owner reported Mini App opening and workspace creation PASS. PR #86 code committed on `feature/telbot-managed-bot-self-service-20261025`; CI/merge/deployment/live managed creation = PENDING until separately verified. Next: CI; merge into isolated TelBot UAT branch; confirm Vercel deploy SHA; user tests Telegram official confirmation; confirm pending bot row and tenant isolation; implement safe token retrieval/activation separately. Do not mark Instagram Production deployed. Preserve earlier PR #76–#85 history and release states.

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
