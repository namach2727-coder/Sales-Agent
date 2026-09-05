from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import httpx
from pydantic import ValidationError
import pytest

from app.application.llm import (
    LLMProvider,
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderRequestError,
    LLMProviderUnavailableError,
)
from app.application.prompts import PromptMetadata, PromptPackage
from app.config import Settings
from app.infrastructure.llm import GroqProvider, build_llm_provider
import app.infrastructure.llm.groq_adapter as adapter_module


BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "qwen/qwen3.6-27b"
API_KEY = "groq-example-key-not-real"
SYSTEM_PROMPT = "GROQ-SYSTEM-CONTEXT-DO-NOT-LOG"
USER_PROMPT = "GROQ-CUSTOMER-MESSAGE-DO-NOT-LOG"
RAW_RESPONSE = "GROQ-RAW-RESPONSE-DO-NOT-LOG"


def _package(*, user_prompt: str = USER_PROMPT) -> PromptPackage:
    return PromptPackage(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        metadata=PromptMetadata(
            conversation_public_id="00000000-0000-4000-8000-000000000003",
            preferred_language="fa-IR",
            knowledge_confidence=0.8,
            business_profile_public_id=None,
            product_public_ids=(),
            faq_public_ids=(),
            business_rule_public_ids=(),
            knowledge_snippet_public_ids=(),
            recent_message_public_ids=(),
        ),
    )


def _payload(
    *,
    text: str = "safe Groq answer",
    finish_reason: str = "stop",
) -> dict[str, Any]:
    return {
        "id": "groq-provider-request",
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 21,
            "completion_tokens": 8,
            "total_tokens": 29,
        },
    }


class FakeResponse:
    def __init__(
        self,
        payload: Any = None,
        *,
        status_code: int = 200,
    ) -> None:
        self.payload = _payload() if payload is None else payload
        self.status_code = status_code
        self.headers = {"x-request-id": "groq-header-request"}

    def json(self) -> Any:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return
        request = httpx.Request("POST", f"{BASE_URL}/chat/completions")
        response = httpx.Response(self.status_code, request=request)
        raise httpx.HTTPStatusError(
            "provider detail must remain hidden",
            request=request,
            response=response,
        )


class FakeClient:
    def __init__(
        self,
        response: FakeResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or FakeResponse()
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, *, json: dict[str, Any]) -> FakeResponse:
        self.calls.append((url, json))
        if self.error is not None:
            raise self.error
        return self.response


def _provider(client: FakeClient | None = None, **kwargs: Any) -> GroqProvider:
    return GroqProvider(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        client=client or FakeClient(),
        **kwargs,
    )


def test_groq_provider_satisfies_contract_and_maps_request() -> None:
    client = FakeClient()
    provider = _provider(client, max_output_tokens=256, reasoning_effort="none")

    result = provider.generate(_package())

    assert isinstance(provider, LLMProvider)
    assert client.calls == [
        (
            "chat/completions",
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT},
                ],
                "max_completion_tokens": 256,
                "reasoning_effort": "none",
                "stream": False,
            },
        )
    ]
    assert result.text == "safe Groq answer"
    assert result.provider == "groq"
    assert result.model == MODEL
    assert result.finish_reason == "stop"
    assert result.input_tokens == 21
    assert result.output_tokens == 8
    assert result.total_tokens == 29
    assert result.provider_request_id == "groq-provider-request"
    assert result.request_public_id is not None
    with pytest.raises(FrozenInstanceError):
        result.text = "changed"


