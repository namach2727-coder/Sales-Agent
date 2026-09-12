"""Add independent commercial product families.

Revision ID: 0016_product_family_commerce
Revises: 0015_automation_rules
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_product_family_commerce"
down_revision: Union[str, Sequence[str], None] = "0015_automation_rules"
branch_labels = None
depends_on = None
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.create_table(
        "commerce_admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_public_id", sa.String(36), nullable=False),
        sa.Column("changes_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_commerce_admin_audit_logs_actor_user_id", "commerce_admin_audit_logs", ["actor_user_id"])
    op.create_index("ix_commerce_admin_audit_logs_action", "commerce_admin_audit_logs", ["action"])
    op.create_index("ix_commerce_admin_audit_logs_target_public_id", "commerce_admin_audit_logs", ["target_public_id"])
    op.create_index("ix_commerce_admin_audit_logs_created_at", "commerce_admin_audit_logs", ["created_at"])
    op.add_column("saas_plans", sa.Column("product_family", sa.String(30), nullable=True))
    op.add_column("saas_plans", sa.Column("description", sa.String(1000), nullable=True))
    op.add_column("saas_plans", sa.Column("billing_unit", sa.String(20), nullable=False, server_default="day"))
    op.add_column("saas_plans", sa.Column("ai_request_limit", sa.Integer(), nullable=True))
    op.add_column("saas_plans", sa.Column("ai_token_limit", sa.Integer(), nullable=True))
    op.add_column("saas_plans", sa.Column("is_purchasable", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("saas_plans", sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("saas_plans", sa.Column("trial_eligible", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("saas_plans", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.execute("UPDATE saas_plans SET product_family = CASE WHEN code = 'START' THEN 'AUTOMATION' ELSE 'LEGACY_BUNDLE' END")
    with op.batch_alter_table("saas_plans") as batch:
        batch.alter_column("product_family", nullable=False)
        batch.alter_column("billing_unit", server_default=None)
        batch.alter_column("is_purchasable", server_default=None)
        batch.alter_column("display_order", server_default=None)
        batch.alter_column("trial_eligible", server_default=None)
        batch.alter_column("revision", server_default=None)
        batch.create_check_constraint("ck_saas_plans_product_family", "product_family IN ('AUTOMATION', 'AI_ASSISTANT', 'LEGACY_BUNDLE')")
    op.create_index("ix_saas_plans_product_family", "saas_plans", ["product_family"])
    op.create_index("ix_saas_plans_is_purchasable", "saas_plans", ["is_purchasable"])

    op.add_column("tenant_subscriptions", sa.Column("product_family", sa.String(30), nullable=True))
    op.add_column("tenant_subscriptions", sa.Column("source", sa.String(20), nullable=True))
    op.execute("UPDATE tenant_subscriptions SET product_family = CASE WHEN plan_id IN (SELECT id FROM saas_plans WHERE code = 'START') THEN 'AUTOMATION' ELSE 'LEGACY_BUNDLE' END")
    op.execute("UPDATE tenant_subscriptions SET source = CASE WHEN plan_id IN (SELECT id FROM saas_plans WHERE code = 'TRIAL') THEN 'TRIAL' ELSE 'LEGACY' END")
    with op.batch_alter_table("tenant_subscriptions") as batch:
        batch.alter_column("order_id", nullable=True)
        batch.alter_column("product_family", nullable=False)
        batch.alter_column("source", nullable=False)
        batch.create_check_constraint("ck_tenant_subscriptions_product_family", "product_family IN ('AUTOMATION', 'AI_ASSISTANT', 'LEGACY_BUNDLE')")
        batch.create_check_constraint("ck_tenant_subscriptions_source", "source IN ('PURCHASED', 'TRIAL', 'ADMIN_GRANT', 'LEGACY')")
    op.create_index("ix_tenant_subscriptions_product_family", "tenant_subscriptions", ["product_family"])
    op.create_index("ix_tenant_subscriptions_source", "tenant_subscriptions", ["source"])


def downgrade() -> None:
    op.drop_index("ix_tenant_subscriptions_source", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_product_family", table_name="tenant_subscriptions")
    with op.batch_alter_table("tenant_subscriptions") as batch:
        batch.drop_constraint("ck_tenant_subscriptions_source", type_="check")
        batch.drop_constraint("ck_tenant_subscriptions_product_family", type_="check")
        batch.alter_column("order_id", nullable=False)
        batch.drop_column("source")
        batch.drop_column("product_family")
    op.drop_index("ix_saas_plans_is_purchasable", table_name="saas_plans")
    op.drop_index("ix_saas_plans_product_family", table_name="saas_plans")
    with op.batch_alter_table("saas_plans") as batch:
        batch.drop_constraint("ck_saas_plans_product_family", type_="check")
        for column in ("revision", "trial_eligible", "display_order", "is_purchasable", "ai_token_limit", "ai_request_limit", "billing_unit", "description", "product_family"):
            batch.drop_column(column)
    for index in ("ix_commerce_admin_audit_logs_created_at", "ix_commerce_admin_audit_logs_target_public_id", "ix_commerce_admin_audit_logs_action", "ix_commerce_admin_audit_logs_actor_user_id"):
        op.drop_index(index, table_name="commerce_admin_audit_logs")
    op.drop_table("commerce_admin_audit_logs")
