# Manual Card-Transfer Payment Flow

1. Customer selects an active plan from `/api/v1/plans`.
2. Backend snapshots the authoritative plan price into an order.
3. `ManualCardTransferProvider` returns card number, account number,
   account-holder name, bank name, and transfer instructions from deployment
   configuration; no real banking details are source constants.
4. Customer uploads a validated receipt to private storage. PostgreSQL stores
   only a non-enumerable key, content type, size and SHA-256 digest.
5. A platform user with `payment.read` reviews the private receipt.
6. A user with `payment.manage` approves or rejects using optimistic revision.
7. Approval locks the payment row and atomically changes payment/order status,
   creates the subscription, applies module entitlements and writes an audit.

The provider boundary intentionally makes no bank call. A production object
storage implementation is still required before accepting real customer
receipts; local private disk is for development/UAT only.
