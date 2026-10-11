# DirectPilot Project Roadmap & Continuity Checkpoint

> **Strategic roadmap / secondary continuity document.** Read `AI_HANDOFF.md` first in every new DirectPilot session; then read this file.
>
> **Last updated:** 2026-10-10
>
> **Authority rule:** verified runtime/deployment evidence > deployed commit > repository source > `AI_HANDOFF.md` > this document > old chat history.
>
> **Secret rule:** record credential names, locations, owners and verification status only. Never record secret values.

---

## 0. Current Resume Marker

```text
PROJECT: DirectPilot
DATE: 2026-10-10

CURRENT_PHASE:
Pilot / market-validation with separated UAT and Production

LATEST_BACKEND_SAFETY_RELEASE:
PRODUCTION_SINGLE_PILOT_SEND_ALLOWLIST_GUARD

RELEASE_STATUS:
UAT PASS / PRODUCTION LIVE / CI PASS

BACKEND_PRODUCTION:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
RENDER_DEPLOYMENT: dep-db33funavr4c739lm9v0
STATUS: LIVE
APP_ENV: production
DB: PASS
MIGRATION: PASS
STARTUP: PASS

BACKEND_UAT:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
RENDER_DEPLOYMENT: dep-db33f1qd0e5s73f0bk00
STATUS: LIVE
APP_ENV: uat
DB: PASS
MIGRATION: PASS
STARTUP: PASS

FRONTEND_PRODUCTION:
SHA: 4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159
VERCEL_STATUS: SUCCESS
OWNER_PRODUCTION_SMOKE: PASS FOR PRIOR RELEASE
ADMIN_PLAN_SCROLL/VALIDATION FIX: DEPLOYED / OWNER RETEST PENDING
ADMIN_CUSTOMER_AUTOMATION_MANAGEMENT: DEPLOYED / OWNER CONFIRMED

META_E2E:
PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E PASS

OUTBOUND_SAFETY:
META_SEND_ENABLED=false
PRODUCTION STARTUP REQUIRES EXACTLY ONE META_SEND_ALLOWED_ACCOUNT_IDS ENTRY WHEN SEND IS ENABLED

PRODUCTION_DB:
FREE / EXPIRES 2026-11-02
DURABILITY: OPEN
BACKUP_RESTORE: OPEN

NEXT EXACT STEP:
Resolve Production database durability and backup/restore acceptance before real-customer onboarding. Keep Meta send disabled by default after the successful controlled E2E. Verify Production LLM configuration as a separate gate.
```

Do not restart completed environment-separation, Auth/UX, SEO, Production OAuth or inbound-relay work without regression evidence.

## 1. Product Direction and Non-Negotiable Invariants

DirectPilot is an Instagram Sales Automation Platform / AI Sales Assistant, not a generic bot or full CRM.

Current product pillars:

1. Deterministic Automation.
2. AI Assistant.
3. Commerce / Subscription.
4. Instagram via official Meta APIs.
5. Future Story Product Automation.

Runtime precedence:

```text
Human Takeover
  -> Story-specific Automation [future]
  -> General Deterministic Automation
  -> AI Assistant fallback
```

Invariants:

- Exact deterministic match performs ZERO LLM / PromptBuilder / knowledge retrieval / AI usage.
- Tenant/store isolation is mandatory and server-side.
- Backend is authoritative for payment, entitlement, subscription and activation state.
- Never activate subscriptions from browser state.
- Commerce activation uses immutable purchase/order snapshots.
- Never blindly retry ambiguous external-provider writes.
- Keep the Modular Monolith for MVP.
- Browser API remains same-origin under `/api/v1/*`.
- Preserve unrelated dirty work; no destructive Git cleanup/history rewriting.
- No paid infrastructure without explicit owner approval.

AI guardrails:

```text
GROQ_CONTEXT_LENGTH=4096
GROQ_MAX_OUTPUT_TOKENS=256
```

---

## 2. Repository and Branch State

