# DirectPilot Production Database — Neon Free Evidence & Maintenance-Window Plan

**Checkpoint:** 2026-10-14. **STATUS: PLAN READY FOR REVIEW; EXECUTION BLOCKED.**
This is an operations plan, **NOT** consent to pause the site, touch Meta/Payexa, open Render database networking, create/delete databases, deploy, migrate data, or change `DATABASE_URL`. Production remains on Render; Neon `neondb` is only a restored snapshot. UAT is separate and must never be changed.

## A. Confirmed infrastructure and usage evidence

| Field | Verified observation |
| --- | --- |
| Neon Production project | `billowing-poetry-05589994`; Free `free_v3`, region `aws-us-west-2` |
| Neon test restore | `production` branch `br-winter-water-argmnyru`; `neondb` PG18.6, 82 tables, Alembic `0025_trial_three_days` |
| Compute endpoint | `ep-super-moon-arziccng`, 0.25–2 CU, no pooled endpoint active, `suspend_timeout_seconds=0` (provider default 5 minutes on Free) |
| Project counter | `compute_time_seconds=1746`, `active_time_seconds=6888`; consumption period 2026-10-12T06:36:22Z–2026-11-01T00:00:00Z |
| CU-hour **estimate** | If `compute_time_seconds` is CU-weighted seconds: 1746 / 3600 = **0.485 CU-hour** (0.485% of the 100 CU-hour Free limit); active wall time 6888 / 3600 = **1.9133 hours**, implied average compute size 1746 / 6888 ≈ 0.2535 CU |
| Provider status | Compute was observed `idle`, then a guarded SELECT succeeded and endpoint became `active`; end-to-end hosted connector request latency measured ~6653 ms, **not actual customer API cold-start latency** |
| Delta counter | No settled increase was yet observed immediately after read-only wakeup; assume reporting lag, not free compute |
| Free plan | 100 CU-hours/project/month, 1 GiB Postgres storage/project, compute autosuspend after 5 minutes; quota exhaustion can suspend access until next period |
| Free capacity scenarios | At continuous **0.25 CU** usage: 6 CU-hours/day, ~180 CU-hours in a 30-day month (over quota). At 0.25 CU, Free allowance buys at most 400 active hours/month or ~13.3 h/day, ignoring higher-CU bursts. Illustrative scenario, NOT measured Production forecast |
| Latest Neon snapshots | `list_snapshots=[]`, `get_snapshot_schedule.schedule=[]`; Neon Free also provides a limited native restore history, which is NOT independent provider/offsite disaster recovery |
| Render production source | `dpg-db0escm0tbcc73fhig2g-a`, `available`, external `ipAllowList=[]`, expires **2026-11-02T11:59:46.610475Z** |
| Render runtime | Production `directpilot-api` LIVE backend `bfe67fd`; `autoDeploy=no`, health path `/live` (no DB query). UAT remains independent |
| Render 24-hour demand sampling | HTTP request_count and latency returned **empty time series** for 2026-10-13T05:45Z–2026-10-14T05:45Z; cannot infer zero traffic from absent monitoring data. Hourly DB active-connection samples were 0–2; **not representative concurrency peaks** |

### Capacity decision: NOT YET PASS

- **Measurement needed:** Neon Console → project → **Usage** (Free quota consumption) at two points at least 24 hours apart with representative customer load, recording CU-hours, compute-size peaks, bytes/storage, cold-wake, and connection count. Some newer provider consumption-history APIs are unavailable to Free customers; the exposed project API counter is a provisional estimate, not invoice-aligned billing.
- **Free-plan stop conditions:** projected monthly CU-hour use over 100; sustained database activity >~13.3 h/day even at 0.25 CU; unacceptable cold-wake; failed logins/timeouts; telemetry not available to detect quota exhaustion; storage not protected. In these cases arrange an explicit paid/alternative capacity decision before placing real customer traffic on Neon.
- **Pooling:** current Backend SQLAlchemy defaults are **10 base + 20 overflow connections per worker**, Docker default 2 workers = theoretical 60 possible connections, NOT actual observed. Do not change pooler settings untested. Trial 2–3 base / 2–3 overflow per worker can be benchmarked in a disposable environment; direct connection stays for `pg_dump`/`pg_restore`/migrations.
- **No implicit monitor:** Do not poll `/ready` continually (it queries database) or run repeated connector SELECTs as a “monitor”; this can keep Free compute awake and bias results. Existing Render `/live` check is preferable for a sleep-friendly health probe.

