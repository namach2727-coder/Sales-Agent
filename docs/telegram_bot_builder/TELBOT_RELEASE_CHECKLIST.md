# DirectPilot TelBot — T0–T3 Master Checklist

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
