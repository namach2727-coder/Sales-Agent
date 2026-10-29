## 2026-10-29 — CURRENT PR #109 activity + #108 menu MERGED; UAT quota BLOCKED

PR #109 https://github.com/namach2727-coder/Sales-Agent/pull/109 reviewed head 9f3cdd3809e527744a9368a0595575f952f94754 passed ALL 11 reported GitHub checks; squash merge 462eb5b4db34657b8aefa6a646c2129c95d9dbad ONLY into feature/telegram-managed-bots-spike-20261017 equals the reviewed tree. Includes previously reviewed/merged #108 reply menus. GitHub Vercel TelBot status on this exact combined merge is FAILURE: "Deployment rate limited — retry in 24 hours." No manual retry, quota workaround or plan change performed.

Live canonical https://directpilot-telbot-uat-api.vercel.app still points to dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5, exact prior d7728442b32f810b01658a64580084759b8b6162 optional-reply release. Both new menu and report are MERGED, NOT LIVE. Latest real UAT baseline: published v6, two saved keyword rules, zero menu buttons. Prior /ready 200 database available/migration current; no new runtime health or owner phone acceptance inferred for unpublished code. UAT replies ON, external API OFF; no schema, customer-setting, credential, outbound test, billing or Production changes.

Report delivers fixed 24-hour receive/sent/failed/uncertain counts and last 20 delivery metadata rows, manual refresh with retained prior results on errors, safe Close/race handling and coexisting editor focus. Authenticated active owner/editor/viewer membership and exact tenant+bot authorization required. No message content, user/chat IDs, raw Telegram message IDs or secrets returned. No sending, replay, mutation or background polling. Existing private/tenant/paused-chat/dedupe/at-most-once guards remain.

CI unit job 123580790111: 134 discovered, 130 PASS + 4 PostgreSQL skips; schema job 123580789774: all 4 PASS, including real report counts/window/20-row bound/cross-tenant/privacy and actual JS UI/HTTP/PostgreSQL menu save-reopen plus report alongside editor. DOM populated/error/duplicate-refresh/close-race/no-write/focus and seven Save scenarios PASS. Standalone Vercel-style import/route PASS locally. Real Telegram keyboard/report phone acceptance PENDING.

NEXT: when quota permits, deploy exact reviewed combined merge 462eb5b4db34657b8aefa6a646c2129c95d9dbad ONCE to existing directpilot-telbot-uat-api project/isolated production target; verify READY, exact canonical alias/source assets activity-1, /ready, unauthorized activity 401; owner then tests menu checkbox save/reopen, /start/button in private child bot and report refresh/status. Update all evidence separately. No TelBot retry automation was created.

---

# TelBot activity report — 2026-10-29

## Scope and owner flow

Read-only activity panel per bot. Open «گزارش عملکرد» in the bot card. It shows 24-hour incoming, sent, failed and uncertain/queued attempt counts, plus the last 20 incoming receipts with their latest delivery result. Update refreshes this panel only; Close removes it without replacing the response editor. Native phone acceptance pending.

Sent means a stored sent outbound status; individual events separately require presence of a Telegram message ID for the strong «پاسخ ارسال شد» label. An inbound without an outbound is not automatically considered a send failure: disabled runtime, unpublished configuration or paused chat can legitimately suppress a response. Queued attempts do not imply an automatic retry/worker. A failure does not cause any resend. No success percentage is computed from incomparable incoming/outgoing totals.

## API and privacy

GET /api/v1/tenants/{tenant_id}/bots/{bot_id}/activity requires valid Telegram initData, active membership and an exact tenant-bound non-revoked bot. Owner/editor/viewer may read. Server derives a fixed 24-hour window and limits events to 20. Counts independently aggregate inbound/outbound created in that window, so join multiplicity cannot inflate totals. Latest outbound is a lateral, same-tenant/same-bot lookup by source update. Response exposes window_hours, summary received/sent/failed/pending/checked_at, and events received_at/processing_status/delivery_status/telegram_acknowledged only. No bodies, chat/user IDs, raw Telegram IDs, credentials or upstream errors are returned. No SQL writes/commit, provider call, Telegram send or migration.

## Validation and release

Local 134 Python discovered: 130 PASS, 4 PostgreSQL skips. Actual DOM tests cover progress, four event outcomes, refresh failure retaining timestamped result, duplicate-click guard, close before late response and zero POST. Real UI/HTTP/PostgreSQL roundtrip also opens an empty report alongside the response editor without focus loss. Disposable PostgreSQL test seeds 25 current receipts, 2 sent/1 failed/1 queued, an old receipt/send and foreign tenant send; asserts counts, time filtering, 20-event bound, scope rejection and no content leakage. CI results and exact release must be recorded separately.

Previous PR #108 menu is merged but deployment quota blocked. Batch the report with that feature for the next single reviewed UAT deployment; no quota workaround, plan upgrade or Production change. Automatic replies remain enabled; external APIs remain disabled. Real UAT baseline v6 with 2 rules and zero buttons is evidence of the previous owner save test only.
