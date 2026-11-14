> **DIRECTPILOT — MANDATORY CONTINUITY AND CHANGE-LOG RULE (owner decision, 2026-10-17).**
> This file is one of the **six mandatory handoff/release artifacts**. On every DirectPilot / DirectPilot TelBot task, the assistant must read current `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`, and `docs/releases/RELEASE_REGISTER.md` **before making changes**; reconcile against actual GitHub/Vercel/Neon state, not chat memory. **After every meaningful change**, update all five main files **and the Release Register** coherently: scope and owner approval, PR/commit, changed artifacts, UAT/Production status, automated and manual evidence, unresolved risks, next action. Keep the current summary easy to scan, preserve history (archive older detail in runbooks; do not delete evidence), and never call code-merged "deployed" or a proposed feature "active". Never publish to Production, touch live data/secrets, or switch Meta/Telegram outbound functionality without specific owner approval. This rule itself MUST remain at the very TOP of each of the six files and must be propagated in any handoff to a new chat.

> **Current infrastructure source of truth — 2026-11-14:** DirectPilot Backend/API and Frontend run on **Vercel**; persistent application data runs on **Neon**. Vercel and Neon are the only active hosting/data platforms in the current architecture. Any older provider references in the chronology below are historical context only and must not be used for current deployment, runtime, database, credential, or incident decisions. Verify live state against the Vercel and Neon projects before operational changes.

## Current implementation-aligned roadmap — 2026-11-09

**Status rule:** this is the concise current roadmap. The previous long-form file is preserved byte-for-byte in docs/runbooks/history/20261109_pre_reconciliation/PROJECT_ROADMAP_2026-11-09_PRE_RECONCILIATION.md and the dated Release Register. A Git merge, passing CI, or READY deployment is not by itself customer acceptance.

### Source baselines inspected

| Workstream | Canonical source | Inspected HEAD / evidence | Interpretation |
|---|---|---|---|
| Backend SaaS | namach2727-coder/Sales-Agent / backend-main | 8062c204d928e8f014ef985c66b5ef3abf6e137c (2026-11-08) | Current backend implementation baseline |
| Public website | namach2727-coder/directpilot-web / main | 1c0bf5cd60c3f9cd863b4f7fb6401325164874ef (2026-11-09) | Current frontend source; newest HEAD production deployment not independently confirmed in this review |
| TelBot backend | Sales-Agent / feature/telegram-managed-bots-spike-20261017 | 70cf3585db0dd006530098b23eca145621a81111 (2026-11-01) | Isolated product branch; not the Instagram SaaS runtime |
| Public SEO evidence | Frontend docs/seo/SEO_POST_RELEASE_CHECK_2026-11-08.md | Live checks recorded 2026-11-08 | Latest reviewed public SEO evidence |

### Product and workstream status

| Workstream | What is present in source | Status to use in planning |
|---|---|---|
| Instagram SaaS core | FastAPI/SQLAlchemy modular backend; automation and AI routing modules; automation-rule runtime; frontend automation workspace; tenant-scoped commerce and admin surfaces | Implemented capabilities are recorded in docs/project-status.md. Do not reopen completed Phase C / D.1 / D.2 items without a new regression or evidence |
| Commerce and payments | Manual card-transfer/receipt workflow; KPay provider and migration 0019; Payexa provider/service and migration 0020; provider routes and tests exist in app/commerce and tests | Source implemented, provider-level live acceptance not established by this documentation review. KPay references remain in code; do not describe KPay as removed or Payexa as the only compiled provider. Production configuration/transaction acceptance must be verified separately |
| Public website SEO | Service landing pages, article CTAs, indexing controls and SEO reporting surfaces; latest main HEAD is newer than the last documented live SEO deployment evidence | PR #76/#77 are recorded merged; #77 deployment dpl_54pQCSuVtEHytFqwZcXsXT35sk8V READY on SHA 1b7d8eabb159c2c3826711a2ad7b91b9ddece560. The later main HEAD 1c0bf5 is source state only until deployment/alias evidence confirms it |
| GSC private MCP | Dedicated Staging and private plugin v0.1.4 are documented; WorkOS/OAuth security preflight 10/10 PASS | Plugin creation and server staging are verified in the dated runbook; ChatGPT Desktop installation, owner OAuth consent and an authenticated gsc_performance call remain NOT VERIFIED |
| TelBot | Isolated backend feature branch and independent UAT product; website main presents custom bot-development portfolio/inquiry flow, not the old universal self-service subscription-builder offer | Keep separate from Instagram Production. Latest branch source exists; deployment, successful authenticated Mini App flow, managed-bot activation and real outbound reply acceptance must be rechecked before calling it operational |
| Commercial multi-tenant SEO service | Separate product direction from public DirectPilot website SEO and the private GSC MCP integration | Do not mark it released or conflate its status with SEO pages, the admin SEO screen, or GSC MCP. Define a separate implementation/release gate before claiming a sellable service |

