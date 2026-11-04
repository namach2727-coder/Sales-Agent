"""Add durable tenant-scoped GSC sync, metrics, coverage and leases (F2b)."""
from alembic import op
import sqlalchemy as sa

revision = "0030_seo_growth_durable_data"
down_revision = "0029_seo_pilot_revision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_seo_sites_id_tenant_store", "seo_sites", ["id", "tenant_id", "store_id"]
    )
    op.create_table(
        "seo_sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("search_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("cursor_json", sa.JSON(), nullable=True),
        sa.Column("rows_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"]),
        sa.CheckConstraint("status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled')",
            name="ck_seo_sync_run_status"),
        sa.CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
            name="ck_seo_sync_run_search_type"),
        sa.CheckConstraint("end_date >= start_date", name="ck_seo_sync_run_dates"),
        sa.UniqueConstraint("id", "tenant_id", "store_id", "site_id", name="uq_seo_sync_run_scope"),
    )
    op.create_index("ix_seo_sync_runs_site_created", "seo_sync_runs",
        ["tenant_id", "store_id", "site_id", "created_at"])

    op.create_table(
        "seo_property_daily_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("search_type", sa.String(20), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("ctr", sa.Numeric(12, 10), nullable=True),
        sa.Column("position", sa.Numeric(14, 6), nullable=True),
        sa.Column("source_run_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"]),
        sa.ForeignKeyConstraint(["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"]),
        sa.CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
            name="ck_seo_property_daily_search_type"),
        sa.CheckConstraint("clicks >= 0 AND impressions >= 0 AND clicks <= impressions",
            name="ck_seo_property_daily_counts"),
        sa.CheckConstraint("position IS NULL OR position >= 0", name="ck_seo_property_daily_position"),
        sa.UniqueConstraint("tenant_id", "store_id", "site_id", "metric_date", "search_type",
            name="uq_seo_property_daily_key"),
    )
    op.create_index("ix_seo_property_daily_period", "seo_property_daily_metrics",
        ["tenant_id", "store_id", "site_id", "metric_date"])

    op.create_table(
        "seo_query_page_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("source_run_id", sa.Integer(), nullable=False),
        sa.Column("search_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("query_text", sa.String(300), nullable=False),
        sa.Column("page_url", sa.String(2048), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("ctr", sa.Numeric(12, 10), nullable=True),
        sa.Column("position", sa.Numeric(14, 6), nullable=True),
        sa.Column("sample_rank", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"]),
        sa.ForeignKeyConstraint(["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"]),
        sa.CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
            name="ck_seo_query_page_search_type"),
        sa.CheckConstraint("clicks >= 0 AND impressions >= 0 AND clicks <= impressions",
            name="ck_seo_query_page_counts"),
        sa.CheckConstraint("sample_rank >= 1", name="ck_seo_query_page_rank"),
        sa.UniqueConstraint("tenant_id", "store_id", "site_id", "search_type", "start_date",
            "end_date", "query_text", "page_url", name="uq_seo_query_page_window_key"),
    )
    op.create_index("ix_seo_query_page_window", "seo_query_page_metrics",
        ["tenant_id", "store_id", "site_id", "start_date", "end_date"])

    op.create_table(
        "seo_metric_coverage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("source_run_id", sa.Integer(), nullable=False),
        sa.Column("search_type", sa.String(20), nullable=False),
        sa.Column("dimension", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("coverage_status", sa.String(20), nullable=False),
        sa.Column("rows_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("row_limit", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"]),
        sa.ForeignKeyConstraint(["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"]),
        sa.CheckConstraint("dimension IN ('date', 'query_page')", name="ck_seo_coverage_dimension"),
        sa.CheckConstraint("coverage_status IN ('complete', 'partial', 'empty', 'unknown', 'truncated', 'failed')",
            name="ck_seo_coverage_status"),
        sa.CheckConstraint("end_date >= start_date", name="ck_seo_coverage_dates"),
        sa.UniqueConstraint("tenant_id", "store_id", "site_id", "search_type", "dimension",
            "start_date", "end_date", name="uq_seo_coverage_window"),
    )

    op.create_table(
        "seo_sync_leases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.String(64), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"]),
        sa.UniqueConstraint("tenant_id", "store_id", "site_id", name="uq_seo_sync_lease_site"),
    )


def downgrade() -> None:
    raise RuntimeError("Refusing destructive downgrade of durable SEO reporting evidence")
