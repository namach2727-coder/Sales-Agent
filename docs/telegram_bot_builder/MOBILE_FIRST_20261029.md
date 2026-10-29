# TelBot mobile-first layout — 2026-10-29

The owner requires mobile to be the design baseline, including the sizes of menus and controls. This corrects the earlier desktop-style override stack; it does not establish owner acceptance of the new layout.

## Design contract

- Phone layout is the default: compact 12px outer/panel spacing and 10px bot/rule padding. At min-width:600px, desktop spacing and side-by-side main actions are opt-in.
- Buttons, tabs, native inputs/selects and expandable summaries use a 48px minimum control height. Checkbox labels provide a 48px clickable row while the checkbox itself remains compact. Text areas have room for multiple lines.
- Input text stays 16px; tab/button/option captions fit a narrow column. Primary save/close/refresh actions stack and fill the phone column; reply move buttons share a row and delete uses its own row.
- Explicit minmax(0,1fr) single-column tracks prevent nested native controls from expanding their parents. Flex tabs and card headers handle RTL layout; long rule captions are bounded to two lines with full accessible text and title retained.
- Public HTTPS URLs/JSON stay inside their controls. Short dropdown captions retain the exact same action/match/auth/method values. API mode uses a compact API badge.
- viewport-fit=cover with CSS safe-area padding; no zoom lock, fixed viewport height, sticky keyboard overlay, viewport-resize or automatic-focus handler is introduced.
- Cache revision 20261029-mobile-first-1. No backend, saved configuration, migration, token, external-provider or Telegram-send changes.

## Verification and limitations

Existing app.js DOM regression/behavior PASS, including caret/composition/API focus, refresh/tab state, validation, undo/discard, credential-free preview and one save/publish. Local Python 125 discovered: 123 PASS and 2 PostgreSQL-only cases deferred to CI; syntax/whitespace PASS.

For offline visual/layout review, the actual app DOM was populated using the existing synthetic Telegram/fetch test driver. Two states (text reply/API reply) were rendered at 320,360,390,430 CSS px, including a long username and long rule caption. The document renderer found no horizontal control overflow and no button/disclosure target below 48px. Native closed-details behavior was emulated, selected values copied explicitly and pseudo/anonymous text boxes excluded from control-target counts. This is an approximate static renderer using installed fonts, not a browser, actual OS dropdown, Telegram viewport or physical phone. Safe areas, keyboard and final owner acceptance remain device checks.

Git base 3c232142afe5dbe0ebe0aa6982cb22c49a56bcbd; candidate feature/telbot-mobile-first-20261029. PR, CI, exact UAT deployment and owner phone acceptance PENDING. Keep both outbound flags unchanged.
