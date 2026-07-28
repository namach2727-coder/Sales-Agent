# Business Profile and Knowledge

## Status and scope

FOUNDATION-07 implements the store-owned information that future DirectPilot
capabilities may consume. It is a management domain only. It does not perform
AI inference, retrieval, embeddings, chat, Instagram processing, analytics, or
catalog association.

The module lives in `app/business_knowledge` and owns four aggregates:

| Aggregate | Purpose | Store uniqueness |
|---|---|---|
| `BusinessProfile` | Business identity, description, contacts, address, and working hours | One profile per Store |
| `BusinessPolicy` | Typed operational policy content | `(store_id, code)` |
| `BusinessFAQ` | Curated question, answer, and bounded keywords | `(store_id, normalized_question)` |
| `BusinessKnowledgeEntry` | Structured fact, instruction, reference, or custom content | `(store_id, slug)` |

Legacy `FAQ`, `TrainingDraft`, `KnowledgeVersion`, and `KnowledgeItem` records
remain unchanged. There is intentionally no automatic migration or runtime
bridge between those entities and FOUNDATION-07.

## Trust and ownership boundaries

Tenant and Store identity come exclusively from authenticated path resolution:

```text
authenticated principal
        |
        v
tenant public ID + store public ID
        |
        v
resolve_authorized_context(operational=False)
        |
        +-- tenant permission or explicit provider permission
        +-- active membership
        +-- all-store access or explicit active Store assignment
        |
        v
BusinessKnowledgeService(tenant_id, store_id, lifecycle states, actor)
```

Clients cannot send internal Tenant, Store, or actor identifiers. Responses
contain opaque `public_id` values only. All resource selects contain both
`tenant_id` and `store_id`; unknown, wrong-Store, and cross-Tenant public IDs
share the same safe `404 not_found` contract.

Each table denormalizes `tenant_id`. A composite foreign key from
`(store_id, tenant_id)` to `stores(id, tenant_id)` prevents a resource from
being attached to a Store owned by another Tenant. Store-scoped unique
constraints prevent identifiers from colliding inside a Store while allowing
the same identifier in separate Stores.

## Persistence model

Revision `0007_business_profile_knowledge` creates exactly:

- `business_profiles`
- `business_policies`
- `business_faqs`
- `business_knowledge_entries`

Every table has:

- internal integer `id`;
- globally unique opaque `public_id`;
- non-null `tenant_id` and `store_id`;
- `draft`, `published`, or `archived` status;
- integer `revision >= 1`;
- creation and update timestamps;
- state-consistent `published_at` and `archived_at`;
- compound Tenant/Store/status indexes.

Policies constrain the initial types `shipping`, `returns`, `refunds`,
`payment`, `warranty`, `service`, `privacy`, and `custom`. Knowledge entries
constrain `fact`, `instruction`, `reference`, and `custom`.

FAQ and entry keywords use a JSON string list. They are application-validated
to at most 25 values of at most 100 characters each. They are not a search
index, embedding, or vector representation.

There is no hard-delete operation or DELETE API. Archival is an audited
lifecycle transition.

## Validation

Transport-independent validation is centralized in `domain.py`:

- Unicode is normalized with NFKC.
- Display whitespace is collapsed.
- FAQ uniqueness uses the case-folded normalized question.
- Codes and slugs are stable lowercase identifiers.
- Email, HTTP(S) URL, and phone values are normalized without additional
  dependencies.
- Persian and other Unicode decimal digits in phone values become ASCII.
- Duplicate keywords are removed case-insensitively while preserving order.
- Field lengths, keyword count, and priority are bounded.
- HTML tags, NUL characters, and executable URL schemes are rejected.

Pydantic schemas provide the first request boundary; domain validators remain
authoritative for non-HTTP callers.

## Lifecycle and concurrency

New resources always start in `draft`.

| Current | Allowed target | Notes |
|---|---|---|
| `draft` | `published`, `archived` | Publishing validates required content |
| `published` | `draft`, `archived` | Both require `knowledge.publish` |
| `archived` | `draft` | Direct republish is forbidden |

Only draft resources can be edited. Returning to draft clears both lifecycle
timestamps. Publishing sets only `published_at`; archiving sets only
`archived_at`.

