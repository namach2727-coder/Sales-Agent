# DirectPilot FINAL Render → Neon Production data synchronization

**2026-10-14 status:** new empty final database `directpilot_live` was CREATED in the independent Neon Production project `billowing-poetry-05589994` (branch `br-winter-water-argmnyru`) owned by `neondb_owner`. An independent SQL SELECT confirmed **zero application tables and zero public sequences**. Existing older rehearsal DB `neondb` remains unchanged. **NO Render data has yet been copied into the final database. NO Cutover has occurred.**

## Why full execution is currently BLOCKED

1. Render source Production PostgreSQL `directpilot-production-db` is ACTIVE but has `ipAllowList=[]`. The hosted Render SQL tool explicitly refuses connections; it also has no stable outbound IP for allowlisting. Assistant cannot fetch a fresh dump from that Render Postgres using available connectors.
2. The owner-operated Windows workstation previously ran guarded `pg_dump`/restore with private source credentials and Docker/Postgres client tools; the hosted assistant cannot execute code on that laptop.
3. **All application writes are still active** on `directpilot-api`. DirectPilot has both Instagram webhook receivers, a Payexa GET/POST callback that verifies payments, order creation, receipt uploads, subscriptions and admin actions. An all-writer freeze with **durable webhook/callback hold-and-replay** has NOT been independently implemented or validated. Merely disabling outbound Meta sends or placing frontend in maintenance does not safely freeze payments/webhooks.
4. An **independent encrypted/offsite recoverable backup** is not yet confirmed. The previous owner's waiver was for the rehearsal snapshot ONLY.
5. The Production restored Neon `neondb` snapshot from October 13 is **stale**. Its 82 tables/14 subscriptions/15 orders/1 manual payment do not prove current Render row counts.
6. The current separate `directpilot_live` has no rows/schemas yet; it is deliberately empty and protected from any restore until all gates PASS.

**IMPORTANT:** User authorization to start final sync does NOT imply permission to drop/overwrite tables, knowingly lose paid orders/messages, start an untested webhook downtime, or redirect production traffic. Source Render remains authoritative until explicit live cutover and verified event-safe handoff.

## Local operator execution — ONLY after ALL gates verified

The guarded helper `tools/production_final_sync.py` is provided on GitHub. It is operator-only because source Render DB is not reachable by connected cloud tools.

### Prerequisites

- Check out latest reviewed `backend-main` on a **trusted private Windows workstation** preserving local dirty work. Verify Python 3.10+ and PostgreSQL 18 tools or Docker Desktop.
- Have the verified Render **external Production DB URL** and independent Neon **DIRECT** URL for database **`directpilot_live`**. Keep both secret: DO NOT paste them into ChatGPT, commit to Git, screenshots, files under repo, CI logs or public terminal commands.
- Temporarily allow **only the operator laptop /32 IP** in Render PostgreSQL Networking if needed to perform source export; NEVER allow `0.0.0.0/0`. Revoke /32 immediately after export/verification. This requires the operator in Render dashboard and should not be applied prematurely.
- **Prove all writers quiescent** with explicitly approved reversible maintenance gating AND durable capture/retry for *both* Meta webhook routes plus Payexa callbacks, including in-flight requests, workers, signup/login/session state, order/receipt/payment approvals, state changes and idempotency. If unproven, **STOP** before attempting FINAL backup/restore.
- Preserve encryption/signing keys and receipt/file objects outside PostgreSQL. Obtain a separate encrypted offsite restore-tested source backup and retain source Render.
- Keep source freeze intact until after final table count + critical content/financial event reconciliation and separately approved Go/No-Go.

### Phase 1 — fresh consistent frozen Render backup

Set `DIRECTPILOT_RENDER_SOURCE_URL` **privately and temporarily in the local process**. Run from Backend repository root **only after the write freeze is actually proven**:

```powershell
python -m tools.production_final_sync backup --folder "D:\DirectPilot-Private-Final" --freeze-confirmation ALL_CUSTOMER_WRITES_AND_WEBHOOKS_FROZEN
```

This generates `directpilot-final-YYYYMMDDTHHMMSSZ.dump` and matching `.manifest.json` with SHA-256, checks archive contains table data, and never modifies Render. A flag is an operator attestation, **not technical proof that the freeze is real**.

### Phase 2 — protected backup & empty-target restore

- Copy the dump to an **independently encrypted/offsite** location; verify its checksum and **test that it restores into a disposable database** (not Neon `neondb`, UAT or the proposed live target). Maintain evidence privately.
- Set `DIRECTPILOT_NEON_TARGET_URL` privately to the direct TLS connection URL for **`directpilot_live`**, not old `neondb`. Do not change the Running Render Backend `DATABASE_URL`.
- Use the *specific newly generated file* and maintain the proven all-writer freeze:

```powershell
python -m tools.production_final_sync restore --archive "D:\DirectPilot-Private-Final\directpilot-final-YYYYMMDDTHHMMSSZ.dump" --freeze-confirmation ALL_CUSTOMER_WRITES_AND_WEBHOOKS_FROZEN --recovery-confirmation OFFSITE_ENCRYPTED_BACKUP_RESTORE_TESTED --confirm-empty-target-restore
```

The helper checks: exact independent Neon host and database name, TLS, checksum/manifest, backup age (≤2 hours), availability of archive tables, PostgreSQL public schema object emptiness, and performs `pg_restore --single-transaction --exit-on-error --no-owner --no-privileges`. **No `--clean`, `DROP`, `TRUNCATE`, or overwrite permitted.** Fails closed if the target has any public tables, indexes or sequences. Abort upon error; don't manually clean/retry against a partially loaded DB.

### Phase 3 — post-restore reconciliation and distinct Cutover

- Independently compare the **current frozen Render source** with fresh `directpilot_live` across all expected application tables, FK/index/constraints, all row counts and (when sensitive-data-safe) critical content fingerprints and numeric aggregates; include auth sessions, tenant subscriptions, orders, manual card payments, receipt binary size/checksums, pending/outbound Meta/webhook event IDs, and last accepted callbacks. **Matching counts alone are NOT a complete proof of row parity.**
- Verify Python SQLAlchemy reads using read-only connections against the final database and verify the exact Alembic head. The existing `tools/neon_readonly_preflight.py` targets *old rehearsal `neondb`* and must not be run against final DB without a reviewed safely scoped variant.
- Complete rollback and provider webhook replay validations. Any mismatch, missed/double event, degraded capacity or encryption key failure → **NO-GO**; leave both DBs intact and keep Render authoritative.
- Live Production DB URL, Backend relocation, DNS, Meta callbacks, payment callbacks and Render deletion require additional explicit owner Go/No-Go. A successful Restore is **not** a live Cutover.

## Live state

`directpilot-api` remains on Render with `autoDeploy=no`; `directpilot-uat-api` remains separately active on Render. Neon UAT project `round-shape-42044596` is untouched; old Neon Production rehearsal `neondb` remains intact. The new database `directpilot_live` is currently empty. No credentials were transferred to Neon project settings.
