# DirectPilot SEO Platform — product and technical plan



### SEO-GROWTH-P2-ROBOTS-REGRESSION-20261108

- Corrected source head: `b7856bf2b78f569a97d42b06cc334ca59a9ae0f4` on `feature/seo-growth-commercial-foundation-20261101`, Draft PR #121.
- Follow-up source fixes: normalized the crawler policy module docstring; added explicit regression tests for product-specific User-Agent group selection, wildcard path matching, and end-of-pattern anchors in robots rules.
- The robots policy now selects the most-specific product User-Agent group before wildcard fallback, applies the longest matching path rule, and prefers Allow for equal-length matches.
- Earlier exact-head CI #42374256973 (pre-correction head `97c3713`) reported 1175 passed, 3 failed, 7 skipped. The three failures were addressed in source/tests, but **GitHub Actions CI run #42458086591 is now running for the current source head; Docker build and PostgreSQL 18/Neon compatibility have passed, while the full pytest and PostgreSQL smoke jobs are still in progress**. Vercel deployment checks are not release evidence; the GitHub Python test workflow is the validation gate.
- No UAT/Production deployment or migration, Google API call, customer grant, real-site crawl, or SEO flag change was performed. Migration 0030 remains unapplied; PR #121/#71 remain Draft/unmerged.
- Next gate: obtain exact-head GitHub CI and review all jobs/logs. Do not wire crawler to customer-facing endpoints or persist crawl results until CI passes and per-tenant/per-host concurrency controls plus audit schema are reviewed.

### SEO-GROWTH-P2-CI-REMEDIATION-20261108

- Backend runtime source head: `e94071edd589886b8f2af8c96f16d9771e96ab9d` on `feature/seo-growth-commercial-foundation-20261101`, Draft PR #121. The prior exact-head CI run #42374256973 on `97c37135413d5a4cdec0f43c7cb81d1ed0b07f51` completed with **1175 passed, 3 failed, 7 skipped**; Docker build, PostgreSQL smoke and PostgreSQL 18/Neon compatibility passed.
- Failure analysis from the test log:
  1. Robots `Allow` did not override a less-specific `Disallow`. The parser now selects the most-specific user-agent groups, applies longest matching path rule, and prefers `Allow` on equal-length matches.
  2. The pinned socket test compared a monotonic-deadline timeout to exactly `3.0`; the assertion now checks the numeric-IP destination and uses a small timing tolerance.
  3. The aggregate-byte test fixture configured `max_response_bytes > max_total_bytes`, which the policy correctly rejects, and its page body did not exceed the intended aggregate limit. The fixture now respects the invariant and exceeds the aggregate budget.
- Code changes: `crawler_policy.py` commits `3326a7fffa3765ad0bd1f3469bef105bdf538455` and `fdac376218942a688401fdd7910530c1fcd8b145`; transport test commits `28bab39d3e8278aeb6042053df925a3e8774b320`, `4c7eb29e4d4e34749811433a3a1f27975ee5c913`, and final `e94071edd589886b8f2af8c96f16d9771e96ab9d`.
- **Validation is pending on the corrected source.** No workflow run or combined status was returned for exact head `e94071e`; do not claim the three failures are fixed until exact-head CI completes. The code correction is source-only.
- Release boundary unchanged: PR #121 remains Draft/unmerged; PR #71 remains Draft/unmerged; UAT schema remains `0029_seo_pilot_revision`; migration `0030_seo_growth_durable_data` remains unapplied; SEO flags remain default-off. No UAT/Production deployment or migration, real Google Sync, customer grant, scheduled job, billing, retention/purge, CMS write, or live URL fetch was performed.
- Next: obtain full CI on the corrected source head; fix any new failures. Only then continue distributed per-host/per-tenant rate and concurrency controls plus durable crawl audit persistence before any crawler route integration.

### SEO-GROWTH-P2-TRANSPORT-DEADLINE-20261107

