# DirectPilot Project Roadmap & Continuity Checkpoint

## 2026-10-14 Env architecture clarification and scoped audit (P0)

**Status: no app Environment Variable transfer to Neon.** Backend is still hosted on Render `directpilot-api`; Neon Production `billowing-poetry-05589994` hosts the PostgreSQL copy only; Functions are unavailable for this project. Keep ALL existing Render app keys/values (Meta/IG crypto, payment, cookies, third-party credentials, bootstrap flags) in Render. The future Render-side `DATABASE_URL`/`DATABASE_URL_FILE` update is distinct, requires fresh Neon final DB, verified freeze/reconciliation, and separate owner approval. No changed env values yet.

**Action delivered in PR #28:** offline `tools/render_env_key_audit.py` (names-only, rejects `KEY=value`, catches removed keys), `tests/test_render_env_key_audit.py`, and `docs/runbooks/render_neon_environment_preservation.md`. Actual Render env value parity is **not verified**: connected Render service inventory has no secret read/list capability. Do not claim secrets copied, extracted or moved. PR CI and merge status must be independently checked.

---


## LATEST P0 DECISION BOARD — 2026-10-14 Neon Free usage and maintenance

**Usage:** Free 100 CU-hour/project/month; Neon project API `compute_time_seconds=1746` and `active_time_seconds=6888`; conditional ~**0.485 CU-hour** estimated usage (0.485% Free allocation), **not** independently verified Console billed consumption. Endpoint idle→active observed on successful SELECT with ~6.65-second connector round trip, not app p95. Auto scale 0.25–2 CU; continuous 0.25 CU for 30 days ~180 CU-hour. Source Render 24h HTTP/latency telemetry returned empty time series (NOT zero requests). Real Production demand/Neon quota burn **OPEN**.

**Maintenance plan:** `docs/runbooks/neon_free_usage_and_maintenance_plan.md` records actual mutating API surfaces, 120-minute provisional write-pause budget, checkpoints and abort/rollback contract. Business owner has NOT picked clock time, approved outage or approved cutover. **P0 blocker newly explicit:** no independently demonstrated all-writer freeze and durable hold/replay for both Meta webhook endpoints plus Payexa callbacks. Startup auto-migration and one-shot reset/seed/payment flags require audited isolation. Runbook only: no infrastructure or app deploy.

**Remaining gates:** tested edge/write-freeze and guaranteed preservation/at-least-once replay with idempotency; independent encrypted recoverable backup; fresh source write freeze and snapshot after last accepted event; approved empty Neon final target/restore tooling, full parity and split-brain-safe rollback; Free usage/cold wake under representative traffic; separate explicit owner GO. Temporary Render DB public /32 remains absent (ACL count 0). Source expires Nov 2; internal goal Oct 25.

---


## P0 GATE STATUS UPDATE — 2026-10-14 — ACTUAL RESTORED NEON PREFLIGHT PASS

**Newly CLOSED gate:** Operator/Codex ran `python -m tools.neon_readonly_preflight` on owner workstation against exactly approved independent Neon Production `neondb`; result `OVERALL_STATUS=PASS`: SQLAlchemy 2.0.41, psycopg 3.2.9, SSL, PostgreSQL 18, server-enforced read-only transactions. Production, UAT, Meta, database data and live API were not modified per operator report.

**Independent hosted verification:** 82 tables, 76 sequences, 522 indexes, 427 original constraints, 0 invalid indexes and 0 unvalidated constraints, Alembic `0025_trial_three_days`; subscriptions=14, orders=15, manual payments=1, orphan/invalid periods=0, three trial plan durations=3. Operator's SQLAlchemy/TLS behavior is **operator-reported PASS**, not a remote re-run.

**Compute monitoring baseline:** `Neon.describe_project` returned `compute_time_seconds=1746`, `active_time_seconds=6888` on 2026-10-14 (previously zeros). These API counters are not themselves a paid-invoice/CU-hour burn reading. **Free-plan capacity remains OPEN** pending Neon Console settled consumption, idle/wake test and realistic traffic estimate.

**Go/no-go blockers remain:** encrypted independent recoverable backup; fresh final Render snapshot/delta with complete write-freeze and safe Meta/payment callbacks; dedicated EMPTY Neon final destination (proposed `directpilot_live`, NOT created), reconciliation of 82 tables and finance/idempotency, split-brain-safe rollback, and **explicit separate live cutover approval**. No live DATABASE_URL change, no migration and no Render/UAT deployment. Render source expires **2026-11-02**; target decision by October 25.

---


## LATEST 2026-10-14 P0 READINESS REVIEW — controlled cutover not authorized

- **PASS:** Render Production PostgreSQL remains available and API inventory confirms zero external inbound IP allowlist entries. Old rehearsal Neon `neondb` 82 tables/Alembic 0025 and PostgreSQL 18 read-only catalog integrity confirmed. Synthetic PG18 CI passed.
- **NEW P0 finding:** Neon project `billowing-poetry-05589994` returned `list_snapshots=[]` and `get_snapshot_schedule=[]`; no scheduled independent snapshots evidenced. A PostgreSQL manual payment record has 40,139 bytes of receipt_data inline in restored target, and code supports inline-first/legacy filesystem fallback. Audit external legacy receipt files and protected independent backup before cutover.
- **PLAN RELEASED:** `docs/runbooks/production_neon_cutover.md` merged via backend PR #26, SHA `9ba207da2c5b18bf77003fd7e9b409ac69533f08`, CI run `38514922043` **4/4 PASS**. Covers maintenance/write freeze, fresh pg_dump, proposed separately approved empty `directpilot_live` database (not created), final row and commerce/webhook checks, forward recovery and rollback safeguards. This is a runbook only: no Neon new DB, deployment or live cutover.
- **OPEN HARD GATES:** real restored-data SQLAlchemy preflight on owner workstation, Neon billed CU-hour and cold-start evidence, protected independent restorable backup, webhook hold/replay and idempotency, complete fresh source-to-target parity with freeze, tested rollback and **explicit separate owner approval**. Internal goal Oct 25 before expiry Nov 2; do not sacrifice integrity for deadline.

---


## LATEST P0 GATEBOARD — 2026-10-13 (supersedes older historical status blocks)

| Gate | Latest evidence | Status |
| --- | --- | --- |
| Render source / expiry | Production Free DB available; expiry 2026-11-02 11:59:46 UTC | **OPEN / CRITICAL deadline** |
| Off-machine backup acquisition | `20261013T104236Z` PG custom archive, 557942 bytes, SHA-256 checksum/listing verified by operator | **PASS (operator report)** |
| Durable encrypted offsite copy | Backups currently on unencrypted media; encrypted independent recovery copy deferred by owner only for rehearsal | **OPEN — blocker for live cutover** |
| Isolated Neon restore | PG18.6 `billowing-poetry-05589994/neondb`, 82 tables / 76 sequences / 522 indexes / 427 original constraints; 689 PG18 NOT NULL catalog constraints | **PASS** |
| Snapshot row parity | 82/82 table row counts matched in operator's private report; source cannot be directly re-queried through hosted Render connector | **PASS per operator; independently partial** |
| Neon data integrity | Alembic 0025, 0 invalid constraints/indexes, no orphan subscription/order/payment refs; all three trials 3 days | **PASS read-only** |
| Backend PG18 compatibility | PR #24 merged, PR #25 merged; CI `38401718878` 4/4 PASS, 905 tests PASS, 7 skipped | **PASS synthetic disposable PG18** |
| Actual copied-data SQLAlchemy test | Guarded `python -m tools.neon_readonly_preflight` available; no report of workstation execution | **OPEN** |
| Neon Free compute budget | 0.25–2 CU, idle suspend default, pooler off; returned 0 compute seconds is non-conclusive | **OPEN: measure settled CU-hours/cold starts** |
| Fresh final sync | Source live after backup; no replication or final write freeze/delta reconciliation | **OPEN** |
| Rollback and event safety | Need plan for payment approvals, active sessions, Meta webhook replay/idempotency, and prevention of split-brain | **OPEN** |
| Live cutover | Backend Production remains Render `bfe67fd` LIVE; Neon copy isolated; no approval or env changes | **NOT AUTHORIZED** |
| Render temporary /32 | Render API independently verified 2026-10-14: `ipAllowList=[]` (zero rules) | **PASS / CLOSED** |

**Priority and sequence:** (1) reconcile temporary IP rule; (2) run workstation-only real Neon READ-ONLY SQLAlchemy preflight; (3) monitor Neon console billed CU-hours, idle/wake and connection usage, decide conservative pooling; (4) protect offsite encrypted/independent restorable copy; (5) set final maintenance window + writes/webhooks freeze and verified fresh snapshot/delta; (6) rehearse rollback; (7) request explicit Production cutover authorization. **Internal target Oct 25**, before Render expiry Nov 2. Never claim zero data-loss risk or actual Production cutover based on snapshot restore alone.

**Code/runtime separation:** PR #24 `dab43e7` and PR #25 `f5b6f98` are merged **repository/CI checks**, not deployed on Render. Last confirmed Production/UAT Backend runtime remains `bfe67fd`. Current frontend Production `/solutions` has been promoted and verified Vercel READY (`79b8fad`). Supersede earlier dated TODOs implying those promotions remain pending.

---


> **Strategic roadmap / secondary continuity document.** Read `AI_HANDOFF.md` first in every new DirectPilot session; then read this file.
>
> **Latest roadmap and continuity audit:** 2026-10-13 (older dated sections are historical; follow the current P0 action plan below).
>
> **Authority rule:** verified runtime/deployment evidence > deployed commit > repository source > `AI_HANDOFF.md` > this document > old chat history.
>
> **Secret rule:** record credential names, locations, owners and verification status only. Never record secret values.

---


## P0 — Production Database Expiry and Disaster Recovery (verified 2026-10-13)

**Status: OPEN / CRITICAL. Owner priority above marketing features and nonessential deployments.**
**Source of truth:** Render workspace `tea-dabsgm0n74is738av7l0`, database `directpilot-production-db` / `dpg-db0escm0tbcc73fhig2g-a`. Read-only Render inventory on 2026-10-13 reports `plan=free`, `status=available`, `expiresAt=2026-11-02T11:59:46.610475Z` (approximately 15:29 Iran local time). Production service `srv-db0f3uc9v7es73b5k51g`, UAT service `srv-dabsmo7qj5pc7397jqf0`, both on Render with autoDeploy disabled. Neon project `round-shape-42044596` is the ISOLATED UAT database, not a Production backup or migration target.

**Primary failure mode:** Production DB expiry could make the app unavailable and put production records at risk. RISK IS NOT ZERO until an independently stored, verified restorable copy and a durable live database both exist. Do not claim zero absolute risk; after controls are accepted, classify residual risk based on measured restore results.

### Hard gates and dates (UTC dates; complete before expiry)
| Due | Priority | Deliverable | Owner / evidence / exit criterion |
| --- | --- | --- | --- |
| **Oct 14** | P0 | Verify Production data inventory and access path without changing firewall or exposing credentials. Inventory tables, orders, active subscriptions, receipts, account identities, encryption keys dependencies, background jobs and Meta integration touchpoints. | Operator + engineering; documented read-only query results, access limitations, chosen backup transfer mechanism. |
| **Oct 15** | P0 | Acquire first full Production `pg_dump -Fc` via an approved secured execution path (prefer controlled Render-side job or protected runner; do not assume empty IP allowlist allows remote connection), transfer it OFF Render ephemeral filesystem to a private encrypted durable destination. | Object existence, timestamp, bytes, SHA-256 checksum, PostgreSQL version, source DB identifier, authorized custodian; no secrets in documentation. |
| **Oct 16** | P0 | Restore into a brand-new disposable *isolated* Postgres database. Verify `pg_restore --list`, migration head, row counts and critical business invariants: accounts, tenant separation, paid subscriptions, pending orders, payment receipt blobs, admin payment cards and Meta token presence (do not expose tokens). | Restore logs, reconciliation matrix, application smoke tests, exact measured RTO and backup-age RPO. Never restore over live Production/UAT. |
| **Oct 17–20** | P0 | Select durable Production destination: **A** approved paid Render Postgres upgrade (simplest if cost accepted), or **B** a genuinely separate provider with verified connectivity/migration and sustained operational limits. Estimate total cost; check data region, retention, automated backups/PITR and support. | Owner explicitly approves infrastructure spend and/or data-provider cutover. No automatic paid upgrade. |
| **Oct 21–24** | P0 | Run rehearsal: fresh source snapshot, isolated target restore, migration compatibility, controlled app smoke; for provider move, test SSL/database URL, pooling, CORS/Meta unaffected at app level, migration head, API start/readiness, receipt fetch, subscription lifecycle and rollback. | Signed rehearsal report, verified endpoint and backup evidence, tested rollback within agreed window. |
| **Oct 25** | **HARD INTERNAL DEADLINE** | Production on durable database with validated restore and at least two independently retained backup copies; approve cutover only after reconciliation. | Post-cutover clean deployment, health/readiness PASS, data integrity checks PASS and owner acceptance. |
| **Oct 26–Nov 1** | P0 | Daily expiry watch, automated backup completion/age alerts, access check and emergency rehearsal; retain source while safe and permitted. | Alerts working, on-call/owner notified if backup or DB health fails. |
| **Nov 2** | FINAL EXTERNAL DEADLINE | **Do not depend on Free Render Postgres at expiry.** | Business continuity verified on durable destination. |

