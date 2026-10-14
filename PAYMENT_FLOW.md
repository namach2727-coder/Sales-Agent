# Manual Card-Transfer Payment Flow

## Current authoritative workflow (2026-10-14)

1. The customer selects an active plan from `/api/v1/plans`.
2. The backend captures the authoritative plan price in a subscription order.
3. `ManualCardTransferProvider` returns the configured card/account details and payment instructions. No banking secrets are embedded in source code, and the manual provider makes no bank call.
4. The customer pays outside DirectPilot and uploads a JPEG, PNG or PDF receipt through the authenticated `/api/v1/payments/{payment_public_id}/receipt` endpoint.
5. The backend validates the file signature/type, size limit (configured by `RECEIPT_MAX_BYTES`, default 5 MiB), and ownership/payment state. It generates a non-enumerable `db:` storage key and a SHA-256 checksum.
6. **Durable primary storage is PostgreSQL, not local disk.** The receipt's binary bytes are stored in `manual_payments.receipt_data` (LargeBinary/bytea) alongside `receipt_storage_key`, `receipt_content_type`, `receipt_size` and `receipt_sha256`. The payment changes to `submitted`; its order moves to `payment_submitted`.
7. Authorized platform administrators with `payment.read` can access the private receipt from `GET /api/v1/admin/payments/{payment_public_id}/receipt`. The API serves the stored PostgreSQL bytes inline; the customer does not receive an unrestricted public URL.
8. Administrators with `payment.manage` approve or reject the payment using optimistic revision checks. Approval locks/updates the payment and order, grants subscription entitlements, and writes an audit record transactionally.

## Legacy receipt compatibility

Older receipts without `receipt_data` can still be served via the protected `RECEIPT_STORAGE_ROOT` local-disk fallback **only when the original legacy file exists on that host**. This fallback is not durable on Vercel Functions and must not be mistaken for migrated media. Inventory and securely migrate any such historical files before retiring Render.

## Verified evidence and remaining gates

- On 2026-10-14, the independent Neon UAT database had 2 `manual_payments` records with both `receipt_storage_key` and non-null `receipt_data`, and 0 file-only receipts (read-only SQL verification).
- The owner reported PASS for reading existing receipts from the isolated Vercel UAT admin preview. A fresh upload/redeployment/retrieval E2E is **not yet verified**.
- PostgreSQL durability does not bypass Vercel Functions' request-body limit or Neon storage and backup requirements. Receipt sizes up to the application default of 5 MiB may exceed the host request limit: test small uploads and explicitly address oversize requests before commercial release.
- Product publishing **images are a different feature**: `app/media_storage.py` currently uses local files; those media assets require separate durable object storage or another approved redesign. Do not equate them with the PostgreSQL receipt flow.
- Full Production cutover still requires verified independent encrypted backups and restore, fresh source synchronization, all-writer/webhook/payment freeze with replay and reconciliation, rollback and explicit owner approval.

Relevant source: `app/commerce/storage.py`, `app/commerce/service.py`, `app/commerce/router.py`, `app/models.py`.
