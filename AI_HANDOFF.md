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

# DirectPilot — AI Handoff (Current, concise)

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

**Next handoff:** Read all six files and linked checklist. First test `/ready` on current TelBot UAT alias after #67; distinguish DB unavailable from missing Manager settings. Do not move actual tokens/credentials to chat or Git.

---


**وضعیت as-of:** 2026-10-15. **مرجع حقیقت:** [Release Register](docs/releases/RELEASE_REGISTER.md). **منبع شواهد تاریخی بدون حذف:** [Archive Manifest](docs/runbooks/history/20261015_pre_release_register/README.md). برای تصمیم‌های انتشار، همیشه نتیجه GitHub، Vercel Alias، Neon و Render را دوباره بررسی کن.

## در شروع هر چت DirectPilot

این پنج سند را به‌ترتیب بخوان: `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`. سپس ردیف‌های مربوط در `docs/releases/RELEASE_REGISTER.md`، Runbookها و SHA واقعی Deploy را بررسی کن. از کاربر نخواه تصمیم ذخیره‌سازی، UAT URL، تاریخچه رسید یا ناوبری را دوباره توضیح دهد. جزئیات گذشته در Archive با SHA برابر فایل اصلی وجود دارند.

## آخرین پذیرش Owner و جلوگیری از تکرار

**P0-HEALTH-01 — UAT Health & Integration Audit:** مطابق اعلام صریح Owner در ۲۰۲۶-۱۰-۱۵ **ACCEPTED / CLOSED BY OWNER** است و نباید دوباره به‌عنوان کار باز یا پیش‌نیاز تکراری مطرح شود. دامنه تأیید: بررسی اتصال Frontend/Backend/Neon، سلامت ثبت‌نام/ورود/خروج/Session، دریافت پلن/Trial و خطاهای حیاتی UAT طبق چک‌لیست P0-01 مکالمه. این تأیید کاربر جایگزین شواهد ثبت‌نشده CI، تست مستقل یا تأیید E2E خرید، Meta و Production نیست. فقط در صورت Regression جدید با شواهد مشخص بازگشایی شود.

**اقدام بعدی:** P0-02، تکمیل و پذیرش جریان Auth و سپس ثبت‌نام تا پرداخت؛ از ارجاع مجدد به P0-HEALTH-01 خودداری کن.

## مرز محیط‌ها

- **UAT:** `https://uat.directpilot.ir` → Frontend Vercel `directpilot-web` Branch `UAT`, SHA `dad3a3790246f96fbbe760d26e2415afd0a45851`, deployment `dpl_GGgg4EkaQF3bExfnzbfgRBK1GLhj` READY. Branch-only Preview vars: `DIRECTPILOT_API_UPSTREAM=https://directpilot-uat-api.vercel.app`, `NEXT_PUBLIC_SITE_URL=https://uat.directpilot.ir`.
- **UAT Backend:** `directpilot-uat-api.vercel.app` روی Git `Sales-Agent/migration/vercel-uat-fastapi-20261014` با Neon UAT `neondb` مستقل، Alembic `0027_traceable_receipt_versions`; smoke/ready PASS. HTML صفحات ممکن است با Vercel SSO محافظت شوند.
- **Production:** `directpilot.ir` و `www.directpilot.ir` → Frontend Branch `main`, SHA `8592c6e91d4beaed7c31653dc285612fd511fa53`; Backend/DB Render مرجع است. **Production Neon همگام‌سازی نهایی تأییدشده ندارد**. نبود دسترسی read-only به DB Render مجوز حدس‌زدن وضعیت عملیاتی نیست.

## تصمیم‌ها و محدودیت‌های دائمی

