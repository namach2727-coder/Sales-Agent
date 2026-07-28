"""Safe domain errors for the transport-independent conversation core."""


class ConversationCoreError(Exception):
    code = "conversation_core_error"


class ConversationValidationError(ConversationCoreError):
    code = "validation_error"


class ConversationConflictError(ConversationCoreError):
    code = "conflict"


class ConversationNotFoundError(ConversationCoreError):
    code = "not_found"


class ConversationInvalidTransitionError(ConversationCoreError):
    code = "invalid_transition"


class ConversationImmutableError(ConversationCoreError):
    code = "immutable"


class ConversationAssignmentError(ConversationCoreError):
    code = "assignment_error"


class ConversationProcessingError(ConversationCoreError):
    code = "processing_error"