### Backend

```text
Repository: namach2727-coder/Sales-Agent
Branch: backend-main
Accepted deployed runtime-code SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
Runtime includes the Meta relay bridge plus the Production single-pilot outbound allowlist guard.
Later continuity-document commits, if any, must not be described as deployed runtime code unless Render evidence matches them.
```

GitHub CI for `91250140...`:
- test: PASS
- docker-build: PASS
- postgres-smoke: PASS

### Frontend

```text
Repository: namach2727-coder/directpilot-web
Production branch: main
UAT branch: UAT
main SHA: 4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159
UAT SHA: 4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159
```

## 3. Environment Topology

### Production

```text
https://directpilot.ir
  -> Vercel Production / main
  -> same-origin /api/v1/*
  -> DIRECTPILOT_API_UPSTREAM
  -> https://directpilot-api.onrender.com
  -> APP_ENV=production
  -> Production PostgreSQL
```

### UAT

```text
https://uat.directpilot.ir
  -> Vercel Preview / UAT
  -> same-origin /api/v1/*
  -> DIRECTPILOT_API_UPSTREAM
  -> https://directpilot-uat-api.onrender.com
  -> APP_ENV=uat
  -> UAT PostgreSQL
```

Environment separation is COMPLETE and PASS.

---

## 4. Current Deployment Evidence

### Production Backend

- Service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Deployment: `dep-db33funavr4c739lm9v0`
- Deployed Git SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=production`: PASS
- PostgreSQL connectivity: PASS
- Migration current-head verification: PASS
- Application startup: PASS
- Auto deploy: OFF

### UAT Backend

- Service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Deployment: `dep-db33f1qd0e5s73f0bk00`
- SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=uat`: PASS
- Database/migration/startup: PASS

### Frontend / Vercel

Production:
- Branch: `main`
- SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`
- Vercel status: SUCCESS
- Admin plan UX fixes deployed: scroll preservation before paint, inline validation without native scroll-to-invalid, and automatic uppercase normalization for internal plan codes.
- Owner retest for the plan-creation UX fix: PENDING.

UAT:
- Branch: `UAT`
- SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`
- Vercel deployment: SUCCESS / branch aligned with Production source.

## 5D. Admin Customer Automation Management

Frontend SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.

Status: **DEPLOYED TO UAT AND PRODUCTION / OWNER FUNCTIONAL ACCEPTANCE PENDING**.

Changes:
- Admin -> Customers & Stores now exposes **Manage Automation** only for stores with the `instagram_automation` capability.
- The selected customer/store opens the existing Automation Rule Builder with phrase/keyword, match type, response text, priority and enabled state.
- The frontend reuses the existing tenant/store-scoped AutomationRule API.
- Platform Super Admin access is authorized through the existing backend platform permission path; no impersonation or tenant-isolation bypass was added.
- Backend capability and automation-limit checks remain authoritative.
- UAT Vercel: SUCCESS.
- Production Vercel: SUCCESS.
- Owner live functional acceptance: PENDING.

This UI is the preferred path for creating the Production pilot deterministic rule when testing from the Platform Admin account.

## 5C. Meta UAT-to-Production Relay Bridge

