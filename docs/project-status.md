# DirectPilot Project Status

## Canonical source location

- Repository: `C:/Users/q/Documents/Codex/2026-07-11/referenced-chatgpt-conversation-this-is-untrusted`
- Remote: `https://github.com/namach2727-coder/Sales-Agent.git`
- Canonical backend branch: `backend-main` (also the GitHub default branch).
- Canonical RC: `6186155e2fa4ed13dd9215942527101ae47db8c6`, subject
  `feat: prepare DirectPilot SaaS backend RC1`.
- Legacy `main`: separate GitHub Pages/legal-content lineage, retained unchanged.

The previously reported `31aef92` is not present in the local object database,
any local branch/worktree/reflog, or any branch/tag advertised by the configured
remote. Remote `main` contains the public legal-site files and is not the
backend lineage. It must not be treated as the backend RC source.

## Current phase

Automation/AI Phase C is **COMPLETE / PASS**. Real cloud UAT verified the
rule-first runtime for deterministic DM, Story Reply, and Comment -> Private
Reply, the no-match Knowledge-grounded AI fallback, and Human Takeover
suppression/resume. Phase D, the customer-facing Automation UX, is now active.

## Architecture and implemented MVP

- FastAPI/SQLAlchemy/Alembic/PostgreSQL modular monolith.
- Official Instagram API with Instagram Login as the MVP channel.
- Tenant/store isolation, identity, opaque sessions, permission-based RBAC.
- Business catalog and approved knowledge boundary.
- Conversation persistence, deterministic prompt builder, provider-neutral LLM
  layer, Ollama/OpenAI adapters, AI orchestration, and Instagram delivery.
- Customer registration/login, plan/order/manual card-transfer payment,
  private receipt, provider approval, subscription, and entitlement APIs.
- Official Instagram OAuth onboarding into encrypted `InstagramConnection`.
- Customer-owned business knowledge/profile editing, paginated read-only
  inbox, persisted audited automation pause/resume, and safe browser OAuth
  completion redirects are implemented for Final-UAT.
- Industry Knowledge V2 keeps the sixteen canonical industries while adding
  schema-driven subcategory visibility, physical/digital/service type
  differentiation, transparent minimum/recommended/optional readiness,
  reusable price/currency/availability fields, variant and listing details,
  bounded custom field types, regulated-domain safety boundaries, and
  label/section/provenance metadata in the Knowledge Engine.  It uses the
  existing `industry-profile` JSON entry (schema version 2) and requires no
  migration.

## Migration source of truth

The validated linear chain is:

`0009_conversation_core_models`
-> `0010_saas_commerce`
-> `0011_instagram_oauth_onboarding`
-> `0012_plan_billing_duration`
-> `0013_store_automation_control`
-> `0014_transport_neutral_inbound`

Current source Alembic head is `0014_transport_neutral_inbound`; current UAT
remains safely unchanged at `0012_plan_billing_duration` until the normal
forward migration is deployed. Revision 0013 adds only the store-owned,
revisioned automation switch with a safe default of enabled for existing rows;
revision 0014 adds transport-neutral inbound processing without changing the
legacy webhook contract.

The 0010-0012 files are byte-identical between the reviewed RC source and the
running UAT image. They are tracked by the canonical RC commit and must remain
immutable after that commit.

## Approved commercial model

| Plan | Price | Period | AI replies | Automations | Instagram accounts |
|---|---:|---:|---:|---:|---:|
| TRIAL | 0 IRR | 14 days | 200 | 3 | 1 |
| START | 2,990,000 IRR | 30 days | 1,500 | 10 | 1 |
| PRO | 6,990,000 IRR | 30 days | 5,000 | 30 | 1 |

Limits apply per plan period. Follower-based pricing is not used. The backend
is the price, period, order amount, and entitlement authority. Legacy FREE and
PILOT records are retained only for referential compatibility and are inactive,
so they are unavailable for new orders.

## Current UAT evidence

- Revision: `0012_plan_billing_duration` (not reset or migrated by the
  Final-UAT API implementation task).
- UAT persistent database and volumes were not reset or downgraded.
- Tenant, store, user, platform/tenant RBAC, tenant membership, encrypted active
  Instagram connection, conversation, messages, inbound events, and webhook
  deliveries are present.
- Read-only ownership, scope, counter, connector, event/webhook, and commerce
  referential-integrity checks all pass.
- The active connector retains an encrypted credential.
- Current data-integrity status: **PASS**.
- `META_SEND_ENABLED` remains fail-closed; no live Meta send was made during
  reconciliation.

The exposed UAT PostgreSQL credential was treated as compromised. It was
replaced with a random URL-safe value stored only in the gitignored `.env.uat`.
PostgreSQL rejected the old credential; DirectPilot and Instagram gateway were
recreated against the new credential and returned healthy.

## Migration rehearsal

Two isolated disposable PostgreSQL databases were created and removed without
touching UAT:

- Fresh database -> 0012 head: **PASS**.
- 0010 database with synthetic user, tenant/store, active legacy PILOT plan,
  order, and subscription -> 0011 -> 0012 -> production plan reconciliation:
  **PASS**.