- Latest backend source head: `97c37135413d5a4cdec0f43c7cb81d1ed0b07f51`, branch `feature/seo-growth-commercial-foundation-20261101`, Draft PR #121. Exact-head CI run #42374256973 is in progress; do not call the transport validated until the full test job and all infrastructure jobs pass.
- The pinned transport now uses an absolute per-request deadline across TCP connect, TLS handshake, request send, response headers and body reads. Remaining time is recalculated before each validated-IP retry. Socket timeouts map to a stable crawler time-budget error.
- User-Agent matching is fixed to the DirectPilotBot product token used by the actual request header. Cross-origin redirects are rejected, preventing a redirect from silently switching robots.txt scope; same-origin redirects are re-resolved, revalidated and pinned.
- Transport and test suite include regression checks for same-origin redirect validation, cross-origin redirect rejection, robots-before-page behavior, byte accounting, compressed response rejection, numeric-IP connection pinning, SNI preservation and total timeout handling.
- The service remains a library-level capability only. No public route, worker, queue, DB crawl record, distributed host/tenant rate limiter or concurrency lease is implemented. Injected DNS must be bounded by its caller. No external URL was fetched by tests.
- UAT remains at `0029_seo_pilot_revision`; source migration `0030_seo_growth_durable_data` is unapplied; SEO flags remain default-off. No customer grant, Google Sync, billing, CMS write, UAT/Production deployment or migration was performed.
- Next: complete exact-head CI, address any failures, then design persistent per-host/per-tenant concurrency and rate controls and audit persistence before route integration.



### SEO-GROWTH-P2-PINNED-TRANSPORT-20261107

- Backend branch `feature/seo-growth-commercial-foundation-20261101`, source head before documentation update: `a61798ed29c7277aa2dc44ecb0c48c6bd6932f16`; Draft PR #121 remains open and unmerged.
- Added `app/seo_growth/crawler_transport.py`: synchronous GET-only HTTP transport opens sockets to validated numeric IPs (no HTTP-client hostname lookup), preserves HTTPS certificate verification and original hostname SNI, sends the matching Host header, disables compression/cookies/auth, manually follows only same-origin redirects, and checks every redirect through URL/DNS validation.
- Fetch orchestration requests `/robots.txt` before the page, applies the Robots decision, rejects non-HTML responses and non-identity content encodings, enforces response/robots byte limits, total crawl byte budget, redirect count and elapsed/request timeouts. DNS is re-resolved and pinned for each redirect; IP retries recompute remaining time. The current function is not wired to any public API route.
- Added focused transport tests for numeric-IP socket pinning, TLS SNI hostname preservation, redirect validation and limits, robots-before-page behavior, compression rejection, byte accounting and timeout recomputation. Tests use fake request handlers; no external URL was fetched.
- Exact-head CI for `a61798ed29c7277aa2dc44ecb0c48c6bd6932f16` is queued (Docker build, PostgreSQL smoke, PostgreSQL 18/Neon compatibility and full tests). The earlier preflight-only head `e550c25eb5613d0ef1c8fe74b208ead82903af50` passed all four jobs; that does not validate the new transport.
- Scope deliberately remains incomplete: no distributed per-host/tenant concurrency or rate limiter, no crawler queue/worker, no crawl graph/depth traversal, no persistent crawl records or API endpoint. The injected DNS resolver must be bounded by its caller. Cross-origin redirects are rejected rather than silently transferring robots scope. These are explicit follow-up gates.
- No UAT/Production migration or deployment, SEO flag activation, real Google Sync, customer grant, billing activation, CMS write, or live URL fetch was performed. UAT remains at `0029_seo_pilot_revision`; migration `0030_seo_growth_durable_data` remains unapplied.
- Next: exact-head CI; fix any failures; then add distributed host/tenant rate and concurrency controls plus audit persistence before any endpoint integration. Keep PR #121 Draft and do not enable crawling until security review and controlled UAT acceptance.



### SEO-GROWTH-P2-POLICY-LAYER-20261107