Accepted backend runtime SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`.

Status: **OAUTH PASS / INBOUND PASS / OUTBOUND E2E OPEN**.

Evidence:
- GitHub CI: test PASS, docker-build PASS, postgres-smoke PASS,
- UAT Render deploy `dep-db33f1qd0e5s73f0bk00`: LIVE; APP_ENV/DB/migration/startup PASS,
- Production Render deploy `dep-db33funavr4c739lm9v0`: LIVE; APP_ENV/DB/migration/startup PASS,
- Production OAuth through the UAT callback relay: PASS,
- UAT webhook relay to Production: PASS,
- Production inbound routing/account resolution/persistence/processing: PASS.

Observed live behavior:
- inbound `قیمت` reached Production,
- no deterministic AutomationRule matched,
- AI fallback failed with `llm_provider_configuration_error`,
- Production send remained disabled, so no provider send occurred.

Outbound safety release:
- `META_SEND_ENABLED=false` remains the current Production state,
- when Production send is enabled, runtime validation now requires exactly one entry in `META_SEND_ALLOWED_ACCOUNT_IDS`,
- zero or multiple allowed accounts fail Production environment validation,
- the sender still enforces sender-account membership in the allowlist.

Next gate:
- deterministic `DM_KEYWORD` + `EXACT` rule for `قیمت`,
- exactly one connected Production pilot account in the allowlist,
- one controlled outbound E2E,
- verify one provider delivery, dedupe and no own-message echo loop.

## 5B. SEO Phase 2 Release

Production/UAT SEO Phase 2 accepted SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8` (later frontend UX fixes are deployed at `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`).

Status: Production PASS.

Changes:
- completed Article/Organization schema image and logo fields,
- shortened long commercial search-result titles,
- expanded `/pricing` and `/comment-to-direct` to remove thin-content warnings,
- preserved canonical/indexability and Preview/UAT noindex controls.

Live Production audit after deployment:
- 5 priority pages audited,
- HTTP 200 on all,
- indexable 5/5,
- critical 0,
- high 0,
- medium 0,
- low 0,
- schema issues 0.

Ranking impact remains OPEN until Google recrawls the changed pages and a later settled Search Console window is available.

## 5A. SEO Phase 1 Release

Production frontend SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`.

Status: Production deployment completed successfully in Vercel.

Changes:
- aligned commercial metadata and homepage H1 with actual search intent,
- strengthened direct/comment/comment-to-DM landing pages,
- expanded long-tail solution pages,
- corrected stale “free forever” claims to the backend-authoritative Automation Trial: 14 days, one Instagram account, up to 3 automations,
- added Pricing structured data,
- refreshed the smart-direct guide around observed queries including “آموزش دایرکت هوشمند” and “ربات دایرکت هوشمند اینستاگرام”,
- prevented Vercel Preview/UAT indexing.

Google Search Console baseline through 2026-10-04: 14 clicks, 315 impressions, 4.44% CTR, average position 40.30. Sitemap `https://directpilot.ir/sitemap.xml` was resubmitted on 2026-10-07 and accepted; Google recrawl/ranking movement remains asynchronous.

## 5. Authenticated UX / Account Security Release

### UAT Acceptance

Owner-confirmed PASS:

- session persistence,
- auth routing,
- login CTA after auth,
- customer logout,
- admin logout,
- customer navigation,
- admin navigation,
- settings dirty state,
- account security,
- password change,
- RTL desktop,
- RTL mobile,
- regression smoke.

Still not PASS:

- Forgot Password: BLOCKED — no verified recovery delivery provider.
- Meta E2E: BLOCKED_EXTERNAL / deferred.

Frontend exact-candidate validation:

- `npm test`: 156/156 PASS
- type-check: PASS
- lint: PASS
- build: PASS
- diff check: PASS
- secret scan: PASS

Backend CI for `84b7df6...`:

- test: PASS
- docker-build: PASS
- postgres-smoke: PASS

### Production Acceptance

Owner-confirmed Production smoke after deployment: PASS for customer and platform-admin login/session persistence, routing, navigation, Account & Security, Settings dirty-state and logout.

The release is closed. Do not rerun without related change/regression evidence.

---

## 6. Authentication Decisions

- Valid server session persists across refresh/navigation.
- Customer authenticated landing route: `/dashboard`.
- Platform-admin authenticated landing route: `/admin`.
- Unauthenticated protected routes redirect to `/login`.
- Auth tokens are not stored in localStorage/sessionStorage.
- Logout uses backend session revocation.
- Password change requires current password, enforces policy and revokes all sessions.
- Raw session tokens are never shown in session-management UI.
- Forgot Password remains blocked until a verified recovery provider and secure recovery-token lifecycle exist.

---

