"""Make the approved AI paid plan available without touching existing commerce data.

The UAT plan may already exist; respect that row and all historical snapshots.
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0024_ai_assistant_v1_catalog"
down_revision = "0023_user_phone_number"
branch_labels = None
depends_on = None


def _plan_table():
    return sa.table(
        "saas_plans",
        sa.column("public_id", sa.String(36)),
        sa.column("code", sa.String(50)),
        sa.column("name", sa.String(120)),
        sa.column("description", sa.String(1000)),
        sa.column("product_family", sa.String(30)),
        sa.column("price_amount", sa.Integer()),
        sa.column("currency", sa.String(3)),
        sa.column("reply_limit", sa.Integer()),
        sa.column("automation_limit", sa.Integer()),
        sa.column("instagram_account_limit", sa.Integer()),
        sa.column("duration_days", sa.Integer()),
        sa.column("billing_unit", sa.String(20)),
        sa.column("ai_request_limit", sa.Integer()),
        sa.column("ai_token_limit", sa.Integer()),
        sa.column("module_codes", sa.JSON()),
        sa.column("is_active", sa.Boolean()),
        sa.column("is_purchasable", sa.Boolean()),
        sa.column("display_order", sa.Integer()),
        sa.column("trial_eligible", sa.Boolean()),
        sa.column("revision", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )


def upgrade() -> None:
    bind = op.get_bind()
    existing = bind.scalar(
        sa.text("SELECT id FROM saas_plans WHERE code = :code"),
        {"code": "AI_ASSISTANT_V1"},
    )
    if existing is not None:
        # A UAT/admin-created row must never be overwritten by deployment.
        return

    now = sa.func.current_timestamp()
    bind.execute(
        _plan_table().insert().values(
            public_id=str(uuid4()),
            code="AI_ASSISTANT_V1",
            name="AI Assistant",
            description="دستیار هوشمند برای پاسخ‌گویی بر اساس اطلاعات کسب‌وکار",
            product_family="AI_ASSISTANT",
            price_amount=6_900_000,
            currency="IRR",
            reply_limit=1_000,
            automation_limit=0,
            instagram_account_limit=1,
            duration_days=30,
            billing_unit="day",
            ai_request_limit=1_000,
            ai_token_limit=None,
            module_codes=["ai_assistant", "knowledge_base"],
            is_active=True,
            is_purchasable=True,
            display_order=20,
            trial_eligible=False,
            revision=1,
            created_at=now,
            updated_at=now,
        )
    )


def downgrade() -> None:
    # Commercial plans may be linked to paid orders. Deleting or disabling a
    # pre-existing admin-created plan on migration rollback would be unsafe.
    # Rollback of selling eligibility is an explicit audited admin decision.
    pass
