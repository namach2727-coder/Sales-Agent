"""Create credential-free audit history for explicit seed runs."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_seed_history"
down_revision: str | None = "0001_baseline_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


def upgrade() -> None:
    op.create_table(
        "seed_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("seed_name", sa.String(100), nullable=False),
        sa.Column("seed_version", sa.String(50), nullable=False),
        sa.Column("profile", sa.String(20), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("tenant_id",), ("stores.id",)),
    )
    op.create_index("ix_seed_history_seed_name", "seed_history", ["seed_name"])
    op.create_index("ix_seed_history_tenant_id", "seed_history", ["tenant_id"])
    op.create_index("ix_seed_history_status", "seed_history", ["status"])


def downgrade() -> None:
    op.drop_index("ix_seed_history_status", table_name="seed_history")
    op.drop_index("ix_seed_history_tenant_id", table_name="seed_history")
    op.drop_index("ix_seed_history_seed_name", table_name="seed_history")
    op.drop_table("seed_history")