## 7. Commercial Scope

Production V1 sale scope remains:

```text
AUTOMATION_V1
Price: 4,900,000 IRR
Duration: 30 days
Automation limit: 20
Instagram account limit: 1
AI reply limit: 0
```

- `AUTOMATION_TRIAL`: active trial, not purchasable.
- `AI_ASSISTANT_TRIAL`: active trial, not purchasable.
- Legacy plans: not public purchasable.
- No paid `AI_ASSISTANT_V1` is approved for Production.
- UAT-only stale/test catalog data must not be propagated to Production.

---

## 8. Production Database Durability

Production database:

```text
Name: directpilot-production-db
ID: dpg-db0escm0tbcc73fhig2g-a
PostgreSQL: 16
Plan: FREE
Expiry: 2026-11-02T11:59:46.610475Z
HA: disabled
Read replicas: none
```

Current status: pilot-only.

Before real customers:

- choose durable target,
- obtain explicit approval for any paid change,
- define migration/cutover,
- establish backup policy,
- complete restore acceptance,
- document practical RPO/RTO.

This is the next priority gate.

---

## 9. Integration Status

### Meta / OAuth

Status: IN PROGRESS — RELAY BRIDGE DEPLOYED / PRODUCTION OAUTH NEXT.

- Owner approved the UAT -> Production relay workaround because Meta Developer settings are currently inaccessible.
- Shared Meta App credentials remain valid for the pilot.
- Meta continues to know the existing UAT OAuth callback.
- Production now deliberately sends that same provider redirect URI while prefixing its OAuth state with `production.`.
- UAT relays only `production.` callback state to the Production callback; UAT does not consume that state.
- Production consumes its own state and stores its own encrypted Instagram token/connection.
- Webhook relay code is deployed to UAT but remains disabled until Production OAuth succeeds.
- Production outbound remains fail-closed with `META_SEND_ENABLED=false`.
- CI for relay runtime `b8f945d...`: 871 passed / 7 skipped; docker-build PASS; postgres-smoke PASS.
- Production deploy `dep-db31vu60tbcc738ee1dg`: LIVE.
- UAT deploy `dep-db31uljncjis73e6gq90`: LIVE.
- Never copy UAT encrypted tokens/database rows or the UAT encryption key into Production.

### LLM

Status: OPEN.

- Verify provider/model configuration by environment.
- Keep secrets backend-only.
- Preserve AI guardrails.

### Payment Provider

Status: OPEN.

- Verify UAT sandbox vs Production provider configuration.
- Verify callback bases and credentials without exposing values.
- Real provider transaction acceptance is a separate gate.

---

## 10. Local Working-Tree Safety

The old workstation can still contain local-only dirty work.

Important known item:

- Local frontend commit `4733d9a7f8b942486ca221c1dba1564e6cb34d2b` was created accidentally on local `main` during promotion and was never pushed.
- Remote `main` is authoritative at `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`.

Do not use destructive reset/clean/force operations. Preserve or reconcile local-only work explicitly before device migration/handoff.

---

## 11. Release / Deployment Approach

When API compatibility matters:

```text
UAT backend
 -> UAT frontend
 -> UAT acceptance
 -> Production backend
 -> Production frontend
 -> Production smoke
 -> continuity update
```

Rules:

- exact SHA correlation,
- runtime verification before PASS,
- no Production env changes unless explicitly required,
- no unrelated changes between accepted UAT candidate and Production promotion.

---

## 12. Exact Next Work Queue

### P1 — Immediate

```text
PRODUCTION_DATABASE_DURABILITY
BACKUP_RESTORE_ACCEPTANCE
```

### P1 — After/Alongside Durability

```text
PAYMENT_PROVIDER_ENVIRONMENT_SPLIT
LLM_ENVIRONMENT_VERIFICATION
```

### Meta — Active

```text
META_UAT_TO_PRODUCTION_RELAY_ACTIVATION
```