### Non-negotiable recovery architecture
1. **Prevent data loss:** Use database-consistent `pg_dump` custom format and `pg_restore` in disposable isolated DB. Existing `scripts/deployment/backup.sh` calls `pg_dump --format=custom`, `pg_restore --list` and writes under `BACKUP_DIR` (default `/app/backups`); that is NOT accepted as durable offsite backup. Existing `scripts/deployment/restore.sh` has a destructive confirmation flag: NEVER point it at Production for rehearsal.
2. **Offsite 3-2-1 goal:** At least two recoverable independent copies in different failure domains, one outside Render; encryption at rest/in transit, least-privilege access, no public URLs, SHA-256 manifest, documented keys custodian. Backups must not be committed into Git, attached to tickets/chats or moved into UAT. Receipt blobs in the DB are part of backup scope; inspect any non-DB file dependencies and back those up separately.
3. **Backup cadence:** Until durable migration, at least daily verified offsite copy; while traffic is active or immediately ahead of cutover, take a fresh consistent snapshot and enforce a write freeze or application-coordinated quiescence. On durable Production, target 24-hour minimum recovery point in first phase, then improve to <=1 hour where supported by managed PITR/continuous archiving. These are TARGETS, NOT accepted SLOs until tested.
4. **Restore and monitoring:** Automated daily job must fail loudly if source dump, offsite upload, checksum, age or retention fails. Periodic (initially weekly) disposable restore must reconcile critical counts and business state; log actual RPO/RTO, do not invent metrics. Alert on failed DB readiness, low storage and impending expiry.
5. **Cutover safety:** Obtain pre-cutover verified offsite backup; pause writes/orders/payment approval/Meta sends as necessary, avoid lost webhook events and duplicated payment/order actions, transfer final delta or full consistent snapshot, validate target and connection, switch only authorized secrets, smoke-test API and web, then reopen traffic. Rollback must be explicit: if writes have resumed on target, reverting DB URL alone may lose or split data. Never mix UAT and Production records, tokens or financial details.
6. **Security:** No DATABASE_URL or credential values in Git docs/logs. Render DB external allowlist is empty; Render's hosted MCP read-only SQL cannot connect. Assess a secure in-platform export/approved tunnel mechanism, not widening internet exposure as a shortcut.

### Risks and escalation
- **Red / blocked:** No successful offsite backup and restore proof; keep real-customer onboarding and new paid production orders gated as long as business policy allows. Escalate to owner immediately.
- **Red / Oct 17:** No durable provider choice/approval => present explicit paid Render upgrade as low-change contingency; a free replacement is not assumed durable.
- **Red / Oct 21:** No tested restore => abort migration/cutover, fix recovery first. Preserve current business records and escalate.
- **Red / Oct 25:** Not yet migrated => activate outage-prevention contingency. Obtain explicit approval for paid database upgrade; if unavailable, communicate controlled service pause before expiry rather than promising uninterrupted service.
- **Risk closure only when:** durable destination LIVE, offsite backup independent, restore PASS, reconciliation PASS, alerts enabled, operational handoff complete. Remaining nonzero risk must be stated.

### Backup execution access decision — 2026-10-13

- Read-only verification: Render Production Free Postgres external IP allowlist is empty. Hosted Render MCP read-only SQL cannot connect (Render hosted connector has no fixed allowlist IP); Free Render Web Service does not support Shell/SSH or one-off jobs. NO direct service-run backup is possible through current connectors without changing access model.
- Prepared secure offline operator procedure and tool: GitHub Sales-Agent PR #23, `tools/production_db_transfer.py`, `docs/runbooks/production_db_backup_restore.md` (CI status must be checked before acceptance). These run on owner's trusted workstation using Docker/PostgreSQL 18 client and Render *external* DB URL entered only locally. Source scope limited to Render Production, target limited to verified independent Neon Production; Restore requires explicit confirmation and empty target.
- **ACTUAL PG_DUMP: NOT EXECUTED.** **OFFSITE ENCRYPTED COPY: NOT STORED.** **ACTUAL PG_RESTORE: NOT EXECUTED.** Do not mark P0 backup/restore gates PASS.
- Required next operator step: temporarily allowlist only trusted workstation public IPv4 /32 on Render Postgres; retrieve Render external DB URL privately from Render Connect; enter it via a local secure PowerShell prompt; execute the reviewed backup script, verify SHA-256 manifest and PostgreSQL archive list, preserve an independent encrypted copy, and remove the temporary IP allowlist entry. Never paste URL or backup into chat/GitHub.
- After backup verification, enter the Neon Production direct connection URL locally for isolated restore. Then run schema/row-count and customer/payment/token presence reconciliation. DO NOT update Production DATABASE_URL or copy partial data into UAT.
- **No cutover authorization or production data mutation occurred** during this preparation.

### Actual status at this checkpoint
- DONE: Identified exact expiry and source DB/provider via Render read-only inventory.
- NEW 2026-10-13 OWNER-REPORTED Render Production storage indicator: 7.51% of 1 GB (~76.9 MiB allocated/used by displayed gauge; exact meaning and PostgreSQL logical database size require verification). This is far below Neon's 1 GiB per-project nominal storage, but does not prove dump/restore or production compute fit. Next: read-only pg_database_size if possible, backup size, table counts, Neon Production independently scoped project, isolated restore, parity checks.

- DONE: Existing backup/restore scripts reviewed, but NOT executed against Production and NOT validated for offsite durability.
- NOT DONE: Backup extraction and offsite object, recovery drill, database cost/provider approval, source-to-target migration, tested rollback, measured RPO/RTO.
- DO NOT treat Neon UAT `round-shape-42044596` as a recovery replica. Do not alter Production DB credentials, billing plan, network allowlist or connection string without separate operator approval and measured cutover plan.

---

## 0B. Current Frontend UI / Brand Release — 2026-10-11

```text
WORKSTREAM: HUMANIZED_UI_V2_AND_ANIMATED_BRAND
RELEASE: FRONTEND_PR_9_MERGED
PRODUCTION_FRONTEND_SHA: f5f6a5399f938969b9307475eeed208f0e10988b
VERCEL_DEPLOYMENT: dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ
VERCEL_STATUS: READY
PRODUCTION_DOMAIN: directpilot.ir
WWW_DOMAIN: www.directpilot.ir -> directpilot.ir
GITHUB_MAIN_MATCH: PASS
OWNER_VISUAL_ACCEPTANCE: PASS (favicon animation + dashboard/layout)
UAT_BRANCH_SHA: dd9dee1f573151cd7507877aa9a868db467c95ba
UAT_DEPLOYMENT: dpl_J3foazh8ogYg7suDPUuEzCr37mJJ
PAYMENT_META_BACKEND_ENV_CHANGES: NONE
```

The owner accepted the new UI on live Production after hard-refresh on 2026-10-11; Vercel confirms both domains resolve to the exact `main` SHA. This acceptance is **visual/branding only**, not a new logged-in functional E2E, payment E2E, browser matrix, or `sign_up` GA4 E2E. PR #9 reconciled divergent branches rather than merging all UAT history; Production SEO/GA4 instrumentation, 14-day trial copy, and manual card-transfer fixes were preserved. Rate-limited/intermediate release-branch preview failures are historical and do not describe this READY Production deployment.

The SEO/GA4 marker below is a historical PR #8 measurement checkpoint; its initial `d9a1a53` state has been superseded by the release above. Database durability (free PostgreSQL expiry 2026-11-02), validated backup/restore, conversion E2E, and separately marked plan-management retests remain independent gates.

## 0A. SEO/GA4 PR #8 Measurement Resume Marker — 2026-10-11 (historical deployment)

```text
WORKSTREAM: SEO_PLUS_GA4_MEASUREMENT
GA4_PR8_FRONTEND_SHA: d9a1a53a6171f3d417637d12cec66eed1832a07b
GA4_PR8_VERCEL_DEPLOYMENT: dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw
VERCEL_STATUS: READY
SEO_RELEASES: FRONTEND PRS #1-#8 MERGED
LIVE_SEO_AUDIT: HISTORICAL PR1-5 PASS / 6 URLS / 0 ISSUES
INDEX_TRACKER: 10 URLS INDEXED AT LAST CHECKPOINT
GA4_PROPERTY: properties/558426868
GA4_STREAM: G-9D1Z7HDYVZ
GSC_WIZARD_LINK: sc-domain:directpilot.ir -> GA4 VERIFIED
GA4_PAGE_VIEW: HTTP_204_AND_REALTIME_PASS
GA4_SIGN_UP_KEY_EVENT: CONFIGURED_DELIVERY_UNVERIFIED
WEEKLY_SEO_GA4_TASK: ENABLED / MONDAY_09_ASIA_DUBAI
SEARCH_RANKING_IMPACT: NOT YET VERIFIED
NEXT_SEO_GATE: FIRST_SETTLED_GA4_AND_SIGNUP_E2E_AND_GSC_RECRAWL
```

This marker preserves the PR #8 SEO/GA4 measurement evidence only. The current Production frontend release is PR #9 above. Older integration snapshots below are historical.

## 0. Historical Integration Resume Marker (2026-10-10)

```text
PROJECT: DirectPilot
DATE: 2026-10-10

CURRENT_PHASE:
Pilot / market-validation with separated UAT and Production

LATEST_BACKEND_SAFETY_RELEASE:
PRODUCTION_SINGLE_PILOT_SEND_ALLOWLIST_GUARD

RELEASE_STATUS:
UAT PASS / PRODUCTION LIVE / CI PASS

BACKEND_PRODUCTION:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
RENDER_DEPLOYMENT: dep-db33funavr4c739lm9v0
STATUS: LIVE
APP_ENV: production
DB: PASS
MIGRATION: PASS
STARTUP: PASS

BACKEND_UAT:
SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
RENDER_DEPLOYMENT: dep-db33f1qd0e5s73f0bk00
STATUS: LIVE
APP_ENV: uat
DB: PASS
MIGRATION: PASS
STARTUP: PASS

FRONTEND_PRODUCTION:
SHA: 4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159
VERCEL_STATUS: SUCCESS
OWNER_PRODUCTION_SMOKE: PASS FOR PRIOR RELEASE
ADMIN_PLAN_SCROLL/VALIDATION FIX: DEPLOYED / OWNER RETEST PENDING
ADMIN_CUSTOMER_AUTOMATION_MANAGEMENT: DEPLOYED / OWNER CONFIRMED

META_E2E:
PRODUCTION OAUTH PASS / INBOUND RELAY PASS / OUTBOUND E2E PASS

OUTBOUND_SAFETY:
META_SEND_ENABLED=false
PRODUCTION STARTUP REQUIRES EXACTLY ONE META_SEND_ALLOWED_ACCOUNT_IDS ENTRY WHEN SEND IS ENABLED

PRODUCTION_DB:
FREE / EXPIRES 2026-11-02
DURABILITY: OPEN
BACKUP_RESTORE: OPEN

NEXT EXACT STEP:
Resolve Production database durability and backup/restore acceptance before real-customer onboarding. Keep Meta send disabled by default after the successful controlled E2E. Verify Production LLM configuration as a separate gate.
```

