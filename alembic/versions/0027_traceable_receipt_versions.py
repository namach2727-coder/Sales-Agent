"""Preserve every uploaded manual payment receipt for later customer tracing.

Additive schema only: retain manual_payments receipt bytes and historical orders.
Preexisting PostgreSQL receipt_data are copied as version 1 once at upgrade.
The migration does not move, delete or rewrite any original payment evidence.
"""
from alembic import op
import sqlalchemy as sa

revision = "0027_traceable_receipt_versions"
down_revision = "0026_durable_product_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manual_payment_receipt_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("manual_payments.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("subscription_orders.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("receipt_data", sa.LargeBinary(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("payment_id", "version", name="uq_manual_receipt_payment_version"),
        sa.CheckConstraint("version >= 1", name="ck_manual_receipt_positive_version"),
        sa.CheckConstraint("byte_size > 0", name="ck_manual_receipt_positive_size"),
    )
    for column in ("payment_id", "order_id", "tenant_id", "store_id", "user_id", "submitted_at"):
        op.create_index(f"ix_manual_payment_receipt_versions_{column}", "manual_payment_receipt_versions", [column])
    # PostgreSQL and SQLite compatible; only copy previously stored durable
    # bytes and never touch source payment rows. No legacy disk reads.
    op.execute(
        sa.text(
            """
            INSERT INTO manual_payment_receipt_versions (
                payment_id, order_id, tenant_id, store_id, user_id,
                version, content_type, byte_size, sha256, receipt_data, submitted_at
            )
            SELECT id, order_id, tenant_id, store_id, user_id, 1,
                   receipt_content_type, receipt_size, receipt_sha256,
                   receipt_data, COALESCE(submitted_at, created_at)
            FROM manual_payments
            WHERE receipt_data IS NOT NULL
              AND receipt_content_type IS NOT NULL
              AND receipt_size > 0
              AND receipt_sha256 IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    # Destroying four-month-old customer evidence must never be a blind undo.
    count = op.get_bind().scalar(sa.text("SELECT count(*) FROM manual_payment_receipt_versions"))
    if count:
        raise RuntimeError("Refusing downgrade: retained receipt evidence exists")
    for column in ("submitted_at", "user_id", "store_id", "tenant_id", "order_id", "payment_id"):
        op.drop_index(f"ix_manual_payment_receipt_versions_{column}", table_name="manual_payment_receipt_versions")
    op.drop_table("manual_payment_receipt_versions")
