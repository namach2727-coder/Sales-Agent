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

Save must keep its direct click handler, immediate footer feedback and shared guarded submit path. Do not revert to external native form association. Match persisted ID/version/greeting/fallback/ordered rules before success or replacing the form; preserve typed text on failures. Keep mobile-first/focus invariants. The CI real UI/HTTP/disposable-PostgreSQL save/reopen gate is mandatory evidence; never manufacture acceptance by editing live customer settings.

PR #106 reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc passed all 11 reported GitHub checks. Squash merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 ONLY into feature/telegram-managed-bots-spike-20261017 exactly matches the reviewed tree. Vercel dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9 is READY on that merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The project target label production is the isolated TelBot UAT service, not business Production promotion.

Verified 2026-10-29 13:15 Asia/Tehran / 09:45 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, save-click-1 revision, unauthenticated synthetic preview POST 401. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS, including the actual JS UI through HTTP/FastAPI/PostgreSQL add-save-close-reopen twice (3 versions total, 2 current replies, duplicate-submit guard). Both DOM behavior/focus and 5 save-error/readback scenarios PASS. Read-only UAT after deployment still shows published v4, 4 versions total and 0 rules; no customer configuration was written by deployment/testing. Both outbound flags remain absent/default OFF. Actual owner phone Save acceptance remains PENDING.

---

## 2026-10-29 — CURRENT PR #105 mobile-first layout: UAT READY

Owner requirement: mobile is the baseline. Preserve 320/360/390/430px sizing, minimum 48px touch areas, 16px input text, safe-area padding and focus-stable input ancestors. Use fluid widths/zero-minimum grid tracks; desktop spacing is opt-in from 600px. Do not replace this with desktop-first overrides or viewport/focus workarounds. Full evidence: docs/telegram_bot_builder/MOBILE_FIRST_20261029.md.

PR #105 reviewed head 01f5b47681020187026cd704c0a5803dd04fb05f passed all 11 reported GitHub checks. Squash merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 ONLY into feature/telegram-managed-bots-spike-20261017 has the exact reviewed tree. Vercel dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh is READY on that exact merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The Vercel target label production belongs only to this isolated UAT project; business Production was not promoted.

Verified 2026-10-29 11:31 Asia/Tehran / 08:01 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, mobile-first-1 revision, unauthenticated synthetic preview POST 401. Dedicated CI: 123 Python PASS plus 2 PostgreSQL cases PASS in schema-test, and actual app.js DOM/focus behavior PASS. Offline review: basic text/API states (176 controls) plus expanded reply settings/POST-message-forwarding states (216 controls), each at 320/360/390/430 CSS px; no horizontal control/container overflow or button/disclosure target below 48px. PNGs reviewed. This approximate document renderer does not establish native OS dropdown, Telegram safe-area, keyboard or real-device acceptance. Owner phone acceptance remains PENDING. Both outbound flags remain absent/default OFF; no backend, stored customer setting, migration, secret or live-send changes.

---

## 2026-10-29 — CURRENT PR #104 editor usability and typing fix: UAT READY

Preserve input ancestors while typing/composing: update captions without moving cards. Guard list refresh while any reply editor is open. Maintain the persistent three-tab DOM, optional technical settings, hidden-field validation and unsaved-close guard. Full evidence: docs/telegram_bot_builder/EDITOR_USABILITY_20261029.md.

PR #104 merged ONLY into feature/telegram-managed-bots-spike-20261017 as 17b2545849f8391291f14a46a7b6c18ed443ab22 after all 11 reported GitHub checks SUCCESS on reviewed head b45bdf9b0985464f3621a5792c17d9b62b4730b6. Merge tree exactly equals the reviewed tree. Vercel deployment dpl_DZDzon4PcrDYzGfvLa8rEP9VqJFD is READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. This project target label production is the isolated TelBot UAT project, not business Production.

Verified 2026-10-29 10:57 Asia/Tehran / 07:27 UTC: /ready 200 ready/database available/migration current; HTML, JS and CSS 200 and byte-identical to the reviewed local assets (20261029-editor-ux-1); unauthenticated synthetic POST /preview 401 missing_init_data. Dedicated CI ran 123 Python cases PASS, with the other 2 PostgreSQL cases PASS in schema-test; actual app.js DOM behavior/focus regression PASS. Both outbound flags remain absent/default OFF. No schema, stored customer-setting, credential, provider-call or Telegram-send change. Owner real Telegram/iOS keyboard and visual acceptance remains PENDING.

