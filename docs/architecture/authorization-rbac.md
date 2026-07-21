# Production RBAC and Authorization Architecture

## Purpose and security boundary

The authorization package under `app/authz` is the single reusable policy
boundary for platform and tenant permissions. It is deny-by-default and is
usable from FastAPI dependencies, internal services, administration tools, and
future authenticated identity adapters. Authentication answers *who the caller
is*; authorization answers *whether that authenticated principal may perform a
specific action*. Neither substitutes for the other.

The implementation never grants access because a client supplies a role name or
tenant ID. HTTP tenant identity must come from trusted server-side
`TenantContext`; CLI tenant identity is resolved from an explicit Store slug.
Protected cross-tenant operations return the same permission-denied response as
other authorization failures and do not disclose resource existence.

## Principal model

`AuthorizationPrincipal` is an immutable request/service identity containing:

- a stable `subject_id`;
- a `PrincipalType` (`user`, `provider_admin`, `service_account`, `api_key`, or
  `anonymous`);
- authentication state;
- optional trusted tenant and membership identifiers;
- temporary server-generated bootstrap roles used only by the local provider
  compatibility adapter.

FOUNDATION-04 now resolves persistent `UserIdentity` records through opaque
sessions into this abstraction; future providers can use the same boundary.
Anonymous principals are always denied. Direct permission grants are not
implemented; all grants resolve through role-to-permission mappings. See
[authentication-identity.md](authentication-identity.md).

## Permission codes and scopes

Codes are stable lowercase dot-separated identifiers and are defined centrally
in `app/authz/permissions.py`. Labels and role names are never authorization
rules. Catalog construction rejects invalid or duplicate codes and rejects a
role mapped to a permission of another scope.

Platform permissions:

- `tenant.create`, `tenant.read`, `tenant.update`, `tenant.disable`,
  `tenant.provision`, `tenant.access_manage`
- `platform.audit_read`, `platform.access_manage`,
  `platform.settings_manage`
- `module.catalog_manage`

Tenant permissions:

- `tenant.settings_read`, `tenant.settings_update`
- `tenant.members_read`, `tenant.members_manage`
- `module.entitlement_read`, `module.entitlement_manage`
- `product.read`, `product.manage`
- `content.read`, `content.manage`
- `connector.read`, `connector.manage`
- `conversation.read`, `conversation.manage`
- `order.read`, `order.manage`
- `analytics.read`, `audit.read`

Platform and tenant scope are distinct. A platform permission does not silently
become a tenant permission. The one explicit provider-wide access-management
policy is `tenant.access_manage`, which permits the role-assignment service to
manage roles for an explicitly resolved tenant; it is not general tenant data
access.

## Roles and membership

System roles are relational records seeded from the immutable catalog:

| Scope | Roles |
| --- | --- |
| Platform | `platform_super_admin`, `platform_operator`, `platform_auditor` |
| Tenant | `tenant_owner`, `tenant_admin`, `tenant_operator`, `tenant_content_manager`, `tenant_analyst`, `tenant_viewer` |

`platform_super_admin` contains a finite, explicit set of platform permissions;
there is no wildcard and no unconditional service bypass. Tenant roles never
authorize another tenant.

`TenantMembership` connects one principal to one Store and has an explicit
status. An active membership grants no permission by itself. Active tenant role
assignments attached to that membership are required. Disabled membership or
revoked assignment is denied. Database uniqueness constraints prevent duplicate
membership and role assignments.

Custom role administration is deferred. The schema's non-enum role table and
role-permission join table permit a reviewed future design without changing the
decision model.

## Decision flow

For every check, `AuthorizationService`:

1. normalizes and resolves the permission from the central catalog;
2. denies unknown permissions;
3. denies anonymous or unauthenticated principals;
4. determines platform or tenant scope from the permission definition;
5. for tenant permissions, requires an explicit trusted tenant and rejects
   principal/membership tenant mismatch;
6. loads active assignments and relational role permissions;
7. returns a deterministic `AuthorizationDecision` with a safe reason code and
   sorted effective permissions.

`check()` never commits. `require()` raises `PermissionDeniedError` on denial.
Callers outside HTTP use the same API with an explicit SQLAlchemy session.
Routine checks do not create audit rows and never log payloads or credentials.

## HTTP and service integration

`require_permission(code)` is the generic FastAPI guard. It returns 401 for an
anonymous caller and 403 with constant `Permission denied` detail for an
authenticated unauthorized caller. Tenant scope is derived only from trusted
request state.

`require_admin_permission(code, mutation=...)` first runs the existing local
provider-admin authentication. Mutation routes retain loopback, same-origin,
and Fetch Metadata protections. Only after authentication does the adapter map
the caller to an explicit platform principal and invoke RBAC.

The first migrated high-risk provider routes are Store inventory/provisioning,
Store module-entitlement mutation, and module-catalog mutation. Other legacy
admin routes retain their existing authentication and should be migrated in
small permission-reviewed batches.

Internal write services must call `AuthorizationService.require()` before
loading or mutating protected resources. Route checks alone are not sufficient
for reusable business operations.

## Module entitlement policy