- Backend branch: `feature/seo-growth-commercial-foundation-20261101`; source head before documentation update: `866799fdb86847244e02758f508f4317eed7d675`; Draft PR #121 remains open and unmerged.
- Exact-head CI for this source is queued: Docker build, PostgreSQL smoke, PostgreSQL 18/Neon compatibility and full test job. The prior source head `e550c25eb5613d0ef1c8fe74b208ead82903af50` completed all four jobs successfully; that result does not validate later commits.
- A source review found that `resolve_public_addresses` trusted the caller-supplied `CrawlTarget.hostname` fields instead of re-normalizing `target.url`. This was corrected in `68369dfbf7331624de263e6fbacc4bda30e2ae81`, with forged-object regression tests. DNS resolution now derives the hostname and port from the canonicalized URL.
- Added `app/seo_growth/crawler_policy.py` and focused tests: bounded page/per-host/depth/redirect/response-byte/total-byte/time settings; budget accounting; HTML/XHTML response and Content-Length validation; and robots.txt allow/disallow parsing. Robots 401/403/429 and server errors fail closed; 404/410 mean no robots file. The module remains network-independent.
- These are policy primitives, not an operational crawler. No HTTP transport, DNS resolver, endpoint, scheduler, or customer URL fetch is enabled. The transport must still pin each connection to validated IPs, preserve TLS hostname verification/SNI and Host, stream-enforce wire and decoded byte limits, enforce redirect limits, and apply robots policy before page fetches.
- No UAT/Production migration or deployment, SEO flag activation, real Google Sync, billing activation, customer grant, CMS write, or live URL fetch was performed. UAT remains at migration `0029_seo_pilot_revision`; migration `0030_seo_growth_durable_data` remains unapplied.
- Next: exact-head CI; then implement/test the pinned HTTP transport and integrate robots + budgets behind a non-public internal service boundary. Do not expose a customer crawler endpoint until security tests and controlled UAT acceptance are complete.

**Status:** approved development direction from owner instruction on 2026-11-07. This document is a product/engineering plan, not a release or activation approval.

## Product goal
Move from a standalone SEO report to a multi-tenant service that diagnoses, prioritizes and helps improve a customer's organic search performance. The product loop is: Business Profile → Data Collection → SEO Intelligence → SEO Action Center → Continuous Improvement.

## Customer journey
1. Connect a website and authorize Google Search Console.
2. Complete a business profile: category, services, primary SEO objective, description, audience/market and optional competitor domains (maximum three).
3. Run an explicit technical audit and connect performance/search data sources.
4. Review evidence-backed findings and opportunities, sorted by impact, confidence and effort.
5. Approve individual actions; record execution evidence and measure subsequent outcomes.

## Source-of-truth boundaries
| Source | May support | Must not be used for |
|---|---|---|
| Google Search Console | clicks, impressions, CTR, average position, query/page/date dimensions | HTML structure, page speed, crawlability outside reported data |
| First-party crawler | fetched HTML, status, title, description, canonical, robots, headings, links, image alt | search volume, rankings, clicks or inferred Google index state |
| PageSpeed Insights | Lighthouse performance diagnostics and available field metrics | guaranteed ranking impact or universal site score |
| Competitor URLs | publicly accessible page structure and content observations | private analytics or unsupported traffic/rank estimates |

Daily property metrics remain authoritative for property totals. Query/page rows remain bounded samples and must never be summed into site totals. Missing dates are unknown, not zero; incomplete or truncated coverage must be visible in reports.

## Technical audit MVP
Initial deterministic HTML parser (no network access):
- document title and length;
- meta description and length;
- canonical URL;
- robots meta directives;
- language attribute;
- H1 count/text and heading hierarchy observations;
- image count and missing/empty alt count;
- internal and external anchor counts relative to the verified site origin.

The parser reports observations, not ranking penalties. It must preserve page-level evidence and avoid asserting a defect when the HTML input is incomplete.

## Network crawler — separate security gate
Before any URL fetch is implemented, require: HTTP(S)-only URL normalization; reject credentials and unusual ports; resolve and reject loopback/private/link-local/multicast/reserved IPs; pin validated destinations or revalidate every connection; repeat checks on every redirect; block cloud metadata ranges; enforce robots.txt policy; per-host concurrency/rate limits; maximum redirects, pages, response bytes and elapsed time; content-type allowlist; decompression limits; no cookies/auth headers; and tenant-scoped audit/rate limits. DNS rebinding and redirect-to-private-address tests are mandatory. No arbitrary user URL fetch until this gate is tested.

