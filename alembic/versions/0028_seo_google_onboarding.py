"""Add independent SEO pilot grants and tenant-bound Google onboarding.

No grants, plans, prices or customer credentials are seeded by this migration.
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_seo_google_onboarding"
down_revision = "0027_traceable_receipt_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("seo_access_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("max_sites", sa.Integer(), nullable=False),
        sa.Column("max_connections", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]),
        sa.UniqueConstraint("tenant_id", "store_id", name="uq_seo_grant_scope"),
        sa.CheckConstraint("max_sites BETWEEN 1 AND 20", name="ck_seo_grant_sites"),
        sa.CheckConstraint("max_connections BETWEEN 1 AND 10", name="ck_seo_grant_connections"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_seo_grant_status"))
    op.create_table("seo_oauth_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("state_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("session_digest", sa.String(64), nullable=False),
        sa.Column("encrypted_verifier", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]))
    op.create_table("seo_google_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("key_version", sa.String(30), nullable=False),
        sa.Column("granted_scope", sa.Text(), nullable=False),
        sa.Column("consent_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["store_id", "tenant_id"], ["stores.id", "stores.tenant_id"]),
        sa.UniqueConstraint("tenant_id", "store_id", "user_id", name="uq_seo_connection_owner"),
        sa.UniqueConstraint("id", "tenant_id", "store_id", name="uq_seo_connection_scope"),
        sa.CheckConstraint("status IN ('connected', 'reauthorization_required', 'disconnected')", name="ck_seo_connection_status"))
    op.create_table("seo_sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.String(2048), nullable=False),
        sa.Column("permission_level", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id", "tenant_id", "store_id"],
                                ["seo_google_connections.id", "seo_google_connections.tenant_id", "seo_google_connections.store_id"]),
        sa.UniqueConstraint("tenant_id", "store_id", "property_id", name="uq_seo_site_property"),
        sa.CheckConstraint("status IN ('connected', 'disconnected', 'permission_lost')", name="ck_seo_site_status"))
    for table in ("seo_access_grants", "seo_oauth_attempts", "seo_google_connections", "seo_sites"):
        for column in ("tenant_id", "store_id"):
            op.create_index(f"ix_{table}_{column}", table, [column])
    for table in ("seo_oauth_attempts", "seo_google_connections"):
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])
    for table in ("seo_google_connections", "seo_sites"):
        op.create_index(f"ix_{table}_public_id", table, ["public_id"], unique=True)
    op.create_index("ix_seo_sites_connection_id", "seo_sites", ["connection_id"])


def downgrade() -> None:
    # Explicitly refuse to destroy any onboarding, entitlement or site evidence.
    for table in ("seo_sites", "seo_google_connections", "seo_oauth_attempts", "seo_access_grants"):
        if op.get_bind().scalar(sa.text(f"SELECT count(*) FROM {table}")):
            raise RuntimeError("Refusing downgrade: SEO onboarding evidence exists")
    op.drop_table("seo_sites")
    op.drop_table("seo_google_connections")
    op.drop_table("seo_oauth_attempts")
    op.drop_table("seo_access_grants")
