"""Provider-neutral outbound delivery application contracts."""

from app.application.outbound.contracts import (
    OutboundDeliveryResult,
    OutboundMessage,
    OutboundSender,
)
from app.application.outbound.exceptions import (
    OutboundAuthenticationError,
    OutboundConnectionUnavailableError,
    OutboundDeliveryError,
    OutboundInvalidMessageError,
    OutboundInvalidResponseError,
    OutboundRateLimitError,
    OutboundRecipientUnavailableError,
    OutboundRejectedError,
    OutboundRequestError,
    OutboundScopeError,
    OutboundTimeoutError,
    OutboundUnavailableError,
)

__all__ = [
    "OutboundAuthenticationError",
    "OutboundConnectionUnavailableError",
    "OutboundDeliveryError",
    "OutboundDeliveryResult",
    "OutboundInvalidMessageError",
    "OutboundInvalidResponseError",
    "OutboundMessage",
    "OutboundRateLimitError",
    "OutboundRecipientUnavailableError",
    "OutboundRejectedError",
    "OutboundRequestError",
    "OutboundScopeError",
    "OutboundSender",
    "OutboundTimeoutError",
    "OutboundUnavailableError",
]
