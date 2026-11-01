## 2026-11-01 — CURRENT: own portfolio/inquiry bot LIVE; website source merged, publish QUOTA BLOCKED

Owner replaces the public universal/no-code bot-builder with OUR OWN DirectPilot Bot Studio: curated business ideas, explicit demos, custom-development inquiries and owner follow-up. Generic workflow/payment/panel development is deferred; historical code/configurations remain preserved. Existing owner test bot https://t.me/tetsteee1bot is repurposed as our showcase, not newly created or renamed in BotFather. Native profile/username branding and actual phone/Telegram notification acceptance remain PENDING.

Backend PR #127 https://github.com/namach2727-coder/Sales-Agent/pull/127: reviewed 88ae302e8e04ab39627896742e492063a1a9b6cb, all 11 checks SUCCESS; squash merge 9e82353fddfebfa7161fba6905a25bf306d7117c only isolated TelBot branch; reviewed/merged trees match. Automatic UAT deployment dpl_CEqktcsxdKDa63uceerNpysYgnTi READY at exact merge. Additive 0004_showcase_inquiries applied only Neon curly-cell-93038441 / br-tiny-poetry-arz49v2o / telbot after real PostgreSQL CI. One explicitly enabled registered-owner bot; TELBOT_SHOWCASE_ENABLED=true only isolated UAT production target. Existing replies ON, external API actions OFF; 1 active bot and published v6 preserved. Latest confirmed inquiries count 0; no synthetic request or real customer content inserted into UAT by testing.

Verified /ready 200 database available/migration current; /showcase, its JS/CSS and manager Mini App HTML/JS 200 and byte-exact source. Public catalog 200 with 24 categories and actual bot link; unauthenticated private inbox 401 missing_init_data. Cloud browser visually verified desktop portfolio, search input focus/results, modal simulated selection and category-specific Telegram link. Telegram's public page was unavailable from cloud browser; this does NOT establish bot failure or live Telegram delivery. Physical mobile/native acceptance remains separate. Local 157 Python discovered = 151 PASS + 6 PostgreSQL skips; dedicated CI ran the 6 PostgreSQL cases PASS, including migration, persistent inquiry flow, duplicate suppression, encrypted records, unknown notification outcome and owner-only inbox. DOM/editor/Save/showcase tests PASS.

Website PR #73 https://github.com/namach2727-coder/directpilot-web/pull/73: reviewed 663378bee2d0e5d417f3becccfb79d254e125996, both validate/verify SUCCESS; squash merge 957d4c46fd448b40e97e8b89094c30792c79ea19 to website main, identical reviewed tree. 287 tests, TypeScript, full lint (3 existing warnings) and production build PASS. Includes minimal pre-existing SEO loading-effect lint fix to permit CI; no auth/API redesign. New /telbot custom service, 24 category links, homepage/subnav and neutral former checkout; historical proposed tiers no longer shown. Publication request rejected HTTP 402 api-deployments-free-per-day (more than 100; retryAfter 86400). NO new website deployment created. directpilot.ir remains prior READY 4451e50916b5c58ba0b55b303362ff37fd04227e / dpl_J8Ux4SBhPWctAvZZ5ShQJzpP2BB9. Do NOT claim new website links live. No CLI quota workaround, hosting/audience change, billing upgrade or repeated retry planned.

NEXT: owner can inspect live https://directpilot-telbot-uat-api.vercel.app/showcase and test /start + category/demo/need/contact/review/Confirm in existing bot; check saved code, owner notification and private inbox. Finalize professional BotFather branding separately. When Vercel quota permits, deploy exact reviewed website merge ONCE to existing directpilot-web, verify canonical /telbot and bot links, then record deployment; no new retry automation created. Business backend Production, payments and Instagram runtime unchanged. Full runbook: docs/telegram_bot_builder/OWN_SHOWCASE_BOT_20261101.md. This checkpoint supersedes the generic builder/transaction engine next steps below without deleting history.

---

| Release | Reviewed / merge | Deployment | Acceptance |
| --- | --- | --- | --- |
| TelBot #127 own portfolio/inquiry runtime | 88ae302e8e04ab39627896742e492063a1a9b6cb / 9e82353fddfebfa7161fba6905a25bf306d7117c | UAT LIVE dpl_CEqktcsxdKDa63uceerNpysYgnTi; schema 0004; one own bot enabled | Browser/CI PASS; native Telegram/mobile notification PENDING |
| Website #73 custom-development portfolio/link | 663378bee2d0e5d417f3becccfb79d254e125996 / 957d4c46fd448b40e97e8b89094c30792c79ea19 | SOURCE MERGED; Vercel daily publication quota BLOCKED; current site still 4451e509 | 2 CI checks / 287 tests PASS; new production page NOT LIVE |

## 2026-11-01 — CURRENT OWNER PIVOT: our portfolio bot + custom development inquiries

Owner explicitly replaces the customer-facing universal/no-code builder with DirectPilot's OWN service-discovery/portfolio Telegram bot. Prospects choose a business category, try clearly simulated examples, describe a need, optionally give contact, review/consent and Confirm; then the registered owner receives a notification and scopes/builds each project. Website links to this bot. This supersedes the generic workflow designer/payment/panel engine next steps below; prior code/configuration/evidence are retained as history and internal assets, not deleted. No AI or universal/API support claim.

New source: /showcase mobile-first Persian portfolio, 24 curated categories + demos, deterministic private Telegram conversation, additive 0004 scoped encrypted session/inquiry/delivery records, owner notification and owner-only last-30 inbox. Flag defaults OFF; only explicitly enabled own bot changes behavior. Confirmed requests persist before sends, unknown notifications remain visible without blind retry; no guaranteed delivery/exactly-once claim. Native phone/Telegram acceptance is separate from tests. Legacy inbound message text policy still applies; new ciphertext is not whole-database encryption.

Implementation/local validation, CI, UAT migration/activation, exact deployment, website release and owner acceptance are separate gates; do not infer completion. Existing sole active UAT test bot has ready credentials/registered active owner; reusing it is not creation or renaming of a new BotFather account. External APIs remain OFF, business backend Production untouched. Runbook: docs/telegram_bot_builder/OWN_SHOWCASE_BOT_20261101.md.

---

## 2026-11-01 — CURRENT: synthetic service-sales prototype #119 LIVE in isolated UAT

PR https://github.com/namach2727-coder/Sales-Agent/pull/119 reviewed head 1f3a2a44f5af8fdee4a653a7463a71fa44db99c5 passed all 11 checks. Squash merge b18514a08e55d5c2c330eaebe263d3a7bfd83502 ONLY into feature/telegram-managed-bots-spike-20261017 has identical reviewed tree dc88b555f4ff01de6336976479234ea235ccba70. Automatic deployment dpl_45WCEywF5XqqdJVQhFcXahbNyrVv is READY on the exact merge and owns canonical https://directpilot-telbot-uat-api.vercel.app. This is the isolated TelBot UAT project; business Production was not promoted.

Verified release: /ready 200, database available, migration current; /telbot and both assets 200 and byte-identical to reviewed source, cache revision 20261101-service-flow-preview-1. New service-flow-preview POST with synthetic IDs and no authentication returns 401 missing_init_data. Read-only Neon UAT metadata: 1 active bot, 0 paused, published version 6. No schema migration, customer configuration/status change, secret retrieval, external API flag change, actual provider/payment/account or Telegram send performed for this release. Ordinary replies remain enabled; external API calls remain disabled.

CI unit job 124781995713: 150 discovered, 145 PASS + 5 PostgreSQL skips; schema job 124781995908: all 5 PASS including real UI/FastAPI/PostgreSQL sample with editor identity/focus and existing configuration counts preserved. Both DOM/editor and seven Save scenarios PASS. Initial schema fixture focus expectation was corrected after report Close deliberately focused its opener; the final reviewed head passed. Native owner phone acceptance remains PENDING.

Owner/editor can open «نمونهٔ فروش و تحویل سرویس» and explicitly run paid, unconfirmed, amount-mismatch or lost-response scenarios. Fixed fictional prices, inert checkout text and invalid DEMO account/config; simulation=true, live_actions=false. Engine is IN-MEMORY and customer Telegram runtime is NOT connected to it. This release does not deliver actual VPN/payment/checkout accounts, a generic workflow designer, or durable cross-restart idempotency. No AI is implemented. Owner chose a synthetic engine/sample because no panel exists yet; private reference-bot behavior and latency remain unverified.

NEXT: implement versioned mobile no-code steps and durable scoped orders/runs/operation ledger with encrypted sensitive data; then integrate actual documented panel and verified payment adapters with reconciliation, and private Telegram delivery. Real sandbox acceptance requires the eventual panel/gateway contract. See docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md for gates. Do not wire this prototype to live commerce as-is.

---

| PR | Reviewed / merge | UAT | Production | Acceptance |
| --- | --- | --- | --- | --- |
| #119 synthetic service-sales engine and owner sample | 1f3a2a44f5af8fdee4a653a7463a71fa44db99c5 / b18514a08e55d5c2c330eaebe263d3a7bfd83502 | LIVE READY dpl_45WCEywF5XqqdJVQhFcXahbNyrVv; exact assets/auth/health PASS | Not promoted | Owner mobile sample pending; real panel/payment not implemented |

## 2026-11-01 — CURRENT: owner directs transactional service bot builder; synthetic prototype (release pending)

Owner clarified target: a no-code bot capable of server-connected service sales, checkout, verified payment, account creation and configuration delivery, using a VPN seller as an example. Current TelBot has NO AI. Private behavior/source/latency of @sadshekanvpnbot was not observed; only public profile plus owner description are evidence. Owner answered that NO real panel is available and selected engine + synthetic sample now, real connection later. Do not substitute more keyword-only polish for this direction and do not claim real provisioning/payment integration is complete.

Implemented first pure ServiceFlow state machine and UAT owner/editor-only «نمونهٔ فروش و تحویل سرویس» preview: select fixed synthetic plan -> frozen order amount/currency -> synthetic checkout -> trusted-adapter payment check bound to order/reference/amount/currency -> provisioning instruction -> mock username/password/config delivery. Four cases: paid, unconfirmed, mismatched amount, unknown provisioning outcome. All demo links are inert text; all accounts/configs are clearly unusable DEMO data. Preview does membership/bot reads only; no DB writes, real HTTP/provider/vault/Telegram operation even with outbound flags ON. Existing child-bot runtime is NOT wired to this engine.

