# SEO Growth F2a — bounded customer analysis preview

Owner-authorized continuation of the independent commercial SEO product. Backend DRAFT PR #121 and frontend DRAFT PR #71 now add an explicit report preview to the existing customer SEO workspace. This is implemented development code, not an activated customer integration. Dedicated Google OAuth/configuration and real customer acceptance remain pending. The separate public website keyword-content release is preserved; this task does not change that content or release Production.

## Customer behavior

An eligible customer opens `/dashboard/seo`, selects their authorized workspace and a connected site, then explicitly requests its 28-day report. The report displays the recent and prior equal windows, date coverage, reported clicks/impressions, recomputed CTR, impression-weighted position and bounded query/page review candidates. A day without a GSC row is unknown, not zero. A period with no reported date rows has null totals; an explicitly reported zero remains zero.

The preview exists only in the response and current page state. Leaving the workspace/page or successfully changing the connection/site clears it, including when a secondary status refresh fails. No metric snapshot, report history, successful-sync timestamp, scheduled ingestion, automatic website edit or ranking forecast is introduced. `sync_status` remains `not_started`; this preview is not a completed background sync.

## Implemented API and data contract

POST `/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/seo/sites/{site_public_id}/analysis-preview`, with exactly `{}`. Caller-supplied dates, filters, property names and extra fields are rejected. Responses and failures are no-store/no-referrer. Existing HttpOnly authentication, exact configured Origin, `X-CSRF-Token: seo`, current workspace write authority, active tenant/store and explicit unexpired SEO pilot grant are required. A platform administrator cannot use another user's Google credential by knowing their site ID.

The response identifies `google_search_console`, `data_state: final`, `search_type: web`, `timezone: America/Los_Angeles`, actual property/period and request time. The selected recent window ends three Pacific calendar days before the request; this is a conservative window-selection rule, not a promise that every date has data. The previous window is the immediately preceding 28 days.

- One token refresh, one Google property-list permission check, one unfiltered date query for both windows (56-row bound) and one recent query/page sample (500-row bound). Calls use fixed Google hosts; no customer website is fetched. There is no automatic provider or POST retry.
- The provider explicitly requests finalized Web Search data and property aggregation for non-page dimensions; query/page grouping uses auto aggregation. An explicit unexpected daily aggregation fails closed.
- Totals come only from date rows. CTR is total clicks / total impressions. Position is weighted by impressions, with null when undefined. Query/page rows never supply property totals. Fractional counts, invalid/nonfinite values, unsafe integer ranges, malformed/duplicate/out-of-window dates, duplicate query/page pairs and unsafe/foreign page URLs are rejected as sanitized `google_invalid_response`.
- The daily series contains all 28 requested dates with null metrics for omitted rows. Percentage changes and other deltas are suppressed if either window lacks a date. Percentage change is also null when its previous denominator is zero. CTR differences use percentage points; position differences are current minus previous. No causal attribution or seasonality adjustment is claimed.
- At most 20 proposal-only opportunities are produced by the existing deterministic triage engine. The sample is Google's top rows, sorted by clicks before local selection, and is not exhaustive even below the 500-row cap. Reaching the cap is disclosed. The existing triage thresholds are heuristics, not universal CTR benchmarks or a ranking guarantee.
- The API adds backward-compatible `analysis_preview_enabled` status and `analysis_available` site metadata. The latter identifies connected sites using the current user's own Google connection; it does not replace endpoint RBAC, feature or entitlement checks. Older responses lacking these fields keep the new UI hidden.

## Permission, quota and lifecycle controls

`SEO_ANALYSIS_PREVIEW_ENABLED=false` is a separate default-off backend flag, mirrored in all existing SEO configuration examples. `SEO_GROWTH_ENABLED` and the frontend SEO build flag still apply. No cloud setting or credential is changed by the code.

