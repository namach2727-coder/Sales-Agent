"""Add sellable SaaS plans, orders, manual payments, and subscriptions.

Revision ID: 0010_saas_commerce
Revises: 0009_conversation_core_models
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_saas_commerce"
down_revision: Union[str, Sequence[str], None] = "0009_conversation_core_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def _public_index(table: str) -> None:
    op.create_index(f"ix_{table}_public_id", table, ["public_id"], unique=True)


def upgrade() -> None:
    op.create_table(
        "saas_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reply_limit", sa.Integer(), nullable=False),
        sa.Column("automation_limit", sa.Integer(), nullable=False),
        sa.Column("instagram_account_limit", sa.Integer(), nullable=False),
        sa.Column("module_codes", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_amount >= 0", name="ck_saas_plans_price_nonnegative"),
        sa.CheckConstraint("reply_limit >= 0", name="ck_saas_plans_reply_limit"),
        sa.CheckConstraint("automation_limit >= 0", name="ck_saas_plans_automation_limit"),
        sa.CheckConstraint("instagram_account_limit >= 0", name="ck_saas_plans_instagram_limit"),
    )
    _public_index("saas_plans")
    op.create_index("ix_saas_plans_code", "saas_plans", ["code"], unique=True)
    op.create_index("ix_saas_plans_is_active", "saas_plans", ["is_active"])

    op.create_table(
        "subscription_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("saas_plans.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("price_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'payment_submitted', 'paid', 'cancelled')", name="ck_subscription_orders_status"),
        sa.CheckConstraint("price_amount >= 0", name="ck_subscription_orders_price"),
    )
    _public_index("subscription_orders")
    for column in ("tenant_id", "store_id", "user_id", "plan_id", "status"):
        op.create_index(f"ix_subscription_orders_{column}", "subscription_orders", [column])

    op.create_table(
        "manual_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("subscription_orders.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("receipt_storage_key", sa.String(300), nullable=True),
        sa.Column("receipt_content_type", sa.String(100), nullable=True),
        sa.Column("receipt_size", sa.Integer(), nullable=True),
        sa.Column("receipt_sha256", sa.String(64), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("order_id", name="uq_manual_payments_order"),
        sa.CheckConstraint("status IN ('pending', 'submitted', 'approved', 'rejected')", name="ck_manual_payments_status"),
        sa.CheckConstraint("amount >= 0", name="ck_manual_payments_amount"),
    )
    _public_index("manual_payments")
    for column in ("tenant_id", "store_id", "order_id", "user_id", "status"):
        op.create_index(f"ix_manual_payments_{column}", "manual_payments", [column])

    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("saas_plans.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("subscription_orders.id"), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("manual_payments.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("limits_json", sa.JSON(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("order_id", name="uq_tenant_subscriptions_order"),
        sa.UniqueConstraint("payment_id", name="uq_tenant_subscriptions_payment"),
        sa.CheckConstraint("status IN ('active', 'expired', 'cancelled')", name="ck_tenant_subscriptions_status"),
    )
    _public_index("tenant_subscriptions")
    for column in ("tenant_id", "store_id", "plan_id", "order_id", "payment_id", "status"):
        op.create_index(f"ix_tenant_subscriptions_{column}", "tenant_subscriptions", [column])

    op.create_table(
        "commerce_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_public_id", sa.String(36), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("tenant_id", "store_id", "actor_user_id", "action", "target_public_id", "created_at"):
        op.create_index(f"ix_commerce_audit_logs_{column}", "commerce_audit_logs", [column])


def downgrade() -> None:
    op.drop_table("commerce_audit_logs")
    op.drop_table("tenant_subscriptions")
    op.drop_table("manual_payments")
    op.drop_table("subscription_orders")
    op.drop_table("saas_plans")
