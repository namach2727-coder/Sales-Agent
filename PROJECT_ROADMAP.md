# DirectPilot Project Roadmap & Continuity Checkpoint

> **Strategic roadmap / secondary continuity document.** Read `AI_HANDOFF.md` first in every new ChatGPT/Codex session; then read this file.
>
> **Last updated:** 2026-10-04
>
> **Current authority rule:** Runtime evidence > deployed commit > repository source > `AI_HANDOFF.md` > this document > old chat history. If reality conflicts with this file, verify reality first and then update this file.
>
> **Secret rule:** This document intentionally records credential **names, owners, locations and status**, but never credential values. Never paste API keys, database passwords/DSNs, Meta tokens, session tokens, encryption keys or payment-provider secrets into Git, chat, logs, screenshots or frontend variables.

---

## 0. Current Resume Marker

```text
PROJECT: DirectPilot
DATE: 2026-10-04

CURRENT_PHASE:
Pilot / market-validation infrastructure with separated UAT and Production

CURRENT_TASK:
POST_SEPARATION_PRODUCTION_REGRESSION_AND_INTEGRATION_SPLIT

UAT_ENVIRONMENT_SEPARATION:
PASS

UAT_E2E_REGISTRATION_SESSION_TRIAL:
PASS

PRODUCTION_E2E_REGISTRATION_SESSION_TRIAL:
PASS (verified before final UAT cutover; rerun regression next)

BACKEND_HEAD_AND_DEPLOYED_COMMIT:
cc6591b6862d4a9b5b33c96509cda0410528c0f2
chore(deploy): separate uat and production config

FRONTEND_ENV_SEPARATION_COMMIT:
ede06b5822b499812cfe24464c737d67bf781014
chore(deploy): separate uat and production config

LATEST_VERIFIED_MIGRATION_HEAD:
0023

NEXT EXACT STEP:
1. Regression-smoke Production after UAT cutover.
2. Verify/separate Meta/OAuth, LLM and payment-provider credentials by environment.
3. Resolve Preview NEXT_PUBLIC_SITE_URL/callback canonical URL if needed.
4. Before real customers, replace/upgrade the expiring Free Production PostgreSQL database and establish backup/restore.
```

Do not restart completed environment-separation work unless runtime evidence proves regression.

---

## 1. Product Direction and Non-Negotiable Invariants

DirectPilot is an **Instagram Sales Automation Platform / AI Sales Assistant**, not a generic Instagram bot or full CRM.

Current product pillars:

1. **Deterministic Automation** — predefined rules/responses; an exact deterministic match performs **ZERO LLM / PromptBuilder / Knowledge retrieval / AI usage**.
2. **AI Assistant** — approved business knowledge + AI fallback; separate commercial product family.
3. **Commerce / Subscription** — plans, immutable order snapshots, payment, subscription activation and entitlement enforcement.
4. **Instagram Channel** — official Meta APIs only for the MVP.
5. **Future Story Product Automation** — story-specific product/offer/price mapping; not yet the active implementation task.

Runtime precedence remains:

```text
Human Takeover
  -> Story-specific Automation   [future Phase 2]
  -> General Deterministic Automation
  -> AI Assistant fallback
```

Other invariants:

- Tenant/store isolation is mandatory and server-side.
- Backend is authoritative for payment, entitlement and subscription state.
- Never activate a subscription from browser/frontend state.
- Commerce activation uses immutable order purchase snapshots.
- Never blindly retry an ambiguous external-provider write.
- Public UUID-style IDs are API boundaries; internal numeric IDs are persistence details.
- Keep the Modular Monolith; do not introduce microservices during MVP.
- Browser API traffic remains same-origin through `/api/v1/*`.
- Do not add a frontend catch-all proxy, unnecessary serverless functions or polling without an explicit architecture decision.
- Preserve unrelated dirty user work. Never reset, clean, auto-stash, force-push, rebase published history or rewrite history.

AI runtime guardrails retained from repository instructions:

