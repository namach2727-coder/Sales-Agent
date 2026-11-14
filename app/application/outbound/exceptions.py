"""Safe outbound delivery failures without provider payloads or secrets."""


class OutboundDeliveryError(Exception):
    category = "delivery_error"

    def __init__(
        self,
        message: str = "",
        *,
        provider_http_status: int | None = None,
        provider_error_code: int | None = None,
        provider_error_subcode: int | None = None,
        provider_error_type: str | None = None,
        provider_trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        # Only allowlisted, non-secret provider diagnostics may cross this
        # boundary. Raw response bodies and credentials are never retained.
        self.provider_diagnostics = {
            key: value
            for key, value in {
                "provider_http_status": provider_http_status,
                "provider_error_code": provider_error_code,
                "provider_error_subcode": provider_error_subcode,
                "provider_error_type": provider_error_type,
                "provider_trace_id": provider_trace_id,
            }.items()
            if value is not None
        }


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


class OutboundAmbiguousDeliveryError(OutboundDeliveryError):
    """The provider may have accepted the request, so retry is unsafe."""

    category = "delivery_ambiguous"


class OutboundRejectedError(OutboundDeliveryError):
    category = "rejected"


class OutboundRequestError(OutboundDeliveryError):
    category = "request_error"


class OutboundInvalidResponseError(OutboundDeliveryError):
    category = "invalid_response"
