---
name: directpilot-commerce-migration
description: Design or validate DirectPilot plan, product-family, subscription, entitlement, order, or payment schema migrations. Use for commerce lifecycle changes; not for ordinary UI copy or runtime diagnostics.
---

# DirectPilot commerce migration

1. Audit current models, services, migrations, constraints, tests, and authoritative commercial policy before designing changes.
2. Classify rows as current catalog definitions or immutable historical snapshots. Preserve historical orders, payments, and subscriptions.
3. Prefer one additive, forward-only migration with deterministic reconciliation. Keep one Alembic head and avoid destructive resets or downgrades.
4. Preserve tenant/store ownership and enforce server-side, fail-closed entitlements for independent Automation and AI Assistant product families.
5. Test fresh database to head, the supported upgrade path, idempotent reconciliation, legacy reads, new-order eligibility, expiry/downgrade, authorization, and referential integrity.
6. Use only fresh temporary validation databases, never `sales_assistant.db` or a populated environment without explicit migration authorization and backup/restore readiness.
7. Run focused migration/commerce tests during iteration and the full backend suite once before release when required.
