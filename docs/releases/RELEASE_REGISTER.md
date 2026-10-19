# DirectPilot — Release Register (مرجع واحد انتشار)

## 2026-10-19 — MANUAL BotFather bot connection: UAT code under review

**Decision:** `@MhnPdr_bot` token tested by owner: `matches_expected=true`, `can_manage_bots=false`; Telegram BotFather UI on web/mobile does not expose Bot Management Mode to owner. Instead of blocking TelBot, implement optional manual child-bot onboarding. Customer creates/controls their own bot through official BotFather and submits the token **only through a future authenticated HTTPS TelBot UAT interface** (never chat, GitHub, screenshots or analytics). Preserve managed-bot capability as optional future path; do not delete old code.

**Implementation under UAT feature branch** `feature/telbot-manual-bot-connect-uat-20261019`: add `POST /api/v1/tenants/{tenant_id}/bots/connect-manual`, guarded by `TELBOT_ENV=uat` AND `TELBOT_MANUAL_CONNECT_ENABLED=enabled` (disabled by default). Requires Telegram Mini App signed `initData` and tenant OWNER; does read-only Telegram `getMe` to validate owner-supplied credential, verifies bot identity, encrypts token server-side with independent `TELBOT_TOKEN_FERNET_KEY` Fernet secret, inserts into existing `telbot.bots` fields with `credential_key_version=1`, `status=pending`, and logs sanitized audit event. Unique `telegram_bot_id` blocks cross-tenant re-registration. API returns bot public username/ID record reference and `webhook_registered=false`/`message_sending_enabled=false`, never token, ciphertext or raw Telegram errors. HTTP client URL logging disabled to protect token-in-path. No new DB migration. Synthetic offline tests cover encryption and rejection. Verify CI/PR before merge.

**Release gates:** Source code only until PR CI success and controlled UAT deployment. Feature flag must remain DISABLED and `TELBOT_TOKEN_FERNET_KEY` must not be generated in client or Git. UAT Neon has 0 tenants/bots, so customer-facing Mini App, tenant bootstrap and onboarding are **NOT READY** even if backend `/ready` PASS. Do NOT activate webhook, send messages, connect any real/customer bot, change TelBot Neon Production, or change Instagram DirectPilot Production. Only after UAT QA: provision cryptographic key (Sensitive), implement customer-facing input UI, tenant creation, least-privilege runtime role and operator-reviewed webhook/test.

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