Next gate is Production OAuth from the Production dashboard. Webhook relay remains disabled until that succeeds.

### Blocked

```text
FORGOT_PASSWORD_RECOVERY
```

Requires verified recovery delivery provider.

### P2

- controlled payment-provider acceptance,
- future Story Product Automation.

---

## 13. Future Story Product Automation

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

- deterministic price/offer data,
- no LLM-invented price,
- exact story match performs ZERO LLM,
- Human Takeover retains highest precedence.

---

## 13A. Future Telegram Bot Builder

Status: **IDEA PARKED / NOT IN CURRENT EXECUTION SCOPE**

Concept:
- No-code AI Telegram Bot Builder / bot-builder SaaS.
- Prefer Telegram Managed Bots capability where suitable.
- One manager/builder experience can provision and manage tenant bots.
- Multi-tenant shared runtime; do not deploy a separate application per customer.
- Candidate modules: deterministic rules, AI assistant, menus, lead capture, human handoff, knowledge, analytics, later commerce/payment/CRM.
- Keep this as a future product track only. Do not divert DirectPilot readiness work until current Production gates are closed.

## 14. Resume Instructions

On a new session:

1. Read all five continuity files in canonical order.
2. Verify remote branch heads and deployed runtime SHAs before mutation.
3. Verify Render Production/UAT runtime state.
4. Verify Vercel branch/deployment state when relevant.
5. Preserve local dirty work.
6. Resume from `Exact Next Work Queue`.
7. If runtime evidence conflicts with docs, runtime wins and docs must be corrected.

## 9A. Meta Production Activation

Status: IN PROGRESS.

- Owner explicitly resumed Meta work on 2026-10-07.
- UAT live evidence shows inbound webhook events accepted and outbound delivery completed on 2026-10-07.
- Shared Meta App pilot decision remains valid.
- Production non-secret Meta settings were normalized with Production OAuth callback, official provider endpoints, signature verification enabled, content publishing disabled, and outbound sending fail-closed.
- The env update triggered Production deployment `dep-db317cm0tbcc738c4qlg`; it is LIVE.
- Production deployment checked out Git SHA `fa8316e71ec1ce7c32c4806f428c5bde0e26db16`; compare against accepted runtime code `84b7df6...` contains only continuity Markdown files.
- Render connector cannot safely read secret env values, so shared app credentials must be confirmed/copied in the Render dashboard without pasting them into chat.
- Production OAuth must create its own encrypted connection/token rows in the Production database. Do not copy UAT encrypted token rows across environments.
- Keep `META_SEND_ENABLED=false` until Production OAuth, webhook routing and restricted account allowlist are verified.

## Meta OAuth Relay Runtime

- OAuth relay deployment is live in both environments at `b6962c6701897ece4ee4fdda5ffcf7f2ec67da3a`.
- UAT deploy: `dep-db32aebncjis73e7irl0` — LIVE.
- Production deploy: `dep-db32beom7kps73cpcf50` — LIVE.
- Production OAuth redirect intentionally uses the existing UAT callback registered with Meta.
- Production OAuth state prefix: `prod.`.
- UAT callback relays only matching `prod.` states to the Production callback.
- Webhook relay remains disabled until Production OAuth connection is accepted.
- Production sending remains disabled until restricted-account E2E.

## Meta Production OAuth Acceptance

- Production OAuth accepted on 2026-10-07 through the UAT relay bridge.
- UAT callback relay evidence: `instagram.oauth.relayed`.
- Production provider evidence: short-token exchange 200, requested permissions complete, BUSINESS profile probes PASS, long-lived-token exchange 200, profile lookup 200.
- UAT webhook relay is now enabled to the Production webhook endpoint.
- UAT webhook-relay deploy: `dep-db32pmvavr4c739je950` — LIVE.
- Production sending remains disabled pending inbound-routing acceptance and allowlist verification.

## Meta Production Inbound Acceptance