## B. Maintenance design / blast-radius inventory

**Business source-of-truth remains Render PostgreSQL 16.** The copied Neon `neondb` is a snapshot created 2026-10-13 and is not synchronized.

**Observed write-sensitive code paths (not exhaustive; inventory all API routers before GO):**

| Class | Actual routes / implementation | Freeze requirement |
| --- | --- | --- |
| Account creation and sessions | `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout` via `app/commerce/router.py`; `/auth/login` and `/logout` via `app/authentication/router.py` | Prevent account/session writes without breaking public informational pages |
| Subscription purchase | `/api/v1/orders` via `app/commerce/router.py` | Disable new orders; preserve all pending orders, expiry snapshots and idempotency |
| Manual card transfer | `/api/v1/payments/{payment_public_id}/receipt` and corresponding admin payment approval/rejection handlers | Disable receipt submissions and admin decisions only within approved freeze; preserve inline `bytea` receipts and legacy external receipts |
| Payment provider | `GET/POST /api/v1/payments/payexa/callback/{payment_public_id}`; `PayexaService.verify` can update payment and activate a subscription | STOP if callback preservation/retry contract has not been documented and tested; 303 redirect is not a durable acknowledgment |
| Meta webhooks (new and legacy) | `POST /api/v1/integrations/instagram/webhook` and `POST /webhooks/instagram` | Both require verified durable ingress or tested provider retry/replay. They can persist inbound events and trigger real outbound Instagram messages |
| Meta send / reconciliation | `app/application/services/instagram_outbound_reconciliation.py`, `app/instagram_channel/router.py`, `app/instagram.py` | Disable send operations, workers and replay until target becomes authoritative; ensure no duplicate customer replies |
| Background / startup writes | `scripts/deployment/docker-entrypoint.sh` runs `tools.run_migrations` on every app start; optional seed, admin bootstrap/password reset, and one-shot payment approval flags | Inspect flags and prove disabled, test migration head on final target, disable automation during freeze |

**CRITICAL P0 FINDING:** No established comprehensive maintenance-mode write barrier and durable inbound webhook queue/replay implementation has been verified in the deployed version `bfe67fd`. A marketing banner, `META_SEND_ENABLED=false`, or stopping frontend traffic does not guarantee write freeze. **Do not approve a live maintenance window until operator demonstrates a reversible, tested mechanism covering all writers and durable webhook/Payexa events.** Unproven provider retry timing must never be asserted or treated as guaranteed.

## C. Proposed window (for owner approval only)

- **Target business period:** before internal Oct 25 goal and well before source expiry Nov 2. Choose **date and clock time with the owner**, informed by actual traffic. Do NOT auto-schedule, restart, enable Render Maintenance Mode, or change routes based on this proposal.
- **Proposed operational budget:** up to **120 minutes of controlled write pause**, with checkpoint at T+60 and GO/NO-GO at T+90. These are planning limits, **not guaranteed completion times**. If a safe rollback before write reopening is impossible, abort; do not overrun silently.
- **Stage-only activity BEFORE window:** establish separate recoverable protected backup; confirm cold-wake/quota readiness; dry-run webhook ingestion/hold-and-replay and payment receipt access in an isolated copy; review migration, roles, SSL, compute, tenant/session secrets and precise deployment action; validate a guarded restore tool that supports an explicitly approved new empty `directpilot_live` target. Existing restore script expects `neondb` and must not be repointed ad hoc.

### Before T=0 — prerequisites / assignments

| Owner role | Required evidence |
| --- | --- |
| Business owner (GO/NO-GO) | Approves date, duration, impact and rollback authority **separately from planning** |
| Backend operator | Lists ALL writable routes, jobs, admin and third-party callbacks; demonstrates reliable freeze/unfreeze and replay |
| DB operator | Tests isolated restore, verifies fresh backup+hash, source/target identities and parity reports without secrets |
| On-call verifier | Verifies sign-in, subscriptions, payment receipts, Meta event count/idempotency, error logs, response time, and CU telemetry |
| Communications owner | Notifies affected users/support and payment/Meta integration stakeholders of planned unavailability if required |

**Hard abort before T=0** if: missing durable protected backup, missing safe webhook/Payexa hold strategy, unclear auth keys, missing approved new empty target/restore script, insufficient CU quota visibility, or lack of owner GO approval.

### T=0 to T+15 — Freeze and prove source quiescence

