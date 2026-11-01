## 2026-11-01 — CURRENT: combined TelBot UAT release #108–#111 LIVE / READY

Supersedes the historical Vercel quota blocker: PR #111 https://github.com/namach2727-coder/Sales-Agent/pull/111 reviewed head c1d106287e52abb133258b56ef1414cd360b0fe4 passed ALL 11 reported checks. Squash merge 69f3858c60d3ca531c48798610eac55e98db9407 ONLY into feature/telegram-managed-bots-spike-20261017 equals the reviewed tree. Automatic deployment dpl_Gr3NmxVt57kFkd4FNKjbj5bxu1FK READY on that exact merge; canonical https://directpilot-telbot-uat-api.vercel.app points to it. No duplicate/manual deploy or plan upgrade. Target production here is the isolated TelBot UAT project, not business Production.

All four features are now DEPLOYED: #108 optional keyword menu buttons with inert mobile preview; #109 private 24-hour activity/last-20 delivery report; #110 audited owner/editor Pause/Resume with durable paused receipts and no replay; #111 local search and explicit text/API copying, including corrected text-to-API credential source identity. Mobile/focus/direct Save/optional blank-next-row/readback invariants remain. Source assets use 20261029-rule-library-1 revision; the date in that cache key is not the deployment date.

Verified 2026-11-01 06:33–06:34 UTC / 10:03–10:04 Asia/Tehran: /ready HTTP 200 ready/database available/migration current; /telbot, JS and CSS HTTP 200 and byte-identical to reviewed source. Unauthenticated activity GET 401; unauthenticated reply-state POST using synthetic UUIDs 401 missing_init_data. Environment metadata: 7 keys, TELBOT_ENV=uat and TELBOT_REPLIES_ENABLED=true; external API flag absent/default OFF. No secret value retrieved. Fresh read-only Neon UAT before/after release: 1 active bot, 0 paused, published v6, 2 saved keyword rules, 0 menu buttons. No real customer configuration/status, schema, credential, provider call, actual Telegram send or business Production mutation was performed by deployment/testing.

CI evidence on reviewed head: unit job 123620031044 ran 141 discovered (136 PASS + 5 PostgreSQL skips); schema job 123620030513 ran all 5 PASS including real UI/HTTP/PostgreSQL copied-response two-save/reopen, saved API credential clone/redaction, menu/history retention, report scope/window/counts, and pause/receipt/resume/duplicate/no replay. Both actual app.js DOM/focus/search/copy/report/control and seven Save error/readback scenarios PASS. Infrastructure/CI is NOT owner phone/native Telegram acceptance.

NEXT OWNER ACCEPTANCE: reopen a fresh Telegram Mini App, test search and Copy with a NEW trigger, Save/close/reopen. Select a response's menu checkbox and Save, then send /start and tap the button in the private child bot. Refresh activity report. Explicitly Pause, send a fresh message (receipt without response), Resume and send another fresh message (no historical replay). Already-reserved sends may finish, as stated in UI. Record these live/native outcomes separately; none is inferred from READY. Keep external APIs OFF until separately authorized provider testing. Production not promoted.

---

## 2026-10-29 — CURRENT PR #110 pause/resume MERGED; combined UAT deployment quota BLOCKED

PR #110 https://github.com/namach2727-coder/Sales-Agent/pull/110 reviewed head ee25a6e32cf541a384d30f0a7ee0a4ec30a4f66f passed ALL 11 reported GitHub checks. Squash merge 95820708380036aa1ffccd412e58f1cd22929e54 ONLY into feature/telegram-managed-bots-spike-20261017 matches the reviewed tree. This combined source includes #108 menu, #109 activity and #110 owner/editor Pause/Resume. Vercel TelBot status on this exact merge is FAILURE: "Deployment rate limited — retry in 24 hours." All three features are MERGED, NOT LIVE. No manual deployment retry, quota workaround or plan change.

Canonical https://directpilot-telbot-uat-api.vercel.app still points to dpl_7rjBLHUqRRQ5RaiFniN2R8SoqjR5 / prior d772844 optional-reply source. Fresh /ready HTTP 200 database available/migration current. Direct read-only UAT: 1 active bot, 0 paused bots, published v6 with 2 keyword rules. No real customer status/configuration was changed by this work; no actual Telegram/provider test. Reply flag remains ON, external API OFF. No schema, secret, billing or business Production change.

