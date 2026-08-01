"""Official OpenAI Responses API adapter for the application LLM contract."""

from __future__ import annotations

import logging
from time import monotonic
from typing import Any, Protocol
from uuid import uuid4

from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from app.application.llm import (
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderRequestError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMResponse,
)
from app.application.prompts import PromptPackage


logger = logging.getLogger("sales_assistant.llm.openai")
PROVIDER_NAME = "openai"


class ResponsesResource(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class OpenAIClient(Protocol):
    responses: ResponsesResource


class OpenAIProvider:
    """Map immutable prompt packages to one bounded OpenAI request."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        client: OpenAIClient | None = None,
    ) -> None:
        credential = api_key.strip() if isinstance(api_key, str) else ""
        if not credential:
            raise LLMProviderConfigurationError(
                "OpenAI credentials are not configured"
            )
        self.model = _configured_model(model)
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise LLMProviderConfigurationError(
                "OpenAI timeout configuration is invalid"
            )
        if not 1.0 <= float(timeout_seconds) <= 300.0:
            raise LLMProviderConfigurationError(
                "OpenAI timeout configuration is invalid"
            )
        if (
            isinstance(max_retries, bool)
            or not isinstance(max_retries, int)
            or not 0 <= max_retries <= 3
        ):
            raise LLMProviderConfigurationError(
                "OpenAI retry configuration is invalid"
            )
        self.timeout_seconds = float(timeout_seconds)
        self.max_retries = max_retries
        self._client: OpenAIClient = (
            client
            if client is not None
            else OpenAI(
                api_key=credential,
                timeout=self.timeout_seconds,
                max_retries=self.max_retries,
            )
        )

    def generate(self, prompt_package: PromptPackage) -> LLMResponse:
        if not isinstance(prompt_package, PromptPackage):
            raise LLMProviderRequestError("Invalid prompt package")

        request_public_id = str(uuid4())
        started_at = monotonic()
        logger.info(
            "llm request started provider=%s model=%s request_public_id=%s",
            PROVIDER_NAME,
            self.model,
            request_public_id,
            extra={"event_code": "llm.request.started"},
        )
        try:
            response = self._client.responses.create(
                model=self.model,
                instructions=prompt_package.system_prompt,
                input=prompt_package.user_prompt,
                store=False,
            )
        except AuthenticationError as exc:
            self._log_failure("authentication", request_public_id, started_at)
            raise LLMProviderAuthenticationError(
                "OpenAI authentication failed"
            ) from exc
        except APITimeoutError as exc:
            self._log_failure("timeout", request_public_id, started_at)
            raise LLMProviderTimeoutError("OpenAI request timed out") from exc
        except RateLimitError as exc:
            self._log_failure("rate_limit", request_public_id, started_at)
            raise LLMProviderRateLimitError(
                "OpenAI rate limit was reached"
            ) from exc
        except (APIConnectionError, InternalServerError) as exc:
            self._log_failure("unavailable", request_public_id, started_at)
            raise LLMProviderUnavailableError(
                "OpenAI is temporarily unavailable"
            ) from exc
        except APIResponseValidationError as exc:
            self._log_failure("invalid_response", request_public_id, started_at)
            raise LLMProviderInvalidResponseError(
                "OpenAI returned an invalid response"
            ) from exc
        except (
            BadRequestError,
            PermissionDeniedError,
            UnprocessableEntityError,
        ) as exc:
            self._log_failure("invalid_request", request_public_id, started_at)
            raise LLMProviderRequestError(
                "OpenAI rejected the request"
            ) from exc
        except Exception as exc:
            self._log_failure("provider_error", request_public_id, started_at)
            raise LLMProviderError("OpenAI request failed") from exc

        try:
            result = _normalized_response(
                response,
                configured_model=self.model,
                request_public_id=request_public_id,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            self._log_failure("invalid_response", request_public_id, started_at)
            raise LLMProviderInvalidResponseError(
                "OpenAI returned an invalid response"
            ) from exc

        logger.info(
            (
                "llm request completed provider=%s model=%s "
                "request_public_id=%s latency_ms=%s input_tokens=%s "
                "output_tokens=%s total_tokens=%s"
            ),
            PROVIDER_NAME,
            result.model,
            request_public_id,
            _elapsed_ms(started_at),
            result.input_tokens,
            result.output_tokens,
            result.total_tokens,
            extra={"event_code": "llm.request.completed"},
        )
        return result

    def _log_failure(
        self,
        outcome: str,
        request_public_id: str,
        started_at: float,
    ) -> None:
        logger.warning(
            (
                "llm request failed provider=%s model=%s "
                "request_public_id=%s latency_ms=%s outcome=%s"
            ),
            PROVIDER_NAME,
            self.model,
            request_public_id,
            _elapsed_ms(started_at),
            outcome,
            extra={"event_code": f"llm.request.{outcome}"},
        )


def _normalized_response(
    response: Any,
    *,
    configured_model: str,
    request_public_id: str,
) -> LLMResponse:
    usage = getattr(response, "usage", None)
    status = _optional_scalar_text(getattr(response, "status", None))
    metadata = {"status": status} if status is not None else {}
    return LLMResponse(
        text=getattr(response, "output_text"),
        provider=PROVIDER_NAME,
        model=(
            _optional_scalar_text(getattr(response, "model", None))
            or configured_model
        ),
        finish_reason=_finish_reason(response),
        input_tokens=_optional_token(usage, "input_tokens"),
        output_tokens=_optional_token(usage, "output_tokens"),
        total_tokens=_optional_token(usage, "total_tokens"),
        request_public_id=request_public_id,
        provider_request_id=_optional_scalar_text(
            getattr(response, "_request_id", None)
        ),
        metadata=metadata,
    )


def _finish_reason(response: Any) -> str | None:
    direct = _optional_scalar_text(getattr(response, "finish_reason", None))
    if direct is not None:
        return direct
    incomplete = getattr(response, "incomplete_details", None)
    if incomplete is not None:
        reason = _optional_scalar_text(getattr(incomplete, "reason", None))
        if reason is not None:
            return reason
    return _optional_scalar_text(getattr(response, "status", None))


def _optional_token(usage: Any, name: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, name, None)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid {name}")
    return value


def _optional_scalar_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("provider response text field is invalid")
    normalized = value.strip()
    return normalized or None


def _configured_model(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "OpenAI model configuration is invalid"
        )
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > 100
        or "\n" in normalized
        or "\r" in normalized
    ):
        raise LLMProviderConfigurationError(
            "OpenAI model configuration is invalid"
        )
    return normalized


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((monotonic() - started_at) * 1000))