1. Deploy only the preapproved **reversible** ingress freeze mechanism; pause all direct API writers, admin actions, worker/scheduler and Meta/Payexa callbacks with **durable handling**. Record start timestamp and accepted-last-event watermark. Reject, rather than silently 2xx-ACK, events that cannot be safely stored; check actual provider retry guarantees and notify owner of residual risk.
2. Reconcile inflight requests, unfinished transactions and any already-accepted webhook deliveries; prove Render source row counts/critical last-write watermark remain stable across an observation period.
3. Any new unaccounted source write after baseline → ABORT and restart controlled process, not data switch.

### T+15 to T+35 — New consistent backup and isolated restore

1. Export **fresh** transactionally consistent PostgreSQL 16 `pg_dump -Fc` from Render **after freeze**; verify archive list, SHA-256 manifest, and independent encrypted/off-provider copy.
2. Restore using guarded PostgreSQL 18 `pg_restore --exit-on-error --single-transaction --no-owner --no-privileges` into the **new separately approved EMPTY destination** (proposed `directpilot_live`, **not yet created**); never overwrite the `neondb` rehearsal or touch UAT.
3. Keep Render source and freeze active. If any restore, timing, permissions, extension, migration or destination identity check fails: ABORT, leave original intact.

### T+35 to T+65 — Parity and safe rehearsal

- Compare ALL table counts and, for critical commerce/auth/Meta tables, relevant aggregate and cryptographic/field integrity checks where feasible. Validate 82-table schema (if source schema changes, adjust expected count only with reviewed migration), sequences, indexes, FK constraints, `alembic_version`, tenants, orders, subscriptions, inline/legacy receipt files, session/idempotency keys, Meta delivery event count and last accepted source watermark.
- Confirm protected token encryption key continuity without printing or sending secrets and **without calling external Graph or payment endpoints**.
- Confirm target can serve **read-only** app DB preflight; no real payments, sends, sessions or external callbacks allowed in rehearsal.
- Sign-off checkpoint: no unresolved source→target differences. Row-count parity alone cannot guarantee content identity.

### T+65 to T+90 — Explicit GO / no-write warm start

- With owner GO, securely update **only approved Render Production Backend DATABASE_URL** to approved fresh Neon database and start reviewed exact backend revision; ensure one-shot seed/reset/payment flags OFF, migrations already at head, app readiness PASS.
- Keep external write ingress frozen. Perform read-only smoke of /live, /ready, public catalog, customer identities under safe isolation, plan/entitlement and receipt metadata. No unapproved new login/session mutation during freeze.
- If confidence or parity fails, **revert before reopening writes**, maintain Render as source and replay preserved events only after source is authoritative again.

### T+90 to T+120 — Open and monitor ONLY after final owner acceptance

- Reopen API writes and webhook/Payexa deliveries **in a controlled sequence**, replaying buffered messages with deduplication; confirm orders/payment state and customer message delivery once, not twice.
- Monitor new Neon authoritative writes, Render stale source isolation, API status, provider callbacks, 4xx/5xx, CU-hour slope, DB storage, connection limits and idle wake. Preserve Render and backup until separate retention approval.
- **Rollback after first Neon write is NOT a simple DATABASE_URL flip.** Pause all writers again and use verified forward/reverse recovery plus operator GO. Unplanned dual-write/split-brain → STOP immediately.

## D. Decision ledger / current blockers

| Checkpoint | State on 2026-10-14 |
| --- | --- |
| Historical snapshot restore + 82-table parity | PASS; old snapshot only |
| Real SQLAlchemy/TLS/READ ONLY to restored Neon | PASS operator report; verified Neon SQL catalog separately |
| Neon idle→active SELECT smoke | PASS; ~6.65 s connector round trip, **not** p95 site SLA |
| Neon billed Free CU-hours under real demand | **OPEN** (provider counters approximate; HTTP demand metric unavailable) |
| Neon snapshots/scheduled snapshots | None observed; independent recoverable backup still **OPEN** |
| Render database temporary /32 allowlist removed | PASS / 0 rules |
| All writers and webhook/Payexa durable hold solution | **OPEN / BLOCKING** |
| New fresh Render backup under verified write freeze | NOT STARTED |
| New empty `directpilot_live` + scoped restore tooling | NOT CREATED / NOT APPROVED |
| Content-sensitive parity, rollback rehearsal, zero split-brain | **OPEN** |
| Owner approves maintenance date and execution | **NOT APPROVED** |
| Live DATABASE_URL or service deployment changed | **NO** |

Keep all sensitive files and reports out of Git and chat. See `docs/runbooks/production_neon_cutover.md` for background and prior acceptance history.
