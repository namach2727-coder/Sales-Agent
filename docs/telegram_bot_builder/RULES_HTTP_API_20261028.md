## 2026-10-29 — TelBot editor usability and typing fix (release pending)

The next editor UI uses three tabs, with API connection options shown only for API replies and advanced request settings collapsed. Runtime/API contract and encrypted credentials are unchanged. Preview still executes no provider or Telegram calls. See EDITOR_USABILITY_20261029.md for current owner feedback, regression and release gates.

Owner rejected the previous editor as confusing and reported keyboard dismissal while typing. A regression test reproduced keyword-input focus changing to BODY because reorder() re-appended every card on each input event. Typing now updates captions only; card insertion/movement occurs on explicit add/reorder/undo actions. Real Telegram/iOS keyboard and visual acceptance are still pending; DOM focus tests are not a device acceptance claim.

---

## 2026-10-29 — CURRENT TelBot checkpoint: PR #103 deployed to UAT

This checkpoint supersedes the historical 2026-10-28 preview deployment quota blocker. Vercel directpilot-telbot-uat-api / team_Cu7IBomJgSNCXUMp3sILUUD4 is READY on dpl_Hy4hsuSi9PzhGNLcoZsqCDejkdYY, exact reviewed merge c08a3c26422ad2d28036946c274b035216fff8c0. Canonical alias https://directpilot-telbot-uat-api.vercel.app points to this deployment. The project target label production belongs ONLY to this isolated UAT project; it is not a business Production promotion.

Verified 2026-10-29 06:52 UTC (10:22 Asia/Tehran): /ready 200 ready/database available/migration current; /telbot 200 with response-preview-1 asset revision; JS 200 with preview and multi-rule controls; CSS 200 with preview layout; POST /preview with a synthetic body and no Telegram session returns 401 missing_init_data. Environment metadata still has six keys; TELBOT_REPLIES_ENABLED and TELBOT_EXTERNAL_API_ENABLED are absent/default OFF. No migration, customer-setting mutation, Telegram send, API-provider call or billing change performed. Owner mobile/preview interaction and live provider acceptance remain PENDING.

The previous quota blocker is resolved for this deployment: one authenticated Vercel Git deployment request of the exact reviewed merge succeeded. No repeated or parallel deployment was created. Existing CI evidence was reused because no executable code changed. Authenticated owner preview behavior remains a device acceptance step; server rule-selection/security cases were already covered offline.

Owner path: reopen Mini App -> تنظیم پیام‌های ربات -> آزمایش پاسخ -> enter a test message -> نمایش پیش‌نمایش. Use an API-rule test to verify that the panel identifies the selected rule and explicitly labels fallback, without calling the provider.

---

# Versioned replies and HTTP/JSON actions — UAT implementation

Owner request: allow more than a start/fallback message and connect bots to APIs. This is the independent TelBot track; no Instagram/Production changes.

## User behavior

- Up to 100 rules per version. Each has a keyword, exact/contains match, enabled state and ordered priority. First enabled matching rule wins; /start always uses greeting.
- Text replies and HTTP/JSON replies. API failure uses that rule's configured replacement text.
- Add, reorder, disable and remove rules from a new snapshot. Archived published versions remain intact. Legacy clients omitting rules copy existing rules; menu buttons and FAQs are copied to the new configuration rather than silently discarded.
- Editor preserves API credentials without readback using a scoped source-rule ID. Changing endpoint/auth mechanism requires entering a credential again. No key in browser storage, logs or returned configuration.
- Save and publish check the loaded base version to reject concurrent stale edits. A successful publish remains successful if optional refresh fails; re-open to continue editing.

## Supported HTTP adapter

- HTTPS public DNS domains, port 443; GET query parameters or POST JSON body. No query strings/userinfo/fragment in endpoint URL; use explicit query fields.
- No auth, Bearer token, or X-* API key header. Header secrets are encrypted with the dedicated TelBot vault key and a distinct API-config envelope.
- Static query values are strings; JSON body is an object limited to 8 KiB/depth 6. Optional user-message forwarding uses a chosen field name. It is OFF by default and clearly disclosed in the editor.
- Simple dotted response path, including array indices, selects a scalar text/number/bool. No script/template evaluation. Selected text must be nonempty and at most 4096 characters.
- This is NOT universal API compatibility: OAuth consent/refresh, SOAP/XML, gRPC, streaming, file uploads and nonpublic intranet APIs are not implemented.

