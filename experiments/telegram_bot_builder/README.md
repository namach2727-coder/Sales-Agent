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
