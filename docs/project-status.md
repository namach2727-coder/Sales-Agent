# DirectPilot Project Status

## Canonical source location

- Repository: `C:/Users/q/Documents/Codex/2026-07-11/referenced-chatgpt-conversation-this-is-untrusted`
- Remote: `https://github.com/namach2727-coder/Sales-Agent.git`
- Branch: `integration-01-complete-ai-flow`
- Previous tracked base: `8055286f5b0859cd708c33ee6c8dd9f4bc513307`
- Canonical RC: the commit containing this document, with subject
  `feat: prepare DirectPilot SaaS backend RC1`.

The previously reported `31aef92` is not present in the local object database,
any local branch/worktree/reflog, or any branch/tag advertised by the configured
remote. Remote `main` contains the public legal-site files and is not the
backend lineage. It must not be treated as the backend RC source.

## Current phase

DirectPilot MVP release-candidate reconciliation. Production is not provisioned
or deployed.

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

## Migration source of truth

The validated linear chain is:

`0009_conversation_core_models`
-> `0010_saas_commerce`
-> `0011_instagram_oauth_onboarding`
-> `0012_plan_billing_duration`

Current Alembic head and current UAT revision are both
`0012_plan_billing_duration`. Revision 0012 legitimately follows 0011 and adds
the backend-authoritative optional positive billing duration required by the
approved plan periods.

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

- Revision: `0012_plan_billing_duration`.
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

- Migration policy: one head (`0012_plan_billing_duration`), schema drift check
  and base -> head -> base -> head checks pass.
- Full SQLite: `613 passed, 4 skipped`.
- Full PostgreSQL: `615 passed, 2 skipped` against a fresh explicitly opted-in
  PostgreSQL test database at head.
- Focused contract/Instagram regression: `99 passed`.
- Expanded Instagram/OAuth/gateway/outbound/UAT runtime regression:
  `98 passed`.
- Contract tests are included in both full suites.
- Local Ollama provider smoke returned a nonblank response.
- UAT DirectPilot, Instagram gateway, PostgreSQL, and Ollama are healthy;
  `/live`, `/ready`, and `/version` return HTTP 200.
- Compile/import, dependency, and whitespace validation pass.

The recurring Windows pytest temporary-directory cleanup warning happens after
successful test completion and does not change the passing exit status.

## Remaining P0 blockers

1. Production infrastructure, managed PostgreSQL/backup restore, private receipt
   storage, DNS/TLS, production Meta approval, and privacy/legal operations are
   external launch gates; production provisioning has not started.

## Exact next action

Review the canonical RC commit and explicitly authorize its push; do not deploy
production from this local-only state.