Do not restart completed environment-separation, Auth/UX, SEO, Production OAuth or inbound-relay work without regression evidence.

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
Accepted deployed runtime-code SHA: 91250140cccc7c9be9102c2d6e17e6775a836f24
Runtime includes the Meta relay bridge plus the Production single-pilot outbound allowlist guard.
Later continuity-document commits, if any, must not be described as deployed runtime code unless Render evidence matches them.
```

GitHub CI for `91250140...`:
- test: PASS
- docker-build: PASS
- postgres-smoke: PASS

### Frontend

```text
Repository: namach2727-coder/directpilot-web
Production branch: main
UAT branch: UAT
main deployed (current UI+GA4) SHA: f5f6a5399f938969b9307475eeed208f0e10988b
UAT SHA (separate branch/deployment; GA4 remains Production-only): dd9dee1f573151cd7507877aa9a868db467c95ba
```

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
- Deployment: `dep-db33funavr4c739lm9v0`
- Deployed Git SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=production`: PASS
- PostgreSQL connectivity: PASS
- Migration current-head verification: PASS
- Application startup: PASS
- Auto deploy: OFF

### UAT Backend

- Service: `directpilot-uat-api`
- Service ID: `srv-dabsmo7qj5pc7397jqf0`
- Deployment: `dep-db33f1qd0e5s73f0bk00`
- SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`
- Status: LIVE
- `APP_ENV=uat`: PASS
- Database/migration/startup: PASS

### Frontend / Vercel

Production:
- Branch: `main`
- Current verified SHA: `f5f6a5399f938969b9307475eeed208f0e10988b`, Vercel `dpl_Ghi3KVJrDwpW1a1nABBDk2wztyBJ` READY; owner visual acceptance PASS.
- Historical Admin Plan UX source SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159` (do not report this as the current Production SHA).
- Admin plan UX fixes deployed: scroll preservation before paint, inline validation without native scroll-to-invalid, and automatic uppercase normalization for internal plan codes.
- Owner retest for the plan-creation UX fix: PENDING.

UAT:
- Branch: `UAT`
- SHA: `dd9dee1f573151cd7507877aa9a868db467c95ba`
- Vercel deployment: READY (`dpl_J3foazh8ogYg7suDPUuEzCr37mJJ`); branch is distinct from Production `main`.

## 5F. GA4, Conversion Measurement and Mobile Lab Baseline — 2026-10-11

- PR #6 — frontend `ae077e06915e5e280fbb5ff226ac5dd4d529891e`: consent-first GA4 tag, event bridge, limited sanitized marketing `page_view`, `signup_intent`, `pricing_plan_click`, `demo_start`, `blog_cta_click`, and `sign_up` after the backend register call succeeds; Production-only `NEXT_PUBLIC_GA_ID`, strict Preview/UAT isolation, privacy disclosure, CI tests and mobile Lighthouse workflow.
- PR #7 — frontend `31c348ab51c7dc6ae1d4c407c32da1c08a5b5c03`: corrected GA4 collection endpoint allowlists in Production CSP (no `unsafe-eval` and no ad tagging).
- PR #8 — frontend `d9a1a53a6171f3d417637d12cec66eed1832a07b`: repaired gtag.js queue compatibility by pushing JavaScript `arguments`, not spread Arrays, into `dataLayer`; shipped through tested PR with a narrowly justified lint exception.

- Historical GA4 PR #8 Production checkpoint (superseded by UI PR #9 above): `d9a1a53a6171f3d417637d12cec66eed1832a07b`; Vercel deployment `dpl_EnejDGuCcotpf4kQrSQk7pnPsyRw` = **READY** (https://vercel.com/mohcenp-9857s-projects/directpilot-web/EnejDGuCcotpf4kQrSQk7pnPsyRw). This supersedes the earlier SEO PR #5 release `e527c8f7e47a3259457f4efd72ded588eb3e26b9` / `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2`; those older SHAs remain valid **historical** checkpoints only.
- GA4 Web Stream: `https://directpilot.ir`, `DirectPilot - Production Web`, Measurement ID `G-9D1Z7HDYVZ`, GA4 Property ID `558426868`, GA4 reporting timezone `Asia/Dubai`. Vercel `NEXT_PUBLIC_GA_ID` is set for **Production only**; a fresh Production build is READY.
- Browser verification on 2026-10-11 **after PR #8**: granted consent; gtag.js loaded; `dataLayer` contains `page_view`; request to `https://region1.google-analytics.com/g/collect` returned HTTP **204** with `en=page_view`. GA4 Realtime showed **one active user**, and `first_visit`, `session_start`, `page_view` each observed once. This establishes end-to-end **page-view event delivery and Realtime ingestion**, not all-event/real-signup acceptance.
- In GA4, `sign_up` is defined as a **Key Event** (code-based, no default monetary value, once per event). **The actual `sign_up` delivery after a successful backend registration has NOT been tested**; do not mark conversion E2E PASS or equate `signup_intent` with completed registration.
- GA4 is natively linked to Search Console Domain Property `directpilot.ir`, and GSC Wizard's GA4 connection is separately verified: `sc-domain:directpilot.ir` ↔ `properties/558426868` under `DirectPilot - Production`. GA4 reports and blended GSC+GA4 sections are visible.
- GSC Wizard reports through 2026-10-10 initially showed GA4 zeros because collection was first accepted on 2026-10-11. Respect settled-data lag (~1-3 days), the GA4 launch boundary, site/session definitions, user consent and small samples; **do not** read historical zero as malfunction or claim ranking/conversion uplift. Google Search Console clicks and GA4 sessions are not interchangeable.

- Existing weekly automation **«پایش هفتگی SEO و GA4 DirectPilot»** updated (ID `6acb649a476c8191895050914165ee85`), **enabled**, next intended run Monday 2026-10-12 at approximately 09:00 **Asia/Dubai**, `flexible_schedule`. It now checks settled 28-day SEO windows, 10 indexed URLs, queries/landing pages/cannibalization/sitemap, and GA4 sessions, landing pages, engagement, `signup_intent`, `sign_up` / Key Events, with post-activation/date-alignment safeguards. This is an automation-instructions update; it does not change site code or GA4 settings.
- This scheduled task's automation record currently reports `notifications_enabled=false` and `email_enabled=false`; delivery/notification permissions should be reviewed by the owner separately if push or email alerts are expected. Do not falsely claim notification delivery is enabled.

Mobile **Lighthouse lab** checkpoint (run 2026-10-11, preceding current GA4 ingest validation): `/` Performance **74**, SEO **100**, LCP **2.74s**, CLS **0.000**, TBT **974ms**; `/instagram-direct-automation` Performance **97**, SEO **100**, LCP **2.41s**, CLS **0.007**, TBT **64ms**. These are throttled lab measurements, not real-user INP/CrUX; the homepage's long main-thread blocking is an optimization candidate, not an SEO ranking claim.

**Remaining SEO/measurement gates:** allow settled GA4 data after 2026-10-11, then verify Sessions / Page Views / Organic Search and event counts; run a controlled **successful** test registration and confirm `sign_up` in GA4 before declaring conversion PASS; compare GSC impressions/clicks/CTR/position on aligned post-recrawl windows; inspect the previously observed mobile homepage Lighthouse bottleneck (lab Performance 74, LCP ~2.74s, TBT ~974ms) separately from CrUX field vitals. Maintain the privacy consent gate, no personal data in analytics, no `unsafe-eval`, Production-only tagging, and unchanged backend/payment/Meta readiness gates.

## 5E. Earlier SEO Incremental Releases / 2026-10-11

- PR #1 `a0d663a59421de0f96789dc2dcd5e51d981430f8`: auto-comment article content, `dateModified` / Open Graph / sitemap last-modified support.
- PR #2 `cbb7f74b9f21e9e61f78eaad11c89b9510631ad1`: blog hub guidance, FAQ and contextual navigation.
- PR #3 `3afdd4af2d75ab15abc975ba699c6f7b8fa4575a`: corrected shared trust copy from an inaccurate permanent-free-plan claim to the 14-day trial.
- PR #4 `d3227c949bd051713b6abede9c44499d898e187e`: expanded `/about` with genuine product approach, human handoff, trial transparency, security and links.
- PR #5 `e527c8f7e47a3259457f4efd72ded588eb3e26b9`: added commercial-intent guidance, FAQ and contextual links to `/instagram-direct-automation`, fixed bold-wrapped Markdown links in `/blog/instagram-smart-direct`, and added a clear article-to-service/demo CTA.

Verified Production deployment: frontend `main` SHA `e527c8f7e47a3259457f4efd72ded588eb3e26b9`, Vercel `dpl_Btry5s2bBzHpW6n618fNB9ZihWn2` = READY. A live GSC Wizard on-page crawl on 2026-10-11 returned HTTP 200 / indexable / self-canonical / 0 issues for six pages: `/`, `/blog`, `/blog/instagram-auto-comment-reply`, `/about`, `/instagram-direct-automation`, `/blog/instagram-smart-direct`. Word/link changes: `/blog` 244->426 words, 39->44 internal links; `/about` 139->464 words, 30->36 links; service page 437->680 words, 39->40 links; smart-direct article 30->39 internal links. This proves live publishing and a clean technical audit, **not** a Google recrawl, new indexing event, or ranking/traffic uplift.

Pre-change Search Console context (2026-09-11 to 2026-10-08; not a post-change performance comparison): `/blog/instagram-smart-direct` 88 impressions / 2 clicks; `/instagram-direct-automation` 12 impressions / 1 click; `/instagram-comment-automation` 22 impressions / 1 click. Educational intent belongs with the blog article, commercial/product intent with the direct-automation landing page; pricing intent with `/pricing`.

Next SEO gate: let Google recrawl the changed URLs and accumulate a meaningful settled Search Console window; compare page+query impressions, clicks, CTR and average position against a date-aligned baseline. Check article -> service internal-link visibility and keep service/blog keyword ownership separate. Do not claim rank growth or repeat copy rewrites based only on immediate deployment data. Preserve Production-only indexing and UAT/Preview noindex.

SEO release PR and Vercel evidence lives in the frontend repository `namach2727-coder/directpilot-web`; this roadmap is a documentation checkpoint in `Sales-Agent`. Backend product/payment rollout gates have not been closed by SEO publishing.

## 5D. Admin Customer Automation Management

