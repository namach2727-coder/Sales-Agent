"""Add tenant-scoped, credential-free SEO crawler audit events."""
from alembic import op
import sqlalchemy as sa

revision = "0031_seo_crawler_audit"
down_revision = "0030_seo_growth_durable_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_crawl_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("crawl_id", sa.String(36), nullable=False),
        sa.Column("event_kind", sa.String(20), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("robots_decision", sa.String(24), nullable=False, server_default="not_checked"),
        sa.Column("url_host", sa.String(253), nullable=False),
        sa.Column("url_fingerprint", sa.String(64), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("bytes_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        sa.CheckConstraint("event_kind IN ('robots', 'page')", name="ck_seo_crawl_audit_event_kind"),
        sa.CheckConstraint(
            "outcome IN ('allowed', 'blocked', 'fetched', 'failed', 'redirected')",
            name="ck_seo_crawl_audit_outcome",
        ),
        sa.CheckConstraint(
            "robots_decision IN ('allow', 'disallow', 'unavailable_allow', 'unavailable_block', 'not_checked')",
            name="ck_seo_crawl_audit_robots_decision",
        ),
        sa.CheckConstraint(
            "http_status IS NULL OR http_status BETWEEN 100 AND 599",
            name="ck_seo_crawl_audit_http_status",
        ),
        sa.CheckConstraint("bytes_received >= 0", name="ck_seo_crawl_audit_bytes"),
        sa.CheckConstraint("duration_ms >= 0", name="ck_seo_crawl_audit_duration"),
    )
    op.create_index(
        "ix_seo_crawl_audit_crawl_id", "seo_crawl_audit_events", ["crawl_id"]
    )
    op.create_index(
        "ix_seo_crawl_audit_site_created", "seo_crawl_audit_events",
        ["tenant_id", "store_id", "site_id", "created_at"],
    )
    op.create_index(
        "ix_seo_crawl_audit_expiry", "seo_crawl_audit_events", ["expires_at"]
    )


    op.create_table(
        "seo_crawl_leases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("host", sa.String(253), nullable=False),
        sa.Column("crawl_id", sa.String(36), nullable=False),
        sa.Column("lease_token", sa.String(64), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("host", name="uq_seo_crawl_lease_host"),
        sa.CheckConstraint("length(crawl_id) = 36", name="ck_seo_crawl_lease_crawl_id"),
        sa.CheckConstraint("length(lease_token) = 64", name="ck_seo_crawl_lease_token"),
        sa.CheckConstraint(
            "lease_expires_at > created_at", name="ck_seo_crawl_lease_expiry"
        ),
    )
    op.create_index(
        "ix_seo_crawl_lease_tenant_expiry", "seo_crawl_leases",
        ["tenant_id", "lease_expires_at"],
    )
    op.create_index(
        "ix_seo_crawl_lease_expiry", "seo_crawl_leases", ["lease_expires_at"]
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.scalar(sa.text("SELECT count(*) FROM seo_crawl_audit_events")):
        raise RuntimeError("Refusing downgrade: SEO crawler audit evidence exists")
    if bind.scalar(sa.text("SELECT count(*) FROM seo_crawl_leases")):
        raise RuntimeError("Refusing downgrade: active SEO crawler leases exist")
    op.drop_index("ix_seo_crawl_lease_expiry", table_name="seo_crawl_leases")
    op.drop_index("ix_seo_crawl_lease_tenant_expiry", table_name="seo_crawl_leases")
    op.drop_table("seo_crawl_leases")
    op.drop_index("ix_seo_crawl_audit_expiry", table_name="seo_crawl_audit_events")
    op.drop_index("ix_seo_crawl_audit_site_created", table_name="seo_crawl_audit_events")
    op.drop_index("ix_seo_crawl_audit_crawl_id", table_name="seo_crawl_audit_events")
    op.drop_table("seo_crawl_audit_events")