## SEO Intelligence and Action Center
Each finding includes stable code, category, severity, confidence, affected URL/count, observed value, expected condition, evidence/source, recommendation, estimated effort, potential impact (clearly labelled as an estimate), and automation eligibility. Avoid fabricated traffic uplift or deterministic ranking promises. Recommendations are proposal-only by default.

## Delivery phases
- P0 — F2b durability: backend and customer UI are implemented. A single explicit sync persists 56 days of daily totals and the current 28-day query/page sample; analysis and per-dimension sync history are read from the database. Backend CI: 1094 passed, 7 skipped; frontend validation: 301 passed, type-check/lint/build and mobile audit passed. UAT acceptance remains pending.
- P1 — Technical audit core: deterministic HTML parser and tests are implemented in app/seo_growth/technical_audit.py and tests/test_seo_growth_technical_audit.py; the parser performs no network requests. The latest CI run exposed a stale H1-outline assertion; its correction is committed separately and awaits CI.
- P2 — Safe crawler: network-free URL/DNS preflight and crawler policy primitives are implemented. The resolver re-normalizes the URL before DNS; page/per-host/depth/redirect/byte/time budgets and robots parsing are covered by tests. No HTTP transport or crawler endpoint exists yet. Exact-head CI for the latest branch source is queued. Next: pinned HTTP(S) transport with TLS hostname verification, streaming byte caps, redirect enforcement and policy integration.
- P3 — Business Profile: tenant/store/site-scoped business profile and up to three validated competitor URLs.
- P4 — Intelligence/Action Center: evidence-backed rules, prioritization, action status and report UI.
- P5 — Performance integration: PageSpeed Insights, quotas, caching and source-specific freshness.
- P6 — Continuous improvement: compare subsequent GSC/crawl snapshots with prior baselines and record approved changes.

## Explicit non-goals until separately approved
No automatic CMS edits, automatic publishing, customer billing/plan changes, scheduler or backfill, data-retention TTL/purge, UAT or Production migration/deployment, or enabling SEO flags. PR #121 backend and PR #71 frontend remain Draft/unmerged. UAT schema remains 0029; source migration 0030 must not be applied to UAT without explicit approval.

## Current source validation
CI run #42012950916, source 52909808babad964da8c19612e12a9837d033a24: 1080 passed, 7 skipped, 3 warnings; all four CI jobs passed. This does not constitute live Google, UAT, or Production acceptance.


## 2026-11-07 P1 test correction

The parser includes H1 in the heading outline. The initial fixture still expected only H2, causing the latest PR #121 test job to fail while PostgreSQL smoke, PostgreSQL 18 compatibility and Docker build passed. The expected outline is corrected to [1, 2]. The correction's CI result is pending; this plan does not claim P1 validation until the exact new head passes. UAT remains at 0029 and source migration 0030 remains unapplied.

## 2026-11-07 F2b report-window alignment

Backend commit `d925c2c1c7a718a5de8780ec0ecd5a31fe1e5c55` adds the optional `query_page_start_date` to explicit sync, allowing one 56-day request to store daily totals for both 28-day report periods and a query/page sample for the current 28-day period. Sync history returns per-dimension coverage, and the status response exposes the independent data-sync flag. Synthetic API tests cover the split-window persistence and persisted report contract. Exact-head CI is pending. Frontend PR #71 still needs the customer-facing Sync, persisted analysis and sync-history flow. No live Google/UAT/Production activation is implied.

## 2026-11-07 F2b end-to-end source validation

Backend head `4856b6f71956031f58c834dfcfa8899621521097` passed CI run #42369504917 with 1094 passed, 7 skipped and 3 warnings; PostgreSQL 17 smoke, PostgreSQL 18 compatibility and Docker build passed. Frontend head `0ff906946a88d86d9b4d5bbb03606326de6eabfa` passed 301 tests, TypeScript, lint, production-static build, verification and mobile audit. The persisted customer portal is now wired to explicit sync, persisted analysis and dimension-level history. Both PRs remain Draft. UAT remains at 0029 with zero grants/connections/sites; migration 0030 and all SEO flags remain unapplied/off. Next gate is controlled UAT acceptance with an authorized test account, not automatic Production rollout.

## 2026-11-07 P2 crawler security preflight

