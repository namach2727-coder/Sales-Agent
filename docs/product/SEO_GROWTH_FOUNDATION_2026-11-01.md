> **Current continuation:** F1 onboarding and customer UI are now implemented in the existing DRAFT PRs #121/#71. The original F0-only descriptions below are historical. See [F1 implementation and gates](SEO_GROWTH_F1_ONBOARDING_2026-11-01.md). No deployment, real customer Google consent, commercial billing or website automation is claimed.

# DirectPilot SEO Growth — Commercial Service Foundation
> 2026-11-01 | **F0 development / review only** — not deployed, no customer OAuth, no database migration, no customer website writes. Owner authorized a NEW commercial SEO capability, not changes to Instagram MVP or existing SEO Production.

## Product outcome
A customer can purchase a separate DirectPilot SEO module, log into the existing multi-tenant customer panel, connect Google Search Console using **their own Google account**, choose only properties they are authorized to access, see verifiable traffic/search data, review SEO improvement proposals and — after adding a separate authorized CMS/repository connection — approve safe website improvements with deployment evidence and rollback.

**No guaranteed ranking, indexing or clicks.** Search Console data is diagnostic. SEO improvements have uncertainty, measurement delay, algorithm/seasonality effects and Google policies.

## UX flow (mobile-first, Persian RTL)
1. Customer chooses **SEO Growth** independent of the Instagram subscription.
2. **Connect Google** opens Google's official OAuth consent, scope **webmasters.readonly**. No manual service-account JSON and no customer Google credentials in DirectPilot forms.
3. OAuth callback validates one-time state, PKCE and current tenant user. Server lists properties from Google **Sites.list**; user explicitly chooses a site.
4. Initial sync loads settled daily clicks, impressions, CTR, position; separately imports query/page/device/country slices and optional URL inspection. Loading, empty, no permission, stale data, revoked grant and API quota states are visually distinct.
5. Dashboard shows evidence-linked findings and drafts of specific SEO tasks. No fabricated traffic forecast. Filter by website, dates, query, page and status.
6. Optional **CMS connection** (WordPress first, repository integration later) enables an **approval queue** with affected URLs, old/new diff, risk classification, permissions, execution log and rollback.
7. Measure observed 28-day post-change outcomes versus prior comparable windows, disclose missing data and avoid claiming causality from a simple before/after.

## Google API reality
- **Search Console Sites.list** returns user-authorized property IDs and permission levels: https://developers.google.com/webmaster-tools/v1/sites/list
- **Search Analytics** is read-only. It can return top rows rather than all query/page combinations; **days without data are omitted**. Site-level totals come from independent date grouping, never a truncated query-page response: https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- **URL Inspection** reports Google's indexed view, not the current live URL or a request to index anything: https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- **Indexing API applies only to JobPosting and BroadcastEvent in VideoObject**, not ordinary site pages: https://developers.google.com/search/apis/indexing-api/v3/using-api
- Respect Search Console per-site/per-user/per-project quotas: https://developers.google.com/webmaster-tools/limits
- Commercial Google OAuth requesting sensitive scopes can require verification, consent branding, privacy policy, domain proof and security preparation. Separate UAT and Production Google projects: https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
- Google warns of SEO tools that guarantee outcomes and penalizes scaled low-value content: https://developers.google.com/search/docs/essentials/spam-policies

## Architecture: reuse the existing DirectPilot identity, not the private MCP
- Backend: FastAPI, SQLAlchemy/Alembic, PostgreSQL, existing Tenant / Store / membership / RBAC / SaaS module catalogue. Source: app/tenant_management/context.py, app/commerce/service.py, app/authentication/dependencies.py, app/module_catalog.py.
- Customer UI: existing Next.js/Vinext React customer portal and session cookie API. **app/admin/seo** is *operator SEO*, not customer SEO. Do not expose it to commercial tenants.
- Private DirectPilot GSC MCP currently uses operator-only **sc-domain:directpilot.ir** service account and WorkOS subject; it MUST NOT supply cross-customer access. This new commercial module needs dedicated Google OAuth per customer and a separate data boundary.
- Product entitlement is a **new optional seo_growth module**; not dependent on Instagram purchase. Prices/packages are hypotheses, do not silently change existing plan prices or DB seeds.

## F0 implementation committed on this feature branch
- app/seo_growth/google_client.py: safe Google-only read-only provider boundary; PKCE S256 + state generators, fixed redirect authorization, code exchange and refresh (no token/body logging), Sites.list (ignores unverified properties), date/query/page Search Analytics, read-only indexed URL inspection. Only a calling tenant-safe service may persist/use credentials. No database/network side effects on import.
- app/seo_growth/analysis.py: pure deterministic data-contract engine, period totals only from daily rows, explicitly missing dates, impression-weighted average position, bounded prioritized proposal-only SEO finding list. No estimated uplift and **no site mutation**.
- tests/test_seo_growth_google_client.py and tests/test_seo_growth_analysis.py use synthetic Google responses and the owner-supplied historic 2026-10-25..30 GSC example, with missing Oct 31 intentionally unknown.
**F0 is NOT a working customer connector**. It has no HTTP router, encrypted token DB, OAuth callback persistence, front-end connection UI or billing integration. Do not advertise it as ready for sign-ups.