- Historical PILOT order/subscription references remained valid, orphan count
  remained zero, PILOT became inactive, and TRIAL/START/PRO matched the approved
  prices, limits, and durations.

## Validation evidence

- Migration policy: one head (`0014_transport_neutral_inbound`), schema drift check
  and base -> head -> base -> head checks pass.
- Full SQLite: `635 passed, 4 skipped` (RELEASE-01 validation).
- PostgreSQL: fresh database -> `0013` passed; full suite produced `620 passed,
  2 skipped` plus two receipt tests blocked only by Windows path length, and
  both blocked tests passed when rerun with a shorter workspace temp path.
- Final-UAT focused customer API/Instagram/OAuth suite: `22 passed`.
- Focused contract/Instagram regression: `99 passed`.
- Expanded Instagram/OAuth/gateway/outbound/UAT runtime regression:
  `98 passed`.
- Contract tests are included in both full suites.
- Local Ollama provider smoke returned a nonblank response.
- UAT DirectPilot, Instagram gateway, PostgreSQL, and Ollama are healthy;
  `/live`, `/ready`, and `/version` return HTTP 200.
- Compile/import, dependency, and whitespace validation pass.
- Industry Knowledge V2 validation: targeted industry/API/prompt/onboarding
  tests **57 passed** on the final focused run; the final full SQLite run
  completed with **654 passed, 4 skipped**. Frontend checks after the V2
  questionnaire changes: **86 passed**, TypeScript, ESLint, build, and
  diff-check pass.
- Automation/AI Phase A validation: capability-focused tests **14 passed**;
  commerce/module tests **50 passed**; final focused tests **20 passed**; final
  full backend regression **727 passed, 4 skipped**. Compile, diff, focused
  secret review, tenant isolation, store isolation, and security checks pass.
- Phase A was pushed to `backend-main` at
  `74991049f66a5943eba162baac6e5d70eb8c3fc0`. Render `/live`, `/ready`, and
  `/version` returned HTTP 200 after the release check. The public endpoints do
  not expose the active deployment SHA, so exact Render commit verification is
  **MANUAL_REQUIRED**; this is not a functional blocker.

The recurring Windows pytest temporary-directory cleanup warning happens after
successful test completion and does not change the passing exit status.

## Remaining P0 blockers

1. Configure and verify Render UAT `META_APP_ID` and
   `META_OAUTH_REDIRECT_URI` (`https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback`);
   local provider validation is complete but Render control is unavailable in
   this environment, so `/connect` readiness remains unverified.
2. Apply the normal forward-only `0012` -> `0014` migration chain to disposable
   UAT, deploy the updated backend, and complete the customer Final-UAT.
3. Provision the always-on Linux Docker host, DNS/TLS reverse proxy, off-host
   backup destination, monitoring/operator ownership, and production-only
   secrets.
4. Perform and evidence production PostgreSQL backup/restore rehearsal before
   migrating real data.
5. Complete production Meta application review/configuration and controlled
   webhook/outbound acceptance without reusing UAT assets.
6. Select and configure the existing external AI-provider adapter (or a
   deliberately operated non-laptop Ollama endpoint).

## Exact next action

Implement Phase D: a Persian, RTL customer-facing AutomationRule management
experience over the existing authenticated CRUD contract. Keep rule
administration deterministic and zero-LLM.

## Automation and AI capability lifecycle

Phase A status: **PASS**.

The backend-authoritative canonical capability codes are:

- `instagram_automation`
- `knowledge_base`
- `ai_assistant`

The controlled plan mapping is:

| Plan | Effective capability grants |
|---|---|
| TRIAL | `instagram_automation`, `knowledge_base`, `ai_assistant` |
| START | `instagram_automation` |
| PRO | `instagram_automation`, `knowledge_base`, `ai_assistant` |

Runtime authorization foundations are capability-based and never depend on a
display plan name or a frontend claim. The canonical implementation in
`app/module_catalog.py` provides `effective_subscription()`,
`effective_capabilities()`, and `has_capability()`.

The latest tenant/store-scoped active subscription, ordered by `starts_at` and
then internal ID, controls effective capabilities. Capabilities are never
unioned across arbitrary simultaneous active subscriptions. An expired or
not-yet-started effective subscription grants no capabilities. Resolution also
requires the plan grant, valid module definition, valid `StoreModule` state and
time bounds, and valid dependencies.

On PRO -> START, `instagram_automation` remains enabled while `knowledge_base`
and `ai_assistant` become ineffective. On START -> PRO, all three become
effective. Downgrades do not delete Knowledge records or other historical
data. A stale `StoreModule` row cannot independently grant a capability absent
from the effective subscription and plan.

The authenticated `GET /api/v1/subscription/me` response exposes
`effective_capabilities`. The backend remains authoritative.

No schema migration was required. The migration head remains
`0014_transport_neutral_inbound`. Controlled seed reconciliation is
non-destructive and preserves subscription history, Knowledge records,
conversations, Instagram connections, and historical module rows. No database
reset occurred.

