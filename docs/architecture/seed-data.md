# Production Seed Data Framework

## Purpose

Alembic owns database schema. The explicit seed framework owns minimal,
environment-aware system and tenant defaults. Seed data is never embedded in a
schema migration, and application or webhook startup never invokes a seed.

Run seeds only through the reviewed command:

    python -m tools.seed_data ...

The deprecated `SEED_DEMO_DATA` setting is retained for configuration
compatibility but is ignored. It cannot enable startup seeding.

Admin read paths never repair missing catalogs or tenant defaults. They return a
service-unavailable/not-found response when explicit initialization has not been
performed. Explicit admin mutation/provisioning remains a separate business
operation, not a hidden read-time seed.

## Profiles

Every seed explicitly lists compatible profiles and whether it is production
safe. Safety is metadata, never inferred from a name.

| Profile | Intended use | Policy |
| --- | --- | --- |
| `production` | Minimal operational defaults | Only explicitly production-safe seeds run. |
| `development` | Local engineering environments | Compatible production-safe and development seeds may run. |
| `test` | Deterministic disposable fixtures | Only explicitly test-compatible seeds run. |
| `demo` | Isolated demonstration environments | Demo-compatible seeds may run; never select them in production. |

Unknown profiles fail. A named seed that is incompatible with the selected
profile fails rather than being silently ignored.

## Scopes and tenant resolution

`global` seeds manage provider/system records and do not require a tenant.
`tenant` seeds require `--tenant STORE_SLUG`. The runner resolves that slug
through the trusted internal tenant resolver, rejects unknown/inactive tenants,
and supplies a complete `TenantContext` to the handler.

Tenant handlers must include `context.tenant_id` in every tenant-owned lookup and
write. They must never use a default tenant. Reports expose only the selected
tenant slug and aggregate counters, not another tenant's records.

When no named seeds and no tenant are supplied, the runner selects only compatible
global seeds. Supplying a tenant includes compatible global and tenant seeds in
dependency order. Explicitly naming a tenant seed without `--tenant` fails.

## Initial seeds

The registry intentionally starts small:

- `system.module_definitions` (`global`, version 1): creates missing provider
  module definitions using stable `ModuleDefinition.code` keys.
- `tenant.module_entitlements` (`tenant`, version 1): creates missing inactive
  `StoreModule` rows for one resolved tenant using the existing unique
  `(store_id, module_code)` constraint. It depends on the global module catalog.

No production seed creates customers, leads, orders, conversations, messages,
products, FAQs, social-media connections, credentials, or tokens. Existing MVP
demo catalog helpers remain legacy application utilities; they are not registered
as production seeds. Product and FAQ models are not yet tenant-owned, so adding a
multi-tenant demo catalog seed would be unsafe and is deferred.

## Ownership and idempotency

Each `SeedDefinition` declares one ownership mode:

- `create_only`: create missing natural keys and preserve all existing fields.
- `upsert_seed_owned`: update only fields explicitly documented as seed-owned.
- `verify_only`: verify required data without mutating it.

Both initial seeds are `create_only`. Provider edits to module names, prices,
availability, or limits are not overwritten. Re-running a seed reports
`created`, `updated`, `unchanged`, or `skipped` and never intentionally creates a
duplicate. Stable model constraints remain the final concurrency guard.

Random identifiers are not used as seed keys. A new seed must document its
natural key, owned fields, version, profiles, production-safety status, scope,
dependencies, and retry behavior.

## Transactions, retry, and audit history

Normal execution uses one transaction per seed. Successful data changes and the
corresponding `seed_history` row commit atomically. A failure rolls back the
entire seed, then records a separate credential-free failed audit entry. This
boundary makes retry and failure ownership clear; previously completed seeds are
not rolled back when a later independent seed fails.

One retry is attempted after an integrity conflict so a concurrent create can be
re-read as unchanged. Database uniqueness constraints provide the authoritative
duplicate protection. SQLite is adequate for deterministic local testing but
does not provide the production concurrency guarantees expected from PostgreSQL.