### Current public SEO measurement baseline

The 2026-11-08 checkpoint reports Search Console property sc-domain:directpilot.ir, Web Search, 2026-10-10..2026-11-06: 22 clicks, 213 impressions, 10.33% CTR, average position 24.35. The matched prior 28-day window reports 13 clicks, 145 impressions, 8.97% CTR, average position 45.59. These windows overlap the 2026-11-02 release; the changes cannot be causally attributed to that release. The three principal service pages had impressions but no clicks in the page breakdown. Treat this as a baseline, not a ranking guarantee or proof of post-release lift. See the frontend post-release checkpoint for query/page, GA4 and sitemap detail.

### Priorities — ordered by evidence and dependency

1. **Release-state reconciliation:** read current GitHub, Vercel aliases, CI and backend runtime evidence before treating the latest source SHA as deployed. Specifically resolve the frontend main 1c0bf5 vs last documented live SEO SHA 1b7d8eab.
2. **Commerce acceptance:** verify configured provider and safe sandbox/test lifecycle for Payexa/KPay without exposing credentials or initiating a real charge. Keep immutable receipt history, tenant ownership and admin audit requirements.
3. **TelBot UAT:** verify exact deployed SHA and domain, Mini App authentication, tenant ownership, existing managed-bot identity/webhook and a controlled end-to-end reply. Do not create a new bot or send live messages without separate approval.
4. **GSC MCP owner connection:** complete ChatGPT Desktop install/WorkOS consent and one authorized read-only tool call. Keep the REST SEO service and Production routes untouched.
5. **SEO measurement:** compare settled post-release Search Console windows and organic signup attribution using matching dimensions; do not deploy daily copy changes from tiny samples.
6. **Commercial SEO product:** keep as an independent discovery/build stream with explicit multi-tenant data isolation, customer authorization, measurable deliverables and a separate release plan.

### Explicitly not authorized by this roadmap

No Production deployment or promotion, merge to backend-main or frontend main, live database migration/write, destructive cleanup, credential rotation, pricing/subscription/payment mutation, Meta/Telegram outbound action, or change to Vercel/legacy hosting provider/Neon configuration. Obtain separate owner approval for each such action.

### Code references

- Backend automation: app/automation_rules/, app/automation/, tests/test_automation_rule_runtime.py, tests/test_automation_rules.py.
- Backend commerce: app/commerce/, alembic/versions/0019_kpay_payment_gateway.py, alembic/versions/0020_payexa_verification_token.py, tests/test_kpay_provider.py, tests/test_payexa_provider.py, tests/test_payexa_commerce.py.
- Frontend: components/automation-rules-workspace.tsx, components/admin-commerce.tsx, components/admin-seo.tsx, app/telbot/, docs/seo/SEO_POST_RELEASE_CHECK_2026-11-08.md.
- TelBot UAT: docs/TELBOT_STUDIO_20261101.md and Sales-Agent isolated feature branch.
- GSC MCP: docs/seo/GSC_MCP_CONNECTION_STATUS_2026-10-29.md, GSC_MCP_DESKTOP_CONNECTION_RUNBOOK_2026-10-31.md, GSC_MCP_RELEASE_GATE_2026-10-31.md.


### PUBLIC-SEO-PR84-20261109 — frontend pricing-page copy PR status

The owner requested repository-first continuity, source/documentation reconciliation, and an SEO documentation update after the frontend pricing-page work. Frontend `namach2727-coder/directpilot-web` is the public SEO source; Backend `namach2727-coder/Sales-Agent` on `backend-main` carries the six canonical handoff/release files. Those six files are not present in the frontend repo; frontend SEO references are under `docs/seo/`.