Frontend SHA: `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.

Status: **DEPLOYED TO UAT AND PRODUCTION / OWNER FUNCTIONAL ACCEPTANCE PENDING**.

Changes:
- Admin -> Customers & Stores now exposes **Manage Automation** only for stores with the `instagram_automation` capability.
- The selected customer/store opens the existing Automation Rule Builder with phrase/keyword, match type, response text, priority and enabled state.
- The frontend reuses the existing tenant/store-scoped AutomationRule API.
- Platform Super Admin access is authorized through the existing backend platform permission path; no impersonation or tenant-isolation bypass was added.
- Backend capability and automation-limit checks remain authoritative.
- UAT Vercel: SUCCESS.
- Production Vercel: SUCCESS.
- Owner live functional acceptance: PENDING.

This UI is the preferred path for creating the Production pilot deterministic rule when testing from the Platform Admin account.

## 5C. Meta UAT-to-Production Relay Bridge

Accepted backend runtime SHA: `91250140cccc7c9be9102c2d6e17e6775a836f24`.

Status: **OAUTH PASS / INBOUND PASS / OUTBOUND E2E OPEN**.

Evidence:
- GitHub CI: test PASS, docker-build PASS, postgres-smoke PASS,
- UAT Render deploy `dep-db33f1qd0e5s73f0bk00`: LIVE; APP_ENV/DB/migration/startup PASS,
- Production Render deploy `dep-db33funavr4c739lm9v0`: LIVE; APP_ENV/DB/migration/startup PASS,
- Production OAuth through the UAT callback relay: PASS,
- UAT webhook relay to Production: PASS,
- Production inbound routing/account resolution/persistence/processing: PASS.

Observed live behavior:
- inbound `قیمت` reached Production,
- no deterministic AutomationRule matched,
- AI fallback failed with `llm_provider_configuration_error`,
- Production send remained disabled, so no provider send occurred.

Outbound safety release:
- `META_SEND_ENABLED=false` remains the current Production state,
- when Production send is enabled, runtime validation now requires exactly one entry in `META_SEND_ALLOWED_ACCOUNT_IDS`,
- zero or multiple allowed accounts fail Production environment validation,
- the sender still enforces sender-account membership in the allowlist.

Next gate:
- deterministic `DM_KEYWORD` + `EXACT` rule for `قیمت`,
- exactly one connected Production pilot account in the allowlist,
- one controlled outbound E2E,
- verify one provider delivery, dedupe and no own-message echo loop.

## 5B. SEO Phase 2 Release

Production/UAT SEO Phase 2 accepted SHA: `4a1f8bb1812ce942e055c7f2c810f7d719939ab8` (later frontend UX fixes are deployed at `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`).

Status: Production PASS.

Changes:
- completed Article/Organization schema image and logo fields,
- shortened long commercial search-result titles,
- expanded `/pricing` and `/comment-to-direct` to remove thin-content warnings,
- preserved canonical/indexability and Preview/UAT noindex controls.

Live Production audit after deployment:
- 5 priority pages audited,
- HTTP 200 on all,
- indexable 5/5,
- critical 0,
- high 0,
- medium 0,
- low 0,
- schema issues 0.

Ranking impact remains OPEN until Google recrawls the changed pages and a later settled Search Console window is available.

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

Status: IN PROGRESS — RELAY BRIDGE DEPLOYED / PRODUCTION OAUTH NEXT.

- Owner approved the UAT -> Production relay workaround because Meta Developer settings are currently inaccessible.
- Shared Meta App credentials remain valid for the pilot.
- Meta continues to know the existing UAT OAuth callback.
- Production now deliberately sends that same provider redirect URI while prefixing its OAuth state with `production.`.
- UAT relays only `production.` callback state to the Production callback; UAT does not consume that state.
- Production consumes its own state and stores its own encrypted Instagram token/connection.
- Webhook relay code is deployed to UAT but remains disabled until Production OAuth succeeds.
- Production outbound remains fail-closed with `META_SEND_ENABLED=false`.
- CI for relay runtime `b8f945d...`: 871 passed / 7 skipped; docker-build PASS; postgres-smoke PASS.
- Production deploy `dep-db31vu60tbcc738ee1dg`: LIVE.
- UAT deploy `dep-db31uljncjis73e6gq90`: LIVE.
- Never copy UAT encrypted tokens/database rows or the UAT encryption key into Production.

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
- Remote `main` is authoritative at `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`.

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

### Meta — Active

```text
META_UAT_TO_PRODUCTION_RELAY_ACTIVATION
```

Next gate is Production OAuth from the Production dashboard. Webhook relay remains disabled until that succeeds.

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

## 13A. Future Telegram Bot Builder

Status: **IDEA PARKED / NOT IN CURRENT EXECUTION SCOPE**

Concept:
- No-code AI Telegram Bot Builder / bot-builder SaaS.
- Prefer Telegram Managed Bots capability where suitable.
- One manager/builder experience can provision and manage tenant bots.
- Multi-tenant shared runtime; do not deploy a separate application per customer.
- Candidate modules: deterministic rules, AI assistant, menus, lead capture, human handoff, knowledge, analytics, later commerce/payment/CRM.
- Keep this as a future product track only. Do not divert DirectPilot readiness work until current Production gates are closed.

## 14. Resume Instructions

On a new session:

1. Read all five continuity files in canonical order.
2. Verify remote branch heads and deployed runtime SHAs before mutation.
3. Verify Render Production/UAT runtime state.
4. Verify Vercel branch/deployment state when relevant.
5. Preserve local dirty work.
6. Resume from `Exact Next Work Queue`.
7. If runtime evidence conflicts with docs, runtime wins and docs must be corrected.

## 9A. Meta Production Activation

Status: IN PROGRESS.

- Owner explicitly resumed Meta work on 2026-10-07.
- UAT live evidence shows inbound webhook events accepted and outbound delivery completed on 2026-10-07.
- Shared Meta App pilot decision remains valid.
- Production non-secret Meta settings were normalized with Production OAuth callback, official provider endpoints, signature verification enabled, content publishing disabled, and outbound sending fail-closed.
- The env update triggered Production deployment `dep-db317cm0tbcc738c4qlg`; it is LIVE.
- Production deployment checked out Git SHA `fa8316e71ec1ce7c32c4806f428c5bde0e26db16`; compare against accepted runtime code `84b7df6...` contains only continuity Markdown files.
- Render connector cannot safely read secret env values, so shared app credentials must be confirmed/copied in the Render dashboard without pasting them into chat.
- Production OAuth must create its own encrypted connection/token rows in the Production database. Do not copy UAT encrypted token rows across environments.
- Keep `META_SEND_ENABLED=false` until Production OAuth, webhook routing and restricted account allowlist are verified.

## Meta OAuth Relay Runtime

- OAuth relay deployment is live in both environments at `b6962c6701897ece4ee4fdda5ffcf7f2ec67da3a`.
- UAT deploy: `dep-db32aebncjis73e7irl0` — LIVE.
- Production deploy: `dep-db32beom7kps73cpcf50` — LIVE.
- Production OAuth redirect intentionally uses the existing UAT callback registered with Meta.
- Production OAuth state prefix: `prod.`.
- UAT callback relays only matching `prod.` states to the Production callback.
- Webhook relay remains disabled until Production OAuth connection is accepted.
- Production sending remains disabled until restricted-account E2E.

## Meta Production OAuth Acceptance

- Production OAuth accepted on 2026-10-07 through the UAT relay bridge.
- UAT callback relay evidence: `instagram.oauth.relayed`.
- Production provider evidence: short-token exchange 200, requested permissions complete, BUSINESS profile probes PASS, long-lived-token exchange 200, profile lookup 200.
- UAT webhook relay is now enabled to the Production webhook endpoint.
- UAT webhook-relay deploy: `dep-db32pmvavr4c739je950` — LIVE.
- Production sending remains disabled pending inbound-routing acceptance and allowlist verification.

## Meta Production Inbound Acceptance

- Production inbound relay accepted on 2026-10-07.
- Evidence: UAT `instagram.webhook.relay_succeeded`; Production `instagram.inbound.received`, account resolution, conversation creation, message persistence, webhook accepted and processing completed.
- Test message `قیمت` reached Production but no deterministic AutomationRule matched; AI fallback attempted and failed with `llm_provider_configuration_error`.
- Production send remained disabled, so no outbound provider call was made.
- Next gate: deterministic Production rule + restricted non-empty send allowlist + one controlled outbound E2E.


## Controlled Production Outbound Gate — 2026-10-11
Status: **CONTROLLED PILOT E2E PASS**
- Deterministic pilot rule: owner confirmed.
- Single-account Production restriction: configured.
- Restricted Production send: enabled only for the controlled test; returned to disabled afterward.
- Deployment `dep-db5ihrg473hc73ba3be0`: LIVE.
- Environment, DB, migration and startup checks: PASS.
- Controlled retest passed: deterministic response, one provider delivery, no AI fallback, and no self-echo loop.


## Controlled Outbound Attempt 1 — Inconclusive
- First pilot message coincided with UAT relay redeployment.
- No inbound webhook reached UAT or Production, so there is no automation/outbound verdict.
- Relay is healthy again; repeat one controlled message after relay readiness.


## Meta Production Controlled E2E — PASS (2026-10-11)

Acceptance evidence:
- UAT webhook relay delivered the clean retest to Production.
- Production inbound routing/persistence: PASS.
- Deterministic rule evaluation: PASS.
- Exactly one `instagram_outbound_started`: PASS.
- Exactly one `instagram_outbound_delivered`: PASS.
- No `instagram_outbound_failed`: PASS.
- No AI start/failure for the deterministic flow: PASS.
- Provider/self follow-up event was ignored; no second outbound was started: PASS.
- Post-test rollback: `META_SEND_ENABLED=false`.
- Rollback deployment `dep-db5illid0e5s73fju470`: LIVE.

Meta transport is no longer the current Production-readiness blocker. Production database durability and backup/restore remain the highest-priority blocker before real customers; LLM verification remains a separate open gate.


## Meta Production Controlled E2E — PASS (2026-10-11)
- UAT relay -> Production inbound: PASS.
- Deterministic rule handling: PASS.
- Exactly one outbound delivery: PASS.
- AI fallback not invoked: PASS.
- No duplicate second send observed: PASS.
- Follow-up/self event was ignored; no loop observed: PASS.
- Production send returned to disabled after acceptance.
- Post-test deployment `dep-db5illid0e5s73fju470`: LIVE.
- Current highest-priority readiness blocker: Production database durability and backup/restore before real customers.


## Production DB Durability Assessment — 2026-10-11
- Current Production Postgres is Free, expires 2026-11-02, has no managed backups/PITR, no HA, no replicas, and an empty external IP allowlist.
- Seven-day metrics show very low Pilot load: CPU ~0.007 cores, memory roughly 40-60 MB, active connections peak 6.
- Recommended minimum paid target: Render Postgres `0.1c-256mb` with current storage kept minimal.
- Expected base compute cost: about $6/month; 1 GB storage included, additional Postgres storage is billed separately.
- Paid Render Postgres enables PITR; on a Hobby workspace the recovery window is 3 days. On-demand logical exports are available for paid instances and retained for 7 days.
- Compute-plan change requires brief database downtime.
- Paid infrastructure change remains blocked until explicit owner approval.


## Production DB Upgrade Decision — 2026-10-11
- Owner explicitly deferred the paid Production Postgres upgrade for now.
- Do not change the current Free Production database plan or incur paid infrastructure cost without a new explicit approval.
- Current risk remains accepted temporarily: Free Production Postgres expires 2026-11-02 and does not satisfy durability/backup-restore acceptance.
- Real-customer onboarding remains blocked by Production database durability until this decision is revisited.


## Production LLM Configuration Verification — DIAGNOSIS PASS / READINESS BLOCKED

Runtime evidence (2026-10-11):
- Safe observability SHA: `398d6dc52e436f4db25f21b19e7dbca4bef10f3c`.
- CI: test PASS, docker-build PASS, postgres-smoke PASS.
- UAT: Groq selected; configured credential and model present; deployment `dep-db5j4ebbc2fs73934e7g` LIVE.
- Production: OpenAI selected with `gpt-5.6-sol`, but selected-provider credential is absent; Groq credential/model are also absent; deployment `dep-db5j5c7lk1mc73a6ofkg` LIVE.
- Production backend health remains PASS; only AI provider execution is blocked.
- No provider secret was logged or copied across environments.

Next:
1. Provision a Production-specific LLM credential securely in Render.
2. Select and configure a currently supported Production model.
3. Preserve `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256` if Groq is selected.
4. Run one controlled AI fallback E2E.


## Groq Model Support Check — 2026-10-11
- UAT currently selects `qwen/qwen3.6-27b`.
- Official Groq deprecation guidance says `qwen/qwen3.6-27b` was deprecated for Free/Developer usage on 2026-09-14.
- Direct replacement: `qwen/qwen3.8-27b`.
- Do not copy the deprecated UAT model into Production.
- If Production Groq is approved, target `qwen/qwen3.8-27b` with existing guardrails `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, and `GROQ_REASONING_EFFORT=none`.
- Production still requires its own securely provisioned `GROQ_API_KEY`; never copy or expose the UAT credential.


## Production Groq Configuration Activated — 2026-10-11
- Production LLM provider is now `groq`.
- Production model is `qwen/qwen3.8-27b`.
- Groq credential presence: verified true through sanitized startup metadata; secret value was never logged or copied.
- Guardrails: `GROQ_CONTEXT_LENGTH=4096`, `GROQ_MAX_OUTPUT_TOKENS=256`, `GROQ_REASONING_EFFORT=none`.
- Production environment, DB connectivity, migration head and application startup: PASS.
- LLM configuration deployment `dep-db5jh9lckfvc73aekfbg`: LIVE.
- Restricted Meta-send test deployment `dep-db5ji6ss728c73823a50`: LIVE.
- Meta send is enabled only under the existing single-pilot account allowlist for one controlled AI fallback E2E.
- Next: send one deliberately unmatched pilot message and verify Groq request completion, assistant persistence, exactly one outbound delivery, quota accounting, dedupe and no echo loop.


## Production AI Fallback E2E — PASS (2026-10-11)

Acceptance:
- UAT relay -> Production: PASS.
- Unmatched message -> AI fallback: PASS.
- Groq `qwen/qwen3.8-27b`: PASS.
- Provider request completed in 226 ms with 488 total tokens.
- Assistant persistence: PASS.
- Exactly one Meta outbound delivery: PASS.
- AI/outbound failures: NONE.
- Duplicate/echo second send: NOT OBSERVED.
- Quota enforcement path executed before provider call; token metadata was persisted for server-authoritative usage aggregation. Exact aggregate usage count was not directly queried because Production DB networking remains closed.
- Meta send returned to disabled after the test.
- Rollback deployment `dep-db5jm4nlk1mc73a8du40`: LIVE.