```text
GROQ_CONTEXT_LENGTH=4096
GROQ_MAX_OUTPUT_TOKENS=256
```

Do not increase limits merely to hide prompt/context defects.

---

## 2. Repositories, Branches and Local Laptop Paths

### Backend

```text
Local root:
C:\Users\q\Documents\Codex\2026-07-11\referenced-chatgpt-conversation-this-is-untrusted

GitHub:
https://github.com/namach2727-coder/Sales-Agent

Branch:
backend-main

Current repository/deployment commit:
cc6591b6862d4a9b5b33c96509cda0410528c0f2
```

Important recent backend commits:

```text
cc6591b6862d4a9b5b33c96509cda0410528c0f2  chore(deploy): separate uat and production config
54a3ddc55ab2a332c87f873e56b4e96631e3e367  feat(auth): require mobile number at registration
0663e4055ed46290cd39809ef774353eee461129  feat(payments): persist receipt bytes durably
4946ba291ef2cc280c89e88b6ad833321762627f  feat(payments): add admin-managed manual payment cards
62b0023fa42f39480a6aea1098575bb232b6d76d  chore(payexa): log create rejection status
33e774dcd0f298145da55e15dbf24b6632aed287  feat(commerce): add Payexa payment gateway
0f68f9a6e322f64ffb7922007b83e858baf24570  feat(commerce): add safe KPay payment gateway
```

### Frontend

```text
Local root:
C:\Users\q\Documents\Web Site

GitHub:
https://github.com/namach2727-coder/directpilot-web

Production branch:
main

UAT/Preview branch:
UAT

Environment-separation commit verified on main and used to create UAT:
ede06b5822b499812cfe24464c737d67bf781014
```

The `UAT` branch was created from `main` at `ede06b5...`; at creation it was 0 ahead / 0 behind.

### Canonical roadmap location

This file lives in the backend repository:

```text
Sales-Agent/PROJECT_ROADMAP.md
```

Keep one canonical roadmap rather than maintaining divergent backend/frontend copies.

---

## 3. Environment Topology — Production vs UAT

### Production

```text
Browser
  https://directpilot.ir
        |
        v
Vercel Production / frontend branch main
        |
        | same-origin /api/v1/* rewrite
        v
DIRECTPILOT_API_UPSTREAM
  https://directpilot-api.onrender.com
        |
        v
Render service directpilot-api
  APP_ENV=production
        |
        v
Production PostgreSQL
```

### UAT

```text
Browser
  https://uat.directpilot.ir
        |
        v
Vercel Preview / frontend branch UAT
        |
        | same-origin /api/v1/* rewrite
        v
DIRECTPILOT_API_UPSTREAM
  https://directpilot-uat-api.onrender.com
        |
        v
Render service directpilot-uat-api
  APP_ENV=uat
        |
        v
UAT PostgreSQL
```

### Environment-separation approach

The cloud browser must never know or choose the Render backend directly. The frontend uses same-origin `/api/v1/*`; Vercel selects the backend by environment using the **server-only** `DIRECTPILOT_API_UPSTREAM` variable.

Rules implemented in the environment-separation release:

- Production build fails closed if the required upstream is absent/unsafe.
- Production must not target the known UAT backend.
- Preview/UAT may target the UAT backend.
- Local development may retain local behavior when the cloud upstream variable is absent.
- Do not expose the cloud upstream as `NEXT_PUBLIC_*`.
- No new catch-all API proxy function and no polling were introduced.

---

## 4. Addresses, IDs and Operational Endpoints

### 4.1 Production addresses

```text
Primary frontend:
https://directpilot.ir

WWW alias:
https://www.directpilot.ir
(verified configured as 308 redirect to https://directpilot.ir)

Vercel project alias:
https://directpilot-web.vercel.app

Backend:
https://directpilot-api.onrender.com

Backend liveness:
https://directpilot-api.onrender.com/live

Backend readiness:
https://directpilot-api.onrender.com/ready

Backend version:
https://directpilot-api.onrender.com/version

Same-origin public plans:
https://directpilot.ir/api/v1/plans

Authenticated subscription check:
https://directpilot.ir/api/v1/subscription/me

Meta OAuth backend callback target from production example config:
https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback

Instagram webhook API root:
https://directpilot-api.onrender.com/api/v1/integrations/instagram/webhook
```

