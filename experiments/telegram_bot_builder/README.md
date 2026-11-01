## 2026-11-01 — CURRENT: synthetic service-sales prototype #119 LIVE in isolated UAT

PR https://github.com/namach2727-coder/Sales-Agent/pull/119 reviewed head 1f3a2a44f5af8fdee4a653a7463a71fa44db99c5 passed all 11 checks. Squash merge b18514a08e55d5c2c330eaebe263d3a7bfd83502 ONLY into feature/telegram-managed-bots-spike-20261017 has identical reviewed tree dc88b555f4ff01de6336976479234ea235ccba70. Automatic deployment dpl_45WCEywF5XqqdJVQhFcXahbNyrVv is READY on the exact merge and owns canonical https://directpilot-telbot-uat-api.vercel.app. This is the isolated TelBot UAT project; business Production was not promoted.

Verified release: /ready 200, database available, migration current; /telbot and both assets 200 and byte-identical to reviewed source, cache revision 20261101-service-flow-preview-1. New service-flow-preview POST with synthetic IDs and no authentication returns 401 missing_init_data. Read-only Neon UAT metadata: 1 active bot, 0 paused, published version 6. No schema migration, customer configuration/status change, secret retrieval, external API flag change, actual provider/payment/account or Telegram send performed for this release. Ordinary replies remain enabled; external API calls remain disabled.

CI unit job 124781995713: 150 discovered, 145 PASS + 5 PostgreSQL skips; schema job 124781995908: all 5 PASS including real UI/FastAPI/PostgreSQL sample with editor identity/focus and existing configuration counts preserved. Both DOM/editor and seven Save scenarios PASS. Initial schema fixture focus expectation was corrected after report Close deliberately focused its opener; the final reviewed head passed. Native owner phone acceptance remains PENDING.

Owner/editor can open «نمونهٔ فروش و تحویل سرویس» and explicitly run paid, unconfirmed, amount-mismatch or lost-response scenarios. Fixed fictional prices, inert checkout text and invalid DEMO account/config; simulation=true, live_actions=false. Engine is IN-MEMORY and customer Telegram runtime is NOT connected to it. This release does not deliver actual VPN/payment/checkout accounts, a generic workflow designer, or durable cross-restart idempotency. No AI is implemented. Owner chose a synthetic engine/sample because no panel exists yet; private reference-bot behavior and latency remain unverified.

NEXT: implement versioned mobile no-code steps and durable scoped orders/runs/operation ledger with encrypted sensitive data; then integrate actual documented panel and verified payment adapters with reconciliation, and private Telegram delivery. Real sandbox acceptance requires the eventual panel/gateway contract. See docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md for gates. Do not wire this prototype to live commerce as-is.

---

## 2026-11-01 — CURRENT: owner directs transactional service bot builder; synthetic prototype (release pending)

Owner clarified target: a no-code bot capable of server-connected service sales, checkout, verified payment, account creation and configuration delivery, using a VPN seller as an example. Current TelBot has NO AI. Private behavior/source/latency of @sadshekanvpnbot was not observed; only public profile plus owner description are evidence. Owner answered that NO real panel is available and selected engine + synthetic sample now, real connection later. Do not substitute more keyword-only polish for this direction and do not claim real provisioning/payment integration is complete.

Implemented first pure ServiceFlow state machine and UAT owner/editor-only «نمونهٔ فروش و تحویل سرویس» preview: select fixed synthetic plan -> frozen order amount/currency -> synthetic checkout -> trusted-adapter payment check bound to order/reference/amount/currency -> provisioning instruction -> mock username/password/config delivery. Four cases: paid, unconfirmed, mismatched amount, unknown provisioning outcome. All demo links are inert text; all accounts/configs are clearly unusable DEMO data. Preview does membership/bot reads only; no DB writes, real HTTP/provider/vault/Telegram operation even with outbound flags ON. Existing child-bot runtime is NOT wired to this engine.

Core separates customer actions from trusted external receipts, suppresses repeated callbacks/customer taps within a run, produces scope/run-bound operation/idempotency IDs, rejects invalid prices/foreign operations/payment mismatches, redacts account repr/error details, and stops unknown outcomes without blind retry. This is IN-MEMORY prototype behavior, NOT durable cross-restart idempotency. Live use still requires persistent version-pinned workflow/order/operation storage, encrypted result handling, real verified gateway + panel adapters with idempotency/reconciliation contracts, no-code scenario authoring and customer-chat renderers. No financial amount/latency/commercial readiness claim.