1. تصاویر محصولات و همه نسخه‌های رسید پرداخت باید در **PostgreSQL BYTEA** باشند؛ **R2/S3 ممنوع** مگر تصمیم جدید Owner. هر رسید به مشتری/tenant/فروشگاه/سفارش/پرداخت، زمان، SHA-256 و تاریخچه ادمین متصل باشد؛ چهار ماه یا بیشتر قابل بازیابی. نسخه‌های قبلی پس از آپلود مجدد پاک نشوند. Backup مستقل و SLA عملیاتی هنوز PENDING.
2. **پلن‌های واقعی فقط از DB/API**: در Neon UAT فقط `AUTOMATION_V1` و `AI_ASSISTANT_V1` دارای `is_purchasable=true`اند، دو Trial تخصصی `trial_eligible=true` و **۳روزه**‌اند؛ `TRIAL` قدیمی قابل انتخاب Trial تازه نیست. قیمت‌های IRR، محدودیت‌ها و جدول هشت‌ردیفی در Release Register. کاتالوگ Production از UAT قابل استنتاج نیست.
3. **DM/Story/Comment هم‌زمان** در UAT یک فرم checkbox اما **یک Rule مستقل برای هر کانال** است؛ هر Rule یک ظرفیت پلن مصرف می‌کند، ثبت ترتیبی و امکان موفقیت ناقص. Meta سه‌کاناله E2E هنوز باز است.
4. ناوبری موبایل UAT باید Back/Close واضح و خروج بدون گیرکردن در منو/فرم داشته باشد. F#32 در UAT منتشر و ۲۲۳ تست PASS؛ تست لمس روی آیفون/اندروید PENDING.
5. **Release status ≠ signoff:** ادغام PR، PASS تست، READY در Vercel، PASS مرورگر، پذیرش کسب‌وکار و GO Production شش سطح مستقل‌اند. کاربر مستندسازی شش مورد را تأیید کرده، **نه GO Production**.

## تفکیک انتشار

- در SHA فعال Frontend Production: **خرید چندماهه، نمایش/کپی کارت، پیش‌نمایش اولیه رسید** از قبل وجود دارند؛ دوباره به‌عنوان «قابلیت جدید منتقل‌نشده» ثبت نشوند.
- **فقط UAT فعلی:** checkbox چندکاناله F#12، آرشیو نسخه‌دار رسید B#36/F#31، ذخیره تصویر در DB B#34، ورود غیرمسدودشونده F#31 و ناوبری جدید موبایل F#32. برای Production همچنان گیت مستقل دارند.
- SEO/GA4 و Solutions پیش‌تر PRهای Production دارند؛ اندازه‌گیری ردیابی GA4/ایندکس/کارایی جدا از Merge است.

## Runbook و گام بعد

- ثبت انتشار: [RELEASE_REGISTER](docs/releases/RELEASE_REGISTER.md)
- [Signup/Plan/Payment Acceptance](docs/runbooks/uat_customer_billing_acceptance_20261015.md)
- [DM/Story/Comment & Mobile](docs/runbooks/uat_multichannel_mobile_acceptance_20261015.md)
- [UAT Technical Evidence](docs/runbooks/official_uat_acceptance_gate_20261014.md)
- [Mobile Audit](docs/runbooks/uat_mobile_frontend_ux_audit_20261015.md)

**Production Hard Stop:** بدون تأیید مرورگری UAT، حسابرسی دیتابیس و پرداخت، Backup مستقل قابل بازیابی، freeze/replay webhookها، تطبیق دیتای نهایی، برنامه rollback، تطبیق میزبانی تجاری و GO صریح Owner، **هیچ Deployment/DB/DNS/Render/Meta Production انجام نده**.

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

## ۲۰۲۶-۱۰-۱۷ — نتیجه واقعی P0-07 و وضعیت انتقال Schema

P0-07: بکاپ واقعی Production و Restore ایزوله روی کامپیوتر Owner **PASS** (۱۷ اکتبر؛ ۸۲ جدول، Alembic 0025، SHA ثبت‌شده در Release Register). UAT Neon **0027/۸۳ جدول** است. Branch فعلی Backend Production تا **0025** Migration دارد؛ 0026/0027 فقط در Branch UAT هستند؛ **اجرای Schema Migration روی Render بدون کد Backend سازگار ممنوع**. آزمون Migration و Backup مستقل خارج از دستگاه هنوز باز است. جزئیات در `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Neon directpilot_live restore and schema migration

**STATUS: NEON STAGING RESTORE + SCHEMA 0027 PASS (NOT A CUTOVER).** User ran validated local dump restore to empty Neon `directpilot_live` (82 tables; 0025). Two equivalent additive migrations applied transactionally via Neon API; read-only verification: 83 tables, 0027, BYTEA image column and receipt-history table. Render Production still live/unchanged. Backend compatibility, data parity after final sync, secure credential rotation (sensitive connection URL exposed in chat), independent encrypted backup and GO for cutover are **OPEN**. Details: `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Neon role credential rotation after URI exposure

