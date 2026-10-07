# DirectPilot Project Roadmap & Continuity Checkpoint

> **Strategic roadmap / secondary continuity document.** Read `AI_HANDOFF.md` first in every new DirectPilot session; then read this file.
>
> **Last updated:** 2026-10-07
>
> **Authority rule:** verified runtime/deployment evidence > deployed commit > repository source > `AI_HANDOFF.md` > this document > old chat history.
>
> **Secret rule:** record credential names, locations, owners and verification status only. Never record secret values.

---

## 0. Current Resume Marker

```text
PROJECT: DirectPilot
DATE: 2026-10-07

CURRENT_PHASE:
Pilot / market-validation with separated UAT and Production

LATEST_RELEASE:
SEO_PHASE_1

RELEASE_STATUS:
PRODUCTION DEPLOYED / VERCEL SUCCESS

BACKEND_PRODUCTION:
SHA: 84b7df6196fe380fad21a3791e3160840c098602
RENDER_DEPLOYMENT: dep-db2ufns9v7es73aarbg0
STATUS: LIVE

FRONTEND_PRODUCTION:
SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
VERCEL_STATUS: SUCCESS
OWNER_PRODUCTION_SMOKE: PASS

UAT:
BACKEND SHA: 84b7df6196fe380fad21a3791e3160840c098602
BACKEND DEPLOYMENT: dep-db1mq5vavr4c73cmjgo0
FRONTEND SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
FUNCTIONAL ACCEPTANCE: PASS

FORGOT_PASSWORD:
BLOCKED — no verified recovery delivery provider

META_E2E:
BLOCKED_EXTERNAL / OWNER-DEFERRED

NEXT EXACT STEP:
Resolve Production database durability and backup/restore before real-customer onboarding.
```

Do not restart completed environment-separation or UX/Auth promotion work without regression evidence.

---

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
Accepted runtime-code SHA: 84b7df6196fe380fad21a3791e3160840c098602
Continuity-document commits may be newer on backend-main; do not treat them as deployed runtime code.
```

Accepted backend release adds secure password/session management and remains the Production/UAT runtime candidate.

### Frontend

```text
Repository: namach2727-coder/directpilot-web
Production branch: main
UAT branch: UAT
main SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
UAT SHA: da73f8055f676aaa1a07901fe351d20f4455ad5a
```

The Production frontend was promoted by fast-forward from the UAT-accepted release.

---

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
- Deployment: `dep-db2ufns9v7es73aarbg0`
- SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- Status: LIVE
- `APP_ENV=production`: PASS
- PostgreSQL connectivity: PASS
- Migration current-head verification: PASS
- Application startup: PASS
- Auto deploy: OFF

### UAT Backend

- Service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Deployment: `dep-db1mq5vavr4c73cmjgo0`
- SHA: `84b7df6196fe380fad21a3791e3160840c098602`
- Status: LIVE
- `APP_ENV=uat`: PASS
- Database/migration/startup: PASS

### Frontend / Vercel

Production:

- Branch: `main`
- SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Vercel GitHub status: SUCCESS / Deployment completed
- Deployment status target reference:
  `https://vercel.com/mohcenp-9857s-projects/directpilot-web/4WadnbNq9X79RjTx8fANyZWuwN8g`

UAT:

- Branch: `UAT`
- SHA: `da73f8055f676aaa1a07901fe351d20f4455ad5a`
- Vercel deployment completed successfully before Production promotion.

A canonical current `dpl_...` Production deployment ID was not independently recovered in this checkpoint. Do not invent one.

---

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

Status: PARTIAL / BLOCKED_EXTERNAL / owner-deferred.

- Shared Meta App pilot decision remains.
- Production and UAT have distinct OAuth redirect URIs.
- Do not resume Meta work unless explicitly requested.
- Real OAuth callback and controlled webhook/DM acceptance remain open.

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
- Remote `main` is authoritative at `da73f8055f676aaa1a07901fe351d20f4455ad5a`.

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

### Deferred

```text
META_OAUTH_ENVIRONMENT_SPLIT / E2E
```

Meta remains paused until explicit owner instruction.

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

## 14. Resume Instructions

On a new session:

1. Read all five continuity files in canonical order.
2. Verify remote branch heads and deployed runtime SHAs before mutation.
3. Verify Render Production/UAT runtime state.
4. Verify Vercel branch/deployment state when relevant.
5. Preserve local dirty work.
6. Resume from `Exact Next Work Queue`.
7. If runtime evidence conflicts with docs, runtime wins and docs must be corrected.