Phase A caused zero LLM calls and changed no AI runtime path. The existing
limits remain `CONTEXT_LIMIT=4096` and `MAX_OUTPUT=256`.

The future deterministic-automation invariant remains:

`DETERMINISTIC AUTOMATION MATCH` -> zero PromptBuilder -> zero Knowledge
generation -> zero Groq/OpenAI/Ollama calls -> zero AI usage -> zero AI tokens.

Phase A provides the entitlement foundation only; later Automation phases must
enforce this invariant at runtime.

## Automation roadmap

Completed:

- Instagram OAuth
- DM Cloud E2E
- Story Reply Cloud E2E
- Comment -> Private Reply Cloud E2E
- Knowledge -> AI Cloud E2E
- echo/loop prevention
- token-aware conversation context
- Inbox MVP
- registration/Trial activation and idempotency
- Phase A capability lifecycle

Completed — Phase B: AutomationRule Domain + CRUD:

- `AutomationRule` model/domain
- tenant/store ownership and isolation
- trigger types, match types, keywords, actions, and priority
- revision and validation
- authenticated CRUD
- `instagram_automation` entitlement gate
- `automation_limit` behavior decision/enforcement appropriate to Phase B

Completed — Phase C: deterministic matching engine and Instagram
interception:

- Rule-first order: normalize/deduplicate/scope -> human-active guard ->
  `instagram_automation` entitlement -> deterministic rule evaluation. A
  successful match delivers and stops; an unmatched event may enter the
  `ai_assistant` fallback, with `knowledge_base` controlling Knowledge context.
- DM exact-match cloud UAT: marker `DPTEST4827`, rule
  `ba11099e-5c89-44bc-8048-c864f3038e75`, exactly one sent deterministic
  response, zero LLM tokens, and no duplicate/echo/loop.
- No-match AI fallback cloud UAT: marker `DPAIFALLBACK-Q7M9X2`, controlled
  Knowledge fact `DP-4827`, Groq model `qwen/qwen3.6-27b`, 1,115 input and 46
  output tokens (1,161 total), context 4,096 and max output 256. Grounding and
  single delivery were verified with no duplicate/echo/loop.
- Human Takeover lifecycle on conversation
  `4be87d47-9c08-4b0e-8641-8e2e3682ea3e`: normal automation -> takeover ->
  `human_active` -> deterministic and AI suppression -> resume -> automation
  restored. Marker `DPHUMAN-H8K4R2` caused zero automatic outbound and zero
  LLM tokens while takeover was active.
- Story Reply exact-match cloud UAT: marker `DPSTORY-7Q9M2K`, rule
  `ecdce8b6-729b-49dd-a2d3-0eb8e0a5b891`, `event_kind=story_reply`, correlation
  `94647335-fb5d-497f-8548-3a304ac9c31d`, one sent response, zero LLM tokens,
  and no duplicate/echo/loop.
- Comment -> Private Reply exact-match cloud UAT: marker
  `DPCOMMENT-4K8M7Q`, rule `ca74ccf4-0b71-4d5e-b4c8-40622c99629e`,
  `event_kind=comment`, correlation `88c3fa42-763f-4a89-8647-fd4ce099c89c`,
  action `SEND_PRIVATE_MESSAGE`; the comment identifier and
  `recipient.comment_id` path were verified. One private reply was sent with
  zero LLM tokens and no duplicate/echo/loop.
- Current UAT inventory is three enabled rules (DM, Story, Comment) against an
  automation limit of three; remaining capacity is zero.
- Capability mapping remains: TRIAL and PRO grant `instagram_automation`,
  `knowledge_base`, and `ai_assistant`; START grants `instagram_automation`
  only. There is no automatic plan upgrade, and deterministic rules always
  take priority over AI.

**Phase C Cloud UAT is complete and passed.** Phase D is now active:

- Phase D: frontend Automation UX
- Phase E: commercial enforcement and metering
- Phase F: Cloud UAT

## Non-blocking backlog

- P2: raw `&#x20;` rendering in some historical Inbox messages.
- P2: Render public endpoints do not expose the active deployment SHA.

## RELEASE-01 validation (2026-09-01)

- The frontend worktree contains the existing FLOW-01/KNOWLEDGE-01/INBOX-01
  changes plus RELEASE-01 customer UX polish: animated DirectPilot brand mark
  with reduced-motion support, real dashboard status summary, setup checklist,
  human/AI inbox states, and customer-facing automation/product/knowledge copy.
- Frontend checks: `npm test` **48 passed**, TypeScript **pass**, ESLint
  **pass**, production build **pass**, and `git diff --check` **pass**.
- Backend focused regression: **70 passed**; full SQLite suite: **635 passed,
  4 skipped**; migration policy, compile/import, and `git diff --check` pass.
- A disposable local customer journey (register → Trial → knowledge → product
  → automation → inbox) completed through the real API against a temporary
  SQLite database. No UAT database, Meta endpoint, or outbound message was
  touched.
- Public/UAT browser acceptance is **blocked** until the Tailscale/public UAT
  endpoint and a browser-reachable backend are available. The temporary local
  API port is intentionally isolated from UAT.
