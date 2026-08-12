"""Local Ollama adapter for the provider-neutral application LLM contract."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from time import monotonic
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import httpx

from app.application.llm import (
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRequestError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMResponse,
)
from app.application.prompts import PromptPackage


logger = logging.getLogger("sales_assistant.llm.ollama")
PROVIDER_NAME = "ollama"
DEFAULT_MAX_OUTPUT_TOKENS = 128


class OllamaHttpResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]

    def json(self) -> Any: ...

    def raise_for_status(self) -> None: ...


class OllamaClient(Protocol):
    def post(
        self,
        url: str,
        *,
        json: Mapping[str, Any],
    ) -> OllamaHttpResponse: ...


class OllamaProvider:
    """Map immutable prompt packages to one bounded native Ollama call."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
        context_length: int = 4096,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        thinking_enabled: bool = False,
        client: OllamaClient | None = None,
    ) -> None:
        self.base_url = _configured_base_url(base_url)
        self.native_base_url = _native_base_url(self.base_url)
        self.model = _configured_model(model)
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise LLMProviderConfigurationError(
                "Ollama timeout configuration is invalid"
            )
        if not 1.0 <= float(timeout_seconds) <= 300.0:
            raise LLMProviderConfigurationError(
                "Ollama timeout configuration is invalid"
            )
        if (
            isinstance(context_length, bool)
            or not isinstance(context_length, int)
            or not 512 <= context_length <= 262144
        ):
            raise LLMProviderConfigurationError(
                "Ollama context configuration is invalid"
            )
        if (
            isinstance(max_output_tokens, bool)
            or not isinstance(max_output_tokens, int)
            or not 1 <= max_output_tokens <= 4096
        ):
            raise LLMProviderConfigurationError(
                "Ollama output token configuration is invalid"
            )
        if not isinstance(thinking_enabled, bool):
            raise LLMProviderConfigurationError(
                "Ollama thinking configuration is invalid"
            )
        self.timeout_seconds = float(timeout_seconds)
        self.context_length = context_length
        self.max_output_tokens = max_output_tokens
        self.thinking_enabled = thinking_enabled
        self._client: OllamaClient = (
            client
            if client is not None
            else httpx.Client(
                base_url=self.native_base_url,
                timeout=httpx.Timeout(self.timeout_seconds),
                follow_redirects=False,
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
            response = self._client.post(
                "/api/chat",
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
                    "stream": False,
                    "think": self.thinking_enabled,
                    "options": {
                        "num_ctx": self.context_length,
                        "num_predict": self.max_output_tokens,
                    },
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            self._log_failure("timeout", request_public_id, started_at)
            raise LLMProviderTimeoutError("Ollama request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise self._mapped_status_error(
                exc,
                request_public_id=request_public_id,
                started_at=started_at,
            ) from exc
        except httpx.RequestError as exc:
            self._log_failure("unavailable", request_public_id, started_at)
            raise LLMProviderUnavailableError(
                "Ollama is temporarily unavailable"
            ) from exc
        except Exception as exc:
            self._log_failure("provider_error", request_public_id, started_at)
            raise LLMProviderError("Ollama request failed") from exc

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
                "Ollama returned an invalid response"
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

    def _mapped_status_error(
        self,
        exc: httpx.HTTPStatusError,
        *,
        request_public_id: str,
        started_at: float,
    ) -> LLMProviderError:
        status = exc.response.status_code
        if status == 404:
            self._log_failure("model_not_found", request_public_id, started_at)
            return LLMProviderConfigurationError(
                "The configured Ollama model is not available"
            )
        if status in {401, 403}:
            self._log_failure("configuration", request_public_id, started_at)
            return LLMProviderConfigurationError(
                "Ollama endpoint configuration was rejected"
            )
        if status == 429 or status >= 500:
            self._log_failure("unavailable", request_public_id, started_at)
            return LLMProviderUnavailableError(
                "Ollama is temporarily unavailable"
            )
        self._log_failure("invalid_request", request_public_id, started_at)
        return LLMProviderRequestError("Ollama rejected the request")

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
    message = payload.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("provider response message is invalid")

    input_tokens = _optional_token(payload, "prompt_eval_count")
    output_tokens = _optional_token(payload, "eval_count")
    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )
    done = payload.get("done")
    if done is not None and not isinstance(done, bool):
        raise ValueError("provider done field is invalid")
    done_reason = _optional_scalar_text(payload.get("done_reason"))
    request_id = _optional_scalar_text(headers.get("x-request-id"))
    metadata = {"status": "completed"} if done is True else {}
    return LLMResponse(
        text=message.get("content"),
        provider=PROVIDER_NAME,
        model=configured_model,
        finish_reason=done_reason or ("completed" if done is True else None),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        request_public_id=request_public_id,
        provider_request_id=request_id,
        metadata=metadata,
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


def _configured_model(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Ollama model configuration is invalid"
        )
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > 100
        or "\n" in normalized
        or "\r" in normalized
    ):
        raise LLMProviderConfigurationError(
            "Ollama model configuration is invalid"
        )
    return normalized


def _configured_base_url(value: object) -> str:
    if not isinstance(value, str):
        raise LLMProviderConfigurationError(
            "Ollama base URL configuration is invalid"
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
            "Ollama base URL configuration is invalid"
        )
    return normalized


def _native_base_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    path = parsed.path.rstrip("/")
    if path.endswith("/v1"):
        path = path[:-3]
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", "")).rstrip("/")


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((monotonic() - started_at) * 1000))
