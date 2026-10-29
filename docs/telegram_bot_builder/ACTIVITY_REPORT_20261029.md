# TelBot activity report — 2026-10-29

## Scope and owner flow

Read-only activity panel per bot. Open «گزارش عملکرد» in the bot card. It shows 24-hour incoming, sent, failed and uncertain/queued attempt counts, plus the last 20 incoming receipts with their latest delivery result. Update refreshes this panel only; Close removes it without replacing the response editor. Native phone acceptance pending.

Sent means a stored sent outbound status; individual events separately require presence of a Telegram message ID for the strong «پاسخ ارسال شد» label. An inbound without an outbound is not automatically considered a send failure: disabled runtime, unpublished configuration or paused chat can legitimately suppress a response. Queued attempts do not imply an automatic retry/worker. A failure does not cause any resend. No success percentage is computed from incomparable incoming/outgoing totals.

## API and privacy

GET /api/v1/tenants/{tenant_id}/bots/{bot_id}/activity requires valid Telegram initData, active membership and an exact tenant-bound non-revoked bot. Owner/editor/viewer may read. Server derives a fixed 24-hour window and limits events to 20. Counts independently aggregate inbound/outbound created in that window, so join multiplicity cannot inflate totals. Latest outbound is a lateral, same-tenant/same-bot lookup by source update. Response exposes window_hours, summary received/sent/failed/pending/checked_at, and events received_at/processing_status/delivery_status/telegram_acknowledged only. No bodies, chat/user IDs, raw Telegram IDs, credentials or upstream errors are returned. No SQL writes/commit, provider call, Telegram send or migration.

## Validation and release

Local 134 Python discovered: 130 PASS, 4 PostgreSQL skips. Actual DOM tests cover progress, four event outcomes, refresh failure retaining timestamped result, duplicate-click guard, close before late response and zero POST. Real UI/HTTP/PostgreSQL roundtrip also opens an empty report alongside the response editor without focus loss. Disposable PostgreSQL test seeds 25 current receipts, 2 sent/1 failed/1 queued, an old receipt/send and foreign tenant send; asserts counts, time filtering, 20-event bound, scope rejection and no content leakage. CI results and exact release must be recorded separately.

Previous PR #108 menu is merged but deployment quota blocked. Batch the report with that feature for the next single reviewed UAT deployment; no quota workaround, plan upgrade or Production change. Automatic replies remain enabled; external APIs remain disabled. Real UAT baseline v6 with 2 rules and zero buttons is evidence of the previous owner save test only.