`seed_history` is introduced by `0002_create_seed_history` and records seed name,
version, profile, scope, optional tenant ID, status, timestamps, and a bounded
safe summary. It stores no database URLs, exception messages, credentials, or
secrets. History is audit evidence, not the idempotency mechanism; natural keys
remain authoritative.

## Dry-run

Dry-run validates selection, profile compatibility, dependencies, tenant
resolution, handler execution, and database constraints. All selected seeds run
in deterministic order inside one transaction so dependent seeds can observe
earlier intended changes. The transaction is always rolled back, and no history
row is written.

    python -m tools.seed_data --profile development --dry-run \
      --database-url sqlite:///./disposable.db

Always verify the database is already migrated to Alembic head.

## CLI usage

List seeds without opening a database:

    python -m tools.seed_data --list

Run safe global production defaults:

    python -m tools.seed_data --profile production \
      --database-url postgresql+driver://USER:PASSWORD@HOST/DB

Provision defaults for an existing tenant:

    python -m tools.seed_data --profile production --tenant store-slug \
      --database-url postgresql+driver://USER:PASSWORD@HOST/DB

Select named seeds:

    python -m tools.seed_data --profile development \
      --seed system.module_definitions --database-url sqlite:///./local.db

Using the application's configured database requires a conspicuous opt-in:

    python -m tools.seed_data --profile production --use-configured-database

Execution never silently falls back to `DATABASE_URL`. Output never echoes a
database URL. Prefer an injected environment secret over placing credentials in
shell history.

## Adding and testing a seed

1. Add a focused handler under `tools/seeding/seeds/`.
2. Use a stable natural key and tenant-qualified predicates where applicable.
3. Return a `SeedMutation` with accurate counters and a credential-free summary.
4. Register a `SeedDefinition` with explicit scope, profiles, safety, ownership,
   version, order, and dependencies.
5. Test first run, second run, user-field preservation, dry-run, rollback, profile
   rejection, tenant isolation, and concurrency constraints on a migrated
   disposable database.
6. Run `python -m tools.migration_policy` and the complete test suite.

Do not call `commit()` inside a handler; the runner owns the transaction. Do not
catch and suppress handler exceptions.

## Safe production and tenant provisioning

Apply schema migrations before seeds. Run one reviewed seed job with the least
database privileges needed, capture its safe report, and verify `seed_history`.
For a new tenant, create the `Store` through the trusted provisioning workflow,
then run tenant seeds with its explicit slug. Never create or infer a default
production tenant.

Development/demo profiles must use isolated databases. A production invocation
rejects every definition whose `production_safe` flag is false even if profile
metadata was configured incorrectly.

## Failure recovery

The failed seed's writes are rolled back. Inspect the safe audit record and
protected application logs, correct the cause, and rerun the same seed; natural
keys make retry deterministic. Do not delete unrelated tenant data or edit
`seed_history` to pretend success. If a prior seed completed before a later seed
failed, treat it as committed and idempotently rerun the selection.

## Prohibited content and secrets policy

Seeds must never contain or report:

- access/API/bot tokens, signing secrets, passwords, or private keys;
- real customer, lead, order, payment, message, or social-media data;
- production database URLs or credentials;
- environment-specific connector accounts;
- cross-tenant record details in summaries.

Summary keys containing secret, password, token, credential, or database URL
markers are redacted before persistence. This safeguard does not replace code
review: secret values must never be passed to a seed summary in the first place.

## PostgreSQL future strategy

Before production PostgreSQL deployment, run seeds concurrently in CI against a
temporary PostgreSQL service and adopt native conflict handling where useful
(`INSERT ... ON CONFLICT`, row/advisory locks, or serializable provisioning
transactions). Keep unique constraints as the final authority, bound lock waits,
and verify failed-history recording under deadlocks and connection loss.