---

## 2026-10-29 — CURRENT TelBot checkpoint: PR #103 deployed to UAT

This checkpoint supersedes the historical 2026-10-28 preview deployment quota blocker. Vercel directpilot-telbot-uat-api / team_Cu7IBomJgSNCXUMp3sILUUD4 is READY on dpl_Hy4hsuSi9PzhGNLcoZsqCDejkdYY, exact reviewed merge c08a3c26422ad2d28036946c274b035216fff8c0. Canonical alias https://directpilot-telbot-uat-api.vercel.app points to this deployment. The project target label production belongs ONLY to this isolated UAT project; it is not a business Production promotion.

Preview is now live on UAT. Preserve its invariant: evaluate the submitted unsaved snapshot with the shared matcher; only tenant-role/bot-identity reads, no saved credential reads or configuration writes, and no Telegram/API calls. Do not repeat deployment because of the older quota notes. Detailed evidence: docs/telegram_bot_builder/RULES_HTTP_API_20261028.md.

Verified 2026-10-29 06:52 UTC (10:22 Asia/Tehran): /ready 200 ready/database available/migration current; /telbot 200 with response-preview-1 asset revision; JS 200 with preview and multi-rule controls; CSS 200 with preview layout; POST /preview with a synthetic body and no Telegram session returns 401 missing_init_data. Environment metadata still has six keys; TELBOT_REPLIES_ENABLED and TELBOT_EXTERNAL_API_ENABLED are absent/default OFF. No migration, customer-setting mutation, Telegram send, API-provider call or billing change performed. Owner mobile/preview interaction and live provider acceptance remain PENDING.

---

2026-10-28 TelBot UAT managed child activation (isolated feature, NOT YET deployed): owner reports Telegram managed bot successfully created, dashboard status pending. Read-only Neon UAT confirms one managed bot status pending and encrypted credential present. Add owner-only POST /api/v1/tenants/{tenant_id}/bots/{bot_id}/activate-managed, restricted to TELBOT_ENV=uat and exact Tenant+Telegram owner+managed request+pending+encrypted credential. Server decrypts token internally, verifies getMe identity, refuses to overwrite webhook pointing elsewhere, uses setWebhook with independent random secret and allowed_updates ['message'], preserves pending events, verifies getWebhookInfo URL, then stores SHA-256 secret digest and changes status to active. Client offers explicit activation button only to owner for credential-ready pending bots. Synthetic tests cover auth, token secrecy, successful verify and missing credential. Existing child webhook accepts verified inbound messages and deduplicates updates; **automated reply/sendMessage is not implemented and must not be claimed PASS**. Live activation requires explicit owner click after CI and UAT deployment. No manual DB edits, no new bots, no Instagram Production changes. No Telegram token disclosed.

2026-10-28 TelBot UAT: user confirms webhook buttons still appear ineffective even after PR95 release (commit e6b77837, GitHub Vercel status SUCCESS). Source review confirmed `bots-list` empty-state text is independent of global top `notice`; webhook handler messages only target global notice, potentially invisible when scrolled to buttons. Isolated patch creates `manager-webhook-status` aria-live text immediately beneath webhook controls, populated synchronously on click and on API success/failure, showing HTTP error and independent of connected-bot list. Cache-busted Mini App script v20261028-inline-webhook-3. Prior linkage failure remains: Neon UAT had no linked bots and no manager inbound updates; official Telegram webhook configuration NOT verified. PR, CI, merge and deployment must be verified separately. No DB mutation, webhook action automation, or DirectPilot Instagram Production changes.

2026-10-27 TelBot UAT: owner reports both webhook diagnostic/repair controls visually present but taps inert. Code review found Mini App script URL unversioned (/telbot/app.js, possible stale Telegram WebView cache) and both handlers returned silently when activeTenant missing. Isolated patch adds versioned JS asset URL, immediate progress feedback and explicit missing-tenant error; no webhook mutation is triggered by this patch. Live verification pending CI, merge, Vercel UAT deployment and owner's click test. Previous 4 expired requests/zero linked bots remain unresolved; no Production changes.

