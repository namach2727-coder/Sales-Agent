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
suppression/resume. Phase D.1 is **COMPLETE / RELEASED / CLOUD VERIFIED**.
Automation and AI Assistant are independent product families with simultaneous
ownership supported, backed by the System Admin commercial foundation. Phase
Phase D.2 — AI Assistant Workspace is **COMPLETE / IMPLEMENTED / RELEASED /
CLOUD VERIFIED**. Authenticated cloud acceptance verified the independent AI
workspace and a real Knowledge-grounded Instagram AI response.

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
-> `0015_automation_rules`
-> `0016_product_family_commerce`
-> `0017_ai_assistant_workspace`

Current source Alembic head is `0017_ai_assistant_workspace`. Revision 0016 is
additive: existing START subscriptions are classified as Automation, existing
TRIAL/PRO subscriptions as compatibility-only `LEGACY_BUNDLE`, and historical
orders, amounts, dates, public IDs, relations, rules, Knowledge, and AI usage
remain unchanged. Revision 0017 adds the tenant/store-scoped AI Assistant
workspace settings and usage foundation without changing the independent
Automation product boundary.

The 0010-0012 files are byte-identical between the reviewed RC source and the
running UAT image. They are tracked by the canonical RC commit and must remain
immutable after that commit.

## Historical commercial model

| Plan | Price | Period | AI replies | Automations | Instagram accounts |
|---|---:|---:|---:|---:|---:|
| TRIAL | 0 IRR | 14 days | 200 | 3 | 1 |
| START | 2,990,000 IRR | 30 days | 1,500 | 10 | 1 |
| PRO | 6,990,000 IRR | 30 days | 5,000 | 30 | 1 |

These values describe the historical catalog only. Legacy TRIAL/START/PRO are
not available for new purchase or renewal after Phase D.1. START remains
Automation-only until expiry; TRIAL and PRO remain compatibility-only combined
entitlements until expiry. New Automation and AI Assistant prices, durations,
and limits are System Admin-managed; no unapproved sellable values are seeded
or hard-coded. The backend remains authoritative for catalog values, charged
order amounts, and subscription snapshots.

## Current UAT evidence

- Migration head: `0017_ai_assistant_workspace`.
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

1. Provision the always-on Linux Docker host, DNS/TLS reverse proxy, off-host
   backup destination, monitoring/operator ownership, and production-only
   secrets.
2. Perform and evidence production PostgreSQL backup/restore rehearsal before
   migrating real data.
3. Complete production Meta application review/configuration and controlled
   webhook/outbound acceptance without reusing UAT assets.
4. Select and configure the existing external AI-provider adapter (or a
   deliberately operated non-laptop Ollama endpoint).

## Exact next action

Define the next post-D.2 product phase without changing the independent
Automation and AI Assistant entitlement boundary.

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
`app/module_catalog.py` provides `effective_subscription_for_family()`,
`effective_product_subscriptions()`, `effective_capabilities()`, and
`has_capability()`.

The latest tenant/store-scoped active subscription within each product family,
ordered by `starts_at` and then internal ID, controls that family's effective
capabilities. Capabilities are unioned across Automation, AI Assistant, and an
active compatibility-only Legacy Bundle. An expired or not-yet-started
subscription grants no capabilities. Resolution also
requires the plan grant, valid module definition, valid `StoreModule` state and
time bounds, and valid dependencies.

On PRO -> START, `instagram_automation` remains enabled while `knowledge_base`
and `ai_assistant` become ineffective. On START -> PRO, all three become
effective. Downgrades do not delete Knowledge records or other historical
data. A stale `StoreModule` row cannot independently grant a capability absent
from the effective subscription and plan.

The authenticated `GET /api/v1/subscription/me` response exposes
`effective_capabilities`. The backend remains authoritative.

Phase D.1 adds the additive `0016_product_family_commerce` migration. Controlled
seed reconciliation is non-destructive and preserves subscription history,
Knowledge records, conversations, Instagram connections, and historical module
rows. No database reset is part of this change.

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

### Automation Edit Workflow cloud acceptance

Automation Edit Workflow is **COMPLETE / IMPLEMENTED / RELEASED / CLOUD
VERIFIED**. The frontend implementation was released in commit
`361cedefbde60f388746b079ef8e5122be0430c7`; the backend Edit API uses
the pre-existing authenticated PATCH implementation. Cloud UAT updated the
existing rule `ba11099e-5c89-44bc-8048-c864f3038e75` in place at its full
capacity of 3/3 rules, without creating a fourth rule. The prior exact DM
trigger `DPTEST4827` was replaced by `DP-EDIT-8H3R6V2Q`, with deterministic
response `EDIT-UAT-8H3R6V2Q`; rule count remained three before and after.
The edited trigger matched at runtime and produced exactly one sent outbound.
The primary event took no AI fallback, PromptBuilder, Knowledge retrieval,
LLM provider, or AI-usage path. No professional-account echo re-ingestion or
loop was observed.

### Ignored inbound event state consistency

`READY_EVENT_WITH_IGNORE_ERROR` is **RESOLVED / IMPLEMENTED / RELEASED /
CLOUD VERIFIED**. The backend fix in
`aef9551afb08574f289f3ec5c65c717d1c46814d` was pushed to
`backend-main`; the operator confirmed the matching Render deployment is
Live. Rechecked `/live` and `/ready` returned HTTP 200, with database
available and migration current. Validation passed 53 targeted tests and
781 full backend tests (4 skipped), plus compile/import and diff checks.

