"""Application orchestration for delivery of one persisted assistant message."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import logging
from time import perf_counter

from app.application.outbound import (
    OutboundConnectionUnavailableError,
    OutboundDeliveryError,
    OutboundDeliveryResult,
    OutboundInvalidMessageError,
    OutboundInvalidResponseError,
    OutboundMessage,
    OutboundRecipientUnavailableError,
    OutboundScopeError,
    OutboundSender,
    OutboundUnavailableError,
)
from app.infrastructure.database.repositories.instagram_outbound_repository import (
    InstagramOutboundConnectionContext,
    InstagramOutboundMessageContext,
    InstagramOutboundRepository,
)
from app.instagram_channel.exceptions import (
    InstagramCredentialConfigurationError,
)
from app.instagram_channel.security import TokenCipher
from app.tenant_management.context import TenantStoreContext


logger = logging.getLogger(__name__)
InstagramSenderFactory = Callable[..., OutboundSender]


class InstagramOutboundDeliveryService:
    """Deliver one existing assistant message without owning its transaction."""

    def __init__(
        self,
        *,
        repository: InstagramOutboundRepository,
        token_cipher: TokenCipher,
        sender_factory: InstagramSenderFactory,
    ) -> None:
        self.repository = repository
        self.token_cipher = token_cipher
        self.sender_factory = sender_factory

    def deliver(
        self,
        message_public_id: str,
        *,
        conversation_public_id: str,
        context: TenantStoreContext,
        correlation_id: str | None = None,
        delivered_at: datetime | None = None,
        before_provider_call: Callable[[], None] | None = None,
    ) -> OutboundDeliveryResult:
        tenant_id, store_id, tenant_public_id, store_public_id = _active_scope(
            context
        )
        safe_correlation_id = _optional_single_line(
            correlation_id, "correlation_id", maximum=128
        )
        persisted = self.repository.get_message_context(
            _public_id(message_public_id, "message_public_id"),
            conversation_public_id=_public_id(
                conversation_public_id, "conversation_public_id"
            ),
            tenant_id=tenant_id,
            store_id=store_id,
        )
        if persisted is None:
            raise OutboundInvalidMessageError("outbound message was not found")
        _validate_message(persisted)

        metadata = dict(persisted.metadata)
        if _already_delivered(persisted, metadata):
            provider_message_id = persisted.provider_message_id or _metadata_text(
                metadata.get("provider_message_id")
            )
            logger.info(
                "instagram_outbound_already_delivered",
                extra={
                    "message_public_id": persisted.message_public_id,
                    "conversation_public_id": persisted.conversation_public_id,
                    "tenant_public_id": tenant_public_id,
                    "store_public_id": store_public_id,
                    "channel": "instagram",
                    "provider": "instagram",
                    "correlation_id": safe_correlation_id,
                    "outcome": "already_delivered",
                },
            )
            return OutboundDeliveryResult(
                message_public_id=persisted.message_public_id,
                conversation_public_id=persisted.conversation_public_id,
                channel="instagram",
                provider="instagram",
                delivered=True,
                already_delivered=True,
                provider_message_id=provider_message_id,
            )

        recipient = persisted.provider_participant_key.strip()
        if not recipient:
            logger.warning(
                "instagram_outbound_recipient_unavailable",
                extra=_log_fields(
                    persisted,
                    tenant_public_id=tenant_public_id,
                    store_public_id=store_public_id,
                    correlation_id=safe_correlation_id,
                    outcome="recipient_unavailable",
                ),
            )
            raise OutboundRecipientUnavailableError(
                "Instagram recipient is unavailable"
            )
        try:
            connections = self.repository.list_active_connections(
                tenant_id=tenant_id,
                store_id=store_id,
            )
            connection = _select_connection(
                connections,
                expected_connection_id=persisted.instagram_connection_id,
            )
            if not connection.encrypted_access_token:
                raise OutboundConnectionUnavailableError(
                    "Instagram connection credentials are unavailable"
                )
        except OutboundConnectionUnavailableError:
            logger.warning(
                "instagram_outbound_connection_unavailable",
                extra=_log_fields(
                    persisted,
                    tenant_public_id=tenant_public_id,
                    store_public_id=store_public_id,
                    correlation_id=safe_correlation_id,
                    outcome="connection_unavailable",
                ),
            )
            raise

        outbound = OutboundMessage(
            message_public_id=persisted.message_public_id,
            conversation_public_id=persisted.conversation_public_id,
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            channel="instagram",
            recipient_external_id=recipient,
            text=persisted.text or "",
            correlation_id=safe_correlation_id,
        )
        attempt_count = _attempt_count(metadata) + 1
        pending_metadata = _delivery_metadata(
            metadata,
            status="pending",
            attempt_count=attempt_count,
        )
        self._update(
            persisted,
            tenant_id=tenant_id,
            store_id=store_id,
            metadata=pending_metadata,
        )
        operation_started = perf_counter()
        logger.info(
            "instagram_outbound_started",
            extra=_log_fields(
                persisted,
                tenant_public_id=tenant_public_id,
                store_public_id=store_public_id,
                correlation_id=safe_correlation_id,
                outcome="started",
            ),
        )
        if before_provider_call is not None:
            before_provider_call()

        try:
            # Plaintext exists only for the smallest possible interval: after
            # all validation and immediately before constructing the sender.
            access_token = self.token_cipher.decrypt(
                connection.encrypted_access_token
            )
            sender = self.sender_factory(
                access_token=access_token,
                sender_account_id=connection.instagram_account_id,
            )
            result = sender.send(outbound)
            _validate_result(outbound, result)
        except InstagramCredentialConfigurationError as exc:
            failure = OutboundConnectionUnavailableError(
                "Instagram connection credentials are unavailable"
            )
            self._record_failure(
                persisted,
                tenant_id=tenant_id,
                store_id=store_id,
                metadata=pending_metadata,
                failure=failure,
                tenant_public_id=tenant_public_id,
                store_public_id=store_public_id,
                correlation_id=safe_correlation_id,
                operation_started=operation_started,
            )
            raise failure from exc
        except OutboundDeliveryError as exc:
            self._record_failure(
                persisted,
                tenant_id=tenant_id,
                store_id=store_id,
                metadata=pending_metadata,
                failure=exc,
                tenant_public_id=tenant_public_id,
                store_public_id=store_public_id,
                correlation_id=safe_correlation_id,
                operation_started=operation_started,
            )
            raise
        except Exception as exc:
            failure = OutboundUnavailableError(
                "Instagram delivery is unavailable"
            )
            self._record_failure(
                persisted,
                tenant_id=tenant_id,
                store_id=store_id,
                metadata=pending_metadata,
                failure=failure,
                tenant_public_id=tenant_public_id,
                store_public_id=store_public_id,
                correlation_id=safe_correlation_id,
                operation_started=operation_started,
            )
            raise failure from exc

        timestamp = _aware_datetime(delivered_at or datetime.now(UTC))
        sent_metadata = _delivery_metadata(
            pending_metadata,
            status="sent",
            attempt_count=attempt_count,
            provider_message_id=result.provider_message_id,
            delivered_at=timestamp.isoformat(),
        )
        # There is an unavoidable crash window between Meta accepting the
        # request and this flush. This MVP is at-most-once after a recorded
        # success, not exactly-once across process/database failures.
        self._update(
            persisted,
            tenant_id=tenant_id,
            store_id=store_id,
            metadata=sent_metadata,
            provider_message_id=result.provider_message_id,
        )
        logger.info(
            "instagram_outbound_delivered",
            extra={
                **_log_fields(
                    persisted,
                    tenant_public_id=tenant_public_id,
                    store_public_id=store_public_id,
                    correlation_id=safe_correlation_id,
                    outcome="delivered",
                ),
                "latency_ms": round(
                    (perf_counter() - operation_started) * 1000, 3
                ),
            },
        )
        return result

    def _record_failure(
        self,
        persisted: InstagramOutboundMessageContext,
        *,
        tenant_id: int,
        store_id: int,
        metadata: dict[str, object],
        failure: OutboundDeliveryError,
        tenant_public_id: str,
        store_public_id: str,
        correlation_id: str | None,
        operation_started: float,
    ) -> None:
        failed = _delivery_metadata(
            metadata,
            status="failed",
            attempt_count=_attempt_count(metadata),
            failure_category=failure.category,
        )
        self._update(
            persisted,
            tenant_id=tenant_id,
            store_id=store_id,
            metadata=failed,
        )
        logger.warning(
            "instagram_outbound_failed",
            extra={
                **_log_fields(
                    persisted,
                    tenant_public_id=tenant_public_id,
                    store_public_id=store_public_id,
                    correlation_id=correlation_id,
                    outcome="failed",
                ),
                "failure_category": failure.category,
                "latency_ms": round(
                    (perf_counter() - operation_started) * 1000, 3
                ),
            },
        )

    def _update(
        self,
        persisted: InstagramOutboundMessageContext,
        *,
        tenant_id: int,
        store_id: int,
        metadata: dict[str, object],
        provider_message_id: str | None = None,
    ) -> None:
        updated = self.repository.update_delivery(
            persisted.message_public_id,
            conversation_public_id=persisted.conversation_public_id,
            tenant_id=tenant_id,
            store_id=store_id,
            metadata=metadata,
            provider_message_id=provider_message_id,
        )
        if not updated:
            raise OutboundInvalidMessageError("outbound message was not found")


def _active_scope(
    context: TenantStoreContext,
) -> tuple[int, int, str, str]:
    if (
        not isinstance(context, TenantStoreContext)
        or context.tenant_status != "active"
        or context.store_status != "active"
        or context.store_id is None
        or context.store_public_id is None
    ):
        raise OutboundScopeError("active tenant/store context is required")
    return (
        context.tenant_id,
        context.store_id,
        context.tenant_public_id,
        context.store_public_id,
    )


def _validate_message(message: InstagramOutboundMessageContext) -> None:
    if (
        message.direction != "outbound"
        or message.content_type != "text"
        or message.text is None
        or not message.text.strip()
        or message.metadata.get("author_type") != "assistant"
        or message.metadata.get("source") != "ai_response_orchestrator"
    ):
        raise OutboundInvalidMessageError(
            "message is not a deliverable assistant text"
        )


def _already_delivered(
    message: InstagramOutboundMessageContext,
    metadata: dict[str, object],
) -> bool:
    return (
        metadata.get("delivery_status") == "sent"
        and metadata.get("delivery_provider") == "instagram"
        and bool(
            message.provider_message_id
            or _metadata_text(metadata.get("provider_message_id"))
        )
    )


def _select_connection(
    connections: tuple[InstagramOutboundConnectionContext, ...],
    *,
    expected_connection_id: int,
) -> InstagramOutboundConnectionContext:
    if len(connections) != 1:
        raise OutboundConnectionUnavailableError(
            "exactly one active Instagram connection is required"
        )
    connection = connections[0]
    if connection.connection_id != expected_connection_id:
        raise OutboundConnectionUnavailableError(
            "conversation Instagram connection is unavailable"
        )
    return connection


def _validate_result(
    outbound: OutboundMessage,
    result: object,
) -> None:
    if (
        not isinstance(result, OutboundDeliveryResult)
        or not result.delivered
        or result.already_delivered
        or result.message_public_id != outbound.message_public_id
        or result.conversation_public_id != outbound.conversation_public_id
        or result.channel != "instagram"
        or result.provider != "instagram"
        or not result.provider_message_id
    ):
        raise OutboundInvalidResponseError(
            "Instagram returned an invalid delivery result"
        )


def _delivery_metadata(
    existing: dict[str, object],
    *,
    status: str,
    attempt_count: int,
    provider_message_id: str | None = None,
    delivered_at: str | None = None,
    failure_category: str | None = None,
) -> dict[str, object]:
    result = dict(existing)
    result.update(
        {
            "delivery_status": status,
            "delivery_provider": "instagram",
            "delivery_attempt_count": attempt_count,
        }
    )
    if provider_message_id is not None:
        result["provider_message_id"] = provider_message_id
    if delivered_at is not None:
        result["delivered_at"] = delivered_at
    if failure_category is not None:
        result["last_failure_category"] = failure_category
    elif status == "sent":
        result.pop("last_failure_category", None)
    return result


def _attempt_count(metadata: dict[str, object]) -> int:
    value = metadata.get("delivery_attempt_count", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OutboundInvalidMessageError("invalid delivery metadata")
    return value


def _metadata_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _public_id(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or "\n" in value
        or "\r" in value
        or len(value.strip()) > 200
    ):
        raise OutboundInvalidMessageError(f"invalid {field}")
    return value.strip()


def _aware_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise OutboundInvalidMessageError("invalid delivered_at")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optional_single_line(
    value: object | None,
    field: str,
    *,
    maximum: int,
) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value.strip()
        or "\n" in value
        or "\r" in value
        or len(value.strip()) > maximum
    ):
        raise OutboundInvalidMessageError(f"invalid {field}")
    return value.strip()


def _log_fields(
    message: InstagramOutboundMessageContext,
    *,
    tenant_public_id: str,
    store_public_id: str,
    correlation_id: str | None,
    outcome: str,
) -> dict[str, object]:
    return {
        "channel": "instagram",
        "provider": "instagram",
        "tenant_public_id": tenant_public_id,
        "store_public_id": store_public_id,
        "conversation_public_id": message.conversation_public_id,
        "message_public_id": message.message_public_id,
        "correlation_id": correlation_id,
        "outcome": outcome,
    }