### 4.2 UAT addresses

```text
Primary UAT frontend:
https://uat.directpilot.ir

Stable Vercel UAT branch domain:
https://directpilot-web-git-uat-mohcenp-9857s-projects.vercel.app

Deployment-specific Preview URL observed during cutover:
https://directpilot-o4mdhzydb-mohcenp-9857s-projects.vercel.app
(ephemeral; do not use as canonical UAT URL)

Backend:
https://directpilot-uat-api.onrender.com

Backend liveness:
https://directpilot-uat-api.onrender.com/live

Backend readiness:
https://directpilot-uat-api.onrender.com/ready

Backend version:
https://directpilot-uat-api.onrender.com/version

Same-origin public plans:
https://uat.directpilot.ir/api/v1/plans

Authenticated subscription check:
https://uat.directpilot.ir/api/v1/subscription/me

Meta OAuth backend callback target from UAT example config:
https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback

Instagram webhook API root:
https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/webhook
```

### 4.3 Render identifiers

```text
Workspace name: My Workspace
Workspace ID:   tea-dabsgm0n74is738av7l0
Owner email:    namach2727@gmail.com
Region:         Oregon

Production service:
Name: directpilot-api
ID:   srv-db0f3uc9v7es73b5k51g
URL:  https://directpilot-api.onrender.com
Branch: backend-main
Auto deploy: OFF
Plan: Free
Health check: /live

UAT service:
Name: directpilot-uat-api
ID:   srv-dabsmo7qj5pc7397jqf0
URL:  https://directpilot-uat-api.onrender.com
Branch: backend-main
Auto deploy: OFF
Plan: Free
Health check: /live
```

### 4.4 Production database

```text
Render database name: directpilot-production-db
Render database ID:   dpg-db0escm0tbcc73fhig2g-a
PostgreSQL version:    16
Database name:         directpilot_production_db
Database user:         directpilot_production_db_user
Region:                Oregon
Plan:                  Free
Expires:               2026-11-02T11:59:46Z
```

**Critical:** the Free Production database is pilot/market-validation infrastructure, not a durable real-customer database. It expires on 2026-11-02. Do not onboard real customers or rely on durable customer data until this is replaced/upgraded and backup/restore is established. No paid resource may be created without explicit owner approval.

The UAT runtime is verified against PostgreSQL through `DATABASE_URL`, but its actual host/DSN/password are intentionally not recorded here. Current Render database listing exposes only the Production Render PostgreSQL instance, so do not invent the UAT provider/host.

### 4.5 Vercel identifiers

```text
Project name: directpilot-web
Project ID:   prj_w46jn80pmeOpoIZ5KZmQiY7GfKDl
Team/account: mohcenp-9857s-projects
Team ID:      team_Cu7IBomJgSNCXUMp3sILUUD4
Production branch: main
UAT Preview branch: UAT
```

Operational note: the connected Vercel inspection tool returned 403 for this project during the separation work. Use the Vercel Dashboard or authenticated Vercel CLI for authoritative project/deployment inspection until connector permissions are fixed.

---

## 5. Current Deployment Evidence

### Production backend

```text
Service: directpilot-api
Deploy ID: dep-db0ffinavr4c73ffdc2g
Commit: cc6591b6862d4a9b5b33c96509cda0410528c0f2
Status: LIVE
APP_ENV: production
```

Production startup previously verified:

- environment validation passed,
- PostgreSQL connectivity passed,
- migrations reached/current at head,
- application startup passed,
- controlled production seed completed,
- seed-on-start was returned to `false`.

### UAT backend