Production LLM is no longer an open blocker.


## Payexa Environment Split Verification — 2026-10-11

- Safe Payexa runtime observability SHA: `b7c510912a6b5bb13c736192e390bce44a3dcb61`.
- CI for the observability change: test PASS / docker-build PASS / postgres-smoke PASS.
- Initial UAT runtime was incorrectly configured against Production Payexa: base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, credential present. This environment-split finding was FAIL and was corrected immediately.
- UAT is now isolated to Payexa Sandbox: base `https://sandbox.pexn.ir`, callback base `https://uat.directpilot.ir`, sandbox credential configured. Deployment `dep-db5k0pcs728c7383hnh0`: LIVE. UAT Payexa environment split: PASS.
- Initial Production Payexa state was fail-closed: sandbox/default base, empty callback, no credential.
- Production non-secret Payexa configuration is now base `https://pay.pexn.ir`, callback base `https://directpilot.ir`, timeout 15s, while Production credential remains absent. Deployment `dep-db5k2e142hec7398l0h0`: LIVE.
- Production Payexa environment structure is therefore correct but provider execution remains intentionally BLOCKED until a Production-specific `PAYEXA_API_KEY` is provisioned securely.
- Current frontend checkout intentionally does not invoke Payexa; manual card transfer remains the primary checkout path. Payexa source/routes and result page remain present.
- Real-provider acceptance is NOT PASS. It requires Production credential provisioning, Payexa-side verification/approval of the DirectPilot callback site/domain as applicable, and a controlled transaction path.
- Never copy UAT credentials into Production, expose provider secrets in chat/logs, or blindly retry ambiguous create operations.

- Next payment gate: securely provision the Production Payexa credential, verify the callback site/domain in the Payexa panel, then enable a controlled checkout/test path before any real-provider acceptance claim.


## Authoritative Payment Flow Correction — 2026-10-11

- Current DirectPilot payment architecture is **manual card transfer with admin approval**, not Payexa.
- Customer selects a paid plan and receives the configured payment-card details from DirectPilot.
- Customer transfers the exact amount using any banking method outside DirectPilot.
- Customer uploads a JPEG/PNG/PDF receipt from the customer panel.
- Backend validates the receipt and persists the receipt bytes plus metadata in PostgreSQL (`receipt_data`, content type, size, SHA-256), then changes payment status to `submitted` and order status to `payment_submitted`.
- Platform Admin reviews submitted payments in Admin -> Payments, can securely view the receipt, and chooses Approve or Reject.
- Approve is backend-authoritative: it row-locks/checks optimistic revision, marks payment `approved`, marks order `paid`, creates/activates the subscription, applies plan/module entitlements and writes an audit record atomically.
- Reject returns the order to `pending` and records the rejection reason without deleting the payment.
- UAT frontend currently contains this complete customer + admin flow and its Vercel deployment is SUCCESS at frontend UAT SHA `4acd10aaa2a78ab52ba8b3e9f1f1cc84ac48d159`.
- Backend manual flow is present and deployed from `backend-main`; current CI remains PASS.
- Payexa/KPay routes are preserved only as non-primary/deferred integration code. They are **not** part of the current customer checkout path and are **not** a Production-readiness gate for the current payment process.
- Do not request or provision Payexa credentials unless the owner explicitly decides to re-open automated payment-gateway work.
- Current payment readiness should be evaluated against manual-card-transfer E2E and admin approval, not Payexa acceptance.

- Current payment gate: verify/promote the manual card-transfer flow in Production, including configured payment card, customer receipt upload, Admin receipt review, approval/rejection and subscription activation.
- Automated Payexa acceptance is deferred/out of current scope.


## Production Manual Payment E2E Readiness — 2026-10-11

- Authoritative payment path remains manual card transfer + customer receipt upload + Admin approval.
- Frontend Production `main` is one commit ahead of UAT but has no payment/checkout/admin-payment differences from UAT. Production Vercel status is SUCCESS.
- Safe manual-payment readiness probe SHA: `c05669d3448ea3f6f151bb73a22db5dcfffcf7b7`.
- CI: test PASS / docker-build PASS / postgres-smoke PASS.
- UAT deployment `dep-db5kjhnlot8c73f9ueb0`: LIVE; runtime readiness `active_cards=1 active_default_cards=1` => PASS.
- Production deployment `dep-db5kkhid0e5s73fq7h90`: LIVE; runtime readiness `active_cards=0 active_default_cards=0` => BLOCKED.
- Production cannot create a manual payment until an Admin configures at least one active default payment card.
- No card number/account data was logged or copied from UAT. Do not fabricate, infer, or transfer banking details across environments.
- Once a real Production destination card is configured by an authorized Admin, run controlled E2E: paid-plan order -> show card -> upload test receipt -> Admin reviews receipt -> Admin approves -> verify payment approved, order paid, subscription active and module entitlements applied.

- Immediate payment blocker: Production payment-card configuration only. Code/deployment path is otherwise ready.


## Production Payment Card Form Reset Incident — FIXED (2026-10-11)

- User hit frontend error while creating the first Production payment card: `Cannot read properties of null (reading 'reset')`.
- Root cause was frontend-only: `createCard()` called `event.currentTarget.reset()` after an awaited API request. The React form event's `currentTarget` was no longer reliable at that point.
- Fix: capture the HTML form element before the async boundary, build `FormData` from that stable reference, and call `formElement.reset()` after the successful request.
- A regression test now requires the stable form reference and forbids async use of `event.currentTarget.reset()`.
- UAT fix SHA `910bd2b0add605ab926e08ab18be444431c0a134`: Vercel SUCCESS.
- Production runtime fix SHA `2f0ba54287e04ad8d7f5d747d2adcefdfd25bbbf`: Vercel SUCCESS.
- Production test-only follow-up SHA `a8e90d3aa1112dd2e577ee82c452ecb421668618` adds the regression test; runtime behavior is unchanged from the successful runtime-fix commit.
- Because the failing `reset()` statement executes only after `await adminPaymentsApi.createCard(...)` resolves, the backend card-create request had already succeeded before this UI exception. Do not ask the user to re-enter the same card blindly; first refresh/reload the Admin Payments view and confirm the created card is present.
- Production DB remains externally closed; no banking details were queried, logged or exposed.

- Payment E2E next step: reload Production Admin Payments, confirm the card is present/active/default, then continue customer order -> card display -> receipt upload -> Admin approval -> subscription activation.


## Payment Card Display Readability Fix — 2026-10-11

- Admin payment-card rows previously rendered bank name, account holder and card number as adjacent inline text, producing unreadable output such as `بانکنام صاحب حساب5859...`.
- Frontend now renders bank/label, account holder and card number on separate lines.
- Card numbers are formatted visually in four-digit groups and rendered LTR for readability; stored card data is unchanged.
- UAT frontend SHA `61ef804dba0c03e14eb6e26308a05e63e2ed2ae2`: Vercel SUCCESS.
- Production frontend SHA `b5b7d1e5fbeef6622dcbe8c105caeb17b41df0fb`: Vercel SUCCESS.
- Regression coverage added for separated metadata layout and grouped card-number rendering.


## Customer Card Copy Action — 2026-10-11

- Customer manual-payment page now exposes a dedicated **Copy card number** action beside the destination card.
- Copy behavior first uses the modern Clipboard API and falls back to a temporary readonly textarea + `execCommand("copy")` for broader mobile-browser compatibility.
- The copied value is normalized to digits/no spaces before being written to the clipboard.
- Successful copy changes the button label to `کپی شد ✓` and shows the status message `شماره کارت در کلیپ‌بورد کپی شد.`.
- Mobile layout makes the copy button full-width below the card row for easier tapping.
- UAT frontend SHA `1e33cda4e572d1eac44608e1b57a6674a99ca18f`: Vercel SUCCESS.
- Production frontend SHA `cc924aa651069682e903ae236fd061e002288bbb`: Vercel SUCCESS.
- Regression coverage added for Clipboard API, mobile fallback, normalized card value, button feedback and mobile layout.


## Production Manual Payment Card Readiness — PASS (2026-10-11)

- Production backend deployment `dep-db5m7m7lot8c73fesnug`: LIVE.
- Safe startup readiness reports `active_cards=1 active_default_cards=1`.
- Production manual-payment destination card configuration is therefore READY.
- Customer manual-payment flow can now proceed to controlled E2E: paid plan order -> display destination card -> test card-copy action -> upload test receipt -> Admin review -> Approve -> verify payment approved, order paid, subscription active and entitlements updated.


## Customer Billing Discoverability Fix — 2026-10-11

- Verified the customer billing flow exists in Production source and is rendered by AuthenticatedShell on both desktop and mobile as `اشتراک و پرداخت`.
- Root UX gap: the customer Overview page had no direct CTA into billing, making the payment flow easy to miss even though the section and routes existed.
- Added a prominent primary action `مشاهده پلن‌ها و پرداخت` to the customer Overview quick-actions card, linking directly to `/dashboard?section=billing`.
- UAT frontend SHA `eccb29022e81141bd90b9abf77c019f018889d8c`: Vercel SUCCESS.
- Production frontend SHA `cd9d3e5f10a97fd2edc9b6fb2d8ee34e87575030`: Vercel SUCCESS.
- Existing billing logic, order creation, checkout, manual card-transfer payment and receipt upload routes were unchanged.

## Latest Commercial Resume Marker — Production Manual Payment E2E PASS (2026-10-11)

CURRENT_TASK: `CONTROLLED_PRODUCTION_MANUAL_PAYMENT_E2E` -> **PASS / CLOSED**

Acceptance completed:
- Production Trial/Billing purchase visibility: PASS.
- `AUTOMATION_V1` selection: PASS.
- Destination payment-card display: PASS.
- Customer card-number copy/use: PASS.
- Receipt upload: PASS.
- Backend/Admin approval path: PASS.
- Payment state: `approved`.
- Order state: `paid`.
- Subscription state: `active`, source `PURCHASED`.
- Entitlements: automation limit 20, Instagram account limit 1, duration 30 days.
- Owner visually confirmed the approved Production payment in the UI.

Runtime/deployment evidence:
- Production frontend final commit: `2e9122f2632972c118e98ad16a43d1c957ec446d`, Vercel READY on `directpilot.ir`.
- Guarded Production approval runtime commit: `421d157fc85549ae238c72f553d68ac8e3bd85ae`.
- Cleanup deployment after disabling the one-shot: `dep-db5p0nng0jfs73bign50` LIVE.
- Manual payment readiness remains `active_cards=1 active_default_cards=1`.

NEXT:
1. Do not reopen manual-payment readiness unless a regression is reported.
2. Keep Payexa/KPay deferred unless explicitly reopened by the owner.
3. Continue with the next unresolved Production-readiness item; DB durability remains owner-deferred and should not incur paid changes without explicit approval.


## 2026-10-12 — Shared-Meta UAT webhook validation plan
- Gate A: offline signed/event ingestion regression with disposable database; no calls to Meta or Production (code prepared, CI pending).
- Gate B: read-only inspect Render UAT webhook logs and isolated Neon counts; do not assume zero rows means failure while UAT relays to Production.
- Gate C: any live UAT webhook ingestion test requires a separately approved safe routing architecture; no changes to shared Meta app or operational relay until that plan is validated.

