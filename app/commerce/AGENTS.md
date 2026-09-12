# Commerce scope

- Treat the backend as authoritative for product families, plans, prices, limits, entitlements, orders, payments, and subscription lifecycle.
- Keep Automation and AI Assistant as independent product families. Preserve legacy commercial rows as historical snapshots; do not make obsolete plans orderable.
- Apply commercial policy prospectively: changes to current catalog definitions must not retroactively alter historical order or subscription snapshots.
- Entitlement checks fail closed and remain tenant/store scoped. A visual or client-side state never grants access.
- Restrict commercial policy administration server-side and preserve an auditable record of privileged changes.
- Preserve historical orders and subscriptions. Prefer additive schema evolution and explicit reconciliation for existing tenants.
- Test idempotency, downgrade/expiry behavior, product-family isolation, authorization, and historical referential integrity for commerce changes.
