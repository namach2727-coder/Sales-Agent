# Production Tenant Provisioning

## Purpose

`TenantProvisioningService` is the controlled workflow for creating a commercial
tenant (`Store`). It is reusable by the provider admin route,
`tools.provision_tenant`, tests, and future onboarding or internal tools. It does
not depend on FastAPI request objects and never runs during application startup.

Legacy demo/test helpers such as `ensure_default_store()` remain for MVP
compatibility. They are not a production provisioning path and must not infer a
default production tenant.

## Lifecycle

The existing `Store.status` supports the required lifecycle without a migration:

- `provisioning`: temporary state inside the uncommitted transaction;
- `active`: assigned only after seeds, entitlements, and verification succeed;
- `disabled`, `suspended`, and `deleted`: existing inactive operational states.

There is no committed `failed` tenant in this phase. A failure rolls back the
tenant, entitlements, seed history, and audit. Durable failed/resume state is
deferred to a separately designed workflow.

## Request model and identity

`TenantProvisioningRequest` contains only fields supported by the current model:

- `name`: required display name, trimmed, maximum 200 characters;
- `slug`: required tenant identity and subdomain label;
- `profile`: explicit `production`, `development`, `test`, or `demo` profile;
- `requested_module_codes`: optional module codes to activate.

No credentials, access tokens, connector accounts, customer records, fake
orders, or social-media data are accepted or provisioned.

Provisioning also does not infer an owner identity. When no explicit owner
principal is part of the contract (the current state), it creates no
`TenantMembership` and no tenant role assignment. Onboarding must explicitly
assign `tenant_owner` through the authorization administration workflow after
the Store commits. Membership alone would still grant no permission. See
[authorization-rbac.md](authorization-rbac.md).

Persistent identities do not change this rule. Onboarding explicitly adds the
user membership with `tools.manage_identities`, then assigns the tenant role
with `tools.manage_access`; provisioning never infers an owner from email,
session, or caller.

## Slug rules and reserved names

Slugs are trimmed and lowercased. A valid slug is 1 through 63 ASCII characters,
contains only lowercase letters, digits, and single hyphens, begins and ends
with a letter or digit, has no `--`, and is not reserved.

The canonical set is `RESERVED_STORE_SLUGS` in `app.tenancy`: `admin`, `api`,
`app`, `auth`, `docs`, `health`, `internal`, `login`, `logout`, `media`,
`openapi`, `public`, `static`, `system`, `webhook`, `webhooks`, and `www`.
Future externally routable system labels must be added there.

Every trusted path stores lowercase. A case-insensitive pre-check provides a
clear conflict, while the existing unique `stores.slug` index is final race
protection. An `IntegrityError` is translated without exposing SQL. The
pre-check alone is not considered concurrency protection.

## Transaction ownership

The service owns exactly one transaction and requires a session with no active
transaction. It commits once on success, or rolls back once on dry-run and every
failure. Seed handlers and routes do not commit. This prevents partial tenants,
entitlements, settings, history, or misleading success audits.

SQLite implements local/test behavior. PostgreSQL must retain this boundary and
add an appropriate isolation or slug-locking policy for expected contention.

## Deterministic steps

1. `validate_identity`: case-insensitive existence check.
2. `create_tenant`: insert `Store(status="provisioning")` and flush its ID.
3. `establish_tenant_context`: build an explicit trusted `TenantContext`.
4. `run_tenant_seeds`: run the dependency chain in the same session.
5. `configure_modules`: validate, expand dependencies, and activate selection.
6. `verify_tenant`: verify identity, scope, seeds, and entitlements.
7. `finalize_tenant`: set `active`.
8. `record_audit`: add a credential-free success record.

`TenantProvisioningStep` plus constructor-level handler injection lets tests
fail one step without a deployed failure flag or production backdoor.

## Seed integration

Provisioning selects `tenant.module_entitlements`; its dependency runs
`system.module_definitions` first. `SeedRunner.run_in_session()` accepts an
explicit tenant context and never opens, closes, commits, rolls back, or retries
the caller session. Its seed history shares the provisioning transaction. The
standalone seed CLI retains its existing transaction behavior.

The global history row has no tenant ID and the tenant entitlement history row
uses exactly the new tenant ID. No fake production business data is seeded.

## Module integration and defaults

`MODULE_SEEDS` remains the canonical built-in catalog; existing database module
definitions may extend it. Unknown, duplicate, non-sellable, and planned module
requests are rejected.

`DEFAULT_PROVISIONING_MODULES` is intentionally empty: no billable capability is
enabled implicitly. Explicit selections expand dependencies deterministically
and activate those entitlements; all others remain inactive. This preserves the
provider API's existing safe behavior and avoids enabling beta/planned features
by default.

## Dry-run

Dry-run executes normalization, conflict checks, seeds, entitlement planning,
verification, finalization, and audit construction, then rolls everything back.
The result is `planned` and lists steps, seeds, and modules. Tests prove no
`Store`, `StoreModule`, `ModuleDefinition`, `SeedHistory`, or `AdminAuditLog`
remains.

## CLI

The database must already be at Alembic head. Profile and database selection are
explicit:

```powershell
python -m tools.provision_tenant `
  --name "Validation Store" `
  --slug validation-store `
  --profile development `
  --dry-run `
  --database-url "sqlite:///./temp_provisioning_validation.db"
```

Use repeated `--module CODE`, optional `--json`, or explicit
`--use-configured-database`. Exit codes are `0` success, `1` execution/database
failure, `2` validation failure, and `3` conflict. Output never prints database
URLs or credentials.

## Admin API integration

Authorized `POST /admin/api/provider/stores` delegates to the service and keeps
its response and authorization. Optional `profile` and `modules` fields expose
the workflow without creating a public API. When profile is absent, this trusted
route maps configured application environment to an explicit supported profile.

## Audit, logging, and security

The final transaction step adds `AdminAuditLog(action="tenant_provisioned")`
with operation ID, profile, selected module codes, and completed step names. It
cannot survive failure or dry-run. Failures currently use protected application
logging rather than a separate transaction that could create misleading audit.

Logs may contain operation ID, canonical slug, step, status, and duration. They
must not contain database URLs, passwords, credentials, connector/API tokens,
authorization headers, complete payloads, or cross-tenant business data.

## Retry, recovery, and deferred repair

An existing slug is always a conflict: provisioning never treats it as success,
overwrites its name, or changes manager-owned modules. After a rolled-back
failure, operators inspect safe logs, correct the cause, confirm the slug does
not exist, and explicitly retry.

Automatic resume/repair is deferred. A future repair command needs separate
authorization, preservation rules, transaction semantics, and audit behavior.

## PostgreSQL considerations

Before launch, run migrations, provisioning, rollback, and concurrent-slug tests
against disposable PostgreSQL in CI. Retain the unique constraint, classify
constraint failures by name, evaluate `SERIALIZABLE` or slug-scoped advisory
locks, bound statement/lock timeouts, and verify JSON, time-zone, sequence,
deadlock, and connection-loss behavior. Migrations, global seeds, and tenant
provisioning remain separate controlled operations.
