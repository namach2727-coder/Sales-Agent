"""Groq chat-completions adapter for the provider-neutral LLM contract."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from time import monotonic
from typing import Any, Protocol
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

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
from app.application.prompts import PromptContextBudget, PromptPackage


logger = logging.getLogger("sales_assistant.llm.groq")
PROVIDER_NAME = "groq"
CHAT_COMPLETIONS_PATH = "chat/completions"
PROMPT_OVERHEAD_BUDGET = 64


class GroqHttpResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def json(self) -> Any: ...

    def raise_for_status(self) -> None: ...


class GroqClient(Protocol):
    def post(
        self,
        url: str,
        *,
        json: Mapping[str, Any],
    ) -> GroqHttpResponse: ...


class GroqProvider:
    """Map one immutable prompt package to one bounded Groq request."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
        context_length: int = 4096,
        max_output_tokens: int = 256,
        reasoning_effort: str = "none",
        client: GroqClient | None = None,
    ) -> None:
        credential = _configured_api_key(api_key)
        self.base_url = _configured_base_url(base_url)
        self.model = _configured_model(model)
        self.timeout_seconds = _configured_timeout(timeout_seconds)
        self.context_length = _configured_context_length(context_length)
        self.max_output_tokens = _configured_max_output_tokens(max_output_tokens)
        self.reasoning_effort = _configured_reasoning_effort(reasoning_effort)
        if self.max_output_tokens + PROMPT_OVERHEAD_BUDGET >= self.context_length:
            raise LLMProviderConfigurationError(
                "Groq context configuration leaves no input budget"
            )
        self._client: GroqClient = (
            client
            if client is not None
            else httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seconds),
                follow_redirects=False,
                headers={"Authorization": f"Bearer {credential}"},
            )
        )

    @property
    def context_budget(self) -> PromptContextBudget:
        return PromptContextBudget(
            context_limit=self.context_length,
            reserved_output_tokens=self.max_output_tokens,
            safety_margin_tokens=PROMPT_OVERHEAD_BUDGET,
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
        if not self._prompt_fits(prompt_package):
            self._log_failure("input_too_large", request_public_id, started_at)
            raise LLMProviderRequestError(
                "Groq prompt exceeds the configured context budget"
            )

        try:
            response = self._client.post(
                CHAT_COMPLETIONS_PATH,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt_package.system_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt_package.user_prompt,
                        },
                    ],
                    "max_completion_tokens": self.max_output_tokens,
                    "reasoning_effort": self.reasoning_effort,
                    "stream": False,
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            self._log_failure("timeout", request_public_id, started_at)
            raise LLMProviderTimeoutError("Groq request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise self._mapped_status_error(
                exc,
                request_public_id=request_public_id,
                started_at=started_at,
            ) from exc
        except httpx.RequestError as exc:
            self._log_failure("unavailable", request_public_id, started_at)
            raise LLMProviderUnavailableError(
                "Groq is temporarily unavailable"
            ) from exc
        except Exception as exc:
            self._log_failure("provider_error", request_public_id, started_at)
            raise LLMProviderError("Groq request failed") from exc

        try:
            result = _normalized_response(
                response.json(),
                headers=response.headers,
                configured_model=self.model,
                request_public_id=request_public_id,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            self._log_failure("invalid_response", request_public_id, started_at)
            raise LLMProviderInvalidResponseError(
                "Groq returned an invalid response"
            ) from exc
        if result.finish_reason in {"length", "max_tokens"}:
            self._log_failure("truncated", request_public_id, started_at)
            raise LLMProviderInvalidResponseError(
                "Groq returned a truncated response"
            )

        logger.info(
            (
                "llm request completed provider=%s model=%s "
                "request_public_id=%s latency_ms=%s input_tokens=%s "
                "output_tokens=%s total_tokens=%s finish_reason=%s"
            ),
            PROVIDER_NAME,
            result.model,
            request_public_id,
            _elapsed_ms(started_at),
            result.input_tokens,
            result.output_tokens,
            result.total_tokens,
            result.finish_reason,
            extra={"event_code": "llm.request.completed"},
        )
        return result

    def _prompt_fits(self, package: PromptPackage) -> bool:
        # A UTF-8 byte count is a conservative upper bound for tokenizer pieces.
        # Reject instead of truncating system/safety or business context silently.
        prompt_bytes = len(package.system_prompt.encode("utf-8")) + len(
            package.user_prompt.encode("utf-8")
        )
        available = (
            self.context_length
            - self.max_output_tokens
            - PROMPT_OVERHEAD_BUDGET
        )
        return prompt_bytes <= available

    def _mapped_status_error(
        self,
        exc: httpx.HTTPStatusError,
        *,
        request_public_id: str,
        started_at: float,
    ) -> LLMProviderError:
        status = exc.response.status_code
        if status in {401, 403}:
            self._log_failure("authentication", request_public_id, started_at)
            return LLMProviderAuthenticationError(
                "Groq authentication failed"
            )
        if status == 429:
            self._log_failure("rate_limit", request_public_id, started_at)
            return LLMProviderRateLimitError("Groq rate limit was reached")
        if status == 404:
            self._log_failure("model_not_found", request_public_id, started_at)
            return LLMProviderConfigurationError(
                "The configured Groq model is not available"
            )
        if status >= 500:
            self._log_failure("unavailable", request_public_id, started_at)
            return LLMProviderUnavailableError(
                "Groq is temporarily unavailable"
            )
        self._log_failure("invalid_request", request_public_id, started_at)
        return LLMProviderRequestError("Groq rejected the request")

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
    payload: Any,
    *,
    headers: Mapping[str, str],
    configured_model: str,
    request_public_id: str,
) -> LLMResponse:
    if not isinstance(payload, Mapping):
        raise ValueError("provider response must be an object")
    choices = payload.get("choices")
    if (
        not isinstance(choices, list)
        or len(choices) != 1
        or not isinstance(choices[0], Mapping)
    ):
        raise ValueError("provider response choices are invalid")
    choice = choices[0]
    message = choice.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("provider response message is invalid")
    usage = payload.get("usage")
    if usage is not None and not isinstance(usage, Mapping):
        raise ValueError("provider response usage is invalid")
    usage_mapping: Mapping[str, Any] = usage or {}
    provider_request_id = _optional_scalar_text(payload.get("id")) or (
        _optional_scalar_text(headers.get("x-request-id"))
    )
    return LLMResponse(
        text=message.get("content"),
        provider=PROVIDER_NAME,
        model=(
            _optional_scalar_text(payload.get("model")) or configured_model
        ),
        finish_reason=_optional_scalar_text(choice.get("finish_reason")),
        input_tokens=_optional_token(usage_mapping, "prompt_tokens"),
        output_tokens=_optional_token(usage_mapping, "completion_tokens"),
        total_tokens=_optional_token(usage_mapping, "total_tokens"),
        request_public_id=request_public_id,
        provider_request_id=provider_request_id,
        metadata={"status": "completed"},
    )


