from __future__ import annotations

from contextvars import ContextVar
from datetime import UTC, datetime
import json
import logging
import re
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import Settings


correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SAFE_LOG_CATEGORY = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        failure_category = _safe_log_category(
            getattr(record, "failure_category", None)
        )
        if failure_category is not None:
            message = f"{message} failure_category={failure_category}"
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "correlation_id": getattr(record, "correlation_id", None) or correlation_id.get(),
        }
        if hasattr(record, "event_code"):
            payload["event_code"] = record.event_code
        if failure_category is not None:
            payload["failure_category"] = failure_category
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _safe_log_category(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if SAFE_LOG_CATEGORY.fullmatch(normalized) else None


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    handler = next(
        (item for item in root.handlers if getattr(item, "_sales_agent_handler", False)),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler()
        handler._sales_agent_handler = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    formatter: logging.Formatter = (
        JsonFormatter()
        if settings.json_logs
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(message)s] correlation_id=%(correlation_id)s")
    )
    if not settings.json_logs:
        class CorrelationFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                if not getattr(record, "correlation_id", None):
                    record.correlation_id = correlation_id.get()
                return True
        handler.addFilter(CorrelationFilter())
    handler.setFormatter(formatter)
    root.setLevel(settings.log_level)
    # These libraries may otherwise include full URLs or connection metadata.
    for logger_name in ("httpx", "httpcore", "sqlalchemy.engine", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if SAFE_REQUEST_ID.fullmatch(supplied) else str(uuid.uuid4())
        token = correlation_id.set(request_id)
        request.state.correlation_id = request_id
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            correlation_id.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'",
        )
        return response
