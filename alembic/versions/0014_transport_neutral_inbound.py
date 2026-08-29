"""Allow normalized Instagram events without a fake webhook delivery.

Revision ID: 0014_transport_neutral_inbound
Revises: 0013_store_automation_control
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_transport_neutral_inbound"
down_revision: Union[str, Sequence[str], None] = (
    "0013_store_automation_control"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The upgrade widens compatibility by dropping NOT NULL. The migration policy
# still classifies every alter_column operation as requiring explicit review.
DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = True
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    with op.batch_alter_table("instagram_inbound_events") as batch:
        batch.alter_column(
            "webhook_delivery_id",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    connection = op.get_bind()
    transport_events = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM instagram_inbound_events "
            "WHERE webhook_delivery_id IS NULL"
        )
    )
    if transport_events:
        raise RuntimeError(
            "cannot restore mandatory webhook linkage while transport-neutral "
            "Instagram events exist"
        )
    with op.batch_alter_table("instagram_inbound_events") as batch:
        batch.alter_column(
            "webhook_delivery_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
