# TelBot editor usability correction — 2026-10-29

## Owner feedback and verified cause

The owner found the previous mixed text/API form confusing and reported that the keyboard closed while typing. The old keyword input handler called reorder(), which appended every existing rule card back into the same container. A synthetic DOM regression test reproduced document.activeElement changing from the focused input to BODY after the first character. This establishes a DOM focus-loss bug consistent with the report; it does not substitute for testing a physical iOS Telegram keyboard.

## Final behavior

- Three persistent tabs: پیام شروع, پاسخ‌ها, آزمایش. Switching tabs preserves values and does not rebuild the fields. No automatic input focus when opening the editor.
- Existing bot owners see their workspace without the initial creation hero/steps. The setup introduction remains available for workspaces with no bots.
- Ordinary reply fields use کاربر چه می‌نویسد؟ and ربات چه پاسخی بدهد؟ with short examples. Matching/order/enable/delete stay in optional reply settings. API settings appear only for API replies; auth and request details have separate disclosures.
- Typing/composition changes only caption text. Only explicit add/reorder/undo actions move cards. Cursor and focus remain in the typed input.
- Automatic app-return refresh and manual list refresh preserve any open editor. Draft values remain in memory; no secret-bearing browser storage is introduced.
- A failed validation opens the right tab and nested disclosure, focuses the invalid field and explains the next action. The single save button saves/publishes the complete snapshot with the existing stale-version checks.
- Remove can be undone before save. Closing a changed form offers continued editing or explicit discard. Preview remains outside the save form, omits the credential and makes no provider/Telegram call.
- Mobile input text is 16px. Cache revision: 20261029-editor-ux-1.

## Scope and verification

No backend, database schema, saved customer configuration, credential, outbound flag, production project or live external provider is changed. Existing API GET/POST, response path, key-preservation and version isolation contracts remain.

Local checks: 125 Python tests discovered, 123 PASS and 2 disposable-PostgreSQL cases deferred to CI; actual app.js DOM behavior PASS. Regression asserts continuous keyword/caret and composition focus with no card moves, API-input focus, three-tab state, refresh preservation, hidden-field validation, undo/discard, secret-free preview and exactly one save/publish. JavaScript syntax and whitespace PASS.

Release branch feature/telbot-editor-usability-20261029, based on baa11ea3798c7a6d0e569daef6190a802faeece3. PR, CI, merge, exact UAT alias deployment and owner mobile acceptance PENDING. No mobile visual or physical keyboard acceptance is claimed.
