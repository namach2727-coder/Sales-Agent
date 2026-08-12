"""Add the store-owned automatic AI handling switch.

Revision ID: 0013_store_automation_control
Revises: 0012_plan_billing_duration
Create Date: 2026-08-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_store_automation_control"
down_revision: Union[str, Sequence[str], None] = "0012_plan_billing_duration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    with op.batch_alter_table("stores") as batch:
        batch.add_column(
            sa.Column(
                "automation_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "automation_revision",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch.create_check_constraint(
            "ck_stores_automation_revision",
            "automation_revision >= 1",
        )
    # Defaults are needed only while existing rows are backfilled. Runtime
    # creation remains explicit through the SQLAlchemy model, avoiding
    # permanent database defaults and schema drift.
    with op.batch_alter_table("stores") as batch:
        batch.alter_column("automation_enabled", server_default=None)
        batch.alter_column("automation_revision", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("stores") as batch:
        batch.drop_constraint("ck_stores_automation_revision", type_="check")
        batch.drop_column("automation_revision")
        batch.drop_column("automation_enabled")
