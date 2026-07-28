# DirectPilot development instructions

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
14. Never validate migrations against `sales_assistant.db`; use a fresh temporary validation database.
15. Do not perform Git mutations unless the user explicitly requests them.
16. Do not claim scalability, test success, or provider support without evidence.
17. Preserve foundation boundaries and do not implement future capability merely because its architecture is documented.
18. Treat public UUID-style identifiers as API boundaries and internal numeric identifiers as persistence details.
