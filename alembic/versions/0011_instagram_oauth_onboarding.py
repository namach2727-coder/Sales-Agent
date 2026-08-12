"""Add one-time Instagram OAuth onboarding state.

Revision ID: 0011_instagram_oauth_onboarding
Revises: 0010_saas_commerce
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_instagram_oauth_onboarding"
down_revision: Union[str, Sequence[str], None] = "0010_saas_commerce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.create_table(
        "instagram_oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("state_digest", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column(
            "initiated_by_user_id",
            sa.Integer(),
            sa.ForeignKey("user_identities.id"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_instagram_oauth_states_store_tenant",
        ),
        sa.UniqueConstraint(
            "state_digest", name="uq_instagram_oauth_states_digest"
        ),
    )
    op.create_index(
        "ix_instagram_oauth_states_public_id",
        "instagram_oauth_states",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_instagram_oauth_states_tenant_id",
        "instagram_oauth_states",
        ["tenant_id"],
    )
    op.create_index(
        "ix_instagram_oauth_states_store_id",
        "instagram_oauth_states",
        ["store_id"],
    )
    op.create_index(
        "ix_instagram_oauth_states_initiated_by_user_id",
        "instagram_oauth_states",
        ["initiated_by_user_id"],
    )
    op.create_index(
        "ix_instagram_oauth_states_expires_at",
        "instagram_oauth_states",
        ["expires_at"],
    )
    op.create_index(
        "ix_instagram_oauth_states_scope",
        "instagram_oauth_states",
        ["tenant_id", "store_id", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_instagram_oauth_states_scope", table_name="instagram_oauth_states")
    op.drop_index("ix_instagram_oauth_states_expires_at", table_name="instagram_oauth_states")
    op.drop_index("ix_instagram_oauth_states_initiated_by_user_id", table_name="instagram_oauth_states")
    op.drop_index("ix_instagram_oauth_states_store_id", table_name="instagram_oauth_states")
    op.drop_index("ix_instagram_oauth_states_tenant_id", table_name="instagram_oauth_states")
    op.drop_index("ix_instagram_oauth_states_public_id", table_name="instagram_oauth_states")
    op.drop_table("instagram_oauth_states")
