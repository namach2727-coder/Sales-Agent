"""Validated metadata semantics for Instagram outbound delivery certainty."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final
from uuid import uuid4


NOT_SENT_CONFIRMED: Final = "NOT_SENT_CONFIRMED"
SENT_CONFIRMED: Final = "SENT_CONFIRMED"
FAILED_CONFIRMED: Final = "FAILED_CONFIRMED"
DELIVERY_AMBIGUOUS: Final = "DELIVERY_AMBIGUOUS"

NOT_REQUIRED: Final = "NOT_REQUIRED"
REQUIRED: Final = "REQUIRED"
IN_PROGRESS: Final = "IN_PROGRESS"
RESOLVED: Final = "RESOLVED"

DELIVERY_CERTAINTIES: Final = frozenset(
    {NOT_SENT_CONFIRMED, SENT_CONFIRMED, FAILED_CONFIRMED, DELIVERY_AMBIGUOUS}
)
RECONCILIATION_STATUSES: Final = frozenset(
    {NOT_REQUIRED, REQUIRED, IN_PROGRESS, RESOLVED}
)


def attempt_marker(
    existing: dict[str, object],
    *,
    attempt_count: int,
    reconciliation_value: str = REQUIRED,
) -> tuple[dict[str, object], str]:
    if reconciliation_value not in {REQUIRED, IN_PROGRESS}:
        raise ValueError("invalid attempt reconciliation status")
    attempt_id = str(uuid4())
    result = dict(existing)
    result.update(
        {
            "delivery_status": "pending",
            "delivery_provider": "instagram",
            "delivery_attempt_count": attempt_count,
            "delivery_attempt_id": attempt_id,
            "provider_call_started_at": datetime.now(UTC).isoformat(),
            "delivery_certainty": DELIVERY_AMBIGUOUS,
            "reconciliation_status": reconciliation_value,
            "reconciliation_reason": "provider_attempt_outcome_unknown",
            "safe_retry_eligible": False,
        }
    )
    result.pop("last_failure_category", None)
    return result, attempt_id


def certainty(metadata: dict[str, object]) -> str | None:
    value = metadata.get("delivery_certainty")
    return value if isinstance(value, str) and value in DELIVERY_CERTAINTIES else None


def reconciliation_status(metadata: dict[str, object]) -> str | None:
    value = metadata.get("reconciliation_status")
    return value if isinstance(value, str) and value in RECONCILIATION_STATUSES else None


def retry_eligible(metadata: dict[str, object]) -> bool:
    return metadata.get("safe_retry_eligible") is True
