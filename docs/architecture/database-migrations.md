# Database Migrations

## Purpose

Alembic is the authoritative version history for production database schema changes. SQLAlchemy models remain the runtime mapping, while immutable Alembic revisions describe how an existing database moves between schema versions. FOUNDATION-02A records the current schema only; it introduces no business, tenancy or ownership change.

Application startup still calls SQLAlchemy create_all for backward compatibility during this foundation task. Production evolution must use Alembic, and a later deployment task may retire runtime table creation after all environments are migration-managed.

## Architecture

alembic/env.py imports Base from app.database and imports app.models only to register every ORM table in Base.metadata. target_metadata points directly to that metadata; Base is not duplicated. The database URL comes from the existing Settings/database_url mechanism. Tests may provide a Config attribute override so validation always targets a disposable database.

The baseline revision is a static snapshot. It does not import current models, seed records or execute application services. This prevents a historical migration from changing when future models change.

## Directory structure

- alembic.ini: command and logging configuration.
- alembic/env.py: online/offline environment and application metadata integration.
- alembic/script.py.mako: template for future revisions.
- alembic/versions/0001_baseline_schema.py: current-schema baseline.
- tests/test_alembic.py: graph, metadata and disposable-database validation.

## Migration lifecycle

1. Change models only as part of an approved schema task.
2. Generate one revision with autogenerate.
3. Review every operation; autogenerate is a draft, not approval.
4. Test upgrade on an empty database and a sanitized production-like copy.
5. Test the documented rollback path.
6. Commit model and migration together.
7. Apply migrations before deploying code that requires the new schema.

## Developer workflow

From the repository root:

    alembic current
    alembic heads
    alembic history
    alembic upgrade head
    alembic downgrade -1
    alembic revision --autogenerate -m "short schema description"

Set DATABASE_URL through the same environment/configuration mechanism used by the application. Never edit alembic.ini to point at a personal or production database.

## Production workflow and baseline adoption

For a new empty database, run alembic upgrade head.

For an existing database that already has the baseline tables, do not run the baseline upgrade over those tables. Back up the database, compare its schema with the baseline, and only after explicit operational approval run:

    alembic stamp 0001_baseline_schema

Stamping records version state without creating tables. It is safe only when the existing schema has been independently verified as equivalent. After adoption, normal releases run alembic upgrade head as a separate deployment step with exclusive migration ownership.

## Upgrade procedure

1. Confirm backup and restore readiness.
2. Confirm exactly one expected head.
3. Run alembic current and alembic history.
4. Apply alembic upgrade head in a controlled release job.
5. Verify current revision, application health and critical queries.
6. Record revision, duration and operator in deployment evidence.

Never let multiple application replicas race to migrate on startup.

## Downgrade and rollback

Use alembic downgrade -1 only when the revision has a tested, data-safe downgrade. Schema rollback does not automatically restore deleted or transformed data. For destructive or lossy future changes, prefer forward repair or restore from a verified backup. Stop application writes before any rollback requiring consistency.

The baseline downgrade removes the entire baseline and is intended only for empty/disposable validation databases. It must never be used on a populated production database.

## Autogenerate rules

- Keep target_metadata wired to Base.metadata.
- Generate against the intended database URL and expected current revision.
- Investigate every add/drop/alter, especially unexpected table drops.
- Give constraints and indexes stable names where future changes require them.
- Do not include seed data, credentials or environment-specific values.
- Do not modify an applied revision; create a new revision.
- Ensure one head unless a reviewed merge revision is intentional.

## Review checklist

- Upgrade matches the approved model change and nothing else.
- Downgrade is complete or explicitly documented as unsafe.
- Table, column, type, nullability, FK, unique constraint and index changes are correct.
- Large-table locking and backfill order have been assessed.
- Existing data remains valid throughout mixed-version deployment.
- No business writes, secrets, tenant assumptions or seed records appear.
- Empty and production-like upgrade tests pass.
- Backup, monitoring and rollback owners are identified.

## Common mistakes

Do not hardcode SQLite or any DATABASE_URL in migration files. Do not redefine Base in env.py. Do not call create_all inside a revision. Do not import mutable current model metadata from a historical revision. Do not assume autogenerate detects data migrations, renames or all constraint semantics. Do not stamp an unverified existing database.

## Best practices

Prefer small, reversible revisions. Separate schema expansion, application dual-write/backfill and constraint enforcement. Use expand-and-contract for compatibility. Make backfills resumable and observable. Verify downgrade on disposable data. Keep production credentials outside repository files and restrict migration identity to required DDL permissions.
