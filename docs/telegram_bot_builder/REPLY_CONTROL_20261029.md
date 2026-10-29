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