Root cause: an ignored inbound result retained event status `ready` after
its webhook delivery became `processed`; the router then entered Automation
without conversation/message identifiers and raised
`ConversationValidationError`. Ignored and duplicate inbound results now
transition to terminal `ignored`, and benign results stop before Automation
or AI. Genuine exceptions are not broadly swallowed; normal Automation and
AI paths remain intact.

Read-only UAT history found 49 `ready` events with processed deliveries.
Twenty-eight had messages: five with Automation output, thirteen with AI
output, and ten with a message but no outbound. The other 21 had no message:
six were probable duplicates and fifteen remain unresolved. No row was
proven to be an ignored, duplicate, or failed event incorrectly left ready;
no row was a probable old-bug match. Because `ready` is valid for handled
events and there are zero safely proven repair candidates, historical repair
is **not required**. No historical rows were changed.

Separate non-blocking follow-up: `REAL_FAILURE_REPLAY_LIMITATION` remains
outside this ignored-event control-flow fix and requires its own audit.

## Phase D.1 independent product commerce

Status: **COMPLETE / RELEASED / CLOUD VERIFIED**.

- Authoritative backend runtime commit:
  `58e2efde42dc2634eff38a35f9f4d2bb63c8fd7a`.
- Authoritative frontend production commit:
  `e0f37bb7bc12bdc0051ea13cd7b3686aa635ebf0`.
- Cloud health and readiness passed with migration head
  `0016_product_family_commerce`.
- Authenticated acceptance passed for `/subscription/me`, the product-aware
  collection, legacy compatibility, preserved historical subscription, and
  effective capabilities `ai_assistant`, `instagram_automation`, and
  `knowledge_base`.
- Three Automation rules and five Knowledge records were preserved. The catalog
  correctly exposes zero purchasable plans while commercial pricing values are
  pending; legacy TRIAL/START/PRO are not purchasable and no fake zero-price
  sellable plan is visible.
- The System Admin authorization boundary passed: the non-platform-super-admin
  acceptance identity was correctly denied Admin reads.

- `AUTOMATION` grants `instagram_automation`; `AI_ASSISTANT` grants
  `ai_assistant` and `knowledge_base`. A store may own either, both, or neither.
- Legacy START remains Automation-only. Legacy TRIAL and PRO remain immutable
  `LEGACY_BUNDLE` subscriptions until their existing expiry. None of the legacy
  plans is offered for new purchase or renewal.
- New registration Trial activation atomically and idempotently creates two
  separate subscriptions: one Automation trial and one AI Assistant trial.
- `GET /api/v1/subscription/me` retains its singular compatibility fields and
  adds authoritative product-aware state plus a separate legacy-bundle view.
- Catalog price, duration, limits, trial eligibility, visibility, and purchase
  availability are System Admin-managed. Active subscription terms are
  snapshotted at activation, so later catalog edits affect only future
  activations and renewals.
- The existing `platform_super_admin` role authorizes the minimal server-backed
  plan, customer/store, subscription, grant, and revoke APIs. Tenant admins are
  not platform administrators. Sensitive admin changes write sanitized audit
  records and never include credential material.
- Customer pricing remains API-driven. Structural Automation and AI Assistant
  trial plans are non-purchasable, and no new sellable price has been invented.
- Automation-only customers see Automation; AI-only customers see AI Assistant
  and Knowledge; customers with both see both. Full AI Workspace UX remains
  deferred to Phase D.2.
- Deterministic Automation and all Admin/catalog operations remain zero-LLM.
  Knowledge belongs to AI Assistant and is not an Automation product concern.
  Runtime limits remain `GROQ_CONTEXT_LENGTH=4096` and
  `GROQ_MAX_OUTPUT_TOKENS=256`.
- The authenticated acceptance was read-only: it caused no database,
  subscription, catalog, AutomationRule, or Knowledge mutation; no Meta,
  Instagram, LLM, or AI-usage action occurred.

## Phase D.2 AI Assistant Workspace

Status: **COMPLETE / IMPLEMENTED / RELEASED / CLOUD VERIFIED**.

- Authoritative backend runtime commit:
  `dba9841d7bd44e6d1ab61f59befd4181417a1530`.
- Authoritative frontend production commit:
  `1dbdd2bf4541cddf4d23e479a90b2919b2a9c1b0`.
- Cloud health and readiness passed with migration head
  `0017_ai_assistant_workspace`.
- Authenticated read-only acceptance verified the AI Assistant workspace,
  separate Automation entry, Knowledge visibility, AI enabled state, usage
  summary, hidden provider/model/API-key internals, and the normal-user Admin
  authorization boundary. Existing three Automation rules and five Knowledge
  records were preserved.
- AI entitlement and the store-level enabled state remain separate controls:
  entitlement plus enabled permits AI; disabling suppresses AI without
  changing entitlement; an unentitled store cannot enable AI.
- Real Instagram cloud UAT verified both Knowledge lifecycle cases. While the
  relevant FAQ was draft, retrieval correctly selected zero Knowledge chunks
  and the AI reported that the information was unavailable. After publication,
  retrieval selected the relevant FAQ, included one Knowledge chunk within the
  bounded PromptBuilder context, called Groq/Qwen, recorded AI usage, and sent
  exactly one answer consistent with the published FAQ.
- The grounded cloud path produced no deterministic Automation match,
  duplicate inbound, duplicate outbound, echo re-ingestion, or loop. Human
  Takeover priority and the independent Automation product boundary remain
  unchanged.
- Runtime limits remain `GROQ_CONTEXT_LENGTH=4096` and
  `GROQ_MAX_OUTPUT_TOKENS=256`; the verified request respected both limits.

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
