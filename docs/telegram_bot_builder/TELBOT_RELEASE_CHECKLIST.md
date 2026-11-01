## 2026-11-01 — CURRENT: owner directs transactional service bot builder; synthetic prototype (release pending)

Owner clarified target: a no-code bot capable of server-connected service sales, checkout, verified payment, account creation and configuration delivery, using a VPN seller as an example. Current TelBot has NO AI. Private behavior/source/latency of @sadshekanvpnbot was not observed; only public profile plus owner description are evidence. Owner answered that NO real panel is available and selected engine + synthetic sample now, real connection later. Do not substitute more keyword-only polish for this direction and do not claim real provisioning/payment integration is complete.

Implemented first pure ServiceFlow state machine and UAT owner/editor-only «نمونهٔ فروش و تحویل سرویس» preview: select fixed synthetic plan -> frozen order amount/currency -> synthetic checkout -> trusted-adapter payment check bound to order/reference/amount/currency -> provisioning instruction -> mock username/password/config delivery. Four cases: paid, unconfirmed, mismatched amount, unknown provisioning outcome. All demo links are inert text; all accounts/configs are clearly unusable DEMO data. Preview does membership/bot reads only; no DB writes, real HTTP/provider/vault/Telegram operation even with outbound flags ON. Existing child-bot runtime is NOT wired to this engine.

Core separates customer actions from trusted external receipts, suppresses repeated callbacks/customer taps within a run, produces scope/run-bound operation/idempotency IDs, rejects invalid prices/foreign operations/payment mismatches, redacts account repr/error details, and stops unknown outcomes without blind retry. This is IN-MEMORY prototype behavior, NOT durable cross-restart idempotency. Live use still requires persistent version-pinned workflow/order/operation storage, encrypted result handling, real verified gateway + panel adapters with idempotency/reconciliation contracts, no-code scenario authoring and customer-chat renderers. No financial amount/latency/commercial readiness claim.

Local Python: 150 discovered, 145 PASS + 5 disposable PostgreSQL skips. Actual DOM paid/unconfirmed/mismatch/timeout, inert links/plain text, duplicate run and close-race tests plus existing editor/report/control/search/copy and seven Save scenarios PASS. Updated CI real UI/HTTP/PostgreSQL case opens/runs the synthetic sample while preserving reply editor and configuration version counts. New pure/API tests cover payment gate, scope/amount/currency/reference, duplicate operations, unknown outcomes, no live effects, auth and secret-redacted validation. CI/PR/merge/deployment/owner phone acceptance PENDING. No schema, customer setting/status, external flag, real order/payment/account/provider/send or Production change. Runbook docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md.

---

## 2026-11-01 — CURRENT: combined TelBot UAT release #108–#111 LIVE / READY

Supersedes the historical Vercel quota blocker: PR #111 https://github.com/namach2727-coder/Sales-Agent/pull/111 reviewed head c1d106287e52abb133258b56ef1414cd360b0fe4 passed ALL 11 reported checks. Squash merge 69f3858c60d3ca531c48798610eac55e98db9407 ONLY into feature/telegram-managed-bots-spike-20261017 equals the reviewed tree. Automatic deployment dpl_Gr3NmxVt57kFkd4FNKjbj5bxu1FK READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. No duplicate/manual deploy or plan upgrade. Target production here is the isolated TelBot UAT project, not business Production.

All four features are now DEPLOYED: #108 optional keyword menu buttons with inert mobile preview; #109 private 24-hour activity/last-20 delivery report; #110 audited owner/editor Pause/Resume with durable paused receipts and no replay; #111 local search and explicit text/API copying, including corrected text-to-API credential source identity. Mobile/focus/direct Save/optional blank-next-row/readback invariants remain. Source assets use 20261029-rule-library-1 revision; the date in that cache key is not the deployment date.

Verified 2026-11-01 06:33–06:34 UTC / 10:03–10:04 Asia/Tehran: /ready HTTP 200 ready/database available/migration current; /telbot, JS and CSS HTTP 200 and byte-identical to reviewed source. Unauthenticated activity GET 401; unauthenticated reply-state POST using synthetic UUIDs 401 missing_init_data. Environment metadata: 7 keys, TELBOT_ENV=uat and TELBOT_REPLIES_ENABLED=true; external API flag absent/default OFF. No secret value retrieved. Fresh read-only Neon UAT before/after release: 1 active bot, 0 paused, published v6, 2 saved keyword rules, 0 menu buttons. No real customer configuration/status, schema, credential, provider call, actual Telegram send or business Production mutation was performed by deployment/testing.

CI evidence on reviewed head: unit job 123620031044 ran 141 discovered (136 PASS + 5 PostgreSQL skips); schema job 123620030513 ran all 5 PASS including real UI/HTTP/PostgreSQL copied-response two-save/reopen, saved API credential clone/redaction, menu/history retention, report scope/window/counts, and pause/receipt/resume/duplicate/no replay. Both actual app.js DOM/focus/search/copy/report/control and seven Save error/readback scenarios PASS. Infrastructure/CI is NOT owner phone/native Telegram acceptance.

NEXT OWNER ACCEPTANCE: reopen a fresh Telegram Mini App, test search and Copy with a NEW trigger, Save/close/reopen. Select a response's menu checkbox and Save, then send /start and tap the button in the private child bot. Refresh activity report. Explicitly Pause, send a fresh message (receipt without response), Resume and send another fresh message (no historical replay). Already-reserved sends may finish, as stated in UI. Record these live/native outcomes separately; none is inferred from READY. Keep external APIs OFF until separately authorized provider testing. Production not promoted.

---

## 2026-10-29 — CURRENT: response search/copy (source; combined release pending)

Owner requested continued development. Added local keyword/response-text search with Persian ya/kaf + NFKC and case-insensitive Latin matching, count/no-results and Show All. Search alone does not dirty or publish the form, never transmits queries and never indexes API keys/technical fields. Filtering only changes visibility, not order/values; editing a matched card does not re-hide its focused ancestors. Validation clears filter and reveals the offending field; Add/Copy/Undo reveal their target. Filtered Save still serializes every completed response.

Explicit Copy in each response's more settings preserves text/match/enabled or current API settings. The new trigger starts blank and menu selection off, requiring owner choice before saving; no autosave or provider call. Saved API credentials stay referenced to the authorized current source, never retrieved; a newly typed credential is copied only within masked password fields in this same form and omitted from preview. New copied rows remain distinct from persisted rows. Also fixes text-to-API conversion incorrectly referencing a text row as a reusable saved API source; clearing an existing persisted response still fails validation rather than silently deleting it.

Local 141 Python discovered: 136 PASS + 5 PostgreSQL skips; actual DOM/focus/search/no-dirty/no-network/secret-exclusion/text+API copy/hidden-field validation/filtered Save and existing seven Save cases PASS. Updated CI real UI/HTTP/PostgreSQL roundtrip creates the second response by Copy, saves while filtered with an optional blank next row, then reopens both. Storage CI also clones an API rule with its saved credential source and asserts redacted public readback. CI/PR/merge/actual phone acceptance PENDING. No backend/schema/customer-setting/status/flag/provider/Telegram/Production change.

Current canonical still prior optional-reply d772844 / dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5; latest docs SHA 7422728 Vercel status freshly confirms daily quota failure. #108 menu/#109 report/#110 pause are merged, NOT LIVE. Batch this UI enhancement with them for one reviewed UAT deployment when quota permits. Reply flag remains ON, external API OFF. No repeated/manual deploy or quota workaround. Runbook docs/telegram_bot_builder/RESPONSE_LIBRARY_20261029.md.

---

## 2026-10-29 — CURRENT PR #110 pause/resume MERGED; combined UAT deployment quota BLOCKED

PR #110 https://github.com/namach2727-coder/Sales-Agent/pull/110 reviewed head ee25a6e32cf541a384d30f0a7ee0a4ec30a4f66f passed ALL 11 reported GitHub checks. Squash merge 95820708380036aa1ffccd412e58f1cd22929e54 ONLY into feature/telegram-managed-bots-spike-20261017 matches the reviewed tree. This combined source includes #108 menu, #109 activity and #110 owner/editor Pause/Resume. Vercel TelBot status on this exact merge is FAILURE: "Deployment rate limited — retry in 24 hours." All three features are MERGED, NOT LIVE. No manual deployment retry, quota workaround or plan change.

Canonical https://directpilot-telbot-uat-api.vercel.app still points to dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5 / prior d772844 optional-reply source. Fresh /ready HTTP 200 database available/migration current. Direct read-only UAT: 1 active bot, 0 paused bots, published v6 with 2 keyword rules. No real customer status/configuration was changed by this work; no actual Telegram/provider test. Reply flag remains ON, external API OFF. No schema, secret, billing or business Production change.

Delivered in reviewed code: expected-state tenant/role-guarded Pause/Resume plus atomic audit; local progress/error and preserved editor; paused authenticated receipts persist/dedupe without vault/API/send; observed-paused receipt cannot slip through racing Resume; current-state shared decision lock serializes Pause until pre-network durable attempt commit. Already-reserved/in-flight attempts may finish and UI says so. Resume never replays old/paused/uncertain messages. Pending/revoked/unready bots cannot use Resume to bypass activation; service global OFF remains OFF.

CI unit job 123609004576 ran 141 discovered (136 PASS + 5 PostgreSQL skips); schema job 123609005120 ran all 5 PASS, including real share-lock conflict, audited API transitions, ignored paused receipt/no outbound, Resume+duplicate/no replay and one NEW mocked reply. Actual JS/HTTP/PostgreSQL save/reopen/menu/report regression also PASS. DOM pause delayed/duplicate/error/expected-state/editor-focus, report/menu and seven Save scenarios PASS. Standalone Vercel-style reply-control import/route PASS locally. Actual phone/Telegram pause acceptance PENDING.

NEXT: after quota permits, deploy exact reviewed combined source 95820708380036aa1ffccd412e58f1cd22929e54 ONCE in existing isolated TelBot UAT project (production target here means UAT only); require READY/exact canonical alias/reply-control-1 source assets, /ready and unauthenticated activity/control 401. Owner then tests menu, report and Pause -> private message stored/no response -> Resume -> old duplicate not replayed/new message responds. Keep customer acceptance separate from CI. Update these checkpoints. No TelBot release retry automation created.

---

## 2026-10-29 — CURRENT: bot pause/resume control (source; release pending)

