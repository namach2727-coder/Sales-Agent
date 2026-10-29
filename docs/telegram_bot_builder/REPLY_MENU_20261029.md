## 2026-10-29 — CURRENT PR #108 menu buttons MERGED; UAT deployment quota BLOCKED

PR #108 https://github.com/namach2727-coder/Sales-Agent/pull/108 reviewed head 590a5cffdf037b52d11c6606099de10ee01744da passed all 11 reported GitHub checks. Squash merge 67d61c0ba4a006c123b00beab0a0deb9fb58c886 ONLY into feature/telegram-managed-bots-spike-20261017 matches the reviewed tree. GitHub Vercel TelBot status is FAILURE: "Deployment rate limited — retry in 24 hours." No deployment for this merged SHA exists. Do not claim keyboard controls are live or repeatedly trigger deployment/upgrade plans.

Current canonical https://directpilot-telbot-uat-api.vercel.app remains on dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5, prior optional-reply release. /ready 200 database available/migration current. Direct read-only UAT before/after source release confirms published v6, TWO keyword rules, zero menu buttons; previous real save fix is now verified in actual storage, but no menu test claimed. Owner reported prior UI excellent. Reply flag stays enabled; external API stays OFF. No schema, customer configuration, credentials or business Production change.

Feature awaiting deployment: optional per-response menu checkbox, inert mobile preview, versioned menu snapshot/readback, published enabled keyword-backed Telegram reply keyboard (12 choices/64-character labels product bounds, max 2 short labels per row, long label full-row), removal on next eligible response when cleared. Existing history and unrelated legacy menus/FAQs preserved; omitted controls retain older-client behavior. Private/tenant/paused-chat/dedupe/at-most-once guards preserved.

CI evidence: unit job 123572458715 ran 131 discovered (128 PASS + 3 PostgreSQL skips); schema job 123572459276 ran all 3 PASS including actual JS UI/HTTP/PostgreSQL checkbox persistence over two saves/reopens, optional blank rows, storage button removal and unrelated legacy/archive retention. Both JS DOM/focus and seven Save scenarios PASS. Native Telegram appearance/tapping acceptance remains PENDING.

NEXT: after quota permits, deploy exact merge 67d61c0ba4a006c123b00beab0a0deb9fb58c886 in existing isolated TelBot UAT project (its target production is UAT, not business Production), require READY and exact canonical alias/source assets plus /ready; then owner checks a response's menu option, saves/reopens and sends /start/taps button in private child-bot chat. Record real Telegram result separately. No automatic schedule created, no quota workaround or repeated deployment attempt.

---

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
