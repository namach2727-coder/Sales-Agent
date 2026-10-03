"""Persist manual-payment receipt bytes in the durable application database."""

from alembic import op
import sqlalchemy as sa


revision = "0022_durable_receipt_blob"
down_revision = "0021_admin_payment_cards"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("manual_payments") as batch:
        batch.add_column(
            sa.Column(
                "receipt_data",
                sa.LargeBinary(),
                nullable=True,
            )
        )


def downgrade():
    bind = op.get_bind()

    receipt_count = bind.scalar(
        sa.text(
            """
            SELECT count(*)
            FROM manual_payments
            WHERE receipt_data IS NOT NULL
            """
        )
    )

    if receipt_count:
        raise RuntimeError(
            "Cannot downgrade while durable receipt evidence exists"
        )

    with op.batch_alter_table("manual_payments") as batch:
        batch.drop_column("receipt_data")
