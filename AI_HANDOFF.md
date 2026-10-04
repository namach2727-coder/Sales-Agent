# DirectPilot AI Handoff

> **PRIMARY CROSS-CHAT CONTINUITY AUTHORITY**
>
> Read this file first in every new DirectPilot session.
> Chat history is not the project Source of Truth.
>
> Read order:
> 1. `AI_HANDOFF.md`
> 2. `PROJECT_ROADMAP.md`
> 3. `DECISIONS.md`
> 4. `CURRENT_STATE.md`
> 5. `NEXT_ACTIONS.md`
>
> Evidence rule: verifiable runtime/deployment state > deployed commit > repository source > continuity documents > old chat history.
> If evidence conflicts with a document, verify reality first and then correct the document.
>
> Last reconciled: 2026-10-04

## Current Production State

### Backend

- Repository: `namach2727-coder/Sales-Agent`
- Branch: `backend-main`
- Latest runtime-code repository commit before continuity-doc commits: `67d7be01bd32118fee4e98118b2f9e60fc0c3048`
- Production Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Deployment ID: `dep-db13jm5g1s2s738d5bv0`
- Deployed commit: `67d7be01bd32118fee4e98118b2f9e60fc0c3048`
- Deployment status: `LIVE`
- `APP_ENV=production`: VERIFIED
- PostgreSQL connectivity: PASS
- Migration runner/current-head startup verification: PASS
- Application startup: PASS
- Render auto-deploy: OFF

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- GitHub repository access: VERIFIED on 2026-10-04
- Public Production domain: `https://directpilot.ir`
- Public UAT domain: `https://uat.directpilot.ir`
- Exact current Vercel deployed frontend SHA: NOT YET REVERIFIED in this checkpoint
- Vercel deployment inspection: OPEN; do not infer a deployment SHA without authoritative evidence

### Database

- Production Render PostgreSQL: `directpilot-production-db`
- Database ID: `dpg-db0escm0tbcc73fhig2g-a`
- PostgreSQL: 16
- Status: AVAILABLE
- Plan: FREE
- Expires: `2026-11-02T11:59:46.610475Z`
- High availability: disabled
- Read replicas: none
- Latest file-recorded migration head: `0023`
- Deployed startup current-head verification: PASS
- Durability for real customers: OPEN

## Current UAT State

- Render service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Deployment ID: `dep-db127cc9v7es73dj9am0`
- Deployed commit: `64be7ef8cfdcab7f75560a95baeb931071a35e62`
- Deployment status: `LIVE`
- `APP_ENV=uat`: VERIFIED
- Database connectivity/startup: PASS
- Environment separation: PASS — DO NOT REPEAT without regression evidence

## Verified Features / Milestones

- UAT/Production environment separation: PASS.
- UAT registration/session/trial acceptance: PASS from the accepted separation milestone.
- Production backend deployment/startup/database connectivity: PASS.
- Production one-shot platform administrator bootstrap executed; runtime log recorded creation of platform administrator `user_id=3`. Credentials are not recorded here.
- Automation V1 source publication commit: `391ef3f0d835099f3f71ace028b0e92eddb40a0d`.
- Production startup seed evidence recorded creation of the new plan row after Automation V1 publication.
- Historical Instagram DM / Story Reply / Comment Private Reply E2E foundations: PASS before environment split.
- Deterministic Automation / AI separation: established; exact deterministic match must use ZERO AI.

## Active Workstream

`PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT`

Status: **PARTIAL**

Environment separation itself is complete. Do not rebuild it.

## Completed

- Production/UAT backend separation.
- Production/UAT `APP_ENV` validation.
- Production database connectivity and migration startup verification.
- UAT database connectivity/startup verification.
- GitHub App installation and repository access for both backend and frontend repositories.
- Production backend deployed at `67d7be0...`.
- UAT backend deployed at `64be7ef...`.

## Open Issues

- Live Production same-origin `/api/v1/plans` response still requires direct re-verification after the Automation V1 publication/seed change.
- Authenticated Production session must be reverified non-destructively.
- Production/UAT data isolation must be reverified from observable application behavior.
- Exact current Vercel Production/UAT frontend deployment SHAs and routing evidence must be reverified.
- Meta/OAuth credentials and callback separation require post-separation acceptance.
- LLM provider/environment configuration requires verification.
- Payment-provider environment separation and real provider acceptance remain open.
- Production PostgreSQL durability/backup/restore is not acceptable for real customers while using the expiring Free database.

