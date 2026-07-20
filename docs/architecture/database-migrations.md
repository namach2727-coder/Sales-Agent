# Production Database Migration Policy

## Purpose and authority

Alembic is the authoritative history for production schema changes. SQLAlchemy
models are the runtime mapping; immutable Alembic revisions are the audited path
between schema versions. The current history has one root and one head:
`0001_baseline_schema`.

Application startup must never silently run Alembic migrations. Migrations are a
separate release operation with one owner. The current application still uses
`Base.metadata.create_all()` for backward-compatible local startup; that creates
missing tables but is not a production migration strategy and does not replace
`alembic upgrade head`.

`alembic/env.py` imports the application's single `Base.metadata`. Tests and the
policy command override the database URL with disposable SQLite files. Alembic
logging is configured only on the `alembic` logger and must not reset handlers
owned by the running application.

## Revision naming

Every revision filename and revision ID use the same value:

    NNNN_short_snake_case_description.py
    revision = "NNNN_short_snake_case_description"

Rules:

- `NNNN` is a zero-padded, sequential four-digit number.
- The slug starts with a lowercase ASCII letter.
- The slug contains only lowercase ASCII letters, digits, and single underscores.
- The recommended and enforced maximum slug length is 60 characters.
- The filename stem and `revision` value must match exactly.
- The current history is linear: each `down_revision` names the immediately
  preceding revision; branches, gaps, merge points, `branch_labels`, and
  `depends_on` are rejected.

Valid examples:

- `0001_baseline_schema.py`
- `0002_add_tenant_status.py`
- `0003_create_module_subscriptions.py`

Invalid examples:

- `2_add_status.py` — prefix is not four digits.
- `0002-Add-Status.py` — hyphens and uppercase characters are not allowed.
- `0002_add status.py` — spaces are not allowed.
- filename `0002_add_status.py` with revision `abc123` — values do not match.

Do not modify a revision that has been applied outside a disposable environment.
Create the next numbered revision instead.

## Creating and reviewing a migration

1. Make the approved SQLAlchemy model change.
2. Confirm the current graph is clean:

       python -m tools.migration_policy
       alembic heads
       alembic current

3. Generate a revision with the next compliant ID. Alembic's default random ID
   does not meet this repository's policy, so provide the ID explicitly. The
   repository's `file_template` makes the filename equal to that ID:

       alembic revision --autogenerate --rev-id 0002_add_tenant_status -m "add tenant status"

4. Treat autogenerate as a draft. Review every table, column, type, nullability,
   foreign key, unique constraint, index, server default, and data operation.
5. Implement and test `downgrade()`. If a downgrade is deliberately impossible,
   set `EMPTY_DOWNGRADE_ALLOWED = True` only with documented operational review.
6. Run the policy command, focused tests, and the full suite before review.
7. Commit the model and migration together after approval.

Never place credentials, production URLs, environment-specific values, or tenant
seed records in a migration.

## Applying migrations

### New empty database

Always build a new database by executing the full history:

    alembic upgrade head

Do not use `stamp` on an empty database. `stamp` only writes version state; it
does not create schema objects and would leave an empty database falsely marked
as current.

### Existing database onboarding

An existing database that already contains the baseline schema can be enrolled
only after backup, restore verification, and an independent schema comparison.
After operational approval:

    alembic stamp 0001_baseline_schema

Stamping does not validate or change schema. If the existing schema differs,
repair or explicitly migrate it before stamping. Never stamp merely to silence a
migration error.

### Production release

1. Confirm a tested backup and restore path.
2. Run `python -m tools.migration_policy` in CI.
3. Confirm exactly one expected head and record the current revision.
4. Quiesce writes when the migration plan requires it.
5. Run `alembic upgrade head` from one controlled release job.
6. Verify the resulting revision, application health, and critical queries.
7. Record revision, duration, operator, diagnostics, and rollback decision.

Multiple application replicas must never race to migrate during startup.

## Automated validation

Run from the repository root:

    python -m tools.migration_policy
    python -m pytest tests/test_alembic.py tests/test_migration_policy.py -v
    python -m pytest

The policy command performs these checks without reading `DATABASE_URL`:

