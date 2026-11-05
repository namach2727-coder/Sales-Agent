# SEO Growth F2b — durable Search Console data foundation

**Status:** implementation design for backend Draft PR #121; not a release or entitlement approval.

## Purpose and current source
Move the independent commercial SEO service from response-only previews to durable, tenant-isolated Search Console data. Backend: `namach2727-coder/Sales-Agent`, branch `feature/seo-growth-commercial-foundation-20261101`, PR #121. Companion frontend PR #71. UAT schema is already `0029_seo_pilot_revision`; migration 0027→0029 is complete and must never be replayed.

F1 OAuth/property onboarding and F2a explicit on-demand reports exist. F2a compares two adjacent 28-day Pacific-calendar windows using finalized Web Search data, daily property totals, and up to 500 query/page rows. Missing dates remain unknown; truncated query/page samples never form property totals. Results are response-only.

## Proposed additive storage model
Create a new migration only after confirming the current graph; expected next revision is 0030, but the exact ID must follow repository naming conventions.

1. **Sync run:** tenant/store/site, requested/effective date range, data state, search type, dimensions, status, started/completed timestamps, retry metadata, row counts, coverage summary and sanitized error code.
2. **Daily property metric:** unique site/date/search type/data-state key; clicks, impressions and position. CTR is derived from clicks/impressions.
3. **Query/page metric:** unique site/date/query/page/search type/data-state key; clicks, impressions and position. Query/page rows are discovery samples, not a source for property totals.
4. **Coverage marker:** explicit per-date/dimension completion, including successful empty results, distinguishing zero rows from unknown/missing/failed data.
5. **Sync lease/cursor:** per-site partition ownership and resumability across workers; database locking/lease expiry, never process-local locks.

All persisted records must carry tenant/store/site scope and use composite foreign keys/unique constraints. Permission loss, grant expiry, site disconnect and Google disconnect must block new ingestion and report reads. Do not store OAuth secrets, raw provider payloads or query text in audit logs.

## Ingestion invariants
- Start with bounded explicit backfill and incremental date windows; no unlimited history.
- Fetch daily property totals independently from query/page rows.
- Use deterministic unique keys and idempotent upserts; replaying a window cannot duplicate or double-count.
- Persist successful empty partitions as complete; missing or failed partitions remain unknown.
- Refresh a configurable recent-data correction window; do not assume first-seen GSC values are immutable.
- Apply per-site/tenant quotas. Retry only transient network/429/5xx errors with bounded backoff and jitter; honor Retry-After. Do not retry invalid-grant or permission failures as transient.
- Keep provider HTTP outside long DB transactions. Claim a short DB lease, fetch bounded batches, then atomically commit each partition.
- Store source date, fetched_at, property, Web search type, dimensions, dataState and normalization version.
- Sanitize provider failures; never log OAuth code/state, tokens, query text or credential-bearing URLs.

## Report contract
Customer report remains explicitly requested and reads persisted snapshots. Show last successful sync, freshness and per-dimension/date coverage. Calculate property totals only from daily property metrics. Query/page opportunities carry sample/truncation labels. Compare periods only with complete comparable coverage. Distinguish zero, unknown, partial and complete. Recommendations remain review proposals, not rank predictions.

## Retention and deletion
No retention period is approved. Thirteen months is only a proposal to evaluate. Until owner approval: no purge job, TTL, hard-coded retention constant, destructive migration or automatic deletion. Do not imply Google disconnect deletes previously collected metrics. Decide duration, privacy/legal basis, customer disclosure, deletion scope, backup expiry and aggregate treatment before purge implementation.

## Rollout and acceptance
All flags remain default-off. Implement and test only on the existing feature branch. Migration must be additive; downgrade must refuse when metric rows exist. Validate PostgreSQL 18, multi-worker leases, idempotency, partial failures, empty partitions, permission loss, disconnect/reconnect, tenant isolation, quota/retry behavior and freshness/coverage output. Do not migrate UAT/Production, configure secrets, create grants, connect real Google accounts, schedule jobs or mutate websites without explicit owner approval.

Acceptance: repeated sync leaves row counts/totals unchanged; property totals match independent daily GSC data; successful empty partitions are complete; failed partitions remain unknown; workers cannot own the same partition concurrently; DB and query scope prevent cross-tenant access; permission loss blocks ingestion and reports; report exposes freshness/coverage; retention stays non-destructive until approved.


### F2b CI correction checkpoint · 2026-11-05

The first full CI run for F2b completed with 1064 passed, 2 failed and 7 skipped. Both failures were stale migration-head assertions that still expected `0029_seo_pilot_revision` after the additive `0030_seo_growth_durable_data` revision became Alembic head. No migration execution or persistence-contract test failed.

Corrected the readiness assertion in `tests/test_environment_deployment.py` and the single-head assertion in `tests/test_seeding.py` to expect `0030_seo_growth_durable_data`. The corrected source head is `5cd2ad78eadfa9455883f469bb947baa1bb40a9d`; CI run [#42010674663](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42010674663) is currently in progress. Docker build, PostgreSQL smoke and PostgreSQL 18 compatibility/preflight have passed on this run; the full pytest job is still running. Do not claim the full suite green until its conclusion is recorded.

No UAT or Production migration/deployment was performed. Vercel checks currently show the DirectPilot UAT API and website successful, while the TelBot UAT API check is failed; this is separate from the GitHub CI jobs. Keep PR #121 Draft and unmerged.


**CI result update · 2026-11-05:** The corrected source head `5cd2ad78eadfa9455883f469bb947baa1bb40a9d` passed CI run [#42010674663](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42010674663): **1066 passed, 7 skipped, 0 failed**. Docker build, PostgreSQL smoke and PostgreSQL 18 compatibility/preflight passed. This is source/test evidence only, not a UAT/Production release or live Google acceptance.


### F2b explicit ingestion implementation · 2026-11-05

Added the first user-triggered ingestion path on this branch:

- New `seo_data_sync_enabled` setting and `SEO_DATA_SYNC_ENABLED=false` in environment examples; the new path is disabled by default.
- Authenticated, CSRF-protected `POST /sites/{site_public_id}/sync` accepts an explicit date range only. It rejects windows over 90 days and dates newer than the three-day final-data delay.
- Google access is refreshed and property permission is rechecked before ingestion. Daily property totals and query/page samples are fetched independently.
- Daily metrics are replaced for the requested window so stale dates omitted by a successful provider response are removed; query/page samples are replaced by deterministic SHA-256 row keys. Successful empty and truncated query/page coverage are explicitly recorded.
- Per-site database lease, sync-run state, sanitized audit events and revalidation of site/connection/grant authority are implemented. There is no scheduler or automatic backfill.

**Validation pending:** this implementation and the additional schema constraints are newer than CI run #42010674663. Do not treat the new sync path as tested until the next full CI run passes. No live Google request, customer grant, UAT/Production migration or deployment was performed. Bounded retry/backoff, sync history/read APIs and reports reading persisted data remain follow-up work. Retention remains unapproved.