## 2026-10-12 — Multi-month manual subscription purchase
- Delivery: backend order pricing/duration snapshots for 1–12 prepaid months (PR #8) and frontend UAT month selector, total preview and manual receipt path (PR #15).
- Deployment order: Backend CI PASS → merge/backend UAT-only deploy → verify API → frontend PR #15 merge into UAT → visual payment/receipt tests. Do not deploy Production; both Render services track backend-main with auto deploy disabled.
- Remaining UAT acceptance: 3-month Automation order must yield IRR 14,700,000 and 90 days; receipt approval must create correct subscription. Existing payment card default exists in isolated Neon.

### Release evidence — 2026-10-12
- Backend automated CI #355 PASS; merged #8 `b1a63ea9`; Render UAT deploy `dep-db6becvlk1mc73cksvi0` LIVE.
- Frontend multi-month PR #15 merged UAT `34b19e6e`; Vercel Success; account/browser acceptance for 3× Automation and manual receipt still required.
- Dashboard/billing clarity reconciliation PR #16 pending Preview; no Production deploy. Next: manual UAT test and expiry check.

- Final UAT interface release: PR #16 merged at `8f083473` with Vercel Success; both month selection and dashboard/payment guidance retained. Browser three-month purchase/receipt E2E remains unverified; Production not deployed.


### UAT receipt preview update
- 2026-10-12 UAT payment admin UX: Inline preview for secured JPG/PNG/PDF receipts in payment review panel; approve/reject remains an explicit admin action. Backend #10 merged and UAT LIVE, Frontend #17 merged into UAT; verify Vercel Success and real admin view. No Meta or Production changes.


### 2026-10-12 UAT compact payment UI
- 2026-10-12 UAT UI: compact payment review + receipt-sized in-page preview + active plan/upgrade-only CTA implemented in frontend PR #18; merged to UAT `1cae8c08`. Validate mobile/desktop receipt JPG/PNG/PDF, after-approval plan visibility and upgrade label before any Production promotion.


### Production promotion preflight (2026-10-12)
- 2026-10-12 Production release gates: 1) Resolve frontend draft PR #19 conflicts preserving production-only GA4/CSP/SEO config; 2) review current Production DB schema and backup/rollback, ensure only additive approved migrations + catalog entries; 3) run CI and staging compatibility; 4) deploy backend Production with monitoring and rollback, then frontend Production; 5) validate signup/login, Instagram shared relay, manual payments, multi-month calculations, receipts and active-plan upgrade UI. Until then status BLOCKED, nothing deployed.


## 2026-10-12 — Production commerce rollout evidence (supersedes older UAT-only markers)
- Backend Production `043d37ff` LIVE on Render deploy `dep-db6fr2bl550s73esrnh0`; startup/DB/migration PASS; no new Alembic files across rollout. Multi-month server order pricing and receipt-inline policy are available in Production backend.
- Frontend selectively reconciled PR #20 merged to `main` SHA `06ebe316` preserving GA4/SEO/CSP; CI #38271830924 210 tests/type-check/lint/build PASS. Vercel PROD alias/READY UNVERIFIED due connector project access and missing GitHub Vercel status.
- Production catalog seeding of paid `AI_ASSISTANT_V1` and read-only plan comparison still OPEN; do not bulk-transfer isolated UAT Neon data. Restore verification remains OPEN; owner has deferred paid DB upgrade.
- Gate to close: Vercel inspect actual `directpilot.ir` deployment, browser customer/admin smoke, audit Production paid-plan catalog and safely add missing AI plan only after protected DB review.


## Production promotion — 2026-10-12 release checkpoint
- DONE: Backend production `043d37ff`, Render `dep-db6fr2bl550s73esrnh0` LIVE; DB/migration/startup PASS. Frontend production `main` PR #20 merged (`06ebe316`), 210 UI tests + type-check + lint + build PASS; GA4/SEO and receipt/admin/customer UX selectively reconciled.
- OPEN: Vercel Production deployed SHA evidence unavailable because connector cannot access linked deployment. Owner or newly authorized Vercel connection must verify `directpilot.ir` latest READY deployment points to the production merge SHA before considering frontend fully released.
- OPEN: Paid AI Assistant catalog activation in Production. UAT row independently verified in Neon. Backend PR #15 adds only missing row with idempotent Alembic 0024; tests and UAT/Production release pending. Never import UAT orders/customers/cards or tokens into Production.
- GATES: Production Free Postgres no accepted backup/restore; no new customer onboarding; manual card payment and shared Meta unchanged. Controlled independent-product and three-month price/expiry tests after release, without unapproved transfers.


## 2026-10-12 Production catalog release evidence
- PASS: UAT `dep-db6gbobbc2fs73c1r860` LIVE; migration 0024 safe no-op on existing AI row and Neon readback unchanged.
- PASS: Production Backend `dep-db6gco59fdbs7382opb0` LIVE and Alembic 0024 applied, current-head/startup PASS; active/default manual payment card count=1.
- PASS: GitHub Actions `38275924090` read-only public Production plan catalog acceptance. Automation IRR 4,900,000/30d/20 rules and AI IRR 6,900,000/30d/1,000 AI requests/replies.
- PENDING: Vercel Production frontend deployment matching merged `main` SHA `06ebe316`; authenticated admin/customer UI smoke and non-payment three-month 90d quote check. Do not infer Ready from GitHub merge alone.
- Production Free Postgres durability and backup/restore gate still OPEN; no Meta, payment provider or infrastructure-plan changes.


### Mobile login overlay hotfix — 2026-10-12
- 2026-10-12 Mobile Login: UAT PR #21 and Production selective PR #22 both merged; respective GitHub quality checks PASS. Fix persistent mobile navigation overlay, safe-area and keyboard focus; no backend modifications. Gate still OPEN: verify Vercel Production READY deployment SHA 69632c8a and manually test login navigation on mobile Safari/Chrome.


### Customer Dashboard UAT UX (2026-10-12)
- 2026-10-12 UAT customer dashboard UX PR #23 merged SHA `00d29a89`, CI run `38281718727` PASS. Improve navigation hierarchy, checkout safety on failed reads, mobile responsive shortcuts, and remove the customer-visible online conversation screen entirely while preserving historical data/APIs. Next gates: visually review `uat.directpilot.ir/dashboard` (mobile/desktop), confirm removed Inbox nav and `?section=inbox` fallback, validate paid/trial/unpaid/disconnected scenarios and check that UAT Vercel deployed SHA is Ready; only then promote selectively to Production with GA4/SEO/CSP retained.


### Customer Inbox follow-up — 2026-10-12
- 2026-10-12 UAT customer Inbox follow-up: PR #24 merged `16e2547d`, CI PASS, removed actual 10k-character customer InboxPanel renderer that PR #23 had left in code. Vercel branch UAT READY SHA and mobile/desktop visual confirmation are outstanding gates. No Production promotion until confirmed.


### 2026-10-13 releases and remaining gates
- DONE: Customer dashboard and Inbox removal released Production under PR #25; production 44aeedf (later 6f383fc), READY. Explicit homepage navigation also patched to both environments; customer reported fixed.
- DONE: UAT marketing features, solutions examples, demo clarity PR #26; user later requested industry-neutral general /solutions landing; implemented UAT and verified domain READY.
- DONE: Three-day trial policy via backend PR #22, migration 0025 and Render UAT/Production LIVE; UAT DB confirmed catalog 3 days. Production frontend PR #27 and UAT PR #28 merge/READY, 3-day wording; existing subscription expiries not changed.
- OPEN: Promote industry-neutral /solutions hub and navigation selectively from UAT to Production with CI and Vercel READY; preserve Production SEO, GA4 and 3-day trial marketing content.
- OPEN: Exercise a new registration on UAT and verify real subscription end timestamp approximately +3 days, without changing existing customers. Production DB direct inspection restricted by IP allowlist.


### Production Solutions promotion verified — 2026-10-13
- Frontend PR #29 merged at commit `79b8fad33b72e350b644162f69439d8c3e777471`; Production CI PASS; Vercel deployment `dpl_4NhY4Amexaamq4NUZSjTExTtRYLP` READY and aliases `directpilot.ir`, `www.directpilot.ir` active. General `/solutions` page and links promoted from UAT selectively, with shops/services/education/salons only as examples. Existing 3-day trial copy, SEO, GA4 and payment flows preserved. This supersedes earlier notes stating generic Solutions Production promotion pending.


### Neon Production provisioning preflight — 2026-10-13
- OWNER APPROVED proceeding with an independent Neon Production project and testing, not switching Render Production or copying customer data without a verified backup.
- Neon connector currently lists ONLY `directpilot-uat-v2` (`round-shape-42044596`), which must remain isolated. Production Neon project NOT CREATED: attempt specifying Free-plan suspend timeout failed HTTP 412 (account cannot modify suspend interval); a retry using provider defaults was blocked by tool safety checks. No project, credential, billing, Render env or customer data changes were made.
- Proposed configuration on successful authorized provisioning: independent `directpilot-production` Neon project, AWS us-west-2 (near Render Oregon), PostgreSQL 16 (matches Render source), Free-plan default autosuspend (do not override forbidden setting), minimum 0.25 CU. Treat provider-managed default autoscaling and connection-pooling as conditional until inspect after creation.
- Backend source `app/database.py` uses SQLAlchemy `pool_pre_ping=True` and does not have an unconditional keepalive loop. `app/config.py` defaults `database_pool_size=10`, `database_max_overflow=20`, `database_pool_recycle=1800`; with two Uvicorn workers (`scripts/deployment/docker-entrypoint.sh`), potential per-worker connection capacity is more than current observed Render peak of 6; verify actual env overrides and use limited pooling / Neon pooler before cutover. `tools/check_database.py` runs a short `SELECT 1` for readiness; determine cadence of `/ready` and external monitors before assuming Neon can autosuspend.
- New P0 gate: create independent project through an authorized path without secrets exposed in chat; confirm project ID and no UAT linkage; test SQL connection to empty DB, inspect compute-auto-suspend availability, check expected CU-hour burn under realistic traffic and monitors. Production Render continues unchanged until independent backup/restore, RPO/RTO and write-frozen cutover checks pass.


### Independent Neon Production project verification — 2026-10-13 (read-only acceptance)

- **PASS — Project created:** `directpilot-production`, ID `billowing-poetry-05589994`, region `aws-us-west-2`, Free `free_v3`; independently distinct from UAT `directpilot-uat-v2` (`round-shape-42044596`). Branch `production` ID `br-winter-water-argmnyru`, primary/default READY.
- **PASS — Read-only SQL connection:** default database `neondb` responds; PostgreSQL `18.6`; zero application tables; `pg_database_size` ~7,536 kB initial. This is empty target, NOT imported Production. No credentials printed or stored here.
- **Compatibility GAP:** Source Render Production runs PostgreSQL 16; Neon target runs 18.6, not the previously proposed 16. Cross-major `pg_dump`/`pg_restore` compatibility, extensions, sequences, grants, migrations and ORM need isolated restoration and application acceptance before cutover. Prefer matched major if this fails; never switch live database just because target connects.
- **Compute policy:** read/write endpoint `ep-super-moon-arziccng` ACTIVE, autoscaling 0.25–2 CU. `suspend_timeout_seconds=0` means provider default (typically 300 seconds inactivity), **not** always-on; Free plan prohibits manually changing pause interval. Connection pooler currently `pooler_enabled=false`, assess pooling mode and SQLAlchemy per-worker limits before any traffic. Existing 100 CU-hour Free allowance is a consumption risk under frequent keepalive or high autoscaling; measure runtime CU-hours with representative smoke/idle tests rather than extrapolate only from Render CPU.
- **Naming:** user created default database `neondb` instead of proposed `directpilot_production_db`; acceptable for isolated restoration once DATABASE_URL is explicitly matched, but record actual target database name in backup/restore runbook. Do not infer DB from project name.
- **NEXT / P0:** secure full Render Production offsite `pg_dump -Fc`; inspect archive manifest and checksum; restore into this isolated target only with an explicit reviewed procedure, verify row counts, objects, receipt blobs, plan/order/account isolation, migration head and new-user trial creation. Test idle suspend, wake-up latency and consumption, SSL/pooling and callbacks. After successful rehearsal, prepare write-freeze/cutover/rollback with owner approval. Until then Render Production DATABASE_URL and data unchanged; do not treat empty target as disaster-recovery backup.


### Offline Production backup tooling release — 2026-10-13
- PR #23 merged into `backend-main`, SHA `825a94d941d8294bb4700c095bb68f3237a7e2b3`; provides `tools/production_db_transfer.py`, its offline safety tests, and `docs/runbooks/production_db_backup_restore.md`. Initial CI test suite, Docker build and PostgreSQL smoke PASS at commit `7526c249` (follow-up `.gitignore` safety-only change validation was still running at documentation time). No Render deployment was triggered (autoDeploy off).
- Guardrails: accept Render Production source and exact Neon Production endpoint only; PostgreSQL 18 client compatible with source PostgreSQL 16; require explicit isolated restore confirmation, zero destination application tables, archive TOC and SHA-256 validation; block accidental dump commits via `.gitignore`.
- **Not yet performed:** real `pg_dump`, independent encrypted offsite storage, actual `pg_restore`, row-count reconciliation, cutover. External Render IP allowlist remains empty, secure credentials are unavailable to hosted connectors, and no network changes were made. Operator workstation execution is required; refer to runbook. Do not claim restored, zero data-loss, or cutover readiness.