def _optional_token(payload: Mapping[str, Any], name: str) -> int | None:
    value = payload.get(name)
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


def _configured_api_key(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Groq credential configuration is invalid"
        )
    normalized = value.strip()
    if not normalized or "\n" in normalized or "\r" in normalized:
        raise LLMProviderConfigurationError(
            "Groq credentials are not configured"
        )
    return normalized


def _configured_base_url(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Groq base URL configuration is invalid"
        )
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise LLMProviderConfigurationError(
            "Groq base URL configuration is invalid"
        )
    return normalized


def _configured_model(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Groq model configuration is invalid"
        )
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > 100
        or "\n" in normalized
        or "\r" in normalized
    ):
        raise LLMProviderConfigurationError(
            "Groq model configuration is invalid"
        )
    return normalized


def _configured_timeout(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LLMProviderConfigurationError(
            "Groq timeout configuration is invalid"
        )
    normalized = float(value)
    if not 1.0 <= normalized <= 300.0:
        raise LLMProviderConfigurationError(
            "Groq timeout configuration is invalid"
        )
    return normalized


def _configured_context_length(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LLMProviderConfigurationError(
            "Groq context configuration is invalid"
        )
    if not 512 <= value <= 262144:
        raise LLMProviderConfigurationError(
            "Groq context configuration is invalid"
        )
    return value


def _configured_max_output_tokens(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LLMProviderConfigurationError(
            "Groq output token configuration is invalid"
        )
    if not 1 <= value <= 4096:
        raise LLMProviderConfigurationError(
            "Groq output token configuration is invalid"
        )
    return value


def _configured_reasoning_effort(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Groq reasoning configuration is invalid"
        )
    normalized = value.strip().casefold()
    if normalized not in {"none", "default", "low", "medium", "high"}:
        raise LLMProviderConfigurationError(
            "Groq reasoning configuration is invalid"
        )
    return normalized


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((monotonic() - started_at) * 1000))
