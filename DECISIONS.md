# DirectPilot Decisions

> Read after `AI_HANDOFF.md` and `PROJECT_ROADMAP.md`.
> Last reconciled: 2026-10-10.
> These decisions remain fixed unless new verified technical or product evidence justifies a change.

## Continuity and Evidence

- `AI_HANDOFF.md` is the primary cross-chat continuity authority.
- Chat history is not the project Source of Truth.
- Read continuity files in this order:
  1. `AI_HANDOFF.md`
  2. `PROJECT_ROADMAP.md`
  3. `DECISIONS.md`
  4. `CURRENT_STATE.md`
  5. `NEXT_ACTIONS.md`
- Evidence precedence is: verified runtime/deployment evidence > deployed commit > repository source > continuity documents > old chat history.
- Never mark PASS/DONE without evidence.
- Repository HEAD and deployed runtime commit are separate facts.
- Documentation-only commits must never be described as deployed runtime code.
- After a meaningful Production release, update the five continuity files only after Production verification passes.

## Architecture

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL.
- Keep a Modular Monolith for MVP; do not introduce microservices opportunistically.
- Official Meta APIs only.
- Tenant/store isolation is mandatory and server-side.
- Browser API traffic remains same-origin under `/api/v1/*`.
- Cloud backend selection remains server-side through `DIRECTPILOT_API_UPSTREAM`; never expose backend secrets through `NEXT_PUBLIC_*`.
- Public UUID-style IDs remain API boundaries; internal numeric IDs are persistence details.
- Migrations are additive/forward-only unless an explicit migration plan says otherwise.
- Do not add unnecessary frontend catch-all proxies, serverless functions, or polling.

## Runtime Precedence and AI

```text
Human Takeover
  -> Story-specific Automation [future]
  -> General Deterministic Automation
  -> AI Assistant fallback
```

- Human Takeover suppresses both automation and AI.
- Exact deterministic automation matches perform ZERO LLM, PromptBuilder, knowledge retrieval, or AI usage.
- AI execution requires entitlement.
- Preserve deduplication, echo prevention, and loop protection.
- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256` unless a separately justified change is approved.

## Authentication and Session UX

- Authentication state is server-authoritative.
- Browser auth uses the existing HttpOnly session-cookie contract; do not move auth tokens into localStorage or sessionStorage.
- A valid session must survive normal refresh/navigation and be restored through `/auth/me`; repeatedly asking for a password while the server session is valid is not an accepted UX.
- Authenticated customer routing resolves to `/dashboard`; authenticated platform administrators resolve to `/admin`.
- Unauthenticated protected customer/admin routes must redirect to `/login` without loops.
- Login CTA must not remain visible after authentication.
- Customer and platform-admin workspaces must expose a real backend logout action.
- Authenticated password change requires the current password, enforces backend policy, and revokes all sessions.
- Session-management UI must never expose raw session tokens.
- Forgot-password/self-service recovery remains BLOCKED until a verified email/SMS recovery delivery provider and secure token lifecycle exist. Do not ship a fake or UI-only reset flow.

## Frontend Release Discipline

- UX/Auth changes are accepted in UAT before Production promotion.
- Promotion should use the exact UAT-approved change set; do not insert unrelated feature changes between UAT acceptance and Production.
- The accepted Frontend UX/Auth release is `1f82494f87fe39f0fb2e22043adfd75f7735668c`.
- The accepted Backend Auth/Session release is `84b7df6196fe380fad21a3791e3160840c098602`.
- UAT and Production smoke evidence must be kept distinct; an untested criterion is NOT_TESTED/BLOCKED, not FAIL.

## Commerce

- Backend is authoritative for plan, entitlement, payment, subscription, and activation state.
- Frontend/browser state must never activate a subscription.
- Activation uses immutable purchase/order snapshots.
- Never blindly retry an ambiguous external-provider write.
- Current verified V1 sale scope is `AUTOMATION_V1`.
- `AUTOMATION_TRIAL` and `AI_ASSISTANT_TRIAL` are trials and are not purchasable.
- Legacy FREE/TRIAL/START/PRO plans are not public purchasable plans.
- Do not publish a paid AI Assistant plan unless a new explicit product decision and verified source/runtime change establishes it.
- Payment-provider source/routes are not equivalent to real provider acceptance.

## Environment and Infrastructure

- UAT/Production environment separation is complete and must not be rebuilt without regression evidence.
- Production and UAT use independent runtime configuration/secrets.
- Render backend auto-deploy remains OFF.
- No paid infrastructure/resource may be created without explicit owner approval.
- Current Free Production PostgreSQL is pilot infrastructure only; real-customer durability requires replacement/upgrade plus backup/restore acceptance.
- Production database external access controls must not be weakened merely for inspection.

## Security and Operations

- Never write secret values to Git, chat, logs, screenshots, or frontend public variables.
- Credential documentation records names, locations, and verification status only.
- Production administrator bootstrap/reset credentials remain outside Git and logs.
- Preserve unrelated local dirty work. Never reset, clean, auto-stash, force-push, rebase published history, or rewrite history automatically.
- A Git push is not deployment acceptance; correlate each deployed runtime with its exact commit SHA and verify runtime evidence.

## Shared Meta App Pilot Decision

- For the current pilot, Production and UAT may use the same Meta App credentials.
- Meta Developer settings are currently inaccessible to the owner; therefore the approved pilot workaround is a guarded UAT -> Production relay bridge.
- The provider-facing OAuth redirect intentionally remains the already-registered UAT callback:
  `https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production OAuth requests use that same provider redirect but prefix newly generated state with `production.`.
