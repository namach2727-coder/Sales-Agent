# DirectPilot TelBot — current UAT deployment guide

**Last verified 2026-10-19.** Independent Vercel project `directpilot-telbot-uat-api`; Git connected to `feature/telegram-managed-bots-spike-20261017`; Root Directory `experiments/telegram_bot_builder`; framework `fastapi`. Native root `app.py` exports the FastAPI app from `api.py`. PR #66 removed obsolete catch-all rewrite to `/api/index.py`, which previously masked `/live` with a 404.

PRs #64 dependencies, #66 routing, #67 temporary UAT owner database acceptance MERGED. Source `bd20c44a883a4de3f57ca2f9d009b8d981519c18`; [Vercel deployment](https://vercel.com/mohcenp-9857s-projects/directpilot-telbot-uat-api/DYjA434LnV79oYHDnXSHW36dXAL6) READY and alias `https://directpilot-telbot-uat-api.vercel.app` verified.

## Secrets and data access
- UAT Neon project `curly-cell-93038441`, UAT branch `br-tiny-poetry-arz49v2o`, DB `telbot`. SSL required; pooled connection appropriate for serverless, direct for migrations.
- Vercel env keys present: `TELBOT_ENV=uat`, Sensitive `TELBOT_UAT_DATABASE_URL`, `TELBOT_UAT_DB_HOST`. Presence does **not** validate connection.
- Code temporarily accepts `telbot_owner` in UAT with environment, database and UAT marker guards; this role has elevated CREATEDB/CREATEROLE and must be replaced by least-privileged `telbot_ua_runtime` before real customers.
- Missing as last inventoried: `TELBOT_MANAGER_TOKEN`, `TELBOT_MANAGER_WEBHOOK_SECRET`, `TELBOT_TOKEN_FERNET_KEY`. Manager Bot owner must set these securely, never paste them in chat/Git.

## Acceptance diagnostics
- `/live` previously owner tested PASS with expected JSON after PR #66.
- `/ready` has **not** been retested since #67; `TelBot UAT database unavailable` means DB failing; `Telegram manager not configured` means DB/schema checks succeeded but Manager secrets missing. Neither is HTTP 200.
- `/` returning 404 is not by itself a health failure. Build READY != database ready or Telegram end-to-end ready.

See [Master Checklist](../../docs/telegram_bot_builder/TELBOT_RELEASE_CHECKLIST.md); no Production Instagram or TelBot Neon Production changes authorized.
