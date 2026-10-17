# DirectPilot — selective 0027 backend release, safe production database cutover

**Checkpoint:** 2026-10-17. **Status:** CODE PREPARED / LIVE CUTOVER NOT AUTHORIZED.
This supplements `docs/runbooks/production_neon_cutover.md` and `docs/releases/RELEASE_REGISTER.md`. Older records may say `directpilot_live` is empty: that statement is superseded.

## Confirmed topology and evidence

| System | Identifying details | Observed state |
|---|---|---|
| Actual live Production | Render API `directpilot-api`, Render PostgreSQL `directpilot_production_db`, PG16 | Original production write source; no cutover |
| Independent Neon Production project | `billowing-poetry-05589994`, branch `production` | PG18, **not yet live** |
| Neon staging restore candidate | Database `directpilot_live` | Restored Oct 17 Render backup; 83 public tables; Alembic 0027 |
| Old Neon copy | `neondb` in same Neon project | 82 tables; Alembic 0025; do not use as live |
| Independent UAT | Neon `round-shape-42044596/neondb` | 83 tables, Alembic 0027 |
| Selected code | `release/prod-neon-0027-backend-20261017`, PR #47 to `backend-main` | Draft: only PR #34 media/receipt backend delta and tests |

- Render backup evidence (operator-provided): `directpilot_prod_20261017_103343.dump`, SHA-256 `9E46745AA1D115EA74A0877ACEC28A53423ADE73DBEE9FD490842AAFC6D8D064`, local restore rehearsal 82 tables / revision 0025 PASS. Backup contains personal/payment data; NEVER upload to repo or chat.
- The same archive restored into an initially empty `directpilot_live` through an approved direct client: 82 tables, Alembic 0025. The additive 0026 and 0027 schema operations and historical receipt backfill were subsequently applied transactionally; Neon direct queries verified 83 tables and Alembic 0027. **This is NOT a fresh, write-frozen snapshot of source.**
- Independent UAT and restored Neon have the same **918 column schema fingerprint** and **530 index definition fingerprint**. Constraint counts are both 1,137; exact constraint definition fingerprints differ because restored PG16 and native PG18 format some CHECK casts and NOT NULL constraint names differently. Do NOT claim byte-for-byte equal constraint definitions.
- Owner-approved password rotation of Neon `neondb_owner` completed after prior URI exposure. Do not record or reuse an old URI. Provider API read-only connection to both Neon databases after rotation succeeded. Runtime Vercel sensitive DATABASE_URL was not readable; application reconnect requires testing.

## Scope of PR #47

Selective changes from UAT backend PR #34:
1. Alembic files `0026_durable_product_media.py`, `0027_traceable_receipt_versions.py`;
2. Product images persisted in PostgreSQL BYTEA with quota and secure response;
3. Durable numbered payment receipt history and tenant-scoped/admin review endpoints;
4. Matching schema, functionality, PostgreSQL and CI tests.

Do NOT merge all UAT. No current Render or Neon live service, DNS, domain, customer payment, plan, or Meta callback is changed by this PR.

## Blockers before new backend deployment

- CI jobs on PR #47 must finish PASS, including PostgreSQL 18 and Docker build; no production deploy yet.
- `scripts/deployment/docker-entrypoint.sh` **automatically calls `python -m tools.run_migrations` at every startup**. Deploying the code against the current Render database (0025) can change live schema. Release must target verified final Neon 0027 and must not run one-shot seed/admin/password reset/payment-approval flags.
- Validate actual runtime settings, encryption/signing keys, role access, TLS and resource limits from an isolated process; do not expose credentials or customer records. The Vercel/Hobby commercial eligibility is a separate blocker when choosing Production hosting.
- Existing Media files external to database (if any) must be inventoried: restoring PostgreSQL alone does not restore arbitrary Docker-local files.

## Safe final sync and cutover sequence (not yet executed)

1. Separate Owner **GO** and approved maintenance window. Preserve existing live Render API. Inventory write paths: signup/session, orders, manual receipts, admin approvals, Meta webhook/worker/retry, payment callbacks/schedulers. Put them into a verified freeze or durable hold/replay. A frontend banner alone is insufficient; do not acknowledge undurably dropped webhooks.
2. Record source snapshot timestamp and payment/order/webhook last sequence. With writes frozen, produce **a fresh independent** Render full dump, SHA-256, archive integrity check, encrypted off-device copy and successful isolated restore.
3. Do NOT blindly restore over nonempty `directpilot_live` or older `neondb`. Prefer a new empty isolated Neon database or branch for fresh final copy; apply 0026 and 0027 via tested Alembic, then re-compare all table counts and key financial/idempotency/receipt aggregates, sequences, indexes, constraints and access rules.
4. Verify no Render writes after final snapshot; if new writes arrive, abort or repeat the entire snapshot during a genuine freeze. Do not use a stale staging snapshot for GO.
5. Test the **selected production Backend** against the fresh target, with outbound Meta/payment side effects disabled and strong access control. Confirm production encryption key continuity without printing tokens; request separate Owner GO before switching its DATABASE_URL and front-end API origin. Frontend talks to Backend HTTP, never directly to PostgreSQL.
6. Verify API health, signup/session without creating live fake purchases, entitlement reading, receipt-history retrieval, Meta event dedup and payment integrity before resuming external writers. Monitor Neon compute/quota, latency and 5xx. Retain Render data and rollback capability.
7. Before any writes land on Neon rollback means returning to Render; **after writes land on Neon, rollback needs reverse reconciliation** to avoid loss. No automatic switching back on errors.

## Current hard stop

**MIGRATION PREPARED ≠ LIVE PROMOTION.** Backend runtime E2E, source data delta after Oct 17 backup, full independent encrypted copy, freeze/replay and Owner deployment GO remain OPEN. Do not change Render DATABASE_URL or Frontend production aliases yet.
