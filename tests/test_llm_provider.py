from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
import pytest

from app.application.llm import (
    LLMProvider,
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMResponse,
)
from app.application.prompts import PromptMetadata, PromptPackage
from app.config import Settings
from app.infrastructure.llm import OpenAIProvider, build_llm_provider
import app.infrastructure.llm.openai_adapter as adapter_module


API_KEY = "sk-test-not-a-real-credential"
MODEL = "gpt-5.6-sol"
SYSTEM_PROMPT = "SYSTEM-CONTEXT-DO-NOT-LOG"
USER_PROMPT = "CUSTOMER-MESSAGE-DO-NOT-LOG"


def _package() -> PromptPackage:
    return PromptPackage(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        metadata=PromptMetadata(
            conversation_public_id=(
                "00000000-0000-4000-8000-000000000001"
            ),
            preferred_language="fa-IR",
            knowledge_confidence=0.9,
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
    text: str = "پاسخ امن",
    model: str | None = MODEL,
    usage: Any = None,
    request_id: str | None = "req_test_123",
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


def _provider(responses: FakeResponses | None = None) -> OpenAIProvider:
    return OpenAIProvider(
        api_key=API_KEY,
        model=MODEL,
        timeout_seconds=12.0,
        max_retries=1,
        client=FakeClient(responses),
    )


def _status_error(error_type: type[Exception], status: int) -> Exception:
    request = httpx.Request(
        "POST", "https://api.openai.com/v1/responses"
    )
    response = httpx.Response(status, request=request)
    return error_type("provider detail must remain hidden", response=response, body=None)


def test_prompt_package_maps_in_fixed_order_and_keeps_prompts_separate() -> None:
    responses = FakeResponses()
    package = _package()

    _provider(responses).generate(package)

    assert len(responses.calls) == 1
    request = responses.calls[0]
    assert list(request) == ["model", "instructions", "input", "store"]
    assert request == {
        "model": MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": USER_PROMPT,
        "store": False,
    }
    assert request["instructions"] != request["input"]


def test_success_is_normalized_to_immutable_provider_neutral_response() -> None:
    raw = _response(
        usage=SimpleNamespace(
            input_tokens=21,
            output_tokens=8,
            total_tokens=29,
        )
    )

    result = _provider(FakeResponses(raw)).generate(_package())

    assert result.text == "پاسخ امن"
    assert result.provider == "openai"
    assert result.model == MODEL
    assert result.finish_reason == "completed"
    assert result.input_tokens == 21
    assert result.output_tokens == 8
    assert result.total_tokens == 29
    assert result.provider_request_id == "req_test_123"
    assert result.request_public_id is not None
    assert result.metadata == {"status": "completed"}
    assert not any(
        item.name in {"raw", "raw_response", "sdk_response"}
        for item in fields(LLMResponse)
    )
    with pytest.raises(FrozenInstanceError):
        result.text = "changed"
    with pytest.raises(TypeError):
        result.metadata["unsafe"] = "changed"


def test_blank_provider_response_is_rejected() -> None:
    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        _provider(FakeResponses(_response(text="  \n"))).generate(_package())

    assert isinstance(raised.value.__cause__, ValueError)


def test_missing_api_key_fails_before_client_or_network_construction() -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key="",
        openai_model=MODEL,
    )

    with pytest.raises(
        LLMProviderConfigurationError,
        match="credentials are not configured",
    ):
        build_llm_provider(settings, client=FakeClient())


def test_settings_support_secret_file_and_explicit_provider_configuration(
    tmp_path: Path,
) -> None:
    secret_file = tmp_path / "openai-api-key"
    secret_file.write_text(API_KEY, encoding="utf-8")
    settings = Settings(
        _env_file=None,
        openai_api_key_file=str(secret_file),
        openai_model=MODEL,
        openai_timeout_seconds=17,
        openai_max_retries=0,
    )

    provider = build_llm_provider(settings, client=FakeClient())

    assert isinstance(provider, OpenAIProvider)
    assert provider.model == MODEL
    assert provider.timeout_seconds == 17.0
    assert provider.max_retries == 0
    assert API_KEY not in repr(settings.openai_api_key)


@pytest.mark.parametrize(
    ("provider_error", "application_error"),
    [
        (
            _status_error(AuthenticationError, 401),
            LLMProviderAuthenticationError,
        ),
        (
            APITimeoutError(
                request=httpx.Request(
                    "POST", "https://api.openai.com/v1/responses"
                )
            ),
            LLMProviderTimeoutError,
        ),
        (
            _status_error(RateLimitError, 429),
            LLMProviderRateLimitError,
        ),
        (
            APIConnectionError(
                request=httpx.Request(
                    "POST", "https://api.openai.com/v1/responses"
                )
            ),
            LLMProviderUnavailableError,
        ),
        (
            _status_error(InternalServerError, 500),
            LLMProviderUnavailableError,
        ),
    ],
)
def test_known_provider_errors_map_to_safe_application_errors(
    provider_error: Exception,
    application_error: type[LLMProviderError],
) -> None:
    with pytest.raises(application_error) as raised:
        _provider(FakeResponses(error=provider_error)).generate(_package())

    assert raised.value.__cause__ is provider_error
    assert "provider detail" not in str(raised.value)


def test_invalid_sdk_response_and_unknown_error_map_safely() -> None:
    request = httpx.Request(
        "POST", "https://api.openai.com/v1/responses"
    )
    invalid = APIResponseValidationError(
        httpx.Response(200, request=request),
        {"secret": "not exposed"},
    )
    with pytest.raises(LLMProviderInvalidResponseError) as invalid_raised:
        _provider(FakeResponses(error=invalid)).generate(_package())
    assert invalid_raised.value.__cause__ is invalid

    unknown = RuntimeError("raw provider secret")
    with pytest.raises(LLMProviderError) as unknown_raised:
        _provider(FakeResponses(error=unknown)).generate(_package())
    assert type(unknown_raised.value) is LLMProviderError
    assert str(unknown_raised.value) == "OpenAI request failed"
    assert unknown_raised.value.__cause__ is unknown


def test_missing_usage_request_id_and_response_model_are_supported() -> None:
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


def test_adapter_does_not_mutate_prompt_package() -> None:
    package = _package()
    before = (
        package.system_prompt,
        package.user_prompt,
        package.metadata,
    )

    _provider().generate(package)

    assert (
        package.system_prompt,
        package.user_prompt,
        package.metadata,
    ) == before


def test_application_can_inject_a_fake_provider_without_network() -> None:
    expected = LLMResponse(
        text="fake",
        provider="fake",
        model="fake-model",
    )

    class FakeProvider:
        def generate(self, prompt_package: PromptPackage) -> LLMResponse:
            assert prompt_package is _package_instance
            return expected

    _package_instance = _package()
    provider: LLMProvider = FakeProvider()

    assert isinstance(provider, LLMProvider)
    assert provider.generate(_package_instance) is expected


def test_sdk_client_configuration_is_explicit_and_bounded(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module, "OpenAI", client_factory)

    provider = OpenAIProvider(
        api_key=API_KEY,
        model=MODEL,
        timeout_seconds=18,
        max_retries=1,
    )

    assert provider.max_retries == 1
    assert provider.timeout_seconds == 18.0
    assert captured == {
        "api_key": API_KEY,
        "timeout": 18.0,
        "max_retries": 1,
    }


def test_safe_logs_exclude_credentials_prompts_and_provider_payload(
    caplog,
) -> None:
    caplog.set_level("INFO", logger="sales_assistant.llm.openai")
    raw_text = "RAW-RESPONSE-MUST-NOT-BE-LOGGED"

    _provider(FakeResponses(_response(text=raw_text))).generate(_package())

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "llm request started" in log_text
    assert "llm request completed" in log_text
    for prohibited in (API_KEY, SYSTEM_PROMPT, USER_PROMPT, raw_text):
        assert prohibited not in log_text


def test_llm_modules_have_no_database_or_instagram_outbound_dependencies() -> None:
    adapter_module_path = Path(adapter_module.__file__)
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            adapter_module_path,
            adapter_module_path.parents[2]
            / "application"
            / "llm"
            / "contracts.py",
        )
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