## Security and delivery

- Validates HTTPS host syntax; resolves all A/AAAA answers at connection time and rejects private/reserved/loopback/link-local/multicast/mapped/tunnel destinations. Pins the actual TCP connection to a validated public IP, preserving original Host header, TLS SNI and certificate verification. No second unchecked DNS lookup.
- No proxy inheritance, redirects, application retries or cookie reuse. 8-second total request deadline, 64 KiB response cap, JSON content only, no compressed responses. Only static safe error codes escape the adapter.
- Credentials are never returned to the form. New-config validation errors omit submitted bodies. Credentials cannot be silently reused against a different URL/auth mechanism. Echo of the configured credential in selected response is rejected.
- Both TELBOT_REPLIES_ENABLED=true and TELBOT_ENV=uat are required for replies. TELBOT_EXTERNAL_API_ENABLED=true is separately required to call configured external APIs. These flags are NOT enabled by saving/publishing.
- Durable attempt is committed before API or Telegram network. Duplicate update does not repeat API POST. At-most-once attempt can lose a reply on crash/timeout; no exactly-once promise or automatic retry/recovery worker.
- Per-bot API budget: 20 attempts/minute, reserved under a PostgreSQL advisory lock and recorded as content-free audit events. Disabled/paused/budget-exhausted actions do not call the provider.

## Migration and verification

- Additive 0003_rule_api_calls adds action_type and encrypted API configuration to reply_rules; existing text rules default to text.
- Development database branch br-curly-fire-ar5mdqwv derives from a VERIFIED EMPTY parent (zero app tables), not UAT customer/bot credentials. It expires 2026-10-29T18:00:00Z. Migrations 0001–0003 applied there; SQL smoke verified default text, cipher constraint, tenant FK, ordering uniqueness and immutable historical copies; test fixture rollback left zero tenants/rules.
- Python tests cover input limits, network destination/connection pinning/TLS hostname, opt-in message forwarding, response limits, errors/no retries, encrypted round-trip/no key readback, scope checks, version conflict and runtime gating.
- DOM simulation executes the actual app.js with synthetic Telegram identity/fetch: existing rules, adding/reordering/removing, preserving secret reference, publishing once, reload and close. It is NOT a mobile visual/browser acceptance test.
- CI includes disposable PostgreSQL 18 to verify upgrades of legacy rows and actual HTTP draft/publish storage. It accepts only an explicitly named loopback test database, never live Neon credentials.

## Release order and acceptance

1. Require focused and CI tests. Deploy UAT code with both outbound flags unchanged/OFF; code supports 0002 while API schema is absent.
2. Verify exact UAT deployment SHA/alias and /ready. Apply checked-in 0003 transactionally ONLY to UAT after isolated migration tests. Verify old published configuration and bot counts are unchanged.
3. Owner reopens Mini App: start/fallback plus two text rules, reorder, disable, publish/reload, old versions retained, viewer denied.
4. Configure one owner-chosen API and select a safe response path. Do not collect its key in chat. No live provider calls until explicit acceptance/enablement; do not claim a particular provider works without its documented contract and real test.
5. Validate one real API response, provider failure fallback and duplicate update after controlled enablement. Record separate owner mobile/functional acceptance. No commercial/Production release is implied.

## Reference implementation guidance

- OWASP SSRF prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- HTTPX custom transport interface: https://www.python-httpx.org/advanced/transports/
- HTTPcore 1.x and HTTPX 0.27–0.28 interfaces are bounded in requirements and verified by fake network-stream tests; review these tests when upgrading the transport dependencies.


