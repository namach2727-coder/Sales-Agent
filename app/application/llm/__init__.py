"""Provider-neutral LLM application boundary."""

from app.application.llm.contracts import LLMProvider, LLMResponse, SafeScalar
from app.application.llm.exceptions import (
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderRequestError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)

__all__ = [
    "LLMProvider",
    "LLMProviderAuthenticationError",
    "LLMProviderConfigurationError",
    "LLMProviderError",
    "LLMProviderInvalidResponseError",
    "LLMProviderRateLimitError",
    "LLMProviderRequestError",
    "LLMProviderTimeoutError",
    "LLMProviderUnavailableError",
    "LLMResponse",
    "SafeScalar",
]
