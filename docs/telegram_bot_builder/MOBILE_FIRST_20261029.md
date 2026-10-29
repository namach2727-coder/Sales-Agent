# TelBot mobile-first layout — 2026-10-29

The owner requires mobile to be the design baseline, including the sizes of menus and controls. This corrects the earlier desktop-style override stack; it does not establish owner acceptance of the new layout.

## Design contract

- Phone layout is the default: compact 12px outer/panel spacing and 10px bot/rule padding. At min-width:600px, desktop spacing and side-by-side main actions are opt-in.
- Buttons, tabs, native inputs/selects and expandable summaries use a 48px minimum control height. Checkbox labels provide a 48px clickable row while the checkbox itself remains compact. Text areas have room for multiple lines.
- Input text stays 16px; tab/button/option captions fit a narrow column. Primary save/close/refresh actions stack and fill the phone column; reply move buttons use a wrapping row and delete uses its own row.
- Explicit minmax(0,1fr) single-column tracks prevent nested native controls from expanding their parents. Flex tabs and card headers handle RTL layout; long rule captions are bounded to two lines with full accessible text and title retained.
- Public HTTPS URLs/JSON stay inside their controls. Short dropdown captions retain the exact same action/match/auth/method values. API mode uses a compact API badge.
- viewport-fit=cover with CSS safe-area padding; no zoom lock, fixed viewport height, sticky keyboard overlay, viewport-resize or automatic-focus handler is introduced.
- Cache revision 20261029-mobile-first-1. No backend, saved configuration, migration, token, external-provider or Telegram-send changes.

## Verification and limitations

Existing app.js DOM regression/behavior PASS, including caret/composition/API focus, refresh/tab state, validation, undo/discard, credential-free preview and one save/publish. Local Python 125 discovered: 123 PASS and 2 PostgreSQL-only cases deferred to CI; syntax/whitespace PASS.

For offline visual/layout review, the actual app DOM was populated using the existing synthetic Telegram/fetch test driver. Two states (text reply/API reply) were rendered at 320,360,390,430 CSS px, including a long username and long rule caption. The document renderer found no horizontal control overflow and no button/disclosure target below 48px. Native closed-details behavior was emulated, selected values copied explicitly and pseudo/anonymous text boxes excluded from control-target counts. This is an approximate static renderer using installed fonts, not a browser, actual OS dropdown, Telegram viewport or physical phone. Safe areas, keyboard and final owner acceptance remain device checks.

Git base 3c232142afe5dbe0ebe0aa6982cb22c49a56bcbd; candidate feature/telbot-mobile-first-20261029. PR, CI and exact UAT deployment are complete. Owner physical phone acceptance remains pending; both outbound flags are unchanged.

## Verified UAT release

PR #105 reviewed head 01f5b47681020187026cd704c0a5803dd04fb05f passed all 11 reported GitHub checks. Squash merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 ONLY into feature/telegram-managed-bots-spike-20261017 has the exact reviewed tree. Vercel dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh is READY on that exact merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The Vercel target label production belongs only to this isolated UAT project; business Production was not promoted.

Verified 2026-10-29 11:31 Asia/Tehran / 08:01 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, mobile-first-1 revision, unauthenticated synthetic preview POST 401. Dedicated CI: 123 Python PASS plus 2 PostgreSQL cases PASS in schema-test, and actual app.js DOM/focus behavior PASS. Offline review: basic text/API states (176 controls) plus expanded reply settings/POST-message-forwarding states (216 controls), each at 320/360/390/430 CSS px; no horizontal control/container overflow or button/disclosure target below 48px. PNGs reviewed. This approximate document renderer does not establish native OS dropdown, Telegram safe-area, keyboard or real-device acceptance. Owner phone acceptance remains PENDING. Both outbound flags remain absent/default OFF; no backend, stored customer setting, migration, secret or live-send changes.

Additional advanced review used a text reply with matching/enable/reorder controls expanded and an API reply with POST body and explicit message forwarding fields visible. These are synthetic local fixtures, never provider or Telegram requests. Native details/selected-state behavior was emulated for the static renderer, whose wrapping may differ from a real browser. No debug PDF/image is a customer acceptance artifact.
