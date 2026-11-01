## 2026-11-01 — CURRENT: combined TelBot UAT release #108–#111 LIVE / READY

Supersedes the historical Vercel quota blocker: PR #111 https://github.com/namach2727-coder/Sales-Agent/pull/111 reviewed head c1d106287e52abb133258b56ef1414cd360b0fe4 passed ALL 11 reported checks. Squash merge 69f3858c60d3ca531c48798610eac55e98db9407 ONLY into feature/telegram-managed-bots-spike-20261017 equals the reviewed tree. Automatic deployment dpl_Gr3NmxVt57kFkd4FNKjbj5bxu1FK READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. No duplicate/manual deploy or plan upgrade. Target production here is the isolated TelBot UAT project, not business Production.

All four features are now DEPLOYED: #108 optional keyword menu buttons with inert mobile preview; #109 private 24-hour activity/last-20 delivery report; #110 audited owner/editor Pause/Resume with durable paused receipts and no replay; #111 local search and explicit text/API copying, including corrected text-to-API credential source identity. Mobile/focus/direct Save/optional blank-next-row/readback invariants remain. Source assets use 20261029-rule-library-1 revision; the date in that cache key is not the deployment date.

Verified 2026-11-01 06:33–06:34 UTC / 10:03–10:04 Asia/Tehran: /ready HTTP 200 ready/database available/migration current; /telbot, JS and CSS HTTP 200 and byte-identical to reviewed source. Unauthenticated activity GET 401; unauthenticated reply-state POST using synthetic UUIDs 401 missing_init_data. Environment metadata: 7 keys, TELBOT_ENV=uat and TELBOT_REPLIES_ENABLED=true; external API flag absent/default OFF. No secret value retrieved. Fresh read-only Neon UAT before/after release: 1 active bot, 0 paused, published v6, 2 saved keyword rules, 0 menu buttons. No real customer configuration/status, schema, credential, provider call, actual Telegram send or business Production mutation was performed by deployment/testing.

CI evidence on reviewed head: unit job 123620031044 ran 141 discovered (136 PASS + 5 PostgreSQL skips); schema job 123620030513 ran all 5 PASS including real UI/HTTP/PostgreSQL copied-response two-save/reopen, saved API credential clone/redaction, menu/history retention, report scope/window/counts, and pause/receipt/resume/duplicate/no replay. Both actual app.js DOM/focus/search/copy/report/control and seven Save error/readback scenarios PASS. Infrastructure/CI is NOT owner phone/native Telegram acceptance.

NEXT OWNER ACCEPTANCE: reopen a fresh Telegram Mini App, test search and Copy with a NEW trigger, Save/close/reopen. Select a response's menu checkbox and Save, then send /start and tap the button in the private child bot. Refresh activity report. Explicitly Pause, send a fresh message (receipt without response), Resume and send another fresh message (no historical replay). Already-reserved sends may finish, as stated in UI. Record these live/native outcomes separately; none is inferred from READY. Keep external APIs OFF until separately authorized provider testing. Production not promoted.

---

# TelBot response library — 2026-10-29

## Owner flow

Search by customer trigger or response text. Search is local, handles Persian ya/kaf variants and Latin letter case, and does not edit configuration. Show All clears it. Hidden replies retain their global order and values; Save includes all completed replies, not only visible ones. A matched card remains visible as its text is edited, until the owner changes the search again. Invalid hidden fields clear the filter and open the proper pane/disclosures.

Expand a response's more settings and tap Copy. The text, matching/enabled settings or API configuration are copied into a separate new card, while trigger is empty and menu selection is off. Enter a new trigger, edit as needed and Save. The limit remains 100 rows; Copy is guarded during Save/uncertain readback and empty placeholders cannot be copied. No autosave, API execution or external call. Add and Undo clear the filter so the focused new/restored card is visible.

## Credential and snapshot invariants

Search indexes only trigger and response text, never URL, JSON, API credentials or other technical inputs. Query is never part of Save/Preview and no browser storage is introduced. Existing API secret reuse uses the existing authorized tenant/bot/current-version source ID; saved secrets are not read back. A freshly typed key can be copied within the same form's masked password fields, and never enters preview or status output. Invalid API JSON prevents Copy and reveals the error rather than creating an empty/misconfigured clone.

Persisted-row identity is separate from API credential source identity. A saved text response changing to API has no reusable API source reference; it must provide its new settings/key normally. Saved API rows retain their source. A copied card is always new even when referencing a saved source. An existing saved card cleared to blanks still fails validation; a wholly blank new text placeholder remains optional. Verified server readback is required for Save success.

## Evidence and release

Local 141 discovered Python tests: 136 PASS, 5 PostgreSQL skips; actual DOM and seven Save scenarios PASS. Added search focus/normalization/no-results/no-request/no-dirty/Enter guard, no secret search, text/API copy, filtered hidden validation, existing cleared-row validation, text-to-API source and filtered full-save regressions. Real UI/HTTP/PostgreSQL CI now copies the second response before saving/reopening; storage CI verifies saved API source reuse for a clone without key readback.

Previous menu, activity and pause code is merged but unpublished due Vercel daily quota. This feature is also not live until CI/review, isolated merge and a single combined exact-SHA UAT deployment when quota permits. Keep private/tenant/paused/dedupe/runtime flags unchanged. No migration or actual customer configuration mutation. Real Telegram mobile acceptance pending.
