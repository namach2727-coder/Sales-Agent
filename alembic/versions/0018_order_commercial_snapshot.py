"""Add immutable commercial snapshots to subscription orders.

Revision ID: 0018_order_commercial_snapshot
Revises: 0017_ai_assistant_workspace
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018_order_commercial_snapshot"
down_revision: Union[str, Sequence[str], None] = "0017_ai_assistant_workspace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = (
        sa.Column("plan_code_snapshot", sa.String(length=50), nullable=True),
        sa.Column("plan_name_snapshot", sa.String(length=120), nullable=True),
        sa.Column("product_family_snapshot", sa.String(length=30), nullable=True),
        sa.Column("duration_days_snapshot", sa.Integer(), nullable=True),
        sa.Column("instagram_account_limit_snapshot", sa.Integer(), nullable=True),
        sa.Column("automation_limit_snapshot", sa.Integer(), nullable=True),
        sa.Column("ai_reply_limit_snapshot", sa.Integer(), nullable=True),
        sa.Column("ai_request_limit_snapshot", sa.Integer(), nullable=True),
        sa.Column("ai_token_limit_snapshot", sa.Integer(), nullable=True),
    )
    with op.batch_alter_table("subscription_orders") as batch_op:
        for column in columns:
            batch_op.add_column(column)


def downgrade() -> None:
    names = (
        "ai_token_limit_snapshot", "ai_request_limit_snapshot",
        "ai_reply_limit_snapshot", "automation_limit_snapshot",
        "instagram_account_limit_snapshot", "duration_days_snapshot",
        "product_family_snapshot", "plan_name_snapshot", "plan_code_snapshot",
    )
    with op.batch_alter_table("subscription_orders") as batch_op:
        for name in names:
            batch_op.drop_column(name)
