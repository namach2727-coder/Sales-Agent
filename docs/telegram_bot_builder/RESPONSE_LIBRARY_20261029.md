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
