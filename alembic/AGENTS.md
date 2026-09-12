# Migration scope

- Keep one linear Alembic head unless an approved merge migration is required.
- Prefer additive, forward-only changes with deterministic upgrade behavior; never reset or recreate a populated database to make a migration pass.
- Preserve historical commerce records, tenant/store ownership, automation rules, knowledge, connector credentials, conversations, and AI usage.
- Validate fresh-database-to-head, supported upgrade paths, and downgrade safety where a downgrade is intentionally supported. Never use `sales_assistant.db`.
- Separate migration validation from deployment. Confirm backup/restore readiness before any populated-environment migration.
