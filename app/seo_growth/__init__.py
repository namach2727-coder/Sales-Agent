"""DirectPilot SEO Growth, customer-facing commercial module foundation.

Read-only Google provider and proposal-only analysis are implemented here.
Tenant OAuth persistence, paid entitlement, UI and CMS write operations are NOT.
"""
from .analysis import DailyMetric, QueryPageMetric, SeoOpportunity, SeoReport, build_seo_report

__all__ = ["DailyMetric", "QueryPageMetric", "SeoOpportunity", "SeoReport", "build_seo_report"]
