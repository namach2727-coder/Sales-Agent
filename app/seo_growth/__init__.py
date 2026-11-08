"""DirectPilot SEO Growth, customer-facing commercial module foundation.

Read-only Google provider, proposal-only analysis and tenant OAuth onboarding.
Commercial billing, scheduled ingestion and CMS write operations are future work.
"""
from .analysis import DailyMetric, QueryPageMetric, SeoOpportunity, SeoReport, build_seo_report

__all__ = ["DailyMetric", "QueryPageMetric", "SeoOpportunity", "SeoReport", "build_seo_report"]
