"""Add backend-authoritative billing duration to SaaS plans.

Revision ID: 0012_plan_billing_duration
Revises: 0011_instagram_oauth_onboarding
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_plan_billing_duration"
down_revision: Union[str, Sequence[str], None] = "0011_instagram_oauth_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.add_column(
        "saas_plans",
        sa.Column("duration_days", sa.Integer(), nullable=True),
    )
    with op.batch_alter_table("saas_plans") as batch:
        batch.create_check_constraint(
            "ck_saas_plans_duration_days",
            "duration_days IS NULL OR duration_days > 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("saas_plans") as batch:
        batch.drop_constraint(
            "ck_saas_plans_duration_days",
            type_="check",
        )
        batch.drop_column("duration_days")
