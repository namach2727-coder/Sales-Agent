# DirectPilot — 2026-10-17 Vercel Backend / Neon Production Cutover

## Authoritative observed status: Production website API routing SWITCHED and SMOKE PASS

Owner stated that all production traffic/payments/Meta usage is **experimental** and explicitly authorized using the Oct 17 Render database backup as final source, discarding any newer *test* writes in Render. Therefore this cutover is a test-only transition, NOT a zero-data-loss replication.

### Topology — verified

| Component | Previous | Current |
| --- | --- | --- |
| Frontend public domains | Vercel `directpilot.ir`, `www.directpilot.ir` | Same domains, new Vercel production deployment `dpl_AKFqXWre8HxCHVvvNz9yZeviGLF9` READY |
| Frontend source SHA | GitHub `directpilot-web` main `8592c6e91d4beaed7c31653dc285612fd511fa53` | **Same SHA**, no untested front-end feature change |
| Frontend API proxy | Production Vercel env `DIRECTPILOT_API_UPSTREAM` | **`https://directpilot-prod-api.vercel.app`** (Production only); `NEXT_PUBLIC_DIRECTPILOT_API_URL` aligned |
| Backend | Render `directpilot-api` | Vercel project `directpilot-prod-api` id `prj_89ZBNaJ4ZKg9GOzBmoh8tNW6Wclx`; deployment `dpl_5wSJ1veseCg7BprMsGfQ4HTQ6sAJ` READY |
| Backend source | `backend-main` at 0025 migrations | Selective Backend PR **#47**, `release/prod-neon-0027-backend-20261017`, app SHA `65a3ef946a373452b3642f61f141b650e33a5c41`; new `api/index.py` ASGI entrypoint |
| Database | Render PG16 `directpilot_production_db` | Neon project `billowing-poetry-05589994`, branch `production`, database **`directpilot_live`**, PG18, 83 public tables, Alembic `0027_traceable_receipt_versions` |
| UAT | Vercel UAT API / separate Neon UAT | **UNCHANGED** |

### Data and security

- Owner executed local pg_dump custom format snapshot `directpilot_prod_20261017_103343.dump`, SHA-256 `9E46745AA1D115EA74A0877ACEC28A53423ADE73DBEE9FD490842AAFC6D8D064`, validated isolated local restore PASS: 82 tables / Alembic 0025. Subsequently restored same backup into an initially empty Neon `directpilot_live` and SQL-migrated 0026/0027 transactionally. Post-restore direct checks: 83 tables and revision 0027; historic payment receipt version created via backfill. Do not upload sensitive archive to GitHub/chat.
- User knowingly chose NOT to re-synchronize any newer Render test transactions. This is an **accepted test-data RPO**, not a fully consistent zero-loss production migration.
- Neon PostgreSQL role password was rotated following accidental earlier URI disclosure. The old copied URI is invalid. Both Neon database read queries PASS after rotation.
- Existing Render environment secrets were unavailable to connectors. New **separate** application signing secret and Fernet encryption key were securely provisioned in sensitive Vercel environment variables; never publish them or copy secrets to docs. As a result old cookies/sessions and historically encrypted test Instagram credentials may not be usable until relogin/reconnect.
- API environment is `APP_ENV=production`, strict hosts/CORS, HTTPS and secure cookies, conservative DB pool, **Meta outbound send and content publish disabled** by default. Existing Render Meta OAuth/webhook callbacks, AI/OpenAI/Groq API keys, payment gateway and other provider credentials were **NOT** copied. Any provider features need their own credential and callback setup/acceptance. Manual card-to-card data is DB-backed, but UI end-to-end payment approval still requires owner test.

### Evidence of successful HTTP cutover

1. GitHub Actions [Backend Neon health smoke](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39018969331) PASS: `https://directpilot-prod-api.vercel.app/ready` 200 with `status=ready, database=available, migration=current`, plus `/live`, `/version` HTTP 200.
2. [Production public-site API smoke](https://github.com/namach2727-coder/Sales-Agent/actions/runs/39019279518) PASS: GET `/api/v1/plans` from `https://directpilot.ir` HTTP 200; backend HTTP 200; equivalent plan JSON; unauthenticated `/api/v1/auth/me` returns HTTP 401 at BOTH domains.
3. Independent GitHub CI on release backend PR #47 PASS at preceding source commits: tests, PG smoke, PostgreSQL18 compatibility and Docker build. Any later workflow-only commits need their own CI check; do not assume success until verified.
4. Vercel new backend READY and new frontend READY; frontend production aliases `directpilot.ir` and `www.directpilot.ir` verified assigned to new deployment.
5. Neon direct read-only check after switch: public_tables=83 and Alembic 0027.

### Outstanding / blocked before claiming commercial readiness

- **NOT VERIFIED:** end-to-end login using real test credentials after changed app signing secret, paid order creation, bank-card instructions/receipt upload/admin approval in actual browser, Meta webhook events/DM/Story/Comment automation, AI response, OAuth, payment callbacks, emails and provider credentials.
- Old Render API and database still exist and have not been deleted. They are retained as fallback/archival copies until explicitly retired; frontend no longer routes to them. Do not claim full Render deprovisioning.
- New production Vercel API project was created without linking Git for auto-deploy; API deployment was made explicitly from GitHub release SHA. Future changes need a controlled deploy or Git link setup. No automatic deployment assumption.
- Existing backup file is stored on owner workstation, not a verified encrypted independent off-device copy. Establish off-provider DR and automated Neon backups before real customer onboarding.
- Vercel runtime-error API returned permission 403; absence of runtime errors cannot be asserted. GitHub HTTP smoke is authoritative for listed endpoints only.
- Neon Free plan limits, cold starts and performance for sustained real traffic remain not fully validated. Commercial hosting policy and billing should be revisited before real customers.

### Safeguarded rollback

- Previous website production deployment: `dpl_cRZsk7rndqFWH1KnKdhLVbNU1VxF`, previous website SHA `8592c6e9...`. New deployment uses same SHA with changed Production environment variables.
- To roll back frontend API routing, securely reset Production `DIRECTPILOT_API_UPSTREAM` to `https://directpilot-api.onrender.com` and redeploy the pinned website SHA; do NOT alter UAT preview variables.
- **After any writes on Neon**, rolling back to Render silently discards those writes unless reconciled. As of the cutover owner characterized all data test-only, but respect this limitation and warn before any rollback.
- Do not delete Render DB until owner explicitly confirms acceptance, independent backup and all provider integrations.

**Status string:** `WEB_API_CUTOVER_PASS / FULL_FEATURE_ACCEPTANCE_PARTIAL / RENDER_DECOMMISSION_PENDING`.
