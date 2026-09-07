"""Add store-scoped AutomationRule definitions.

Revision ID: 0015_automation_rules
Revises: 0014_transport_neutral_inbound
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015_automation_rules"
down_revision: Union[str, Sequence[str], None] = "0014_transport_neutral_inbound"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("trigger_type", sa.String(40), nullable=False),
        sa.Column("match_type", sa.String(30), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("action_type", sa.String(40), nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("store_id", "tenant_id"), ("stores.id", "stores.tenant_id"), name="fk_automation_rules_store_tenant"),
        sa.CheckConstraint("trigger_type IN ('DM_KEYWORD', 'STORY_REPLY_KEYWORD', 'COMMENT_KEYWORD')", name="ck_automation_rules_trigger_type"),
        sa.CheckConstraint("match_type IN ('EXACT', 'CONTAINS', 'STARTS_WITH')", name="ck_automation_rules_match_type"),
        sa.CheckConstraint("action_type IN ('SEND_MESSAGE', 'SEND_PRIVATE_MESSAGE')", name="ck_automation_rules_action_type"),
        sa.CheckConstraint("priority >= 0 AND priority <= 10000", name="ck_automation_rules_priority"),
        sa.CheckConstraint("revision >= 1", name="ck_automation_rules_revision"),
    )
    op.create_index("ix_automation_rules_public_id", "automation_rules", ["public_id"], unique=True)
    op.create_index("ix_automation_rules_tenant_id", "automation_rules", ["tenant_id"])
    op.create_index("ix_automation_rules_store_id", "automation_rules", ["store_id"])
    op.create_index("ix_automation_rules_enabled", "automation_rules", ["enabled"])
    op.create_index("ix_automation_rules_tenant_store_priority", "automation_rules", ["tenant_id", "store_id", "priority"])


def downgrade() -> None:
    op.drop_index("ix_automation_rules_tenant_store_priority", table_name="automation_rules")
    op.drop_index("ix_automation_rules_enabled", table_name="automation_rules")
    op.drop_index("ix_automation_rules_store_id", table_name="automation_rules")
    op.drop_index("ix_automation_rules_tenant_id", table_name="automation_rules")
    op.drop_index("ix_automation_rules_public_id", table_name="automation_rules")
    op.drop_table("automation_rules")