- Production inbound relay accepted on 2026-10-07.
- Evidence: UAT `instagram.webhook.relay_succeeded`; Production `instagram.inbound.received`, account resolution, conversation creation, message persistence, webhook accepted and processing completed.
- Test message `قیمت` reached Production but no deterministic AutomationRule matched; AI fallback attempted and failed with `llm_provider_configuration_error`.
- Production send remained disabled, so no outbound provider call was made.
- Next gate: deterministic Production rule + restricted non-empty send allowlist + one controlled outbound E2E.


## Controlled Production Outbound Gate — 2026-10-11
Status: **CONTROLLED PILOT E2E PASS**
- Deterministic pilot rule: owner confirmed.
- Single-account Production restriction: configured.
- Restricted Production send: enabled only for the controlled test; returned to disabled afterward.
- Deployment `dep-db5ihrg473hc73ba3be0`: LIVE.
- Environment, DB, migration and startup checks: PASS.
- Controlled retest passed: deterministic response, one provider delivery, no AI fallback, and no self-echo loop.


## Controlled Outbound Attempt 1 — Inconclusive
- First pilot message coincided with UAT relay redeployment.
- No inbound webhook reached UAT or Production, so there is no automation/outbound verdict.
- Relay is healthy again; repeat one controlled message after relay readiness.


## Meta Production Controlled E2E — PASS (2026-10-11)

Acceptance evidence:
- UAT webhook relay delivered the clean retest to Production.
- Production inbound routing/persistence: PASS.
- Deterministic rule evaluation: PASS.
- Exactly one `instagram_outbound_started`: PASS.
- Exactly one `instagram_outbound_delivered`: PASS.
- No `instagram_outbound_failed`: PASS.
- No AI start/failure for the deterministic flow: PASS.
- Provider/self follow-up event was ignored; no second outbound was started: PASS.
- Post-test rollback: `META_SEND_ENABLED=false`.
- Rollback deployment `dep-db5illid0e5s73fju470`: LIVE.

Meta transport is no longer the current Production-readiness blocker. Production database durability and backup/restore remain the highest-priority blocker before real customers; LLM verification remains a separate open gate.


## Meta Production Controlled E2E — PASS (2026-10-11)
- UAT relay -> Production inbound: PASS.
- Deterministic rule handling: PASS.
- Exactly one outbound delivery: PASS.
- AI fallback not invoked: PASS.
- No duplicate second send observed: PASS.
- Follow-up/self event was ignored; no loop observed: PASS.
- Production send returned to disabled after acceptance.
- Post-test deployment `dep-db5illid0e5s73fju470`: LIVE.
- Current highest-priority readiness blocker: Production database durability and backup/restore before real customers.


## Production DB Durability Assessment — 2026-10-11
- Current Production Postgres is Free, expires 2026-11-02, has no managed backups/PITR, no HA, no replicas, and an empty external IP allowlist.
- Seven-day metrics show very low Pilot load: CPU ~0.007 cores, memory roughly 40-60 MB, active connections peak 6.
- Recommended minimum paid target: Render Postgres `0.1c-256mb` with current storage kept minimal.
- Expected base compute cost: about $6/month; 1 GB storage included, additional Postgres storage is billed separately.
- Paid Render Postgres enables PITR; on a Hobby workspace the recovery window is 3 days. On-demand logical exports are available for paid instances and retained for 7 days.
- Compute-plan change requires brief database downtime.
- Paid infrastructure change remains blocked until explicit owner approval.


## Production DB Upgrade Decision — 2026-10-11
- Owner explicitly deferred the paid Production Postgres upgrade for now.
- Do not change the current Free Production database plan or incur paid infrastructure cost without a new explicit approval.
- Current risk remains accepted temporarily: Free Production Postgres expires 2026-11-02 and does not satisfy durability/backup-restore acceptance.
- Real-customer onboarding remains blocked by Production database durability until this decision is revisited.


## Production LLM Configuration Verification — DIAGNOSIS PASS / READINESS BLOCKED