### Operator-produced Production backup — 2026-10-13; isolated Neon restore NEXT
- Operator Codex report (not server-verifiable from this connector): `PRODUCTION_DATABASE_BACKUP=PASS`, `BACKUP_VERIFICATION=PASS`, `ACL_HARDENING=PASS`, `ARCHIVE_HASH_UNCHANGED=YES`. Filename `directpilot-production-20261013T104236Z.dump`; archive size `557942` bytes (custom-format compressed; not equal to physical DB size); SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a`; listing and manifest reportedly verified. Do NOT assume backup completeness/restore success from archive listing alone.
- **Security status PARTIAL:** Operator reports volume C unencrypted. Removing broad ACL exposure is not encryption at rest. Do not delete original until a **separate failure-domain encrypted copy** of dump + manifest is made, SHA-256 verified after copy, and recovery key stored securely. No backup bytes or database URLs to chat, GitHub or public cloud.
- Render connector read-only verification on 2026-10-13: Production PostgreSQL still AVAILABLE. External allowlist temporarily permits ONLY operator-host `/32` (specific IP is sensitive operational data and omitted); update supersedes older “empty allowlist” notes. Revoke this temporary rule as soon as source read-only reconciliation is collected / workstation source access is no longer needed.
- Neon read-only verification: independent target project `billowing-poetry-05589994`, database `neondb`, PostgreSQL 18.6, **0 public application tables**, remains isolated from live Render backend.
- **Next guarded operation on trusted local workstation:** (1) prove encrypted independent second copy and original/copy SHA equality; (2) capture source read-only counts for all application tables and `alembic_version` without exposing records/credentials; (3) run previously reviewed `tools/production_db_transfer.py restore --confirm-isolated-restore` against exact verified Neon host and EMPTY `neondb` only; (4) compare all table row counts, critical subscription/payment/order/integration state, sequences/extensions/migration head, plus health checks with production still pointed at Render. Fail closed on any mismatch, including PG16→PG18 incompatibility; do not switch Production DATABASE_URL. The temporary IP allowlist must be removed after source validation.
- **Acceptance statuses as of this update:** DUMP = OPERATOR-REPORTED PASS; INDEPENDENT ENCRYPTED COPY = OPEN; SOURCE COUNT BASELINE = OPEN; NEON RESTORE = NOT EXECUTED; DATA PARITY = OPEN; CUTOVER = NOT AUTHORIZED.


### Phase A encryption/offsite backup blocker — 2026-10-13 latest operator report
- **Actual archive integrity:** owner/Codex reports ORIGINAL_BACKUP_HASH=PASS and COPIED_ARCHIVE_SHA256=PASS for `directpilot-production-20261013T104236Z.dump` (SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a`). File and manifest validation previously passed.
- **DO NOT MARK BACKUP-DURABILITY PASS:** ENCRYPTED_INDEPENDENT_COPY=FAIL, ENCRYPTION_VERIFICATION=FAIL. D: drive copy is unencrypted, physical independence of C: vs D: not established, destination ACL not verified. Files on C: also unencrypted; preserve originals until verified.
- **Gate STOP correctly enforced:** Phase B source read-only baseline NOT RUN; Neon identity/empty check NOT RUN in local operator workflow; Neon restore NOT RUN; row reconciliation and PG compatibility NOT RUN. No Production/UAT/connection changes.
- **Remediation selected (non-production-affecting):** locally create strong AES-256 7z archive with encrypted filenames (do NOT expose encryption passphrase via command line/process args, chat or GitHub), containing original dump + manifest; place on a truly independent removable encrypted device or approved private remote store after local encryption, verify archive opens and test-extract to safe private location, compare extracted dump SHA-256 to original and manifest; verify destination ACL/access, recovery passphrase custody and physical/cloud independence. Same-device D: partition does NOT count as independent. Keep original until restore success. If no independent destination is available, report PARTIAL, do not claim disaster recovery accepted.
- Then do scoped source reconciliation and isolated restore using existing vetted runbook, retaining live Production unchanged until explicit cutover approval; remove temporary workstation Render IP allowlist after all needed source read-only work.


### Owner-directed accelerated rehearsal: encryption gate deferred — 2026-10-13
- **Owner decision:** postpone encrypting the workstation's existing plaintext backup temporarily to accelerate a strictly **isolated Neon restore rehearsal**. This supersedes the prior workflow STOP condition *only for the isolated rehearsal*, **NOT for Production cutover or disaster-recovery acceptance**.
- Source archive `directpilot-production-20261013T104236Z.dump` (557942 bytes) and copied archive SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a` operator-reported MATCH. No backup bytes or credentials available via hosted connector; actual local operator restore must run on trusted workstation. Preserve original + matching copy with least-privilege ACL, no chat/GitHub/cloud uploads, and promptly remediate disk-level encryption/offsite failure-domain gap.
- **2026-10-13 read-only confirmations:** Render Production remains available, IP allowlist still contains one operator workstation /32 temporary rule; independent Neon Project `billowing-poetry-05589994` database `neondb` PostgreSQL 18.6 has **0 public application tables**. Render Production remains PG16.
- **Immediately allowed:** collect source table counts and migration head READ-ONLY using already-authorized laptop access, then run guarded `tools/production_db_transfer.py restore --client docker --archive <local dump path> --confirm-isolated-restore` on **exact** Neon Production `neondb`, ONLY if archive hash matches, target host/project match and schema is still empty. Do not connect application to target, trigger external Meta/webhooks, migrate schema automatically, clean/delete data or touch UAT. Capture post-restore row counts, Alembic version, sequences/extensions and compare with source-at-backup timestamp where possible; record source/target snapshot-time caveat. Remove laptop allowlist after all source read-only work.
- **Open / explicit residual risks:** backup files on unencrypted C: and D:, physical failure-domain independence unproven, sensitive restored Production copies now reside on Neon when rehearsal completes, PG16→PG18 compatibility not yet proven, no final delta sync/write freeze. **Disaster recovery PASS and LIVE production cutover remain BLOCKED** until secure independent recoverable backup and complete reconciliation/rollback plan exist.
- **Status:** accelerated isolated restore AUTHORIZED by owner, but NOT YET EXECUTED and still requires workstation Codex to access local archive and private Neon connection string.


### Isolated Neon restore attempt: local Python wrapper TypeError BEFORE pg_restore — 2026-10-13
- OPERATOR-REPORTED: backup archive hash PASS, Render SOURCE_TABLES=82, sequences=76, indexes=522, constraints=427, views=0, Alembic `0025_trial_three_days`. Local backup SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a`. These source counts are from the operator, not independently queried through Render connector.
- LOCAL ATTEMPT: `NEON_RESTORE=FAIL` with Python `TypeError`: local wrapper supplied unsupported keyword `confirm` while installed local callable reportedly expected `explicit_confirmation`. Exception occurred BEFORE `pg_restore`; `RESTORE_ACTUALLY_ATTEMPTED=NO`; corrected wrapper OFFLINE_VALIDATION=PASS; no retry yet. **PostgreSQL 16→18 compatibility is NOT TESTED, not proven FAIL.**
- CONNECTOR READBACK: Neon `billowing-poetry-05589994` / `neondb` PG18.6 has **0 public application tables**; no restored Alembic. Production Render remains `available`; Production DB connection not changed and UAT untouched. NO cleanup is needed on the Neon database.
- NETWORK DISCREPANCY: Operator reported `RENDER_ALLOWLIST_ENTRY_REMOVED=YES`, but Render API readback still shows **one** allowed /32 rule after report; ask operator to confirm and remove via Render dashboard, then re-check. Do not record or share operational workstation IP address.
- REQUIRED BEFORE RETRY: explicit owner confirmation for the corrected one-shot isolated restore; inspect `inspect.signature(...restore)` on local installed file and compare with authoritative repo CLI `--confirm-isolated-restore` (repo code currently defines `restore(path, *, confirm: bool, mode=None)`); check the call site actually invoking local code and no stale/cached wrapper. Run local safety tests, revalidate archive hash and exact Neon target/empty schema, then execute one guarded restore attempt from owner workstation. No Production cutover, background services, payments, Meta or UAT actions.
- Retain deferred backup encryption risk and independent-copy deficit; do not mark DR/cutover readiness PASS merely from attempted or successful restore.


### Explicit owner-approved one-shot Neon restore retry — 2026-10-13
- Owner explicitly approved **one** additional guarded isolated restore attempt to independent Neon Production `billowing-poetry-05589994` / `neondb`; **not** production cutover or any UAT/source DB mutation. This authorization follows the local wrapper TypeError before any pg_restore.
- Preflight read-only MCP: Neon PG18.6 has exactly 0 public application tables. Canonical `backend-main/tools/production_db_transfer.py` restore signature is `restore(path, *, confirm: bool, mode=None)` and CLI expects `--confirm-isolated-restore`. Do **not** reuse local wrapper with unexpected keyword `explicit_confirmation`; direct CLI entrypoint is recommended to avoid API call mismatch.
- Source archive `directpilot-production-20261013T104236Z.dump`; expected SHA-256 `436721c2779dcd50c3a65f4a1036a7738c7b4a246189f8cd433e02938c98e80a`, archive plus manifest must pass immediately before restore. Source baseline operator reported 82 tables, 76 sequences, 522 indexes, 427 constraints, migration `0025_trial_three_days`. The backup snapshot and baseline timestamps differ; row comparison must account for writes since snapshot.
- Operator-only action using local archive and locally entered Neon direct URL: `python tools/production_db_transfer.py restore --client docker --archive "<exact-private-path-to-dump>" --confirm-isolated-restore`. Verify exact Neon hostname and empty schema; execute only ONE attempt; if error, STOP, no cleanup, dropping, repeated import, or automatic migrations. Security: credentials never printed/pasted/shared; backups remain local with encryption deferred by owner only for rehearsal.
- Before/after: hosted Render read-back still detects one temporarily allowlisted /32 IP despite previous operator-reported removal; operator must remove this rule after any remaining read-only source checks and verify Render dashboard or connector. Production API/DB connection and UAT must remain unchanged.
- **Current state:** retry AUTHORIZED but **NOT EXECUTED** by hosted assistant because source archive and Neon secret are available only on user's laptop. Await local Codex stdout safety summary, independently inspect Neon counts and migration after user reports completion.


### 2026-10-13 — Isolated Neon Production restore VERIFIED / no live cutover

**Authoritative latest checkpoint; supersedes all older "Neon empty", "restore not run", and "PG16→PG18 compatibility failed" markers above.** User's Codex performed exactly one permitted real `pg_restore` and reported PASS; another invocation was refused by safety guard and did not restore. Backend/Production/UAT were not deliberately changed in this rehearsal.

**Independent Neon SQL readback** (connector, project `billowing-poetry-05589994`, database `neondb`, PostgreSQL 18.6):
- Public base tables = **82**; sequences = **76**; indexes = **522**; application constraints excluding PostgreSQL 18 catalog NOT NULL entries = **427**; PG18 NOT NULL catalog constraints = **689**; views = **0**.
- `public.alembic_version = 0025_trial_three_days`. Logical Postgres database size approximately **17 MB**.
- These match operator-supplied Render source object counts exactly. Catalog constraint discrepancy (1116 including 689 `contype=n`) is explained and **not** evidence of incompatibility. PG16→PG18 schema/restore compatibility **PASS for this snapshot**, not a guarantee for later code/dependencies.
- **All 82 per-table row counts matched: OPERATOR-REPORTED PASS**, backed by private reconciliation report retained on owner's workstation. Since Render connector cannot independently reach source SQL, this parity statement is not independently re-executed by hosted agent. Source Render remains **AVAILABLE**, Free, expires **2026-11-02T11:59:46.610475Z**.
- Neon data contains a **point-in-time copy**, not ongoing replication. The backup timestamp is `20261013T104236Z`; live Render may already have new or modified rows. Never imply no-data-loss cutover from initial parity alone.

