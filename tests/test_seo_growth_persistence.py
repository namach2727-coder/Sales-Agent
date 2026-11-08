"""Metadata contracts for durable, tenant-scoped SEO reporting storage."""
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from app.database import Base
from app import models  # noqa: F401 - registers all application tables


def test_f2b_tables_are_registered_and_scope_bound():
    expected = {
        "seo_sync_runs",
        "seo_property_daily_metrics",
        "seo_query_page_metrics",
        "seo_metric_coverage",
        "seo_sync_leases",
        "seo_crawl_audit_events",
    }
    assert expected <= set(Base.metadata.tables)

    for name in expected:
        table = Base.metadata.tables[name]
        foreign_keys = [
            tuple(element.parent.name for element in constraint.elements)
            for constraint in table.foreign_key_constraints
        ]
        assert ("site_id", "tenant_id", "store_id") in foreign_keys
        assert "tenant_id" in table.c and "store_id" in table.c


def test_daily_property_totals_are_independent_from_query_page_samples():
    daily = Base.metadata.tables["seo_property_daily_metrics"]
    query_page = Base.metadata.tables["seo_query_page_metrics"]

    assert "query_text" not in daily.c and "page_url" not in daily.c
    assert {"clicks", "impressions", "ctr", "position"} <= set(daily.c.keys())
    assert {"query_text", "page_url", "row_key"} <= set(query_page.c.keys())

    daily_keys = {
        tuple(column.name for column in constraint.columns)
        for constraint in daily.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    sample_keys = {
        tuple(column.name for column in constraint.columns)
        for constraint in query_page.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("tenant_id", "store_id", "site_id", "metric_date", "search_type") in daily_keys
    assert ("tenant_id", "store_id", "site_id", "search_type", "start_date",
            "end_date", "row_key") in sample_keys


def test_coverage_and_lease_tables_preserve_unknown_and_resumable_states():
    coverage = Base.metadata.tables["seo_metric_coverage"]
    lease = Base.metadata.tables["seo_sync_leases"]

    assert {"dimension", "coverage_status", "rows_received", "row_limit"} <= set(coverage.c.keys())
    assert {"lease_token", "lease_expires_at", "cursor_json"} <= set(lease.c.keys())
    assert any(isinstance(item, ForeignKeyConstraint) for item in coverage.constraints)
    assert any(isinstance(item, UniqueConstraint) and
               tuple(c.name for c in item.columns) == ("tenant_id", "store_id", "site_id")
               for item in lease.constraints)