Commit `4cb701b6849e2dc341afd6f098f894a2d8c242a1` adds the first crawler security layer. It canonicalizes public HTTP(S) targets, rejects credentials, unusual ports, local hostnames, private/reserved IPs and mixed DNS answers, blocks IPv4/IPv6 transition forms that can obscure private destinations, and revalidates redirects. DNS is injected; there is no default socket resolver and no HTTP fetcher. Tests use synthetic DNS answers only. The exact-head CI run #42370354421 is pending. Do not enable crawling until a pinned transport, robots enforcement, redirect limits, per-host/tenant throttling and hard resource budgets are implemented and tested.

## 2026-11-07 P2 multicast correction and deployment boundary

Commit `e550c25eb5613d0ef1c8fe74b208ead82903af50` explicitly rejects multicast and other non-unicast address classes after CI showed that Python 3.12 may report multicast as `is_global`. DNS-answer tests now include IPv4 and IPv6 multicast. Exact-head CI run #42370736355 is pending; the three infrastructure jobs passed and pytest remains in progress. The backend Vercel API deployment is a branch preview only (`target=null`). The separate TelBot preview fails due its configured nonexistent root directory `experiments/telegram_bot_builder`, unrelated to SEO. UAT schema remains 0029 and migration 0030 remains unapplied.


### P2 crawler audit foundation · 2026-11-08

Added a tenant/store/site-scoped crawler audit data foundation on top of migration 0030:

- Alembic revision `0031_seo_crawler_audit` adds `seo_crawl_audit_events`, with composite site-scope FK, crawl correlation ID, event kind, outcome, robots decision, HTTP status, byte count, duration, sanitized error code, creation time and explicit expiry.
- The audit writer requires an explicit retention duration (1–365 days); no retention period is silently selected by the persistence helper and no purge job is implemented.
- URL evidence stores only host and a SHA-256 fingerprint of scheme/host/path. Query strings and fragments are excluded; raw URLs, headers, response bodies, credentials and arbitrary exception text are not persisted.
- Added metadata, URL-sanitization, validation and migration-chain tests. PostgreSQL disposable-CI schema expectations were advanced to 0031 (93 tables, 87 sequences, 570 indexes, 508 constraints); production restored-schema expectations were not changed.
- Crawler audit persistence is not yet connected to the transport or a customer API. Distributed per-tenant/per-host concurrency, durable cancellation, rate/quota enforcement and a reviewed purge process remain gates before endpoint exposure.

Validation boundary:
- The earlier fixture-only CI run #42458901036 has Docker, PostgreSQL smoke and PostgreSQL 18 compatibility jobs passing; full pytest was still running at the last status read.
- CI run #42459069120 failed before pytest. Its migration-policy job found ORM/migration drift (default/index/unique metadata), and its PostgreSQL 18 job found stale expected head 0030. The ORM drift was corrected in subsequent commits; PostgreSQL fixture head and disposable CI schema counts were advanced to 0031.
- The current branch head is newer than those run results. A successful CI result for the exact current head has not yet been observed. Do not report this foundation as validated until CI completes successfully.

Migration 0031 exists only in source/CI. UAT remains at 0029; no UAT/Production migration or deployment, live crawl, live Google request, customer grant, scheduled job, or CMS write was performed. Keep backend PR #121 and frontend PR #71 Draft/unmerged. Vercel deployment quota remains a release constraint; do not attempt repeated Preview deployments.



### Crawler audit CI green · 2026-11-08

