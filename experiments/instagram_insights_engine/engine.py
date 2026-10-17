"""Typed, source-grounded Instagram Insights processing — UAT prototype only.

Metrics are from the *owner-authorized professional Instagram account*; never
guess missing values. The source adapter intentionally performs no HTTP calls.
The AI input prompt contains only aggregate numeric KPIs, no credentials or
personal-level information, and must be subject to quota & consent in runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Mapping
from urllib.parse import quote

PROPOSED_AI_QUOTAS = {"AUTOMATION": 3, "AI_ASSISTANT": 15}
# Start with a conservative subset of the documented account insights metrics.
ACCOUNT_METRICS = frozenset({"reach", "views", "accounts_engaged", "total_interactions"})
MEDIA_METRICS = frozenset({"reach", "views", "likes", "comments", "saved", "shares"})

@dataclass(frozen=True)
class MetricSnapshot:
    account_id: str
    period_start: datetime
    period_end: datetime
    collected_at: datetime
    metrics: Mapping[str, int | None]
    source: str = "meta_instagram_api"

    def __post_init__(self) -> None:
        if not self.account_id.isdecimal() or not (1 <= len(self.account_id) <= 32):
            raise ValueError("Invalid IG account ID")
        if self.source != "meta_instagram_api":
            raise ValueError("Metrics source must be explicit")
        if any(d.tzinfo is None or d.utcoffset() is None for d in
               (self.period_start, self.period_end, self.collected_at)):
            raise ValueError("Timezone-aware timestamps required")
        if not self.period_start < self.period_end <= self.collected_at:
            raise ValueError("Invalid reporting period")
        for key, value in self.metrics.items():
            if key not in ACCOUNT_METRICS:
                raise ValueError("Unsupported account metric")
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Numeric metrics must be nonnegative or missing")


def metric_delta(current: int | None, previous: int | None) -> Decimal | None:
    """Percentage comparison. Zero/absent denominator -> missing, not infinity."""
    if current is None or previous is None or previous <= 0:
        return None
    return (Decimal(current - previous) * Decimal(100) / Decimal(previous)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def compare_snapshots(
    current: MetricSnapshot, previous: MetricSnapshot | None
) -> dict[str, object]:
    if previous and current.account_id != previous.account_id:
        raise ValueError("Cross-account comparison prohibited")
    data: dict[str, object] = {
        "source": "meta_instagram_api",
        "account_id": current.account_id,
        "period_start": current.period_start.astimezone(timezone.utc).isoformat(),
        "period_end": current.period_end.astimezone(timezone.utc).isoformat(),
        "collected_at": current.collected_at.astimezone(timezone.utc).isoformat(),
        "metrics": {},
        "warnings": [],
    }
    metrics: dict[str, object] = {}
    warnings: list[str] = []
    for key in sorted(ACCOUNT_METRICS):
        value = current.metrics.get(key)
        prior = previous.metrics.get(key) if previous else None
        metrics[key] = {
            "value": value,
            "previous": prior,
            "change_percent": float(delta) if (delta := metric_delta(value, prior)) is not None else None,
        }
        if value is None:
            warnings.append(f"{key}: Meta did not supply this metric.")
    if previous is None:
        warnings.append("No previous period for comparison.")
    data["metrics"] = metrics
    data["warnings"] = warnings
    return data


def build_ai_report_input(summary: dict[str, object]) -> tuple[str, str]:
    """Generate guarded prompts for a later AI adapter — does NOT call an LLM."""
    if summary.get("source") != "meta_instagram_api":
        raise ValueError("Cannot analyze unverified or demo data as Meta source")
    facts = {
        key: summary.get(key) for key in
        ("period_start", "period_end", "collected_at", "metrics", "warnings")
    }
    system = (
        "You are a Persian-language Instagram analytics assistant. "
        "Use only the supplied aggregate metrics and time period. "
        "State limitations and avoid claiming causation, audience demographics, "
        "financial uplift, algorithm secrets, content quality, or predictions "
        "without evidence. Never invent missing values. "
        "Provide up to three testable recommendations, labeling hypotheses."
    )
    user = (
        "Only these aggregated, verified business metrics may be used. "
        "Explain changes, missing data, and 3 low-risk tests in Persian.\n"
        + json.dumps(facts, ensure_ascii=False, sort_keys=True)
    )
    return system, user


def build_meta_insights_request(account_id: str, metrics: tuple[str, ...], period: str) -> tuple[str, dict[str, str]]:
    """Build a safe HTTPS path and params; access token is never in URL/params.

    API version, OAuth headers, rate limit, permissions and account ownership
    require integration UAT before making a real Meta request.
    """
    if not account_id.isdecimal() or not (1 <= len(account_id) <= 32):
        raise ValueError("Invalid IG account ID")
    if not metrics or set(metrics) - ACCOUNT_METRICS:
        raise ValueError("Unsupported account metrics")
    if period not in {"day", "week", "days_28"}:
        raise ValueError("Unsupported period")
    return f"/{quote(account_id, safe='')}/insights", {
        "metric": ",".join(metrics), "period": period,
    }