## Current Blocker

No GitHub repository-access blocker remains.

Current verification dependencies:
- authoritative Vercel deployment/routing inspection,
- live same-origin Production API verification,
- safe authenticated Production-session evidence,
- observable Production/UAT isolation evidence.

Do not weaken the Production database IP allowlist merely to inspect SQL.

## Last Verified Action

2026-10-04:
- Continuity layer created and verified in GitHub: `AI_HANDOFF.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`.
- `PROJECT_ROADMAP.md` authority header updated so `AI_HANDOFF.md` is primary.
- GitHub App installation detected for account `namach2727-coder`.
- Repository selection is `all`.
- Both `Sales-Agent` and `directpilot-web` report read/write repository access.
- Production Render latest LIVE deployment remains `dep-db13jm5g1s2s738d5bv0` at `67d7be0...`.
- UAT Render latest LIVE deployment remains `dep-db127cc9v7es73dj9am0` at `64be7ef...`.
- Production PostgreSQL remains AVAILABLE on Free plan with expiry 2026-11-02.

## Next Exact Action

1. Reverify live Production same-origin `https://directpilot.ir/api/v1/plans`.
2. Reverify an authenticated Production session non-destructively.
3. Verify Production routes/data do not resolve to UAT and UAT does not expose Production data.
4. Reverify current Vercel Production/UAT frontend deployment/routing evidence.
5. Only after those checks, mark `PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT` PASS.
6. Continue with:
   - `META_OAUTH_ENVIRONMENT_SPLIT`
   - `LLM_ENVIRONMENT_VERIFICATION`
   - `PAYMENT_PROVIDER_ENVIRONMENT_SPLIT`
7. Before real customers, resolve Production database durability and backup/restore acceptance.

## Important Constraints

- Never expose secret values.
- Never claim deployment, migration, API, database, feature, or payment acceptance without evidence.
- Do not repeat PASS/VERIFIED work without regression evidence or a related change.
- Render backend auto-deploy is OFF; Git push does not equal deployment.
- Documentation-only commits must not be described as deployed runtime commits.
- No paid infrastructure/resource without explicit owner approval.
- Preserve unrelated local dirty work; never reset/clean/auto-stash/force-push/rewrite history automatically.
- Official Meta APIs only.
- Tenant isolation is mandatory.
- Backend remains authoritative for payments, entitlements and subscription state.
- Same-origin browser API remains `/api/v1/*`.

## Decisions That Must Not Be Revisited

- Modular Monolith for MVP.
- Human Takeover suppresses automation and AI.
- Deterministic exact match performs ZERO LLM/PromptBuilder/knowledge/AI work.
- AI execution requires entitlement.
- Backend-authoritative commerce/subscription activation.
- Immutable purchase/order snapshots.
- No blind retry of ambiguous external-provider writes.
- UAT/Production environment separation is complete.
- Current V1 sale scope is Automation V1; trials are not purchasable.
- Production Free PostgreSQL is pilot infrastructure only.

## Current Resume Marker

```text
PROJECT: DirectPilot
DATE: 2026-10-04
ACTIVE_WORKSTREAM: PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT
STATUS: PARTIAL

ENVIRONMENT_SEPARATION:
PASS — DO NOT REPEAT

PRODUCTION_BACKEND:
LIVE / VERIFIED
DEPLOYMENT: dep-db13jm5g1s2s738d5bv0
DEPLOYED_SHA: 67d7be01bd32118fee4e98118b2f9e60fc0c3048

UAT_BACKEND:
LIVE / VERIFIED
DEPLOYMENT: dep-db127cc9v7es73dj9am0
DEPLOYED_SHA: 64be7ef8cfdcab7f75560a95baeb931071a35e62

MIGRATION:
LATEST FILE-RECORDED HEAD: 0023
DEPLOYED STARTUP CURRENT-HEAD VERIFICATION: PASS

AUTOMATION_V1:
SOURCE: VERIFIED
PRODUCTION SEED: VERIFIED
LIVE SAME-ORIGIN RESPONSE: PARTIAL / REVERIFY

GITHUB_ACCESS:
BACKEND: PASS
FRONTEND: PASS

FRONTEND_DEPLOYMENT_SHA:
OPEN — REVERIFY AUTHORITATIVELY

NEXT EXACT ACTION:
Verify live Production same-origin plans, authenticated Production session,
Production/UAT isolation, and Vercel routing.
Only then mark Production Regression PASS.
```