Core separates customer actions from trusted external receipts, suppresses repeated callbacks/customer taps within a run, produces scope/run-bound operation/idempotency IDs, rejects invalid prices/foreign operations/payment mismatches, redacts account repr/error details, and stops unknown outcomes without blind retry. This is IN-MEMORY prototype behavior, NOT durable cross-restart idempotency. Live use still requires persistent version-pinned workflow/order/operation storage, encrypted result handling, real verified gateway + panel adapters with idempotency/reconciliation contracts, no-code scenario authoring and customer-chat renderers. No financial amount/latency/commercial readiness claim.

Local Python: 150 discovered, 145 PASS + 5 disposable PostgreSQL skips. Actual DOM paid/unconfirmed/mismatch/timeout, inert links/plain text, duplicate run and close-race tests plus existing editor/report/control/search/copy and seven Save scenarios PASS. Updated CI real UI/HTTP/PostgreSQL case opens/runs the synthetic sample while preserving reply editor and configuration version counts. New pure/API tests cover payment gate, scope/amount/currency/reference, duplicate operations, unknown outcomes, no live effects, auth and secret-redacted validation. CI/PR/merge/deployment/owner phone acceptance PENDING. No schema, customer setting/status, external flag, real order/payment/account/provider/send or Production change. Runbook docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md.

---

## 2026-11-01 — CURRENT: combined TelBot UAT release #108–#111 LIVE / READY

| PRs | Reviewed / merge SHA | UAT | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| #108 menu, #109 activity, #110 pause/resume, #111 search/copy | c1d106287e52abb133258b56ef1414cd360b0fe4 / 69f3858c60d3ca531c48798610eac55e98db9407 | LIVE READY dpl_Gr3NmxVt57kFkd4FNKjbj5bxu1FK; canonical TelBot UAT | Not promoted | New native menu/report/control/search/copy test pending | 11/11 checks; 141 unique Python cases across unit/schema; exact assets/health/auth checks; owner config v6/two rules preserved |

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

| PR | Reviewed / merge SHA | UAT | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| #110 Pause/Resume, includes #108/#109 | ee25a6e32cf541a384d30f0a7ee0a4ec30a4f66f / 95820708380036aa1ffccd412e58f1cd22929e54 | MERGED, NOT LIVE; Vercel daily quota | Not promoted | Native menu/report/pause test pending | 11/11 checks; 141 cases across unit/schema; pause/receipt/resume/replay/lock flow PASS; live old alias healthy |

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

| PR | Reviewed / merge SHA | UAT | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| #109 activity report + #108 menu | 9f3cdd3809e527744a9368a0595575f952f94754 / 462eb5b4db34657b8aefa6a646c2129c95d9dbad | MERGED, NOT LIVE; Vercel daily quota | Not promoted | New menu/report phone test pending | 11/11 checks, 134 Python cases across unit/schema, UI/HTTP/PG PASS; alias remains d772844 |

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

