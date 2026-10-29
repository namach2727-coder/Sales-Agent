## 2026-10-29 — CURRENT PR #106 Save click/readback fix: UAT READY

Save now runs through a direct click handler with feedback next to its footer. Success requires matching persisted readback; errors keep typed text. Three mobile tabs and focus-stable controls remain. The real UI/API/PostgreSQL roundtrip is CI-proven, but physical owner interaction still requires acceptance. Details: SAVE_ROUNDTRIP_20261029.md.

PR #106 reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc passed all 11 reported GitHub checks. Squash merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 ONLY into feature/telegram-managed-bots-spike-20261017 exactly matches the reviewed tree. Vercel dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9 is READY on that merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The project target label production is the isolated TelBot UAT service, not business Production promotion.

Verified 2026-10-29 13:15 Asia/Tehran / 09:45 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, save-click-1 revision, unauthenticated synthetic preview POST 401. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS, including the actual JS UI through HTTP/FastAPI/PostgreSQL add-save-close-reopen twice (3 versions total, 2 current replies, duplicate-submit guard). Both DOM behavior/focus and 5 save-error/readback scenarios PASS. Read-only UAT after deployment still shows published v4, 4 versions total and 0 rules; no customer configuration was written by deployment/testing. Both outbound flags remain absent/default OFF. Actual owner phone Save acceptance remains PENDING.

---

## 2026-10-29 — CURRENT PR #105 mobile-first layout: UAT READY

The owner mobile-first requirement is implemented on UAT: compact default spacing, full-width primary actions, equal tabs and short native-option captions. Focus stability, three-tab navigation, preview isolation and saved-value contracts are unchanged. Detailed sizing evidence: MOBILE_FIRST_20261029.md.

PR #105 reviewed head 01f5b47681020187026cd704c0a5803dd04fb05f passed all 11 reported GitHub checks. Squash merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 ONLY into feature/telegram-managed-bots-spike-20261017 has the exact reviewed tree. Vercel dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh is READY on that exact merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The Vercel target label production belongs only to this isolated UAT project; business Production was not promoted.

Verified 2026-10-29 11:31 Asia/Tehran / 08:01 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, mobile-first-1 revision, unauthenticated synthetic preview POST 401. Dedicated CI: 123 Python PASS plus 2 PostgreSQL cases PASS in schema-test, and actual app.js DOM/focus behavior PASS. Offline review: basic text/API states (176 controls) plus expanded reply settings/POST-message-forwarding states (216 controls), each at 320/360/390/430 CSS px; no horizontal control/container overflow or button/disclosure target below 48px. PNGs reviewed. This approximate document renderer does not establish native OS dropdown, Telegram safe-area, keyboard or real-device acceptance. Owner phone acceptance remains PENDING. Both outbound flags remain absent/default OFF; no backend, stored customer setting, migration, secret or live-send changes.

---

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
