# DirectPilot SEO Platform — product and technical plan

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
- P0 — F2b durability: validate explicit sync, persisted sync history and persisted analysis; keep flags default-off.
- P1 — Technical audit core: deterministic HTML parser and tests; implementation started in app/seo_growth/technical_audit.py and tests/test_seo_growth_technical_audit.py; CI validation pending. No outbound requests.
- P2 — Safe crawler: SSRF-resistant fetch layer, robots policy, bounded crawl and site-level audit records.
- P3 — Business Profile: tenant/store/site-scoped business profile and up to three validated competitor URLs.
- P4 — Intelligence/Action Center: evidence-backed rules, prioritization, action status and report UI.
- P5 — Performance integration: PageSpeed Insights, quotas, caching and source-specific freshness.
- P6 — Continuous improvement: compare subsequent GSC/crawl snapshots with prior baselines and record approved changes.

## Explicit non-goals until separately approved
No automatic CMS edits, automatic publishing, customer billing/plan changes, scheduler or backfill, data-retention TTL/purge, UAT or Production migration/deployment, or enabling SEO flags. PR #121 backend and PR #71 frontend remain Draft/unmerged. UAT schema remains 0029; source migration 0030 must not be applied to UAT without explicit approval.

## Current source validation
CI run #42012950916, source 52909808babad964da8c19612e12a9837d033a24: 1080 passed, 7 skipped, 3 warnings; all four CI jobs passed. This does not constitute live Google, UAT, or Production acceptance.