Frontend PR [#84](https://github.com/namach2727-coder/directpilot-web/pull/84) remains OPEN / UNMERGED on `seo/pricing-commercial-intent-2026-11`, head `7e6c2cb54f04a5f4078c53c5260662429b280462`, based on `main` `1c0bf5cd60c3f9cd863b4f7fb6401325164874ef`. Only `app/[...slug]/page.tsx` changed. Pricing copy is now formatted readable JSX; it emphasizes choice between Automation and AI Assistant, distinguishes inbound DM from comment-triggered private reply, explains trial evaluation and payment verification, and removes repetitive copy/links. Dynamic API/SSR price cards, the interactive Pricing component, FAQ arrays and SoftwareApplication/FAQPage JSON-LD remain unchanged. DM and comment landing pages/keyword ownership were not changed.

Latest Vercel status for the PR head: both `Vercel – directpilot-web` and `Vercel – directpilot-gsc-mcp` are FAILURE with `build-rate-limit`. This is a hosted build blocker, not evidence of code compilation failure. No passing Preview/build, merge, Production deployment, alias update or post-PR Google result is established. No tests/type-check were run during this docs-only follow-up. Do not hide or downgrade this failed status.

The frontend SEO checkpoint `docs/seo/SEO_POST_RELEASE_CHECK_2026-11-08.md` remains the evidence baseline: Search Console rows through 2026-11-06; its 28-day totals predate the Nov 9 PR #84 copy change and cannot measure its effect. The owner-provided Search Console screenshots confirm /pricing is indexed and its Breadcrumb and Software Apps items are valid; the two SoftwareApplication properties shown as missing are optional warnings. Existing noindex/robots policy remains unchanged: experimental TelBot stays noindex; auth/dashboard/payment routes remain excluded; prelaunch Web Design/TelBot content stays noindex.

Next: resolve the Vercel build-rate-limit only through the existing approved no-cost/manual project workflow, without global setting/plan changes. After successful Preview, verify rendered cards, loading state, copy and JSON-LD; then update the frontend SEO post-release checkpoint and measure only with settled comparable GSC windows. Merge and Production remain separate gates. No deployment is performed by this documentation update.


### PUBLIC-SEO-PR84-RECONCILIATION-20261111 — current deployment and measurement follow-up

- **Current public Production:** Vercel read confirms `directpilot-web` deployment `dpl_3rf9syfjYbJgNAKeihEiTRvTZSKF` is READY, target=production, ref=`main`, SHA `06e3381fb77773d449fc61a44991a802d4d037ec`; aliases `directpilot.ir` and `www.directpilot.ir` both resolve to it. Commit message is an automation-capacity entitlement fix, not an SEO release. This supersedes the older assumption that the newest verified Production deployment was main `1c0bf5cd`, but does not imply PR #84 was deployed or browser/Google acceptance passed.
- **Frontend PR #84:** remains OPEN/UNMERGED, head `7e6c2cb54f04a5f4078c53c5260662429b280462`, base `1c0bf5cd60c3f9cd863b4f7fb6401325164874ef`, one runtime file `app/[...slug]/page.tsx`. Latest retrieved Vercel contexts remain FAILURE for both `Vercel – directpilot-web` and `Vercel – directpilot-gsc-mcp` with build-rate-limit. No successful PR84 Preview/build is verified.
- **Frontend docs PR #85:** remains OPEN; retrieved head `fce516961523894b80b8e47ddd873f3af911ca58`. `Vercel – directpilot-web` is SUCCESS; `Vercel – directpilot-gsc-mcp` is FAILURE. Its frontend docs deployment was intentionally canceled by the Ignored Build Step because the branch is not main/UAT; this is not a failed public-site build. Do not conflate the separate GSC project status with website SEO validation.
- **GSC measurement:** Windsor pull `2026-10-14..2026-11-11` returned 89 query/page/date rows through Nov 8; no rows Nov 9–11 are not zeros. The key pricing/comment/free-page signals remain low volume (mostly one impression per observation), so no further copy change or causal impact claim is justified. GSC Wizard remains payment_required. Web search snapshots confirm page-intent separation but are not fresh live HTML; robots/sitemap and direct pricing fetch could not be re-verified in this pass.
- **Decision:** retain existing keyword ownership and noindex policy. No SEO runtime change, merge, Production deployment, project-setting change, plan change, DB or secret change was made. Keep PR #84 open pending approved Preview/source validation; merge and Production are separate owner-approval gates. Next: validate dynamic pricing cards, visible FAQ and JSON-LD in Preview, then measure settled matched page+query GSC windows after an approved release.


### PUBLIC-SEO-PR84-PREVIEW-ATTEMPT-20261111 — source review and release gates

- A direct Vercel Preview was attempted from the exact PR #84 branch/SHA `seo/pricing-commercial-intent-2026-11` / `7e6c2cb54f04a5f4078c53c5260662429b280462`. Deployment `dpl_6oWAovgd7paTPZkpJYWToGNNhik6` was **CANCELED** by the configured Ignored Build Step; no build events or usable preview were produced. The standard PR statuses still report build-rate-limit. No project settings/plan were changed. Do not bypass by disabling ignore rules or mislabeling the SHA as main/UAT.
- Source review of PR #84's pricing route confirms dynamic plan cards continue to use the Pricing component/live `plansApi.list()`; no hardcoded prices were added. The route continues to legacy hosting provider the extended FAQ and SoftwareApplication/FAQPage structured data. Internal links preserve ownership for inbound DM, comment-triggered private reply, free trial and demo; no additional URL/keyword owner was introduced. This is source inspection, not build/type-check/browser QA.
- Corrected sitemap last-modified metadata for the substantive pricing copy edit: `lib/seo.ts` now sets `PAGE_LAST_MODIFIED["/pricing"]` to `2026-11-09`, commit `7986c200a0976ed678f751ce6d14963cd422fe8a` on the PR #84 branch. This is source metadata only; Google sitemap download/recrawl not verified.
- Five-stage gate: (1) repository/doc reconciliation completed; (2) Preview build blocked by Ignored Build Step; (3) source review completed but runtime acceptance open; (4) merge/Production not performed (separate owner approval); (5) post-release matched GSC measurement waits for an approved release and settled Search Console data.
- No Production code, DB, secrets, Vercel project configuration, plan, or infrastructure changed. Keep PR #84 open. Next action requires a compliant Preview route preserving exact PR SHA and current ignore-step policy; if none exists without configuration/quota changes, stop and request owner direction.


## 2026-11-11 — PR #84 CI failure diagnosis and corrective change (current checkpoint)

- Frontend PR [#84](https://github.com/namach2727-coder/directpilot-web/pull/84) remains OPEN / UNMERGED. Latest branch head: `3c3016b62de68a55d928eb2506e2f197ff6b2c94`; base branch `main` currently points to `06e3381fb77773d449fc61a44991a802d4d037ec`. GitHub compare reports the PR branch is 4 commits ahead and 1 behind, with merge base `1c0bf5cd60c3f9cd863b4f7fb6401325164874ef`; GitHub still reports it mergeable. Do not confuse the prior PR base SHA with current Production main.
- The first GitHub Actions run on the prior PR merge candidate failed in both `Production Public Release Validation` and `Production promotion validation` at `npm test`. The exact failing assertion in `tests/seo.test.mjs` expected the existing pricing FAQ phrase «قیمت دایرکت هوشمند به چه عواملی بستگی دارد؟», which had been removed from the revised `pricingFaq` data.
- Corrective source change: restored that exact question in the existing `pricingFaqExtended` collection with an answer explaining comparison by product, validity, account count and plan capacity, while directing users to live plan cards/order summary for the final amount. This preserves the existing FAQ contract and adds no hardcoded price.
- Corrective commit: `3c3016b62de68a55d928eb2506e2f197ff6b2c94`. Changed source remains limited to `app/[...slug]/page.tsx` and `lib/seo.ts`; the restored FAQ is in the former.
- New GitHub Actions runs for the corrective head: `Production promotion validation` run `43003471352` and `Production Public Release Validation` run `43003471403`; both were IN_PROGRESS at the latest check. Their earlier runs failed only at the test step; type-check, lint and build were skipped after that failure. Do not mark validation PASS until the new runs complete and every relevant step is green.
- Vercel check statuses on the corrective head report `build-rate-limit` for both directpilot-web and the separate directpilot-gsc-mcp project. Earlier Preview deployment `dpl_6oWAovgd7paTPZkpJYWToGNNhik6` was CANCELED before build by the configured Ignored Build Step, which explicitly returned exit code 0 for the feature branch. Its actual Git SHA was `7e6c2cb54f04a5f4078c53c5260662429b280462`, not the later PR head; it is not evidence of a built Preview.
- Current Production is deployment `dpl_3rf9syfjYbJgNAKeihEiTRvTZSKF`, READY, target production, main SHA `06e3381fb77773d449fc61a44991a802d4d037ec`, aliases `directpilot.ir` and `www.directpilot.ir`. PR #84 is not included.
- Scope boundaries: no PR merge, Production deployment, Vercel project-setting change, plan upgrade, database/secret/billing/auth/provider/Meta change. Do not bypass the Ignored Build Step by changing global settings or falsifying branch metadata. The next release gate remains: successful current-head Actions, usable Preview/build and route/structured-data smoke tests, then separate explicit owner approval for merge/Production. Search Console impact measurement remains pending until a real release and a settled comparable GSC window.


## 2026-11-11 — Follow-up validation result and Search Console freshness

- The FAQ correction in frontend PR #84 restored the previously asserted pricing FAQ phrase. On the next GitHub Actions attempt, both `Production promotion validation` (run `43003471352`) and `Production Public Release Validation` (run `43003471403`) again FAILED at `npm test`, but the first failure is now a separate assertion in unchanged `components/automation-rules` source: `tests/automation-rules-ui.test.mjs:85` expects the pattern `access?.limit ??`. The source under test does not match that pattern. Type-check, lint and build were skipped after the test failure. This failure is outside PR #84's two-file scope; no unrelated automation-runtime or test changes were made. Therefore the pricing FAQ-specific failure is addressed, but the full suite remains blocked and the current head is NOT validated.
- Latest Search Console pull via the connected Windsor.ai Search Console connector, property `sc-domain:directpilot.ir`, requested `2026-10-14..2026-11-11`, returned 89 query/page/date rows; newest returned date remains `2026-11-08`. No rows for Nov 9–11 were returned; this is a data-freshness limitation, not evidence of zero impressions/clicks.
- Low-volume latest pricing observations remain: `قیمت دایرکت هوشمند اینستاگرام` on `/pricing` had one impression, zero clicks, average position 26 on Nov 2; `هزینه دایرکت خودکار اینستاگرام` had one impression, zero clicks, position 28 on Nov 2. These isolated observations are directional only and cannot establish a ranking trend or PR #84 impact.
- No SEO release occurred; consequently no causal post-release measurement window exists. Keep the prior matched-window property-level comparison as historical baseline only.


### META-OAUTH-SINGLE-REDIRECT-UAT-RELAY-20261114

- Requirement confirmed: retain exactly one Meta Redirect URI, the existing Production callback `https://directpilot-prod-api.vercel.app/api/v1/integrations/instagram/callback`; do not add a UAT URI or modify Meta settings.
- UAT onboarding creates a cryptographically random state with the code-owned `uat.` prefix; the state is persisted in the UAT database as a SHA-256 digest and remains subject to expiry and single-use validation.
- Only the shared Production callback relays `uat.` states to the fixed code-owned UAT callback `https://directpilot-uat-api.vercel.app/api/v1/integrations/instagram/callback`. Destination is not read from environment, query parameters, or headers.
- Non-UAT state does not relay from Production; non-Production environments do not relay; caller-controlled `redirect_uri` remains rejected.
- UAT must use the same Meta-registered Production callback as `META_OAUTH_REDIRECT_URI` for authorization URL generation and token exchange.
- Implementation and focused regression tests are in PR #139 (`fix/meta-single-redirect-uat-relay-20261114`), based directly on current `backend-main` to avoid the unrelated schema/SEO branch divergence found in PR #138.
- Added a focused GitHub Actions workflow for Instagram onboarding and Unified Login tests. Full CI is separately blocked at test collection by missing `app.seo_growth.crawler_policy` on the current base branch; this is not an OAuth Relay failure.
- No Meta settings, Production environment variables, database contents, credentials, encryption keys, or outbound messaging settings were changed. No Production deployment was initiated.
- Remaining activation gates: focused tests pass; review/merge PR #139; deploy shared callback change to Production through the normal approved release process; set only UAT project's `META_OAUTH_REDIRECT_URI` to the already-registered Production callback; deploy UAT; verify live 303 relay and state consumption end-to-end.