- UAT may relay only callbacks whose state matches the configured `production.` prefix to:
  `https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production owns and consumes its own OAuth state and stores its own encrypted token/connection; UAT must never consume/copy Production OAuth state or encrypted connection rows.
- UAT webhook relay may be enabled only after Production OAuth has established the matching Production connection.
- Webhook relay must validate the original Meta HMAC signature before forwarding, preserve exact raw bytes/signature/delivery identifiers, avoid internal retries, and fail closed so Meta can retry.
- Production must not have relay targets configured; validated Production settings reject that topology to prevent relay loops.
- Production `META_SEND_ENABLED` remains false until inbound routing is proven and the pilot account allowlist is explicitly restricted.
- Production runtime now enforces the pilot restriction at startup: if `META_SEND_ENABLED=true`, `META_SEND_ALLOWED_ACCOUNT_IDS` must contain exactly one account. Zero or multiple entries are invalid.
- Secret values stay outside Git/chat/logs/docs. Production and UAT retain independent `INSTAGRAM_TOKEN_ENCRYPTION_KEY` values.
- If the owner later regains Meta Developer access, the preferred steady-state design is direct Production callback/webhook registration; the relay is a controlled pilot bridge, not a permanent architectural requirement.
- If simultaneous independent live webhook delivery is required in both environments, use separate Meta Apps rather than broad relay/multiplexing.

## SEO and Search Indexing

- Production `https://directpilot.ir` is the only indexable DirectPilot web environment.
- Vercel Preview/UAT must remain `noindex, nofollow`; preview robots must block crawling and preview sitemap output must remain empty.
- SEO copy must match backend-authoritative product facts. Do not advertise “Free Forever” while the active Automation trial is 14 days with up to 3 automations and one Instagram account.
- Prefer optimizing pages already receiving Search Console impressions before creating large volumes of new content.
- Keep one primary commercial owner per important keyword cluster to reduce cannibalization.
- Search Console deployment acceptance and ranking acceptance are separate: successful deployment does not imply immediate recrawl or ranking improvement.
- The baseline for SEO Phase 1 is the settled 28-day period through 2026-10-04: 14 clicks, 315 impressions, 4.44% CTR, average position 40.30.
- SEO Phase 2 accepted SHA is `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`; live Production audit is clean on the five priority SEO pages.

- OAuth relay is now the accepted pilot workaround when Meta Developer access is unavailable: Production creates the OAuth state, Meta returns to the already-registered UAT callback, and UAT relays only the Production-prefixed state to the Production callback.
- Webhook relay activation is a separate gate and must not be enabled until Production OAuth connection is verified.
- Production outbound remains fail-closed until the account allowlist is explicitly constrained and controlled E2E is ready.

- Production OAuth through the relay bridge is accepted based on live provider evidence; do not require Meta Developer access for this pilot path unless the existing registered callback changes.
- Webhook relay is now enabled UAT -> Production, but Production sending stays disabled until inbound routing and dedupe are verified.

- A live inbound event through the relay bridge is accepted as Production inbound PASS when relay, account resolution, persistence and webhook processing all complete without warning/error; this was satisfied on 2026-10-07.
- For the first Production outbound E2E, use a deterministic AutomationRule rather than AI fallback. AI fallback remains blocked until Production LLM configuration is separately verified.
- Never enable `META_SEND_ENABLED=true` with an empty send allowlist because the current sender treats an empty allowlist as unrestricted.


## Future Product Scope

- Telegram No-Code AI Bot Builder / Managed Bots is an accepted future exploration track.
- It is explicitly outside the current DirectPilot execution scope.
- Do not divert current Production readiness, Meta outbound E2E, database durability, payment or LLM verification work to implement it opportunistically.


## Platform Admin Customer Automation

