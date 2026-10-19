# DirectPilot TelBot — current UAT deployment guide

## 2026-10-19 — TelBot UAT repeated schema 503 diagnostic and endpoint guard

**Observed:** After Vercel environment update and redeploy `dpl_7NaicKji7PfacmDxUatz3qfNw7VZ` READY, owner still saw HTTP 503 `TelBot UAT schema unavailable`. Read-only Neon UAT `br-tiny-poetry-arz49v2o` shows `telbot.manager_inbound_updates`, migration `0002_webhook_auth`, and both runtime/owner have schema usage and marker SELECT; TelBot Neon production `br-fancy-feather-arydwgj7` has zero tables. This strongly suggests the Vercel **Sensitive** DB URI targets a different branch, but its actual hostname cannot be read with the connector; **root cause remains unverified until endpoint guard response**.

**Correction PR candidate:** isolated branch `fix/telbot-uat-db-branch-host-guard-20261019`, `api.py` now fails closed before psycopg connection unless the URI host matches `TELBOT_UAT_DB_HOST` or its UAT direct equivalent; rejects libpq `host`/`hostaddr` URL overrides. New offline `test_uat_connection_host.py` checks UAT pooled/direct PASS, non-UAT PROD DENY, malformed/missing configuration DENY. No DB migration, credentials, webhooks, production integrations or Telegram messages touched.

**Acceptance gate:** GitHub isolated CI SUCCESS, PR merge into TelBot isolated branch, matching Vercel READY + alias, then owner retry `/ready`. If `TelBot UAT database endpoint mismatch`, **update the Sensitive `TELBOT_UAT_DATABASE_URL` in Vercel to Neon project directpilot-telbot / branch uat / database telbot / temporary role telbot_owner**, redeploy and retry. Never paste secret; do not copy schema into production. If `Telegram manager not configured`, UAT DB/schema check PASS but overall readiness still HTTP 503. Otherwise diagnose role/schema separately. Manager Bot not configured and no live outbound permitted. Checklist and six canonical docs synchronized; previous historical records retained.

---


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