Password for shared Neon Production role `neondb_owner` rotated after URI exposure. Provider read queries on `directpilot_live` (0027) and `neondb` (0025) PASS; new URI retrievable. Old copied URL invalid. No confirmed dependent Render/Vercel environment variables were changed; Vercel sensitive `DATABASE_URL` value was not readable, so actual application connectivity still requires verification. Render live Production remains untouched. Details: `docs/releases/RELEASE_REGISTER.md`.

## 2026-10-17 — Selective Backend release PR #47 (staging only)

- **Source:** `release/prod-neon-0027-backend-20261017` -> draft GitHub PR **#47** (selective UAT PR #34 media/receipt Backend changes + tests), no whole UAT merge and no production deployment. Tracking runbook `docs/runbooks/prod_neon_0027_release_gate_20261017.md` is included on the release branch.
- **Neon staging:** `directpilot_live` has 83 public tables, Alembic `0027_traceable_receipt_versions`. Read-only schema comparison to UAT: 918 column definitions and 530 index definitions have matching fingerprints. Both have 1,137 constraints but constraint text is not byte-identical due in part to PostgreSQL CHECK cast normalization and historical NOT NULL constraint naming; exact constraint equivalence remains a separate review.
- **CI and runtime:** PR #47 started Postgres smoke, PostgreSQL 18 compatibility, Docker build and application tests. Report actual final CI results only after all jobs complete. Render `directpilot-api` remains live on `backend-main` and Render PostgreSQL, with autoDeploy disabled. **Docker startup unconditionally invokes Alembic migrations:** do not deploy this release against live Render while it is still at revision 0025 without explicit authorization.
- **Not cut over:** Render data has likely changed since the Oct 17 static archive; final freeze, fresh backup, independent protected copy, full row-level aggregate reconciliation, isolated backend runtime smoke, signing keys, Meta/payment webhook buffering and explicit Owner GO are pending. The Neon role password was rotated; copied prior URL is stale.

### CI acceptance — PR #47 at 8762c37b (2026-10-17)

GitHub Actions run `39017203961` confirmed **4/4 PASS** on selective release head `8762c37b6a41056b60123a63424901ba8a38199c`: `postgres-smoke`, `postgres18-neon-compatibility`, `docker-build`, and `test` (pytest). PR #47 remains **DRAFT / NOT MERGED**; CI PASS is not real-backend-to-Neon E2E and is not authorization for Production deployment. Live Render database remains the source of truth; fresh write-freeze/final backup/parity and protected cutover still pending.

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

## 2026-10-17 — Receipt upload and admin view PASS

Owner verified that an experimental customer uploaded a receipt and the administrator received and viewed it successfully on the Production site. Independent Neon read-only checks confirm the new manual payment is approved, its associated order is paid, its subscription is active, and its stored receipt matches the version-history copy. Customer subscription UI after approval remains to be visually confirmed. Details are in docs/releases/RELEASE_REGISTER.md.

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
PR #103 reviewed head dfac4cb9c52d77379b926e7885ecfd0d80103a51 passed all 11 reported GitHub checks, including dedicated TelBot unit/DOM, PostgreSQL18 schema and both generic backend runs. Squash merge c08a3c26422ad2d28036946c274b035216fff8c0 ONLY into feature/telegram-managed-bots-spike-20261017. Python: 123 cases PASS in unit job plus 2 PostgreSQL cases PASS in schema job (125 unique); actual app.js DOM PASS. Standalone Vercel-style import PASS. Vercel rejected this exact merged SHA with "Deployment rate limited — retry in 24 hours." No new TelBot deployment exists; official alias remains READY on PR #102 bee4a84d3686def8eca40628c2d7bc24f993365f / dpl_DdZH5HGsp9wKri61GTtwsYbopLLA. Preview is MERGED, NOT LIVE. No repeat deployment, upgrade, flag change, migration or saved customer-setting mutation performed. Owner mobile/preview/provider acceptance remain separate and pending.
Existing multi-reply/API builder remains live. User accepted the prior menu layout. Next action is deployment of exact reviewed preview merge after provider quota resets, then verify alias SHA, assets and /preview auth boundary; do not reimplement or ask the owner to repeat settings.

Final read-only checkpoint 2026-10-28 18:09 UTC: official alias still points to dpl_DdZH5HGsp9wKri61GTtwsYbopLLA; /ready 200 (database available/migration current), /telbot and published JS 200 show rules-api-3 and no preview control/cache revision. Vercel environment metadata has six keys and neither outbound flag. This verifies the prior live release remains healthy, not deployment of PR #103.
