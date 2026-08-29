"""Safe immutable contracts for outbound channel adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class OutboundMessage:
    """Application-safe message; credentials and persistence IDs are excluded."""

    message_public_id: str
    conversation_public_id: str
    tenant_public_id: str
    store_public_id: str
    channel: str
    recipient_external_id: str
    text: str
    recipient_type: str = "account"
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "message_public_id",
            "conversation_public_id",
            "tenant_public_id",
            "store_public_id",
            "channel",
            "recipient_external_id",
        ):
            object.__setattr__(self, name, _single_line(getattr(self, name), name))
        object.__setattr__(self, "text", _text(self.text, "text"))
        recipient_type = _single_line(
            self.recipient_type, "recipient_type", maximum=20
        )
        if recipient_type not in {"account", "comment"}:
            raise ValueError("invalid recipient_type")
        object.__setattr__(self, "recipient_type", recipient_type)
        if self.correlation_id is not None:
            object.__setattr__(
                self,
                "correlation_id",
                _single_line(self.correlation_id, "correlation_id", maximum=128),
            )


@dataclass(frozen=True, slots=True)
class OutboundDeliveryResult:
    message_public_id: str
    conversation_public_id: str
    channel: str
    provider: str
    delivered: bool
    already_delivered: bool = False
    provider_message_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "message_public_id",
            "conversation_public_id",
            "channel",
            "provider",
        ):
            object.__setattr__(self, name, _single_line(getattr(self, name), name))
        if self.provider_message_id is not None:
            object.__setattr__(
                self,
                "provider_message_id",
                _single_line(self.provider_message_id, "provider_message_id"),
            )
        if self.already_delivered and not self.delivered:
            raise ValueError("already_delivered requires delivered")


@runtime_checkable
class OutboundSender(Protocol):
    """A provider adapter bound to trusted credentials outside this contract."""

    def send(self, message: OutboundMessage) -> OutboundDeliveryResult: ...


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} cannot be blank")
    normalized = value.strip()
    if len(normalized) > 10_000:
        raise ValueError(f"{field} is too long")
    return normalized


def _single_line(value: object, field: str, maximum: int = 200) -> str:
    normalized = _text(value, field)
    if "\n" in normalized or "\r" in normalized:
        raise ValueError(f"{field} must be one line")
    if len(normalized) > maximum:
        raise ValueError(f"{field} is too long")
    return normalized
