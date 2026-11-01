## 2026-11-01 — CURRENT: own portfolio/inquiry bot LIVE; website source merged, publish QUOTA BLOCKED

Owner replaces the public universal/no-code bot-builder with OUR OWN DirectPilot Bot Studio: curated business ideas, explicit demos, custom-development inquiries and owner follow-up. Generic workflow/payment/panel development is deferred; historical code/configurations remain preserved. Existing owner test bot https://t.me/tetsteee1bot is repurposed as our showcase, not newly created or renamed in BotFather. Native profile/username branding and actual phone/Telegram notification acceptance remain PENDING.

Backend PR #127 https://github.com/namach2727-coder/Sales-Agent/pull/127: reviewed 88ae302e8e04ab39627896742e492063a1a9b6cb, all 11 checks SUCCESS; squash merge 9e82353fddfebfa7161fba6905a25bf306d7117c only isolated TelBot branch; reviewed/merged trees match. Automatic UAT deployment dpl_CEqktcsxdKDa63uceerNpysYgnTi READY at exact merge. Additive 0004_showcase_inquiries applied only Neon curly-cell-93038441 / br-tiny-poetry-arz49v2o / telbot after real PostgreSQL CI. One explicitly enabled registered-owner bot; TELBOT_SHOWCASE_ENABLED=true only isolated UAT production target. Existing replies ON, external API actions OFF; 1 active bot and published v6 preserved. Latest confirmed inquiries count 0; no synthetic request or real customer content inserted into UAT by testing.

Verified /ready 200 database available/migration current; /showcase, its JS/CSS and manager Mini App HTML/JS 200 and byte-exact source. Public catalog 200 with 24 categories and actual bot link; unauthenticated private inbox 401 missing_init_data. Cloud browser visually verified desktop portfolio, search input focus/results, modal simulated selection and category-specific Telegram link. Telegram's public page was unavailable from cloud browser; this does NOT establish bot failure or live Telegram delivery. Physical mobile/native acceptance remains separate. Local 157 Python discovered = 151 PASS + 6 PostgreSQL skips; dedicated CI ran the 6 PostgreSQL cases PASS, including migration, persistent inquiry flow, duplicate suppression, encrypted records, unknown notification outcome and owner-only inbox. DOM/editor/Save/showcase tests PASS.

Website PR #73 https://github.com/namach2727-coder/directpilot-web/pull/73: reviewed 663378bee2d0e5d417f3becccfb79d254e125996, both validate/verify SUCCESS; squash merge 957d4c46fd448b40e97e8b89094c30792c79ea19 to website main, identical reviewed tree. 287 tests, TypeScript, full lint (3 existing warnings) and production build PASS. Includes minimal pre-existing SEO loading-effect lint fix to permit CI; no auth/API redesign. New /telbot custom service, 24 category links, homepage/subnav and neutral former checkout; historical proposed tiers no longer shown. Publication request rejected HTTP 402 api-deployments-free-per-day (more than 100; retryAfter 86400). NO new website deployment created. directpilot.ir remains prior READY 4451e50916b5c58ba0b55b303362ff37fd04227e / dpl_J8Ux4SBhPWctAvZZ5ShQJzpP2BB9. Do NOT claim new website links live. No CLI quota workaround, hosting/audience change, billing upgrade or repeated retry planned.

NEXT: owner can inspect live https://directpilot-telbot-uat-api.vercel.app/showcase and test /start + category/demo/need/contact/review/Confirm in existing bot; check saved code, owner notification and private inbox. Finalize professional BotFather branding separately. When Vercel quota permits, deploy exact reviewed website merge ONCE to existing directpilot-web, verify canonical /telbot and bot links, then record deployment; no new retry automation created. Business backend Production, payments and Instagram runtime unchanged. Full runbook: docs/telegram_bot_builder/OWN_SHOWCASE_BOT_20261101.md. This checkpoint supersedes the generic builder/transaction engine next steps below without deleting history.

---

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

# Telegram No-Code AI Bot Builder — independent product track

## 2026-10-20 — Manual BotFather onboarding PR #72 MERGED, separate TelBot UAT DEPLOYED

**DECISION:** Bot Management Mode was unavailable on the owner-side BotFather UI, and a locally run official Telegram getMe test for @MhnPdr_bot yielded `can_manage_bots=false`. Proceed with manual BotFather token connection instead of blocking product on managed-bot creation. Existing managed-bot flow remains behind its current unfinished gate.