## 2026-10-28 — PR #102 multi-reply/API builder RELEASED TO UAT
PR #102 merged ONLY to isolated TelBot branch as bee4a84d3686def8eca40628c2d7bc24f993365f after all 11 reported GitHub checks SUCCESS. Dedicated TelBot job: 117 Python cases PASS, 2 PostgreSQL cases skipped there; separate PostgreSQL18 schema-test ran both skipped cases PASS (real legacy upgrade and HTTP snapshot/publish/secret retention). Actual app.js DOM behavior PASS. No real provider/Telegram calls or mobile visual acceptance claimed.
Read-only Vercel verification: official TelBot UAT alias -> dpl_DdZH5HGsp9wKri61GTtwsYbopLLA, READY, exact merge SHA bee4a84d. Code deployed FIRST with 0002-compatible fallback, then checked-in additive migration 0003_rule_api_calls applied atomically ONLY to Neon UAT br-tiny-poetry-arz49v2o/telbot with bounded lock/statement timeout. Pre/post transaction fingerprints and counts PASS: one active bot, four configuration versions, published version 4 preserved byte-equivalently; no rule or customer configuration added/changed by migration. Independent test branch remains expiring 2026-10-29T18:00Z. TelBot Production parent remains untouched.
Vercel environment metadata confirmed TELBOT_REPLIES_ENABLED and TELBOT_EXTERNAL_API_ENABLED absent, hence default OFF. Neither flag changed. API settings UI is available after schema migration; actual provider connectivity requires owner-chosen API contract/key entered privately and separate controlled live acceptance. Post-migration HTTP checks PASS: /ready 200 ready/database available/migration current, /telbot 200 and versioned JS/CSS 200 with new rule editor, unauthenticated config endpoint 401. Owner mobile/editor and real provider acceptance remain PENDING. Updated runbook docs/telegram_bot_builder/RULES_HTTP_API_20261028.md. Instagram Production unchanged.


## 2026-10-28 — PR #103 response preview merged; UAT deployment quota blocked
The editor includes a separate collapsible «آزمایش پاسخ» section after the save form. Enter a test message to evaluate the current unsaved greeting, fallback and ordered rules. The /preview endpoint requires owner/editor membership and the same tenant-bound bot identity as editing; it reads no published configuration or encrypted credential and does not write configuration or explicitly commit. It uses the shared runtime normalization/matching helpers. /start wins first; disabled rules are skipped; the first matching rule reports its displayed ordinal. API results explicitly state no provider was called and label the configured failure/disabled fallback separately. Preview does not establish whether live sending is enabled or a provider works.

The client shares snapshot serialization with publish but omits the credential field in preview requests. A preview result is invalidated when the form/test message changes, and an in-flight stale result is discarded. Output uses textContent; preview never triggers save/publish. Validation responses omit the entire submitted body. Both outbound flags and all persisted customer configuration remain unchanged.

Local verification: 125 Python cases discovered, 123 PASS + 2 PostgreSQL-only skips pending the existing disposable CI service; DOM test covers unsaved greeting, API selection/fallback, credential omission/preservation, plain-text output, stale-result suppression, empty-message handling and unchanged single save/publish behavior. JavaScript syntax and whitespace checks PASS. This is not browser/mobile visual or live-provider acceptance. Release evidence follows.

PR #103 reviewed head dfac4cb9c52d77379b926e7885ecfd0d80103a51 passed all 11 reported GitHub checks, including dedicated TelBot unit/DOM, PostgreSQL18 schema and both generic backend runs. Squash merge c08a3c26422ad2d28036946c274b035216fff8c0 ONLY into feature/telegram-managed-bots-spike-20261017. Python: 123 cases PASS in unit job plus 2 PostgreSQL cases PASS in schema job (125 unique); actual app.js DOM PASS. Standalone Vercel-style import PASS. Vercel rejected this exact merged SHA with "Deployment rate limited — retry in 24 hours." No new TelBot deployment exists; official alias remains READY on PR #102 bee4a84d3686def8eca40628c2d7bc24f993365f / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA. Preview is MERGED, NOT LIVE. No repeat deployment, upgrade, flag change, migration or saved customer-setting mutation performed. Owner mobile/preview/provider acceptance remain separate and pending.

Resume only after quota reset: use this same reviewed source on the existing isolated project, verify official alias exact Git SHA, /ready and preview assets/auth. No new migration is needed. Preview device acceptance and any real API/Telegram acceptance must be recorded separately.

Final read-only checkpoint 2026-10-28 18:09 UTC: official alias still points to dpl_DdZH5HGsp9wKri61GTtwsYbopLLA; /ready 200 (database available/migration current), /telbot and published JS 200 show rules-api-3 and no preview control/cache revision. Vercel environment metadata has six keys and neither outbound flag. This verifies the prior live release remains healthy, not deployment of PR #103.
