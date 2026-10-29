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

Release branch feature/telbot-editor-usability-20261029 was based on baa11ea3798c7a6d0e569daef6190a802faeece3. Implementation, CI, merge and exact UAT deployment are complete. Owner real-device acceptance remains pending; no mobile visual or physical keyboard acceptance is claimed.

## Verified release evidence

PR #104 merged ONLY into feature/telegram-managed-bots-spike-20261017 as 17b2545849f8391291f14a46a7b6c18ed443ab22 after all 11 reported GitHub checks SUCCESS on reviewed head b45bdf9b0985464f3621a5792c17d9b62b4730b6. Merge tree exactly equals the reviewed tree. Vercel deployment dpl_DZDzon4PcrDYzGfvLa8rEP9VqJFD is READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. This project target label production is the isolated TelBot UAT project, not business Production.

Verified 2026-10-29 10:57 Asia/Tehran / 07:27 UTC: /ready 200 ready/database available/migration current; HTML, JS and CSS 200 and byte-identical to the reviewed local assets (20261029-editor-ux-1); unauthenticated synthetic POST /preview 401 missing_init_data. Dedicated CI ran 123 Python cases PASS, with the other 2 PostgreSQL cases PASS in schema-test; actual app.js DOM behavior/focus regression PASS. Both outbound flags remain absent/default OFF. No schema, stored customer-setting, credential, provider-call or Telegram-send change. Owner real Telegram/iOS keyboard and visual acceptance remains PENDING.

Git provider automatically built the reviewed preview, but its /telbot paths returned 404 under that target; runtime acceptance was performed against the configured canonical UAT target after merge. No duplicate manual deployment was created. The only release acceptance outstanding is the owner device interaction; actual external-provider delivery retains its separate gate.
