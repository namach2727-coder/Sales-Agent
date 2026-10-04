# DirectPilot Current State

> Snapshot of verifiable current state. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-04.

## Repository State

### Backend

- Repository: `namach2727-coder/Sales-Agent`
- Branch: `backend-main`
- Latest runtime-code commit: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
- Continuity documentation commits are newer than the deployed runtime SHA and must not be described as deployed application code.

### Frontend

- Repository: `namach2727-coder/directpilot-web`
- Production branch: `main`
- UAT branch: `UAT`
- GitHub App access to repository: PASS
- Current Vercel frontend SHA: `ede06b5822b499812cfe24464c737d67bf781014` for both accepted Production and UAT deployments.

## Production Backend

- Render service: `directpilot-api`
- Service ID: `srv-db0f3uc9v7es73b5k51g`
- Latest LIVE deployment ID: `dep-db159npsrm7s73a57usg`
- Deployment Git SHA: `6183ec60fc7e50b8d80d16fe89fba7138de3f9e4` (documentation-only)
- Effective runtime-code SHA: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
- Status: LIVE
- `APP_ENV=production`: VERIFIED
- Database connectivity: PASS
- Migration startup/current-head verification: PASS
- Application startup: PASS
- Auto deploy: OFF

## UAT Backend

- Render service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Latest LIVE deployment ID: `dep-db14hck9v7es73dtgdlg`
- Deployed SHA: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`
- Status: LIVE
- `APP_ENV=uat`: VERIFIED
- Database connectivity/startup: PASS
- Auto deploy: OFF

## Production Database

- Render database: `directpilot-production-db`
- ID: `dpg-db0escm0tbcc73fhig2g-a`
- PostgreSQL: 16
- Status: AVAILABLE
- Plan: FREE
- Expires: `2026-11-02T11:59:46.610475Z`
- High availability: disabled
- Read replicas: none
- External IP allowlist is empty.
- Latest file-recorded migration head: `0023`.
- Deployed startup verifies current migration head.
- Do not weaken the database IP allowlist merely to inspect SQL.
- This database is pilot infrastructure only; real-customer durability remains OPEN.

## Commercial Catalog

Current source decision:

- `AUTOMATION_V1`: active + purchasable, 4,900,000 IRR, 30 days, automation limit 20, Instagram account limit 1, AI reply limit 0.
- `AUTOMATION_TRIAL`: active trial, not purchasable.
- `AI_ASSISTANT_TRIAL`: active trial, not purchasable.
- Legacy FREE/TRIAL/START/PRO plans: not public purchasable plans.
- No paid `AI_ASSISTANT_V1` is part of the current verified V1 sale scope.

Automation V1 source publication commit:
`391ef3f0d835099f3f71ace028b0e92eddb40a0d`

Production startup seed evidence recorded creation of the new plan row after this release.

Live same-origin Production `/api/v1/plans` response after the catalog change: PASS. Browser response contains only `AUTOMATION_V1` with intended public values: 4,900,000 IRR, 30 days, automation limit 20, Instagram account limit 1, AI reply limit 0.

## Production Administrator Bootstrap

- One-shot bootstrap source remains deployed.
- Admin-login recovery fix deployed in `8bce8ae...`: server-derived `platform_role_codes` are serialized for the frontend, and a separate fail-closed one-shot password reset/unlock path exists.
- Runtime log recorded: platform administrator created with `user_id=3`.
- Credentials are intentionally not recorded.
- Existing Super Admin password reset/unlock: PASS for `user_id=3`.
- Reset cleanup: PASS — reset flag disabled, temporary reset values cleared, clean restart confirmed no rerun.
- Authenticated Production-session and `/admin` acceptance: PASS (user-confirmed browser login and Admin access).

## Environment Separation

Status: PASS.

Do not repeat the separation implementation without regression evidence.

Current work is post-separation Production regression and integration verification, not environment rebuilding.

## Frontend / Vercel

Known canonical domains:

- Production: `https://directpilot.ir`
- UAT: `https://uat.directpilot.ir`

Expected architecture remains same-origin `/api/v1/*` with server-only `DIRECTPILOT_API_UPSTREAM`.

Current Vercel deployment/routing evidence is verified:
- Production: `dpl_3yRwkKf5gFaR6wz5TTpM1FjCZjsR`, branch `main`, READY.
- UAT: `dpl_CZFLfeqwKv8FWUUx5KCh8E2inM7R`, branch `UAT`, READY.
- Both use frontend SHA `ede06b5822b499812cfe24464c737d67bf781014`.
- `DIRECTPILOT_API_UPSTREAM` exists as separate encrypted variables scoped to Production and Preview; values were not decrypted.
- Distinct live public catalogs confirm the two domains are not resolving to the same application data.

## Production Regression Status

`PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT`: PASS.

## Verification Limitations / Open Evidence

- Production and UAT both run `8bce8ae...`; CI and startup acceptance passed with reset disabled.
- Production/UAT data isolation: PASS from observable public-plan differences. Production exposes only `AUTOMATION_V1`; UAT exposes `AUTOMATION_V1` plus `AI_ASSISTANT_V1`, with different `AUTOMATION_V1` public IDs across environments.
- UAT `AI_ASSISTANT_V1` is UAT-only test/stale catalog data; current Production commercial scope remains `AUTOMATION_V1` only.
- Meta/OAuth, LLM, and payment-provider environment separation remain follow-up gates.
- Real payment-provider transaction acceptance is separate from source/route presence.
