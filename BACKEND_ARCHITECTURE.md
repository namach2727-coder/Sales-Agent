# DirectPilot MVP Backend Architecture

## Purpose

DirectPilot is a multi-tenant AI sales assistant for Instagram Professional
accounts. The backend is a FastAPI modular monolith. It is not a generic bot
platform and Instagram through official Meta APIs is the only MVP channel.

## Runtime flow

`Meta webhook -> restricted public gateway -> signature verification -> tenant/store connection routing -> deduplicated inbound event -> conversation/message -> approved business knowledge -> prompt package -> configured LLM provider -> assistant message -> outbound delivery boundary -> Meta Graph API`

`META_SEND_ENABLED` is enforced at the shared outbound boundary and must fail
closed before a network mutation.

## Modules

- `app/authentication`, `app/authz`: Argon2id identities, opaque sessions, RBAC.
- `app/tenant_management`: trusted tenant/store resolution and lifecycle.
- `app/commerce`: registration, plans, orders, manual payments, subscriptions.
- `app/catalog`, `app/business_knowledge`: approved store facts used by AI.
- `app/instagram_onboarding`: official Instagram Login OAuth; it writes into the
  existing encrypted `InstagramConnection` model.
- `app/instagram_channel`: connection lifecycle, webhook security, routing and
  ingestion.
- `app/conversation_core`, `app/application`: conversation persistence and
  application orchestration.
- `app/infrastructure/llm`, `app/infrastructure/outbound`: provider adapters.

## Boundaries and invariants

- REST exposes public UUID-style IDs only. Integer IDs are persistence details.
- Tenant-bound queries include trusted tenant and store criteria.
- SQLAlchemy and Alembic remain the portable PostgreSQL boundary.
- Repositories/services do not introduce a second transaction architecture.
- Credentials are encrypted at rest and never returned by public schemas.
- The customer frontend remains in the separate `directpilot-web` repository.

## Deployment topology

The production target is a long-running Python service at
`https://api.directpilot.ir`, a restricted Instagram gateway, managed
PostgreSQL, private receipt storage and the configured LLM provider. UAT's
Tailscale Funnel is not a production architecture.
