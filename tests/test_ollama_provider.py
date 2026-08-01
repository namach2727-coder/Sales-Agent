from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    BadRequestError,
    NotFoundError,
)
from pydantic import ValidationError
import pytest

from app.application.llm import (
    LLMProvider,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRequestError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from app.application.prompts import PromptMetadata, PromptPackage
from app.config import Settings
from app.infrastructure.llm import (
    OllamaProvider,
    OpenAIProvider,
    build_llm_provider,
)
import app.infrastructure.llm.ollama_adapter as adapter_module


BASE_URL = "http://localhost:11434/v1"
MODEL = "local-test-model"
SYSTEM_PROMPT = "OLLAMA-SYSTEM-CONTEXT-DO-NOT-LOG"
USER_PROMPT = "OLLAMA-CUSTOMER-MESSAGE-DO-NOT-LOG"


def _package() -> PromptPackage:
    return PromptPackage(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        metadata=PromptMetadata(
            conversation_public_id=(
                "00000000-0000-4000-8000-000000000002"
            ),
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


def _response(
    *,
    text: str = "safe local answer",
    model: str | None = "provider-reported-model",
    usage: Any = None,
    request_id: str | None = "req_ollama_test",
    status: str | None = "completed",
) -> SimpleNamespace:
    return SimpleNamespace(
        output_text=text,
        model=model,
        usage=usage,
        _request_id=request_id,
        status=status,
        finish_reason=None,
        incomplete_details=None,
    )


class FakeResponses:
    def __init__(
        self,
        response: Any = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response if response is not None else _response()
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, responses: FakeResponses | None = None) -> None:
        self.responses = responses or FakeResponses()


def _provider(responses: FakeResponses | None = None) -> OllamaProvider:
    return OllamaProvider(
        base_url=BASE_URL,
        model=MODEL,
        timeout_seconds=12,
        client=FakeClient(responses),
    )


def _status_error(error_type: type[Exception], status: int) -> Exception:
    request = httpx.Request("POST", f"{BASE_URL}/responses")
    response = httpx.Response(status, request=request)
    return error_type(
        "local server detail must remain hidden",
        response=response,
        body=None,
    )


def test_ollama_provider_satisfies_existing_protocol() -> None:
    assert isinstance(_provider(), LLMProvider)


def test_prompts_map_separately_to_responses_api_without_mutation() -> None:
    responses = FakeResponses()
    package = _package()
    before = (package.system_prompt, package.user_prompt, package.metadata)

    _provider(responses).generate(package)

    assert responses.calls == [
        {
            "model": MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": USER_PROMPT,
            "store": False,
        }
    ]
    assert responses.calls[0]["instructions"] != responses.calls[0]["input"]
    assert (package.system_prompt, package.user_prompt, package.metadata) == before


def test_success_maps_to_immutable_response_with_usage() -> None:
    raw = _response(
        usage=SimpleNamespace(
            input_tokens=13,
            output_tokens=5,
            total_tokens=18,
        )
    )

    result = _provider(FakeResponses(raw)).generate(_package())

    assert result.text == "safe local answer"
    assert result.provider == "ollama"
    assert result.model == MODEL
    assert result.finish_reason == "completed"
    assert result.input_tokens == 13
    assert result.output_tokens == 5
    assert result.total_tokens == 18
    assert result.provider_request_id == "req_ollama_test"
    assert result.request_public_id is not None
    assert result.metadata == {"status": "completed"}
    with pytest.raises(FrozenInstanceError):
        result.text = "changed"


def test_missing_usage_and_optional_response_fields_are_supported() -> None:
    result = _provider(
        FakeResponses(
            _response(
                model=None,
                usage=None,
                request_id=None,
                status=None,
            )
        )
    ).generate(_package())

    assert result.model == MODEL
    assert result.input_tokens is None
    assert result.output_tokens is None
    assert result.total_tokens is None
    assert result.provider_request_id is None
    assert result.finish_reason is None
    assert result.metadata == {}


def test_blank_and_malformed_responses_are_rejected_safely() -> None:
    with pytest.raises(LLMProviderInvalidResponseError) as blank:
        _provider(FakeResponses(_response(text="  \n"))).generate(_package())
    assert isinstance(blank.value.__cause__, ValueError)

    malformed = SimpleNamespace(output_text=object(), usage=None)
    with pytest.raises(LLMProviderInvalidResponseError) as invalid:
        _provider(FakeResponses(malformed)).generate(_package())
    assert isinstance(invalid.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("provider_error", "application_error"),
    [
        (
            APIConnectionError(
                request=httpx.Request("POST", f"{BASE_URL}/responses")
            ),
            LLMProviderUnavailableError,
        ),
        (
            APITimeoutError(
                request=httpx.Request("POST", f"{BASE_URL}/responses")
            ),
            LLMProviderTimeoutError,
        ),
        (
            _status_error(NotFoundError, 404),
            LLMProviderConfigurationError,
        ),
        (
            _status_error(BadRequestError, 400),
            LLMProviderRequestError,
        ),
    ],
)
def test_known_ollama_errors_map_to_safe_application_errors(
    provider_error: Exception,
    application_error: type[LLMProviderError],
) -> None:
    with pytest.raises(application_error) as raised:
        _provider(FakeResponses(error=provider_error)).generate(_package())

    assert raised.value.__cause__ is provider_error
    assert "local server detail" not in str(raised.value)


def test_sdk_invalid_response_and_unknown_error_map_safely() -> None:
    request = httpx.Request("POST", f"{BASE_URL}/responses")
    invalid = APIResponseValidationError(
        httpx.Response(200, request=request),
        {"private": "provider payload"},
    )
    with pytest.raises(LLMProviderInvalidResponseError) as invalid_raised:
        _provider(FakeResponses(error=invalid)).generate(_package())
    assert invalid_raised.value.__cause__ is invalid

    unknown = RuntimeError("raw local provider detail")
    with pytest.raises(LLMProviderError) as unknown_raised:
        _provider(FakeResponses(error=unknown)).generate(_package())
    assert type(unknown_raised.value) is LLMProviderError
    assert str(unknown_raised.value) == "Ollama request failed"
    assert unknown_raised.value.__cause__ is unknown


def test_client_uses_configured_base_url_and_non_secret_placeholder(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module, "OpenAI", client_factory)

    provider = OllamaProvider(
        base_url=f"{BASE_URL}/",
        model=MODEL,
        timeout_seconds=19,
    )

    assert provider.base_url == BASE_URL
    assert provider.timeout_seconds == 19.0
    assert captured == {
        "base_url": BASE_URL,
        "api_key": "ollama",
        "timeout": 19.0,
        "max_retries": 0,
    }
    assert not hasattr(provider, "api_key")


def test_provider_selection_is_normalized_and_explicit() -> None:
    ollama_settings = Settings(
        _env_file=None,
        llm_provider=" OLLAMA ",
        openai_api_key="",
        ollama_model=MODEL,
    )
    ollama = build_llm_provider(ollama_settings, client=FakeClient())
    assert isinstance(ollama, OllamaProvider)

    openai_settings = Settings(
        _env_file=None,
        llm_provider="OPENAI",
        openai_api_key="not-a-real-key",
    )
    openai = build_llm_provider(openai_settings, client=FakeClient())
    assert isinstance(openai, OpenAIProvider)


def test_unsupported_provider_and_missing_ollama_model_fail_clearly() -> None:
    with pytest.raises(ValidationError, match="llm_provider"):
        Settings(_env_file=None, llm_provider="unsupported")

    with pytest.raises(ValidationError, match="OLLAMA_MODEL is required"):
        Settings(
            _env_file=None,
            llm_provider="ollama",
            ollama_model="   ",
        )


def test_ollama_selection_does_not_require_openai_api_key() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        openai_api_key="",
        ollama_model=MODEL,
    )

    provider = build_llm_provider(settings, client=FakeClient())

    assert isinstance(provider, OllamaProvider)


def test_openai_selection_still_fails_closed_without_api_key() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        openai_api_key="",
    )

    with pytest.raises(
        LLMProviderConfigurationError,
        match="credentials are not configured",
    ):
        build_llm_provider(settings, client=FakeClient())


def test_safe_logs_exclude_prompts_and_provider_payload(caplog) -> None:
    caplog.set_level("INFO", logger="sales_assistant.llm.ollama")
    raw_text = "OLLAMA-RAW-RESPONSE-DO-NOT-LOG"

    _provider(FakeResponses(_response(text=raw_text))).generate(_package())

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "llm request started" in log_text
    assert "llm request completed" in log_text
    for prohibited in (
        SYSTEM_PROMPT,
        USER_PROMPT,
        raw_text,
        "Authorization",
    ):
        assert prohibited not in log_text


def test_ollama_modules_have_no_database_or_instagram_outbound_access() -> None:
    paths = (
        Path(adapter_module.__file__),
        Path(adapter_module.__file__).with_name("dependencies.py"),
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths
    ).casefold()

    for prohibited in (
        "sqlalchemy",
        "session",
        "repository",
        ".commit(",
        ".rollback(",
        "instagram",
        "send_message",
    ):
        assert prohibited not in source

