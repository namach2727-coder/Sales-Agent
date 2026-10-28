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