Corrected source commit `3a800197cceafa3aa65f0191f2e31c7169565e7f` passed [GitHub Actions run #42459686126](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42459686126): **1192 passed, 7 skipped, 0 failed**. All four jobs passed: Python test suite, PostgreSQL smoke, PostgreSQL 18/Neon compatibility including disposable-schema preflight, and Docker build. Migration Policy and compileall also passed.

The verified changes include robots fixture correction; migration 0031 crawler audit table; tenant/store/site composite scope; sanitized URL host/fingerprint without query or fragment; bounded event fields and explicit caller-supplied retention; updated Alembic head, baseline classification, PostgreSQL test fixture and CI schema expectations.

Validation applies to source commit `3a800197cceafa3aa65f0191f2e31c7169565e7f`. Subsequent commits on the PR branch are documentation-only; the runtime source is unchanged. Current documentation branch head at the time of this entry is `4c06e568f9dfed8cd4329d775ef894c35e1cb31e`.

Release boundary remains unchanged: migration 0031 is not applied to UAT or Production; UAT remains at 0029. No customer crawl, live Google request, scheduled job, customer grant, CMS write or deployment was performed. Backend PR #121 and frontend PR #71 remain Draft/unmerged. Current Vercel UAT API and TelBot checks fail due to the free-plan deployment-rate limit; the website check passes. Do not retry deployments until the quota window resets and a deliberate grouped release is approved.

Next engineering gate: add distributed tenant/host concurrency and quota controls, then wire the audit writer into a bounded crawl orchestration service. Only after those controls and explicit customer consent should a default-off technical-audit endpoint be exposed.



### Distributed crawler concurrency foundation · 2026-11-08

Extended migration 0031 with `seo_crawl_leases` and added `app/seo_growth/crawl_leases.py`:

- One active lease per normalized hostname globally, enforced by a unique host constraint.
- Tenant-wide active crawl quota, serialized by locking the tenant row before counting active leases. Default limit is one active crawl per tenant; the internal service accepts only 1–5.
- Cross-tenant first-claim races are resolved through a unique constraint and nested transaction/savepoint; expired host leases can be reclaimed.
- Lease tokens are 256-bit random values stored as 64-character hex, correlated to a UUID crawl ID, and have bounded 30–600 second durations (180 seconds by default).
- Renewal requires the current host/crawl/token tuple and a non-expired lease. Release requires the same current token. The lease table cascades with its site because it is coordination state, not retained audit evidence.
- PostgreSQL row locks and uniqueness provide cross-worker coordination. The helper does not create an API route or start network work; callers must commit the lease transaction before beginning a crawl.
- Disposable PostgreSQL CI schema expectations are now 94 tables, 88 sequences, 574 indexes and 514 constraints. Production/UAT expectations remain untouched.

This is source-only and not yet validated by a CI run for the latest source head. The previous green run #42459686126 validated migration 0031 before the lease table was added. Re-run and complete CI on the new head before treating the expanded migration as validated.

The crawler remains unexposed to customers. A future route must enforce the lease, bounded CrawlBudget, explicit customer consent, site/host ownership, cancellation and audit persistence in one controlled orchestration flow. No UAT/Production migration, deployment, live crawl, Google request, customer grant, scheduled job or CMS write was performed.



### Distributed crawler lease CI green · 2026-11-08

Source commit `68e10af7bbb350c59aef71de3525c0cbe4e0f83b` passed [GitHub Actions run #42460429897](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42460429897): **1206 passed, 7 skipped, 0 failed**. All four jobs passed: Python tests, PostgreSQL smoke, PostgreSQL 18/Neon compatibility with the disposable-schema preflight, and Docker build. Compileall and migration-policy validation also passed.

The validated 0031 source now contains both the credential-free crawler audit event table and the distributed host lease table. Lease behavior covered by tests includes tenant-wide concurrency ceilings, one active lease per normalized hostname, expired lease reclamation, IPv6 host normalization, bounded token/lease duration, renewal and token-checked release. PostgreSQL preflight passed with the expanded disposable CI schema expectations: 94 tables, 88 sequences, 574 indexes and 514 constraints.

This validation applies to source commit `68e10af7bbb350c59aef71de3525c0cbe4e0f83b`. Documentation-only commits followed; runtime source is unchanged. Migration 0031 remains unapplied to UAT and Production. UAT remains at revision 0029. PR #121 remains Draft/unmerged.

The crawler transport and audit/lease foundations are still not wired to a customer-facing crawl route. Before exposure, the remaining work is bounded crawl orchestration, URL discovery/sitemap policy, cancellation, page-level analysis persistence, retention/purge approval, explicit customer consent and final tenant/host authority revalidation. No live crawl, live Google request, scheduled job, customer grant, CMS write or deployment was performed. Vercel UAT API/TelBot checks remain blocked by the free-plan deployment-rate limit; do not retry until quota reset and deliberate grouped deployment.


### Crawl preview budget preflight CI green · 2026-11-08

The crawler path-scope transport fix and crawl-preview budget preflight are now validated on the exact feature branch:

- `e9addd80940895167f642b2a0447d87c5bfcdbc8` passes the allowed path prefix into the redirect transport so the initial page and every same-origin redirect are checked against the configured path scope.
- CI run [#42473221274](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42473221274) exposed one regression-test failure: the preview orchestrator called the page fetch callback before checking the global page budget.
- `03cd1faa5778b949a11f14108a7514b019f17ee5` moves elapsed-time, global-page and per-host-page budget checks ahead of the lease callback and transport invocation. Host-page budget exhaustion is classified as a truncated crawl, not a page failure.
- `c2ff5e791e54048ef1cf4e71507a9b64e521ff07` adds a dedicated host-budget preflight regression test.

Validation: CI run [#42473693841](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42473693841) passed **1218 tests, 7 skipped, 0 failed**. The follow-up run [#42473755764](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42473755764), including the new host-budget test, passed **1219 tests, 7 skipped, 0 failed**. Docker build, PostgreSQL smoke, PostgreSQL 18/Neon compatibility and disposable-schema preflight all passed. Compileall and migration-policy checks passed. Three non-blocking deprecation warnings remain.

The latest validated source head is `c2ff5e791e54048ef1cf4e71507a9b64e521ff07`. This is source/CI validation only. Migration 0031 remains unapplied; UAT remains at revision 0029. Backend PR #121 and frontend PR #71 remain Draft/unmerged. No Vercel deployment, customer crawl, live Google request, customer grant, scheduled job, CMS write or Production change was performed. The Vercel free-plan daily deployment limit remains a release constraint; do not retry Preview deployments until quota reset and a deliberate grouped release.

Next engineering gates: enforce the aggregate byte budget while streaming (rather than only after a response completes), make link-discovery truncation explicit in crawl coverage, then design a cancellable durable crawl job and customer-consent lifecycle. Do not expose a customer crawl endpoint until these controls, page-observation persistence, retention/purge approval and final tenant/site authority revalidation are complete.


### Aggregate byte budget and coverage reporting CI green · 2026-11-08

The crawler now enforces the aggregate response-byte budget during transport, not only after a response completes:

- Each robots/page response is capped by the remaining crawl-wide byte budget as well as its per-response cap.
- Declared Content-Length is rejected before body reads when it exceeds the remaining cap. For responses without Content-Length, the transport never probes one byte beyond the cap; a full cap is conservatively treated as oversized.
- Bytes received by rejected/partial responses are accounted against the aggregate budget and retained in sanitized audit metadata. Received bytes are recorded before the elapsed-time check so deadline failures do not erase resource accounting.
- Crawl Preview stops before the next lease callback when aggregate bytes are exhausted.
- Per-page link discovery is capped at 500 eligible links and reports `link_discovery_truncated`; coverage is marked truncated rather than complete.
- Canonical URLs in crawl output are normalized and stripped of query strings and fragments.

CI run [#42475087348](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42475087348) passed **1223 tests, 7 skipped, 0 failed**. The latest source head, `c3b049aed1c4cdc0f77d8fccbbaa2dc5cbf00fc2`, was validated by CI run [#42475149729](https://github.com/namach2727-coder/Sales-Agent/actions/runs/42475149729): **1224 passed, 7 skipped, 0 failed**. Docker build, PostgreSQL smoke, PostgreSQL 18/Neon compatibility and disposable-schema preflight all passed. Compileall and migration-policy checks passed. Three non-blocking deprecation warnings remain.

This remains internal source/CI validation. No customer-facing crawler endpoint is exposed. Migration 0031 remains unapplied; UAT remains at revision 0029. Backend PR #121 and frontend PR #71 remain Draft/unmerged. No Vercel deployment, customer crawl, live Google request, customer grant, scheduled job, CMS write or Production change was performed. Vercel's free-plan daily deployment limit remains in effect; do not retry Preview deployments until quota reset and a deliberate grouped release.

Next release gates: persist customer crawler consent and revocation; define and approve audit/page-observation retention and purge behavior; design cancellable durable crawl jobs and worker execution; persist page observations under tenant/site scope; then add a customer API behind default-off flags. Do not expose the crawler to customers before those controls and final tenant/site authority checks are implemented and validated.