Delivered in reviewed code: expected-state tenant/role-guarded Pause/Resume plus atomic audit; local progress/error and preserved editor; paused authenticated receipts persist/dedupe without vault/API/send; observed-paused receipt cannot slip through racing Resume; current-state shared decision lock serializes Pause until pre-network durable attempt commit. Already-reserved/in-flight attempts may finish and UI says so. Resume never replays old/paused/uncertain messages. Pending/revoked/unready bots cannot use Resume to bypass activation; service global OFF remains OFF.

CI unit job 123609004576 ran 141 discovered (136 PASS + 5 PostgreSQL skips); schema job 123609005120 ran all 5 PASS, including real share-lock conflict, audited API transitions, ignored paused receipt/no outbound, Resume+duplicate/no replay and one NEW mocked reply. Actual JS/HTTP/PostgreSQL save/reopen/menu/report regression also PASS. DOM pause delayed/duplicate/error/expected-state/editor-focus, report/menu and seven Save scenarios PASS. Standalone Vercel-style reply-control import/route PASS locally. Actual phone/Telegram pause acceptance PENDING.

NEXT: after quota permits, deploy exact reviewed combined source 95820708380036aa1ffccd412e58f1cd22929e54 ONCE in existing isolated TelBot UAT project (production target here means UAT only); require READY/exact canonical alias/reply-control-1 source assets, /ready and unauthenticated activity/control 401. Owner then tests menu, report and Pause -> private message stored/no response -> Resume -> old duplicate not replayed/new message responds. Keep customer acceptance separate from CI. Update these checkpoints. No TelBot release retry automation created.

---

# TelBot per-bot reply control — 2026-10-29

## Owner flow and contract

Bot cards offer «توقف پاسخ خودکار» for active bots and «ادامهٔ پاسخ خودکار» for paused bots, only to owner/editor. Feedback appears next to the same control immediately. A transition updates the card status and button in place; an open response editor is not rebuilt. Failure retains the last known state and re-enables the control. No activation, token rotation, webhook registration or global env flag mutation occurs.

Pause affects new reply decisions. Webhook remains registered and authenticated, and paused receipts are stored/deduplicated with reply processing ignored. There is no historical replay when resumed. Already-reserved attempts may finish after the Pause acknowledgment; the UI explicitly says this. The bot's per-chat pause behavior is unchanged. An active bot with global sending OFF remains OFF and the endpoint/UI state says so.

## API and concurrency

POST /api/v1/tenants/{tenant_id}/bots/{bot_id}/reply-state accepts paused boolean plus expected_status active|paused, with extra fields forbidden. Active tenant membership with owner/editor write role is mandatory; exact bot scope excludes revoked bots. Pending status, stale expected status, missing activation credentials/digest or a concurrent changed row fails closed. UPDATE and bot_replies_paused/bot_replies_resumed audit insert commit atomically; already-desired state does not write another event. No config/version changes and no vault decryption/provider/Telegram request.

The winning child webhook receipt still commits before runtime. Its observed paused status suppresses it even if Resume wins immediately afterward. For other receipts, runtime SELECT status scoped to tenant+bot FOR SHARE holds the decision lock through durable attempt reservation and releases it at the existing pre-network commit. Pause UPDATE conflicts with that share lock. No network operation is performed while this bot decision lock is held. Pause does not cancel an attempt already durably reserved. This preserves at-most-once loss/uncertainty caveats and forbids blind retry.

## Validation and release gates

Local 141 Python discovered: 136 PASS, 5 disposable PostgreSQL skips. DOM tests cover duplicate tap, delayed success, failed resume retaining state, successful resume, unchanged editor identity/focus and expected_status payloads. Existing report/menu/save tests remain. New CI PostgreSQL case checks share lock blocking a status UPDATE, endpoint pause/audit, paused authenticated child receipt and ignored status without outbound, Resume, old duplicate receipt without resend, then one new reply via mocked transport. No real cloud customer status or actual messages changed by tests.

Previous menu #108 and activity #109 await deployment because Vercel daily quota rejected release. Finish CI and review exact source, merge only isolated TelBot branch, then one combined deployment when quota permits; verify exact READY alias/assets/health/auth before owner tests Pause, private message, report receipt, Resume and new private message. Actual phone and actual Telegram behavior must be recorded independently. No Production promotion.

Rollback preserves audit/inbound evidence. If a bot is paused, old code only accepting active bots would reject paused webhook receipts; owner should Resume through the new control before rollback when appropriate. Do not silently auto-resume customers or rewrite DB statuses as a deployment step.
