# DirectPilot Decisions

> Read after `AI_HANDOFF.md` and `PROJECT_ROADMAP.md`.
> Last reconciled: 2026-10-04.
> These decisions remain fixed unless new technical/product evidence justifies a change.

## Continuity and Evidence

- `AI_HANDOFF.md` is the primary cross-chat continuity authority.
- Chat history is not the project Source of Truth.
- Read continuity files in this order:
  1. `AI_HANDOFF.md`
  2. `PROJECT_ROADMAP.md`
  3. `DECISIONS.md`
  4. `CURRENT_STATE.md`
  5. `NEXT_ACTIONS.md`
- Verifiable runtime/deployment evidence wins over stale documentation.
- Correct continuity documents after verification when evidence changes.
- Never mark PASS/DONE without evidence.
- Do not repeat PASS/VERIFIED work unless a related change or regression evidence requires it.
- Repository HEAD and deployed runtime commit are separate facts. Documentation-only commits do not imply deployment.

## Architecture

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL.
- Keep a Modular Monolith for MVP; do not introduce microservices opportunistically.
- Official Meta APIs only.
- Tenant isolation is mandatory and server-side.
- Browser API traffic remains same-origin under `/api/v1/*`.
- Cloud backend selection is server-side through `DIRECTPILOT_API_UPSTREAM`; never expose backend secrets through `NEXT_PUBLIC_*`.
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

## Security and Operations

- Never write secret values to Git, chat, logs, screenshots, or frontend public variables.
- Credential documentation records names, locations, and verification status only.
- Production administrator bootstrap credentials remain outside Git and logs.
- Preserve unrelated local dirty work. Never reset, clean, auto-stash, force-push, rebase published history, or rewrite history automatically.
- A Git push is not deployment acceptance; correlate each deployed runtime with its exact commit SHA and verify runtime evidence.
