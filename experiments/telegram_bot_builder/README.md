# Telegram No-Code Bot Builder — isolated technical spike

**Development branch only**: `feature/telegram-managed-bots-spike-20261017`.
This is a new product track; no DirectPilot Production route, environment variable, migration, secret, Vercel project, Neon project, or customer data is changed.

## What is implemented

- Pure builder helper for `KeyboardButton.request_managed_bot` with user-confirmed bot creation.
- Parsing both `managed_bot` and `message.managed_bot_created` updates without exposing credentials.
- Fail-closed verification of the webhook secret header.
- Deterministic keyword reply engine with Persian Arabic-ya/kaf normalization and per-tenant configuration object.
- Offline unit tests.

Run from repository root:

```bash
python -m unittest discover -s experiments/telegram_bot_builder -p 'test_*.py' -v
```

## NOT implemented (not production ready)

No Manager Bot created or connected, no Telegram credentials, no database schema, no tenant authorization route, no webhook endpoint, no deployed bot runtime, no encrypted vault, no deduplication storage, no Mini App UI, no owner handover, no live Telegram send, no analytics, no AI, and no commercial payments.

The `managed_bot` event MUST be authenticated and deduplicated; the server MUST verify its Telegram owner against its authenticated application tenant before recording the bot. The Bot API token should only be fetched server-side via `getManagedBotToken`, encrypted at rest, never returned to browser or logs. Bot owner remains the Telegram user who confirms creation. Fetching any token is **not** done by this prototype.

See `docs/telegram_bot_builder/MVP_BLUEPRINT.md` for the scoped plan.

## 2026-10-17 — Product name and database boundary for DirectPilot TelBot

**Official name (owner):** DirectPilot TelBot / دایرکت‌پایلوت تل‌بات.

**Database — current:** none. The isolated Telegram spike has no persistence. **Proposed:** create a NEW Neon PostgreSQL project named `directpilot-telbot`, not the Instagram DirectPilot Production project. Give TelBot UAT a distinct branch/database and TelBot Production its own production branch/database, with separate credentials per environment. Make production data inaccessible from UAT by default. Use a distinct TelBot Vercel backend and Mini App project. Keep bot tokens encrypted in TelBot database with encryption key outside Neon in secure Vercel environment variables; avoid plaintext token exposure. Implement tenant-level ownership, unique `(bot_id, update_id)` ingestion, backups and restore validation before any real customer data. **Not provisioned or deployed yet.**

## 2026-10-17 — DirectPilot TelBot Neon provisioned and verified

**LIVE INFRA (owner approved "بسازیم"; this supersedes prior NOT CREATED plan):** Created independent Neon project `directpilot-telbot` in owner org `org-dawn-firefly-87600084` on **Free** plan; project ID `curly-cell-93038441`, region `aws-us-west-2`, PostgreSQL **18.6**, primary branch `production` ID `br-fancy-feather-arydwgj7`, UAT branch `uat` ID `br-tiny-poetry-arz49v2o` (child of empty production). **Both branches contain a database named `telbot`**, isolated at Neon branch level, with database role `telbot_owner`. **Read-only SQL on each branch confirmed database `telbot`, correct PostgreSQL version and `0` public tables.** Owner link: https://console.neon.tech/app/projects/curly-cell-93038441 . The UAT branch is the ONLY intended development database; no Telegram schema, tenant, token, migration, data or bot activity was created. Mainline DirectPilot/Instagram Neon project `billowing-poetry-05589994` and its Production DB `directpilot_live` remain unchanged. Vercel TelBot API/Mini App not provisioned. No connection string, password or API key copied to chat or committed to repository.

**Guardrails:** Branches are not marked protected (Neon Free account); do not assume isolated database credentials just from separate branch names. Before deploying UAT generate/rotate dedicated branch credentials and configure scoped Vercel UAT environment securely; never commit URLs/passwords. Set up backups and a migration framework before creating commercial customer data. Cost: Neon Free plan confirmed by organization inspection; project compute resource defaults are managed by Neon. Meta migration remains paused.

## 2026-10-17 — DirectPilot TelBot T1 database foundation deployed to Neon UAT

**Authorized implementation result:** Versioned additive migration `0001_telbot_foundation` committed in isolated GitHub branch `feature/telegram-managed-bots-spike-20261017`, path `experiments/telegram_bot_builder/migrations/0001_telbot_foundation.sql`, source commit `899a5df77c826056b291f64ae09f677d18dd8d34`. Executed as a **single atomic Neon SQL transaction only on UAT**: project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, PostgreSQL DB `telbot`. **UAT deployment/SQL verification PASS:** schema `telbot`, 13 tables, 18 foreign-key constraints, 39 check constraints, 33 indexes, migration version record `0001_telbot_foundation`. Zero records in all 12 functional/business tables; migration ledger has 1 record. Database content covers tenant/user roles, Managed Bot creation request, bot ownership and encrypted-token ciphertext slots, publishable config versions, menu buttons, keyword rules, FAQs, chat sessions, idempotent inbound updates, outbound deliveries and tenant-scoped audit events. Composite tenant FKs block ordinary cross-tenant FK associations; this is schema-level segregation, NOT yet verified RLS or API authz.

**Database live integrity smoke:** rollback-only SQL `experiments/telegram_bot_builder/migrations/0001_telbot_uat_smoke_rollback.sql` executed on UAT and PASS; expected constraint rejects for duplicate `(bot_id,telegram_update_id)`, second published configuration, mismatched tenant references, cross-tenant owner and active bot without encrypted credential. The intentional rollback restored UAT to empty business tables. Offline branch CI [workflow 39035278379](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39035278379) **13/13 tests PASS** (8 original primitives + 5 schema-contract checks). No real Telegram API/network calls.

**Production untouched:** TelBot production branch `br-fancy-feather-arydwgj7` remains **0 tables**; DirectPilot Instagram Production DB `directpilot_live`, Vercel apps and Render services were not modified. No TelBot API deployment, live Telegram bot, webhook, Mini App, vault encryption implementation, RLS/role separation or data migrations to Production exist yet. Next implementation gate: develop isolated TelBot UAT backend API and service-layer tenant authorization with dedicated, non-owner application DB role/credentials, webhook idempotency workflow, and safe token encryption; no Production deploy without owner acceptance. Do not paste real DB connection URLs/Telegram tokens in GitHub or chat.