def test_client_uses_bearer_auth_timeout_and_normalized_base(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module.httpx, "Client", client_factory)
    provider = GroqProvider(
        api_key=f"  {API_KEY}  ",
        base_url=f"{BASE_URL}/",
        model=MODEL,
        timeout_seconds=19,
    )

    provider.generate(_package())

    assert provider.base_url == BASE_URL
    assert captured["base_url"] == BASE_URL
    assert captured["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert captured["follow_redirects"] is False
    assert isinstance(captured["timeout"], httpx.Timeout)
    assert fake_client.calls[0][0] == "chat/completions"
    assert API_KEY not in repr(provider)


def test_selector_requires_secret_and_model_only_for_groq(monkeypatch) -> None:
    with pytest.raises(ValidationError, match="GROQ_API_KEY is required"):
        Settings(
            _env_file=None,
            llm_provider="groq",
            groq_api_key="",
            groq_model=MODEL,
        )
    with pytest.raises(ValidationError, match="GROQ_MODEL is required"):
        Settings(
            _env_file=None,
            llm_provider="groq",
            groq_api_key=API_KEY,
            groq_model=" ",
        )

    settings = Settings(
        _env_file=None,
        llm_provider=" GROQ ",
        groq_api_key=API_KEY,
        groq_model=MODEL,
        groq_max_output_tokens=256,
        groq_context_length=4096,
        groq_reasoning_effort="none",
    )
    provider = build_llm_provider(settings, client=FakeClient())

    assert isinstance(provider, GroqProvider)
    assert provider.model == MODEL
    assert provider.max_output_tokens == 256
    assert provider.context_length == 4096
    assert provider.reasoning_effort == "none"
    assert API_KEY not in repr(settings)


def test_uppercase_environment_mapping(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", API_KEY)
    monkeypatch.setenv("GROQ_MODEL", MODEL)

    settings = Settings(_env_file=None)

    assert settings.groq_api_key.get_secret_value() == API_KEY
    assert settings.groq_model == MODEL
    assert API_KEY not in repr(settings)


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, LLMProviderAuthenticationError),
        (403, LLMProviderAuthenticationError),
        (404, LLMProviderConfigurationError),
        (429, LLMProviderRateLimitError),
        (500, LLMProviderUnavailableError),
        (400, LLMProviderRequestError),
    ],
)
def test_http_failures_map_to_existing_safe_errors(
    status: int,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type) as raised:
        _provider(FakeClient(FakeResponse(status_code=status))).generate(_package())

    assert "provider detail" not in str(raised.value)
    assert API_KEY not in str(raised.value)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": object()}}]},
        {"choices": [{"message": {"content": "ok"}}], "usage": []},
    ],
)
def test_malformed_or_empty_response_fails_safely(payload: Any) -> None:
    with pytest.raises(LLMProviderInvalidResponseError):
        _provider(FakeClient(FakeResponse(payload))).generate(_package())


@pytest.mark.parametrize("finish_reason", ["length", "max_tokens"])
def test_truncated_response_is_not_silently_accepted(finish_reason: str) -> None:
    with pytest.raises(
        LLMProviderInvalidResponseError,
        match="truncated",
    ):
        _provider(
            FakeClient(FakeResponse(_payload(finish_reason=finish_reason)))
        ).generate(_package())


def test_oversized_prompt_fails_closed_without_provider_call() -> None:
    client = FakeClient()
    provider = _provider(
        client,
        context_length=512,
        max_output_tokens=128,
    )

    with pytest.raises(LLMProviderRequestError, match="context budget"):
        provider.generate(_package(user_prompt="x" * 400))

    assert client.calls == []


def test_logs_and_errors_exclude_secret_prompt_and_response(caplog) -> None:
    caplog.set_level("INFO", logger="sales_assistant.llm.groq")
    request = httpx.Request("POST", f"{BASE_URL}/chat/completions")
    provider = _provider(
        FakeClient(
            error=httpx.ConnectError(
                f"transport rejected {API_KEY} {USER_PROMPT} {RAW_RESPONSE}",
                request=request,
            )
        )
    )

    with pytest.raises(LLMProviderUnavailableError) as raised:
        provider.generate(_package())

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    for prohibited in (API_KEY, SYSTEM_PROMPT, USER_PROMPT, RAW_RESPONSE):
        assert prohibited not in rendered
        assert prohibited not in str(raised.value)


@pytest.mark.parametrize(
    "base_url",
    [
        "api.groq.com/openai/v1",
        "https://user:password@api.groq.com/openai/v1",
        "https://api.groq.com/openai/v1?secret=value",
    ],
)
def test_invalid_base_urls_fail_closed(base_url: str) -> None:
    with pytest.raises(LLMProviderConfigurationError):
        GroqProvider(
            api_key=API_KEY,
            base_url=base_url,
            model=MODEL,
            client=FakeClient(),
        )