> **2026-10-27 TelBot UAT Webhook root-cause investigation (unreleased):** Owner confirmed child managed bot creation on Telegram mobile but Mini App lists zero bots. Direct read-only Neon TelBot UAT branch showed 4 expired `managed_bot_requests`, 0 rows in `bots`, 0 `manager_inbound_updates`; PR #92 revision `30340763` deployed READY. Vercel TelBot project has `TELBOT_MANAGER_TOKEN`, `TELBOT_MANAGER_WEBHOOK_SECRET`, and UAT DB settings, but **presence is not proof of actual Telegram setWebhook**. Official Bot API sends `managed_bot` updates if configured. Added UAT-only owner-authenticated read-only `getWebhookInfo` diagnostic returning safe categorical fields and guarded explicit `setWebhook` action against exact UAT manager webhook URL, only if Telegram currently has no webhook or it already matches; requires valid configured secret, subscribes `message` and `managed_bot`, never drops pending updates. No secret disclosure, Production modification, or auto-linking by username. PR CI, deployment, live diagnostic and historical bot ownership repair remain pending. An expired request must not be auto-relinked without live owner validation.

> **2026-10-27 | TelBot UAT managed-bot native private-chat request (under review):** Owner reports Telegram Create Bot tap remains inert after fixing pending request; a retry/deploy alone is not an acceptance test. Official Telegram Bot API supports reply keyboard `KeyboardButton.request_managed_bot` exclusively in private chats for bots with Bot Management Mode enabled. New branch `feature/telbot-native-keyboard-20261027` adds owner-only, request-scoped `POST /api/v1/tenants/{tenant_id}/managed-bot-requests/{request_id}/send-keyboard`, with HMAC Mini App auth, Tenant owner validation, request ID+owner+unexpired pending filter, and Telegram manager `sendMessage` using native managed-bot request. UI prefers this native private-chat button; deeplink remains fallback. Tests mock Telegram; no token disclosure, Neon migration, webhook activation, or Instagram Production changes. CI/Merge/UAT/live Telegram acceptance PENDING. User must have opened/started the manager's private chat and enabled Bot Management Mode. If client Create Bot still inert, inspect Telegram version/platform and permissions; never mark actual child-bot creation as passed from message delivery alone. Prior PR #91 cancel-pending is separate and its release status must be checked.

> **TelBot UAT — managed creation deep-link UX bug (2026-10-26):** Owner opened creation link after entering business name and bot username but screenshot showed generic `https://t.me/DirectPilotManagerBot?utm_source=chatgpt.com` bot preview with inert Start Bot / Open in Web. This is NOT proof of a successful `/newbot/{manager}/{username}?name=...` invocation, and bot creation/credential preparation remain PENDING. Telegram documentation confirms official `https://t.me/newbot/{manager_bot_username}/{suggested_username}?name={suggested_name}` syntax and requires active Bot Management Mode. Follow-up fix changes client click navigation to `Telegram.WebApp.openTelegramLink(full_creation_url)` inside Telegram Mini App (browser fallback remains a normal link) and removes forced new-tab target. Check CI, merge, UAT deployment SHA, and real in-Telegram creation dialog; do not mark live PASS on screenshot alone. PR #88 refresh enhancement previously CI PASS and merged `bbeaab6e75b9921a62a35a05b44e44e388e73764`; this change is a separate PR. No credential exfiltration, token rotation, Neon migration, or Production deploy.

> **TelBot UAT progress checkpoint — 2026-10-26:** PR #87 merged as `402e5b47e0f40496f3e0366b97c1eab45ad1b4eb`; all three CI PASS and Vercel `directpilot-telbot-uat-api` deployment SUCCESS. The server-side getManagedBotToken + encrypted vault change is published to UAT, **not yet customer-accepted**. Manual successful Telegram managed bot creation, manager-bot mode, managed update delivery, credential vault persistence and webhook activation are NOT yet verified. New follow-up patch adds an explicit `refresh-bots` control and refresh on return to the Mini App, so owners can see created bots without closing the app. This patch is pending CI, merge and UAT deploy; do not claim it live until verified. Telegram owner confirmation is mandatory; customer API tokens remain absent from onboarding. No Instagram Production / Neon migration / child webhook activation. Next gate: confirm manager bot management mode, run a real owner-confirmed managed creation, refresh, check pending row and credential readiness, update evidence.