```text
Service: directpilot-uat-api
Deploy ID: dep-db103us9v7es73da6qpg
Commit: cc6591b6862d4a9b5b33c96509cda0410528c0f2
Status: LIVE
APP_ENV: uat
```

Post-cutover UAT logs explicitly verified:

```text
environment = uat
status = valid
Database connectivity check passed.
Database migration completed and current head was verified.
Application startup complete.
Uvicorn running on 0.0.0.0:10000
```

An earlier UAT deploy `dep-db1016gu01pc73c70320` failed environment validation. Required UAT security settings were corrected, and the later deploy above is the accepted baseline.

### Frontend / Vercel

Verified domain mapping:

```text
https://directpilot.ir      -> Vercel Production / main
https://www.directpilot.ir  -> 308 redirect to directpilot.ir
https://uat.directpilot.ir  -> Vercel Preview / branch UAT
```

Verified server-only upstream split:

```text
DIRECTPILOT_API_UPSTREAM
Production -> https://directpilot-api.onrender.com
Preview    -> https://directpilot-uat-api.onrender.com
```

`NEXT_PUBLIC_DIRECTPILOT_API_URL` still exists in Production configuration from older work, but the intended cloud routing invariant is the server-only upstream + same-origin browser API. Do not make browser routing depend on a public backend URL.

`NEXT_PUBLIC_SITE_URL` is a hidden Vercel variable scoped to Preview and Production. Its exact current value was not exposed/reverified during the cutover. This is a known follow-up because OAuth/canonical URLs may require environment-specific values.

---

## 6. UAT and Production E2E Acceptance

### UAT — PASS on 2026-10-04

The custom UAT domain was tested after the final backend cutover.

`GET https://uat.directpilot.ir/api/v1/plans` returned the UAT paid catalog:

```text
AUTOMATION_V1
price_amount = 4,900,000 IRR
automation_limit = 20
instagram_account_limit = 1

AI_ASSISTANT_V1
price_amount = 6,900,000 IRR
reply_limit = 1000
ai_request_limit = 1000
instagram_account_limit = 1
```

A new user was then registered through `https://uat.directpilot.ir`. The authenticated `/api/v1/subscription/me` response proved:

```text
Registration: PASS
Session/authentication: PASS
UAT frontend -> UAT backend routing: PASS
UAT database write/read: PASS
Automatic trial activation: PASS

AUTOMATION_TRIAL:
status = active
duration_days = 14
automation_limit = 3
instagram_account_limit = 1

AI_ASSISTANT_TRIAL:
status = active
duration_days = 14
reply_limit = 200
instagram_account_limit = 1

Observed trial period:
2026-10-04 -> 2026-10-18
```

The response also showed effective capabilities including `ai_assistant`, `instagram_automation`, and `knowledge_base`.

### Production — previously PASS, regression still required after UAT cutover

Production was previously verified end-to-end through:

```text
https://directpilot.ir
 -> Vercel Production
 -> https://directpilot-api.onrender.com
 -> Production PostgreSQL
 -> Registration
 -> Session
 -> automatic trials
 -> /api/v1/subscription/me
```

The production registration flow accepts the new Iranian mobile requirement and successfully created a test account before the final UAT cutover.

**Next action:** rerun a non-destructive Production smoke/regression after the UAT separation work. Do not mutate payment state merely to prove routing.

### Production public plan caveat

During the latest Production smoke, `https://directpilot.ir/api/v1/plans` returned `[]`. The seeded Production plans were not publicly purchasable at that moment. Therefore do **not** claim the Production paid catalog is published until it is intentionally enabled and reverified. This supersedes older roadmap text that said Production exposed the two paid plans.

---

## 7. Authentication, Registration and Trial Behavior

Registration now requires an Iranian mobile number.

Accepted forms:

```text
09123456789
+989123456789
```

Backend normalizes local Iranian format to `+989xxxxxxxxx` and remains authoritative for validation.

Relevant backend commit:

```text
54a3ddc55ab2a332c87f873e56b4e96631e3e367
feat(auth): require mobile number at registration
```

Migration safety: the persisted phone field was introduced nullable for existing-data migration safety; do not infer uniqueness unless current schema/code explicitly proves it.

Automatic trial behavior is intentional. Registration activates both product-family trials when eligible:

```text
AUTOMATION_TRIAL
AI_ASSISTANT_TRIAL
```

Do not remove this behavior as a bug. It was explicitly accepted as the intended trial model.

---

## 8. Credential / Secret Inventory — Names and Locations Only

### Security rule

**Never put actual values in this file.** Credential values belong only in Render/Vercel/provider secret stores or local gitignored environment files. The purpose of this section is to let a new session know **what exists, where it belongs, and what still needs verification**.

### 8.1 Core backend secrets — separate per environment

Expected/configured secret families:

```text
DATABASE_URL / DATABASE_URL_FILE
APPLICATION_SECRET / APPLICATION_SECRET_FILE
INSTAGRAM_TOKEN_ENCRYPTION_KEY / INSTAGRAM_TOKEN_ENCRYPTION_KEY_FILE
MEDIA_SIGNING_SECRET / MEDIA_SIGNING_SECRET_FILE
```

Production location:

```text
Render -> service directpilot-api -> Environment
```

UAT location:

```text
Render -> service directpilot-uat-api -> Environment
```

Status:

- Production `DATABASE_URL`, `APPLICATION_SECRET` and Instagram encryption configuration passed deployed environment validation.
- UAT `DATABASE_URL`, independent `APPLICATION_SECRET` and Instagram encryption configuration passed deployed environment validation after the 2026-10-04 cutover.
- UAT `APPLICATION_SECRET` was rotated/set independently during cutover; old UAT sessions may have been invalidated. This is expected.
- Never reuse Production and UAT application/encryption secrets intentionally.

### 8.2 Meta / Instagram credentials

Backend-only credential/configuration family:

```text
META_VERIFY_TOKEN
META_APP_ID
META_APP_SECRET / META_APP_SECRET_FILE
META_ACCESS_TOKEN / META_ACCESS_TOKEN_FILE
META_IG_USER_ID
INSTAGRAM_TOKEN_ENCRYPTION_KEY / INSTAGRAM_TOKEN_ENCRYPTION_KEY_FILE
META_OAUTH_REDIRECT_URI
META_SEND_ENABLED
META_SEND_ALLOWED_ACCOUNT_IDS
META_SIGNATURE_REQUIRED
```

Production callback target:

```text
https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback
```

UAT callback target:

```text
https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback
```

Historical UAT Instagram DM / Story Reply / Comment Private Reply E2E had passed before the environment split. **Post-separation Meta/OAuth behavior has not yet been reaccepted in this checkpoint.** Verify environment-specific callback URLs and credentials before declaring Meta Production/UAT complete.

### 8.3 LLM credentials

Possible backend-only provider families already supported/configured by source:

```text
OPENAI_API_KEY / OPENAI_API_KEY_FILE
GROQ_API_KEY
OLLAMA_API_KEY
```

Provider/model settings must remain environment-specific and backend-only. Do not put provider keys in Vercel `NEXT_PUBLIC_*` variables.

Current roadmap does not assert the exact secret value or currently selected provider in each cloud environment; inspect Render configuration/runtime before changing it.

### 8.4 Payexa credentials

Backend-only family:

```text
PAYEXA_BASE_URL
PAYEXA_API_KEY
PAYEXA_CALLBACK_BASE_URL
PAYEXA_TIMEOUT_SECONDS
```

Source defaults/examples distinguish:

```text
UAT sandbox host: https://sandbox.pexn.ir
Production host:  https://pay.pexn.ir
```

Callback base should be environment-specific:

```text
UAT:        https://uat.directpilot.ir
Production: https://directpilot.ir
```

Never expose `PAYEXA_API_KEY` to frontend or Git.

