"""Add KPay provider state to the existing payment boundary.

Revision ID: 0019_kpay_payment_gateway
Revises: 0018_order_commercial_snapshot
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0019_kpay_payment_gateway"
down_revision: Union[str, Sequence[str], None] = "0018_order_commercial_snapshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("manual_payments") as batch_op:
        batch_op.add_column(sa.Column("provider_transaction_id", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("provider_authority", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("provider_status", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("provider_operation_state", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("provider_payment_url", sa.String(1000), nullable=True))
        batch_op.add_column(sa.Column("provider_created_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("provider_paid_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("provider_amount", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("provider_final_amount", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("provider_fee", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_manual_payments_provider_operation_state",
            "provider_operation_state IS NULL OR provider_operation_state IN "
            "('NOT_STARTED', 'CREATE_IN_FLIGHT', 'CREATED', 'CREATE_UNKNOWN', "
            "'VERIFY_PENDING', 'PAID', 'FAILED')",
        )
        batch_op.create_unique_constraint(
            "uq_manual_payments_provider_transaction",
            ["provider", "provider_transaction_id"],
        )
    op.create_index(
        "ix_manual_payments_provider_authority",
        "manual_payments", ["provider_authority"], unique=True,
    )
    op.create_index(
        "ix_manual_payments_provider_operation_state",
        "manual_payments", ["provider_operation_state"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_manual_payments_provider_operation_state", table_name="manual_payments")
    op.drop_index("ix_manual_payments_provider_authority", table_name="manual_payments")
    with op.batch_alter_table("manual_payments") as batch_op:
        batch_op.drop_constraint("uq_manual_payments_provider_transaction", type_="unique")
        batch_op.drop_constraint("ck_manual_payments_provider_operation_state", type_="check")
        for name in (
            "provider_fee", "provider_final_amount", "provider_amount",
            "provider_paid_at", "provider_created_at", "provider_payment_url",
            "provider_operation_state", "provider_status", "provider_authority",
            "provider_transaction_id",
        ):
            batch_op.drop_column(name)
