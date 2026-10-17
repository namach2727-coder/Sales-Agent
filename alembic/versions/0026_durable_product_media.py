"""Add durable PostgreSQL bytes for product images; preserve existing metadata.

Old local-file-only rows remain readable on persistent Docker hosts until an
explicit, verified backfill is performed. This migration does not read or
delete any external files and never touches receipt storage.
"""

from alembic import op
import sqlalchemy as sa

revision = "0026_durable_product_media"
down_revision = "0025_trial_three_days"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("product_media_assets") as batch:
        batch.add_column(sa.Column("image_data", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = bind.scalar(
        sa.text("SELECT count(*) FROM product_media_assets WHERE image_data IS NOT NULL")
    )
    if existing:
        raise RuntimeError(
            "Cannot downgrade while durable product images are stored in PostgreSQL"
        )
    with op.batch_alter_table("product_media_assets") as batch:
        batch.drop_column("image_data")