A Store module entitlement answers whether the tenant purchased or enabled a
capability. A permission answers whether this principal may act. They are
independent. `app/authz/policy.py` composes both checks for module-protected
operations: an active entitlement does not bypass RBAC, and a permission does
not enable an unentitled module.

## Relational schema and migration

Revision `0003_authorization_rbac` creates:

- `auth_permissions`
- `auth_roles`
- `auth_role_permissions`
- `auth_platform_role_assignments`
- `tenant_memberships`
- `auth_tenant_role_assignments`
- `auth_audit_logs`

Foreign keys, tenant/principal lookup indexes, timestamps, assignment status,
and unique natural-key constraints are included. No credentials or request
payloads are stored. The revision follows `0002_create_seed_history`, preserves
one Alembic head, and has a complete downgrade.

## Seed ownership

The explicit seed framework owns `system.auth_permissions`,
`system.auth_roles`, and `system.auth_role_permissions`. They are global,
create-only, idempotent, and production-safe. Stable codes are their natural
keys. They create no identities, memberships, tenant business data, or secrets,
and never run at application startup.

Catalog changes require code review, a versioned seed change, migration-policy
validation, and authorization regression tests. Existing database definitions
are preserved by create-only ownership; changing seed-owned mappings requires a
future explicit reconciliation policy rather than a silent startup repair.

## Tenant provisioning and initial owner

Provisioning creates the Store, module defaults, verification evidence, and
audit within its existing transaction. It creates no tenant membership or owner
assignment because the request has no authenticated owner principal. Onboarding
must explicitly assign `tenant_owner` afterward. No user is inferred, selected,
or created automatically.

## Role assignment, audit, and transactions

`RoleAssignmentService` owns one clean SQLAlchemy transaction per mutation. It
validates principal type, role existence, role scope, explicit tenant identity,
and the actor's access-management permission. Assignment and revocation are
idempotent; database constraints remain authoritative under races.

Successful and unchanged operations write a credential-free `AuthAuditLog`
containing safe actor/target identifiers, tenant ID when applicable, action,
role code, outcome, and timestamp. Audit-write failure, permission lookup
failure, or any other mutation failure rolls back the assignment. Integrity
conflicts are translated without exposing SQL.

## CLI and first-super-admin bootstrap

The administration CLI requires an explicit database choice and a database at
Alembic head. It never creates an identity or chooses a tenant implicitly:

```powershell
python -m tools.manage_access list-permissions `
  --database-url "sqlite:///./access.db"

python -m tools.manage_access assign-role `
  --principal-type provider_admin `
  --principal-id admin-1 `
  --role platform_operator `
  --database-url "sqlite:///./access.db"

python -m tools.manage_access assign-role `
  --principal-type user `
  --principal-id user-1 `
  --tenant demo-store `
  --role tenant_admin `
  --database-url "sqlite:///./access.db"
```

Commands include `list-permissions`, `list-roles`,
`show-effective-permissions`, `assign-role`, and `revoke-role`, plus JSON output.
Exit codes are 0 success, 1 execution/database failure, 2 validation failure,
and 3 assignment conflict. Output does not echo database URLs or credentials.

During migration,
the already-authenticated development-only local provider admin is mapped
server-side to the finite `platform_super_admin` catalog role. The controlled
CLI uses the same explicit bootstrap authority so an operator can assign the
first persistent platform principal after migrations and authorization seeds.
This is a documented compatibility adapter, not a public bypass. Replace it
with verified persistent administration, then remove the adapter after at least
one tested persistent super-admin exists. A future OIDC provider must resolve
through the same principal boundary.

## Concurrency and database behavior

Application pre-checks provide readable validation; unique constraints provide
the final duplicate guard. SQLite is suitable for deterministic tests but has
coarse write locking and limited concurrency semantics. Before PostgreSQL
launch, test concurrent assignment/revocation, foreign-key behavior, transaction
isolation, lock timeouts, constraint-name classification, and audit rollback on
a disposable PostgreSQL service. Consider `INSERT ... ON CONFLICT` only after
preserving the same idempotent result and audit contract.

## Security rules

- deny by default and deny unknown permission codes;
- no client-provided role grants or unvalidated tenant selection;
- no wildcard permission or implicit super-admin bypass;
- no public access-management endpoints;
- no password, token, authorization header, database URL, stack trace, or full
  payload in authorization logs/audit;
- no hidden commit, global mutable session, startup seed, or default owner;
- preserve Instagram gateway safe logging and existing authentication controls;
- use constant 403 behavior where resource existence could leak.

## Roadmap

1. Migrate remaining high-risk legacy admin operations after defining their
   exact platform/tenant ownership.
2. Introduce a production authentication adapter (OIDC/OAuth) that maps verified
   immutable subject claims to `AuthorizationPrincipal`.
3. Add API-key/service-account authentication with hashed/revocable credentials;
   reuse this RBAC engine without accepting role claims from the key.
4. Design custom tenant roles with protected system-role invariants, lifecycle,
   optimistic concurrency, and audit.
5. Add PostgreSQL concurrency and operational recovery tests.
6. Remove the local bootstrap adapter after the production identity migration
   and first-super-admin runbook have been exercised.
