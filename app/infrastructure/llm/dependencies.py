"""Explicit construction for the configured LLM provider."""

from app.application.llm import LLMProvider, LLMProviderConfigurationError
from app.config import Settings
from app.infrastructure.llm.ollama_adapter import OllamaClient, OllamaProvider
from app.infrastructure.llm.openai_adapter import OpenAIClient, OpenAIProvider


def build_llm_provider(
    settings: Settings,
    *,
    client: OpenAIClient | OllamaClient | None = None,
) -> LLMProvider:
    """Build without global clients or import-time network activity."""

    if settings.llm_provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
            client=client,
        )
    if settings.llm_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            context_length=settings.ollama_context_length,
            max_output_tokens=settings.ollama_max_output_tokens,
            thinking_enabled=settings.ollama_thinking_enabled,
            client=client,
        )
    raise LLMProviderConfigurationError(
        "Unsupported LLM provider configuration"
    )