- AST-based filename, revision metadata, and function-body validation.
- Exactly one root and head, one linear chain, unique IDs and filenames, no
  unresolved branches or merge points, and all revisions reachable.
- Forward-operation safety checks and multi-tenant `tenant_id` staging rules.
- Upgrade to head in a fresh temporary SQLite database.
- Alembic autogenerate comparison of migrated schema with registered SQLAlchemy
  metadata, with individual drift tuples printed as diagnostics.
- Upgrade to head, downgrade to base, and upgrade to head again in a disposable
  database, followed by another metadata comparison.

Exit code `0` means all checks passed. Any violation returns a non-zero code.
Temporary database URLs are never printed, and the normal application database
is never opened.

## Destructive-operation review

The validator identifies potentially destructive forward operations, including:

- `op.drop_table`, `op.drop_column`, and `op.drop_constraint`;
- column alteration or schema-object rename operations;
- dynamic SQL that cannot be proven safe;
- `op.execute` containing `DROP`, `TRUNCATE`, `DELETE`, `RENAME`, or `REPLACE`.

A deliberately reviewed revision may declare:

    DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = True

Acknowledgement does **not** make an operation safe. It only proves that the
author did not introduce it accidentally. Approval still requires impact
analysis, backups, restore evidence, lock/downtime estimates, data-preservation
or archival steps, observability, and a recovery owner. Destructive operations
in `downgrade()` are assessed through downgrade review because inverse removal
of objects created by `upgrade()` is normally expected.

Prefer expand-and-contract: add compatible schema, deploy dual-read/write code,
backfill, verify, then remove legacy schema in a later release.

## Downgrade expectations

Every revision needs a meaningful downgrade unless an explicit reviewed
exception sets `EMPTY_DOWNGRADE_ALLOWED = True`. A schema downgrade cannot
restore discarded or transformed data. For lossy revisions, use a tested
forward repair or restore from backup instead of assuming downgrade is recovery.

The baseline downgrade removes the complete application schema. It exists only
for empty disposable validation databases and must never run against a populated
environment.

## Multi-tenant migration principles

- Never add `tenant_id` as immediately non-nullable to a table that may contain
  rows. Add it nullable, deploy compatible code, backfill deterministically and
  restart-safely, verify every row, then enforce `NOT NULL` separately.
- Tenant-scoped unique constraints generally include `tenant_id`; document any
  truly global uniqueness rule.
- Indexes on tenant-owned tables should lead with or otherwise include
  `tenant_id` according to measured query patterns.
- Never assume a single/default tenant in schema or data migration logic.
- Backfills must be bounded, deterministic, observable, idempotent or safely
  restartable, and must record progress for large datasets.
- Schema migrations and tenant seed/configuration data are separate concerns.
- A migration must be compatible with mixed application versions when rolling
  deployments are used.

This policy enforces unsafe non-nullable `tenant_id` additions statically. Unique
constraint and index intent still require human review because ownership cannot
always be inferred from syntax.

## SQLite limitations and PostgreSQL readiness

SQLite is used for local validation. Alembic enables batch-compatible behavior,
but SQLite has limited `ALTER TABLE`, constraint alteration, locking, type, and
server-default semantics. A passing SQLite test is necessary, not proof that a
production migration is operationally safe.

Before PostgreSQL adoption, run the same history and drift checks against a
temporary PostgreSQL service in CI. Review transactional DDL, lock levels,
concurrent index creation, enum changes, sequence ownership, time zones, JSON
types, constraint validation, statement timeouts, and long-running backfills.
Keep revisions dialect-aware only where necessary and test every supported
dialect explicitly.

## Emergency recovery

1. Stop the migration job; do not repeatedly retry an unknown partial failure.
2. Preserve logs and record the database revision and transaction state without
   exposing credentials.
3. Pause application writes if continued writes may increase inconsistency.
4. Determine whether DDL rolled back; SQLite and PostgreSQL behavior may differ.
5. Choose among a tested downgrade, a forward repair revision, or restore from a
   verified backup. Never improvise a production `stamp` to bypass recovery.
6. Validate schema and critical data before resuming traffic.
7. Record the incident and add a regression test before the next release.

Escalate destructive, partial, or cross-tenant failures to the database and
application owners. Recovery decisions must account for data, not only schema.