Local Python: 150 discovered, 145 PASS + 5 disposable PostgreSQL skips. Actual DOM paid/unconfirmed/mismatch/timeout, inert links/plain text, duplicate run and close-race tests plus existing editor/report/control/search/copy and seven Save scenarios PASS. Updated CI real UI/HTTP/PostgreSQL case opens/runs the synthetic sample while preserving reply editor and configuration version counts. New pure/API tests cover payment gate, scope/amount/currency/reference, duplicate operations, unknown outcomes, no live effects, auth and secret-redacted validation. CI/PR/merge/deployment/owner phone acceptance PENDING. No schema, customer setting/status, external flag, real order/payment/account/provider/send or Production change. Runbook docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md.

---

# Telegram No-Code Bot Builder — isolated technical spike
> **Current checkpoint — 2026-10-19:** This README preserves historic prototype notes. Dedicated Neon UAT schema and Vercel FastAPI deployment now exist (PRs #64/#66/#67, READY at `bd20c44a`). `/live` user PASS; post-#67 `/ready` and Manager Bot still PENDING; no live child bot, Telegram send or Mini App. See [Master Checklist](../../docs/telegram_bot_builder/TELBOT_RELEASE_CHECKLIST.md) and [Deployment](DEPLOYMENT.md).


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

## 2026-10-17 — T1 API/security implementation checkpoint

**UAT ONLY:** Independent FastAPI core in `api.py` with Telegram Mini App `initData` HMAC authentication (`auth.py`), per-tenant role checks, bot/config endpoints, draft/publish versioning, two authenticated webhook receivers (Manager Bot and child bot) with deduplication. `vault.py` implements standalone Fernet token encryption/decryption; it has NOT been wired to live Telegram `getManagedBotToken` or DB storage. Child/manager webhook processing currently acknowledges and stores update IDs; live sending and automated registration are NOT implemented.

**UAT DB schema:** migration `0002_webhook_auth.sql` applied successfully to `curly-cell-93038441` / `br-tiny-poetry-arz49v2o` / `telbot`. Fourteen tables (12 original business tables + ledger + new Manager webhook receipt). No tenant/bot/token/inbound records. Rollback-only SQL `0002_webhook_auth_uat_smoke_rollback.sql` PASS, manager update duplicate rejected, after-test count zero. Production TelBot unchanged with zero tables.

**Neon runtime identity security:** API-created `telbot_uat_api` role was too privileged (Neon API auto neon_superuser), removed. SQL-created `telbot_ua_runtime` has `NO[BYPASSRLS|CREATEDB|CREATEROLE|SUPERUSER]`, SELECT/INSERT/UPDATE but no DELETE, no migration-ledger write permission. Password is NULL (login not usable); no DB URL/secret shared or committed. API module's connection checks require this runtime user, database `telbot`, UAT table.

**CI:** 29/29 offline unit tests PASS ([GitHub Actions 39036439669](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39036439669)). Vercel UAT packaging prepared (`api/index.py`, `vercel.json`, `requirements.txt`, `DEPLOYMENT.md`) and not deployed. Attempted new independent `directpilot-telbot-uat-api` project creation via Vercel connector returned HTTP 403 permission denied. Manual owner creation or Vercel project-create grant required before UAT deploy; no existing service modified.

**Next gates:** owner creates standalone Telegram Manager Bot via @BotFather with bot-management enabled and configures its secret safely; complete managed-bot ownership validation and encrypted credential persistence, non-owner UAT role password bootstrap (without disclosure), UAT deploy, live webhook tests, Mini App UI, RLS/backup, no Production change.
 
## 2026-10-18 — UAT-only managed-bot enrollment checkpoint

This update extends the isolated T1 code with a **tenant-owner-only** management request endpoint and owner-verified webhook reconciliation:

- `POST /api/v1/tenants/{tenant_id}/managed-bot-requests`: Telegram Mini App signed `initData` + verified active tenant owner required. Returns a 15-minute server-side request and Telegram keyboard markup with **delivery_status=not_sent** (the API does NOT message Telegram).
- Locks the Telegram owner in the DB transaction and disallows ambiguous active requests across tenants.
- Manager webhook checks its configured shared secret and update-ID deduplication, then links a Telegram-managed child bot **only when one unexpired authorized owner request exists**; stores the bot in **pending** with **no token**. Ambiguous, absent or uninvited events are durable but ignored.
- Existing `telbot_ua_runtime` restricted DB identity and schema `0002` remain unchanged. There are **no new migrations, DB writes to Neon or live Bot API calls** from this patch.

Important implementation limit: Telegram's `managed_bot` update provides owner/bot IDs but does **not** provide the creation request_id. Correlation therefore requires a single unexpired pending request per owner across tenants. The webhook cannot by itself prove a user approved an action without secret validation.

**Next release gates:** BotFather Manager Bot with management enabled, dedicated UAT project/configuration/secrets and limited runtime role login, actual Telegram keyboard delivery and ownership confirmation, server-side `getManagedBotToken` encryption and safe rotation, child webhook registration, reply worker/queue, Mini App form, tenant isolation/E2E tests. Keep public purchase, commercial activation, AI and Production disabled pending acceptance.
