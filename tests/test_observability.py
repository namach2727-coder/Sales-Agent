from __future__ import annotations

import json
import logging

from app.observability import JsonFormatter


def _record(*, failure_category: str) -> logging.LogRecord:
    record = logging.LogRecord(
        name="sales_assistant.instagram_ai_flow",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="instagram_ai_flow_ai_failed",
        args=(),
        exc_info=None,
    )
    record.event_code = "instagram_ai_flow_ai_failed"
    record.correlation_id = "safe-correlation-id"
    record.failure_category = failure_category
    return record


def test_json_formatter_exposes_sanitized_failure_category() -> None:
    payload = json.loads(
        JsonFormatter().format(
            _record(failure_category="llm_provider_configuration_error")
        )
    )

    assert payload["message"] == (
        "instagram_ai_flow_ai_failed "
        "failure_category=llm_provider_configuration_error"
    )
    assert payload["failure_category"] == "llm_provider_configuration_error"
    assert payload["event_code"] == "instagram_ai_flow_ai_failed"


def test_json_formatter_drops_unsafe_category_and_unlisted_extras() -> None:
    api_key = "TEST-API-KEY-MUST-NOT-BE-LOGGED"
    customer_message = "PRIVATE-CUSTOMER-MESSAGE-MUST-NOT-BE-LOGGED"
    unsafe_category = f"invalid category {api_key}"
    record = _record(failure_category=unsafe_category)
    record.api_key = api_key
    record.customer_message = customer_message

    formatted = JsonFormatter().format(record)
    payload = json.loads(formatted)

    assert payload["message"] == "instagram_ai_flow_ai_failed"
    assert "failure_category" not in payload
    assert api_key not in formatted
    assert customer_message not in formatted