Every mutation requires `expected_revision`. Creation requires zero and stored
resources start at one. Update and transition requests must match the stored
revision or receive `409 stale_write`. SQLAlchemy mapper version checks also
protect two sessions that both loaded the same revision; a racing second
writer is translated to the same safe conflict.

Domain mutation and `TenantAuditLog` insertion share a single transaction.
Audit details contain the resource public ID, action, changed field names,
status changes, and revision. Full profile, policy, FAQ, or entry content is
never copied to audit details.

## Store lifecycle policy

This module deliberately resolves with `operational=False`, then applies its own
state policy:

| Store state | Read | Mutate |
|---|---:|---:|
| `onboarding` | yes | yes |
| `active` | yes | yes |
| `suspended` | yes | no |
| `archived` | safe 404 | safe 404 |
| `deleted` or `deleted_at` set | safe 404 | safe 404 |

The Tenant itself must remain active. Other Store states are denied. This
policy permits knowledge preparation during onboarding without weakening the
normal Store assignment boundary.

## Authorization

The central authorization catalog owns the five permissions:

- `business_profile.read`
- `business_profile.manage`
- `knowledge.read`
- `knowledge.manage`
- `knowledge.publish`

Role grants are finite and deny by default:

| Role | Profile read | Profile manage | Knowledge read | Knowledge manage | Publish |
|---|---:|---:|---:|---:|---:|
| `tenant_owner` | yes | yes | yes | yes | yes |
| `tenant_admin` | yes | yes | yes | yes | yes |
| `tenant_operator` | yes | yes | yes | yes | no |
| `tenant_content_manager` | yes | yes | yes | yes | yes |
| `tenant_analyst` | yes | no | yes | no | no |
| `tenant_viewer` | yes | no | yes | no | no |
| `store_manager` | yes | yes | yes | yes | yes |
| `operator` | yes | no | yes | no | no |
| `read_only` | yes | no | yes | no | no |

A role permission never bypasses Store assignment. Provider read and mutation
access continue to require the existing `tenant.read` and `tenant.update`
platform permissions. There are no wildcard or FOUNDATION-specific bypasses.

## REST API

Base path:

```text
/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/business-knowledge
```

Profile:

- `POST /profile`
- `GET /profile`
- `PATCH /profile`
- `POST /profile/transitions`

Policies, FAQs, and entries each expose create, list, read, draft update, and
transition endpoints. List endpoints support `page`, `page_size` (maximum
100), `status`, and `search`; policies also support `policy_type`, and entries
support `entry_type`. Ordering is deterministic by priority then internal row
order, while internal IDs never leave the service.

Validation errors return `422`, stale writes and invalid lifecycle operations
return `409`, denied state/publish operations return `403`, and unresolvable
scope or resource lookups return safe `404`.

## Deployment and migration

The linear migration chain is:

```text
0001_baseline_schema
  -> 0002_create_seed_history
  -> 0003_authorization_rbac
  -> 0004_authentication_identity
  -> 0005_tenant_store_management
  -> 0006_lean_business_catalog
  -> 0007_business_profile_knowledge
```

Run the normal production controls:

```powershell
alembic heads
python -m tools.migration_policy
python -m tools.seed_data --profile production --database-url $env:DATABASE_URL
```

Migration 0007 inserts no permission or business rows. The existing
production-safe seed framework consumes the central permission and role
catalogs idempotently.

## Verification

`tests/test_business_knowledge.py` covers normalization, unsafe markup,
singleton behavior, CRUD, uniqueness, filters, pagination, lifecycle
timestamps, revision conflicts, concurrent writers, audit minimization,
database constraints, composite Tenant/Store integrity, Store states, role
grants, public schemas, endpoint inventory, assignment enforcement, and safe
cross-Tenant responses.

Migration policy tests validate one head, metadata parity, a clean
base-to-head upgrade, downgrade, and re-upgrade on disposable SQLite databases.
PostgreSQL DDL must compile before release; a disposable live PostgreSQL
upgrade remains an environment-dependent deployment validation.

## Explicit non-goals and future integration

FOUNDATION-07 does not decide how published content will be retrieved or used.
Future foundations must consume this domain through a separately approved
contract and must not mutate its rows directly. In particular, this module
contains no AI provider, prompt, embedding, vector, Instagram, queue,
conversation, analytics, Product, or SKU dependency.