Owner requested continued TelBot development. Added owner/editor-only per-bot Pause/Resume with immediate local progress/error feedback and no editor rebuild. Viewer cannot mutate. Pending/revoked/incompletely activated bots cannot be resumed; expected_status plus conditional update rejects stale/racing state. Successful transitions append audit events in the same transaction; no-op does not duplicate audit. No credentials decrypted, webhooks changed or messages sent by the control endpoint. No global flag changes: runtime-enabled response explicitly distinguishes an active bot from service-wide sending disabled.

Webhook now accepts both active and paused registered bots with existing secret verification/dedupe and records incoming receipts. Paused receipt is ignored for replies without vault/API/send. A receipt first observed paused remains suppressed even if resume races ahead. Runtime rechecks current tenant+bot status under FOR SHARE until the durable pre-network attempt commit; pause UPDATE serializes against that decision. Already-reserved/in-flight responses may finish; UI explains this. Resume affects new messages only; no replay of paused receipts, uncertain attempts or prior messages. Existing per-chat paused suppression also remains.

Local Python 141 discovered: 136 PASS + 5 PostgreSQL skips; actual DOM control success/error/duplicate-click/state/caret tests and seven Save cases PASS. New disposable PostgreSQL case covers share-lock vs pause update, real API pause/audit, paused webhook receipt ignored with zero send, resume + duplicate producing no replay, then one new reply through mocked transport. CI/PR/merge/cloud/live phone acceptance PENDING. No schema, customer data/status/configuration mutation, provider call, actual Telegram send, flag, billing or Production change by implementation.

Previous #108 menu and #109 activity are merged but NOT LIVE due verified Vercel quota; previous canonical optional-reply release d772844 / dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5 remains last verified. Latest real UAT baseline v6/two saved rules/zero buttons. Batch these features for one reviewed UAT deployment after quota permits; never claim native/live acceptance from CI. Runbook docs/telegram_bot_builder/REPLY_CONTROL_20261029.md.

---

## 2026-10-29 — CURRENT PR #109 activity + #108 menu MERGED; UAT quota BLOCKED

PR #109 https://github.com/namach2727-coder/Sales-Agent/pull/109 reviewed head 9f3cdd3809e527744a9368a0595575f952f94754 passed ALL 11 reported GitHub checks; squash merge 462eb5b4db34657b8aefa6a646c2129c95d9dbad ONLY into feature/telegram-managed-bots-spike-20261017 equals the reviewed tree. Includes previously reviewed/merged #108 reply menus. GitHub Vercel TelBot status on this exact combined merge is FAILURE: "Deployment rate limited — retry in 24 hours." No manual retry, quota workaround or plan change performed.

Live canonical https://directpilot-telbot-uat-api.vercel.app still points to dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5, exact prior d7728442b32f810b01658a64580084759b8b6162 optional-reply release. Both new menu and report are MERGED, NOT LIVE. Latest real UAT baseline: published v6, two saved keyword rules, zero menu buttons. Prior /ready 200 database available/migration current; no new runtime health or owner phone acceptance inferred for unpublished code. UAT replies ON, external API OFF; no schema, customer-setting, credential, outbound test, billing or Production changes.

Report delivers fixed 24-hour receive/sent/failed/uncertain counts and last 20 delivery metadata rows, manual refresh with retained prior results on errors, safe Close/race handling and coexisting editor focus. Authenticated active owner/editor/viewer membership and exact tenant+bot authorization required. No message content, user/chat IDs, raw Telegram message IDs or secrets returned. No sending, replay, mutation or background polling. Existing private/tenant/paused-chat/dedupe/at-most-once guards remain.

CI unit job 123580790111: 134 discovered, 130 PASS + 4 PostgreSQL skips; schema job 123580789774: all 4 PASS, including real report counts/window/20-row bound/cross-tenant/privacy and actual JS UI/HTTP/PostgreSQL menu save-reopen plus report alongside editor. DOM populated/error/duplicate-refresh/close-race/no-write/focus and seven Save scenarios PASS. Standalone Vercel-style import/route PASS locally. Real Telegram keyboard/report phone acceptance PENDING.

NEXT: when quota permits, deploy exact reviewed combined merge 462eb5b4db34657b8aefa6a646c2129c95d9dbad ONCE to existing directpilot-telbot-uat-api project/isolated production target; verify READY, exact canonical alias/source assets activity-1, /ready, unauthorized activity 401; owner then tests menu checkbox save/reopen, /start/button in private child bot and report refresh/status. Update all evidence separately. No TelBot retry automation was created.

---

## 2026-10-29 — CURRENT: bot activity report (source; combined release pending)

Owner requested continued development while Vercel daily deployment quota blocks merged menu PR #108. Added a read-only per-bot report: incoming/sent/failed/uncertain attempt counts over server-side last 24 hours, last 20 receipt/delivery metadata rows, checked timestamp, manual refresh and Close. No message bodies, user/chat IDs, Telegram message IDs, secrets or provider responses are returned. A queued attempt is labelled outcome unknown, not promised background retry. Refresh failure keeps previously timestamped results; late response after Close cannot reopen the panel. Existing response editor focus/text are preserved.

GET /api/v1/tenants/{tenant_id}/bots/{bot_id}/activity requires authenticated active tenant membership plus bot ownership scope; viewers may read, cross-tenant/bot requests fail before report queries. All queries use tenant+bot and bounded event count/time. No writes, replay, outbound calls, schema changes or new background task. Replies remain ON in UAT, external API OFF, Production unchanged. Native phone/report acceptance remains separate.

Local 134 Python discovered: 130 PASS + 4 PostgreSQL skips; DOM suite including populated report, refresh error, duplicate refresh, close/race/no writes PASS; existing seven Save scenarios PASS. CI disposable PostgreSQL test covers real counts (25 incoming, 2 sent, 1 failed, 1 uncertain), last-20 bound, old-row exclusion, other-tenant exclusion and content privacy. Actual JS/HTTP/PostgreSQL roundtrip also opens the empty report alongside the reply editor. CI/PR/merge still PENDING at this source checkpoint. Runbook docs/telegram_bot_builder/ACTIVITY_REPORT_20261029.md.

Publishing remains BLOCKED by Vercel's previous "Deployment rate limited — retry in 24 hours"; no repeated/manual deployment attempts. Current live alias remains prior optional-reply release d7728442b32f810b01658a64580084759b8b6162 / dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5. PR #108 menu code and this report are NOT LIVE. After quota permits, deploy the latest reviewed combined TelBot UAT head once and verify exact alias/source, /ready, auth and owner phone acceptance. Published real UAT v6 with 2 replies/0 buttons was last verified; do not change customer settings to manufacture acceptance.

---

## 2026-10-29 — CURRENT PR #108 menu buttons MERGED; UAT deployment quota BLOCKED

PR #108 https://github.com/namach2727-coder/Sales-Agent/pull/108 reviewed head 590a5cffdf037b52d11c6606099de10ee01744da passed all 11 reported GitHub checks. Squash merge 67d61c0ba4a006c123b00beab0a0deb9fb58c886 ONLY into feature/telegram-managed-bots-spike-20261017 matches the reviewed tree. GitHub Vercel TelBot status is FAILURE: "Deployment rate limited — retry in 24 hours." No deployment for this merged SHA exists. Do not claim keyboard controls are live or repeatedly trigger deployment/upgrade plans.

Current canonical https://directpilot-telbot-uat-api.vercel.app remains on dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5, prior optional-reply release. /ready 200 database available/migration current. Direct read-only UAT before/after source release confirms published v6, TWO keyword rules, zero menu buttons; previous real save fix is now verified in actual storage, but no menu test claimed. Owner reported prior UI excellent. Reply flag stays enabled; external API stays OFF. No schema, customer configuration, credentials or business Production change.

Feature awaiting deployment: optional per-response menu checkbox, inert mobile preview, versioned menu snapshot/readback, published enabled keyword-backed Telegram reply keyboard (12 choices/64-character labels product bounds, max 2 short labels per row, long label full-row), removal on next eligible response when cleared. Existing history and unrelated legacy menus/FAQs preserved; omitted controls retain older-client behavior. Private/tenant/paused-chat/dedupe/at-most-once guards preserved.

CI evidence: unit job 123572458715 ran 131 discovered (128 PASS + 3 PostgreSQL skips); schema job 123572459276 ran all 3 PASS including actual JS UI/HTTP/PostgreSQL checkbox persistence over two saves/reopens, optional blank rows, storage button removal and unrelated legacy/archive retention. Both JS DOM/focus and seven Save scenarios PASS. Native Telegram appearance/tapping acceptance remains PENDING.

NEXT: after quota permits, deploy exact merge 67d61c0ba4a006c123b00beab0a0deb9fb58c886 in existing isolated TelBot UAT project (its target production is UAT, not business Production), require READY and exact canonical alias/source assets plus /ready; then owner checks a response's menu option, saves/reopens and sends /start/taps button in private child-bot chat. Record real Telegram result separately. No automatic schedule created, no quota workaround or repeated deployment attempt.

---

## 2026-10-29 — CURRENT: mobile reply-menu buttons (source, release pending)

Owner accepted the optional-reply UI and requested further development. Next feature: opt-in keyword buttons inside the customer bot. Each reply has a checkbox; selected enabled rules form a resizeable Telegram reply keyboard, at most two short labels per row, one long label per row. Limits are product bounds: 12 selections, 64 characters per label; ordinary keyword-only rules still allow 120. Current-form visual preview is inert, no provider/Telegram calls. Unticking all buttons removes a previously shown keyboard on the next eligible private reply. Existing UAT reply flag stays enabled; external API stays OFF.

Uses existing versioned menu_buttons storage, no migration. Public rules derive show_button only from tenant/configuration/keyword-matched reply entries. Explicit replace_reply_buttons plus rule selections replaces keyword-backed menu entries in a NEW snapshot; unrelated URL/callback/custom menus and FAQs are retained. Older clients omitting the new fields copy the full previous menu. Published history is never edited. Save readback includes button selections; never show success for mismatched menu state. Runtime attaches only published enabled selections, retains private-message/tenant/paused-chat/dedupe/pre-network-attempt guards; no unsolicited send is made by release.

Local validation: 131 Python discovered, 128 PASS + 3 disposable PostgreSQL skips; actual app.js DOM/focus and seven Save scenarios PASS. CI real UI/HTTP/PostgreSQL tests now assert button choices persist through two saves and reopen, with optional blank next cards; storage test covers removing a selected button, preserving archived menu and unrelated legacy reply. CI, PR, merge, exact UAT deployment and actual Telegram keyboard acceptance PENDING. Runbook: docs/telegram_bot_builder/REPLY_MENU_20261029.md.

Read-only real UAT before this release now confirms published v6 with TWO saved keyword rules and zero menu buttons. This supersedes the earlier v4/zero-rules persistence uncertainty; owner said the previous fix is excellent. Real keyword matching/keyboard appearance still require their own live acceptance. No customer configuration changed by the agent.

