"""Safe outbound delivery failures without provider payloads or secrets."""


class OutboundDeliveryError(Exception):
    category = "delivery_error"


class OutboundScopeError(OutboundDeliveryError):
    category = "invalid_scope"


class OutboundInvalidMessageError(OutboundDeliveryError):
    category = "invalid_message"


class OutboundRecipientUnavailableError(OutboundDeliveryError):
    category = "recipient_unavailable"


class OutboundConnectionUnavailableError(OutboundDeliveryError):
    category = "connection_unavailable"


class OutboundAuthenticationError(OutboundDeliveryError):
    category = "authentication"


class OutboundRateLimitError(OutboundDeliveryError):
    category = "rate_limit"


class OutboundTimeoutError(OutboundDeliveryError):
    category = "timeout"


class OutboundUnavailableError(OutboundDeliveryError):
    category = "unavailable"


class OutboundRejectedError(OutboundDeliveryError):
    category = "rejected"


class OutboundRequestError(OutboundDeliveryError):
    category = "request_error"


class OutboundInvalidResponseError(OutboundDeliveryError):
    category = "invalid_response"
