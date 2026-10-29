## 2026-10-29 — CURRENT: optional next reply / explicit Add fix (release pending)

Owner reports that an empty next reply blocks Save; requests optional creation through Add beside Save. Move the single type=button Add into the same mobile two-column footer as Save, with Close full-width below. Add switches to the replies tab and creates a card ONLY on explicit click; repeated Add reuses an untouched blank card. Typing/save never adds another card. New wholly blank text cards (including whitespace) are omitted from save and preview; a partial reply, existing saved rule cleared by the user, or selected API action remains validated rather than silently discarded. Backend required fields and snapshot/readback checks remain unchanged. Preserve focus-stable typing, touch sizing and direct Save click feedback.

Local actual app.js DOM suite PASS and seven Save scenarios PASS: zero replies/blank optional card, completed reply plus blank next card, partial validation, expired session, conflict and two readback failures. Updated real UI/HTTP/disposable PostgreSQL CI scenario adds an empty next card before both saves and verifies only the two completed responses survive reopening. CI, PR, merge, exact UAT deployment and owner phone acceptance PENDING at this source checkpoint. No backend/schema/customer-setting edits. UAT automatic replies remain enabled by prior owner authorization; external API remains OFF; business Production unchanged.

---

# TelBot Save click and verified persistence — 2026-10-29

## Report and evidence

Owner reports that new replies are not saved and selected «هیچ اتفاقی نمی‌افتد» for Save behavior. Read-only Neon UAT br-tiny-poetry-arz49v2o / telbot inspection found four configuration versions, v4 published with zero rules, no newer drafts. Greeting/fallback are present; no customer text or credential was retrieved. Schema 0003 exists; both allowed runtime roles have the required builder-table SELECT/INSERT/UPDATE privileges. Runtime log grouping yielded no useful request evidence, which does not prove absence of HTTP requests. No customer configuration was changed.

The previous Save button depended on native external-form association. A device-specific browser defect has not been reproduced; the fix removes that dependency instead of claiming a confirmed WebKit root cause.

## Behavior

- Save is type=button with an explicit click handler; Enter/form submit shares the same guarded operation. Handlers are registered before the configuration load enables actions.
- Progress, validation errors, expired-auth/conflict failures and success appear next to the Save control as well as the editor header. Repeated taps while busy do not create another version.
- Publication acknowledgement is followed by GET readback. Published ID/version, greeting, fallback and ordered rule fields/count must match before the form is replaced and success displayed. Readback failure/mismatch keeps the entered text and reports uncertainty; it does not silently republish.
- Authentication TTL, tenant isolation, secret handling, backend/version schema and both outbound flags are unchanged. No browser secret storage, forced auth bypass or automatic publication retry.
- Cache revision 20261029-save-click-1. Mobile 48px controls/16px inputs and persistent typing DOM remain intact.

## Verification

Local existing actual-JS DOM/focus tests PASS; five new save scenarios PASS: invalid required field, expired session, stale publish conflict, failed readback and mismatched readback. They verify visible footer feedback, retained input/card identity, re-enabled responsive Save and no false success or silent republish. Local Python 126 discovered: 123 PASS, 3 disposable-PostgreSQL cases deferred to CI. Syntax/whitespace PASS.

The schema CI job adds an actual-JS DOM test against a local FastAPI HTTP server and disposable PostgreSQL 18. A synthetic unique actor creates a text reply, explicitly saves, closes/reopens and reads it back, then adds a second reply and repeats. Database assertions require exactly three versions (seed plus two saves), two current rules and no duplicate publish from a second submit. The test only accepts a loopback database named telbot with user telbot_test; no live Neon credentials or Telegram/provider calls are used. It does not constitute a physical mobile/WebView acceptance test.

Candidate feature/telbot-save-click-20261029 based on f0edc4655ff082b549bea4fc2738e5403f81936b. CI, PR, merge and exact UAT deployment are complete. Owner phone Save acceptance is still pending. Do not alter the owner's v4 manually to manufacture an acceptance result.

## Verified release evidence

PR #106 reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc passed all 11 reported GitHub checks. Squash merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 ONLY into feature/telegram-managed-bots-spike-20261017 exactly matches the reviewed tree. Vercel dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9 is READY on that merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The project target label production is the isolated TelBot UAT service, not business Production promotion.

Verified 2026-10-29 13:15 Asia/Tehran / 09:45 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, save-click-1 revision, unauthenticated synthetic preview POST 401. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS, including the actual JS UI through HTTP/FastAPI/PostgreSQL add-save-close-reopen twice (3 versions total, 2 current replies, duplicate-submit guard). Both DOM behavior/focus and 5 save-error/readback scenarios PASS. Read-only UAT after deployment still shows published v4, 4 versions total and 0 rules; no customer configuration was written by deployment/testing. Both outbound flags remain absent/default OFF. Actual owner phone Save acceptance remains PENDING.

The schema test printed “TelBot real UI -> FastAPI -> PostgreSQL save/reopen: PASS”; it ran three cases successfully in the disposable service. A workflow dependency path was corrected before the reviewed head passed. No live customer POST was sent during release verification. The prior native-form mechanism was removed, but a physical browser-specific root cause is not claimed.
