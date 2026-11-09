> **DIRECTPILOT — MANDATORY CONTINUITY AND CHANGE-LOG RULE (owner decision, 2026-10-17).**
> This file is one of the **six mandatory handoff/release artifacts**. On every DirectPilot / DirectPilot TelBot task, the assistant must read current `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`, and `docs/releases/RELEASE_REGISTER.md` **before making changes**; reconcile against actual GitHub/Vercel/Neon state, not chat memory. **After every meaningful change**, update all five main files **and the Release Register** coherently: scope and owner approval, PR/commit, changed artifacts, UAT/Production status, automated and manual evidence, unresolved risks, next action. Keep the current summary easy to scan, preserve history (archive older detail in runbooks; do not delete evidence), and never call code-merged "deployed" or a proposed feature "active". Never publish to Production, touch live data/secrets, or switch Meta/Telegram outbound functionality without specific owner approval. This rule itself MUST remain at the very TOP of each of the six files and must be propagated in any handoff to a new chat.

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

No Production deployment or promotion, merge to backend-main or frontend main, live database migration/write, destructive cleanup, credential rotation, pricing/subscription/payment mutation, Meta/Telegram outbound action, or change to Vercel/Render/Neon configuration. Obtain separate owner approval for each such action.

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