### 8.5 Historical KPay credentials

KPay code remains for historical compatibility/manual fallback context, but KPay was abandoned as the primary provider before a real provider transaction because its credential lifecycle was unsuitable/unclear for DirectPilot's server integration. Do not interpret that as a claim that KPay itself is defective.

Backend-only family:

```text
KPAY_BASE_URL
KPAY_ACCESS_TOKEN
KPAY_SHOP_ID
KPAY_CARD_ID
KPAY_CALLBACK_BASE_URL
KPAY_FEE_SIDE
KPAY_TIMEOUT_SECONDS
KPAY_VERIFY_SEND_AUTH
KPAY_CHECK_SEND_AUTH
```

Do not configure or revive KPay as primary without an explicit product/provider decision.

### 8.6 Manual card-transfer configuration

Backend-only/admin-managed configuration includes card-transfer destination data and manual payment cards. Source environment family includes:

```text
CARD_TRANSFER_CARD_NUMBER
CARD_TRANSFER_ACCOUNT_NUMBER
CARD_TRANSFER_ACCOUNT_NAME
CARD_TRANSFER_BANK_NAME
CARD_TRANSFER_INSTRUCTIONS
```

Later backend work added admin-managed manual payment cards. Never publish full card/account details in this roadmap.

### 8.7 Vercel configuration

Authoritative routing variable:

```text
DIRECTPILOT_API_UPSTREAM
Production -> https://directpilot-api.onrender.com
Preview    -> https://directpilot-uat-api.onrender.com
```

Other known Vercel variables:

```text
NEXT_PUBLIC_DIRECTPILOT_API_URL  [Production; legacy/public config exists]
NEXT_PUBLIC_SITE_URL             [Hidden; Preview + Production; exact value needs re-verification]
```

Do not store backend credentials, payment keys, database DSNs, Meta app secrets or LLM keys in Vercel public variables.

---

## 9. Commerce and Payment Status

### Commercial product policy

UAT currently exposes:

```text
AUTOMATION_V1
price = 4,900,000 IRR
30 days
1 Instagram account
20 automation rules
AI reply limit = 0

AI_ASSISTANT_V1
price = 6,900,000 IRR
30 days
1 Instagram account
1000 AI replies / requests per effective period
```

Production publication status must be reverified separately; latest `/plans` smoke returned an empty list.

### Immutable order snapshots

Commerce activation must continue using immutable order purchase terms rather than rereading mutable plan data. Preserve snapshot-based activation.

### Payexa — current primary implementation direction

Payexa implementation was released into source before the environment split.

Backend release commit:

```text
33e774dcd0f298145da55e15dbf24b6632aed287
feat(commerce): add Payexa payment gateway
```

Frontend Payexa release baseline recorded during deployment work:

```text
4318517b8fef23603f6b65e13dbd44a3a6814949
```

Backend routes were confirmed present after deployment:

```text
Payexa create route: present
Payexa callback GET: present
Payexa callback POST: present
Payexa status route: present
```

Payexa safety semantics retained:

- `amount_unique` is a verification token, not immutable purchase price.
- only a valid first-success verify result may activate from immutable order snapshots,
- already-verified/ambiguous states require reconciliation rather than unsafe activation,
- ambiguous creates are not blindly retried,
- callback verification/finalization is serialized/idempotent,
- tokens/credentials/card data stay out of public responses and logs.

**Production Payexa credentials/provider transaction are not declared complete in this checkpoint.** Configure/verify separately after Production regression and environment credential split.

### Durable receipt storage

Backend commit:

```text
0663e4055ed46290cd39809ef774353eee461129
feat(payments): persist receipt bytes durably
```

Receipt bytes are persisted in PostgreSQL for pilot durability instead of relying only on ephemeral filesystem storage.

Known payment/security follow-ups before real customers:

- review/remediate any plaintext full-card-PAN storage risk,
- review default-card concurrency/race behavior,
- close admin UI edit gaps where required,
- ensure failed automated-provider flows do not incorrectly switch to manual state,
- perform real provider acceptance separately from source-code route presence.

