# TelBot UAT — manual token onboarding (alternative to Bot Management Mode)

Decision 2026-10-20: Telegram \`@MhnPdr_bot\` getMe confirmed username, but \`can_manage_bots=false\` and owner cannot locate the BotFather toggle. Do NOT block core product on Bot Management Mode. Add **manual BotFather bot-token connection** as a separate optional onboarding path.

Security/acceptance:
- Owner must be authenticated using Telegram Mini App initData and have **owner** role in active TelBot tenant. No anonymous connect API; enforce tenant isolation before any Telegram call.
- Collect child-bot token over HTTPS POST body only. Reject malformed tokens; call Bot API **getMe** (read-only), no token in response, logs, exceptions, GET parameters (except Telegram-required upstream Bot API route), analytics, browser localStorage or Git. Never retry repeatedly on error.
- Encrypt using independent Fernet key \`TELBOT_TOKEN_FERNET_KEY\`, stored Sensitive only in **independent TelBot UAT** project. Fail closed without key. Never store plaintext in Neon.
- Insert linked bot with status \`pending\` and per-tenant owner ID. Enforce globally unique Telegram bot ID; reject a bot already claimed by another tenant (HTTP 409). **No setWebhook**, live delivery, outbound message or Production change at this phase.
- Require additional proof of bot control/connection security, token rotation/revoke handling, published rules and receipt testing before marking the bot active. An API token alone is a bearer capability, not durable ownership proof.
- Current increment: offline-tested credential format/getMe helper; authenticated API wiring, live UAT deployment and UI remain next gates. Do not mislabel this as a finished customer workflow.
