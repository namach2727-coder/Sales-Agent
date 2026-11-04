# DirectPilot SEO Service — Product and Technical Architecture
Date: 2026-11-04
Status: foundation proposal; no runtime implementation or customer-facing release
Repository: `namach2727-coder/Sales-Agent`
Branch: `feature/seo-service-foundation-20261104`

## 1. Product boundary

This is a separate, multi-tenant commercial service. It is not the DirectPilot public-site SEO workstream, the current platform-admin SEO report, or the private GSC MCP integration.

A customer must be able to:
1. Sign in to their existing DirectPilot account.
2. Connect a Google account through Google's OAuth 2.0 authorization-code flow.
3. Select a Search Console property that Google reports as accessible to that account.
4. Run an initial audit and see evidence-backed findings, priorities, and recommended actions.
5. Review, approve, defer, or reject recommendations.
6. In a later release, authorize supported changes through an explicit, reversible integration (for example a CMS connector). No arbitrary website code changes are allowed.

The initial product does not promise ranking gains, full Google indexing, or automatic fixes without customer approval.

## 2. Existing architecture to reuse

The Backend already provides:
- authenticated principals and cookie-backed sessions;
- tenant/store membership and store-level access checks;
- RBAC permissions;
- subscription and store-module entitlement primitives;
- Fernet-based credential encryption for Instagram OAuth credentials;
- credential-free audit-log conventions and linear Alembic migrations.

The current public-site `/admin/seo` dashboard is platform-super-admin-only and reads one configured GSC source. It is not a tenant SEO workspace. The current MCP/GSC plugin workstream is separate and must not be used as the customer-facing authorization model.

## 3. Proposed service architecture

### Backend bounded context

Create an isolated `app/seo_service/` package with:
- `models.py`: Google account connection, Search Console property, OAuth state, audit run, finding, recommendation, recommendation decision, and optional crawl snapshot.
- `provider.py`: Google OAuth and Search Console API client behind provider interfaces.
- `security.py`: provider-specific token cipher boundary and state hashing/validation.
- `service.py`: tenant/store-scoped orchestration and entitlement checks.
- `router.py`: authenticated customer API.
- `schemas.py`: typed request/response contracts.

Use existing `AuthenticatedPrincipal`, `CommerceService.customer_scope`, tenant/store authorization, `module_enabled`, and audit conventions. Every read/write query must include the resolved tenant and store IDs. Never accept tenant/store integer IDs from an untrusted body as authorization.

### Google authorization

- OAuth authorization-code flow; state is cryptographically random, stored as a digest, single-use, short-lived, and bound to initiating user + tenant + store.
- Request only `https://www.googleapis.com/auth/webmasters.readonly` for the initial read-only release.
- Request offline access only where refresh-token operation is required; encrypt refresh tokens at rest with a dedicated SEO Google token key, separate from the Instagram key.
- Keep client ID, client secret, redirect URI, encryption key and callback configuration in deployment secrets/configuration only.
- Callback must validate state, active tenant/store, active membership and current user identity before persisting credentials.
- Revoke/disconnect must clear encrypted credentials and invalidate connection state. Never log access tokens, refresh tokens, OAuth codes, state values, email addresses, or raw customer query data.

### Search Console property control

- Discover properties using the authenticated Google account's `sites.list`; do not let the browser submit an arbitrary property and assume ownership.
- Persist the selected exact property identifier returned by Google (for example `sc-domain:example.com` or a URL-prefix property).
- Re-check access when provider errors indicate revoked permission.
- Search Analytics queries use bounded date ranges, pagination, bounded row limits, and explicit search type. Preserve source freshness and aggregation metadata.
- URL Inspection is a separate capability and must not be represented as a live-page test. It reports the indexed version known to Google.

### Technical crawl

Search Console is not a full technical crawler. Add a separate, rate-limited public-site crawler for customer-authorized domains:
- start only from the verified selected property and its declared sitemap/robots rules;
- enforce public HTTP(S), DNS/IP checks, redirect limits, private/reserved IP blocking, response-size and content-type limits, crawl depth/page caps, per-host concurrency and timeouts;
- do not fetch arbitrary user-supplied URLs or internal/private network addresses;
- identify canonical, robots directives, status codes, titles, headings, internal links, sitemap coverage, and basic structured-data presence;
- store evidence and crawl timestamps so each recommendation is explainable and reproducible.

Do not claim Lighthouse/Core Web Vitals or backlink data unless a separately verified provider/source is implemented.

## 4. Data model (proposed; migration not yet created)

