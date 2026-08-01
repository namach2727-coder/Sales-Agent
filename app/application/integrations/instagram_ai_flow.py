"""Synchronous MVP coordination of committed inbound, AI, and delivery phases."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from time import monotonic
from typing import Literal, Protocol

from app.application.instagram import InstagramInboundProcessingResult
from app.application.knowledge import KnowledgeEngineError
from app.application.llm import LLMProviderError
from app.application.outbound import OutboundDeliveryError
from app.application.prompts import PromptBuilderError
from app.application.services import (
    AIResponseOrchestrator,
    AIResponseOrchestratorError,
    InstagramOutboundDeliveryService,
)
from app.conversation_core.exceptions import ConversationCoreError
from app.tenant_management.context import TenantStoreContext


AIStatus = Literal["not_started", "skipped", "completed", "failed"]
DeliveryStatus = Literal["not_started", "skipped", "sent", "failed"]
logger = logging.getLogger("sales_assistant.instagram_ai_flow")


class TransactionPhaseBoundary(Protocol):
    """Outer transaction owner injected into the integration coordinator."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


@dataclass(frozen=True, slots=True)
class InstagramAIFlowResult:
    acknowledged: bool
    inbound_status: str
    ai_status: AIStatus
    delivery_status: DeliveryStatus
    duplicate: bool
    ignored: bool
    correlation_id: str
    conversation_public_id: str | None = None
    inbound_message_public_id: str | None = None
    assistant_message_public_id: str | None = None
    safe_reason: str | None = None


