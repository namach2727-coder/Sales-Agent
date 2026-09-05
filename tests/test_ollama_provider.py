from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import httpx
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
API_KEY = "ollama-example-key-not-real"


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


def _payload(
    *,
    text: str = "safe local answer",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    done: bool | None = True,
    done_reason: str | None = "stop",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"message": {"content": text}}
    if input_tokens is not None:
        payload["prompt_eval_count"] = input_tokens
    if output_tokens is not None:
        payload["eval_count"] = output_tokens
    if done is not None:
        payload["done"] = done
    if done_reason is not None:
        payload["done_reason"] = done_reason
    return payload


class FakeResponse:
    def __init__(
        self,
        payload: Any = None,
        *,
        status_code: int = 200,
        request_id: str | None = "req_ollama_test",
    ) -> None:
        self.payload = payload if payload is not None else _payload()
        self.status_code = status_code
        self.headers = (
            {"x-request-id": request_id} if request_id is not None else {}
        )

    def json(self) -> Any:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return
        request = httpx.Request("POST", f"{BASE_URL}/api/chat")
        response = httpx.Response(self.status_code, request=request)
        raise httpx.HTTPStatusError(
            "local server detail must remain hidden",
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


def _provider(client: FakeClient | None = None) -> OllamaProvider:
    return OllamaProvider(
        base_url=BASE_URL,
        model=MODEL,
        timeout_seconds=12,
        client=client or FakeClient(),
    )


def test_ollama_provider_satisfies_existing_protocol() -> None:
    assert isinstance(_provider(), LLMProvider)


def test_prompts_map_separately_to_native_chat_without_mutation() -> None:
    client = FakeClient()
    package = _package()
    before = (package.system_prompt, package.user_prompt, package.metadata)

    _provider(client).generate(package)

    assert client.calls == [
        (
            "/api/chat",
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT},
                ],
                "stream": False,
                "think": False,
                "options": {"num_ctx": 4096, "num_predict": 128},
            },
        )
    ]
    assert (package.system_prompt, package.user_prompt, package.metadata) == before


