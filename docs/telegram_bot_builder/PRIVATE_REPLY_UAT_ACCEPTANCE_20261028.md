# TelBot private reply UAT acceptance — PR #100

Scope: isolated TelBot branch/service/database only. Instagram and TelBot Production are excluded.

## Verified release baseline

- UAT alias: https://directpilot-telbot-uat-api.vercel.app
- Current alias deployment: dpl_9CpPG3S682sh1PJMN5awe2ZWmY3G, READY.
- Current deployed source: f31249005fee63017e25185fab5f533a1d6fd86f (#98).
- Candidate reply/editor source: a9da4f28f410f90826feb45af173ae874cc37e4e (#100).
- Candidate is NOT on the UAT alias. Vercel Git status reports build-rate-limit.
- Local validation: 94 unittest tests PASS; JavaScript syntax PASS.
- Candidate dedicated TelBot unit-test, Docker and PostgreSQL checks PASS; general backend CI was still running at this checkpoint.

## Release procedure

1. Finish CI for exact candidate SHA; merge only to feature/telegram-managed-bots-spike-20261017 after review. Do not merge backend-main.
2. Once existing Vercel quota permits, build the merged SHA in the existing directpilot-telbot-uat-api project. Its production target is the independent UAT service, not Instagram Production. Do not promote a Preview with different secrets or upgrade plans automatically.
3. Require READY and exact alias-to-SHA evidence. Retain current deployment above for rollback.
4. Keep TELBOT_REPLIES_ENABLED absent/false during editor acceptance. Verify /ready and existing owner login/workspace/bot activation have no regression.
5. Owner/editor opens the bot message form, loads current published text, enters greeting/fallback, saves and publishes. Close/back restores navigation. Viewer cannot write. A configuration with existing keyword rules is deliberately blocked by this basic editor to avoid deleting those rules.
6. Test invalid/blank/oversized text and failed save/publish. Do not retry an uncertain mutation automatically; inspect current published state first. Verify draft-only text is never used by runtime.
7. After explicit live UAT send authorization, enable TELBOT_REPLIES_ENABLED=true only in this service with TELBOT_ENV=uat, deploy exact reviewed source, then test /start and arbitrary text from the owner's private Telegram chat.
8. Verify one sent outbound row with Telegram message ID, matched inbound row marked processed, tenant/bot isolation, paused chat suppression and duplicate receipt producing no second send. Count-only evidence; no tokens or customer message contents in documentation.
9. Record owner mobile UI and real reply acceptance independently. Until then do not mark T2 complete or publicly enable purchases.

## Delivery limitations

At-most-once attempts, not exactly-once Telegram delivery. Attempt is committed before network. Timeout/crash can lose a reply and leave an uncertain queued attempt (attempts=1) or failed delivery_unknown. No automatic resend or recovery worker. Do not replay these rows blindly. Disabled runtime/unpublished bot leaves incoming receipt without sending; no historical catch-up is implemented.

## Stop/rollback

Disable the UAT reply flag for future invocations and restore the verified prior deployment if necessary; already-started sends may finish. Do not delete inbound/outbound audit evidence or change credentials/Production. Investigate cross-tenant behavior, any credential disclosure, duplicate sends or regressions before re-enabling.
