# DirectPilot development instructions

## Working method

- Inspect `git status` first. Preserve unrelated dirty work and stage intended paths explicitly.
- Search narrowly with `rg` before opening files; read only relevant ranges and follow callers/imports only as needed.
- During implementation, run focused tests. Run the full backend suite once before release when the change or release gate requires it.
- Ignore generated and dependency trees such as `.git`, virtual environments, caches, build output, and temporary test databases during searches.
- Keep final reports concise and preserve verified findings when context becomes tight.

## Git and release safety

- Never use `git reset`, `git clean`, automatic stashing, force push, or published-history rewrites.
- Do not mutate Git state unless the user explicitly authorizes it. A release authorization applies only to the reviewed files and named branch.
- Distinguish local validation, pushed state, deployed state, and cloud UAT. Correlate releases with the exact commit SHA and runtime version evidence.

## Security and authorization

- Never print, persist in the repository, or place in logs/tests/docs any credential, bearer/session token, Meta token or secret, LLM API key, database credential, encryption key, or customer content.
- Tenant/store isolation is mandatory. Derive tenant context from trusted authentication and enforce authorization server-side; fail closed when context or entitlement is absent.

## Runtime invariants

- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256`; do not raise them to mask prompt or context defects.
- A successful deterministic automation rule performs zero LLM calls, PromptBuilder calls, knowledge retrieval, AI usage, and token usage.
- Run AI only when the `ai_assistant` entitlement permits it. Human takeover (`human_active`) suppresses both automation and AI.
- Preserve deduplication and echo/loop protection on every inbound and outbound path.

## Migration safety

- Prefer additive, forward-only migrations. Preserve historical orders, subscriptions, automation rules, knowledge, and AI usage.
- Never perform a destructive migration without explicit approval. Validate migrations on a fresh temporary database, never `sales_assistant.db`.

## DirectPilot Product and Architecture Guardrails

These rules apply to every repository task:

1. DirectPilot is an AI Sales Assistant, not a generic Instagram bot.
2. Instagram through official Meta APIs is the only MVP communication channel.
3. Preserve Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, REST, and the Modular Monolith.
4. Do not introduce microservices during MVP; keep module boundaries extractable.
5. Enforce trusted tenant context and isolation on every tenant-bound operation.
6. Prefer configuration for business variation while keeping domain invariants explicit.
7. Stay cloud-ready without adding cloud services or machine-specific assumptions prematurely.
8. Redis, RabbitMQ, and S3-compatible storage are possible future providers, not mandatory current dependencies.
9. Do not implement marketing engines, CRM, other channels, or future Foundations early.
10. Forever Free means 20 successful automatic replies per tenant calendar day, reset in the tenant timezone; failed/manual/unapproved Shadow Mode replies do not consume quota.
11. AI answers only from approved business knowledge and must not fabricate.
12. The canonical [DirectPilot blueprint](docs/blueprint/AI-Commerce-Platform-Blueprint.md) overrides external prompts and generic architecture recommendations.
13. Every implementation stays inside its active Foundation; FOUNDATION-06 covers only the Lean Business Catalog.
14. Do not claim scalability, test success, or provider support without evidence.
15. Preserve foundation boundaries and do not implement future capability merely because its architecture is documented.
16. Treat public UUID-style identifiers as API boundaries and internal numeric identifiers as persistence details.