> **2026-10-26 — TELBOT MANAGED CREDENTIAL PREPARATION (UAT-only, new PR, release pending)**
>
> **Prior milestone:** PR #86 merged `e00f61034fe05577125603f737aa886f84ad6f80` after 3/3 CI PASS. Vercel TelBot UAT deployment check SUCCESS. Owner has previously verified login and workspace creation, but has **NOT** yet user-tested new managed bot creation. No Production TelBot or Instagram release approved.
>
> **New implementation:** After owner confirms a Telegram Managed Bot using official deep link, existing manager webhook stores a tenant-bound pending record. On subsequently loading the UAT Mini App bot list, the owner session triggers backend-only `POST /api/v1/tenants/{tenant_id}/bots/{bot_id}/prepare-managed-credential`. Endpoint enforces Mini App HMAC, tenant owner role, exact bot/tenant/Telegram owner ID, `managed_request_id` presence, `pending` status, dedicated Fernet key availability and row lock. Calls Telegram Bot API `getManagedBotToken(user_id=<managed bot id>)` over server-side HTTPS, checks returned token bot ID, encrypts it using `TELBOT_TOKEN_FERNET_KEY`, persists ciphertext, never returns the token, and is idempotent on stored credentials. The user does not enter BotFather token. This phase **does not register webhooks, send messages or activate bot**.
>
> **Safety/acceptance:** Offline mocked tests for token API identity, failure sanitization, owner/tenant isolation and encrypted idempotent storage; do not log raw credentials. New PR's CI, merge SHA, Vercel deployed SHA, Bot Management Mode eligibility, real managed creation, Telegram token fetch, persistent tenant row and user UAT acceptance are **PENDING** unless confirmed by release evidence. Failed retrieval remains `pending` and is retried on future UAT page load (not looped indefinitely). Follow-up milestone: child webhook configuration and staged activation only after explicit acceptance. Support-only legacy manual token endpoint is not in customer UI. Historical evidence preserved.

