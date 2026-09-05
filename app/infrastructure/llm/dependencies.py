"""Explicit construction for the configured LLM provider."""

from app.application.llm import LLMProvider, LLMProviderConfigurationError
from app.config import Settings
from app.infrastructure.llm.groq_adapter import GroqClient, GroqProvider
from app.infrastructure.llm.ollama_adapter import OllamaClient, OllamaProvider
from app.infrastructure.llm.openai_adapter import OpenAIClient, OpenAIProvider


def build_llm_provider(
    settings: Settings,
    *,
    client: OpenAIClient | OllamaClient | GroqClient | None = None,
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
            api_key=settings.ollama_api_key.get_secret_value(),
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            context_length=settings.ollama_context_length,
            max_output_tokens=settings.ollama_max_output_tokens,
            thinking_enabled=settings.ollama_thinking_enabled,
            client=client,
        )
    if settings.llm_provider == "groq":
        return GroqProvider(
            api_key=settings.groq_api_key.get_secret_value(),
            base_url=settings.groq_base_url,
            model=settings.groq_model,
            timeout_seconds=settings.groq_timeout_seconds,
            context_length=settings.groq_context_length,
            max_output_tokens=settings.groq_max_output_tokens,
            reasoning_effort=settings.groq_reasoning_effort,
            client=client,
        )
    raise LLMProviderConfigurationError(
        "Unsupported LLM provider configuration"
    )
