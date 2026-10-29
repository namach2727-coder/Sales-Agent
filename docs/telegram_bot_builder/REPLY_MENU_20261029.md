# TelBot reply menu — 2026-10-29

Scope: isolated TelBot UAT. Existing private text-response engine; optional text reply keyboard. No inline URL/callback editor, new API provider, migration, Production or billing change.

## Owner flow

Open reply settings, add or expand a completed response, select «نمایش این عبارت به‌صورت دکمه در ربات», inspect the inert menu preview and Save. Close/reopen to confirm checkbox persistence. Send /start in the private child bot, then tap the menu button. Telegram sends that label as ordinary text, routed through the existing first-enabled-match engine. Matching priority is unchanged. Disabled responses never appear. Untick all choices and Save; the next eligible response requests keyboard removal.

At most 12 selected buttons, 64 characters per label; labels equal the trigger text. Short labels are paired, labels longer than 16 characters use one row. Telegram controls final native presentation. Zero selection is supported. No card is added automatically. Partial input validation, readback, optional empty next rows and focus invariants remain.

## Storage and authorization

RuleInput.show_button is nullable for legacy compatibility. DraftInput.replace_reply_buttons defaults false; current UI sends true even for zero replies so removing all replies also removes owned buttons. Read rules uses correlated tenant/configuration menu existence; API credentials remain encrypted and absent from readback. Snapshot edits remove only keyword-backed reply entries in the copied menu. Unrelated prior menu entries and FAQs are copied, archived versions stay intact. Older clients that omit both controls preserve all menus. No new schema is needed.

Runtime only sees enabled rules of the current published tenant+bot configuration; keyboard is attached after private-message validation and before the existing durable attempt/send flow. Empty choices produce ReplyKeyboardRemove. No background catch-up, broadcast, extra send, provider invocation, or change to at-most-once behavior. External API flag stays OFF.

## Evidence / remaining gate

Local 131 Python tests: 128 PASS + 3 PostgreSQL skips; actual app.js DOM/focus and seven Save cases PASS. New tests cover size/count validation, mobile rows, disabled/duplicate suppression, keyboard clearing and /start transport payload. Updated CI storage and actual UI/HTTP/PostgreSQL tests cover checkbox persistence, two saves/reopens, removal and legacy/archive retention. CI/release/real device results must be recorded separately.

Owner accepted prior optional-reply layout. Read-only UAT baseline now published v6, two keyword rules, zero buttons; no customer content retrieved, no customer configuration changed by the agent.

Official Telegram contract: https://core.telegram.org/bots/api#replykeyboardmarkup ; https://core.telegram.org/bots/api#keyboardbutton ; https://core.telegram.org/bots/api#replykeyboardremove . Retrieved 2026-10-29. Product limits above are our editor limits, not claimed Telegram global limits.

## Rollback

Revert this reviewed feature only in isolated TelBot UAT. Preserve all saved snapshots. Old source preserves menu rows while omitting keyboard payload; a previously visible native keyboard may remain until a keyboard removal is sent by the new source. For a specific bot, the owner can untick choices and Save before rollback. Do not replay uncertain sends.