---

## 2026-10-29 — CURRENT PR #107 optional next reply: UAT READY

PR #107 https://github.com/namach2727-coder/Sales-Agent/pull/107 reviewed head 3bbf3d3c21e395f13531d8eb7fc8348c7f0862aa passed all 11 reported checks. Squash merge 1dddb7c65ab8324f94feda52854fc497e7434971 ONLY into feature/telegram-managed-bots-spike-20261017 matches the reviewed tree. Automatic Vercel deployment dpl_6uGhE51M7rFgUmsc2K5EPdhM9Ub8 READY on exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. HTML and optional-replies-1 JS/CSS returned 200 and matched reviewed source byte-for-byte; /ready 200 database available/migration current. Isolated UAT project target production is not business Production.

Delivered: explicit Add beside Save, full-width Close below on mobile; only explicit Add creates a new reply, repeated Add reuses blank placeholder; wholly blank NEW text replies omitted from save/preview, while partial/existing/API rows stay validated. No new row generated by typing or successful Save. Direct Save feedback/readback and focus safeguards preserved. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS including actual UI/HTTP/PostgreSQL two-save-close-reopen with blank next cards. Local DOM/focus and seven Save scenarios PASS. No backend, migration, customer configuration or flag changes in this release; automatic Telegram replies remain enabled and external APIs OFF. Previous real three-message reply acceptance stands.

Owner phone acceptance PENDING: reopen Mini App, complete one response, optionally leave the next card wholly blank, Save and close/reopen. Confirm only completed replies persist, no automatic next row, then send the keyword in private child-bot chat. Do not infer real owner persistence from synthetic tests. Previous deployment for rollback dpl_AwGctrHbVLywSvUMDUq9S1wBwnKw.

---

## 2026-10-29 — CURRENT: optional next reply / explicit Add fix (release pending)

Owner reports that an empty next reply blocks Save; requests optional creation through Add beside Save. Move the single type=button Add into the same mobile two-column footer as Save, with Close full-width below. Add switches to the replies tab and creates a card ONLY on explicit click; repeated Add reuses an untouched blank card. Typing/save never adds another card. New wholly blank text cards (including whitespace) are omitted from save and preview; a partial reply, existing saved rule cleared by the user, or selected API action remains validated rather than silently discarded. Backend required fields and snapshot/readback checks remain unchanged. Preserve focus-stable typing, touch sizing and direct Save click feedback.

Local actual app.js DOM suite PASS and seven Save scenarios PASS: zero replies/blank optional card, completed reply plus blank next card, partial validation, expired session, conflict and two readback failures. Updated real UI/HTTP/disposable PostgreSQL CI scenario adds an empty next card before both saves and verifies only the two completed responses survive reopening. CI, PR, merge, exact UAT deployment and owner phone acceptance PENDING at this source checkpoint. No backend/schema/customer-setting edits. UAT automatic replies remain enabled by prior owner authorization; external API remains OFF; business Production unchanged.

---

## 2026-10-29 — CURRENT: real Telegram automatic reply acceptance VERIFIED

Owner reported test completed. Direct read-only Neon UAT evidence: three new private updates at 15:24:56–15:25:10 UTC (18:54:56–18:55:10 Asia/Tehran), all processed; three outbound rows sent, all with Telegram message IDs, one attempt each, no error codes. One /start and two other text messages were answered. This confirms real inbound-to-backend-to-Telegram reply delivery; it does not establish a replay or paused-chat live test.

Persistence remains separate: current published configuration is STILL v4 dated 2026-10-28, with zero keyword rules and no newer draft/version. Therefore the two non-start messages exercised the published fallback; no new keyword response save or match acceptance can be claimed. Do not change customer configuration to manufacture acceptance. Next: diagnose owner Save feedback if they attempted to add a response; keep direct click feedback and readback verification. External API flag remains OFF; no provider test established. Seven older inbound rows precede reply activation and were not replayed.

Source/service/rollback details remain in the activation checkpoint below. Production unchanged. This checkpoint supersedes only the prior pending real automatic reply delivery status.

---

## 2026-10-29 — CURRENT: owner-authorized UAT automatic replies ENABLED

Owner explicitly requested enabling automatic replies to test saving and real replies together. Set TELBOT_REPLIES_ENABLED=true ONLY for directpilot-telbot-uat-api (prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L), existing production target of the isolated UAT project. TELBOT_EXTERNAL_API_ENABLED remains absent/default OFF. No business Production, Instagram, credentials, migrations or stored customer configuration changes.

Deployed existing reviewed source 03897ad0729222b1f031b43f3a8ab68311e111ad with the new flag: dpl_5atro4n9dYhVhb1VEp3MExVGCeq9 READY; canonical https://directpilot-telbot-uat-api.vercel.app points to that deployment. /ready HTTP 200, database available and migration current verified 2026-10-29 15:23 UTC (18:53 Asia/Tehran). Source behavior is unchanged from PR #106 / reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc; prior CI evidence still applies. Rollback: disable UAT reply flag and redeploy; no blind replay of uncertain outbound attempts.

Read-only baseline before live acceptance: 1 active bot, published v4, 0 published keyword rules, 0 sent outbound messages. Enabling replies affects new private text updates only; no historical catch-up. /start uses published greeting, first matching enabled rule supplies its response, unmatched text uses published fallback. API rules use configured failure response while external API calls are disabled. Existing deduplication, tenant isolation, chat pause and durable at-most-once attempt guards remain.

PENDING owner acceptance: reopen Mini App; add/save a keyword response and close/reopen to confirm; send /start, that keyword and unmatched text in the child bot private chat. Then verify count/status-only inbound/outbound evidence and Telegram message IDs. No actual Telegram delivery or owner-phone save acceptance claimed by infrastructure health alone.

---

## 2026-10-29 — CURRENT PR #106 Save click/readback fix: UAT READY

PASS: direct Save click, immediate feedback, busy duplicate guard, invalid/expired/conflict/readback cases with form retention, existing focus/mobile behavior, actual-JS/HTTP/PostgreSQL two-save/close/reopen, all CI, exact UAT deployment/assets/health/401. PENDING: actual owner phone tap and subsequent real-customer rule persistence confirmation. No live Telegram/provider call or production promotion.

PR #106 reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc passed all 11 reported GitHub checks. Squash merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 ONLY into feature/telegram-managed-bots-spike-20261017 exactly matches the reviewed tree. Vercel dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9 is READY on that merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The project target label production is the isolated TelBot UAT service, not business Production promotion.

Verified 2026-10-29 13:15 Asia/Tehran / 09:45 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, save-click-1 revision, unauthenticated synthetic preview POST 401. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS, including the actual JS UI through HTTP/FastAPI/PostgreSQL add-save-close-reopen twice (3 versions total, 2 current replies, duplicate-submit guard). Both DOM behavior/focus and 5 save-error/readback scenarios PASS. Read-only UAT after deployment still shows published v4, 4 versions total and 0 rules; no customer configuration was written by deployment/testing. Both outbound flags remain absent/default OFF. Actual owner phone Save acceptance remains PENDING.

---

## 2026-10-29 — CURRENT PR #105 mobile-first layout: UAT READY

PASS: persistent DOM/focus tests; ordinary and expanded settings at four phone widths in the offline renderer; 48px button/disclosure targets; all CI; exact alias/merge/source assets; health 200 and unauthenticated preview 401. PENDING: real Telegram phone layout, native dropdown, safe-area and keyboard acceptance. Static review is not device acceptance.

PR #105 reviewed head 01f5b47681020187026cd704c0a5803dd04fb05f passed all 11 reported GitHub checks. Squash merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 ONLY into feature/telegram-managed-bots-spike-20261017 has the exact reviewed tree. Vercel dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh is READY on that exact merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The Vercel target label production belongs only to this isolated UAT project; business Production was not promoted.

Verified 2026-10-29 11:31 Asia/Tehran / 08:01 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, mobile-first-1 revision, unauthenticated synthetic preview POST 401. Dedicated CI: 123 Python PASS plus 2 PostgreSQL cases PASS in schema-test, and actual app.js DOM/focus behavior PASS. Offline review: basic text/API states (176 controls) plus expanded reply settings/POST-message-forwarding states (216 controls), each at 320/360/390/430 CSS px; no horizontal control/container overflow or button/disclosure target below 48px. PNGs reviewed. This approximate document renderer does not establish native OS dropdown, Telegram safe-area, keyboard or real-device acceptance. Owner phone acceptance remains PENDING. Both outbound flags remain absent/default OFF; no backend, stored customer setting, migration, secret or live-send changes.

---

## 2026-10-29 — CURRENT PR #104 editor usability and typing fix: UAT READY

PASS: before/after DOM focus regression; caret/composition and API-field focus; zero rule-list moves while typing; tab/refresh preservation; hidden-field error focus; undo/discard; credential-free preview and one save/publish; all CI checks; exact UAT alias, source assets, health and 401 auth smoke. PENDING: owner physical Telegram/iOS typing and visual acceptance. No live-provider test claimed.

PR #104 merged ONLY into feature/telegram-managed-bots-spike-20261017 as 17b2545849f8391291f14a46a7b6c18ed443ab22 after all 11 reported GitHub checks SUCCESS on reviewed head b45bdf9b0985464f3621a5792c17d9b62b4730b6. Merge tree exactly equals the reviewed tree. Vercel deployment dpl_DZDzon4PcrDYzGfvLa8rEP9VqJFD is READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. This project target label production is the isolated TelBot UAT project, not business Production.

Verified 2026-10-29 10:57 Asia/Tehran / 07:27 UTC: /ready 200 ready/database available/migration current; HTML, JS and CSS 200 and byte-identical to the reviewed local assets (20261029-editor-ux-1); unauthenticated synthetic POST /preview 401 missing_init_data. Dedicated CI ran 123 Python cases PASS, with the other 2 PostgreSQL cases PASS in schema-test; actual app.js DOM behavior/focus regression PASS. Both outbound flags remain absent/default OFF. No schema, stored customer-setting, credential, provider-call or Telegram-send change. Owner real Telegram/iOS keyboard and visual acceptance remains PENDING.

---

## 2026-10-29 — CURRENT TelBot checkpoint: PR #103 deployed to UAT

This checkpoint supersedes the historical 2026-10-28 preview deployment quota blocker. Vercel directpilot-telbot-uat-api / team_Cu7IBomJgSNCXUMp3sILUUD4 is READY on dpl_Hy4hsuSi9PzhGNLcoZsqCDejkdYY, exact reviewed merge c08a3c26422ad2d28036946c274b035216fff8c0. Canonical alias https://directpilot-telbot-uat-api.vercel.app points to this deployment. The project target label production belongs ONLY to this isolated UAT project; it is not a business Production promotion.