| PR | Git ref / SHA | UAT deployment | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| [#106](https://github.com/namach2727-coder/Sales-Agent/pull/106) | feature/telegram-managed-bots-spike-20261017; reviewed 174acbb2ee5b8e630ec08724c3b9f66137186efc; merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 | READY dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9; canonical TelBot UAT alias | No change / not promoted | Owner phone Save/real-customer persistence pending | 11/11 CI; 126 Python cases across unit/schema, actual UI/HTTP/PG two-save-reopen PASS; exact live assets, ready 200 and preview auth 401 |

PR #106 reviewed head 174acbb2ee5b8e630ec08724c3b9f66137186efc passed all 11 reported GitHub checks. Squash merge 4bd44451a08cded6e6ecf93f91036ad7782722b0 ONLY into feature/telegram-managed-bots-spike-20261017 exactly matches the reviewed tree. Vercel dpl_GWCqrTgAXucDZyEpWYYmPo3xphs9 is READY on that merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The project target label production is the isolated TelBot UAT service, not business Production promotion.

Verified 2026-10-29 13:15 Asia/Tehran / 09:45 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, save-click-1 revision, unauthenticated synthetic preview POST 401. CI unit: 126 discovered, 123 PASS + 3 PostgreSQL skips; schema job ran all 3 PASS, including the actual JS UI through HTTP/FastAPI/PostgreSQL add-save-close-reopen twice (3 versions total, 2 current replies, duplicate-submit guard). Both DOM behavior/focus and 5 save-error/readback scenarios PASS. Read-only UAT after deployment still shows published v4, 4 versions total and 0 rules; no customer configuration was written by deployment/testing. Both outbound flags remain absent/default OFF. Actual owner phone Save acceptance remains PENDING.

---

## 2026-10-29 — CURRENT PR #105 mobile-first layout: UAT READY

| PR | Git ref / SHA | UAT deployment | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| [#105](https://github.com/namach2727-coder/Sales-Agent/pull/105) | feature/telegram-managed-bots-spike-20261017; reviewed 01f5b47681020187026cd704c0a5803dd04fb05f; merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 | READY dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh; canonical TelBot UAT alias | No change / not promoted | Physical phone/native controls/safe areas pending | 11/11 CI; exact live assets, ready 200 and preview 401; offline four-width basic/expanded sizing review |

PR #105 reviewed head 01f5b47681020187026cd704c0a5803dd04fb05f passed all 11 reported GitHub checks. Squash merge 755ba03363fa7be6d8ac2a51f3434c41d41e7810 ONLY into feature/telegram-managed-bots-spike-20261017 has the exact reviewed tree. Vercel dpl_D7xb62HSgQdSMc3Jt2gBArXMPWKh is READY on that exact merge and canonical https://directpilot-telbot-uat-api.vercel.app points to it. The Vercel target label production belongs only to this isolated UAT project; business Production was not promoted.

Verified 2026-10-29 11:31 Asia/Tehran / 08:01 UTC: /ready 200 (database available/migration current), HTML/JS/CSS 200 and byte-identical to reviewed assets, mobile-first-1 revision, unauthenticated synthetic preview POST 401. Dedicated CI: 123 Python PASS plus 2 PostgreSQL cases PASS in schema-test, and actual app.js DOM/focus behavior PASS. Offline review: basic text/API states (176 controls) plus expanded reply settings/POST-message-forwarding states (216 controls), each at 320/360/390/430 CSS px; no horizontal control/container overflow or button/disclosure target below 48px. PNGs reviewed. This approximate document renderer does not establish native OS dropdown, Telegram safe-area, keyboard or real-device acceptance. Owner phone acceptance remains PENDING. Both outbound flags remain absent/default OFF; no backend, stored customer setting, migration, secret or live-send changes.

---

## 2026-10-29 — CURRENT PR #104 editor usability and typing fix: UAT READY

| PR | Git ref / SHA | UAT deployment | Production | Owner acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| [#104](https://github.com/namach2727-coder/Sales-Agent/pull/104) | feature/telegram-managed-bots-spike-20261017; reviewed b45bdf9b0985464f3621a5792c17d9b62b4730b6; merge 17b2545849f8391291f14a46a7b6c18ed443ab22 | READY dpl_DZDzon4PcrDYzGfvLa8rEP9VqJFD; canonical TelBot UAT alias | No change / not promoted | New physical keyboard and usability acceptance PENDING | 11/11 GitHub checks; 125 Python cases across unit/schema jobs, DOM regression PASS; exact live assets, health 200 and preview auth 401 |

PR #104 merged ONLY into feature/telegram-managed-bots-spike-20261017 as 17b2545849f8391291f14a46a7b6c18ed443ab22 after all 11 reported GitHub checks SUCCESS on reviewed head b45bdf9b0985464f3621a5792c17d9b62b4730b6. Merge tree exactly equals the reviewed tree. Vercel deployment dpl_DZDzon4PcrDYzGfvLa8rEP9VqJFD is READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. This project target label production is the isolated TelBot UAT project, not business Production.

Verified 2026-10-29 10:57 Asia/Tehran / 07:27 UTC: /ready 200 ready/database available/migration current; HTML, JS and CSS 200 and byte-identical to the reviewed local assets (20261029-editor-ux-1); unauthenticated synthetic POST /preview 401 missing_init_data. Dedicated CI ran 123 Python cases PASS, with the other 2 PostgreSQL cases PASS in schema-test; actual app.js DOM behavior/focus regression PASS. Both outbound flags remain absent/default OFF. No schema, stored customer-setting, credential, provider-call or Telegram-send change. Owner real Telegram/iOS keyboard and visual acceptance remains PENDING.

---

## 2026-10-29 — CURRENT TelBot checkpoint: PR #103 deployed to UAT

| PR | Git ref / SHA | UAT deployment | Production | Customer acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| [#103](https://github.com/namach2727-coder/Sales-Agent/pull/103) | feature/telegram-managed-bots-spike-20261017; reviewed dfac4cb9c52d77379b926e7885ecfd0d80103a51; deployed merge c08a3c26422ad2d28036946c274b035216fff8c0 | READY dpl_Hy4hsuSi9PzhGNLcoZsqCDejkdYY; canonical TelBot UAT alias verified | Not promoted / no change | Owner mobile/provider acceptance pending | Prior 11/11 CI checks; live health/assets 200, unauthenticated preview 401; outbound flags OFF |

This checkpoint supersedes the historical 2026-10-28 preview deployment quota blocker. Vercel directpilot-telbot-uat-api / team_Cu7IBomJgSNCXUMp3sILUUD4 is READY on dpl_Hy4hsuSi9PzhGNLcoZsqCDejkdYY, exact reviewed merge c08a3c26422ad2d28036946c274b035216fff8c0. Canonical alias https://directpilot-telbot-uat-api.vercel.app points to this deployment. The project target label production belongs ONLY to this isolated UAT project; it is not a business Production promotion.

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

# DirectPilot — Release Register (مرجع واحد انتشار)

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


## Latest TelBot project checkpoint — 2026-10-19

**LATEST VERIFIED TELBOT CHECKPOINT — 2026-10-19.** All six canonical project files plus [TelBot release checklist](docs/telegram_bot_builder/TELBOT_RELEASE_CHECKLIST.md) must remain synchronized after every meaningful TelBot change. Historic statements below are preserved and may be outdated.

- Product: DirectPilot TelBot. Source only on isolated branch `feature/telegram-managed-bots-spike-20261017`. **Never conflate** this with DirectPilot Instagram Production or the independent TelBot Neon Production branch.
- [PR #64](https://github.com/namach2727-coder/Sales-Agent/pull/64) delivery contract/requirements, [PR #66](https://github.com/namach2727-coder/Sales-Agent/pull/66) FastAPI routing and [PR #67](https://github.com/namach2727-coder/Sales-Agent/pull/67) temporary Neon UAT owner role: all MERGED. #67 GitHub main CI and isolated TelBot CI both SUCCESS.
- Operational source SHA `bd20c44a883a4de3f57ca2f9d009b8d981519c18`; independent Vercel TelBot UAT project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`, [deployment `dpl_DYjA434LnV79oYHDnXSHW36dXAL6`](https://vercel.com/mohcenp-9857s-projects/directpilot-telbot-uat-api/DYjA434LnV79oYHDnXSHW36dXAL6) READY; alias `directpilot-telbot-uat-api.vercel.app` mapped to this deployment.
- After PR #66 owner received correct `/live` JSON: `{"status":"live","service":"directpilot-telbot-uat"}` — historical PASS. No post-PR #67 `/ready` HTTP result has been confirmed, so **DB connectivity remains PENDING**, regardless of Vercel READY.
- Read-only Neon UAT: project `curly-cell-93038441`, branch `br-tiny-poetry-arz49v2o`, DB `telbot`: 14 tables; latest migration `0002_webhook_auth`; 0 tenants and 0 bots.
- Vercel UAT-only project environment lists `TELBOT_ENV=uat`, Sensitive `TELBOT_UAT_DATABASE_URL`, and `TELBOT_UAT_DB_HOST`. **Secret presence != working connection**. PR#67 API guard temporarily permits `telbot_owner` or `telbot_ua_runtime`, still verifying database `telbot` and UAT schema; owner role has CREATEDB/CREATEROLE and must be replaced before real customer data.
- Manager token/webhook secret/Fernet keys **not present** in last env inventory; real Manager Bot, Telegram outbound, Mini App UI, child token storage, commercial subscriptions, cross-tenant E2E and owner acceptance are NOT DONE. No Instagram Production or TelBot Neon Production deployment authorized.

**TelBot release row — T1 PARTIAL:** PR#64 requirements/keyboard contract, #66 FastAPI routing, #67 temporary UAT owner role merged. GitHub CI successful; UAT Vercel READY on source `bd20c44a`, deployment `dpl_DYjA434LnV79oYHDnXSHW36dXAL6`; user `/live` PASS; Neon UAT 14 tables / migration 0002; post-#67 DB `/ready` unverified; Telegram E2E/Owner signoff PENDING; Production NO GO.

---


**آخرین تطبیق مستنداتی:** 2026-10-15 | **دامنه UAT:** https://uat.directpilot.ir | **دامنه Production:** https://directpilot.ir

این ثبت، **وضعیت واقعی استقرار** را از **وجود کد**، **PASS تست خودکار**، **تأیید کسب‌وکار** و **اجازه انتقال Production** جدا می‌کند. تاریخچه اصلی بدون حذف در `docs/runbooks/history/20261015_pre_release_register/` نگهداری شده است. هیچ سطر این جدول مجوز انتشار Production نیست.

## قرارداد وضعیت و تأیید

- **UAT-CODE**: کد در Branch `UAT` یا Backend مخصوص UAT وجود دارد؛ **UAT-DEPLOY**: commit متناظر روی دامنه رسمی UAT مستقر و READY شده؛ **CI-PASS**: تست خودکار موفق؛ **UAT-BROWSER-PENDING**: تست مرورگر واقعی/کاربر هنوز کامل نیست.
- **PROD-DEPLOY-CODE**: کد مربوط در **SHA واقعاً متصل به alias Production** یافت شده؛ **PROD-PR**: PR به `main` ادغام شده، ولی اجرای کسب‌وکاری جدا از آن است؛ **PROD-ABSENT**: در SHA فعال Production، کد قابلیت وجود ندارد؛ **PROD-UNVERIFIED**: شواهد کافی برای اعلام پیاده‌سازی یا سلامت عملیاتی نداریم.
- **OWNER-DOC-APPROVED** یعنی کاربر در 2026-10-15 شش اصلاح **مستنداتی** را تأیید کرده است، نه تأیید UAT هر قابلیت یا GO برای Production. همه ردیف‌های نیازمند UAT واقعی با **OWNER-UAT-PENDING** باقی می‌مانند.
- وضعیت قابلیت تنها با PR کافی نیست: وجود در SHA استقرار، کنترل دامنه، نیازهای دیتابیس/Backend و تست end-to-end جداگانه ضروری است.

## شواهد استقرار مرجع

| محیط | Frontend و GitHub | Backend و Database | سطح شواهد |
|---|---|---|---|
| UAT | `directpilot-web`, Branch `UAT`, SHA `dad3a3790246f96fbbe760d26e2415afd0a45851`, Vercel `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` READY | `directpilot-uat-api.vercel.app`, Branch `migration/vercel-uat-fastapi-20261014`, مستقل از Production؛ Neon `round-shape-42044596/neondb`, Alembic `0027_traceable_receipt_versions` | CI و HTTP smoke PASS؛ موبایل/رسید/Meta end-to-end کامل نیست |
| Production | `directpilot-web`, Branch `main`, SHA `8592c6e91d4beaed7c31653dc285612fd511fa53`, Vercel `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF` READY | Render `directpilot-api` و دیتابیس مرجع Render؛ با Neon UAT یکی نیست | وجود کد Frontend و PRهای Production بررسی‌شده؛ DB واقعی Render از این اتصال تأیید مستقیم نشده؛ هیچ cutover صورت نگرفته است |

> وضعیت این جدول snapshot است. برای تصمیم انتشار بعدی، alias و commit و نسخه migration را همان لحظه دوباره استعلام کنید. **مرجع Production پایگاه داده فعلی Render است؛ Neon Production هنوز همگام‌سازی نهایی تأییدشده ندارد.**

## ثبت قابلیت‌ها و انتشارها — ۸ تا ۱۵ اکتبر

| شناسه | PR منبع (F=Frontend، B=Backend) | قابلیت/خروجی مشخص | UAT | Production | تأیید کاربر |
|---|---|---|---|---|---|
| REL-001 | F#1–#5, F#30 | بهبود سئو، لینک‌سازی داخلی و انتشار مقاله Smart Direct | کد مشترک/بخشی از UAT؛ آزمون سئوی عملی جدا | **PROD-PR / PROD-DEPLOY-CODE** در `main`؛ نتیجه رتبه‌بندی/ایندکس جداگانه سنجیده نشده | OWNER-DOC-APPROVED؛ KPI نیازمند اندازه‌گیری |
| REL-002 | F#6–#8 | GA4 consent، اصلاح CSP و صف gtag | اثر روی Production source ثابت است؛ نتیجه Realtime مستقل | **PROD-PR**؛ رخدادهای `page_view`, `signup_intent`, `sign_up` بدون شواهد لحظه‌ای PASS محسوب نمی‌شوند | اندازه‌گیری PENDING |
| REL-003 | F#9 | Humanized UI و motion | تغییر طراحی ادغام‌شده | **PROD-PR**؛ ارزیابی دیداری/دسترس‌پذیری جداست | UI acceptance PENDING |
| REL-004 | F#10, F#20 | ثبت‌نام→داشبورد→انتخاب پلن→سفارش→کارت‌به‌کارت→رسید | UAT-DEPLOY؛ E2E سناریوی کامل PENDING | **PROD-PR / code present** در انتشار F#20؛ تراکنش واقعی و پرداخت تأییدشده از این ممیزی اثبات نشده | OWNER-UAT-PENDING |
| REL-005 | F#11, F#20 | توضیح تفکیکی پلن‌ها، CTA و نمایش مشخصات کارت | UAT-DEPLOY؛ UX مشتری PENDING | **PROD-PR / code present**؛ نمایش کارت، کپی و مسیر پرداخت در SHA Production دیده شده | OWNER-UAT-PENDING |
| REL-006 | F#12 | انتخاب هم‌زمان **DM / Story / Comment**، حفظ اسکرول انتخاب پلن و تمایز AI | **UAT-DEPLOY / CI-PASS**؛ Meta end-to-end PENDING | **PROD-ABSENT** در کامپوننت انتخاب trigger نسخه فعال | OWNER-UAT-PENDING؛ نیازمند GO مستقل |
| REL-007 | F#15, F#16, F#20 | خرید **۱ تا ۱۲ ماهه** پلن پولی ۳۰روزه؛ مبلغ و مدت snapshot سفارش | **UAT-DEPLOY / CI-PASS**؛ بررسی مالی واقعی PENDING | **PROD-DEPLOY-CODE**: فراخوانی `ordersApi.create(id,months)` در SHA فعال Production تأیید شد؛ E2E مالی مستقل | OWNER-UAT-PENDING |
| REL-008 | F#17, F#18, F#20 | پیش‌نمایش امن JPEG/PNG/PDF رسید در ادمین، صفحه پرداخت جمع‌وجور، CTA ارتقا، کپی شماره کارت | **UAT-DEPLOY / CI-PASS**؛ مسیر حقیقی پرداخت PENDING | **PROD-DEPLOY-CODE** برای فرم‌ها/کپی و PR انتشار F#20؛ پذیرش نسخه‌های تاریخی شامل این ردیف نیست | OWNER-UAT-PENDING |
| REL-009 | F#21, F#22 | رفع پوشانده‌شدن ورود با منوی موبایل در نسخه اولیه | **UAT-DEPLOY** | **PROD-PR** F#22؛ اصلاح کامل جدید REL-016 نیست | مرورگر موبایل PENDING |
| REL-010 | F#23, F#24, F#25 | ساده‌سازی داشبورد مشتری و حذف نمایش مکالمات آنلاین | **UAT-DEPLOY** | **PROD-PR** F#25؛ عدم بازگشت پنل مکالمات باید در مرورگر تأیید شود | OWNER-UAT-PENDING |
| REL-011 | F#26, F#29 | محتوای Features/Solutions و انتشار مرکز راهکارها | **UAT-DEPLOY** | **PROD-PR** F#29؛ صفحه عمومی `/solutions` در `main` ثبت شده | محتوای عمومی نیازمند بازبینی نهایی |
| REL-012 | F#27, F#28, F#31 | اصلاح پیام دوره آزمایشی از ادعای ۱۴ روز به **۳ روز** و سپس تبدیل متن پلن به داده واقعی Backend | **UAT-DEPLOY**؛ جدول دیتابیس و قواعد `trial_eligible` پایین، نه متن تبلیغاتی ثابت | **PROD-PR** F#27 (پیام ۳روز)؛ همسانی کاتالوگ/نحوه فعال‌سازی Production **PROD-UNVERIFIED** | تعیین متن نهایی و تست Signup PENDING |
| REL-013 | B#34 | ذخیره تصاویر محصول با `product_media_assets.image_data BYTEA`، محدودیت ۲ MiB/تصویر و ۵۰ MiB/فروشگاه | **UAT-CODE/SCHEMA/DEPLOY**؛ تست واقعی آپلود/حذف/پایداری PENDING | **PROD-ABSENT / NOT CUT OVER**؛ PR به UAT Backend محدود بود | OWNER-UAT-PENDING |
| REL-014 | B#36, F#31 | **رسید نسخه‌دار** با اتصال مشتری/سفارش/پرداخت، جست‌وجوی ایمیل/تاریخ، سابقه ادمین، SHA-256 | **UAT-DEPLOY/DB 0027؛ ۲/۲ receipt backfill PASS**؛ Browser E2E و backup مستقل PENDING | **PROD-ABSENT / PROD-UNVERIFIED**؛ تاریخچه قبلی را در Production بدون شواهد فرض نکنید | OWNER-UAT-PENDING |
| REL-015 | F#31 | اصلاح «بررسی حساب» بدون بلوکه‌کردن فرم ورود و محافظت در برابر `/auth/me` دیرهنگام | **UAT-DEPLOY / CI-PASS**؛ اندازه‌گیری سرعت روی گوشی PENDING | **PROD-ABSENT** برای UX جدید در کد فعلی فرم ورود | OWNER-UAT-PENDING |
| REL-016 | F#32 | بازطراحی ناوبری موبایل مشتری/ادمین/عمومی؛ Back و Close، Escape، Touch، Safe-area و فرم‌ها | **UAT-DEPLOY / ۲۲۳ تست PASS**؛ iPhone/Android دستی PENDING | **PROD-ABSENT** برای منوی مشترک جدید | OWNER-UAT-PENDING |
| REL-017 | B#31, B#38–#43 | انتقال Backend UAT به Vercel + Neon و حفاظت/تست دامنه `uat.directpilot.ir` | **UAT Backend READY، /ready و routing PASS**؛ UAT business signoff هنوز باز | **NOT A PRODUCTION RELEASE**؛ Render همچنان مرجع | GO Production داده نشده |
| REL-018 | B#33 (بسته)، B#35, B#37 | تصمیم دائمی **PostgreSQL BYTEA؛ عدم استفاده از R2/S3** و رد پیاده‌سازی آزمایشی Storage خارجی | ثبت در مستندات؛ UAT migration مطابق تصمیم | تغییر Production در این تصمیم اعمال نشده | **تصمیم معماری تأییدشده** |
| REL-019 | F#31, B#36 | الزام بازیابی رسیدهای هر مشتری **پس از چهار ماه و حتی بعد از جایگزینی رسید ردشده** | مدل و تست ۱۲۵ روزه در کد؛ آزمون Backup و بازیابی بلندمدت PENDING | **NOT VERIFIED / NOT PROMOTED** | الزام محصول تأیید شده، SLA عملیاتی هنوز نه |
| REL-020 | F#20, F#25, F#29, F#30 | انتشارهای مستقل و انتخابی Frontend Production طی ۱۲ تا ۱۴ اکتبر | ثبت صرفاً به‌عنوان شاهد انتشار انتخابی | **PROD-PR**؛ انتشارهای قبلی را دوباره مهاجرت ندهید | تأیید انتشار گذشته ≠ UAT همه قابلیت‌ها |

لینک‌های PR در GitHub:
- Frontend: `https://github.com/namach2727-coder/directpilot-web/pull/<number>`
- Backend: `https://github.com/namach2727-coder/Sales-Agent/pull/<number>`

## کاتالوگ واقعی UAT — Snapshot فقط‌خواندنی Neon، ۱۵ اکتبر

**Source of truth:** `neondb.public.saas_plans`؛ نوع پول **IRR**، مبالغ به **ریال** هستند؛ تمام اطلاعات زیر از داده واقعی UAT هستند، **نه Production**.

| کد | نوع | قیمت دوره (ریال) | روز | وضعیت فعال | قابل خرید | مجاز برای Trial | سقف اتوماسیون | سهمیه پاسخ/AI | اکانت Instagram |
|---|---|---:|---:|---|---|---|---:|---|---:|
| `AUTOMATION_TRIAL` | Automation | ۰ | ۳ | بله | خیر | **بله** | ۳ | پاسخ ۰، AI — | ۱ |
| `AI_ASSISTANT_TRIAL` | AI Assistant | ۰ | ۳ | بله | خیر | **بله** | ۰ | پاسخ ۲۰۰، AI request نامشخص | ۱ |
| `AUTOMATION_V1` | Automation | ۴٬۹۰۰٬۰۰۰ | ۳۰ | بله | **بله** | خیر | ۲۰ | پاسخ ۰، AI — | ۱ |
| `AI_ASSISTANT_V1` | AI Assistant | ۶٬۹۰۰٬۰۰۰ | ۳۰ | بله | **بله** | خیر | ۰ | پاسخ ۱۰۰۰، AI request ۱۰۰۰ | ۱ |
| `START` | legacy | ۲٬۹۹۰٬۰۰۰ | ۳۰ | بله | **خیر** | خیر | ۱۰ | پاسخ ۱۵۰۰ | ۱ |
| `PRO` | legacy | ۶٬۹۹۰٬۰۰۰ | ۳۰ | بله | **خیر** | خیر | ۳۰ | پاسخ ۵۰۰۰ | ۱ |
| `TRIAL` | legacy | ۰ | ۳ | بله | **خیر** | **خیر** | ۳ | پاسخ ۲۰۰ | ۱ |
| `FREE` | legacy | ۰ | — | **خیر** | **خیر** | خیر | ۱ | پاسخ ۲۰ | ۱ |

- **فعال‌بودن** معادل **قابل خرید بودن** نیست؛ `START`, `PRO` و `TRIAL` ممکن است به دلیل سابقه برای خواندن داده باقی بمانند و نباید در UI خرید آزاد نمایش داده شوند.
- فقط دو طرح تخصصی `*_TRIAL` دارای `trial_eligible=true` و مدت سه روزند. عبارت «همه پلن‌ها سه روز رایگان» بدون بررسی سیاست ثبت‌نام ممنوع است.
- قیمت، مدت، محدودیت و کد هر پلن باید از Backend و `saas_plans` خوانده شود؛ تغییرات و Snapshot سفارش بر قیمت آینده اثر پس‌نگر ندارد. به‌روزرسانی کاتالوگ نیازمند تصمیم تجاری مستقل است.
- **Production catalog not verified:** هیچ عدد این جدول مبنای ادعای مقدار دیتابیس فعلی Render نیست.

## تعریف دقیق قابلیت چندکاناله

در Frontend UAT، کاربر می‌تواند **یک، دو یا سه** گزینه مستقل `DM_KEYWORD`, `STORY_REPLY_KEYWORD`, `COMMENT_KEYWORD` را به‌صورت checkbox انتخاب کند، اما **Backend یک Rule مشترک چند trigger ندارد**. UI برای هر کانال **یک قانون مستقل** به‌صورت ترتیبی می‌سازد و هرکدام **یک واحد از ظرفیت پلن** مصرف می‌کند. برای DM و Story اکشن `SEND_MESSAGE` و برای Comment اکشن `SEND_PRIVATE_MESSAGE` ثبت می‌شود. باید دست‌کم یک کانال انتخاب شود و ظرفیت قبل از ارسال کنترل شود. در صورت موفقیت ناقص، UI فهرست را Refresh و از تکرار کورِ کل عملیات منع می‌کند؛ **این عملیات اتمیک نیست**. ویرایش قانون موجود فقط اولین trigger انتخابی را آپدیت و برای انتخاب‌های اضافی Rule جدید می‌سازد. آزمون واقعی Meta webhook/send همچنان **BLOCKED/PENDING** است؛ CI صرفاً قرارداد کد را ثابت می‌کند.

## معیارهای پذیرش و انتقال

جزئیات گام‌به‌گام در این Runbookها:
- `docs/runbooks/uat_customer_billing_acceptance_20261015.md`
- `docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md`
- `docs/runbooks/uat_mobile_frontend_ux_audit_20261015.md`
- `docs/runbooks/official_uat_acceptance_gate_20261014.md`

**صریحاً PENDING:** UAT موبایل Safari/Chrome، انتخاب سه کانال با ظرفیت واقعی، DM/Story/Comment Meta E2E، خرید ۱ تا ۱۲ ماه، عکس رسید با آپلود/بازآپلود و نسخه‌ها، پذیرش ادمین، بازیابی مستقل چهارماهه، GA4 Realtime و صحت کاتالوگ Production.

**Hard stop Production:** هیچ merge از کل `UAT` به `main`، هیچ ایجاد Deployment، تغییر Render/Neon Production، DNS، Meta، پرداخت واقعی، فعال‌سازی دستی اشتراک یا قطع سرویس انجام نشود تا owner جداگانه GO دهد و backup/freeze/parity/rollback و eligibility میزبانی تجاری اثبات شوند.

## روش نگهداری

۱. در هر تغییر PR/Deploy، فقط ردیف مرتبط را با **شماره PR، commit/deployment، وضعیت UAT، Production و تأیید مشتری** اصلاح کنید. ۲. برای PASS عملی، نتیجه تست با زمان، محیط و شواهد ثبت شود. ۳. پنج فایل بالا صرفاً خلاصه و لینک باشند؛ تکرار تاریخچه در هر پنج فایل ممنوع. ۴. تاریخچه اصلی دقیقاً در `docs/runbooks/history/20261015_pre_release_register/` و Git باقی بماند؛ پاک‌سازی آن ممنوع.

## تأیید Owner — بسته‌شدن کارهای P0-01 تا P0-06 از چک‌لیست اجرایی گفتگو (۱۵ اکتبر ۲۰۲۶)

Owner صریحاً **تمام شش مورد اولویت‌بندی اجرایی** را تأیید کرد؛ این شناسه‌ها به جدول Roadmap یا REL IDs اشاره ندارند:
- **P0-01:** سلامت و اتصال UAT (Frontend/Backend/Neon).
- **P0-02:** ثبت‌نام، Login/Logout و Session.
- **P0-03:** پلن‌ها، Trial سه‌روزه و محدودیت‌ها.
- **P0-04:** سفارش و خرید اشتراک ۱ تا ۱۲ ماه.
- **P0-05:** کارت‌به‌کارت، آپلود رسید و تأیید ادمین.
- **P0-06:** مجوزها، امنیت دسترسی و تاریخچه رسید.

**وضعیت مدیریت کار: OWNER-ACCEPTED / CLOSED؛ این شش مورد را به‌صورت پیش‌فرض مجدداً به صف اجرا یا تأیید برنگردان.** نوع شاهد فعلی «اعلام کاربر در گفتگو» است؛ گزارش مستقل E2E/CI یا تغییر Production در این اقدام تولید نشده و جزئیات فنیِ PENDING/UNVERIFIED سابق را به دروغ PASS نمی‌کند. فقط با بروز Regression مستند یا درخواست جدید Owner بازگشایی شوند. **گام اجرایی بعدی: P1-01 بهبود UX داشبورد مشتری و ادمین، سپس P1-02 موبایل و P1-03 اتوماسیون؛** تغییر Production همچنان تابع گیت جداگانه است.

## تأیید جدید Owner — P1-01 تا P1-05 (۱۵ اکتبر ۲۰۲۶)

Owner در گفتگو **تمام پنج ردیف P1-01 تا P1-05 از چک‌لیست اجراییِ اولویت‌بندی‌شده** را تأیید کرد. این شناسه‌ها شناسه‌های اجرایی گفتگو هستند و با P1 Roadmap، REL IDs یا شماره PR یکسان نیستند:

| شناسه | دامنه تأیید‌شده | وضعیت مدیریت کار |
|---|---|---|
| P1-01 | بهینه‌سازی UX داشبورد مشتری و ادمین | OWNER-ACCEPTED / CLOSED |
| P1-02 | ناوبری موبایل و فرم‌ها | OWNER-ACCEPTED / CLOSED |
| P1-03 | انتخاب هم‌زمان DM، Story و Comment | OWNER-ACCEPTED / CLOSED |
| P1-04 | اتصال Instagram و Meta Webhook | OWNER-ACCEPTED / CLOSED |
| P1-05 | عملکرد AI Assistant و سهمیه مصرف | OWNER-ACCEPTED / CLOSED |

**عدم تکرار:** این پنج مورد و شش مورد P0-01..P0-06 پیش‌تر با اعلام Owner بسته شده‌اند و نباید خودکار به فهرست کارهای آینده برگردند؛ فقط Regression مستند یا دستور جدید Owner مجوز بازگشایی است. **ماهیت شاهد:** اعلام تأیید کاربر، نه گزارش فنی تازه؛ بنابراین وضعیت E2E، اتصال زنده Meta، صحت عددی و Production در جدول‌های تاریخی صرفاً با این یادداشت تبدیل به «تست مستقل PASS» نمی‌شود. **پیشنهاد گام بعدی:** P2-01 ذخیره/بازیابی تصاویر محصول و P2-02 SEO/GA4، سپس گیت‌های مهاجرت Production با Backup/Restore و GO جداگانه. هیچ تغییر در Production یا محیط اجرا در این ثبت مستنداتی اعمال نشده است.

## Owner acceptance — operational P2-01 and P2-02 (2026-10-15)

مالک پروژه به‌صراحت دو فعالیت **P2-01 (بررسی ذخیره‌سازی و بازیابی تصاویر محصول)** و **P2-02 (بررسی SEO و GA4)** از *چک‌لیست اجرایی گفتگو* را تأیید کرد. وضعیت پیگیری هر دو: **OWNER-ACCEPTED / CLOSED**. این شناسه‌ها با شماره‌های Roadmap/Release Register یا PR قابل‌جایگزینی نیستند.

**قانون عدم تکرار:** P2-01 و P2-02 مانند P0-01..P0-06 و P1-01..P1-05 بدون گزارش Regression جدید یا دستور صریح Owner دوباره به صف فعالیت‌ها ارجاع داده نشوند. این ثبت، پذیرش کار توسط کاربر است، **نه** نتیجه تست مستقل جدید یا اثبات GA4 Realtime، Recovery چندماهه، صحت داده Production یا صدور GO برای مهاجرت. گزارش‌های فنی تاریخی و وضعیت محیط‌ها بدون جعل PASS محفوظ می‌مانند.

**گام‌های باز بعدی:** P0-07 (Backup و آزمایش Restore پایگاه داده Production)، P0-08 (Sync کنترل‌شده Production به Neon و Data Parity)، P0-09 (Backend cutover و Rollback)، سپس P3-01 (انتشار گزینشی با مجوز مستقل). بدون تأیید مستقل Production GO هیچ Cutover یا تغییر محیط Production انجام نشود.


## P0-07 — Production backup execution preflight (2026-10-15)

- **Confirmed from Render control plane:** Workspace `tea-dabsgm0n74is738av7l0`; production database `directpilot-production-db` (`dpg-db0escm0tbcc73fhig2g-a`), PostgreSQL 16, status `available`, plan `free`, reported expiry **2026-11-02T11:59:46Z**. Production API service `directpilot-api` (`srv-db0f3uc9v7es73b5k51g`) remains on Render.
- **Attempted read-only DB preflight:** `query_render_postgres` could not connect: Render reports **empty IP allowlist blocking all external connections**; hosted Render connector has no fixed IPs for allowlisting. No database-level SQL query was run.
- **Backup outcome: BLOCKED / NOT CREATED. Restore test: NOT RUN.** Available Render connector methods list/read Postgres and execute read-only SQL but do not provide `pg_dump`/snapshot export; never treat schema inspection or copied Neon UAT as a recoverable Production backup.
- **Safe next step:** use a credentialed runtime with authorized private/network DB access to run `pg_dump -Fc` to encrypted durable storage, checksum the archive, then restore to isolated scratch database and validate schema/data counts. Keep source Production unchanged; avoid publishing secrets or raw personal data in GitHub. Do not start P0-08 sync or shutdown until evidence exists.
- **Owner's instruction:** perform work autonomously wherever connected tools permit, without requiring desktop interaction; only request a credential/network authorization if no automated connector route exists. **This entry is an execution blocker, not successful completion.**


## P0-07 — Local Production backup evidence (2026-10-17)

Owner reported successful `pg_dump 16.15 -Fc` against current Render Production database from their Windows computer after restricted network access was restored. Local file: `C:\Users\q\DirectPilotBackups\directpilot_prod_20261017_103343.dump`. A successful `pg_restore --list` confirmed the archive index is readable; SHA-256: `9E46745AA1D115EA74A0877ACEC28A53423ADE73DBEE9FD490842AAFC6D8D064`. **Evidence type: owner-supplied local command output (not an independently inspected file).**

**Stage: BACKUP FILE CREATED / ARCHIVE INDEX PASS; P0-07 OVERALL STILL OPEN.** Full restore test in an isolated scratch database, record-count/schema parity checks, off-device encrypted backup copy and backup recovery plan are still PENDING. Keep local file private; do not upload it to GitHub or chat. No Production schema/data migration, deployment, DNS or service cutover is authorized by this backup evidence. The prior 2026-10-15 BLOCKED note remains as chronological history and is superseded only for backup creation.

## ۲۰۲۶-۱۰-۱۷ — نتیجه واقعی P0-07 و وضعیت انتقال Schema

- **Backup واقعی Render Production با PostgreSQL Client 16.15:** فایل خصوصی ویندوز `directpilot_prod_20261017_103343.dump`؛ SHA-256 `9E46745AA1D115EA74A0877ACEC28A53423ADE73DBEE9FD490842AAFC6D8D064`؛ `pg_restore --list` PASS، طبق خروجی گزارش‌شده توسط Owner.
- **Restore عملی روی PostgreSQL محلی مستقل:** `RESTORE_TEST: PASS` در ۱۷ اکتبر؛ ۸۲ جدول، Alembic `0025_trial_three_days`؛ سرور موقت `127.0.0.1:55432` خاموش شد؛ محیط‌های زنده دست‌نخورده‌اند. سطح شواهد: خروجی ابزار در کامپیوتر Owner، نه دسترسی مستقیم به فایل Backup.
- **UAT Neon استعلام مستقیم:** ۸۳ جدول، Alembic `0027_traceable_receipt_versions`، ستون `product_media_assets.image_data` و جدول `manual_payment_receipt_versions` موجود. **Neon Production قدیمی:** ۸۲ جدول، Alembic `0025`؛ این نسخه جایگزین Render فعلی نیست.
- **مهاجرت‌های منبع:** `0026_durable_product_media` (افزودن ستون BYTEA)، `0027_traceable_receipt_versions` (جدول نسخه رسید + backfill انتخابی)، در Branch `migration/vercel-uat-fastapi-20261014`. در `backend-main` Production هنوز فایل‌های این دو Migration وجود ندارند. **تا آماده‌شدن Backend سازگار، ارتقای دیتابیس زنده به 0027 ممکن است startup/migration برنامه قدیمی را مختل کند.**
- **گیت باز:** آزمون dry-run واقعی Migration روی Restore ایزوله، سپس اجرای خود Alembic با کد منتخب، تطبیق سازگاری Backend/ORM و داده‌ها، نسخه پشتیبان رمزگذاری‌شده مستقل از کامپیوتر و پنجره انتشار/rollback. **No production write or cutover.** وضعیت: P0-07 RESTORE TEST PASS، حفاظت بکاپ مستقل PENDING؛ P0-08 MIGRATION NOT STARTED.


## Neon staging update — 2026-10-17

Neon `directpilot_live` backup restore: PASS (82 tables at revision 0025). Additive schema updates corresponding to UAT 0026 and 0027 were applied in transactions. Read-only verification: 83 tables, revision `0027_traceable_receipt_versions`, image BYTEA column present, receipt history table present. Live Render and production app configuration were not changed. Backend compatibility and final data synchronization remain pending; no production cutover approval. The Neon role credential must be rotated before go-live due to exposure in chat.

## 2026-10-17 — Neon role credential rotation after URI exposure

- **COMPLETED:** Password reset for PostgreSQL role `neondb_owner` on Neon Production project `billowing-poetry-05589994`, branch `br-winter-water-argmnyru` after a connection URI was disclosed in chat. Never record or repeat the previous or new secret.
- **Read-after-write checks PASS:** Neon connector connected to `directpilot_live` (Alembic `0027_traceable_receipt_versions`) and `neondb` (Alembic `0025_trial_three_days`); refreshed connection string for `directpilot_live` was retrievable. Password rotation thus confirmed at provider API level; external application reconnection is not yet proven.
- **No linked deployment changed:** Render Production remains authoritative and uses Render PostgreSQL until cutover. Vercel `directpilot-uat-api` has a sensitive `DATABASE_URL` entry whose value cannot be inspected with current connector permissions; no verified active service was identified as using this Neon Production role. Therefore **no Render/Vercel environment secret was modified** and endpoint dependents cannot be declared fully verified.
- **Follow-up before go-live:** re-copy current Neon connection string when configuring the selected Backend Production deployment, do not reuse leaked/stale local clipboard copies, verify authenticating from the actual backend runtime, then complete controlled final Render data sync, backup/rollback and owner GO.

## 2026-10-17 — Selective Backend release PR #47 (staging only)

- **Source:** `release/prod-neon-0027-backend-20261017` -> draft GitHub PR **#47** (selective UAT PR #34 media/receipt Backend changes + tests), no whole UAT merge and no production deployment. Tracking runbook `docs/runbooks/prod_neon_0027_release_gate_20261017.md` is included on the release branch.
- **Neon staging:** `directpilot_live` has 83 public tables, Alembic `0027_traceable_receipt_versions`. Read-only schema comparison to UAT: 918 column definitions and 530 index definitions have matching fingerprints. Both have 1,137 constraints but constraint text is not byte-identical due in part to PostgreSQL CHECK cast normalization and historical NOT NULL constraint naming; exact constraint equivalence remains a separate review.
- **CI and runtime:** PR #47 started Postgres smoke, PostgreSQL 18 compatibility, Docker build and application tests. Report actual final CI results only after all jobs complete. Render `directpilot-api` remains live on `backend-main` and Render PostgreSQL, with autoDeploy disabled. **Docker startup unconditionally invokes Alembic migrations:** do not deploy this release against live Render while it is still at revision 0025 without explicit authorization.
- **Not cut over:** Render data has likely changed since the Oct 17 static archive; final freeze, fresh backup, independent protected copy, full row-level aggregate reconciliation, isolated backend runtime smoke, signing keys, Meta/payment webhook buffering and explicit Owner GO are pending. The Neon role password was rotated; copied prior URL is stale.

### CI acceptance — PR #47 at 8762c37b (2026-10-17)

GitHub Actions run `39017203961` confirmed **4/4 PASS** on selective release head `8762c37b6a41056b60123a63424901ba8a38199c`: `postgres-smoke`, `postgres18-neon-compatibility`, `docker-build`, and `test` (pytest). PR #47 remains **DRAFT / NOT MERGED**; CI PASS is not real-backend-to-Neon E2E and is not authorization for Production deployment. Live Render database remains the source of truth; fresh write-freeze/final backup/parity and protected cutover still pending.

## 2026-10-17 — Owner clarified Production usage is test-only

Owner explicitly stated **all current usage is experimental**: no real customers, payments or Instagram webhook operations that require commercial continuity. This reduces outage/replay SLA obligations but **does not authorize silent loss of experimental changes after the 2026-10-17 10:33 Render backup**. Render hosted database read-only query attempted by connector but blocked by Render external IP allowlist, so actual post-backup source delta remains unknown. Release PR #47 already has CI 4/4 PASS and remains draft; Neon directpilot_live is ready at revision 0027. Next decision: Owner approval to use the Oct-17 restored staging snapshot as test source of truth and discard any newer Render test changes, OR obtain a fresh source dump during controlled final sync. Frontend must use backend HTTP, never direct Postgres. Do not change Render live DATABASE_URL or production Vercel API routing until this decision and runtime compatibility work.

## 2026-10-17 — Test-only production API cutover to Vercel + Neon VERIFIED

**Owner GO:** All existing records and provider activity are experimental; owner approved the Oct-17 Render dump as source of truth, accepting loss of any later Render test writes.

**WEB/API SWITCH PASS:** Production `directpilot.ir` frontend redeployed at **same main SHA `8592c6e9`**, Vercel deployment `dpl_AKFqXWre8HxCHVvvNz9yZeviGLF9` READY; Production-only `DIRECTPILOT_API_UPSTREAM=https://directpilot-prod-api.vercel.app`. New separate Vercel API `directpilot-prod-api` deployment `dpl_5wSJ1veseCg7BprMsGfQ4HTQ6sAJ` READY, Backend release SHA `65a3ef94`, Neon Production `directpilot_live` **83 tables / Alembic 0027**. GitHub [API ready/live/version smoke #39018969331](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39018969331) PASS; [website→API plans/auth smoke #39019279518](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39019279518) PASS, plan endpoint 200 and unauthenticated /auth/me 401. UAT untouched.

**Important:** The new API uses new Vercel secrets because Render secret values were inaccessible. Existing test sessions and encrypted Instagram connections may need re-login/reconnect. Meta outbound/publishing disabled, AI/payment provider secrets not migrated or end-to-end tested. Render services/DB still retained, **not deleted**. Backend draft PR #47 not yet merged; Vercel Production API project lacks automatic Git connection. Encrypted offsite backup and real browser functional acceptance remain open. Operational evidence, rollback, owner-approved test-data loss in `docs/runbooks/production_vercel_neon_cutover_20261017.md`. **Do NOT declare full feature GO-live or delete Render**.

## 2026-10-17 — Final Git source promotion for Vercel-Neon cutover

PR **#47 MERGED** to `backend-main` at `df4da87a883c590fb649d8a9f5aff2f80de5fa28` after all latest CI checks passed, including PostgreSQL 18, full test, Docker build and PostgreSQL smoke. Previous Draft/PENDING statements about PR #47 are historical and superseded. Vercel Production API deployment `dpl_5wSJ1veseCg7BprMsGfQ4HTQ6sAJ` remains READY on functionally equivalent earlier release SHA `65a3ef94`; newer release commits only added safe workflow files and docs. Vercel frontend `dpl_AKFqXWre8HxCHVvvNz9yZeviGLF9` READY using original main SHA `8592c6e9`, aliases `directpilot.ir` and `www.directpilot.ir` assigned. Test [#39019279518](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39019279518) PASS confirms website API proxy and unauthenticated /auth/me protections. Neon `directpilot_live` confirmed revision `0027_traceable_receipt_versions`. Render Backend `directpilot-api` still has `autoDeploy=no`; no new Render deployment was triggered by the merge. Render service and DB are retained but no longer on Production website's API routing path. Full Meta/AI/payment gateway integration still pending due to untransferred protected Render secrets; no blanket functional acceptance. Canonical cutover runbook: `docs/runbooks/production_vercel_neon_cutover_20261017.md`.

## 2026-10-17 — Super Admin Production UI acceptance

- **User-reported PASS (manual browser acceptance):** Test customer login works on `https://directpilot.ir`. Super Admin login also works after correcting login identity; user confirmed `/admin` and **dashboard, customer list, subscriptions and payments** display correctly. This is explicit owner manual acceptance of read-only administrative navigation, **not** payment workflow / Meta / AI / production payment approval acceptance.
- **Read-only Neon staging/live DB payment preflight:** `directpilot_live` has **1 active/default payment card**, **1 manual payment** with DB-backed receipt bytes and **1 version-history row**, **25 subscription orders**, **24 tenant subscription records**, **1 active Super Admin role** (aggregate counts only; no PII or card data exposed). These counts demonstrate existing structure and records, not successful new payment operations.
- **Next controlled functional tests:** Customer chooses plan -> card number/copy -> uploads test JPEG/PNG/PDF receipt -> admin preview -> admin approval -> customer subscription reflects intended plan. Verify idempotency, failed/rejected resubmission and receipt version history. Do not use actual bank transfer. Owner's next step is to test this flow in Production's test-only environment. No database state changes performed in this checkpoint.

## 2026-10-17 — Production manual payment receipt acceptance (verified)

- **User browser evidence:** Experimental customer successfully uploaded a receipt through `directpilot.ir`, and Super Admin received and opened it in the admin payment view. Customer upload + admin receipt visibility: **PASS (owner confirmed)**.
- **Independent read-only Neon evidence, `directpilot_live`:** Latest manual-card-transfer payment created 2026-10-17 10:05:29Z; receipt submitted 10:05:50Z and payment marked `approved` at 10:06:26Z; order `paid`; one linked subscription `active` with a valid future period end. Current aggregate: 2 manual payments, both with inline receipt bytes, 2 receipt-version records. Latest receipt: 67,073 bytes; current bytes equal the version-1 archive bytes; recorded SHA-256 and byte sizes agree. **Status of DB payment approval + subscription activation: PASS (database evidence)**. No payment was created or approved by the assistant.
- **Limits:** Browser display of the active customer subscription after approval is *not yet owner-confirmed*; customer card-copy button, rejected receipt resubmission/version 2, Meta/AI/provider payment integrations, backup resilience are *not verified*. No real bank transfer required. Never log receipt contents, card values, user emails or tokens in the release notes.

**Release Register entry:** 2026-10-17 Production test-only Commerce Acceptance. Customer receipt upload PASS (manual); admin receipt preview PASS (manual); durable bytea + receipt history PASS (Neon read only); `approved` payment, `paid` order and active linked entitlement PASS (Neon read only). Final customer subscription UI verification **PENDING**, as are invalid/rejected receipt flows. Code baseline is merged Backend PR #47; Production Vercel Backend and Neon in use. This entry **does not claim** full live payment gateway readiness.

## 2026-10-17 — Production manual card-transfer subscription lifecycle accepted

**Owner final manual acceptance: PASS.** The user confirmed that, following the successfully tested experimental customer's order, manual receipt upload, Super Admin receipt viewing and payment approval, the customer portal displays the purchased plan as **active** with the **correct expiration date**. This closes the previously OPEN customer subscription UI acceptance criterion. Independent earlier read-only Neon checks established the matching `approved` manual payment, `paid` subscription order, `active` linked subscription and valid future `current_period_end`, plus intact receipt bytes and version history.

**Scope of PASS:** the normal end-to-end test-only card-to-card purchase and subscription activation path, including customer subscription display. The user performed the browser interactions and gave acceptance; the assistant performed read-only database checks. No real money transfer or assistant-initiated payment approval. Not included: rejected receipt -> resubmission and version 2, concurrency/idempotency edge cases, actual bank settlement, third-party payment gateways, Meta DM/Story/Comment automations, AI request billing, independent backup/restore, or deletion of Render.

**Release Register:** Record as final **Production (experimental) card-transfer E2E = PASS / OWNER ACCEPTED**; keep unrelated providers and exceptional cases as NOT TESTED. Current deploy topology stays Vercel frontend/backend -> Neon `directpilot_live`.

## 2026-10-17 — Infrastructure vs integrations audit (Render retirement blocked)

**Audit after user asked whether Render dependencies and all environment variables were migrated: Answer NO.** Production public web → Vercel `directpilot-prod-api` → Neon `directpilot_live` is tested and working for customer/admin login and manual card-transfer workflow. This does NOT mean all provider integrations and secrets were migrated.

**Connected Vercel inspection (configuration names only, not secret values):** Backend project `directpilot-prod-api` currently has **14 environment keys**, including `DATABASE_URL`, `APP_ENV`, `APPLICATION_SECRET`, `INSTAGRAM_TOKEN_ENCRYPTION_KEY`, `TRUSTED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `FORCE_HTTPS`, `SESSION_COOKIE_SECURE`, `LEGACY_ADMIN_ADAPTER_ENABLED`, `DEBUG`, `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `META_SEND_ENABLED`, `META_CONTENT_PUBLISH_ENABLED`. It does **not** show `META_APP_ID`, `META_APP_SECRET`, `META_VERIFY_TOKEN`, `META_OAUTH_REDIRECT_URI`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `KPAY_ACCESS_TOKEN`, or `PAYEXA_API_KEY`. Outbound Meta send/publish was configured OFF for cutover. A Fernet encryption key *exists*, but it was newly provisioned rather than copied from inaccessible Render secret; it may not decrypt historical tokens.

**Neon read-only Meta inventory:** 1 Instagram connection row with database status `active` and an encrypted access token, 18 historical webhook delivery rows and 7 inbound events; latest recorded webhook at 2026-10-11 07:28:59Z. Database status `active` is NOT validation of current OAuth token decryptability, Meta webhook routing or working DM/Story/Comment automation.

**Render inventory:** Both `directpilot-api` and `directpilot-uat-api` remain provisioned and not suspended, autoDeploy=off. Frontend Production API proxy no longer uses Render for its normal requests, but Meta OAuth/webhook callback addresses and third-party callbacks have not been independently verified, so **zero external Render dependency is NOT established**.

**Exit gate before Render retirement:** Retrieve original Render secret values through an owner-controlled secure channel where technically possible (never in chat/repo); restore valid Meta app/verify/webhook/OAuth configuration and confirm developer-dashboard callback URLs target Vercel; handle old Fernet-encrypted tokens by restoring the original encryption key or reconnecting Instagram; configure/test AI/payment-provider secrets where needed; test DM, Story, Comment, callbacks, media uploads, retries and UAT; confirm backups. Only then consider a separately approved shutdown/deletion of Render resources. Do not write invented API keys or say migration is complete.

## 2026-10-17 — Meta Production environment-variable inventory (user completed)

Owner confirmed they created the Meta variables on Vercel. Connector-verified `directpilot-prod-api` environment now has **27 keys**, up from 14, including these 13 new **Production-only** Meta keys: `META_VERIFY_TOKEN`, `META_SIGNATURE_REQUIRED`, `META_SEND_ALLOWED_ACCOUNT_IDS`, `META_RELAY_TIMEOUT_SECONDS`, `META_OAUTH_TOKEN_URL`, `META_OAUTH_TIMEOUT_SECONDS`, `META_OAUTH_STATE_TTL_MINUTES`, `META_OAUTH_STATE_PREFIX`, `META_OAUTH_REDIRECT_URI`, `META_OAUTH_AUTHORIZE_URL`, `META_GRAPH_BASE_URL`, `META_APP_SECRET`, `META_APP_ID`. Existing `META_SEND_ENABLED` and `META_CONTENT_PUBLISH_ENABLED` remain configured OFF, and existing `INSTAGRAM_TOKEN_ENCRYPTION_KEY` was created during cutover (NOT confirmed to match historical Render Fernet key). **Sensitive values are not exposed by the connector and were not validated; configuration presence does not prove validity, Meta callback registration, token decryptability or integration readiness.** Production OAuth callback path in Backend: `/api/v1/integrations/instagram/callback`; webhook path: `/api/v1/integrations/instagram/webhook`. Meta relay target keys shown blank in owner screenshot; leave blank for Production per validation policy. Next critical prerequisite is replacing existing Vercel `INSTAGRAM_TOKEN_ENCRYPTION_KEY` with the same old Production Render value (owner copies directly in provider consoles, never chat), **OR** arranging Instagram account reauthorization if original key cannot be recovered. Then verify authorized Meta developer OAuth redirect/Webhook URLs and redeploy and smoke-test before enabling outbound sends. `META_API_VERSION` optional Vercel variable not present, code default `v24.0`. Render deletion remains blocked.

## 2026-10-17 — Instagram Fernet key transfer, OAuth correction and security smoke

**Owner action and Vercel confirmation:** Owner states the original `INSTAGRAM_TOKEN_ENCRYPTION_KEY` was copied directly from old Render Production to Vercel `directpilot-prod-api` without sharing its value. Vercel metadata confirms this sensitive variable was updated at 2026-10-17 (Unix milliseconds 1792233378759). This confirms a change, **NOT cryptographic equality or ability to decrypt historical Instagram tokens**. No secret exposed in GitHub or chat.

**Production configuration:** `META_OAUTH_REDIRECT_URI` in Vercel Production was set to **`https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`**. Vercel Production `META_SEND_ENABLED=false` and `META_CONTENT_PUBLISH_ENABLED=false` remain unchanged. Other 13 Meta keys previously entered by owner present but sensitive values unverifiable.

**Release:** Independent Vercel Production API deployed from known/merged Backend SHA `df4da87a883c590fb649d8a9f5aff2f80de5fa28`, deployment **`dpl_4jxhit3evN5CCUwYDAJV7aEgZ9Ct` READY** and alias `directpilot-prod-api.vercel.app` assigned. After deploy, GitHub Actions [Neon API health smoke](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39018969331) rerun **PASS** (GET /ready -> HTTP 200, status=ready, database=available, migration=current; /live 200, /version 200).

**Meta negative-path smoke [#39025898052](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39025898052) PASS:** Meta webhook verification GET with deliberately wrong verify token -> **HTTP 403**; unsigned/invalid HMAC webhook POST -> **HTTP 401**; OAuth callback without code/state -> **HTTP 422**. These checks establish endpoints accessible and security configuration loaded, **NOT** Meta Developer console callback configuration, valid OAuth, decryption of historic encrypted tokens, actual webhook deliveries, or outbound replies.

**Next owner step:** In Meta Developers for the corresponding app, allowlist OAuth redirect EXACTLY `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`; update Webhooks Callback URL EXACTLY `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/webhook` and use the unchanged same `META_VERIFY_TOKEN` value in Meta UI (do not paste into chat). Save/verify and test one isolated Instagram reauthorization and webhook. Do not flip Meta sending/publishing to true or decommission Render yet. No real Meta send initiated.

## 2026-10-17 — Meta Graph code 101 is not proof of invalid Instagram Login credentials

Owner ran read-only PowerShell Meta diagnostic. A no-token `GET https://graph.facebook.com/v24.0/me` returned HTTP 400 (normal, Graph reachable), whereas Facebook Graph app-token issuance `POST https://graph.facebook.com/v24.0/oauth/access_token` with locally entered credentials returned HTTP 400, Graph `OAuthException` code **101** (commonly invalid Facebook application ID). **Critical correction:** DirectPilot backend `app/instagram_onboarding/provider.py` explicitly uses **Instagram API with Instagram Login**, with `https://www.instagram.com/oauth/authorize` and `https://api.instagram.com/oauth/access_token`; its `META_APP_ID`/`META_APP_SECRET` are the credential pair used as Instagram `client_id`/`client_secret`. Meta's **Instagram App ID/Secret** can differ from the main **Facebook Meta App ID/Secret** used by `graph.facebook.com`. Consequently the Graph 101 diagnostic **cannot validate or invalidate an Instagram App ID/Secret pair** and must not trigger unjustified credential rotation. The earlier scripts v2/v3 targeted the wrong API for this architecture unless supplied the *Facebook app* credential pair.

**Safest next step:** Ask owner which source they used for Vercel `META_APP_ID`/`META_APP_SECRET` (Instagram → API setup with Instagram Login, Meta App Settings → Basic, or Render previous production); do not ask them to transmit either value. Then check correct Instagram Login pair and the original Meta Developer registered callback. Never enable sending or disconnect Render before verified real OAuth/Webhook tests. Current status `META_FERNET_TRANSFER_OWNER_REPORTED / BACKEND_HEALTH_PASS / META_NEGATIVE_SECURITY_PASS / INSTAGRAM_OAUTH_REAL_UNVERIFIED / META_DASHBOARD_LOGIN_BLOCKED / RENDER_RETIREMENT_BLOCKED`. No Meta subscriptions, tokens, or environment settings changed in these read-only probes.


## 2026-10-18 — TelBot T1 offline Manager delivery contract (review pending)

**Scope/approval:** Owner requested continuing TelBot development, after six-file review. Isolated branch `feature/telbot-telegram-delivery-contract-20261018` originates from `feature/telegram-managed-bots-spike-20261017`; no Instagram backend-main merge, Production deployment, Neon mutation or Telegram outbound authorization.
**Changed:** `experiments/telegram_bot_builder/delivery_contract.py` and `test_delivery_contract.py` provide a pure validated Telegram sendMessage payload for a pre-authorized managed-bot ticket and five offline test cases. They do NOT deliver messages, access a token or mark a ticket sent. This is only a preparation step, not BotFather provisioning or live integration.
**Evidence:** Files committed on isolated branch; automated CI and deployment status PENDING until verified on PR. UAT API project creation using connected Vercel in team `mohcenp-9857s-projects` failed with HTTP **403 Forbidden**; no project created. Do not retry the unchanged API permission context and do not claim UAT READY.
**Release status:** UAT CODE ONLY / NOT DEPLOYED / Owner live acceptance PENDING; Production unchanged.
**Next:** Review CI, provision Manager Bot via official BotFather by Owner, configure a dedicated TelBot UAT service with secret values entered only in provider secret store and restricted Neon runtime credentials; then implement an authorized sendMessage transport with idempotency and delivery reconciliation before any live UAT.


## 2026-10-18 — TelBot standalone Vercel UAT project provisioned (not deployed)

**Owner approval:** "انجام بده" for creating the standalone TelBot UAT service after project-access diagnosis.
**Verified provider state:** Created new Vercel project `directpilot-telbot-uat-api` (ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`) under team `team_Cu7IBomJgSNCXUMp3sILUUD4`; independently re-read with Vercel get_project: `live=false`, `latestDeployment=null`, no domains, no deployment. Previous 403 was bypassed by omitting the incorrectly scoped team parameter, without modifying existing projects.
**Safety:** No source deployed, no Git production branch connected, no credentials copied, no Telegram sending/webhooks activated, no Neon data/schema changes and no Instagram production changes.
**Next gate:** Configure package root `experiments/telegram_bot_builder` from isolated TelBot branch, restricted Neon UAT runtime login, and secure provider environment variables `TELBOT_ENV`, `TELBOT_UAT_DATABASE_URL`, `TELBOT_MANAGER_TOKEN`, `TELBOT_MANAGER_WEBHOOK_SECRET`, `TELBOT_TOKEN_FERNET_KEY`. Owner must create BotFather Manager Bot and enter its token in secret store (never chat/Git). Deployment and Telegram outbound need separate validation and owner approval.

## 2026-10-18 — TelBot Vercel preview deploy gate

Existing independent project `directpilot-telbot-uat-api` confirmed by Vercel project read, ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`; no latest deployment and no environment variables. PR #64 GitHub isolated TelBot workflow `39139955406` and general CI `39139955392` both completed SUCCESS (source head `105b9f9974447ac3934b094261f0d38e826e19c4`). A **preview-only**, source-file deployment was attempted to this exact project, using the isolated TelBot API package without credentials. Vercel returned HTTP 402 `api-deployments-free-per-day`, retryAfter 86400; deployment NOT created, no Production actions, no live Telegram sending, no Neon writes. Do not represent CI success as deployed acceptance. Next: wait for quota reset or owner-approved plan choice; reattempt preview only, then verify `/live` 200 and `/ready` fail-closed 503 before configuring any scoped secrets. Owner must provision BotFather Manager Bot and enter token directly into provider secret store, never chat.

## 2026-10-18 — TelBot first Git deployment and requirements fix

Owner authorized continuing deployment. Independent Vercel TelBot UAT project `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L` built Git source from isolated spike SHA `e5c1f02272117b830695e7ea8c5dc4669af52784`, deployment `dpl_8BPXE14GxxXBwHRpNJHPByBhqiNS`. Deployment **ERROR** `PYTHON_REQUIREMENTS_PARSE_ERROR`: Vercel could not parse `requirements.txt` indirect `-r requirements-uat.txt`. Fixed by inlining dependencies in `experiments/telegram_bot_builder/requirements.txt` on isolated child branch `feature/telbot-telegram-delivery-contract-20261018`, commit `83a0aff443b199c950ee90d76f95d00e1624aadf`. New Git deployment request without target (Preview) blocked by 402 `api-deployments-free-per-day`, retryAfter 86400. No READY deployment, no live endpoint acceptance, no credentials or Neon/Telegram changes. Production DirectPilot untouched. Do not claim fixed build PASS until fresh deployment succeeds. Next: retry after quota reset, check exact SHA and `/live` 200 `/ready` 503; keep production bot outbound disabled.

## 2026-10-18 — TelBot PR #64 merged; first Git deployment READY

- **Owner authorization:** merge isolated TelBot PR #64 and test the existing independent TelBot Vercel project; NO approval to merge `backend-main`, enable live Telegram sending, or change Instagram Production.
- **Git:** PR https://github.com/namach2727-coder/Sales-Agent/pull/64 merged via squash to `feature/telegram-managed-bots-spike-20261017`, SHA `4a20712f514acf935bbaf8f537d54f740225c7a7`. Changes: offline validated managed-bot delivery contract + 5 tests; corrected standalone `requirements.txt`; six continuity files. Previous `e5c1f02` dependency-parse failure superseded only for this revision.
- **CI:** final PR head `c65ba4a`, general GitHub CI run `39143095922` SUCCESS; isolated TelBot run `39143095920` SUCCESS. Vercel statuses on this prior head included build-rate-limit failures and do not represent source test failures.
- **Vercel:** existing isolated project `directpilot-telbot-uat-api`, ID `prj_kmClcJwNEibzo7s1Vrf5BzCg8W4L`, automatically deployed exact merged SHA. Deployment `dpl_BMzrZe4RmXE7ecdUph3zYHstZHeb` **READY**, Git branch and SHA verified via get_deployment; apex alias `directpilot-telbot-uat-api.vercel.app` verified pointing to that deployment. Vercel target label `production` refers ONLY to TelBot UAT project, not Instagram Production.
- **Acceptance limitations:** HTTP `/live` and `/ready` could not be independently verified from assistant runtime due DNS/network restrictions. No Manager Bot token, database URL, webhook secret, or Fernet key configured; Telegram enrollment/live outbound and Neon runtime integration are NOT accepted/active. Build READY does not equal API-ready.
- **Next:** verify public `/live`=200 and safe-unconfigured `/ready`=503 using browser or connected runtime; then configure UAT-only limited Neon role credentials and owner-managed BotFather Manager Bot via provider secret store, never chat. No production migration or live bot sends without explicit owner GO.

## 2026-10-19 — TelBot native Vercel FastAPI routing correction

User opened `/live` on `directpilot-telbot-uat-api.vercel.app` and received FastAPI `{"detail":"Not Found"`, despite READY build and source-defined `/live`. The deployed `vercel.json` had catch-all rewrite `/ (.*)` → `/api/index.py`; latest Vercel FastAPI route handling treats rewritten destination path as runtime route, consistent with 404. Corrective isolated branch `feature/telbot-fastapi-vercel-routing-20261019` adds standard root `app.py` exporting the isolated `api.py` FastAPI instance, removes catch-all rewrite, retains `framework: fastapi`. No secrets, schema, telemetry, or Telegram outbound changed. Acceptance pending new CI + auto-build; test `/live` 200 and `/ready` 503, plus `/` expected 404 unless status root explicitly added. Never infer runtime pass from build READY.

## 2026-10-19 — Temporary UAT Neon owner bootstrap

Owner explicitly authorized use of Neon `telbot_owner` credentials for **isolated TelBot UAT only**. Vercel project `directpilot-telbot-uat-api` now has a Sensitive `TELBOT_UAT_DATABASE_URL` plus `TELBOT_ENV=uat` (values NOT copied into docs). Existing `api.py` rejected this connection because only `telbot_ua_runtime` was allowed. Isolated branch `feature/telbot-uat-owner-connection-20261019` now accepts `telbot_owner` **or** `telbot_ua_runtime` while retaining `TELBOT_ENV`, database name `telbot`, and UAT schema marker checks. Owner access is temporary; revert to least-privileged UAT runtime role before real user onboarding. No DirectPilot Instagram production, Telegram live sending, or Neon production branch modifications. Acceptance: PR checks, merge to TelBot-only branch, Vercel READY, observe `/ready`: manager-config 503 expected until token/secret configured; database unavailable means investigate Neon connection and deployment env.


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
| PR | Git ref / SHA | UAT deployment | Production | Customer acceptance | Evidence |
| --- | --- | --- | --- | --- | --- |
| [#103](https://github.com/namach2727-coder/Sales-Agent/pull/103) | feature/telegram-managed-bots-spike-20261017; reviewed dfac4cb9c52d77379b926e7885ecfd0d80103a51; merged c08a3c26422ad2d28036946c274b035216fff8c0 | BLOCKED: Vercel daily build quota; alias still PR #102 bee4a84d / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA | No change; not promoted | Menu layout previously accepted; new preview/mobile/provider acceptance pending | All 11 GitHub checks SUCCESS, 125 unique Python cases across two jobs, DOM PASS; merged Git status explicitly rate limited |

PR #103 reviewed head dfac4cb9c52d77379b926e7885ecfd0d80103a51 passed all 11 reported GitHub checks, including dedicated TelBot unit/DOM, PostgreSQL18 schema and both generic backend runs. Squash merge c08a3c26422ad2d28036946c274b035216fff8c0 ONLY into feature/telegram-managed-bots-spike-20261017. Python: 123 cases PASS in unit job plus 2 PostgreSQL cases PASS in schema job (125 unique); actual app.js DOM PASS. Standalone Vercel-style import PASS. Vercel rejected this exact merged SHA with "Deployment rate limited — retry in 24 hours." No new TelBot deployment exists; official alias remains READY on PR #102 bee4a84d3686def8eca40628c2d7bc24f993365f / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA. Preview is MERGED, NOT LIVE. No repeat deployment, upgrade, flag change, migration or saved customer-setting mutation performed. Owner mobile/preview/provider acceptance remain separate and pending.

Final read-only checkpoint 2026-10-28 18:09 UTC: official alias still points to dpl_DdZH5HGsp9wKri61GTtwsYbopLLA; /ready 200 (database available/migration current), /telbot and published JS 200 show rules-api-3 and no preview control/cache revision. Vercel environment metadata has six keys and neither outbound flag. This verifies the prior live release remains healthy, not deployment of PR #103.
