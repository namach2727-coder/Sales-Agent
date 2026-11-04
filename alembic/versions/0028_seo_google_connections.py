"""Create tenant-scoped Google Search Console connection tables."""

from alembic import op
import sqlalchemy as sa

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = True

revision = "0028_seo_google_connections"
down_revision = "0027_traceable_receipt_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_google_oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("state_digest", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("initiated_by_user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("state_digest", name="uq_seo_google_oauth_state_digest"),
        sa.ForeignKeyConstraint(("store_id", "tenant_id"), ("stores.id", "stores.tenant_id"),
                                name="fk_seo_google_oauth_state_store_tenant"),
    )
    op.create_index("ix_seo_google_oauth_states_public_id", "seo_google_oauth_states", ["public_id"], unique=True)
    op.create_index("ix_seo_google_oauth_states_tenant_id", "seo_google_oauth_states", ["tenant_id"])
    op.create_index("ix_seo_google_oauth_states_store_id", "seo_google_oauth_states", ["store_id"])
    op.create_index("ix_seo_google_oauth_states_initiated_by_user_id", "seo_google_oauth_states", ["initiated_by_user_id"])
    op.create_index("ix_seo_google_oauth_states_expires_at", "seo_google_oauth_states", ["expires_at"])
    op.create_index("ix_seo_google_oauth_state_scope", "seo_google_oauth_states", ["tenant_id", "store_id", "expires_at"])

    op.create_table(
        "seo_google_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("google_subject", sa.String(255), nullable=False),
        sa.Column("google_email", sa.String(320), nullable=True),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("granted_scopes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("connected_by_user_id", sa.Integer(), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("id", "tenant_id", "store_id", name="uq_seo_google_connection_scope"),
        sa.UniqueConstraint("store_id", name="uq_seo_google_connection_store"),
        sa.ForeignKeyConstraint(("store_id", "tenant_id"), ("stores.id", "stores.tenant_id"),
                                name="fk_seo_google_connection_store_tenant"),
        sa.CheckConstraint("status IN ('active', 'reauthorization_required', 'disconnected')",
                           name="ck_seo_google_connection_status"),
    )
    op.create_index("ix_seo_google_connections_public_id", "seo_google_connections", ["public_id"], unique=True)
    op.create_index("ix_seo_google_connections_tenant_id", "seo_google_connections", ["tenant_id"])
    op.create_index("ix_seo_google_connections_store_id", "seo_google_connections", ["store_id"])
    op.create_index("ix_seo_google_connections_google_subject", "seo_google_connections", ["google_subject"])
    op.create_index("ix_seo_google_connections_status", "seo_google_connections", ["status"])
    op.create_index("ix_seo_google_connections_connected_by_user_id", "seo_google_connections", ["connected_by_user_id"])
    op.create_index("ix_seo_google_connection_tenant_store", "seo_google_connections", ["tenant_id", "store_id", "status"])

    op.create_table(
        "seo_search_properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("property_uri", sa.String(2048), nullable=False),
        sa.Column("permission_level", sa.String(32), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("store_id", "property_uri", name="uq_seo_property_store_uri"),
        sa.ForeignKeyConstraint(("connection_id", "tenant_id", "store_id"),
                                ("seo_google_connections.id", "seo_google_connections.tenant_id", "seo_google_connections.store_id"),
                                name="fk_seo_property_connection_scope"),
        sa.CheckConstraint("permission_level IN ('siteOwner', 'siteFullUser', 'siteRestrictedUser', 'siteUnverifiedUser')",
                           name="ck_seo_property_permission"),
    )
    op.create_index("ix_seo_search_properties_public_id", "seo_search_properties", ["public_id"], unique=True)
    op.create_index("ix_seo_search_properties_tenant_id", "seo_search_properties", ["tenant_id"])
    op.create_index("ix_seo_search_properties_store_id", "seo_search_properties", ["store_id"])
    op.create_index("ix_seo_search_properties_connection_id", "seo_search_properties", ["connection_id"])
    op.create_index("ix_seo_property_scope", "seo_search_properties", ["tenant_id", "store_id", "is_selected"])


def downgrade() -> None:
    op.drop_table("seo_search_properties")
    op.drop_table("seo_google_connections")
    op.drop_table("seo_google_oauth_states")
