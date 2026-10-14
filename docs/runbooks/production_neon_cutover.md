# DirectPilot Render → Neon Production — Controlled Cutover Runbook

## 2026-10-14 Preflight update — ACTUAL restored Neon read-only PASS

**Operator/Codex reported PASS** for actual isolated restored Neon SQLAlchemy 2.0.41 / psycopg 3.2.9 / Alembic 1.16.5 with verified TLS/host and **server-enforced read-only transactions**. Independent Neon SQL verified 82 tables / 76 sequences / 522 indexes / 427 original constraints, no invalid indexes/unvalidated constraints, Alembic 0025 and 14 subscriptions / 15 subscription orders / 1 manual payment with zero checked orphan relations. This is NOT a write or Meta/payment E2E test. Historical NOT VERIFIED rows below are superseded by this update.

**Compute status:** Neon `describe_project` now shows `compute_time_seconds=1746`, `active_time_seconds=6888`; actual billed CU-hour burn, cold-start and full load remain unverified. Live Render remains source. No final write-frozen snapshot or separate cutover authorization exists.



**Status 2026-10-14: PLANNED / NOT AUTHORIZED / NOT EXECUTED.** Production remains on Render PostgreSQL. This document contains no secret values and is not executable automation. Existing restored Neon `neondb` is an **old snapshot** for rehearsal only. Never switch the live API to it without a fresh final sync.

## Fixed topology and expiry

| Component | Identity | State |
| --- | --- | --- |
| Render Production source | `directpilot-production-db` | PostgreSQL 16, Free; expires 2026-11-02 11:59:46 UTC |
| Canonical source ID | `dpg-db0escm0tbcc73fhig2g-a` | Verify ID from Render dashboard before every operation |
| Render Production API | `srv-db0f3uc9v7es73b5k51g` | Live `bfe67fd`; `autoDeploy=no` |
| Neon Production project | `billowing-poetry-05589994` | PostgreSQL 18.6, AWS us-west-2 |
| Neon rehearsal database | `neondb` | 82 tables, Alembic 0025, snapshot from 2026-10-13 |
| Neon UAT | `round-shape-42044596` | Different project; NEVER import or overwrite |
| Proposed final target | New EMPTY `directpilot_live` database in verified Neon Production project | **NOT CREATED**; conditional on owner approval |

**Internal deadline: October 25**; hard external expiry: November 2. Mark dates as risk targets, not proof that changes occurred.

### Verified restored-data and recovery observations — October 14

- Independent Neon read-only SQL returned `alembic_version=0025_trial_three_days`, 82 application tables, 0 invalid indexes and no missing FK validations. The backup is still a point-in-time copy.
- Existing restored Production data contains **one manual payment record with an inline 40,139-byte receipt blob** in PostgreSQL and a `receipt_storage_key` reference. The current admin receipt endpoint first reads `receipt_data` from DB and falls back to filesystem for legacy receipts. Re-test retrieval offline against verified secrets during cutover; future/legacy external receipt files (if any) require separate inventory and backup.
- The Neon project currently reports **zero saved snapshots and an empty snapshot schedule**. Neither the restored Neon branch nor short plan history should be treated as independent durable DR; arrange protected off-provider archives and tested restore.
- Restored Production includes stored encrypted Instagram connection token metadata; encryption and signing key continuity must be verified in an isolated, outbound-disabled process. Never print/decrypt these secrets into reports.

## Prerequisites before opening maintenance

1. **Owner go/no-go:** obtain separate explicit written approval for the final database cutover and anticipated controlled downtime. No implicit approval from Git merges or this runbook.
2. **Backups:** create and verify an independent protected recoverable source backup. Previous archive `directpilot-production-20261013T104236Z.dump` and SHA-256 only prove the OLD snapshot's integrity, not current source continuity. Owner's encryption deferral was for rehearsal; durable Production DR is still OPEN.
3. **No write ingress:** inventory all app writers: frontend signup/login sessions, orders and subscription purchase, manual payment receipt uploads and admin approvals, Meta webhook receivers/sending and reconciliation, service background workers, scheduled actions, token refresh, and provider callbacks. A frontend maintenance banner alone does NOT freeze background/webhook writes.
4. **Webhook safety:** define durable inbound queue/retry contract for Meta and payment callbacks. If external providers do not retry reliably, arrange an accepted hold-and-replay method and explicitly communicate any interruption; never return success to a webhook if its payload was not durably stored.
5. **Encryption secrets:** confirm required existing Production signing/encryption keys and customer receipts stored as `bytea` will remain valid after migration. Test token decryptability **only in an isolated, side-effect-disabled process**. Do not rotate keys as part of cutover unless separately reviewed.
6. **Capacity/availability:** measure actual Neon Free CU-hour consumption from Neon Console, idle suspension and wake latency, with representative traffic. Current API value `compute_time_seconds=0` is unreliable. 0.25–2 CU, Free 100 CU-hour/month, pooler disabled. Decide a paid fallback before first real customers if Free is insufficient.
7. **Rollback approach:** restoring Render DATABASE_URL after writing to Neon is NOT safe without reverse data reconciliation; define maintenance freeze, final authoritative database, abort window and responsible operator.

## T-minus 30 minutes — Preflight

