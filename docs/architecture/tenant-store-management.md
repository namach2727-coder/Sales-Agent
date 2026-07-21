# Tenant and Store Management

This document describes the production tenant and store boundary introduced by
FOUNDATION-05. A tenant is the commercial and authorization boundary. A store is
an operational sales channel owned by exactly one tenant.

## Boundary model

- `Tenant` owns one or more `Store` records.
- Tenant slugs and public IDs are globally unique.
- Store slugs are unique inside a tenant; subdomains and custom domains are
  globally unique.
- Public APIs use opaque public IDs. Integer primary keys remain internal.
- Every store lookup is constrained by its tenant before authorization results
  are returned, preventing cross-tenant resource discovery.

## Membership and store access

`TenantMembership` grants an identity access to a tenant. Roles supply tenant
permissions through the existing RBAC engine. A membership can either have
`all_store_access` or explicit active `StoreAccessAssignment` rows. Membership
states are `invited`, `active`, `suspended`, and `revoked`.

Platform administrators retain explicit platform-scoped permissions; being a
platform user does not silently create tenant membership.

## Lifecycle

Tenants and stores support `active`, `suspended`, and `archived`. Suspended or
archived resources are blocked from operational resolution. Lifecycle actions
record timestamps and credential-free audit events. Archived resources are not
reactivated implicitly.

## Atomic bootstrap

Bootstrap requires an existing active, verified identity. One transaction
creates the tenant, first store, owner membership, owner role assignment, store
access assignment, and audit records. Any failure rolls the complete operation
back. It never creates or prints credentials.

Example after migrating and seeding authorization definitions:

```powershell
python -m tools.bootstrap_tenant --database-url $env:DATABASE_URL `
  --owner-email owner@example.com --tenant-name "Example Commerce" `
  --tenant-slug example --store-name "Main Store" --store-slug main
```

## Context resolution

`app.tenant_management.context.resolve_authorized_context` is the shared
resolution path for tenant/store APIs. It validates tenant membership, RBAC,
explicit store assignment, and lifecycle status. Unknown and unauthorized
resources both return the same non-disclosing not-found result. Domain lookup
returns active stores only.

## API surface

The `/api/v1` API provides typed tenant, store, membership, lifecycle, and
bootstrap operations. Collection endpoints use bounded offset/limit pagination
and optional status/search filters. Tenant and store public IDs are the external
resource identifiers.

## Migration and deployment

Migration `0005_tenant_store_management` creates tenants, backfills a tenant for
each legacy store, evolves existing membership/audit foreign keys, and creates
store access and tenant audit tables. Existing migration history is immutable.

Before deployment:

```powershell
python -m tools.migration_policy
alembic upgrade head
python -m tools.seed_data --profile production --database-url $env:DATABASE_URL
```

SQLite is supported for development, automated tests, and temporary migration
validation only. Production and UAT use PostgreSQL. Do not run migration
validation against the persistent local `sales_assistant.db` file.