**Verified source/release:** [PR #72](https://github.com/namach2727-coder/Sales-Agent/pull/72) merged into `feature/telegram-managed-bots-spike-20261017` (merge SHA `557b602f862f42ffedae12e4b6d403387c88ac37`). Latest PR isolated Telegram bot-builder CI **SUCCESS**, general CI **SUCCESS** (pytest, Docker build, Neon/Postgres checks). Independent TelBot UAT Vercel project ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` explicitly deployed that merge SHA to the project's `production` target, deployment `dpl_7rNivsQFDgi5bdLbVrybDGfzC9Uk` **READY**, official alias `directpilot-telbot-uat-api.vercel.app` VERIFIED pointing to the same deployment. This is NOT Instagram Production, not TelBot Neon Production.

**Implemented UAT-only:** mobile Persian RTL Mini App at `https://directpilot-telbot-uat-api.vercel.app/telbot` with CSP and no-store; signed Telegram initData auth; explicit one-tenant-per-Telegram-user account bootstrap (`GET/POST /api/v1/me/tenants`); owner-only `POST /api/v1/tenants/{tenant_id}/bots/connect-manual` accepts a BotFather bot token via HTTPS request body, validates its identity via getMe, Fernet encrypts with dedicated Sensitive `TELBOT_TOKEN_FERNET_KEY` (presence CONFIRMED in Vercel UAT), persists credential as `pending` and emits audit event. Globally unique Telegram bot ID, tenant membership checks and fail-closed missing key. Mocked offline acceptance tests PASS. No webhook registered and no Telegram send performed.

**Not yet verified:** Public HTTP browser verification of `/telbot` and new API responses was unavailable from assistant's network/DNS; `READY` alone is deployment evidence, NOT live app acceptance. Owner's prior `/ready` was PASS before this deployment; recheck after deployment when convenient. Neon TelBot UAT had ZERO tenants/bots immediately before release; no customer data changed, and no live BotFather bot token was submitted. Vercel encryption key is Sensitive and cannot be read by the assistant, so presence is verified but actual Fernet key validity is not. No assertion of Telegram auth/initData E2E, getMe from deployed runtime, customer bot connection, active bot, messaging or Production GO.

**Required owner UAT step:** Configure @MhnPdr_bot in BotFather -> My Bots -> Bot Settings -> Menu Button to open HTTPS URL `https://directpilot-telbot-uat-api.vercel.app/telbot`. This is required to obtain Telegram Mini App signed `initData`; launching URL in ordinary Chrome alone will not authenticate. Then open the configured button from Telegram to test: create tenant, connect a TEST child bot token, observe `pending`, no real sending. No bot token or webhook secret must be sent via chat.

**Next gates:** real Telegram Mini App open and basic UAT, scoped runtime `telbot_ua_runtime` replacement before external users, safe token lifecycle (rotation/revoke, encrypted key validity), control of activation/Webhook registration and outbound only under distinct UAT acceptance, full no-code configuration UI and publish flow. Preserve all historical records; older PARTIAL notes are historical and this checkpoint supersedes them.

---


## 2026-10-19 — LIVE TelBot UAT Backend readiness PASS (owner HTTP evidence)

**New verified HTTP response provided by owner from official TelBot UAT `/ready`:** `{"status":"ready","database":"available","migration":"current"}`. Source code for `/ready` checks UAT-only connection URI and role, visible schema marker `telbot.manager_inbound_updates`, latest migration `0002_webhook_auth`, and the nonempty `TELBOT_MANAGER_TOKEN` and `TELBOT_MANAGER_WEBHOOK_SECRET` environment variables. Accordingly **runtime Neon UAT connection, schema, migration and configured-env readiness PASS**. This supersedes historical notes saying `/ready` remained unverified or 503.

**Scope of this PASS:** only the FastAPI `/ready` gate, not Telegram Bot API authentication. `@MhnPdr_bot` is a user-supplied Manager Bot candidate; BotFather ownership, bot management entitlement, real token identity through `getMe`, actual `setWebhook`, update receipt, Mini App, child-bot flow, outbound replies, payments and production GO are **NOT VERIFIED**. No outbound Telegram calls or webhook registrations were made. Vercel project remains dedicated `directpilot-telbot-uat-api`; most recently verified functional deployment `dpl_EurnbxhBgdwP6T6JyWpRf4Nhj2Ap` was READY and mapped to official UAT alias. Neon UAT branch `br-tiny-poetry-arz49v2o` is used, NOT TelBot Neon Production; Instagram DirectPilot Production untouched.

**Next action (UAT-only):** validate BotFather ownership and Telegram Manager token-to-username mapping through a carefully controlled `getMe` read-only Telegram API request via secure server runtime without revealing token; then confirm managed-bot permissions, prepare webhook endpoint security and separately authorize live webhook registration or messaging. `TELBOT_TOKEN_FERNET_KEY` still needed for eventual encrypted child credentials. Before customer traffic, replace temporary privileged `telbot_owner` UAT DB login with restricted `telbot_ua_runtime`. Checklist T1 = infrastructure/backend READY PASS; Telegram real integration and end-to-end acceptance PENDING.

---

> **Current checkpoint — 2026-10-19:** T0 offline DONE; T1 isolated Neon UAT/Vercel Backend `/ready` owner-observed PASS after credentials, schema migration and Manager env setup. Telegram Manager Bot identity `@MhnPdr_bot`, BotFather management permissions, live webhook, Mini App, child-bot E2E and GO NOT VERIFIED. Details in [TelBot Master Checklist](TELBOT_RELEASE_CHECKLIST.md).


Date: 2026-10-17. Status: isolated code spike, **no production deployment**.

## Product hypothesis

A non-technical small business owner can build and manage their own Telegram chatbot from a single Manager Bot and a mobile-friendly Telegram Mini App. Unlike Instagram automation, Telegram is a separate product and release track; no change is made to the existing DirectPilot Instagram Production/UAT configuration.

## Official Telegram primitives (2026 Bot API)

1. In @BotFather's Mini App, enable bot management for the Manager Bot.
2. Manager Bot sends `KeyboardButton.request_managed_bot` in a private chat; user approves creation and the bot belongs to them. Suggest display name and username; do not create fake accounts or bypass user confirmation.
3. Manager Bot receives `managed_bot` update (also possible `message.managed_bot_created`), linking Telegram owner ID and child bot ID. Acquire child's credential securely, server-side, via `getManagedBotToken(user_id=child_bot_id)`.
4. Register a **separate** HTTPS webhook for each child bot using `setWebhook` and its `secret_token`; verify `X-Telegram-Bot-Api-Secret-Token` with a constant-time comparison. Idempotency key is `(child_bot_id, update_id)`.
5. Telegram Mini App provides no-code bot configuration. Validate Telegram Mini App `initData` server-side; never trust `initDataUnsafe`.
6. Support simple rule actions first; add AI only behind explicit opt-in and usage quotas.

Official sources:
- https://core.telegram.org/bots/api (managed_bot, KeyboardButtonRequestManagedBot, getManagedBotToken, setWebhook)
- https://core.telegram.org/bots/webapps (Mini App authorization)

## MVP user flow

1. User opens Manager Bot and taps **Create my bot**.
2. Telegram creates a managed bot after explicit user confirmation. The dashboard shows its username and connection status.
3. User opens **Build bot** (Mini App) and configures greeting, keyboard menu and buttons, keyword → reply rules, FAQ, and fallback.
4. User taps **Publish**. A draft version is validated, stored, and atomically published.
5. A test message sent to the child bot returns the configured response. Operator can pause automated replies and take over.
6. Dashboard displays basic sent/received counts and recent failures with data retention controls.

## Architectural boundaries

- **Product isolation:** dedicated backend project, database and frontend deployment before real UAT; do not reuse DirectPilot Production credentials or database, though patterns may be reused.
- **Data model:** tenants, users, telegram_manager_bot, telegram_child_bots (owner_id, credential_reference, status), bot_configuration_versions, bot_rules, bot_chat_sessions, inbound_updates (unique child_bot_id/update_id), outbound_messages, audit_events.
- **API modules:** manager onboarding, child webhook router, published configuration engine, Telegram outbound client, Mini App backend, operator handover.
- **Security:** vault-encrypted bot tokens with rotation, least privilege, signed Mini App init data, webhook secret check, request-scoped tenant authorization, no credential logging, bot ownership confirmation, idempotency, rate limiting, admin separation.
- **Scale:** webhook handlers acknowledge only after durable queueing or persistence; actual bot reply processing can use a worker/queue as traffic grows. Do not assume serverless request duration suffices for AI calls.

## Delivery increments and acceptance

**T0 — feasibility spike (this branch)**
- Model managed-bot request/updates and rule execution offline.
- Unit tests for bad webhook secret, ownership event parsing, rule priority, tenant-scoped objects.
- No network access or new credentials needed.

**T1 — independent UAT infrastructure**
- Private repository/project or isolated extraction from prototype; own Neon branch/project and dedicated Vercel service.
- Manager Bot created by project owner via official @BotFather, bot-management enabled. Never paste token into tickets, GitHub or chat.
- Webhook endpoints secured; invalid token fails closed, duplicate update idempotent, tenant isolation verified.

**T2 — working customer bot builder**
- Mini App UI: onboarding, create bot, bot list, greeting/fallback, text menu, keyword/FAQ rule editor, Publish button, test preview, basic analytics.
- Test cases: two tenants/bots, no cross-bot responses, no plaintext secrets, bad webhook rejected, published/draft differences respected, create/rotate/delete tested.

**T3 — additional MVP capabilities**
- Lead capture form and human takeover; media/file reply as feasible; optional AI answer with limited requests and cost controls.
- Event logs, user-friendly error handling, audit history.

**Later / not MVP**
- Graphical drag-and-drop flow editor, e-commerce catalog, payment services, CRM connectors, scheduled broadcasting, enterprise integrations.

## Decision gates

- This spike is not a deployable system and must not be merged into Instagram Production.
- Before T1, confirm final product name, isolation strategy and initial pricing/target market.
- Only proceed to a real bot token/webhook after owner has a separate Telegram Manager Bot.
- Meta work remains paused by owner request; preserve Vercel/Render/Neon environment, no integration teardown.

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