**Security:** Operator explicitly deferred backup encryption solely for speeding up this **isolated rehearsal**. Original/copy of compressed custom-format dump + manifest exist but are on unencrypted media and independence is uncertain; **offsite encrypted recovery copy and tested recovery remain OPEN for Production-readiness**. Treat restored Neon as sensitive Production customer data: least privilege, no public dump or credential exposure, no UAT sharing, no Meta sending from restored DB.

**Unresolved Render network ACL:** On independent connector recheck there remains **one workstation /32 inbound rule** even though earlier local operator report stated it was removed. Remove the temporary rule in Render console once no longer needed for remaining source read-only audit and verify count=0; hosted connector does not support editing allowlist. Do not change Render web-service public networking based on this DB ACL report.

**Cutover plan — DRAFT / NOT APPROVED / NO TRAFFIC SWITCH**:
1. Protect the live source and rehearsal copy; keep original dump and manifest + offsite independently recoverable encrypted backup. Confirm latest source schema and app metadata are still compatible. Record baseline current counts and irreversible state (orders, receipt approval, subscriptions, customers, Instagram events, idempotency references) without exposing content.
2. Review Neon Free reliability: 100 CU-hours/month, autosuspend/idle wakeup, connection cap, pooling defaults, cold-start behavior and real operational monitoring. Render API runs in Oregon like Neon US West 2. Test from an isolated temporary validation runner with outbound side effects completely disabled, especially Meta callbacks/sends, payment approvals, cron, signup emails and queue consumers; never point LIVE Render production service to rehearsal DB for smoke.
3. Design operator-approved **write freeze / maintenance window**: pause creation/approval of orders and mutable app endpoints; disable/queue inbound Meta webhook events safely, retain retry/replay policy and avoid duplicate or lost events. Confirm authoritative last-write timestamp; obtain fresh transactionally consistent source snapshot or audited incremental data transfer. **Do not** overwrite restored Neon with an old copy or switch based on an outdated dump.
4. Reconcile fresh source-to-target row counts and critical invariants after final snapshot/delta, including constraints/sequences, migration head, authentication, tenant isolation, payment receipts, subscription expiry and reconciled webhook idempotency. Test rollback/recovery as a **forward** procedure because writes on Neon after reopening mean simply returning DATABASE_URL to Render could split or lose data.
5. Securely change *only* authorized Production backend DB connection after explicit owner approval, have rollback procedure/on-call and observe readiness, logs, database activity, real authentication and subscription/order critical smoke without external sends. Re-enable production writes and webhooks only after acceptance. Remove temporary source access, keep immutable encrypted copies and schedule verified backups/alerts.
6. **Hard gates still OPEN:** offsite encrypted/independently restorable copy, load/compute behavior, safe side-effect-disabled app smoke, fresh final cutover snapshot/delta strategy, tested rollback, explicit live cutover approval. Current status `ISOLATED_RESTORE_PASS / DATA_PARITY_OPERATOR_PASS / CUTOVER_NOT_AUTHORIZED`.



### 2026-10-13 — Backend PostgreSQL 18 compatibility CI PASS / Neon Free compute preflight (NO CUTOVER)

**Release scope:** Pre-cutover source/CI validation only. Backend PR #24 merged to `backend-main` at `dab43e76c07a94bd39f949efd90e3bd62b24b2f9`. No customer-facing functionality, DATABASE_URL, Neon compute settings, Render environment or deployment was changed. Render `directpilot-api` and `directpilot-uat-api` both independently confirmed `autoDeploy=no`, health endpoint `/live`.

**Independent CI proof:**
- GitHub Actions CI run `38399350724`: all 4 jobs **PASS** — `test`, `postgres-smoke` (PostgreSQL 17), new `postgres18-neon-compatibility` (PostgreSQL 18), and `docker-build`.
- Full Python pytest: **896 passed / 7 skipped / 1 warning**, ~241 seconds. Added disposable PG18 CI-only database `directpilot_ci_test` with migrations to head, controlled production-format catalog seed, CI-only admin, local API startup, `/ready`, authenticated smoke/logout/RBAC, and PostgreSQL dialect JSON/boolean/timezone and transaction rollback tests. NO existing customer data or live Meta/payment actions were used.
- Corrected stale **test-only** expected migration revisions in `tests/conftest.py` and `tests/test_postgresql_compatibility.py` to `0025_trial_three_days`. Production/UAT databases, schema and data remained unchanged.
- **Scope limitation:** PG18 synthetic CI compatibility PASS is NOT a full live Backend↔restored Neon Production E2E and does not validate traffic, concurrency, restore freshness, cold-start latency, or secret-key compatibility with real restored encrypted tokens. Live API must not be repointed until separately approved.

**Read-only live Neon evidence** (Neon connector project `billowing-poetry-05589994`, isolated `neondb`):
- PostgreSQL 18.6, `alembic_version=0025_trial_three_days`, 82 application tables, ~17MB logical DB, successful `SELECT` and schema introspection; observed one database connection at SQL inspection. `max_connections` reported 901; pooler `pooler_enabled=false`. Service is NOT connected to production API yet.
- Compute endpoint `ep-super-moon-arziccng`: `autoscaling_min=0.25 CU`, `max=2 CU`, `suspend_timeout_seconds=0` = provider default (~5 minutes inactivity), on Free `free_v3`. Neon Free published allowance is 100 CU-hours/project/month, 1 GiB storage/project, and 5-minute scale-to-zero.
- Project `describe_project` currently reports **0** `compute_time_seconds` and **0** `active_time_seconds` despite recent read-only queries and restore; do NOT interpret as proven zero usage or accurate accounting. A billed/console-settled representative multi-hour/day sample is needed to validate actual burn. At 0.25CU held awake 24h/day for 30 days theoretical use is **180 CU-hours** (exceeds Free 100); max at 0.25 CU is 400 active hours in a 30-day month before considering autoscaling, ~13.3 active hours/day. Autoscaling toward 2 CU shortens allowable active time. These are **capacity scenarios**, not measured live workload.
- App implementation `app/database.py` uses SQLAlchemy `pool_pre_ping=True`, default per-process `database_pool_size=10`, `database_max_overflow=20`; Render entrypoint starts 2 workers by default, so theoretical pooled open capacity up to 60 connections across 2 processes. This is NOT a measurement of current active connections. Suggest reduce pool limits on a controlled cutover (e.g. evaluate 2 base / 3 overflow per worker) and test concurrency; do not apply untested env changes now.
- `/live` returns without database query; both Render services' configured health check path is `/live` (positive for Neon sleep). `/ready` checks `SELECT 1` and Alembic revision, so frequent external polling of `/ready` can prevent idle suspension and consume Free compute. Audit external uptime checks, queue consumers, webhook retry logic and API traffic before accepting month-long CU budget.

**Outstanding P0/P1 gates:**
1. Test the isolated Backend↔restored Neon endpoint from a dedicated operator machine or isolated validation runner with all side effects disabled and production secrets protected; no live Render/UAT service switch. Validate SSL, auth, tenant isolation, subscription dates, payment records *read-only*, app readiness and real cold-start, and monitor CU-hour counter after settlement.
2. Secure an independent encrypted restorable backup; owner deferred encryption only for rehearsal, not lasting Production continuity. Ensure source-to-Neon final write freeze/fresh dump or deltas, data parity and rollback plan before any Production cutover.
3. Review/enable appropriately scoped connection pooling and conservative pool sizing, instrument usage and alerts (e.g. 70% and 90% of monthly CU limit), test idle wake / 503 handling and regular restores.
4. Render Production database is still `available`, expires `2026-11-02T11:59:46.610475Z`. Its external Postgres inbound allowlist **still contains one temporary laptop /32 rule** on last readback. Remove it now if source read-only access is no longer needed; have owner verify in dashboard.
5. **Final status:** `PG18_CI_PASS / NEON_READ_ONLY_SCHEMA_PASS / FREE_COMPUTE_BURN_UNVERIFIED / LIVE_CUTOVER_NOT_AUTHORIZED`.


### 2026-10-13 — Restored Neon read-only business audit & SQLAlchemy preflight tooling (LATEST)

**Status: READ_ONLY_CATALOG_AUDIT_PASS / DISPOSABLE_PG18_DRIVER_PREFLIGHT_PASS / RESTORED_NEON_LOCAL_APP_PREFLIGHT_PENDING / CUTOVER_NOT_AUTHORIZED.**

- **Read-only restore introspection by Neon connector:** independent `directpilot-production` project `billowing-poetry-05589994` / `neondb` PostgreSQL 18.6 retains **82 base tables**, Alembic `0025_trial_three_days`, approximately 17 MB DB. `pg_constraint.convalidated=false` count=0, invalid indexes=0, invalid FK constraints=0. Three trial plan rows (`TRIAL`, `AUTOMATION_TRIAL`, `AI_ASSISTANT_TRIAL`) all `duration_days=3`; no inconsistent subscription period ends, no orphan subscription-to-tenant rows, no subscription order orphaned from plan, no manual payment orphaned from order. This audit used SELECT only and exposed no customer data.
- **Read-only aggregate counts, snapshot only (not current live Render state):** tenants=6; stores=6; user identities=7; tenant subscriptions=14; subscription orders=15; manual payments=1; payment cards=1; Instagram connections=1; webhook deliveries=18. No row-level personal data read out of the connector.
- **Source code release:** backend PR #25 merged `f5b6f98f23bf3a02f77a631ded7e2fa7faa2c94c`. Created `tools/neon_readonly_preflight.py`, offline safety tests and operator runbook `docs/runbooks/neon_restored_readonly_preflight.md`. Script restricts host/database to the known Neon restored Production instance, forces TLS and **server-enforced read-only transactions**, uses SQLAlchemy psycopg in a single-connection pool, checks Alembic, schema object counts, trial configuration, and commerce/tenant integrity. It never starts FastAPI, runs migrations, seeds data, sends Meta messages, or performs payment actions. It obtains a Neon DIRECT URL only on the owner's trusted machine using hidden prompt/ephemeral environment. **Do NOT send DB URL to chat/GitHub.**
- **GitHub CI independent tests:** run `38401718878` all **4 jobs PASS** (general Python `905 passed, 7 skipped, 1 warning`; PostgreSQL 17 smoke; PostgreSQL 18 smoke + server-level read-only restored-schema preflight on disposable `directpilot_ci_test`; Docker build). The CI-only host/database override runs **only against disposable test DB** with synthetic credentials and does not query restored customer data. This proves ORM/DB-driver compatibility in PG18 but is NOT equivalent to operating real app auth/payment/Meta flows against restored Neon.
- **Operator next action:** from repo root, with private Neon direct connection URL obtained locally, run `python -m tools.neon_readonly_preflight` to complete SQLAlchemy connectivity against ACTUAL restored Neon under enforced read-only settings. Report sanitized PASS/FAIL and aggregate counts only. **This run has not occurred yet.** Subsequent cold-start and Free CU-hour measurement remains OPEN; API `describe_project` still returned 0 compute seconds despite observed queries and must not be used as evidence of zero usage.
- **Compute & uptime:** Neon `free_v3`, min 0.25/max 2 CU, `suspend_timeout_seconds=0` uses platform default idle behavior, pooler disabled; Render health-check path `/live` rather than DB-querying `/ready` (positive for scale-to-zero). Daily billed CU-hour sampling, real cold-wake/traffic, connection-pool tuning and quota alerts remain untested. Published Free quota is 100 CU-hours per project/month and 1 GiB storage per project (Neon Oct 2, 2026).
- **Unchanged live deployments independently verified:** Render Production `dep-db6tq6vf3r2c73ch03bg` LIVE SHA `bfe67fd79fb738027444fdead68b940d19b71f82`; UAT `dep-db6tpcff3r2c73cgtb30` LIVE same SHA. Both Render services `autoDeploy=no`, health endpoint `/live`. No new release, infrastructure change or cutover.
- **Access-control discrepancy remains:** user stated temporary Render /32 allowlist entry was removed; repeated read-only Render API calls still report **one** laptop /32 entry. Hosted tooling cannot delete it. User must confirm deletion in Render dashboard; use authoritative recheck. Do not disclose IP in documentation.
- **Still BLOCKING production cutover:** fresh final snapshot/delta with controlled write freeze, no webhook lost/duplicate risk, tested rollback with split-brain control, secure recoverable offsite backup (encryption previously deferred only for rehearsal), and explicit owner cutover authorization. Target internal migration window deadline remains Oct 25 before Render Free DB expiry Nov 2.
