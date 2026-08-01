"""Safe application-level failures for LLM provider calls."""


class LLMProviderError(Exception):
    code = "llm_provider_error"


class LLMProviderConfigurationError(LLMProviderError):
    code = "llm_provider_configuration_error"


class LLMProviderAuthenticationError(LLMProviderError):
    code = "llm_provider_authentication_error"


class LLMProviderTimeoutError(LLMProviderError):
    code = "llm_provider_timeout"


class LLMProviderRateLimitError(LLMProviderError):
    code = "llm_provider_rate_limit"


class LLMProviderUnavailableError(LLMProviderError):
    code = "llm_provider_unavailable"


class LLMProviderRequestError(LLMProviderError):
    code = "llm_provider_request_error"


class LLMProviderInvalidResponseError(LLMProviderError):
    code = "llm_provider_invalid_response"
