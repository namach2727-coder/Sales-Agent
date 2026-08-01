"""Provider-neutral contracts for one normalized LLM generation call."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol, TypeAlias, runtime_checkable

from app.application.prompts import PromptPackage


SafeScalar: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Immutable application-safe result without provider SDK objects."""

    text: str
    provider: str
    model: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    request_public_id: str | None = None
    provider_request_id: str | None = None
    metadata: Mapping[str, SafeScalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _required_text(self.text, "text"))
        object.__setattr__(
            self, "provider", _required_single_line(self.provider, "provider")
        )
        object.__setattr__(
            self, "model", _required_single_line(self.model, "model")
        )
        for name in (
            "finish_reason",
            "request_public_id",
            "provider_request_id",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _required_single_line(value, name),
                )
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer")
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))


@runtime_checkable
class LLMProvider(Protocol):
    """Application boundary implemented by replaceable provider adapters."""

    def generate(self, prompt_package: PromptPackage) -> LLMResponse: ...


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be blank")
    return normalized


def _required_single_line(value: object, field_name: str) -> str:
    normalized = _required_text(value, field_name)
    if "\n" in normalized or "\r" in normalized:
        raise ValueError(f"{field_name} must be one line")
    if len(normalized) > 200:
        raise ValueError(f"{field_name} is too long")
    return normalized


def _safe_metadata(
    value: Mapping[str, SafeScalar],
) -> Mapping[str, SafeScalar]:
    if not isinstance(value, Mapping):
        raise ValueError("metadata must be a mapping")
    copied: dict[str, SafeScalar] = {}
    for key, item in value.items():
        normalized_key = _required_single_line(key, "metadata key")
        if not isinstance(item, (str, int, float, bool, type(None))):
            raise ValueError("metadata values must be safe scalars")
        if isinstance(item, str) and len(item) > 500:
            raise ValueError("metadata text value is too long")
        copied[normalized_key] = item
    return MappingProxyType(copied)