class InstagramAIFlowCoordinator:
    """Coordinate existing services; no channel, AI, or domain logic lives here."""

    def __init__(
        self,
        *,
        ai_orchestrator: AIResponseOrchestrator,
        outbound_delivery: InstagramOutboundDeliveryService,
        transactions: TransactionPhaseBoundary,
        llm_provider_name: str,
    ) -> None:
        self.ai = ai_orchestrator
        self.outbound = outbound_delivery
        self.transactions = transactions
        self.llm_provider_name = llm_provider_name

    def process(
        self,
        inbound: InstagramInboundProcessingResult,
        *,
        context: TenantStoreContext,
        correlation_id: str,
    ) -> InstagramAIFlowResult:
        correlation = _correlation_id(correlation_id)
        if inbound.status == "duplicate":
            self._log(
                "instagram_ai_flow_duplicate_skipped",
                context=context,
                inbound=inbound,
                correlation_id=correlation,
                phase="inbound",
                outcome="duplicate",
            )
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="skipped",
                delivery_status="skipped",
                duplicate=True,
                ignored=False,
            )
        if inbound.status != "processed":
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="skipped",
                delivery_status="skipped",
                duplicate=False,
                ignored=True,
                safe_reason=inbound.reason or "unsupported_event",
            )
        if not inbound.conversation_public_id or not inbound.message_public_id:
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="failed",
                delivery_status="not_started",
                duplicate=False,
                ignored=False,
                safe_reason="invalid_inbound_result",
            )

        self._log(
            "instagram_ai_flow_inbound_persisted",
            context=context,
            inbound=inbound,
            correlation_id=correlation,
            phase="inbound",
            outcome="persisted",
        )
        ai_started = monotonic()
        self._log(
            "instagram_ai_flow_ai_started",
            context=context,
            inbound=inbound,
            correlation_id=correlation,
            phase="ai",
            outcome="started",
        )
        try:
            assistant_public_id = self.ai.generate_response(
                inbound.conversation_public_id,
                context=context,
                before_provider_call=self.transactions.commit,
            )
            self.transactions.commit()
        except _AI_FAILURES as exc:
            self.transactions.rollback()
            reason = _safe_error_code(exc, "ai_failed")
            self._log(
                "instagram_ai_flow_ai_failed",
                context=context,
                inbound=inbound,
                correlation_id=correlation,
                phase="ai",
                outcome="failed",
                failure_category=reason,
                latency_ms=_latency_ms(ai_started),
            )
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="failed",
                delivery_status="not_started",
                duplicate=False,
                ignored=False,
                safe_reason=reason,
            )
        except Exception:
            self.transactions.rollback()
            self._log(
                "instagram_ai_flow_ai_failed",
                context=context,
                inbound=inbound,
                correlation_id=correlation,
                phase="ai",
                outcome="failed",
                failure_category="unexpected_ai_failure",
                latency_ms=_latency_ms(ai_started),
            )
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="failed",
                delivery_status="not_started",
                duplicate=False,
                ignored=False,
                safe_reason="unexpected_ai_failure",
            )

        self._log(
            "instagram_ai_flow_ai_completed",
            context=context,
            inbound=inbound,
            correlation_id=correlation,
            assistant_message_public_id=assistant_public_id,
            phase="ai",
            outcome="completed",
            latency_ms=_latency_ms(ai_started),
        )
        delivery_started = monotonic()
        try:
            delivery = self.outbound.deliver(
                assistant_public_id,
                conversation_public_id=inbound.conversation_public_id,
                context=context,
                correlation_id=correlation,
                before_provider_call=self.transactions.commit,
            )
            self.transactions.commit()
        except OutboundDeliveryError as exc:
            reason = _safe_error_code(exc, "delivery_failed")
            try:
                # The delivery service records safe failed metadata after the
                # external call. Preserve it for explicit manual retry.
                self.transactions.commit()
            except Exception:
                self.transactions.rollback()
                reason = "delivery_state_persistence_failed"
            self._log(
                "instagram_ai_flow_delivery_failed",
                context=context,
                inbound=inbound,
                correlation_id=correlation,
                assistant_message_public_id=assistant_public_id,
                phase="outbound",
                outcome="failed",
                failure_category=reason,
                latency_ms=_latency_ms(delivery_started),
            )
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="completed",
                delivery_status="failed",
                duplicate=False,
                ignored=False,
                assistant_message_public_id=assistant_public_id,
                safe_reason=reason,
            )
        except Exception:
            self.transactions.rollback()
            self._log(
                "instagram_ai_flow_delivery_failed",
                context=context,
                inbound=inbound,
                correlation_id=correlation,
                assistant_message_public_id=assistant_public_id,
                phase="outbound",
                outcome="failed",
                failure_category="unexpected_delivery_failure",
                latency_ms=_latency_ms(delivery_started),
            )
            return _result(
                inbound,
                correlation_id=correlation,
                ai_status="completed",
                delivery_status="failed",
                duplicate=False,
                ignored=False,
                assistant_message_public_id=assistant_public_id,
                safe_reason="unexpected_delivery_failure",
            )

        self._log(
            "instagram_ai_flow_completed",
            context=context,
            inbound=inbound,
            correlation_id=correlation,
            assistant_message_public_id=assistant_public_id,
            phase="flow",
            outcome=(
                "already_delivered"
                if delivery.already_delivered
                else "completed"
            ),
            latency_ms=_latency_ms(delivery_started),
        )
        return _result(
            inbound,
            correlation_id=correlation,
            ai_status="completed",
            delivery_status="sent",
            duplicate=False,
            ignored=False,
            assistant_message_public_id=assistant_public_id,
        )

    def _log(
        self,
        event: str,
        *,
        context: TenantStoreContext,
        inbound: InstagramInboundProcessingResult,
        correlation_id: str,
        phase: str,
        outcome: str,
        assistant_message_public_id: str | None = None,
        failure_category: str | None = None,
        latency_ms: float | None = None,
    ) -> None:
        logger.info(
            event,
            extra={
                "correlation_id": correlation_id,
                "tenant_public_id": context.tenant_public_id,
                "store_public_id": context.store_public_id,
                "conversation_public_id": inbound.conversation_public_id,
                "inbound_message_public_id": inbound.message_public_id,
                "assistant_message_public_id": assistant_message_public_id,
                "phase": phase,
                "outcome": outcome,
                "provider": self.llm_provider_name if phase == "ai" else "instagram",
                "failure_category": failure_category,
                "latency_ms": latency_ms,
            },
        )


_AI_FAILURES = (
    AIResponseOrchestratorError,
    LLMProviderError,
    KnowledgeEngineError,
    PromptBuilderError,
    ConversationCoreError,
)


def _result(
    inbound: InstagramInboundProcessingResult,
    *,
    correlation_id: str,
    ai_status: AIStatus,
    delivery_status: DeliveryStatus,
    duplicate: bool,
    ignored: bool,
    assistant_message_public_id: str | None = None,
    safe_reason: str | None = None,
) -> InstagramAIFlowResult:
    return InstagramAIFlowResult(
        acknowledged=True,
        inbound_status=inbound.status,
        ai_status=ai_status,
        delivery_status=delivery_status,
        duplicate=duplicate,
        ignored=ignored,
        correlation_id=correlation_id,
        conversation_public_id=inbound.conversation_public_id,
        inbound_message_public_id=inbound.message_public_id,
        assistant_message_public_id=assistant_message_public_id,
        safe_reason=safe_reason,
    )


def _correlation_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > 128
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError("invalid correlation ID")
    return value.strip()


def _safe_error_code(error: Exception, fallback: str) -> str:
    value = getattr(error, "category", None) or getattr(error, "code", None)
    return value if isinstance(value, str) and value else fallback


def _latency_ms(started: float) -> float:
    return round((monotonic() - started) * 1000, 3)