PASS: reviewed source, prior CI, UAT READY, exact alias SHA, health, HTML/JS/CSS revision and unauthenticated preview 401. PENDING: owner device/unsaved preview interactions, provider contract and real delivery acceptance. Do not equate deployed preview with a successful API request or Telegram reply.

Verified 2026-10-29 06:52 UTC (10:22 Asia/Tehran): /ready 200 ready/database available/migration current; /telbot 200 with response-preview-1 asset revision; JS 200 with preview and multi-rule controls; CSS 200 with preview layout; POST /preview with a synthetic body and no Telegram session returns 401 missing_init_data. Environment metadata still has six keys; TELBOT_REPLIES_ENABLED and TELBOT_EXTERNAL_API_ENABLED are absent/default OFF. No migration, customer-setting mutation, Telegram send, API-provider call or billing change performed. Owner mobile/preview interaction and live provider acceptance remain PENDING.

---

# DirectPilot TelBot — T0–T3 Master Checklist

## 2026-10-20 — UAT Telegram Mini App login 401; Manager identity diagnostic deployed

Owner launched TelBot Mini App and could see the RTL onboarding form but received `Invalid Telegram Mini App authentication` (translated: `نشست تلگرام معتبر نیست`) when the app fetched tenants, so successful authentication must **NOT** be claimed. In a previous Mini App screenshot the Telegram header appeared to say `@SalesRobot`; verify launch originates from `@MhnPdr_bot` rather than another bot. No tenants or bots were observed at the last UAT Neon check.

Source indicates FastAPI `authenticate()` HMAC-verifies Telegram WebApp `initData` against Sensitive `TELBOT_MANAGER_TOKEN`, with a 1-hour maximum age. Possible causes include mismatch between Vercel-configured manager token and actual launcher bot, expired/invalid initData. Exact cause is not yet proven. Vercel runtime logs returned 403, so no diagnostic logs could be fetched.

**PR #73** https://github.com/namach2727-coder/Sales-Agent/pull/73 merged at SHA `8be18722bb1f6628f6ac405188d5e7409a201225` after dedicated TelBot CI PASS, and general CI later PASS. Vercel UAT deployment `dpl_BdNf1DPkf2sFqzd1bqb5GEjP3bz4` confirmed READY and official alias `https://directpilot-telbot-uat-api.vercel.app` points to it. Changes: GET `/api/v1/uat/manager-identity` calls Telegram Bot API `getMe` using server-side token, caches 5 minutes, returns **only** categorical `match/mismatch/unavailable/missing` (no raw bot token, ID, upstream responses); Persian Mini App now surfaces a targeted message after backend 401. Source/test validation PASS. Note: actual endpoint HTTP response could not be retrieved by assistant: public external fetch blocked and Vercel authenticated web fetch 403. **User must open the UAT diagnostic URL in a browser and share only JSON status**. `match` still does NOT imply valid initData. Do not expose the token or untrusted raw initialization payload. No changes to Instagram Production or TelBot Neon Production; no webhook or outbound messages.

**Next:** open `https://directpilot-telbot-uat-api.vercel.app/api/v1/uat/manager-identity`, record status; if `mismatch`, have owner update Sensitive `TELBOT_MANAGER_TOKEN` privately on dedicated Vercel UAT to actual @MhnPdr_bot token, redeploy and re-test; if `match`, relaunch only from @MhnPdr_bot and analyze auth_date/cryptographic flow without leaking initData; if `unavailable`, investigate Telegram API reachability and validity. Do not declare login PASS until `GET /api/v1/me/tenants` returns 200 under signed Mini App session.

---


## 2026-10-20 — Manual BotFather onboarding PR #72 MERGED, separate TelBot UAT DEPLOYED

**DECISION:** Bot Management Mode was unavailable on the owner-side BotFather UI, and a locally run official Telegram getMe test for @MhnPdr_bot yielded `can_manage_bots=false`. Proceed with manual BotFather token connection instead of blocking product on managed-bot creation. Existing managed-bot flow remains behind its current unfinished gate.

