"""Add independent AI Assistant runtime control.

Revision ID: 0017_ai_assistant_workspace
Revises: 0016_product_family_commerce
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0017_ai_assistant_workspace"
down_revision: Union[str, Sequence[str], None] = "0016_product_family_commerce"
branch_labels = None
depends_on = None
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.add_column("stores", sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("stores", sa.Column("ai_revision", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("stores") as batch:
        batch.create_check_constraint("ck_stores_ai_revision", "ai_revision >= 1")
        batch.alter_column("ai_enabled", server_default=None)
        batch.alter_column("ai_revision", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("stores") as batch:
        batch.drop_constraint("ck_stores_ai_revision", type_="check")
        batch.drop_column("ai_revision")
        batch.drop_column("ai_enabled")
