"""Add optimistic revision to SEO pilot grants without changing any entitlement."""
from alembic import op
import sqlalchemy as sa

revision = "0029_seo_pilot_revision"
down_revision = "0028_seo_google_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("seo_access_grants") as batch:
        batch.add_column(sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
        batch.create_check_constraint("ck_seo_grant_revision", "revision >= 1")


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM seo_access_grants")):
        raise RuntimeError("Refusing downgrade: SEO pilot revision evidence exists")
    with op.batch_alter_table("seo_access_grants") as batch:
        batch.drop_constraint("ck_seo_grant_revision", type_="check")
        batch.drop_column("revision")
