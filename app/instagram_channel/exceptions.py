"""Safe domain errors for the Instagram channel boundary."""


class InstagramChannelError(Exception):
    code = "instagram_channel_error"


class InstagramChannelValidationError(InstagramChannelError):
    code = "validation_error"


class InstagramChannelConflictError(InstagramChannelError):
    code = "conflict"


class InstagramChannelNotFoundError(InstagramChannelError):
    code = "not_found"


class InstagramChannelStaleWriteError(InstagramChannelError):
    code = "stale_write"


class InstagramChannelInvalidTransitionError(InstagramChannelError):
    code = "invalid_transition"


class InstagramChannelScopeError(InstagramChannelError):
    code = "inactive_scope"


class InstagramCredentialConfigurationError(InstagramChannelError):
    code = "credential_configuration_error"


class InstagramWebhookSecurityError(InstagramChannelError):
    code = "webhook_security_error"


class InstagramWebhookPayloadError(InstagramChannelError):
    code = "invalid_webhook_payload"