---

## 10. Instagram / AI / Automation Milestones Already Completed

Previously completed/verified milestones include:

- Instagram OAuth foundation,
- DM E2E,
- Story Reply E2E,
- Comment -> Private Reply E2E,
- Knowledge -> AI flow,
- echo/loop prevention,
- Inbox / Human Handoff,
- Automation edit workflow,
- deterministic Automation / AI separation,
- AI workspace,
- admin/commercial foundation,
- outbound delivery reconciliation,
- admin payment review UI,
- AI request quota hard-cap enforcement,
- admin customer N+1 timeout fix.

Do not repeat these foundations from scratch. Re-test only when the active change can affect them or when environment credentials/callbacks change.

---

## 11. No-Cost Pilot Constraint and Production Readiness

Owner constraint:

```text
No paid infrastructure until real customers / market validation justify it.
```

Current Render web services and Production database are on Free plans. Do not create a paid resource without explicit new approval.

This means the current Production environment is suitable for controlled pilot/market validation, **not yet final durable real-customer production**.

Before real customers:

1. replace/upgrade the expiring Production PostgreSQL database,
2. establish backup + restore drill and retention,
3. verify Production Meta/OAuth credentials and callbacks,
4. verify Production LLM/provider credentials,
5. verify chosen payment provider with a controlled real transaction,
6. close high-risk payment/card-data findings,
7. run Production regression and health/readiness checks,
8. confirm public commercial plan publication intentionally.

---

## 12. Local Working-Tree Safety

Known unrelated backend dirty work that must not be touched by roadmap/deployment work:

```text
tests/test_customer_final_uat_api.py
.uat-temp/
"tatus --short"   [historically observed accidental path]
```

Known unrelated frontend dirty work:

```text
components/instagram-callback.tsx
lib/api/instagram.ts
tests/profile-instagram-timeout.test.mjs
```

Before any local Git mutation:

```powershell
git status --short
```

Never reset/clean/stash these automatically. Stage intended paths explicitly.

Because Render auto-deploy is OFF for both backend services, a Git push does not by itself prove or trigger cloud acceptance. Deploy the exact reviewed commit deliberately and verify runtime evidence.

---

## 13. Release / Deployment Approach

For every substantial task:

1. Read `AGENTS.md` and this roadmap.
2. Inspect `git status` and preserve unrelated work.
3. Search narrowly; do not scan generated/dependency trees unnecessarily.
4. Make the smallest scoped change.
5. Run focused tests first.
6. Run full regression once at the release gate when required.
7. Commit/push only explicitly authorized files/branches.
8. Treat local validation, pushed state, deployed state and UAT acceptance as separate facts.
9. Correlate deployment with exact commit SHA.
10. Verify environment validation, PostgreSQL connectivity and migration head.
11. Verify `/live`, `/ready`, `/version` as appropriate.
12. Run same-origin browser/API smoke through the public frontend domain.
13. Update this roadmap after meaningful deployment, migration, architecture, commercial-policy or UAT milestones.

Environment release order when API compatibility matters:

```text
UAT backend/migration
 -> UAT frontend
 -> UAT E2E acceptance
 -> Production backend/migration
 -> Production frontend
 -> Production smoke
```

For the already-completed environment split, both environments currently run the same backend commit but use different `APP_ENV`, secrets, routing and databases.

---

## 14. Known Documentation / Configuration Follow-ups

The source `.env.uat.example` still contains generic placeholder domains such as `replace-with-uat-frontend.example.com`, `media.uat.example.com` and `shops.uat.example.com`. Runtime UAT is working, but these examples should eventually be aligned with the canonical `uat.directpilot.ir` architecture where appropriate. Do not blindly replace media/tenant domains without checking their actual runtime contract.

The exact current value of Vercel `NEXT_PUBLIC_SITE_URL` must be reverified because it is hidden and scoped to both Preview and Production. If the application uses it for OAuth/canonical links, split it by environment.