## F1 architecture: secure site onboarding (not implemented)
Proposed tables to create in a **future additive Alembic migration** after schema review:
- seo_google_connections: tenant_id, user_id, encrypted refresh token, verified scope, consent/version, expiry/status, disconnected_at and key version.
- seo_oauth_attempts: tenant_id, user_id, one-time SHA-256 state digest, encrypted PKCE verifier, expiry, used_at (replay prevention); fixed callback destination and CSRF validation.
- seo_sites: tenant_id, optional store_id, connection_id, Google-provided exact property ID and permission level; tenant-scoped uniqueness.
- seo_daily_metrics / seo_query_page_metrics: site/tenant/source/date, freshness, Google top-row limitations, bounded storage and idempotent import.
- seo_findings / seo_change_proposals / seo_action_audit: evidence, proposal, customer authorization, execution/rollback status; NEVER store secret values in audit.

**Security gates:** tenant/store access resolved from trusted principal not body; separate Google OAuth UAT/Prod clients; exact readonly scope; one-time state+PKCE; encrypt refresh tokens (existing Fernet/KMS pattern), support revoke and delete; recheck property access on sync; quota/rate limits; idempotent jobs; no arbitrary URL fetching/SSRF; cross-tenant test fixtures; feature flag default OFF and module entitlement before any customer route; audit all changes.

No Google OAuth verification for external production tenants is claimed. The operator's existing service account is neither a replacement for OAuth nor a valid way to onboard arbitrary websites.

## Automated SEO work: stepwise and approved
- **F2 analysis:** report missing days as unknown (not zero), show real GSC source/period for every finding, evaluate page/query opportunities and indexed URL problems. AI can explain findings, but must not fabricate causes.
- **F3 proposals:** prepare page title/meta/schema/internal linking suggestions, content briefs and error remediation plans with preview/diff and explicit customer approval. Rank changes are uncertain.
- **F4 execution:** authorized WordPress adapter first; repository/provider adapter later. Validate site ownership and minimal write scope, perform reversible bounded changes, record before/after, verify deployment and support rollback. Do not auto-create SEO-spam pages or modify robots/canonical across a site without explicit review.
- **F5 commercial release:** independent SEO subscription/limits; Google consent app verification; privacy/terms, disconnect/data deletion, logging, quota budgets, user UAT, cost-based pricing. No invented plan prices.

## Proposed packages (pricing TBD)
| Package | Entitlement |
|---|---|
| Monitor | One Google-verified site, scheduled read-only metrics and diagnostic tasks |
| Grow | Several sites, daily sync, deeper comparisons, evidence-based change queue |
| Autopilot | Grow plus approved CMS connection, change preview, controlled execution and rollback |
Actual fees and included limits require cost measurements and explicit commercial decision.

## KPIs and safety guardrails
- Activation: verified site + first settled GSC sync / all started customer connection attempts; instrument each step separately.
- Organic results: settled 28-day GSC clicks and impressions per property compared with prior equal window, while reporting changed coverage/seasonality.
- Approved-fix completion: executed and independently verified / approved proposed actions; track rolled back and pending.
- Guardrails: zero cross-tenant leakage, zero unauthorized publishing, no secret exposure, percentage stale/missing data, quotas, disconnection/revoke success, successful rollback. Set numeric goals only after pilot baseline; **no invented uplift targets**.

## Acceptance and release gates
| Foundation | Deliverable | Exit gate |
|---|---|---|
| F0 | Tested Google adapter and proposal-only engine | Unit tests, no secrets, code review |
| F1 | Customer OAuth + site selection + persistence | Tenant isolation, replay/missing scope denial, encrypted token, revoke and UAT tests |
| F2 | Mobile-first customer SEO dashboard + sync | GSC quotas, date completeness, source-linked opportunities |
| F3 | Draft task workflow and user approval | No side effects without authorized approval |
| F4 | CMS auto-fix adapter | Per-site write consent, reversible change, audit and rollback |
| F5 | Commercial billing and release | Google OAuth verification as applicable, privacy, cost limits, explicit owner Production approval |

**Do not merge this foundation branch into production or run migrations while integration and consent are unverified.** Do not touch current directpilot.ir, Instagram/Meta app, operator SEO dashboard, existing GSC REST Production, MCP WorkOS settings or private ChatGPT plugin.

## Immediate next engineering tickets
1. Tenant-safe Google OAuth state + callback, encrypted token persistence and per-tenant site table; add addon entitlement and feature flag.
2. Customer SEO Growth portal/mobile onboarding, connect/reconnect/disconnect, selectable Google-verified properties.
3. Quota-aware scheduled ingestion, missing-date visibility and findings UI.
4. Customer approved WordPress edits with previews, rollback and audit trail.
5. Pilot, cost/price validation, Google verification, commercial launch review.
