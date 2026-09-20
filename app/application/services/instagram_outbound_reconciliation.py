"""Explicit, tenant-scoped reconciliation for ambiguous Instagram sends."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.application.outbound import OutboundDeliveryResult
from app.application.outbound.delivery_state import (
    DELIVERY_AMBIGUOUS,
    FAILED_CONFIRMED,
    IN_PROGRESS,
    NOT_REQUIRED,
    NOT_SENT_CONFIRMED,
    REQUIRED,
    RESOLVED,
    SENT_CONFIRMED,
    attempt_marker,
    certainty,
    reconciliation_status,
    retry_eligible,
)
from app.application.services.instagram_outbound_delivery import (
    InstagramOutboundDeliveryService,
)
from app.infrastructure.database.repositories.instagram_outbound_repository import (
    InstagramOutboundMessageContext,
    InstagramOutboundRepository,
)
from app.models import TenantAuditLog
from app.tenant_management.context import TenantStoreContext


ReconciliationDecision = Literal[
    "CONFIRM_SENT", "CONFIRM_NOT_SENT", "LEAVE_UNRESOLVED"
]
RETRY_CLAIM_LEASE = timedelta(minutes=5)


class OutboundReconciliationError(Exception):
    code = "outbound_reconciliation_error"


class OutboundReconciliationNotFound(OutboundReconciliationError):
    code = "not_found"


class OutboundReconciliationConflict(OutboundReconciliationError):
    code = "reconciliation_conflict"


class OutboundReconciliationValidation(OutboundReconciliationError):
    code = "validation_error"


@dataclass(frozen=True, slots=True)
class OutboundReconciliationDetail:
    message_public_id: str
    conversation_public_id: str
    delivery_status: str | None
    delivery_certainty: str | None
    reconciliation_status: str | None
    safe_retry_eligible: bool
    provider_message_id_present: bool
    provider_call_started_at: str | None
    last_failure_category: str | None
    reconciled_at: str | None
    allowed_actions: tuple[str, ...]


class InstagramOutboundReconciliationService:
    """Resolve uncertain sends without reconstructing or regenerating output."""

    def __init__(
        self,
        session: Session,
        *,
        outbound_delivery: InstagramOutboundDeliveryService,
        actor_identity_id: int,
    ) -> None:
        self.session = session
        self.repository = InstagramOutboundRepository(session)
        self.outbound = outbound_delivery
        self.actor_identity_id = actor_identity_id

    def get(
        self, message_public_id: str, *, context: TenantStoreContext
    ) -> OutboundReconciliationDetail:
        message = self._message(message_public_id, context=context, lock=False)
        return _detail(message)

    def reconcile(
        self,
        message_public_id: str,
        *,
        decision: ReconciliationDecision,
        context: TenantStoreContext,
    ) -> OutboundReconciliationDetail:
        if decision not in {
            "CONFIRM_SENT",
            "CONFIRM_NOT_SENT",
            "LEAVE_UNRESOLVED",
        }:
            raise OutboundReconciliationValidation("invalid reconciliation decision")
        message = self._message(message_public_id, context=context, lock=True)
        metadata = dict(message.metadata)
        if _active_retry_claim(metadata):
            raise OutboundReconciliationConflict(
                "outbound retry is currently in progress"
            )
        prior_certainty = _effective_certainty(metadata)
        if prior_certainty == SENT_CONFIRMED and decision != "CONFIRM_SENT":
            raise OutboundReconciliationConflict("sent delivery cannot be reopened")

        now = datetime.now(UTC).isoformat()
        if decision == "CONFIRM_SENT":
            metadata.update(
                {
                    "delivery_status": "sent",
                    "delivery_provider": "instagram",
                    "delivery_certainty": SENT_CONFIRMED,
                    "reconciliation_status": RESOLVED,
                    "reconciliation_source": "operator",
                    "reconciled_at": now,
                    "reconciled_by": str(self.actor_identity_id),
                    "safe_retry_eligible": False,
                }
            )
            metadata.pop("reconciliation_reason", None)
        elif decision == "CONFIRM_NOT_SENT":
            if prior_certainty == SENT_CONFIRMED:
                raise OutboundReconciliationConflict("sent delivery cannot be reopened")
            metadata.update(
                {
                    "delivery_status": "failed",
                    "delivery_provider": "instagram",
                    "delivery_certainty": NOT_SENT_CONFIRMED,
                    "reconciliation_status": RESOLVED,
                    "reconciliation_source": "operator",
                    "reconciled_at": now,
                    "reconciled_by": str(self.actor_identity_id),
                    "safe_retry_eligible": True,
                }
            )
            metadata.pop("reconciliation_reason", None)
        else:
            if prior_certainty not in {DELIVERY_AMBIGUOUS, None}:
                raise OutboundReconciliationConflict(
                    "delivery is not awaiting reconciliation"
                )
            metadata.update(
                {
                    "delivery_status": "pending",
                    "delivery_provider": "instagram",
                    "delivery_certainty": DELIVERY_AMBIGUOUS,
                    "reconciliation_status": REQUIRED,
                    "reconciliation_source": "operator",
                    "reconciled_at": now,
                    "reconciled_by": str(self.actor_identity_id),
                    "safe_retry_eligible": False,
                    "reconciliation_reason": "operator_left_unresolved",
                }
            )

        self._update(message, context=context, metadata=metadata)
        self._audit(
            context=context,
            message=message,
            action="instagram_outbound.reconciled",
            details={
                "decision": decision,
                "prior_certainty": prior_certainty,
                "new_certainty": metadata["delivery_certainty"],
            },
        )
        self.session.flush()
        return _detail(_replace_metadata(message, metadata))

    def retry(
        self,
        message_public_id: str,
        *,
        context: TenantStoreContext,
        correlation_id: str | None = None,
        commit_before_provider_call: Callable[[], None],
    ) -> tuple[OutboundReconciliationDetail, OutboundDeliveryResult]:
        message = self._message(message_public_id, context=context, lock=True)
        metadata = dict(message.metadata)
        if (
            _effective_certainty(metadata) != NOT_SENT_CONFIRMED
            or not retry_eligible(metadata)
            or reconciliation_status(metadata) != RESOLVED
            or metadata.get("delivery_status") == "sent"
        ):
            raise OutboundReconciliationConflict(
                "outbound delivery is not eligible for safe retry"
            )
        attempt_count = _attempt_count(metadata) + 1
        claimed, attempt_id = attempt_marker(
            metadata,
            attempt_count=attempt_count,
            reconciliation_value=IN_PROGRESS,
        )
        claimed["reconciliation_reason"] = "explicit_retry_in_progress"
        self._update(message, context=context, metadata=claimed)
        self._audit(
            context=context,
            message=message,
            action="instagram_outbound.retry_claimed",
            details={"prior_certainty": NOT_SENT_CONFIRMED},
        )
        self.session.flush()
        commit_before_provider_call()
        result = self.outbound.deliver(
            message.message_public_id,
            conversation_public_id=message.conversation_public_id,
            context=context,
            correlation_id=correlation_id,
            retry_claim_id=attempt_id,
        )
        refreshed = self._message(message_public_id, context=context, lock=False)
        return _detail(refreshed), result

    def _message(
        self,
        message_public_id: str,
        *,
        context: TenantStoreContext,
        lock: bool,
    ) -> InstagramOutboundMessageContext:
        if context.store_id is None:
            raise OutboundReconciliationNotFound("outbound message was not found")
        message = self.repository.get_scoped_message_context(
            message_public_id,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            for_update=lock,
        )
        if message is None or message.direction != "outbound":
            raise OutboundReconciliationNotFound("outbound message was not found")
        return message

    def _update(
        self,
        message: InstagramOutboundMessageContext,
        *,
        context: TenantStoreContext,
        metadata: dict[str, object],
    ) -> None:
        assert context.store_id is not None
        if not self.repository.update_delivery(
            message.message_public_id,
            conversation_public_id=message.conversation_public_id,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            metadata=metadata,
        ):
            raise OutboundReconciliationNotFound("outbound message was not found")

    def _audit(
        self,
        *,
        context: TenantStoreContext,
        message: InstagramOutboundMessageContext,
        action: str,
        details: dict[str, object],
    ) -> None:
        self.session.add(
            TenantAuditLog(
                tenant_id=context.tenant_id,
                store_id=context.store_id,
                actor_identity_id=self.actor_identity_id,
                action=action,
                target_type="conversation_message",
                target_public_id=message.message_public_id,
                details_json=details,
            )
        )


def _effective_certainty(metadata: dict[str, object]) -> str | None:
    value = certainty(metadata)
    if value is not None:
        return value
    if metadata.get("delivery_status") == "pending":
        return DELIVERY_AMBIGUOUS
    if metadata.get("delivery_status") == "sent":
        return SENT_CONFIRMED
    if metadata.get("delivery_status") == "failed":
        return FAILED_CONFIRMED
    return None


def _effective_reconciliation(metadata: dict[str, object]) -> str | None:
    value = reconciliation_status(metadata)
    if value is not None:
        return value
    return REQUIRED if metadata.get("delivery_status") == "pending" else NOT_REQUIRED


def _detail(message: InstagramOutboundMessageContext) -> OutboundReconciliationDetail:
    metadata = message.metadata
    certainty_value = _effective_certainty(metadata)
    reconciliation_value = _effective_reconciliation(metadata)
    safe_retry = (
        retry_eligible(metadata)
        and certainty_value == NOT_SENT_CONFIRMED
        and reconciliation_value == RESOLVED
    )
    actions: list[str] = []
    if _active_retry_claim(metadata):
        actions = []
    elif certainty_value == DELIVERY_AMBIGUOUS:
        actions.extend(("CONFIRM_SENT", "CONFIRM_NOT_SENT", "LEAVE_UNRESOLVED"))
    elif certainty_value == FAILED_CONFIRMED:
        actions.extend(("CONFIRM_SENT", "CONFIRM_NOT_SENT"))
    elif safe_retry:
        actions.append("RETRY")
    return OutboundReconciliationDetail(
        message_public_id=message.message_public_id,
        conversation_public_id=message.conversation_public_id,
        delivery_status=_text(metadata.get("delivery_status")),
        delivery_certainty=certainty_value,
        reconciliation_status=reconciliation_value,
        safe_retry_eligible=safe_retry,
        provider_message_id_present=bool(
            message.provider_message_id or _text(metadata.get("provider_message_id"))
        ),
        provider_call_started_at=_text(metadata.get("provider_call_started_at")),
        last_failure_category=_text(metadata.get("last_failure_category")),
        reconciled_at=_text(metadata.get("reconciled_at")),
        allowed_actions=tuple(actions),
    )


def _replace_metadata(
    message: InstagramOutboundMessageContext, metadata: dict[str, object]
) -> InstagramOutboundMessageContext:
    return InstagramOutboundMessageContext(
        message_public_id=message.message_public_id,
        conversation_public_id=message.conversation_public_id,
        conversation_id=message.conversation_id,
        instagram_connection_id=message.instagram_connection_id,
        provider_participant_key=message.provider_participant_key,
        direction=message.direction,
        content_type=message.content_type,
        text=message.text,
        provider_message_id=message.provider_message_id,
        metadata=metadata,
        reply_to_metadata=message.reply_to_metadata,
    )


def _attempt_count(metadata: dict[str, object]) -> int:
    value = metadata.get("delivery_attempt_count", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OutboundReconciliationValidation("invalid delivery metadata")
    return value


def _active_retry_claim(metadata: dict[str, object]) -> bool:
    if reconciliation_status(metadata) != IN_PROGRESS:
        return False
    started_at = _text(metadata.get("provider_call_started_at"))
    if started_at is None:
        return False
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return False
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return datetime.now(UTC) - started.astimezone(UTC) < RETRY_CLAIM_LEASE


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