- Platform Admin customer automation management belongs under **Admin -> Customers & Stores**, scoped to the selected tenant/store.
- Reuse the same AutomationRule domain/service/API used by the customer workspace; do not create a second provider-only rule model or duplicate runtime.
- Platform access must use the existing explicit platform permission path in `resolve_authorized_context`; do not use impersonation or weaken tenant/store isolation.
- The Admin UI may expose the rule builder only when the selected store has the `instagram_automation` effective capability.
- Backend capability and automation-limit checks remain authoritative even when the Platform Admin UI displays an estimated/current limit.


## Controlled Production Outbound
- The first Production outbound test may run only with the single pilot-account restriction active.
- Use one deterministic `قیمت` message from the second Instagram account.
- If routing, duplicate handling, account restriction, or echo behavior differs from expectation, disable Production send immediately before further investigation.


## Controlled Outbound Retest Rule
- If a pilot message produces no inbound webhook at either relay or Production, do not classify automation/outbound as failed.
- After relay health is restored, perform exactly one clean retest before changing rule logic or outbound configuration.


## Meta Controlled E2E Acceptance — 2026-10-11
- Accept Production deterministic Meta outbound E2E as PASS based on runtime evidence.
- Acceptance requires one inbound event, one deterministic response delivery, no AI fallback, no duplicate second send, and no echo loop; all were satisfied in the clean retest.
- Production send is returned to disabled after the test.
- Do not reopen Meta transport work without regression evidence.
- Production database durability/backup-restore is the next highest-priority real-customer readiness gate.


## Production DB Durability Assessment — 2026-10-11
- Current Production Postgres is Free, expires 2026-11-02, has no managed backups/PITR, no HA, no replicas, and an empty external IP allowlist.
- Seven-day metrics show very low Pilot load: CPU ~0.007 cores, memory roughly 40-60 MB, active connections peak 6.
- Recommended paid target: Render Postgres `0.1c-256mb` with current storage kept minimal.
- Expected base compute cost: about $6/month; 1 GB storage included, additional Postgres storage is billed separately.
- Paid Render Postgres enables PITR; on a Hobby workspace the recovery window is 3 days. On-demand logical exports are available for paid instances and retained for 7 days.
- Compute-plan change requires brief database downtime.
- Paid infrastructure change remains blocked until explicit owner approval.


## Production DB Upgrade Decision — 2026-10-11
- Owner explicitly deferred the paid Production Postgres upgrade for now.
- Do not change the current Free Production database plan or incur paid infrastructure cost without a new explicit approval.
- Current risk remains accepted temporarily: Free Production Postgres expires 2026-11-02 and does not satisfy durability/backup-restore acceptance.
- Real-customer onboarding remains blocked by Production database durability until this decision is revisited.


## LLM Production Configuration — 2026-10-11

- Treat LLM diagnosis as PASS but Production LLM readiness as BLOCKED until a Production-specific provider credential exists.
- Never copy UAT LLM secrets into Production and never request/paste provider secrets in chat.
- Selected-provider/model/credential-presence may be logged only as sanitized metadata; credential values must never be logged.
- Production currently selects OpenAI but has no OpenAI credential; Groq credential/model are also absent.
- Before selecting Groq for Production, use a currently supported Groq model rather than blindly mirroring UAT configuration.
- Preserve deterministic-first execution: a matched AutomationRule performs zero LLM work.


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


## Production AI Fallback Acceptance — 2026-10-11

- Accept Production Groq AI fallback E2E as PASS.
- Approved Production runtime: `LLM_PROVIDER=groq`, model `qwen/qwen3.8-27b`, context 4096, max output 256, reasoning effort none.
- Keep provider credentials environment-specific and secret; never copy UAT credentials into Production or expose keys in logs/chat.
- Controlled acceptance requires one provider request, assistant persistence, exactly one Meta delivery, no provider/outbound failure, and no duplicate/echo loop; all were satisfied.
- Keep `META_SEND_ENABLED=false` outside explicitly controlled pilot tests until broader Production-send policy is approved.
- Server-authoritative quota guard remains part of the AI path; do not weaken it for testing.


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

- Decision: keep Production Payexa fail-closed without a credential until explicit merchant credential provisioning is complete.
- Decision: UAT must use only Payexa Sandbox and its sandbox credential; it must never point at Production Payexa.
- Decision: do not expose Payexa checkout broadly until controlled acceptance is complete.


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

- Decision: manual card transfer + Admin approval is the authoritative MVP payment method.
- Decision: Payexa is parked/deferred and must not block MVP Production readiness.


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

- Decision: Production banking destination data must be explicitly configured by an authorized Admin; never copy UAT financial details automatically or use synthetic card data.


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

- Decision: never rely on a React SyntheticEvent/currentTarget after an async boundary; capture required DOM references synchronously before awaiting.
