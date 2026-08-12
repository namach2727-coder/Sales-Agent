# DirectPilot Database

## Technology and migration policy

PostgreSQL is the deployed database; SQLite remains a local development and
unit-test option. `DATABASE_URL` is the only application database contract.
Every schema change is an Alembic revision and deployed startup fails if the
database is not at the single migration head. `create_all()` is not a
production migration mechanism.

Current head: `0011_instagram_oauth_onboarding`.

## Tenant ownership

`Tenant` owns stores and memberships. Tenant/store-scoped data carries internal
foreign keys, while APIs resolve and return public IDs. Compound foreign keys
on critical store records prevent a store from being attached to the wrong
tenant.

## Sellable MVP records

- `saas_plans`: authoritative prices and limits.
- `subscription_orders`: immutable price snapshot for a plan purchase.
- `manual_payments`: receipt metadata and review lifecycle; never receipt bytes.
- `tenant_subscriptions`: active limits and entitlement source.
- `commerce_audit_logs`: credential-free transition audit.
- `instagram_oauth_states`: SHA-256 digest of short-lived, single-use OAuth
  state. Raw state and OAuth codes are never persisted.
- `instagram_connections`: the existing encrypted per-store Meta credential.

## Operations

Before release, validate `alembic upgrade head` from an empty PostgreSQL test
database and run `python -m tools.migration_policy`. Production backup policy:
daily managed snapshots, point-in-time recovery when available, quarterly
restore rehearsal, documented retention and restricted backup credentials.
Neither UAT nor production databases may be reset as part of validation.
