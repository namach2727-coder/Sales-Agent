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

DirectPilot MVP customer Final-UAT API completion. Production is not
provisioned or deployed.

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

## Migration source of truth

The validated linear chain is:

`0009_conversation_core_models`
-> `0010_saas_commerce`
-> `0011_instagram_oauth_onboarding`
-> `0012_plan_billing_duration`
-> `0013_store_automation_control`

Current source Alembic head is `0013_store_automation_control`; current UAT
remains safely unchanged at `0012_plan_billing_duration` until the normal
forward migration is deployed. Revision 0013 adds only the store-owned,
revisioned automation switch with a safe default of enabled for existing rows.

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

- Migration policy: one head (`0013_store_automation_control`), schema drift check
  and base -> head -> base -> head checks pass.
- Full SQLite: `620 passed, 4 skipped`.
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

The recurring Windows pytest temporary-directory cleanup warning happens after
successful test completion and does not change the passing exit status.

## Remaining P0 blockers

1. Apply the normal forward-only `0012` -> `0013` migration to disposable UAT,
   deploy the updated backend, and complete the 15-step customer Final-UAT.
2. Provision the always-on Linux Docker host, DNS/TLS reverse proxy, off-host
   backup destination, monitoring/operator ownership, and production-only
   secrets.
3. Perform and evidence production PostgreSQL backup/restore rehearsal before
   migrating real data.
4. Complete production Meta application review/configuration and controlled
   webhook/outbound acceptance without reusing UAT assets.
5. Select and configure the existing external AI-provider adapter (or a
   deliberately operated non-laptop Ollama endpoint).

## Exact next action

Integrate the documented knowledge, inbox, automation, and OAuth redirect
contracts in `directpilot-web`, then run its customer Final-UAT against an
updated disposable UAT deployment.