The Vercel connector currently lacks permission to inspect this project; Dashboard/CLI evidence remains authoritative.

---

## 15. Exact Next Work Queue

### P0 — immediate

```text
PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT
```

Non-destructively verify:

- `https://directpilot.ir` loads,
- same-origin `/api/v1/*` reaches Production backend, not UAT,
- `/live`, `/ready`, `/version` are healthy,
- existing Production session/auth behavior remains correct,
- no UAT data appears in Production,
- no Production data appears in UAT.

### P1 — integration credential separation

```text
META_OAUTH_ENVIRONMENT_SPLIT
LLM_ENVIRONMENT_VERIFICATION
PAYMENT_PROVIDER_ENVIRONMENT_SPLIT
```

Verify separate UAT/Production callback URLs, app/provider keys, allowlists and send flags. Never copy secrets into this file while doing so.

### P1 — Production durability before real customers

```text
PRODUCTION_DATABASE_DURABILITY
BACKUP_RESTORE_ACCEPTANCE
```

The Free Render Production DB expires 2026-11-02. Upgrade/replace only after explicit cost approval, but do not onboard real customers before durability is solved.

### P2 — payment acceptance

Complete controlled Payexa/provider acceptance and security review. Source presence is not provider acceptance.

### P2 — future product work

Story Product Automation remains the next strategic product expansion after the current Production/integration/payment readiness gates are closed.

---

## 16. Future Phase — Story Product Automation

Target concept:

```text
Instagram Story
 -> internal product/offer
 -> exact price
 -> deterministic response
 -> optional CTA
 -> enabled/disabled
 -> lifecycle/expiry
```

Rules:

- story-specific price/offer data is deterministic,
- LLM must not invent price,
- story-specific deterministic match performs ZERO LLM,
- Human Takeover remains highest precedence.

Later expansion may include catalog/SKU, inventory, offer history, analytics and story-to-checkout, but do not implement these opportunistically during readiness work.

---

## 17. How to Resume in a New Chat

Give the new chat this file and use this instruction:

> Read `PROJECT_ROADMAP.md` completely before proposing or changing anything. Treat it as the DirectPilot continuity checkpoint. First verify the current backend/frontend branch heads, Render Production/UAT deploy commits, Vercel Production/UAT routing, migration head and local dirty files. Do not repeat completed work. Do not expose or request secret values unless an action strictly requires the user to enter them directly into the provider/platform UI. Resume from `Exact Next Work Queue`. If runtime/repository evidence conflicts with the roadmap, runtime/repository evidence wins and the roadmap must be updated.

Minimum facts a new session should verify before mutation:

```text
Backend backend-main HEAD
Frontend main HEAD
Frontend UAT branch HEAD
Render directpilot-api deployed SHA
Render directpilot-uat-api deployed SHA
APP_ENV production vs uat
Production/UAT DATABASE_URL separation without printing values
Vercel DIRECTPILOT_API_UPSTREAM Production vs Preview
Migration head
Production DB expiry/durability
Local git status in both repos
```

---

## 18. Completion Definition for Environment Separation

The UAT/Production separation milestone is considered **COMPLETE** because all of the following were verified:

- dedicated public UAT domain exists,
- UAT domain maps to Vercel Preview branch `UAT`,
- Production domain remains Vercel Production/main,
- Preview upstream points to UAT Render backend,
- Production upstream points to Production Render backend,
- UAT backend runs `APP_ENV=uat`,
- Production backend runs `APP_ENV=production`,
- both backend services run the reviewed environment-separation commit,
- UAT PostgreSQL connectivity/migration/startup passed,
- UAT public plan read passed through custom domain,
- UAT registration passed,
- UAT session/auth passed,
- UAT automatic Automation + AI trials passed,
- Production had previously passed registration/session/trial E2E on its own backend/database.

The remaining work is **regression + integration credential separation + Production durability**, not rebuilding the environment split.