- `seo_google_connections`: tenant_id, store_id, connected_by_user_id, Google subject/email metadata (non-secret), encrypted refresh token, token key version, granted scopes, status, connected_at, last_verified_at, disconnected_at.
- `seo_google_oauth_states`: state_digest, tenant_id, store_id, initiated_by_user_id, expires_at, consumed_at.
- `seo_search_properties`: tenant_id, store_id, connection_id, exact provider property URL, permission level, selected flag, verification timestamp.
- `seo_audit_runs`: tenant_id, store_id, property_id, status, requested range, source freshness, started/completed timestamps, safe error code.
- `seo_findings`: tenant_id, store_id, audit_run_id, category, severity, evidence JSON, source, affected URL/query, first_seen_at, last_seen_at.
- `seo_recommendations`: tenant_id, store_id, finding_id, action type, explanation, expected impact category (not numeric promise), implementation method, risk, approval state.
- `seo_recommendation_events`: tenant_id, store_id, recommendation_id, actor, decision, timestamp, audit metadata.
- `seo_crawl_pages` (optional phase): tenant_id, store_id, audit_run_id, URL, status, canonical, robots state, title, H1, crawl timestamp, response metadata.

All tables use internal foreign keys, tenant/store ownership constraints and indexes. Public APIs expose opaque public IDs, not integer IDs. Tokens and raw OAuth responses are never returned to clients.

## 5. Proposed customer API

- `POST /api/v1/seo/google/connect` — create state and return Google authorization URL.
- `GET /api/v1/seo/google/callback` — consume state and securely store connection.
- `GET /api/v1/seo/google/status` — safe connection status.
- `GET /api/v1/seo/google/properties` — list accessible properties.
- `POST /api/v1/seo/properties` — select one property from the provider-returned list.
- `DELETE /api/v1/seo/google/connection` — disconnect/revoke local stored credential.
- `POST /api/v1/seo/audits` — queue a bounded audit run.
- `GET /api/v1/seo/audits/{public_id}` — audit progress and summary.
- `GET /api/v1/seo/findings` — filter findings by severity/category/status.
- `GET /api/v1/seo/recommendations` — list actionable recommendations.
- `POST /api/v1/seo/recommendations/{public_id}/decision` — approve, reject, or defer a recommendation.

The first release is read-only: approval records intent but does not mutate a customer's website. Website mutation is a later, separately authorized capability.

## 6. Audit and recommendation methodology

Use independent evidence categories:
1. Search performance: query/page/country/device/date clicks, impressions, CTR, position.
2. Search Console property and sitemap evidence.
3. URL Inspection evidence for explicitly inspected URLs.
4. Technical crawl evidence from the controlled crawler.
5. Conversion/analytics evidence only when a customer separately connects a supported analytics source.

Recommendations must include: issue, evidence, affected URLs/queries, why it matters, suggested action, implementation complexity/risk, confidence, and the data timestamp. Distinguish observed facts from model-generated interpretation. Do not invent search volume, keyword difficulty, backlinks, traffic forecasts, ranking improvements, or conversion lift.

## 7. Entitlement and commercial boundary

Do not silently add this service to existing Automation or AI Assistant plans. Add a dedicated SEO service/module and explicit quotas only after the owner confirms the commercial packaging. Candidate limits include connected properties, pages per crawl, audit frequency, history retention, and recommendation volume. Enforce entitlements server-side on every operation; UI visibility is not authorization.

## 8. Delivery phases

- **Phase 0 — architecture and safety:** this document; confirm product boundary, provider configuration, migration and release isolation.
- **Phase 1 — GSC connection:** Google OAuth, secure refresh-token storage, property discovery/selection, disconnect, tenant isolation and tests.
- **Phase 2 — data and audit:** Search Analytics ingestion, sitemap/property checks, URL Inspection where available, bounded technical crawler, evidence model.
- **Phase 3 — recommendations:** deterministic rule engine first, explainable findings, priority scoring, customer decisions and history.
- **Phase 4 — implementation integrations:** CMS-specific adapters, preview/diff, backups, explicit approval, idempotency and rollback. No generic remote code execution.
- **Phase 5 — commercial readiness:** dedicated plans/quotas, onboarding, billing, support and retention controls.

## 9. Release and safety gates

- Work only on the feature branch until reviewed.
- No production deployment, database migration against persistent UAT/Production, or environment-secret changes in this foundation step.
- Add focused tests for OAuth state replay/expiry, wrong user, cross-tenant access, property spoofing, encrypted token handling, revoked access, pagination and quota limits.
- Keep the existing SEO REST/dashboard and isolated MCP service untouched.
- A merged commit, CI pass, deployment READY state, Google OAuth consent, live customer data, and customer acceptance are separate gates.

## 10. Owner decisions still required before commercial activation

1. Initial SEO service plan, trial duration, price, and included quotas.
2. Whether one tenant may connect multiple stores/properties and whether each store has a separate Google account.
3. Supported first CMS for approved implementation (WordPress is a candidate, not assumed).
4. Whether customer recommendations are manual-only in the first paid release (recommended) or require any narrowly scoped automatic changes.
5. Data retention and customer deletion policy for query, crawl, and audit evidence.

## References

- Google Search Analytics API: https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- Google Search Console API reference: https://developers.google.com/webmaster-tools/v1/api_reference_index
- Google URL Inspection API: https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- DirectPilot backend tenant/store architecture: `docs/architecture/tenant-store-management.md`
- DirectPilot backend migration policy: `docs/architecture/database-migrations.md`
