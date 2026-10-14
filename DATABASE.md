# DirectPilot Database


## Durable receipt evidence and retention — pending UAT

`manual_payments.receipt_data` currently holds the latest receipt per payment, but after a rejected payment is resubmitted the former bytes are overwritten. Owner requires every customer's original receipts to remain identifiable and retrievable four months or longer afterward. Stacked UAT PR #36 introduces Alembic `0027_traceable_receipt_versions` (after pending 0026) and `manual_payment_receipt_versions` containing separate immutable `receipt_data BYTEA` for every upload, payment/order/customer/tenant/store IDs, version, content SHA-256, byte size, content type and timestamp. Existing PostgreSQL receipts are copied as version 1 without deleting source records. Authorized admin can search payment history by customer email/date and fetch versioned receipt bytes and events. **Not migrated or deployed**; recovery and real retention evidence remain OPEN. No automatic purge; propose 12-month retention with restricted access, tested independent restorable backups and capacity measurement before any claim of guaranteed durability.

## Technology and migration policy

PostgreSQL is the deployed database; SQLite remains a local development and unit-test option. `DATABASE_URL` is the only application database contract. Every schema change is an Alembic revision and deployed startup fails if the database is not at the single migration head. `create_all()` is not a production migration mechanism.

**Verified Neon UAT revision on 2026-10-14:** `0025_trial_three_days`, with 82 public tables. This is a time-stamped observation, not a permanently hard-coded migration head; always compare `alembic_version` to the current checked-out migration graph before deployment.

## Tenant ownership

`Tenant` owns stores and memberships. Tenant/store-scoped data carries internal foreign keys, while APIs resolve and return public IDs. Compound foreign keys on critical store records prevent a store from being attached to the wrong tenant.

## Sellable MVP records

- `saas_plans`: authoritative prices and limits.
- `subscription_orders`: immutable price snapshot for a plan purchase.
- `manual_payments`: payment status and review lifecycle **plus durable receipt bytes in `receipt_data` (LargeBinary/bytea)**. Receipt metadata includes `receipt_storage_key`, `receipt_content_type`, `receipt_size`, and `receipt_sha256`. Never describe this table as "metadata only."
- `tenant_subscriptions`: active limits and entitlement source.
- `commerce_audit_logs`: credential-free transition audit.
- `instagram_oauth_states`: SHA-256 digest of short-lived, single-use OAuth state. Raw state and OAuth codes are never persisted.
- `instagram_connections`: the existing encrypted per-store Meta credential.

## Owner-approved next step: PostgreSQL product media (pending UAT rollout)

On 2026-10-14 the owner reaffirmed PostgreSQL-only durable image storage. PR #33 (R2/S3) was CLOSED WITHOUT MERGE. UAT-only PR #34 introduces additive Alembic `0026_durable_product_media` and nullable `product_media_assets.image_data BYTEA`, with 2 MiB JPEG/file and 50 MiB active/store guards. **This change is committed to a feature branch, NOT deployed to Neon UAT or Production yet.** Existing `manual_payments.receipt_data` for receipts remains active and unchanged. Apply 0026 only after verified recoverable UAT backup, clean CI, review and explicit UAT migration gate; actual Production remains on Render until independently authorized final cutover.

## Receipt and media storage boundaries

- **New manual-payment receipts:** validated JPEG/PNG/PDF content and SHA-256 metadata stored in PostgreSQL; accessible through authorized admin route. This survives stateless Backend redeployments as long as the database is durable and recoverable.
- **Legacy payment receipts:** protected local-file fallback remains for rows with `receipt_storage_key` but null `receipt_data`; preserve and migrate source disk assets before Render retirement if any exist. On 2026-10-14 Neon UAT, 2/2 stored payments had durable bytes and 0 were file-only (read-only audit).
- **Product-media assets:** `product_media_assets` currently stores metadata and a `storage_key`; image bytes are written by `app/media_storage.py` to local disk. Serverless-hosted image uploads, signed public image links and deletion need separate persistent storage, quotas and acceptance.
- PostgreSQL receipt bytes increase database backup/storage consumption. Do not assume that a successful upload proves offsite backup, provider quota, or disaster-recovery guarantees.

## Operations

Before release, validate `alembic upgrade head` from an empty PostgreSQL test database and run `python -m tools.migration_policy`. Target Production policy: recoverable encrypted/off-provider backups, appropriate provider snapshots/PITR where available, tested restoration, documented retention and restricted backup credentials. These are **required gates**, not verified deployed features. Neither UAT nor Production databases may be reset as part of validation.

Production Render source remains authoritative until separately approved final source freeze/export, parity checks and Neon Production cutover. Never point Production to a stale Neon rehearsal copy or merge independent UAT data into Production.
