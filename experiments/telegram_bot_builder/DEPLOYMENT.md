# DirectPilot TelBot UAT API packaging

- Source branch: `feature/telegram-managed-bots-spike-20261017`.
- Root directory: `experiments/telegram_bot_builder`.
- Entry: `api/index.py` via `vercel.json` to `api.py` (FastAPI).
- Project name: `directpilot-telbot-uat-api`; GitHub is connected; Branch Tracking is isolated to `feature/telegram-managed-bots-spike-20261017`. Never use `backend-main`.
- No real bot tokens or credentials are included.
- Production branch of the TelBot Neon project is untouched.

Required secure environment variables BEFORE a functional UAT:
`TELBOT_ENV=uat`, `TELBOT_UAT_DATABASE_URL` (limited SQL role, UAT branch only), `TELBOT_MANAGER_TOKEN` (owner-created BotFather Manager Bot token), `TELBOT_MANAGER_WEBHOOK_SECRET` (random string allowed by Telegram), `TELBOT_TOKEN_FERNET_KEY` (independent Fernet key, to be wired into manager token storage).
Do not use the old DirectPilot Instagram encryption key.

Without these variables, `/live` is intentionally public, `/ready` returns HTTP503, Mini App auth and Telegram webhook/manager operations reject requests, and no message can be sent.

Current UAT API: tenant-scoped read, draft and publish, idempotent manager and child webhook ingestion. Child bot onboarding via Telegram, token fetch/encrypted persistence and outbound delivery are NOT YET WIRED. These must be completed and tested before actual Telegram registration or live launch.

## 2026-10-18 — Verified UAT database guard and credential handoff

The independent Vercel project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` is a **TelBot UAT-only service**, even when Vercel calls its branch target `production`. Its source is `Sales-Agent/experiments/telegram_bot_builder`. Neon UAT is project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, database `telbot`, migration `0002_webhook_auth`. The TelBot Neon production branch and Instagram services must not be touched.

Current safe Vercel environment keys on this isolated project, in the deployment's `production` target:
- `TELBOT_ENV=uat` — present, non-secret.
- `TELBOT_UAT_DB_HOST` — present, UAT-only Neon branch hostname, non-secret.
- `TELBOT_UAT_DATABASE_URL` — NOT configured; requires the dedicated `telbot_ua_runtime` login (never use `telbot_owner`).
- `TELBOT_MANAGER_TOKEN` — NOT configured; owner must create a dedicated Manager Bot through official BotFather.
- `TELBOT_MANAGER_WEBHOOK_SECRET` — NOT configured; generate a random valid secret and enter directly into Vercel/provider UI.
- `TELBOT_TOKEN_FERNET_KEY` — NOT configured; generate an independent Fernet key and enter directly into Vercel. It must not be the Instagram key.

The runtime role `telbot_ua_runtime` currently has **no password**. A privileged Neon reset-password API call for the role failed with `422 cannot update password for role without password`. The safe provisioning route is for the owner to log into **Neon UAT only** using their secure local PostgreSQL client as an authorized administrator and run `\\password telbot_ua_runtime` in `psql`; this uses a local password prompt and avoids putting the new password in SQL history. Then construct a URL for the UAT branch, role and database, with `sslmode=require`, and paste it **directly into Vercel's Sensitive environment variable**, not GitHub/chat. Confirm Neon branch host equals `TELBOT_UAT_DB_HOST`. Do not use the Neon production endpoint or shared superuser URL.

The guarded API checks the environment name, host, nonempty password, `telbot` DB, `telbot_ua_runtime` role and TLS **before** opening a connection, then validates database/role identity. No credentials are ever returned by endpoints. Without full configuration, `/ready` intentionally fails closed with 503 and no sending is enabled.

**Owner-controlled remaining work:** BotFather Manager Bot creation and enabling bot management; secret provisioning through approved provider UI; real Telegram webhook delivery/ownership and encrypted child token retrieval remain a distinct release gate. Do not claim a READY Vercel build equals Telegram operational acceptance.