def test_success_maps_to_immutable_response_with_usage() -> None:
    raw = _payload(input_tokens=13, output_tokens=5)

    result = _provider(FakeClient(FakeResponse(raw))).generate(_package())

    assert result.text == "safe local answer"
    assert result.provider == "ollama"
    assert result.model == MODEL
    assert result.finish_reason == "stop"
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
        FakeClient(
            FakeResponse(
                _payload(done=None, done_reason=None),
                request_id=None,
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
        _provider(FakeClient(FakeResponse(_payload(text="  \n")))).generate(
            _package()
        )
    assert isinstance(blank.value.__cause__, ValueError)

    malformed = {"message": {"content": object()}}
    with pytest.raises(LLMProviderInvalidResponseError) as invalid:
        _provider(FakeClient(FakeResponse(malformed))).generate(_package())
    assert isinstance(invalid.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("client", "application_error", "cause_type"),
    [
        (
            FakeClient(
                error=httpx.ConnectError(
                    "local server detail must remain hidden",
                    request=httpx.Request(
                        "POST", f"{BASE_URL}/api/chat"
                    ),
                )
            ),
            LLMProviderUnavailableError,
            httpx.ConnectError,
        ),
        (
            FakeClient(
                error=httpx.ReadTimeout(
                    "local server detail must remain hidden",
                    request=httpx.Request(
                        "POST", f"{BASE_URL}/api/chat"
                    ),
                )
            ),
            LLMProviderTimeoutError,
            httpx.ReadTimeout,
        ),
        (
            FakeClient(FakeResponse(status_code=404)),
            LLMProviderConfigurationError,
            httpx.HTTPStatusError,
        ),
        (
            FakeClient(FakeResponse(status_code=400)),
            LLMProviderRequestError,
            httpx.HTTPStatusError,
        ),
    ],
)
def test_known_ollama_errors_map_to_safe_application_errors(
    client: FakeClient,
    application_error: type[LLMProviderError],
    cause_type: type[Exception],
) -> None:
    with pytest.raises(application_error) as raised:
        _provider(client).generate(_package())

    assert isinstance(raised.value.__cause__, cause_type)
    assert "local server detail" not in str(raised.value)


def test_invalid_response_and_unknown_error_map_safely() -> None:
    with pytest.raises(LLMProviderInvalidResponseError) as invalid_raised:
        _provider(FakeClient(FakeResponse({"private": "payload"}))).generate(
            _package()
        )
    assert isinstance(invalid_raised.value.__cause__, ValueError)

    unknown = RuntimeError("raw local provider detail")
    with pytest.raises(LLMProviderError) as unknown_raised:
        _provider(FakeClient(error=unknown)).generate(_package())
    assert type(unknown_raised.value) is LLMProviderError
    assert str(unknown_raised.value) == "Ollama request failed"
    assert unknown_raised.value.__cause__ is unknown


def test_client_uses_native_base_url_and_configured_timeout(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module.httpx, "Client", client_factory)

    provider = OllamaProvider(
        base_url=f"{BASE_URL}/",
        model=MODEL,
        timeout_seconds=19,
    )

    assert provider.base_url == BASE_URL
    assert provider.native_base_url == "http://localhost:11434"
    assert provider.timeout_seconds == 19.0
    assert captured["base_url"] == "http://localhost:11434"
    assert captured["follow_redirects"] is False
    assert "headers" not in captured
    timeout = captured["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 19.0
    assert timeout.read == 19.0
    assert not hasattr(provider, "api_key")


def test_cloud_client_uses_bearer_auth_and_native_chat_path(
    monkeypatch,
    caplog,
) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module.httpx, "Client", client_factory)
    caplog.set_level("INFO", logger="sales_assistant.llm.ollama")
    provider = OllamaProvider(
        api_key=API_KEY,
        base_url="https://ollama.com",
        model=MODEL,
    )

    provider.generate(_package())

    assert provider.native_base_url == "https://ollama.com"
    assert captured["base_url"] == "https://ollama.com"
    assert captured["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert fake_client.calls[0][0] == "/api/chat"
    assert API_KEY not in repr(provider)
    assert API_KEY not in "\n".join(
        record.getMessage() for record in caplog.records
    )


def test_ollama_api_key_is_secret_and_passed_by_provider_selector(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}
    fake_client = FakeClient()

    def client_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(adapter_module.httpx, "Client", client_factory)
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        ollama_api_key=API_KEY,
        ollama_base_url="https://ollama.com",
        ollama_model=MODEL,
    )

    provider = build_llm_provider(settings)

    assert isinstance(provider, OllamaProvider)
    assert captured["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert API_KEY not in repr(settings)


def test_ollama_api_key_uses_standard_environment_mapping(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_API_KEY", API_KEY)

    settings = Settings(_env_file=None)

    assert settings.ollama_api_key.get_secret_value() == API_KEY
    assert API_KEY not in repr(settings)


def test_cloud_transport_failure_does_not_expose_api_key(
    monkeypatch,
    caplog,
) -> None:
    request = httpx.Request("POST", "https://ollama.com/api/chat")
    fake_client = FakeClient(
        error=httpx.ConnectError(
            f"transport rejected {API_KEY}",
            request=request,
        )
    )
    monkeypatch.setattr(
        adapter_module.httpx,
        "Client",
        lambda **_kwargs: fake_client,
    )
    caplog.set_level("INFO", logger="sales_assistant.llm.ollama")
    provider = OllamaProvider(
        api_key=API_KEY,
        base_url="https://ollama.com",
        model=MODEL,
    )

    with pytest.raises(LLMProviderUnavailableError) as raised:
        provider.generate(_package())

    assert API_KEY not in str(raised.value)
    assert API_KEY not in "\n".join(
        record.getMessage() for record in caplog.records
    )


@pytest.mark.parametrize("api_key", [None, object(), "line-one\nline-two"])
def test_invalid_ollama_api_key_configuration_fails_safely(api_key: object) -> None:
    with pytest.raises(
        LLMProviderConfigurationError,
        match="credential configuration is invalid",
    ) as raised:
        OllamaProvider(
            api_key=api_key,  # type: ignore[arg-type]
            base_url=BASE_URL,
            model=MODEL,
            client=FakeClient(),
        )

    assert API_KEY not in str(raised.value)


def test_provider_selection_is_normalized_and_explicit() -> None:
    ollama_settings = Settings(
        _env_file=None,
        llm_provider=" OLLAMA ",
        openai_api_key="",
        ollama_model=MODEL,
        ollama_context_length=2048,
        ollama_max_output_tokens=24,
        ollama_thinking_enabled=True,
    )
    ollama = build_llm_provider(ollama_settings, client=FakeClient())
    assert isinstance(ollama, OllamaProvider)
    assert ollama.context_length == 2048
    assert ollama.max_output_tokens == 24
    assert ollama.thinking_enabled is True

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


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"context_length": 0}, "context configuration"),
        ({"context_length": True}, "context configuration"),
        ({"max_output_tokens": 0}, "output token"),
        ({"max_output_tokens": True}, "output token"),
        ({"thinking_enabled": "false"}, "thinking configuration"),
    ],
)
def test_invalid_generation_controls_fail_closed(
    kwargs: dict[str, Any], message: str
) -> None:
    with pytest.raises(LLMProviderConfigurationError, match=message):
        OllamaProvider(
            base_url=BASE_URL,
            model=MODEL,
            client=FakeClient(),
            **kwargs,
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

    _provider(FakeClient(FakeResponse(_payload(text=raw_text)))).generate(
        _package()
    )

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