> **2026-10-25 — TELBOT MANAGED-BOT SELF-SERVICE IMPLEMENTATION (PR #86, UAT-only; verify CI/deployment before accepting)**
>
> **Owner decision:** Customers must NOT use BotFather to copy/paste an API token. Primary onboarding is official Telegram managed-bot creation via `https://t.me/newbot/DirectPilotManagerBot/<suggested_username>?name=<URL-encoded name>`, after owner creates a TelBot workspace. Telegram requires user confirmation; automated creation without consent is not supported. Official references: https://core.telegram.org/api/bots/managed-bots and https://core.telegram.org/bots/features#managed-bots.
>
> **PR #86 scope:** UAT Mini App now collects display name and bot username, POSTs to existing owner-only `/api/v1/tenants/{tenant_id}/managed-bot-requests`, receives a short-lived request and a safe creation URL, and shows explicit Telegram confirmation link. No customer API token input or frontend credential persistence. Existing manager webhook's `managed_bot` event logic links the new bot to the matching sole unexpired request as `pending`. Legacy manual token endpoint is retained strictly as backend support fallback, not exposed in customer UI. Existing 15-minute TTL / per-owner uniqueness / tenant ownership / webhook signature / dedupe guard remain.
>
> **Important capability boundary:** A successful Telegram managed-bot creation event stores identity and pending bot record. Automatic `getManagedBotToken` retrieval and secure background management are NOT implemented or accepted by this UI change; production rollout and messaging/webhooks remain blocked pending service credential handling, tests, and owner approval. Manager Bot Management Mode must be enabled in BotFather and validated live.
>
> **Evidence and rollout gates:** PR #84 HMAC sign-in fix previously deployed UAT and owner reported Mini App opening and workspace creation PASS. PR #86 code committed on `feature/telbot-managed-bot-self-service-20261025`; CI/merge/deployment/live managed creation = PENDING until separately verified. Next: CI; merge into isolated TelBot UAT branch; confirm Vercel deploy SHA; user tests Telegram official confirmation; confirm pending bot row and tenant isolation; implement safe token retrieval/activation separately. Do not mark Instagram Production deployed. Preserve earlier PR #76–#85 history and release states.

# DirectPilot development instructions

## Canonical release documentation / cross-chat continuity (2026-10-15)

- Before modifying DirectPilot or suggesting promotion, read the **current** five concise files `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`; then `docs/releases/RELEASE_REGISTER.md` and relevant dated runbook. Do not rely on an earlier chronological heading or require owner to re-explain signed-off documentation decisions.
- For EVERY new PR/deployment, update the matching Release Register row with PR number, exact Git ref/SHA, deployed alias/environment, UAT status, Production status, customer acceptance, and evidence. No `CI PASS`/`READY` implies real UAT end-to-end or Production business signoff.
- Never merge the entire Frontend UAT branch to Production main. Two live frontend aliases are separate; backend Vercel UAT/Neon UAT is separate from authoritative Production Render DB/API.
- Neon UAT currently has eight `saas_plans`; only `AUTOMATION_V1`/`AI_ASSISTANT_V1` are purchasable, only `AUTOMATION_TRIAL`/`AI_ASSISTANT_TRIAL` are newly trial eligible (three days). UAT prices do not establish Production DB values. Frontend multi-source DM/Story/Comment makes a separate backend automation rule per selected source, each consuming capacity.
- Owner mandates PostgreSQL BYTEA for all product images and receipt versions, **no R2/S3**, four-month or longer customer-level traceability, obvious mobile Back/Close. Do not misrepresent schema/CI as browser acceptance or independent backup guarantee.
- **Preserve evidence:** original full five canonical docs and supporting AGENTS/PAYMENT_FLOW are archived byte-for-byte at `docs/runbooks/history/20261015_pre_release_register/` and in Git; never remove. Current docs are intentionally concise and supersede chronological status notes in those archives.
- For this **documentation-only** release, Render Production API autodeploy is verified `no` and autoDeployTrigger `off`; nonetheless do not trigger Render deployment, modify production env, data, DNS, Meta, pricing, customer subscriptions, or payments. Production cutover requires separate explicit owner GO.

## Working method

- Inspect `git status` first. Preserve unrelated dirty work and stage intended paths explicitly.
- Search narrowly with `rg` before opening files; read only relevant ranges and follow callers/imports only as needed.
- During implementation, run focused tests. Run the full backend suite once before release when the change or release gate requires it.
- Ignore generated and dependency trees such as `.git`, virtual environments, caches, build output, and temporary test databases during searches.
- Keep final reports concise and preserve verified findings when context becomes tight.

## Git and release safety

- Never use `git reset`, `git clean`, automatic stashing, force push, or published-history rewrites.
- Do not mutate Git state unless the user explicitly authorizes it. A release authorization applies only to the reviewed files and named branch.
- Distinguish local validation, pushed state, deployed state, and cloud UAT. Correlate releases with the exact commit SHA and runtime version evidence.

## Security and authorization

- Never print, persist in the repository, or place in logs/tests/docs any credential, bearer/session token, Meta token or secret, LLM API key, database credential, encryption key, or customer content.
- Tenant/store isolation is mandatory. Derive tenant context from trusted authentication and enforce authorization server-side; fail closed when context or entitlement is absent.

## Runtime invariants

- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256`; do not raise them to mask prompt or context defects.
- A successful deterministic automation rule performs zero LLM calls, PromptBuilder calls, knowledge retrieval, AI usage, and token usage.
- Run AI only when the `ai_assistant` entitlement permits it. Human takeover (`human_active`) suppresses both automation and AI.
- Preserve deduplication and echo/loop protection on every inbound and outbound path.

## Migration safety

- Prefer additive, forward-only migrations. Preserve historical orders, subscriptions, automation rules, knowledge, and AI usage.
- Never perform a destructive migration without explicit approval. Validate migrations on a fresh temporary database, never `sales_assistant.db`.


## Non-negotiable customer receipt traceability (2026-10-14)

Every manual payment receipt must remain attached to customer identity and its original tenant, store, order, payment, timestamp, checksum and admin event sequence. Must permit privileged search and recovery even after four months and preserve previous uploads when rejected receipts are replaced. Pending UAT PR #36 / Alembic 0027 implements append-only receipt-version evidence within PostgreSQL BYTEA; **NOT yet deployed**. No age-based purge or silent overwrite; backup/restore verification, permission tests and admin UI are acceptance requirements. Proposed 12-month operating retention is subject to valid privacy policy and recoverable backups. Do NOT choose R2/S3 or ask user to repeat this requirement.

## Current owner-approved media architecture (2026-10-14)

- DirectPilot payment receipts ALREADY use PostgreSQL `manual_payments.receipt_data` (BYTEA). Product JPEG media MUST also use durable PostgreSQL `product_media_assets.image_data` (BYTEA) once UAT feature PR #34 and additive Alembic 0026 pass review/migration. No R2/S3 provider is approved: experimental PR #33 was closed WITHOUT MERGE. Do not recreate buckets, suggest cloud storage, require credentials or route images to ephemeral Vercel disk unless the owner explicitly changes the decision.
- Media quotas for new JPEGs: 2 MiB decoded per image and 50 MiB active images/store. UAT and Production Neon projects are separate; never apply 0026 to real database or deploy ORM before approved UAT backup/migration/test. Rendering receipts or static HMAC links must preserve authorization and expiry; no real Meta sends during UAT.
- For cross-chat continuity, read `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md` IN THAT ORDER. If they conflict with verified deployments/DB state, verify reality; keep docs updated. The owner should never have to repeat this storage or separation policy.

## DirectPilot Product and Architecture Guardrails

These rules apply to every repository task:

1. DirectPilot is an AI Sales Assistant, not a generic Instagram bot.
2. Instagram through official Meta APIs is the only MVP communication channel.
3. Preserve Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, REST, and the Modular Monolith.
4. Do not introduce microservices during MVP; keep module boundaries extractable.
5. Enforce trusted tenant context and isolation on every tenant-bound operation.
6. Prefer configuration for business variation while keeping domain invariants explicit.
7. Stay cloud-ready without adding cloud services or machine-specific assumptions prematurely.
8. Redis, RabbitMQ, and S3-compatible storage are possible future providers, not mandatory current dependencies.
9. Do not implement marketing engines, CRM, other channels, or future Foundations early.
10. Forever Free means 20 successful automatic replies per tenant calendar day, reset in the tenant timezone; failed/manual/unapproved Shadow Mode replies do not consume quota.
11. AI answers only from approved business knowledge and must not fabricate.
12. The canonical [DirectPilot blueprint](docs/blueprint/AI-Commerce-Platform-Blueprint.md) overrides external prompts and generic architecture recommendations.
13. Every implementation stays inside its active Foundation; FOUNDATION-06 covers only the Lean Business Catalog.
14. Do not claim scalability, test success, or provider support without evidence.
15. Preserve foundation boundaries and do not implement future capability merely because its architecture is documented.
16. Treat public UUID-style identifiers as API boundaries and internal numeric identifiers as persistence details.


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
Preview invariant: evaluate an explicit unsaved snapshot with the shared runtime matcher. Endpoint reads tenant role/bot identity only; do not load saved credentials, write configuration versions, or call Telegram/API. API preview identifies rule/failure fallback without claiming a provider response.
PR #103 reviewed head dfac4cb9c52d77379b926e7885ecfd0d80103a51 passed all 11 reported GitHub checks, including dedicated TelBot unit/DOM, PostgreSQL18 schema and both generic backend runs. Squash merge c08a3c26422ad2d28036946c274b035216fff8c0 ONLY into feature/telegram-managed-bots-spike-20261017. Python: 123 cases PASS in unit job plus 2 PostgreSQL cases PASS in schema job (125 unique); actual app.js DOM PASS. Standalone Vercel-style import PASS. Vercel rejected this exact merged SHA with "Deployment rate limited — retry in 24 hours." No new TelBot deployment exists; official alias remains READY on PR #102 bee4a84d3686def8eca40628c2d7bc24f993365f / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA. Preview is MERGED, NOT LIVE. No repeat deployment, upgrade, flag change, migration or saved customer-setting mutation performed. Owner mobile/preview/provider acceptance remain separate and pending.

Final read-only checkpoint 2026-10-28 18:09 UTC: official alias still points to dpl_DdZH5HGsp9wKri61GTtwsYbopLLA; /ready 200 (database available/migration current), /telbot and published JS 200 show rules-api-3 and no preview control/cache revision. Vercel environment metadata has six keys and neither outbound flag. This verifies the prior live release remains healthy, not deployment of PR #103.