Runtime evidence (2026-10-11):
- Safe observability SHA: `398d6dc52e436f4db25f21b19e7dbca4bef10f3c`.
- CI: test PASS, docker-build PASS, postgres-smoke PASS.
- UAT: Groq selected; configured credential and model present; deployment `dep-db5j4ebbc2fs73934e7g` LIVE.
- Production: OpenAI selected with `gpt-5.6-sol`, but selected-provider credential is absent; Groq credential/model are also absent; deployment `dep-db5j5c7lk1mc73a6ofkg` LIVE.
- Production backend health remains PASS; only AI provider execution is blocked.
- No provider secret was logged or copied across environments.

Next:
1. Provision a Production-specific LLM credential securely in Render.
2. Select and configure a currently supported Production model.
3. Preserve `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256` if Groq is selected.
4. Run one controlled AI fallback E2E.


## Groq Model Support Check — 2026-10-11
- UAT currently selects `qwen/qwen3.6-27b`.
- Official Groq deprecation guidance says `qwen/qwen3.6-27b` was deprecated for Free/Developer usage on 2026-09-14.
- Direct replacement: `qwen/qwen3.8-27b`.
- Do not copy the deprecated UAT model into Production.
- If Production Groq is approved, target `qwen/qwen3.8-27b` with existing guardrails `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, and `GROQ_REASONING_EFFORT=none`.
- Production still requires its own securely provisioned `GROQ_API_KEY`; never copy or expose the UAT credential.


## Production Groq Configuration Activated — 2026-10-11
- Production LLM provider is now `groq`.
- Production model is `qwen/qwen3.8-27b`.
- Groq credential presence: verified true through sanitized startup metadata; secret value was never logged or copied.
- Guardrails: `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, `GROQ_REASONING_EFFORT=none`.
- Production environment, DB connectivity, migration head and application startup: PASS.
- LLM configuration deployment `dep-db5jh9lckfvc73aekfbg`: LIVE.
- Restricted Meta-send test deployment `dep-db5ji6ss728c73823a50`: LIVE.
- Meta send is enabled only under the existing single-pilot account allowlist for one controlled AI fallback E2E.
- Next: send one deliberately unmatched pilot message and verify Groq request completion, assistant persistence, exactly one outbound delivery, quota accounting, dedupe and no echo loop.


## Production AI Fallback E2E — PASS (2026-10-11)

Acceptance:
- UAT relay -> Production: PASS.
- Unmatched message -> AI fallback: PASS.
- Groq `qwen/qwen3.8-27b`: PASS.
- Provider request completed in 226 ms with 488 total tokens.
- Assistant persistence: PASS.
- Exactly one Meta outbound delivery: PASS.
- AI/outbound failures: NONE.
- Duplicate/echo second send: NOT OBSERVED.
- Quota enforcement path executed before provider call; token metadata was persisted for server-authoritative usage aggregation. Exact aggregate usage count was not directly queried because Production DB networking remains closed.
- Meta send returned to disabled after the test.
- Rollback deployment `dep-db5jm4nlk1mc73a8du40`: LIVE.

Production LLM is no longer an open blocker.


## Payexa Environment Split Verification — 2026-10-11

- Safe Payexa runtime observability SHA: `b7c510912a6b5bb13c736192e390bce44a3dcb61`.
- CI for the observability change: test PASS / docker-build PASS / postgres-smoke PASS.
- Initial UAT runtime was incorrectly configured against Production Payexa: base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, credential present. This environment-split finding was FAIL and was corrected immediately.
- UAT is now isolated to Payexa Sandbox: base `https://sandbox.pexn.ir`, callback base `https://uat.directpilot.ir`, sandbox credential configured. Deployment `dep-db5k0pcs728c7383hnh0`: LIVE. UAT Payexa environment split: PASS.
- Initial Production Payexa state was fail-closed: sandbox/default base, empty callback, no credential.
- Production non-secret Payexa configuration is now base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, timeout 15s, while Production credential remains absent. Deployment `dep-db5k2e142hec7398l0h0`: LIVE.
- Production Payexa environment structure is therefore correct but provider execution remains intentionally BLOCKED until a Production-specific `PAYEXA_API_KEY` is provisioned securely.
- Current frontend checkout intentionally does not invoke Payexa; manual card transfer remains the primary checkout path. Payexa source/routes and result page remain present.
- Real-provider acceptance is NOT PASS. It requires Production credential provisioning, Payexa-side verification/approval of the DirectPilot callback site/domain as applicable, and a controlled transaction path.
- Never copy UAT credentials into Production, expose provider secrets in chat/logs, or blindly retry ambiguous create operations.