The existing store-row lock serializes admission with other SEO lifecycle writes. Current tenant/store permission is resolved after acquiring the lock, including if authority changed while waiting. Before Google is called, `seo.analysis_preview_started` commits an attempt. Each workspace has a fixed pilot limit of at least 60 seconds between requests and at most 12 starts in a rolling 24 hours. This is an internal preview request budget, not a paid subscription or a guarantee that project-wide Google quotas cannot be reached. Failed/time-out attempts consume that budget.

No database lock is held during HTTP. Before returning any report, the service reacquires the lock, refreshes request-local ORM state and checks current role/membership, operational scope, feature/grant, site status, connection owner/status and exact encrypted credential. A concurrent disconnect, reconnect, suspension or revocation prevents return. Only explicit Google authorization expiry marks the same unchanged credential as needing reauthorization; quota/transient errors do not. Expiry of an older credential cannot disable a concurrently replaced connection.

Completed/failed events contain only the public site identifier and, on failure, a sanitized code. Query strings, page metrics, raw reports, provider bodies and OAuth secrets are not stored in audit. A report can be lost to a browser/proxy timeout because this phase has no durable report job or recovery snapshot. UI transport waits up to 60 seconds, offers manual retry, and performs no duplicate POST. Google/platform timeouts remain possible.

`tzdata==2026.6` supplies the Pacific calendar on systems without IANA timezone files. A focused fallback test removes the system timezone path and verifies the Pacific date/offset. There is no new cloud service, database table, Alembic revision or live migration. Source and original UAT schema remain **0029_seo_pilot_revision**. The already completed 0027→0029 migration must not be replayed.

## Verification and release boundary

- Full backend **1061 passed, 7 skipped, zero failed**; local migration naming/graph, schema drift and base→head→base→head checks PASS at the unchanged single head 0029.
- Focused report/provider checks: **53 passed**. They cover totals versus query samples, missing/zero dates, undefined percentages, row/URL/number bounds, CSRF/flags/grant, current Google property permission, cooldown/daily budget, cross-scope/user isolation, in-flight authority/credential changes, post-lock revocation and timezone fallback.
- Frontend full suite: **297 passed**, zero failed. Five focused rendered report/onboarding cases pass, including explicit scoped requests, pending duplicate-submit denial, error states without invented zeros, disabled action and successful disconnect clearing a report even after failed status refresh. TypeScript, changed-file ESLint and UAT-flag Next webpack build pass. These are offline synthetic API/Google cases, not visual browser/mobile or real Google acceptance.
- The tested older frontend feature checkout retains a pre-existing full-lint error in unchanged private operator `components/admin-seo.tsx`; this task's files pass their separate lint check. Independent main fixes and public website work are preserved.
- Current backend-main `a83488dbe9633652fac2891de760914fc5c2ff18` changes only seven documentation files after the previously synchronized main. Both main and SEO histories are reconciled, with one mandatory top continuity rule. No main runtime change is imported by that synchronization.
- No Production, canonical UAT deployment, provider secret, customer grant, CMS write or live Google consent was performed. The owner-provided Google project name `directpilot-seo` remains setup context; its clients were not inspected through an authenticated console. Previous access attempts are already recorded; this continuation does not loop on the blocked browser.

## Next concrete sequence

1. Review the bounded preview implementation and retain both SEO feature gates off until dedicated UAT configuration is ready.
2. Complete the dedicated UAT Google Web client/consent, callback, independent encryption key and private upstream/database mapping. The current OAuth UI blocker is not solved by this code.
3. Deploy the exact reviewed source to isolated UAT, explicitly enable preview for the authorized pilot, then test real consent/property permission, report coverage, quota/errors, concurrent disconnect and mobile/browser behavior. No schema migration is needed for F2a.
4. Durable metric/report storage, quota-aware scheduled ingestion, retention/deletion policy, project-wide budgets, paid billing and separately authorized CMS approval/rollback remain later work. Do not describe this transient preview as those capabilities.

Primary references checked:

- https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- https://pypi.org/project/tzdata/
