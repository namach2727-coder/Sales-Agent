# DirectPilot SEO Platform — product and technical plan



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