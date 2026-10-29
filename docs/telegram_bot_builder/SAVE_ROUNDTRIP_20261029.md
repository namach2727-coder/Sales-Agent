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

Candidate feature/telbot-save-click-20261029 based on f0edc4655ff082b549bea4fc2738e5403f81936b. CI/PR/merge/UAT deployment and owner phone Save acceptance PENDING. Do not alter the owner's v4 manually to manufacture an acceptance result.
