# TelBot UAT — manual token onboarding (alternative to Bot Management Mode)

## 2026-10-20 — Manual BotFather onboarding PR #72 MERGED, separate TelBot UAT DEPLOYED

**DECISION:** Bot Management Mode was unavailable on the owner-side BotFather UI, and a locally run official Telegram getMe test for @MhnPdr_bot yielded `can_manage_bots=false`. Proceed with manual BotFather token connection instead of blocking product on managed-bot creation. Existing managed-bot flow remains behind its current unfinished gate.

**Verified source/release:** [PR #72](https://github.com/namach2727-coder/Sales-Agent/pull/72) merged into `feature/telegram-managed-bots-spike-20261017` (merge SHA `557b602f862f42ffedae12e4b6d403387c88ac37`). Latest PR isolated Telegram bot-builder CI **SUCCESS**, general CI **SUCCESS** (pytest, Docker build, Neon/Postgres checks). Independent TelBot UAT Vercel project ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` explicitly deployed that merge SHA to the project's `production` target, deployment `dpl_7rNivsQFDgi5bdLbVrybDGfzC9Uk` **READY**, official alias `directpilot-telbot-uat-api.vercel.app` VERIFIED pointing to the same deployment. This is NOT Instagram Production, not TelBot Neon Production.

**Implemented UAT-only:** mobile Persian RTL Mini App at `https://directpilot-telbot-uat-api.vercel.app/telbot` with CSP and no-store; signed Telegram initData auth; explicit one-tenant-per-Telegram-user account bootstrap (`GET/POST /api/v1/me/tenants`); owner-only `POST /api/v1/tenants/{tenant_id}/bots/connect-manual` accepts a BotFather bot token via HTTPS request body, validates its identity via getMe, Fernet encrypts with dedicated Sensitive `TELBOT_TOKEN_FERNET_KEY` (presence CONFIRMED in Vercel UAT), persists credential as `pending` and emits audit event. Globally unique Telegram bot ID, tenant membership checks and fail-closed missing key. Mocked offline acceptance tests PASS. No webhook registered and no Telegram send performed.

**Not yet verified:** Public HTTP browser verification of `/telbot` and new API responses was unavailable from assistant's network/DNS; `READY` alone is deployment evidence, NOT live app acceptance. Owner's prior `/ready` was PASS before this deployment; recheck after deployment when convenient. Neon TelBot UAT had ZERO tenants/bots immediately before release; no customer data changed, and no live BotFather bot token was submitted. Vercel encryption key is Sensitive and cannot be read by the assistant, so presence is verified but actual Fernet key validity is not. No assertion of Telegram auth/initData E2E, getMe from deployed runtime, customer bot connection, active bot, messaging or Production GO.

**Required owner UAT step:** Configure @MhnPdr_bot in BotFather -> My Bots -> Bot Settings -> Menu Button to open HTTPS URL `https://directpilot-telbot-uat-api.vercel.app/telbot`. This is required to obtain Telegram Mini App signed `initData`; launching URL in ordinary Chrome alone will not authenticate. Then open the configured button from Telegram to test: create tenant, connect a TEST child bot token, observe `pending`, no real sending. No bot token or webhook secret must be sent via chat.

**Next gates:** real Telegram Mini App open and basic UAT, scoped runtime `telbot_ua_runtime` replacement before external users, safe token lifecycle (rotation/revoke, encrypted key validity), control of activation/Webhook registration and outbound only under distinct UAT acceptance, full no-code configuration UI and publish flow. Preserve all historical records; older PARTIAL notes are historical and this checkpoint supersedes them.

---


Decision 2026-10-20: Telegram \`@MhnPdr_bot\` getMe confirmed username, but \`can_manage_bots=false\` and owner cannot locate the BotFather toggle. Do NOT block core product on Bot Management Mode. Add **manual BotFather bot-token connection** as a separate optional onboarding path.

Security/acceptance:
- Owner must be authenticated using Telegram Mini App initData and have **owner** role in active TelBot tenant. No anonymous connect API; enforce tenant isolation before any Telegram call.
- Collect child-bot token over HTTPS POST body only. Reject malformed tokens; call Bot API **getMe** (read-only), no token in response, logs, exceptions, GET parameters (except Telegram-required upstream Bot API route), analytics, browser localStorage or Git. Never retry repeatedly on error.
- Encrypt using independent Fernet key \`TELBOT_TOKEN_FERNET_KEY\`, stored Sensitive only in **independent TelBot UAT** project. Fail closed without key. Never store plaintext in Neon.
- Insert linked bot with status \`pending\` and per-tenant owner ID. Enforce globally unique Telegram bot ID; reject a bot already claimed by another tenant (HTTP 409). **No setWebhook**, live delivery, outbound message or Production change at this phase.
- Require additional proof of bot control/connection security, token rotation/revoke handling, published rules and receipt testing before marking the bot active. An API token alone is a bearer capability, not durable ownership proof.
- Current increment: offline-tested credential format/getMe helper; authenticated API wiring, live UAT deployment and UI remain next gates. Do not mislabel this as a finished customer workflow.