**Verified source/release:** [PR #72](https://github.com/namach2727-coder/Sales-Agent/pull/72) merged into `feature/telegram-managed-bots-spike-20261017` (merge SHA `557b602f862f42ffedae12e4b6d403387c88ac37`). Latest PR isolated Telegram bot-builder CI **SUCCESS**, general CI **SUCCESS** (pytest, Docker build, Neon/Postgres checks). Independent TelBot UAT Vercel project ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` explicitly deployed that merge SHA to the project's `production` target, deployment `dpl_7rNivsQFDgi5bdLbVrybDGfzC9Uk` **READY**, official alias `directpilot-telbot-uat-api.vercel.app` VERIFIED pointing to the same deployment. This is NOT Instagram Production, not TelBot Neon Production.

**Implemented UAT-only:** mobile Persian RTL Mini App at `https://directpilot-telbot-uat-api.vercel.app/telbot` with CSP and no-store; signed Telegram initData auth; explicit one-tenant-per-Telegram-user account bootstrap (`GET/POST /api/v1/me/tenants`); owner-only `POST /api/v1/tenants/{tenant_id}/bots/connect-manual` accepts a BotFather bot token via HTTPS request body, validates its identity via getMe, Fernet encrypts with dedicated Sensitive `TELBOT_TOKEN_FERNET_KEY` (presence CONFIRMED in Vercel UAT), persists credential as `pending` and emits audit event. Globally unique Telegram bot ID, tenant membership checks and fail-closed missing key. Mocked offline acceptance tests PASS. No webhook registered and no Telegram send performed.

**Not yet verified:** Public HTTP browser verification of `/telbot` and new API responses was unavailable from assistant's network/DNS; `READY` alone is deployment evidence, NOT live app acceptance. Owner's prior `/ready` was PASS before this deployment; recheck after deployment when convenient. Neon TelBot UAT had ZERO tenants/bots immediately before release; no customer data changed, and no live BotFather bot token was submitted. Vercel encryption key is Sensitive and cannot be read by the assistant, so presence is verified but actual Fernet key validity is not. No assertion of Telegram auth/initData E2E, getMe from deployed runtime, customer bot connection, active bot, messaging or Production GO.

**Required owner UAT step:** Configure @MhnPdr_bot in BotFather -> My Bots -> Bot Settings -> Menu Button to open HTTPS URL `https://directpilot-telbot-uat-api.vercel.app/telbot`. This is required to obtain Telegram Mini App signed `initData`; launching URL in ordinary Chrome alone will not authenticate. Then open the configured button from Telegram to test: create tenant, connect a TEST child bot token, observe `pending`, no real sending. No bot token or webhook secret must be sent via chat.

**Next gates:** real Telegram Mini App open and basic UAT, scoped runtime `telbot_ua_runtime` replacement before external users, safe token lifecycle (rotation/revoke, encrypted key validity), control of activation/Webhook registration and outbound only under distinct UAT acceptance, full no-code configuration UI and publish flow. Preserve all historical records; older PARTIAL notes are historical and this checkpoint supersedes them.

---


## 2026-10-20 — Manual BotFather token onboarding alternative: UAT PR #72

User approved continuing DirectPilot TelBot without Telegram Bot Management Mode because @MhnPdr_bot returned getMe `can_manage_bots=false` and the BotFather toggle could not be located on mobile or web. Do NOT treat automated managed-bot creation as currently available.

PR https://github.com/namach2727-coder/Sales-Agent/pull/72 is an isolated feature proposal, **NOT YET MERGED or DEPLOYED to official TelBot UAT** at this checkpoint. Manual path added: owner-only authenticated `POST /api/v1/tenants/{tenant_id}/bots/connect-manual`, input `bot_token`, server-side Telegram Bot API `getMe` validation, dedicated `TokenVault` Fernet encryption, tenant-scoped `pending` bot persistence and audit event, global Telegram bot ID uniqueness. No user token returned; no Telegram `setWebhook`, messages, account activations, customer data manipulation or Neon schema migration. Missing `TELBOT_TOKEN_FERNET_KEY` causes intentional HTTP 503 before calling Telegram.

New offline mocked Telegram and auth regression tests check invalid format, unauthorized/rejected token, network errors without leaked URI, Fernet nonplaintext storage, unauthorized users, wrong tenant and missing encryption key. Dedicated TelBot CI successful after fixing a signed_initdata test-fixture signature; general CI must also complete. Frontend self-serve UI, UAT Secret setup, actual live provider getMe, proof/ownership, webhook connection and child bot E2E remain blocked/pending. No modification of Instagram DirectPilot Production or TelBot Neon Production; do not call release GO.

---


## 2026-10-19 — Telegram Manager getMe identity PASS; Bot Management Mode BLOCKED

Owner ran the downloaded **read-only PowerShell getMe** diagnostic against the official Telegram Bot API, entering BotFather token locally (never shared in chat). **User-supplied observed result:** `{"status":"ENABLE_BOT_MANAGEMENT_MODE","username":"MhnPdr_bot","matches_expected":true,"can_manage_bots":false}`. This proves the **locally entered token** maps to the intended `@MhnPdr_bot` and Telegram accepted it. It does **not** prove the Sensitive `TELBOT_MANAGER_TOKEN` stored in Vercel is byte-for-byte identical. No token values, numeric IDs, URLs with embedded tokens, webhook calls, Telegram sends, or Neon writes are in this diagnostic.

**T1 acceptance breakdown:** `/ready` FastAPI/Neon/schema/configuration previously user-observed PASS; Telegram bot identity with manually entered credential PASS; Telegram bot management permission **FAIL/BLOCKED**. Telegram official documentation `https://core.telegram.org/bots/features` instructs: choose `@MhnPdr_bot` in **BotFather Mini App** settings and enable **Bot Management Mode**; this is an owner-operated Telegram account action. After saving, rerun the same local PowerShell getMe diagnostic; required status `VERIFIED`, `matches_expected=true`, `can_manage_bots=true`. Do not create a duplicate bot. Telegram webhooks, Mini App, managed child bots, token-vault storage, end-to-end and Production GO remain pending. Do not claim manager bot is operational until permission PASS.

**Safety:** No change to Instagram DirectPilot Production or TelBot Neon Production. No Telegram `setWebhook`, `sendMessage` or `getManagedBotToken` invoked. Extra reminder before onboarding external users: replace UAT runtime DB role `telbot_owner` with limited `telbot_ua_runtime`.

---


## 2026-10-19 — LIVE TelBot UAT Backend readiness PASS (owner HTTP evidence)

**New verified HTTP response provided by owner from official TelBot UAT `/ready`:** `{"status":"ready","database":"available","migration":"current"}`. Source code for `/ready` checks UAT-only connection URI and role, visible schema marker `telbot.manager_inbound_updates`, latest migration `0002_webhook_auth`, and the nonempty `TELBOT_MANAGER_TOKEN` and `TELBOT_MANAGER_WEBHOOK_SECRET` environment variables. Accordingly **runtime Neon UAT connection, schema, migration and configured-env readiness PASS**. This supersedes historical notes saying `/ready` remained unverified or 503.

**Scope of this PASS:** only the FastAPI `/ready` gate, not Telegram Bot API authentication. `@MhnPdr_bot` is a user-supplied Manager Bot candidate; BotFather ownership, bot management entitlement, real token identity through `getMe`, actual `setWebhook`, update receipt, Mini App, child-bot flow, outbound replies, payments and production GO are **NOT VERIFIED**. No outbound Telegram calls or webhook registrations were made. Vercel project remains dedicated `directpilot-telbot-uat-api`; most recently verified functional deployment `dpl_EurnbxhBgdwP6T6JyWpRf4Nhj2Ap` was READY and mapped to official UAT alias. Neon UAT branch `br-tiny-poetry-arz49v2o` is used, NOT TelBot Neon Production; Instagram DirectPilot Production untouched.

**Next action (UAT-only):** validate BotFather ownership and Telegram Manager token-to-username mapping through a carefully controlled `getMe` read-only Telegram API request via secure server runtime without revealing token; then confirm managed-bot permissions, prepare webhook endpoint security and separately authorize live webhook registration or messaging. `TELBOT_TOKEN_FERNET_KEY` still needed for eventual encrypted child credentials. Before customer traffic, replace temporary privileged `telbot_owner` UAT DB login with restricted `telbot_ua_runtime`. Checklist T1 = infrastructure/backend READY PASS; Telegram real integration and end-to-end acceptance PENDING.

---


## 2026-10-19 — Manager Bot UAT secrets stored; redeploy READY, HTTP check pending

- Owner confirmed BotFather API token saved privately in the **separate TelBot UAT Vercel project** (`prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`). Connector **verified presence**, Sensitive type and `production` target (of this independent UAT-only project) for `TELBOT_MANAGER_TOKEN`. Secret value was **not retrieved**, so bot identity `@MhnPdr_bot` / token match and Telegram getMe have **not** been verified.
- A new 64-character cryptographically random Telegram webhook secret was created and saved only as **Sensitive** `TELBOT_MANAGER_WEBHOOK_SECRET` on the same UAT-only project's `production` target. It was **not printed in docs, chat or GitHub**. Both secrets were verified PRESENT in Vercel env inventory. This merely satisfies backend env readiness gate; **no setWebhook / BotFather API / live message** was invoked. Credential retrieval after storage is restricted, so future webhook registration requires a deliberate secure runtime setup path without exposing the secret.
- Explicit UAT-target deploy after env changes: Vercel `dpl_EurnbxhBgdwP6T6JyWpRf4Nhj2Ap`, Git source `9cba6dd977c7b25f120145f4eeeac261262e75e8`, status **READY**, official alias `directpilot-telbot-uat-api.vercel.app` verified pointing to this deployment. Independent TelBot UAT Neon connection, schema marker and migration `0002_webhook_auth` had PASS from owner-observed prior `/ready` response `Telegram manager not configured`.
- **HTTP runtime READY remains UNVERIFIED:** assistant-side attempts to GET `/ready` fail due to DNS resolution and web access restrictions; owner must verify `https://directpilot-telbot-uat-api.vercel.app/ready` after current deploy. Expected `{"status":"ready","database":"available","migration":"current"}` if all configured, but not yet observed. This would establish Backend ready gate only, not identity verification, Telegram webhook delivery, Manager bot management permission, Mini App, token encryption or child-bot E2E.
- **T1 status:** DB/Schema PASS; Manager env keys SET; Vercel deploy READY; HTTP ready PENDING; Manager @MhnPdr_bot ownership/BotFather permissions UNVERIFIED; live Telegram and child-bot onboarding NOT STARTED. UAT temporarily still using overprivileged database role `telbot_owner`; switch to restricted runtime role before users. Instagram DirectPilot Production and independent TelBot Neon Production unchanged.

---


## 2026-10-19 — Existing Manager Bot candidate identified by owner

Owner supplied existing Telegram handle `@MhnPdr_bot` (`https://t.me/MhnPdr_bot`) when asked which bot appears in BotFather. Treat it as the proposed TelBot UAT **Manager Bot identity**, not as verified ownership, bot-management permission, or working webhook. Do NOT create a duplicate bot. Ownership and BotFather management capability still require operator confirmation.

Current independent TelBot UAT Vercel env inventory contains NO `TELBOT_MANAGER_TOKEN`, NO `TELBOT_MANAGER_WEBHOOK_SECRET`, and NO `TELBOT_TOKEN_FERNET_KEY`. UAT Neon DB and migration gates already PASS based on the owner-observed `/ready` response `Telegram manager not configured`; service overall readiness stays 503. The next action is for the owner to save the actual BotFather API token **privately in Vercel**, Sensitive `TELBOT_MANAGER_TOKEN`, target `production` of the isolated UAT project; never send token via chat or commit. Webhook secret and webhook registration require separate controlled steps and verification; real Telegram messages and Instagram Production untouched.

---


## 2026-10-19 — TelBot UAT Neon runtime gate PASS; Manager Bot settings pending

**NEW OWNER-OBSERVED HTTP RESULT:** On the official separate TelBot UAT API `/ready`, response is HTTP 503 with `{"detail":"Telegram manager not configured"}`. Backend exact execution order: FastAPI `get_connection()` guard validates UAT connection host, successfully opens PostgreSQL, validates allowed role and existence of `telbot.manager_inbound_updates`; then `/ready` reads `telbot.schema_migrations` latest version `0002_webhook_auth`; only after those checks returns this Manager configuration 503. Thus **UAT runtime DB connection, schema marker and migration gates PASS**; service readiness overall remains **503/NOT READY**, and Telegram end-to-end has not been tested.

**Vercel environment inventory (independent project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`):** `TELBOT_ENV`, `TELBOT_UAT_DATABASE_URL` (Sensitive), `TELBOT_UAT_DB_HOST` are present. `TELBOT_MANAGER_TOKEN` and `TELBOT_MANAGER_WEBHOOK_SECRET` are NOT DEFINED; `TELBOT_TOKEN_FERNET_KEY` also not present for future token encryption and child-bot onboarding. Do not invent BotFather credentials, expose secrets in chat/Git, register webhooks, enable child-bot live sends, or change either Instagram Production or TelBot Neon Production. UAT Neo branch migration 0002 and 14 tables confirmed in separate Neon read-only SQL; zero tenants and zero bots so far.

**Next UAT T1 gate:** owner creates/chooses a dedicated test Manager Bot through official Telegram BotFather and securely sets the real Manager Bot API token as Vercel Sensitive `TELBOT_MANAGER_TOKEN` and a generated cryptographically random Telegram webhook secret as Sensitive `TELBOT_MANAGER_WEBHOOK_SECRET` in the independent Vercel TelBot UAT project Production target. Do not request tokens in chat. Redeploy and ask owner to recheck `/ready`. A 200 reply thereafter establishes configured readiness only; does NOT prove Telegram webhook registration, Mini App onboarding, BotFather-managed child tokens, encryption/rotation, outbound replies, payments or product UAT. 

**Safety follow-up before any customer data:** replace temporarily elevated `telbot_owner` runtime connection with restricted role `telbot_ua_runtime` once credentials are provisioned and verified. Preserve evidence and mark T1 = DB/Schema PASS, Manager configuration BLOCKED, end-to-end NOT STARTED.

---


## 2026-10-19 — Owner corrected TelBot Neon UAT credential: redeploy VERIFIED

- Owner reported saving the correct Neon UAT direct connection URL privately in Vercel. No URL or password was handled by the assistant. Vercel environment inventory confirms Sensitive variable `TELBOT_UAT_DATABASE_URL` was UPDATED after previous failed `/ready` test; exact URI value is not accessible to connector, so runtime hostname/password still not directly independently visible.
- Neon project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, database `telbot`: direct host `ep-wandering-heart-ar7z3k0s.c-4.us-west-2.aws.neon.tech`, expected schema marker `telbot.manager_inbound_updates`, migration `0002_webhook_auth` verified read-only. The prior confirmed root cause was owner-provided connection URL using TelBot Neon **Production branch** host `ep-shiny-lab-arzxdhcd` instead of UAT. Owner now provided the UAT host and confirmed the new URL saved in Vercel.
- Independent TelBot UAT project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` was explicitly redeployed targeting its own Vercel `production` environment to inherit Sensitive variables. New deployment `dpl_8CyqxGnzQTDE5HMikDkdvEuckPVC` on code SHA `7a6d05de387159e3f4be24acb0d32448d76c0c08` reached **READY** and the official alias `directpilot-telbot-uat-api.vercel.app` was verified to point to that deployment. This **supersedes earlier quota and undeployed-change blockers**.
- Actual GET `/ready` and `/live` could **not** be performed in the assistant environment: public domain DNS resolution failed and web fetch also rejected the URL. No real runtime DB connectivity or readiness PASS yet. Owner action: open `https://directpilot-telbot-uat-api.vercel.app/ready` and share **only response body and HTTP status** (never secrets). Interpretation: `Telegram manager not configured` means database/schema gate passed but Manager Bot setup is pending; `TelBot UAT database unavailable` means credentials/transport failed; `TelBot UAT schema unavailable` means schema marker unavailable; `hostname_not_in_uat_allowlist` means wrong host remains. Keep TelBot T1 PARTIAL pending HTTP confirmation. This deployment does not touch Instagram Production, TelBot Neon Production, bot token handling or outbound Telegram.

---


## 2026-10-19 — TelBot UAT PR #69 deployment verified READY

**Supersedes prior Vercel Hobby quota blocker for this release.** PR [#69](https://github.com/namach2727-coder/Sales-Agent/pull/69) merged; operational code SHA `164f49f3ed07bd54887f0ab1ca3090a996859e61`. Independent TelBot UAT Vercel project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` deployed production-target (the target is Production *of the UAT-only project*) `dpl_9eyaJeeux53KhHQmBfFpwTy9U1tp` **READY**. Official alias `directpilot-telbot-uat-api.vercel.app` is verified mapped to that exact ID.

GitHub isolated Telegram CI **SUCCESS**, general CI **SUCCESS after retry**. Initial general CI failure was transient external Docker Hub 502 when pulling `python:3.12.10-slim-bookworm`; failed job rerun succeeded. Deployed version includes sanitized endpoint mismatch reason classification from PR #69, without disclosing URL, user or password.

**NOT VERIFIED:** actual runtime HTTP GET `/ready` or `/live` not fetchable from assistant-side network (DNS/URL restricted), so never claim Neon connection, Manager Bot or real Telegram sends PASS. Owner-side next isolated UAT step is `https://directpilot-telbot-uat-api.vercel.app/ready`, return status and JSON body only. If error is `hostname_not_in_uat_allowlist`, `connection_string_format_invalid`, `connection_string_has_extra_whitespace`, `uri_host_override_disallowed`, `connection_string_hostname_missing` or `connection_string_malformed`, resolve that exact reason; **do not ask to re-enter identical connection URL blindly** (owner already did it twice). `Telegram manager not configured` means DB and schema gates passed; Manager not ready. TelBot T1 = deployment PASS, runtime `/ready` pending.

No Instagram DirectPilot Production or TelBot Neon Production changes and no Telegram outbound performed.

---


## 2026-10-19 — No repeated credential request; precise TelBot UAT URI diagnosis

Owner confirms the requested Neon→Vercel connection-string configuration has **already been performed twice**. DO NOT repeat identical setup instructions or assert credentials were not saved. Current official TelBot UAT deployment returns `TelBot UAT database endpoint mismatch`; code's earlier endpoint guard conflated non-UAT host, malformed/shell-wrapped URI, whitespace and libpq host override. Sensitive Vercel URL is not accessible through connector; do not print or copy it.

**New isolated diagnostic fix:** PR branch `fix/telbot-uat-endpoint-mismatch-reason-20261019` adds `uat_host_failure_reason()` and sanitized 503 reason codes: `hostname_not_in_uat_allowlist`, `connection_string_format_invalid`, `connection_string_has_extra_whitespace`, `uri_host_override_disallowed`, `connection_string_hostname_missing`, `connection_string_malformed`, `uat_host_configuration_invalid`. Returns only static classifications — never actual hostname, username, URI, or password. The guard still rejects any unapproved host BEFORE network/database. Offline regression tests added for direct UAT, wrong Neon branch, quoted psql commands, whitespace and host overrides. No DB, Production, Telegram API or env secret changed.

**Release gate:** merge ONLY after TelBot isolated tests PASS; deploy to dedicated TelBot UAT Vercel Production target (NOT Instagram Production) and confirm official alias SHA; user then supplies sanitized `/ready` response. Resolve based on exact reason, without repeated blind credential reentry. Overall Neon runtime readiness remains UNVERIFIED, Manager Bot still not configured, no live outbound.

---


## 2026-10-19 — TelBot UAT endpoint guard triggered (verified new runtime report)

**Owner-provided current `/ready` HTTP response:** `{"detail":"TelBot UAT database endpoint mismatch"}`. This is the *new* PR #68 fail-closed guard, raised **before opening a PostgreSQL connection**, so it does not prove schema or DB availability. Runtime URL is not an accepted host in `TELBOT_UAT_DB_HOST` allowlist, has unexpected URI scheme, or contains a libpq host/hostaddr override. Do not disable this guard.

**Rechecked against the actual providers:** Neon TelBot UAT project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, direct host `ep-wandering-heart-ar7z3k0s.c-4.us-west-2.aws.neon.tech`, pooled variant `ep-wandering-heart-ar7z3k0s-pooler.c-4.us-west-2.aws.neon.tech`, and **pooler_enabled=false**. TelBot Neon Production branch uses a different hostname `ep-shiny-lab-arzxdhcd.c-4.us-west-2.aws.neon.tech`. Vercel TelBot UAT project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` has `TELBOT_UAT_DB_HOST` equal to the correct UAT pooled host. The current guard accepts this hostname and its direct variant. `TELBOT_UAT_DATABASE_URL` is Sensitive: Vercel does NOT reveal the actual URI, so its live hostname cannot be proven from connector metadata. Do not share DB URLs or passwords in chat or GitHub.

**Single unblock action / owner console:** Neon > `directpilot-telbot` > branch `uat` > DB `telbot` > temporary role `telbot_owner` > pooling OFF > copy the **raw** `postgresql://...` connection URI (not a `psql` command, `DATABASE_URL=` prefix, shell quoting, or code sample). In dedicated Vercel project `directpilot-telbot-uat-api`, overwrite Sensitive variable `TELBOT_UAT_DATABASE_URL` for the `Production` *target of this UAT-only project*; re-deploy to apply. Preserve configured `TELBOT_UAT_DB_HOST` (correct). Do not change TelBot Neon Production, its schema or Instagram Production. Before real customer data, replace overprivileged owner role with restricted runtime login.

**Next acceptance:** Recheck `https://directpilot-telbot-uat-api.vercel.app/ready` after redeploy. `TelBot UAT database endpoint mismatch` = URI still wrong format/host; `TelBot UAT database unavailable` = actual DB connection failure; `TelBot UAT schema unavailable` = connected DB has invisible/missing UAT marker; `Telegram manager not configured` = DB/schema checks PASS but Manager secret absent; HTTP 200 = backend readiness only. This incident is **BLOCKED ON SECURE URL UPDATE AND NEW HTTP RESULT**. Keep T1 PARTIAL and do not mark DB readiness PASS. PR#68 CI and Vercel READY are independent of runtime acceptance.

---


## 2026-10-19 — PR #68 deployment LIVE ON OFFICIAL TELBOT UAT ALIAS (new verified checkpoint)

**Supersedes the earlier 402/quota blocker, which is no longer the current deployment state.** Read-only Vercel verification: independent project `directpilot-telbot-uat-api`, deployment `dpl_HKaapwTGMPbo5H3x6gWZWXtYybXj` has **READY** state on source SHA `fe76fd7aa68e5d4ae5baf89ed824cf325937a8e0`; public alias `directpilot-telbot-uat-api.vercel.app` is attached to this exact deployment. GitHub main CI and isolated TelBot CI for PR #68 head `981a9033de7a1d3c8122ba61f8b69b24de982486` are both **SUCCESS**.

PR #68 was merged at `b9228213d1ac3cb02bd2157964ee1436ad15cec4`. The deployed source contains `is_uat_host` checking the configured Neon UAT pooled hostname and its direct equivalent before `psycopg.connect`, denying other hosts with 503 `TelBot UAT database endpoint mismatch`. No production data or Telegram send changed.

Vercel production-target variables on this TelBot-only UAT project: `TELBOT_ENV=uat`, `TELBOT_UAT_DB_HOST=ep-wandering-heart-ar7z3k0s-pooler.c-4.us-west-2.aws.neon.tech`, Sensitive `TELBOT_UAT_DATABASE_URL` (value inaccessible; key last updated 2026-10-19). This verifies presence and release configuration, **NOT successful runtime DB connection**. Attempts to retrieve HTTPS `/ready` and `/live` from assistant environment were blocked by network access; user HTTP smoke needed.

**Next mandatory UAT acceptance:** request `https://directpilot-telbot-uat-api.vercel.app/ready` after this deployment; log status/body and differentiate: `TelBot UAT database endpoint mismatch` = URL wrong Neon branch; `TelBot UAT schema unavailable` = connected DB has missing/invisible UAT marker; `TelBot UAT database unavailable` = DB credential/connection failure; `Telegram manager not configured` = DB marker and migration passed but Manager secrets missing; 200 = readiness only, not Telegram E2E. Prior schema 503 predates this active host guard and cannot be treated as the latest result. Do not ask user to expose any secrets. T1 PARTIAL; Manager Bot/live Telegram not configured; independent TelBot Neon Production and Instagram DirectPilot Production untouched.

---


## 2026-10-19 — TelBot PR #68 merged; Vercel quota blocks official UAT release

- PR [#68](https://github.com/namach2727-coder/Sales-Agent/pull/68) **MERGED** into isolated TelBot branch at Git commit `b9228213d1ac3cb02bd2157964ee1436ad15cec4`. Change: verify Neon URL host against TelBot UAT endpoint BEFORE connecting and fail closed with `TelBot UAT database endpoint mismatch`; offline UAT/direct vs non-UAT tests are present. Isolated TelBot CI for PR head **SUCCESS**; general CI was still running on last inspection and must not be claimed PASS yet.
- Vercel PR preview `dpl_HPUL37DKrN6bUKmR4WcDdLvSvdvM` on PR head is READY, **target=preview**. The database secret in Vercel is **production target only for this separate UAT project**. Do **NOT** promote the preview, since it does not establish inherited Production credentials.
- The official alias `directpilot-telbot-uat-api.vercel.app` **still points** to `dpl_7NaicKji7PfacmDxUatz3qfNw7VZ` on earlier SHA `5b22aac649251ad5856a28c22bc27e9875855044`, so live `/ready` does NOT yet include the host guard. Explicit production-target deployment of merge SHA `b9228213` failed: Vercel HTTP 402 `api-deployments-free-per-day`, retry-after 86400 seconds. **NO official runtime fix, no DB readiness PASS.**
- New deployment must wait until Vercel Hobby quota resets or owner makes a billing/plan decision. Recheck the exact source SHA, deployment state and alias after quota recovery, then ask owner to retest `/ready`. If `TelBot UAT database endpoint mismatch` appears, Vercel Sensitive URL points outside configured Neon UAT endpoint; owner must safely reselect Neon project `directpilot-telbot`, branch `uat`, database `telbot`, temporary role `telbot_owner`. Never paste URL/secret. If `Telegram manager not configured` appears, DB schema gate passed, not full app readiness.
- No Instagram DirectPilot Production, independent TelBot Neon Production, real Telegram webhook/message or customer data touched. Keep T1 PARTIAL and Manager Bot PENDING.

---


## 2026-10-19 — TelBot UAT repeated schema 503 diagnostic and endpoint guard

**Observed:** After Vercel environment update and redeploy `dpl_7NaicKji7PfacmDxUatz3qfNw7VZ` READY, owner still saw HTTP 503 `TelBot UAT schema unavailable`. Read-only Neon UAT `br-tiny-poetry-arz49v2o` shows `telbot.manager_inbound_updates`, migration `0002_webhook_auth`, and both runtime/owner have schema usage and marker SELECT; TelBot Neon production `br-fancy-feather-arydwgj7` has zero tables. This strongly suggests the Vercel **Sensitive** DB URI targets a different branch, but its actual hostname cannot be read with the connector; **root cause remains unverified until endpoint guard response**.

**Correction PR candidate:** isolated branch `fix/telbot-uat-db-branch-host-guard-20261019`, `api.py` now fails closed before psycopg connection unless the URI host matches `TELBOT_UAT_DB_HOST` or its UAT direct equivalent; rejects libpq `host`/`hostaddr` URL overrides. New offline `test_uat_connection_host.py` checks UAT pooled/direct PASS, non-UAT PROD DENY, malformed/missing configuration DENY. No DB migration, credentials, webhooks, production integrations or Telegram messages touched.

**Acceptance gate:** GitHub isolated CI SUCCESS, PR merge into TelBot isolated branch, matching Vercel READY + alias, then owner retry `/ready`. If `TelBot UAT database endpoint mismatch`, **update the Sensitive `TELBOT_UAT_DATABASE_URL` in Vercel to Neon project directpilot-telbot / branch uat / database telbot / temporary role telbot_owner**, redeploy and retry. Never paste secret; do not copy schema into production. If `Telegram manager not configured`, UAT DB/schema check PASS but overall readiness still HTTP 503. Otherwise diagnose role/schema separately. Manager Bot not configured and no live outbound permitted. Checklist and six canonical docs synchronized; previous historical records retained.

---


**Verified as of 2026-10-19.** This is the authoritative action checklist for the independent TelBot project. Keep it synchronized with all six canonical files. Distinguish merge, CI, READY, HTTP verification, end-to-end acceptance and GO.

## Baseline evidence
- [x] Independent Git branch `feature/telegram-managed-bots-spike-20261017`; distinct from Instagram Production.
- [x] PRs [#64](https://github.com/namach2727-coder/Sales-Agent/pull/64), [#66](https://github.com/namach2727-coder/Sales-Agent/pull/66) and [#67](https://github.com/namach2727-coder/Sales-Agent/pull/67) merged; #67 general CI and isolated bot CI both SUCCESS.
- [x] TelBot Vercel project `directpilot-telbot-uat-api`, alias `https://directpilot-telbot-uat-api.vercel.app`; [deployment `dpl_DYjA434LnV79oYHDnXSHW36dXAL6`](https://vercel.com/mohcenp-9857s-projects/directpilot-telbot-uat-api/DYjA434LnV79oYHDnXSHW36dXAL6) READY for source SHA `bd20c44a883a4de3f57ca2f9d009b8d981519c18`.
- [x] User observed `/live` return `{"status":"live","service":"directpilot-telbot-uat"}` after routing PR #66.
- [x] Neon project `curly-cell-93038441`, UAT branch `br-tiny-poetry-arz49v2o`: `telbot` database 14 tables, latest migration `0002_webhook_auth`, 0 tenants / 0 bots.
- [x] TelBot Vercel variables present: `TELBOT_ENV=uat`, Sensitive `TELBOT_UAT_DATABASE_URL`, `TELBOT_UAT_DB_HOST`. **Presence only; cannot conclude connectivity.**

## T0 — Feasibility — COMPLETE
- [x] Official Telegram managed-bot request/event model and owner-correlation algorithm implemented offline.
- [x] Offline tenant ownership, webhook authentication, duplicate filtering and basic rule-priority tests.
- [x] No real Telegram network calls and no Production modifications.

## T1 — Isolated UAT backend — PARTIAL
- [x] Dedicated Neon UAT/Production branches; only UAT contains migrations `0001` and `0002`.
- [x] Git-linked Vercel FastAPI service with project root `experiments/telegram_bot_builder`; native `app.py` routing corrected, requirements parsing corrected.
- [x] Verified `/live` once in owner browser.
- [x] Temporary UAT-only code guard accepts `telbot_owner` or `telbot_ua_runtime` with `TELBOT_ENV`, database name and UAT table marker checks.
- [ ] **URGENT**: Test HTTP `/ready` **after** PR #67 deploy; preserve status and response. An older `503 TelBot UAT database unavailable` predates the owner-role code deploy.
- [ ] If `/ready` returns `TelBot UAT database unavailable`, investigate UAT pooled Neon host, credential, schema permissions and Vercel env without exposing secrets.
- [ ] If `/ready` returns `Telegram manager not configured`, record DB and migration checks PASS but overall readiness still HTTP 503.
- [ ] Replace temporary `telbot_owner` (CREATEDB/CREATEROLE) with dedicated least-privilege login-enabled `telbot_ua_runtime` before real customer/bot data.
- [ ] Owner creates dedicated Manager Bot with @BotFather and activates official managed-bot support.
- [ ] Add `TELBOT_MANAGER_TOKEN`, `TELBOT_MANAGER_WEBHOOK_SECRET`, `TELBOT_TOKEN_FERNET_KEY` privately to independent TelBot UAT only. Last env inventory shows these keys missing.
- [ ] Re-deploy and verify `/ready` HTTP 200; test invalid secret and auth fail closed.
- [ ] With separate owner approval: send manager keyboard, confirm ownership, replay/duplicate protection, webhook receipts and proper audited tenant isolation.
- [ ] Vault/token rotation/backup-restore, RLS/principal permissions and rate limits hardened before real credentials.

## T2 — Customer Telegram bot builder — NOT ACCEPTED
- [x] Tenant-scoped draft/publish, bot/rule APIs and offline keyboard delivery contract exist in source; **no real send**.
- [ ] Persian RTL Mini App for onboarding, bot list, greeting/fallback, buttons/menu, FAQ/keyword rule editor, Publish and preview.
- [ ] Deliver owner-approved `request_managed_bot` via Manager Bot; link one unexpired owner request.
- [ ] Retrieve managed child token server-side, encrypt/store, register child webhook, rotate/revoke credentials.
- [ ] Run published rule engine on live child updates, send replies, deduplicate updates and log failures.
- [ ] Test two real UAT tenants and bots with no cross-tenant reads/sends, real mobile UX, unauthorized actor denial and version differences.
- [ ] Record full user UAT acceptance separately from code CI.

## T3 — Optional AI and commercial release — NOT STARTED
- [ ] Lead capture, human takeover and optional AI with quota/cost controls.
- [ ] Analytics/retention, pricing and subscriptions, operator support.
- [ ] Disaster recovery, commercial hosting costs and backup restore drill.
- [ ] Explicit independent owner approval before TelBot Production or real customer operations.

## HTTP diagnostic contract
- `GET /live` should yield HTTP 200 with `status=live`.
- `GET /ready` returning `TelBot UAT database unavailable` means **DB not verified**.
- `GET /ready` returning `Telegram manager not configured` means DB/schema guard passed but Manager configuration missing.
- `GET /ready` returning HTTP 200 would verify required service dependencies, **not** full Telegram E2E.

## Continuity protocol
On every material change update this checklist AND the six canonical files: AI_HANDOFF.md, PROJECT_ROADMAP.md, DECISIONS.md, CURRENT_STATE.md, NEXT_ACTIONS.md and docs/releases/RELEASE_REGISTER.md. Keep PR/SHA/CI/Deployment/browser/owner evidence separately; never publish connection strings or Telegram tokens.


## 2026-10-28 — Private reply planner implementation checkpoint
Owner requested continued TelBot builder development. Fresh read-only Neon UAT verification recorded 1 active bot and 2 /start inbound updates, status received: inbound Telegram→Webhook→Neon PASS. Added pure private-chat reply planner with tenant/bot scope validation, bot/group/edited-message suppression, keyword/fallback/start selection and /start payload support. Focused tests: 19 PASS via system Python. This is source preparation only: not wired to live child webhook, no sendMessage transport, no deployment, no outbound acceptance, no Production changes. Next: durable outbound idempotency and transport, published-config integration, editor and live UAT verification.


## 2026-10-28 — PR #100 reply runtime follow-up (source only)
Owner authorized continuation and documentation updates. Child webhook now invokes private reply planning only for a newly inserted update, using tenant/bot-scoped published configuration and enabled priority rules. Paused/closed chat sessions suppress replies. Dedicated Fernet vault decrypts credentials internally. TELBOT_REPLIES_ENABLED=true AND TELBOT_ENV=uat are required; default remains OFF. Existing schema is reused; no migration or cloud changes. Outbound attempt is committed before Telegram network call, then sanitized sent/failed outcome is recorded. This is at-most-once attempt semantics, NOT exactly-once delivery: a crash/timeout may lose a reply and leaves an uncertain attempt; no automatic retry/recovery worker is implemented. No live Telegram send was performed.
Validation: previous 19 planner/core tests PASS. New mocked transport/gate tests added; full TelBot suite attempted but collection BLOCKED locally by missing fastapi/httpx/psycopg dependencies. Runtime/CI/live acceptance remain UNVERIFIED. Next: CI including database/concurrency and failure-path coverage, editor UI, explicit UAT enablement and owner live reply acceptance. Production unchanged.


## 2026-10-28 — PR #100 validation correction and delivery guards
Continuation authorized by owner. Prior isolated CI failed because new tests used pytest/relative imports while the workflow runs unittest discovery without pytest. Converted new tests to unittest with package-qualified imports. Installed UAT dependencies locally; exact workflow command `python -m unittest discover -s experiments/telegram_bot_builder -p 'test_*.py' -q`: 94 PASS. Added tests for inbound replay invoking runtime once, published greeting, pre-send durable commit, paused/unpublished suppression, credential bot-ID mismatch, and unknown delivery marked failed without automatic resend. Active tenant is now required by child webhook. Token identity mismatch fails closed; malformed provider JSON does not leak credentials.
Prior head dbe328c: generic backend checks PASS, isolated TelBot CI FAIL (now fixed in source); Vercel TelBot UAT rate-limited. New head CI and deployment must be separately verified. Replies remain OFF unless explicit UAT runtime flag enabled; no live sends, no Production changes. At-most-once attempt can lose messages across crashes; no exactly-once guarantee, retry worker, or queue recovery. Next: latest CI, review/merge gate, UAT deploy of exact SHA, editor/publish configuration and controlled live acceptance.


## 2026-10-28 — PR #100 basic message editor source
Added owner/editor-only Mini App form for greeting and fallback, loading current published text and explicitly saving a draft then publishing its exact ID. Close restores focus; text uses safe DOM properties; inputs freeze while saving; publish failures retain draft ID for deliberate retry. Existing configurations with keyword rules are blocked from this simple editor so their rules are not silently lost. Rules editing is NOT implemented. Script cache key updated. UI does not enable outbound service or claim live replies.
Validation: 94 TelBot unittest tests PASS; node --check app.js PASS. Visual/Telegram mobile and real save/publish acceptance UNVERIFIED. Code remains in PR #100; no merge/deploy/flag changes or live sends. Next: latest CI and controlled UAT deployment/editor acceptance, preserving disabled outbound until approved enablement.


## 2026-10-28 — PR #100 UAT release evidence and acceptance runbook
Read-only Vercel alias/deployment lookup confirmed official TelBot UAT still READY on dpl_9CpPG3S682sh1PJMN5awe2ZWmY3G / f31249005fee63017e25185fab5f533a1d6fd86f (#98), not reply/editor candidate a9da4f28. Candidate dedicated unit-test, Docker and PostgreSQL checks PASS; generic backend test still running at checkpoint. Vercel candidate status build-rate-limit; no new deployment attempted and no reply flag enabled. Added docs/telegram_bot_builder/PRIVATE_REPLY_UAT_ACCEPTANCE_20261028.md with exact baseline, separate editor/live-send gates, privacy-preserving evidence, at-most-once caveats and rollback. No claim of live editor/reply acceptance.


## 2026-10-28 — TelBot PR #100 merged after final CI PASS
Owner requested continued development. PR #100 merged ONLY into feature/telegram-managed-bots-spike-20261017 as 250fb4d3960e5a8b7095689d2363d465ab8d38ff. Reviewed head 9f5b5b7426b0f6d8c446715b3c684aab5c7da1ba: all 10 reported GitHub checks completed SUCCESS (including duplicate push/PR checks, TelBot unit-test, generic backend suites, Docker and PostgreSQL). Local TelBot suite 94 PASS. Includes greeting/fallback Mini App editor and guarded private reply runtime. No rule editor; existing rule-bearing versions cannot be overwritten through basic form.
Vercel status for merged SHA is deploying/PENDING at checkpoint; do not claim deployed until exact alias READY verification. Replies default OFF; no live send, environment flag change, schema migration or Production promotion performed. Next: verify merged deployment exact SHA and owner/editor UI save-publish on UAT, then separately approved live response acceptance. At-most-once attempts and crash/timeout loss caveats remain. Acceptance runbook: docs/telegram_bot_builder/PRIVATE_REPLY_UAT_ACCEPTANCE_20261028.md.


## 2026-10-28 — PR #100 UAT deployment VERIFIED READY
Supersedes the preceding PENDING/build-rate-limit status for this release. Read-only Vercel alias and deployment checks confirm directpilot-telbot-uat-api.vercel.app -> dpl_6SQyfMv4J5oMxdDRP6YTMvvMJXmf, READY, exact Git SHA 250fb4d3960e5a8b7095689d2363d465ab8d38ff, isolated TelBot branch/project. Basic message editor and default-disabled reply runtime are DEPLOYED to UAT. No reply flag enabled or actual outbound send performed. Owner Telegram mobile/editor save-publish and live reply acceptance are still PENDING. Do not re-deploy solely due historical quota failures. Next: owner opens fresh Mini App, uses تنظیم پیام‌های ربات to publish greeting/fallback; verify persisted version, then controlled live-send acceptance separately.

Runtime HTTP smoke after PR #100 deploy: GET /ready returned {"status":"ready","database":"available","migration":"current"}. This verifies runtime DB readiness, not editor save/publish or outbound acceptance.


## 2026-10-28 — TelBot workspace layout correction (source, release pending)
Owner reported disordered menus. Root source: bot identity/status/actions/editor shared a horizontal flex row; diagnostic/repair actions mixed with normal bot management; textarea had no form styling. UI-only patch moves My Bots first, groups bot identity/status in card header, places actions in a separate wrapping row and editor below with full-width styled textareas and separate save/close controls. Create Bot and connection diagnostics become separate native collapsible sections; secondary controls are visually distinct; mobile actions stack at <=410px; LTR usernames and keyboard focus are handled. JS/CSS asset cache keys updated.
Validation: 94 existing TelBot unittest tests PASS; node --check app.js PASS; git diff --check PASS. Connected browser unavailable (originating context missing); real Telegram/mobile visual acceptance NOT VERIFIED. No API, persistence, auth, sending flag, webhook or Production changes. Branch/PR CI, merge, UAT deploy and owner visual acceptance remain separate gates.


## 2026-10-28 — TelBot menu layout PR #101 RELEASED TO UAT
PR #101 merged to isolated TelBot branch as 626c577611b160ac8d42d4d93d2c6b1d6ee06b91 after ALL reported GitHub checks SUCCESS (TelBot suite, general backend push/PR runs, Docker, PostgreSQL). Read-only Vercel checks verified alias directpilot-telbot-uat-api.vercel.app -> dpl_3im9iWhzVuerz2DH4seAJBq44yn8, READY, exact merged SHA. New grouped bot cards, full-width editor and separate collapsed Create/Diagnostics sections are DEPLOYED. Local checks: 94 tests, JS syntax, HTML unique IDs/control targets, and diff whitespace PASS. Real Telegram/mobile visual acceptance remains PENDING; browser extension lacked originating context and local preview was disallowed by cloud browser policy. No auth/API/DB changes, reply flag enablement or live send. Owner should reopen fresh Mini App and verify card/editor, save/close and collapsed menus on device. Historical preview build-rate-limit is superseded for this merged UAT release.


## 2026-10-28 — Versioned multi-reply builder and HTTP/JSON API actions (new UAT feature)
Owner requested more than greeting/fallback and configurable API connections. Implements up to 100 ordered exact/contains keyword rules, enable/disable/reorder/remove in a new snapshot; first enabled match wins, /start remains greeting. Editor supports text or HTTPS GET/POST JSON actions, query/body, no auth/Bearer/X-header secret, selected JSON response path and explicit opt-in message forwarding. Existing rule/menu/FAQ data and archived versions are preserved; stale save/publish is rejected. Credentials are encrypted and never read back; source-rule references are tenant/bot/current-version scoped.
API adapter validates and pins public DNS destinations while retaining original TLS SNI/certificate checks, blocks internal/reserved addresses and redirects/proxies, bounds deadlines/response size, returns static errors and configured fallback; no LLM calls. Durable pre-network attempt and replay suppression cover API POST; at-most-once delivery loss limitations remain. API budget 20/bot/minute reserved with PostgreSQL lock. New TELBOT_EXTERNAL_API_ENABLED flag defaults OFF, separate from replies flag; no live provider or Telegram send performed. HTTP/JSON only, not universal OAuth/SOAP/gRPC/streaming support.
Additive migration 0003_rule_api_calls tested on separate branch br-curly-fire-ar5mdqwv cloned from verified empty parent, expiry 2026-10-29T18:00:00Z. Migration/SQL constraints+rollback smoke PASS; no UAT/Production migration applied yet. Local Python: 119 discovered, 117 PASS and 2 disposable-PostgreSQL tests skipped pending CI. Actual app.js DOM behavior PASS; JavaScript syntax/diff checks PASS. New CI PostgreSQL18 job will exercise legacy upgrade and real draft/publish storage. New feature PR, CI, merge, UAT deployment/migration and owner acceptance must be verified separately. No outbound flag/Production changes. Details: docs/telegram_bot_builder/RULES_HTTP_API_20261028.md.


## 2026-10-28 — PR #102 multi-reply/API builder RELEASED TO UAT
PR #102 merged ONLY to isolated TelBot branch as bee4a84d3686def8eca40628c2d7bc24f993365f after all 11 reported GitHub checks SUCCESS. Dedicated TelBot job: 117 Python cases PASS, 2 PostgreSQL cases skipped there; separate PostgreSQL18 schema-test ran both skipped cases PASS (real legacy upgrade and HTTP snapshot/publish/secret retention). Actual app.js DOM behavior PASS. No real provider/Telegram calls or mobile visual acceptance claimed.
Read-only Vercel verification: official TelBot UAT alias -> dpl_DdZH5HGsp9wKri61GTtwsYbopLLA, READY, exact merge SHA bee4a84d. Code deployed FIRST with 0002-compatible fallback, then checked-in additive migration 0003_rule_api_calls applied atomically ONLY to Neon UAT br-tiny-poetry-arz49v2o/telbot with bounded lock/statement timeout. Pre/post transaction fingerprints and counts PASS: one active bot, four configuration versions, published version 4 preserved byte-equivalently; no rule or customer configuration added/changed by migration. Independent test branch remains expiring 2026-10-29T18:00Z. TelBot Production parent remains untouched.
Vercel environment metadata confirmed TELBOT_REPLIES_ENABLED and TELBOT_EXTERNAL_API_ENABLED absent, hence default OFF. Neither flag changed. API settings UI is available after schema migration; actual provider connectivity requires owner-chosen API contract/key entered privately and separate controlled live acceptance. Post-migration HTTP checks PASS: /ready 200 ready/database available/migration current, /telbot 200 and versioned JS/CSS 200 with new rule editor, unauthenticated config endpoint 401. Owner mobile/editor and real provider acceptance remain PENDING. Updated runbook docs/telegram_bot_builder/RULES_HTTP_API_20261028.md. Instagram Production unchanged.


## 2026-10-28 — PR #103 response preview merged; UAT deployment quota blocked
PASS: authenticated owner/editor preview; cross-tenant/bot/viewer denial; unsaved greeting, ordered/disabled/normalized rules and fallback; no credential reads/configuration writes/provider calls even with flags ON; body-redacted validation; DOM credential omission/plain text/stale result suppression/single publish. MERGED and CI PASS; UAT deployment BLOCKED by Vercel build quota; mobile and live-provider acceptance PENDING.
PR #103 reviewed head dfac4cb9c52d77379b926e7885ecfd0d80103a51 passed all 11 reported GitHub checks, including dedicated TelBot unit/DOM, PostgreSQL18 schema and both generic backend runs. Squash merge c08a3c26422ad2d28036946c274b035216fff8c0 ONLY into feature/telegram-managed-bots-spike-20261017. Python: 123 cases PASS in unit job plus 2 PostgreSQL cases PASS in schema job (125 unique); actual app.js DOM PASS. Standalone Vercel-style import PASS. Vercel rejected this exact merged SHA with "Deployment rate limited — retry in 24 hours." No new TelBot deployment exists; official alias remains READY on PR #102 bee4a84d3686def8eca40628c2d7bc24f993365f / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA. Preview is MERGED, NOT LIVE. No repeat deployment, upgrade, flag change, migration or saved customer-setting mutation performed. Owner mobile/preview/provider acceptance remain separate and pending.

Final read-only checkpoint 2026-10-28 18:09 UTC: official alias still points to dpl_DdZH5HGsp9wKri61GTtwsYbopLLA; /ready 200 (database available/migration current), /telbot and published JS 200 show rules-api-3 and no preview control/cache revision. Vercel environment metadata has six keys and neither outbound flag. This verifies the prior live release remains healthy, not deployment of PR #103.