- Confirm source Render DB is AVAILABLE, API LIVE, current Alembic head `0025_trial_three_days`, relevant counts and verified restore plan. Temporarily allowlist only the trusted operator /32 if necessary for source export; revoke immediately after source activities.
- Confirm Neon project and region and no UAT overlap; isolate the rehearsal `neondb` and **do not overwrite it**. The proposed **empty final target** should be newly created, explicitly named/approved and separately verified to have zero user tables.
- Validate PostgreSQL 16→18 compatibility on disposable CI: PR #24 and #25 tests PASS but *real restored data* SQLAlchemy read-only test remains required. From trusted workstation: `python -m tools.neon_readonly_preflight`, providing target Neon direct URL privately. This is a read-only check, NOT an app E2E.
- Create a private evidence folder outside Git: timestamps, baseline row counts for all tables, object counts, migration, deployment SHA, payment counts, webhook event counts, manual approvals count, last accepted event/watermark. No raw customer rows, private token values or connection strings in logs/tickets.
- Confirm `DIRECTPILOT_SEED_ON_START`, admin bootstrap/password reset and one-shot payment approval flags will **not** execute accidentally during the first migrated backend start. Render Docker entrypoint runs database readiness checks and Alembic migration on every startup: preflight and accept this behavior explicitly.
- Record emergency contacts, rollback mechanism, communication and acceptance thresholds.

## T-zero — Stop writes / capture fresh consistent source

1. Enter controlled maintenance. Disable/queue every route and worker that can write to **Render source**. Do not let Meta/payment webhook handling report success for dropped events. Confirm active database transactions are completed.
2. Record an authoritative read-only baseline of table counts, key financial/tenant invariants, migration revision, and the final accepted message/order/payment watermark. A SQL transaction in `REPEATABLE READ READ ONLY` is recommended; no stale daily BI/snapshot count.
3. Run a **new full consistent `pg_dump -Fc`**, validate `pg_restore --list` plus SHA-256 manifest and protected independent copy. The Oct 13 dump is NOT sufficient for cutover. Check bytes/row count and scope.
4. Freeze persists until target is loaded, reconciled and the switchover is approved. If freeze cannot be verified or new source writes occur after the export, **ABORT**; do not pretend zero data-loss risk.

## Restore into NEW EMPTY destination, not the old rehearsal DB

1. Only after go/no-go, create a separate EMPTY Postgres database in the independent Neon Production project (proposed `directpilot_live`). Do not drop/truncate `neondb` and never touch Neon UAT.
2. Use PostgreSQL 18 `pg_restore` with explicit confirmed target hostname/database and `--exit-on-error --single-transaction --no-owner --no-privileges`. Existing `tools/production_db_transfer.py` is hardcoded to `neondb` and **must NOT be pointed at an alternate database without a separate reviewed scoped change**.
3. Reconcile table/sequence/index/constraint counts, `alembic_version`, source vs target per-table row counts, subscription expiry, orders, manual receipts (including `bytea`), tenant references, sessions, card/account data, Meta connections and idempotency events. Use only counts/aggregate checks in shareable reports; run sensitive functional verification offline.
4. If row counts differ or constraints fail: **ABORT**; remain on the original Render source and keep maintenance as needed. Do not attempt unsafe repeated import onto a nonempty DB.

## Controlled switchover after green data checks

1. Validate the production backend's Python dependencies, SQLAlchemy SSL connection and conservative per-worker pool limits against a disposable or **read-only protected** target first. Avoid broad migrations, seed, payment approval or Meta sends in smoke.
2. Only with explicit approved cutover: securely set the **Production Render Backend DATABASE_URL** to the verified Neon final database (never UAT and never rehearsal DB), deploy/restart only the authorized service and confirm correct SHA/startup/migration and HTTP `/live` + `/ready`. Do not log credentials.
3. Validate authentication and customer dashboards and commerce data without creating/approving real payments; verify receipts/entitlements and check error logs and timeout/sleep/wake. Temporarily keep external write ingress paused.
4. Once owner accepts target state, reopen traffic/queue consumers, resume callbacks carefully with deduplication, and monitor source and target for split-brain. If duplicate or missing events appear, pause again and reconcile before proceeding.
5. Post-cutover watch: errors, DB connections, Neon CU-hour burn, disk/quota, auth, payment approval, Meta events, backup completion and restore recoverability. Retain source until an owner-approved retirement date.

## Failure and rollback

- **Before any writes on Neon:** stop deployment, retain Render as source, revert credentials only with authorized change, validate Render readiness and queued events before reopening.
- **After writes begin on Neon:** do NOT just flip the DATABASE_URL back; source Render is stale. Freeze writes again, recover or replay *all* new Neon changes or use a verified reverse migration path, then explicit owner go/no-go.
- **Any suspected data loss or security failure:** halt cutover, retain immutable logs and approved backups, do not run destructive cleanup.
- Revoke temporary Render /32 promptly once source access is no longer required.

## Evidence / current exit criteria

| Gate | Status as of 2026-10-14 |
| --- | --- |
| Render inbound allowlist zero | **PASS** (Render API `ipAllowList=[]`) |
| Rehearsal Neon restore with 82 tables and migration 0025 | **PASS** |
| Synthetic PG18 / SQLAlchemy CI | **PASS** |
| Actual restored Neon read-only SQLAlchemy CLI | **PASS per operator/Codex** (server-enforced read-only; independent data cross-check) |
| Secure independent offsite backup | **OPEN** |
| Fresh source snapshot with writes frozen | **NOT STARTED** |
| Empty final target created and populated | **NOT STARTED** |
| Provider webhook hold/replay and data parity | **NOT VERIFIED** |
| Neon CU budget and cold-wake | **NOT VERIFIED** |
| Owner-approved cutover | **NOT AUTHORIZED** |

**Prohibition:** This file authorizes NO changes to Production runtime, database, Neon schema, DNS, Meta, billing or webhooks.
