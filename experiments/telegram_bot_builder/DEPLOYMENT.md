# DirectPilot TelBot UAT API packaging

- Source branch: `feature/telegram-managed-bots-spike-20261017`.
- Root directory: `experiments/telegram_bot_builder`.
- Entry: `api/index.py` via `vercel.json` to `api.py` (FastAPI).
- Project name: `directpilot-telbot-uat-api`; keep Git integration disabled to avoid auto-deploying the Instagram Production branch.
- No real bot tokens or credentials are included.
- Production branch of the TelBot Neon project is untouched.

Required secure environment variables BEFORE a functional UAT:
`TELBOT_ENV=uat`, `TELBOT_UAT_DATABASE_URL` (limited SQL role, UAT branch only), `TELBOT_MANAGER_TOKEN` (owner-created BotFather Manager Bot token), `TELBOT_MANAGER_WEBHOOK_SECRET` (random string allowed by Telegram), `TELBOT_TOKEN_FERNET_KEY` (independent Fernet key, to be wired into manager token storage).
Do not use the old DirectPilot Instagram encryption key.

Without these variables, `/live` is intentionally public, `/ready` returns HTTP503, Mini App auth and Telegram webhook/manager operations reject requests, and no message can be sent.

Current UAT API: tenant-scoped read, draft and publish, idempotent manager and child webhook ingestion. Child bot onboarding via Telegram, token fetch/encrypted persistence and outbound delivery are NOT YET WIRED. These must be completed and tested before actual Telegram registration or live launch.