- Next payment gate: securely provision the Production Payexa credential, verify the callback site/domain in the Payexa panel, then enable a controlled checkout/test path before any real-provider acceptance claim.


## Authoritative Payment Flow Correction — 2026-10-11

- Current DirectPilot payment architecture is **manual card transfer with admin approval**, not Payexa.
- Customer selects a paid plan and receives the configured payment-card details from DirectPilot.
- Customer transfers the exact amount using any banking method outside DirectPilot.
- Customer uploads a JPEG/PNG/PDF receipt from the customer panel.
- Backend validates the receipt and persists the receipt bytes plus metadata in PostgreSQL (`receipt_data`, content type, size, SHA-256), then changes payment status to `submitted` and order status to `payment_submitted`.
- Platform Admin reviews submitted payments in Admin -> Payments, can securely view the receipt, and chooses Approve or Reject.
- Approve is backend-authoritative: it row-locks/checks optimistic revision, marks payment `approved`, marks order `paid`, creates/activates the subscription, applies plan/module entitlements and writes an audit record atomically.
- Reject returns the order to `pending` and records the rejection reason without deleting the payment.
- UAT frontend currently contains this complete customer + admin flow and its Vercel deployment is SUCCESS at frontend UAT SHA `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Backend manual flow is present and deployed from `backend-main`; current CI remains PASS.
- Payexa/KPay routes are preserved only as non-primary/deferred integration code. They are **not** part of the current customer checkout path and are **not** a Production-readiness gate for the current payment process.
- Do not request or provision Payexa credentials unless the owner explicitly decides to re-open automated payment-gateway work.
- Current payment readiness should be evaluated against manual-card-transfer E2E and admin approval, not Payexa acceptance.

- Current payment gate: verify/promote the manual card-transfer flow in Production, including configured payment card, customer receipt upload, Admin receipt review, approval/rejection and subscription activation.
- Automated Payexa acceptance is deferred/out of current scope.


## Production Manual Payment E2E Readiness — 2026-10-11

- Authoritative payment path remains manual card transfer + customer receipt upload + Admin approval.
- Frontend Production `main` is one commit ahead of UAT but has no payment/checkout/admin-payment differences from UAT. Production Vercel status is SUCCESS.
- Safe manual-payment readiness probe SHA: `c05669d3448ea3f6f151bb73a22db5dcfffcf7b7`.
- CI: test PASS / docker-build PASS / postgres-smoke PASS.
- UAT deployment `dep-db5kjhnlot8c73f9ueb0`: LIVE; runtime readiness `active_cards=1 active_default_cards=1` => PASS.
- Production deployment `dep-db5kkhid0e5s73fq7h90`: LIVE; runtime readiness `active_cards=0 active_default_cards=0` => BLOCKED.
- Production cannot create a manual payment until an Admin configures at least one active default payment card.
- No card number/account data was logged or copied from UAT. Do not fabricate, infer, or transfer banking details across environments.
- Once a real Production destination card is configured by an authorized Admin, run controlled E2E: paid-plan order -> show card -> upload test receipt -> Admin reviews receipt -> Admin approves -> verify payment approved, order paid, subscription active and module entitlements applied.

- Immediate payment blocker: Production payment-card configuration only. Code/deployment path is otherwise ready.
