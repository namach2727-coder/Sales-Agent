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
- Latest runtime-code repository commit: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
- Production Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Deployment ID: `dep-db159npsrm7s73a57usg`
- Deployment Git commit: `6183ec60fc7e50b8d80d16fe89fba7138de3f9e4` (documentation-only commit)
- Effective runtime-code commit: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
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
- Deployment ID: `dep-db14hck9v7es73dtgdlg`
- Deployed commit: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
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

Status: **PASS**

Environment separation itself is complete. Do not rebuild it.

## Completed

- Production/UAT backend separation.
- Production/UAT `APP_ENV` validation.
- Production database connectivity and migration startup verification.
- UAT database connectivity/startup verification.
- GitHub App installation and repository access for both backend and frontend repositories.
- Production backend deployed at `8bce8ae...` with the admin-login recovery fix; startup PASS and reset flag remained disabled.
- UAT backend deployed at `8bce8ae...`; startup PASS and reset flag remained disabled.

## Open Issues

- P0 Production regression after environment split is complete.

- Backend/frontend principal contract issue was fixed in `8bce8ae...`: `/auth/login` and `/auth/me` expose server-derived `platform_role_codes` required by the Admin UI.
- One-shot password reset/unlock executed successfully for the existing Super Admin (`user_id=3`) on Production. The reset flag was then set to `false`, temporary reset email/password values were cleared, and a clean restart confirmed neither reset nor bootstrap reran.
- Production Super Admin browser login and `/admin` access: PASS (user-confirmed after the Production-only password reset/unlock).
- Production same-origin `/api/v1/plans`: PASS. Browser response exposed only `AUTOMATION_V1` with the intended public catalog values: 4,900,000 IRR, 30 days, automation limit 20, Instagram account limit 1, AI reply limit 0.
- Production/UAT data isolation: PASS from observable public catalog behavior. Production exposes only `AUTOMATION_V1`; UAT exposes `AUTOMATION_V1` plus `AI_ASSISTANT_V1`, and the `AUTOMATION_V1` public IDs differ between environments. This proves the public routes are not resolving to the same data store/catalog.
- UAT currently contains a public `AI_ASSISTANT_V1` test/stale catalog entry. This must remain UAT-only; Production commercial scope remains `AUTOMATION_V1` only.
- Meta/OAuth pilot configuration is PARTIAL: owner chose to reuse the same Meta App credentials for UAT and Production for now. Production Meta variables were added and Production redeployed successfully. Production uses its own OAuth redirect URI; live OAuth + webhook acceptance is still required.
- LLM provider/environment configuration requires verification.
- Payment-provider environment separation and real provider acceptance remain open.
- Production PostgreSQL durability/backup/restore is not acceptable for real customers while using the expiring Free database.

## Current Blocker

No GitHub repository-access blocker remains.

Current verification dependencies:
- P0 has no remaining blocker.
- Next gate is P1 integration credential separation: Meta/OAuth, LLM, and payment-provider environment verification.

Do not weaken the Production database IP allowlist merely to inspect SQL.

## Last Verified Action

