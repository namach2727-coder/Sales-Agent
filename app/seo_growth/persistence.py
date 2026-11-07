"""Durable, tenant-scoped Google Search Console metric storage (F2b)."""
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer,
    JSON, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import utc_now


class SeoSyncRun(Base):
    __tablename__ = "seo_sync_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        CheckConstraint("status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled')",
                        name="ck_seo_sync_run_status"),
        CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
                        name="ck_seo_sync_run_search_type"),
        CheckConstraint("end_date >= start_date", name="ck_seo_sync_run_dates"),
        CheckConstraint("rows_received >= 0", name="ck_seo_sync_run_rows"),
        UniqueConstraint("id", "tenant_id", "store_id", "site_id", name="uq_seo_sync_run_scope"),
        Index("ix_seo_sync_runs_site_created", "tenant_id", "store_id", "site_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("user_identities.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    search_type: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    cursor_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rows_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SeoPropertyDailyMetric(Base):
    """Authoritative daily property totals; never derived from query/page samples."""
    __tablename__ = "seo_property_daily_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
                        name="ck_seo_property_daily_search_type"),
        CheckConstraint("clicks >= 0 AND impressions >= 0 AND clicks <= impressions",
                        name="ck_seo_property_daily_counts"),
        CheckConstraint("position IS NULL OR position >= 0", name="ck_seo_property_daily_position"),
        CheckConstraint("ctr IS NULL OR ctr BETWEEN 0 AND 1", name="ck_seo_property_daily_ctr"),
        UniqueConstraint("tenant_id", "store_id", "site_id", "metric_date", "search_type",
                         name="uq_seo_property_daily_key"),
        Index("ix_seo_property_daily_period", "tenant_id", "store_id", "site_id", "metric_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    search_type: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    ctr: Mapped[float | None] = mapped_column(Numeric(12, 10), nullable=True)
    position: Mapped[float | None] = mapped_column(Numeric(14, 6), nullable=True)
    source_run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    __table_args__ = __table_args__ + (
        ForeignKeyConstraint(
            ["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"],
        ),
    )


class SeoQueryPageMetric(Base):
    """Bounded Google top-row sample for a specific requested window."""
    __tablename__ = "seo_query_page_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        ForeignKeyConstraint(
            ["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"],
        ),
        CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')",
                        name="ck_seo_query_page_search_type"),
        CheckConstraint("clicks >= 0 AND impressions >= 0 AND clicks <= impressions",
                        name="ck_seo_query_page_counts"),
        CheckConstraint("sample_rank >= 1", name="ck_seo_query_page_rank"),
        CheckConstraint("end_date >= start_date", name="ck_seo_query_page_dates"),
        CheckConstraint("length(row_key) = 64", name="ck_seo_query_page_row_key"),
        CheckConstraint("ctr IS NULL OR ctr BETWEEN 0 AND 1", name="ck_seo_query_page_ctr"),
        UniqueConstraint("tenant_id", "store_id", "site_id", "search_type", "start_date",
                         "end_date", "row_key", name="uq_seo_query_page_window_key"),
        Index("ix_seo_query_page_window", "tenant_id", "store_id", "site_id", "start_date", "end_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    search_type: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    row_key: Mapped[str] = mapped_column(String(64), nullable=False)
    query_text: Mapped[str] = mapped_column(String(300), nullable=False)
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    ctr: Mapped[float | None] = mapped_column(Numeric(12, 10), nullable=True)
    position: Mapped[float | None] = mapped_column(Numeric(14, 6), nullable=True)
    sample_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SeoMetricCoverage(Base):
    """Explicit coverage state; absence of a metric row never implies zero."""
    __tablename__ = "seo_metric_coverage"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        ForeignKeyConstraint(
            ["source_run_id", "tenant_id", "store_id", "site_id"],
            ["seo_sync_runs.id", "seo_sync_runs.tenant_id", "seo_sync_runs.store_id", "seo_sync_runs.site_id"],
        ),
        CheckConstraint("search_type IN ('web', 'image', 'video', 'news', 'discover')", name="ck_seo_coverage_search_type"),
        CheckConstraint("dimension IN ('date', 'query_page')", name="ck_seo_coverage_dimension"),
        CheckConstraint("coverage_status IN ('complete', 'partial', 'empty', 'unknown', 'truncated', 'failed')",
                        name="ck_seo_coverage_status"),
        CheckConstraint("end_date >= start_date", name="ck_seo_coverage_dates"),
        CheckConstraint("rows_received >= 0 AND (row_limit IS NULL OR row_limit > 0)", name="ck_seo_coverage_row_counts"),
        UniqueConstraint("tenant_id", "store_id", "site_id", "search_type", "dimension",
                         "start_date", "end_date", name="uq_seo_coverage_window"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    search_type: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    dimension: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    row_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class SeoSyncLease(Base):
    """One database-backed lease/cursor per site; no scheduler is implied."""
    __tablename__ = "seo_sync_leases"
    __table_args__ = (
        ForeignKeyConstraint(
            ["site_id", "tenant_id", "store_id"],
            ["seo_sites.id", "seo_sites.tenant_id", "seo_sites.store_id"],
        ),
        UniqueConstraint("tenant_id", "store_id", "site_id", name="uq_seo_sync_lease_site"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lease_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cursor_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
