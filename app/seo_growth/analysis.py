"""Deterministic, evidence-backed SEO recommendations (no ranking guarantees).

Input must come from a tenant-authorized Google Search Console property.
No site changes occur in this module. Missing GSC dates remain unknown, not zero.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Literal

@dataclass(frozen=True, slots=True)
class DailyMetric:
    day: date
    clicks: int
    impressions: int
    position: float | None

@dataclass(frozen=True, slots=True)
class QueryPageMetric:
    query: str
    page: str
    clicks: int
    impressions: int
    position: float | None

@dataclass(frozen=True, slots=True)
class SeoOpportunity:
    kind: Literal["snippet_review", "onpage_review", "intent_review"]
    query: str
    page: str
    impressions: int
    clicks: int
    position: float | None
    observed_ctr: float
    reason: str
    proposed_action: str
    action_mode: Literal["proposal_only"] = "proposal_only"

@dataclass(frozen=True, slots=True)
class SeoReport:
    start_date: date
    end_date: date
    observed_days: int
    missing_days: tuple[date, ...]
    coverage: Literal["complete_date_rows", "missing_date_rows"]
    total_clicks: int
    total_impressions: int
    ctr: float | None
    weighted_position: float | None
    opportunities: tuple[SeoOpportunity, ...]
    warnings: tuple[str, ...]

def _validate_counts(clicks: int, impressions: int, position: float | None) -> None:
    if (not isinstance(clicks, int) or isinstance(clicks, bool)
            or not isinstance(impressions, int) or isinstance(impressions, bool)
            or clicks < 0 or impressions < 0 or clicks > impressions):
        raise ValueError("invalid_gsc_counts")
    if position is not None and (not isinstance(position, (int, float))
                                 or not math.isfinite(position) or position <= 0):
        raise ValueError("invalid_gsc_position")

def build_seo_report(
    *, start_date: date, end_date: date, daily_rows: list[DailyMetric],
    query_page_rows: list[QueryPageMetric], min_impressions: int = 50,
    max_opportunities: int = 20,
) -> SeoReport:
    """Return a bounded review list, not automated writes or uplift promises.

    Property totals come ONLY from date rows: Search Console can omit top/long
    tail query and page rows, and missing date rows cannot be inferred as zero.
    """
    if end_date < start_date or (end_date - start_date).days > 365:
        raise ValueError("invalid_date_range")
    if not 1 <= min_impressions <= 1_000_000 or not 1 <= max_opportunities <= 100:
        raise ValueError("invalid_analysis_limits")

    seen_days: set[date] = set()
    for row in daily_rows:
        _validate_counts(row.clicks, row.impressions, row.position)
        if row.day in seen_days or row.day < start_date or row.day > end_date:
            raise ValueError("invalid_or_duplicate_daily_row")
        seen_days.add(row.day)
    missing_days = tuple(start_date + timedelta(days=i)
                         for i in range((end_date - start_date).days + 1)
                         if start_date + timedelta(days=i) not in seen_days)
    clicks = sum(row.clicks for row in daily_rows)
    impressions = sum(row.impressions for row in daily_rows)
    position_rows = [row for row in daily_rows if row.impressions and row.position is not None]
    covered = sum(row.impressions for row in position_rows)
    position = (sum(row.impressions * float(row.position) for row in position_rows) / impressions
                if impressions and covered == impressions else None)

    candidates: list[SeoOpportunity] = []
    unique: set[tuple[str, str]] = set()
    for row in query_page_rows:
        _validate_counts(row.clicks, row.impressions, row.position)
        if len(row.query) > 300 or len(row.page) > 2048:
            raise ValueError("invalid_query_page_row")
        key = (row.query, row.page)
        if key in unique:
            raise ValueError("duplicate_query_page_row")
        unique.add(key)
        if row.impressions < min_impressions or row.position is None:
            continue
        ctr = row.clicks / row.impressions
        # These are *triage heuristics*, not universal CTR benchmarks.
        if 4 <= row.position <= 20 and ctr <= 0.02 and row.impressions >= 100:
            kind: Literal["snippet_review", "onpage_review", "intent_review"] = "snippet_review"
            reason = "High impressions and low observed CTR in a potentially visible position range."
            action = "Review intent and current title/snippet; draft a proposed revision for approval."
        elif 8 <= row.position <= 20:
            kind = "onpage_review"
            reason = "Observed impressions with average search position between 8 and 20."
            action = "Review content usefulness, page structure and internal navigation."
        elif row.position > 20 and row.impressions >= 100:
            kind = "intent_review"
            reason = "Impressions with position beyond 20; GSC alone cannot identify cause."
            action = "Review search intent, existing page usefulness and competition; avoid mass content."
        else:
            continue
        candidates.append(SeoOpportunity(
            kind=kind, query=row.query, page=row.page, impressions=row.impressions,
            clicks=row.clicks, position=row.position, observed_ctr=ctr,
            reason=reason, proposed_action=action,
        ))
    candidates.sort(key=lambda item: (-item.impressions, item.query, item.page))
    warnings = [
        "Opportunities are review candidates, not Google ranking predictions.",
        "Search Console query/page rows may be truncated; do not sum them as property totals.",
    ]
    if missing_days:
        warnings.append("Missing date rows are unknown, not zero; period coverage is incomplete.")
    if not impressions:
        warnings.append("No reported impressions: CTR and average position are undefined.")
    return SeoReport(
        start_date=start_date, end_date=end_date, observed_days=len(daily_rows),
        missing_days=missing_days, coverage="missing_date_rows" if missing_days else "complete_date_rows",
        total_clicks=clicks, total_impressions=impressions,
        ctr=clicks / impressions if impressions else None, weighted_position=position,
        opportunities=tuple(candidates[:max_opportunities]), warnings=tuple(warnings),
    )