2026-10-04:
- Continuity layer created and verified in GitHub: `AI_HANDOFF.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`.
- `PROJECT_ROADMAP.md` authority header updated so `AI_HANDOFF.md` is primary.
- GitHub App installation detected for account `namach2727-coder`.
- Repository selection is `all`.
- Both `Sales-Agent` and `directpilot-web` report read/write repository access.
- CI for `8bce8ae...` PASS: docker-build, postgres-smoke, and test; full suite `858 passed, 7 skipped`.
- UAT deploy `dep-db14hck9v7es73dtgdlg` at `8bce8ae...` is LIVE; APP_ENV/database/migration/startup PASS; reset did not run.
- Production reset deploy `dep-db157gnavr4c73aatm1g` succeeded: `Platform administrator password reset: user_id=3`.
- Reset cleanup was applied: flag `false`, temporary reset email/password values cleared.
- Production cleanup deploy `dep-db159npsrm7s73a57usg` is LIVE; database/migration/startup PASS; neither reset nor bootstrap reran. This deploy points at docs-only repository commit `6183ec6...`; runtime application code remains the accepted `8bce8ae...` change set.
- Production Super Admin login succeeded in the browser and `/admin` opened successfully after the reset; admin auth acceptance is PASS.
- Production PostgreSQL remains AVAILABLE on Free plan with expiry 2026-11-02.
- Production environment change for Meta configuration triggered deploy `dep-db15nrou01pc73cv9hf0`, which is LIVE. APP_ENV=production, DB connectivity, migration current-head validation, and application startup all PASS.
- Production public plans: PASS; only `AUTOMATION_V1` is exposed.
- UAT public plans differ from Production (includes UAT-only `AI_ASSISTANT_V1` and distinct public IDs), confirming observable data isolation.
- Vercel Production deployment `dpl_3yRwkKf5gFaR6wz5TTpM1FjCZjsR`: READY, branch `main`, frontend SHA `ede06b5822b499812cfe24464c737d67bf781014`.
- Vercel UAT deployment `dpl_CZFLfeqwKv8FWUUx5KCh8E2inM7R`: READY, branch `UAT`, frontend SHA `ede06b5822b499812cfe24464c737d67bf781014`.
- Vercel contains separate encrypted `DIRECTPILOT_API_UPSTREAM` variables scoped to Production vs Preview; values were not decrypted. Combined with the distinct live catalogs, routing separation is accepted.

## Next Exact Action

1. Complete `META_OAUTH_ENVIRONMENT_SPLIT` acceptance using the shared Meta App pilot decision:
   - keep separate Production/UAT OAuth redirect URIs,
   - make Production the active webhook destination for the shared app,
   - run a real Production OAuth connect/callback test,
   - run a controlled Production webhook/DM acceptance test.
2. Then verify `LLM_ENVIRONMENT_VERIFICATION`.
3. Then verify `PAYMENT_PROVIDER_ENVIRONMENT_SPLIT`.
4. Before real customers, resolve Production database durability and backup/restore acceptance.

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
DEPLOYMENT: dep-db159npsrm7s73a57usg
DEPLOYMENT_GIT_SHA: 6183ec60fc7e50b8d80d16fe89fba7138de3f9e4 (docs-only)
RUNTIME_CODE_SHA: 8bce8aee595c3b3f21bb69ecf47a082a19d11498

UAT_BACKEND:
LIVE / VERIFIED
DEPLOYMENT: dep-db14hck9v7es73dtgdlg
DEPLOYED_SHA: 8bce8aee595c3b3f21bb69ecf47a082a19d11498

MIGRATION:
LATEST FILE-RECORDED HEAD: 0023
DEPLOYED STARTUP CURRENT-HEAD VERIFICATION: PASS

AUTOMATION_V1:
SOURCE: VERIFIED
PRODUCTION SEED: VERIFIED
LIVE SAME-ORIGIN RESPONSE: PASS

GITHUB_ACCESS:
BACKEND: PASS
FRONTEND: PASS

PRODUCTION_ADMIN_LOGIN:
PASS — LOGIN SUCCESSFUL AND /admin OPENED

FRONTEND_DEPLOYMENTS:
PRODUCTION: dpl_3yRwkKf5gFaR6wz5TTpM1FjCZjsR / main / READY
UAT: dpl_CZFLfeqwKv8FWUUx5KCh8E2inM7R / UAT / READY
FRONTEND_SHA: ede06b5822b499812cfe24464c737d67bf781014
ROUTING_SEPARATION: PASS

NEXT EXACT ACTION:
Complete shared-Meta-App Production acceptance: register Production OAuth redirect URI in Meta, set Production as the active webhook callback for the shared app, then run Production OAuth + webhook E2E.
P0 Production regression after environment split is PASS.
Only then mark Production Regression PASS.
```
