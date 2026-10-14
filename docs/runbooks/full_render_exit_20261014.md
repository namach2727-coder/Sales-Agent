# DirectPilot — Full Render Exit Plan

Checkpoint 2026-10-14. **PLAN AND CODE ONLY. NO HOST PROVISIONED, NO CUTOVER, NO DELETION.**

## Verified Render inventory
- Production API: directpilot-api, srv-db0f3uc9v7es73b5k51g, Free
- UAT API: directpilot-uat-api, srv-dabsmo7qj5pc7397jqf0, Free
- Production PG16 DB: directpilot-production-db, dpg-db0escm0tbcc73fhig2g-a, Free, expires Nov 2 2026 at 11:59:46Z
- Render Key Value instances: none
- Neon Production: billowing-poetry-05589994, old restored neondb snapshot (PG18.6, 82 tables), not live-synced
- Neon UAT: round-shape-42044596, separate neondb, direct host ep-quiet-dew-ar9fhqml.c-4.us-west-2.aws.neon.tech
- Frontend is deployed outside Render on Vercel in previously verified deployment context.

## Proposed end-state
- Two FastAPI apps (Production/UAT), two scoped Meta gateway containers and a Caddy HTTPS reverse proxy on a Docker-capable host outside Render.
- Distinct Neon database projects for Prod and UAT, with NEW and approved empty Production final DB directpilot_live; do not point new Production API at the stale neondb rehearsal copy.
- Secret values copied privately from Render web-service environment into the NEW backend host's secret store, never into Neon SQL/project settings, GitHub or chat.
- Persistent and separately isolated media and receipt volumes; independent encrypted external backups; monitoring; HTTPS/DNS/Meta/Payexa callbacks migrated only after verified Go.

## Candidate hosting: owner selection required
- Oracle Cloud Always Free VM: potentially 0 USD recurring, durable Docker FastAPI, but signup/payment verification, home-region and VM availability are blockers. OCI free eligibility depends on VM shape and quota.
- Railway: Trial $5 for 30 days; thereafter Free $1 monthly credit, Hobby $5 per month baseline and additional usage possible. Easier than self-managed VM, not zero-cost reliable Production.
- Northflank Sandbox: two free services but provider explicitly says not to use Sandbox for Production; payment method required.
- Vercel Python Functions supports FastAPI but Hobby is noncommercial only; serverless limits make long webhook/background processing require major rework. Existing Vercel Hobby frontend likewise needs commercial-plan review if monetized.
- Low-cost VPS: dependable alternative after owner approves a monthly budget; Meta API outbound connectivity and region must be verified.

## Prepared portable files (NOT DEPLOYED)
- deploy/full-exit/compose.yaml: separate Prod/UAT FastAPI and restricted Meta gateways, Caddy TLS, persistent volumes; NO local Postgres or Ollama.
- deploy/full-exit/Caddyfile: future proposed hostname routing, no DNS changed.
- scripts/deployment/portable-entrypoint.sh: startup without automatic migrations, seed or one-shot payment approvals.
- tools/full_render_exit_guard.py: exact Prod/UAT Neon host/DB checks, TLS and fail-closed FULL_EXIT_SAFE_START and Meta send flags.
- tests/test_full_render_exit_guard.py: offline target/writer gate tests.
- Old compose.production.yaml and compose.uat.yaml provision local PostgreSQL and Ollama; DO NOT use those as-is for Neon.

## P0 barriers and required sequence
1. Operator chooses new host, region, access/billing and gives permission to create isolated UAT; no Render shutdown.
2. Securely inventory all Render environment secret values and transfer to host after provider is provisioned. Current Render connector cannot read secret values.
3. Verify UAT Neon connectivity and UAT deployment on new host with Meta sending disabled. Preserve separate DB, cookies, signed media, receipt volumes and existing UAT data.
4. Inventory and update Meta OAuth redirect and webhook URLs, public media and payment callback paths in owner-approved sequence. Old configs refer to onrender.com and may use a Production↔UAT OAuth relay.
5. Build/test durable webhook and Payexa callback hold/replay, all-writer freeze and split-brain-safe rollback. A static maintenance banner is not enough.
6. Secure independent recoverable encrypted Render backup. Fresh full dump ONLY after source write freeze; create separate new empty directpilot_live in verified Neon project and reconcile all 82 tables plus critical business data.
7. Obtain separate owner authorization for Production backend DNS/secret switch, database Cutover and provider callback update. Monitor with safe rollback.
8. Decommission both Render APIs and its Postgres ONLY after new Production/UAT accepted, data/receipt parity proven, credentials rotated and retention authorized.

## Current immutable safety
Production and UAT on Render remain LIVE. No new cloud account provisioned. No new Neon DB created. No Meta URL or backend secret changed. No Render service stopped or deleted. No deployment attempted.
Render Free PG expires Nov 2, internal target Oct 25, but never skip backups or continuity controls for deadline.

## Next owner decision
Choose Oracle Cloud Always Free VM (if eligible and available) versus a paid Docker host such as Railway/VPS. A vendor signup may require card verification. Once chosen, provision **UAT only first**, with explicit scoped permission.
