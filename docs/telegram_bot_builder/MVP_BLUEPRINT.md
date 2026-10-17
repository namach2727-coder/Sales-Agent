# Telegram No-Code AI Bot Builder — independent product track

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
