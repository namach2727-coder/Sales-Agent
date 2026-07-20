"""Safe, typed provisioning failures."""


class ProvisioningError(RuntimeError):
    code = "provisioning_error"


class ProvisioningValidationError(ProvisioningError):
    code = "validation_error"


class ProvisioningConflictError(ProvisioningError):
    code = "tenant_conflict"


class ProvisioningTransactionError(ProvisioningError):
    code = "transaction_ownership_error"


class ProvisioningExecutionError(ProvisioningError):
    code = "provisioning_failed"

    def __init__(self, failed_step: str, *, cause: Exception | None = None):
        super().__init__(f"tenant provisioning failed at step {failed_step!r}")
        self.failed_step = failed_step
        self.cause = cause
