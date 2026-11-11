"""Deterministic AutomationRule execution for persisted Instagram inbound messages."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import logging
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.outbound import OutboundDeliveryError
from app.application.services import ConversationService, InstagramOutboundDeliveryService
from app.automation_rules.models import AutomationRule
from app.conversation_core.models import Conversation, ConversationMessage
from app.module_catalog import has_capability
from app.tenant_management.context import TenantStoreContext


logger = logging.getLogger("sales_assistant.automation_rules.runtime")
_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = str.maketrans({
    "،": ",", "؛": ";", "؟": "?", "ـ": "", "‌": " ",
    "“": '"', "”": '"', "‘": "'", "’": "'",
})


def normalize_match_text(value: str) -> str:
    """Return a conservative, reusable comparison value without mutating input."""

    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.translate(_PUNCTUATION).replace("ي", "ی").replace("ك", "ک")
    return _WHITESPACE.sub(" ", normalized).strip().casefold()


def rule_matches(rule: AutomationRule, message_text: str) -> bool:
    message = normalize_match_text(message_text)
    for raw_keyword in rule.keywords or ():
        keyword = normalize_match_text(str(raw_keyword))
        if not keyword:
            continue
        if rule.match_type == "EXACT" and message == keyword:
            return True
        if rule.match_type == "CONTAINS" and keyword in message:
            return True
        if rule.match_type == "STARTS_WITH" and message.startswith(keyword):
            return True
    return False


@dataclass(frozen=True, slots=True)
class AutomationRuntimeResult:
    handled: bool
    matched: bool = False
    delivery_status: str = "skipped"
    outbound_message_public_id: str | None = None
    rule_public_id: str | None = None
    safe_reason: str | None = None


class InstagramAutomationRuleRuntime:
    """Select and execute at most one scoped deterministic rule before AI."""

    def __init__(
        self,
        session: Session,
        *,
        conversation_service: ConversationService,
        outbound_delivery: InstagramOutboundDeliveryService,
        capability_checker: Callable[..., bool] = has_capability,
    ) -> None:
        self.session = session
        self.conversations = conversation_service
        self.outbound = outbound_delivery
        self.capability_checker = capability_checker

    def process(
        self,
        *,
        conversation_public_id: str,
        inbound_message_public_id: str,
        context: TenantStoreContext,
        correlation_id: str | None = None,
    ) -> AutomationRuntimeResult:
        if context.store_id is None:
            return AutomationRuntimeResult(handled=True, safe_reason="invalid_store_scope")
        conversation = self.conversations.get_conversation(
            conversation_public_id,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
        )
        if conversation.status == "human_active":
            return AutomationRuntimeResult(handled=True, safe_reason="conversation_human_active")
        if not self.capability_checker(
            self.session,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            capability_code="instagram_automation",
        ):
            return AutomationRuntimeResult(handled=False, safe_reason="automation_capability_unavailable")

        inbound = self.session.scalar(
            select(ConversationMessage).where(
                ConversationMessage.public_id == inbound_message_public_id,
                ConversationMessage.conversation_id == conversation.id,
                ConversationMessage.tenant_id == context.tenant_id,
                ConversationMessage.store_id == context.store_id,
                ConversationMessage.direction == "inbound",
            )
        )
        if inbound is None or not inbound.text:
            return AutomationRuntimeResult(handled=False, safe_reason="automation_input_unavailable")
        trigger = _trigger_type(inbound)
        rules = tuple(
            self.session.scalars(
                select(AutomationRule)
                .where(
                    AutomationRule.tenant_id == context.tenant_id,
                    AutomationRule.store_id == context.store_id,
                    AutomationRule.enabled.is_(True),
                    AutomationRule.trigger_type == trigger,
                )
                .order_by(AutomationRule.priority.desc(), AutomationRule.id.asc())
            ).all()
        )
        winner = next((rule for rule in rules if rule_matches(rule, inbound.text)), None)
        if winner is None:
            _log_decision(context, correlation_id, matched=False, trigger=trigger)
            return AutomationRuntimeResult(handled=False)

        action_payload = dict(winner.action_payload or {})
        deliveries: list[tuple[str, str, str]] = []
        if trigger == "COMMENT_KEYWORD":
            comment_id = (inbound.metadata_json or {}).get("instagram_comment_id")
            if not isinstance(comment_id, str) or not comment_id.strip():
                return AutomationRuntimeResult(
                    handled=True, matched=True, delivery_status="failed",
                    rule_public_id=winner.public_id, safe_reason="comment_id_unavailable",
                )
            deliveries = [
                ("public_comment_reply", "comment_reply", str(action_payload.get("comment_reply_text") or "")),
                ("private_comment_reply", "comment", str(action_payload.get("text") or "")),
            ]
        else:
            deliveries = [("message", "account", str(action_payload.get("text") or ""))]

        results: list[str] = []
        outbound_ids: list[str] = []
        failures: list[str] = []
        for delivery_kind, recipient_type, response_text in deliveries:
            if not response_text.strip():
                failures.append("response_text_unavailable")
                results.append("failed")
                continue
            key = "automation:" + hashlib.sha256(
                f"{inbound.public_id}:{winner.public_id}:{delivery_kind}".encode("utf-8")
            ).hexdigest()[:48]
            outbound = self.session.scalar(
                select(ConversationMessage).where(
                    ConversationMessage.tenant_id == context.tenant_id,
                    ConversationMessage.store_id == context.store_id,
                    ConversationMessage.idempotency_key == key,
                )
            )
            if outbound is None:
                outbound_metadata = {
                    "author_type": "automation",
                    "source": "automation_rule",
                    "automation_rule_public_id": winner.public_id,
                    "automation_trigger_type": trigger,
                    "automation_action_type": winner.action_type,
                    "automation_delivery_kind": delivery_kind,
                }
                if recipient_type in {"comment", "comment_reply"}:
                    outbound_metadata.update({
                        "instagram_recipient_type": recipient_type,
                        "instagram_comment_id": str((inbound.metadata_json or {}).get("instagram_comment_id") or ""),
                    })
                outbound = self.conversations.append_message(
                    conversation.public_id,
                    tenant_id=context.tenant_id,
                    store_id=context.store_id,
                    idempotency_key=key,
                    direction="outbound",
                    content_type="text",
                    occurred_at=datetime.now(UTC),
                    text=response_text.strip(),
                    reply_to_message_id=inbound.id,
                    metadata=outbound_metadata,
                )
            outbound_ids.append(outbound.public_id)
            try:
                delivery = self.outbound.deliver(
                    outbound.public_id,
                    conversation_public_id=conversation.public_id,
                    context=context,
                    correlation_id=correlation_id,
                    before_provider_call=self.session.commit,
                )
                self.session.commit()
                results.append("already_delivered" if delivery.already_delivered else "sent")
            except OutboundDeliveryError as exc:
                try:
                    self.session.commit()
                except Exception:
                    self.session.rollback()
                results.append("failed")
                failures.append(exc.category)

        matched_delivery = "sent" if all(value in {"sent", "already_delivered"} for value in results) else (
            "partial" if any(value in {"sent", "already_delivered"} for value in results) else "failed"
        )
        _log_decision(
            context, correlation_id, matched=True, trigger=trigger,
            rule_public_id=winner.public_id, delivery=matched_delivery,
        )
        return AutomationRuntimeResult(
            handled=True, matched=True, delivery_status=matched_delivery,
            outbound_message_public_id=outbound_ids[0] if outbound_ids else None,
            rule_public_id=winner.public_id,
            safe_reason=failures[0] if failures else None,
        )


def _trigger_type(message: ConversationMessage) -> str:
    event_kind = (message.metadata_json or {}).get("instagram_event_kind")
    if event_kind == "story_reply":
        return "STORY_REPLY_KEYWORD"
    if event_kind == "comment":
        return "COMMENT_KEYWORD"
    return "DM_KEYWORD"


def _log_decision(
    context: TenantStoreContext,
    correlation_id: str | None,
    *,
    matched: bool,
    trigger: str,
    rule_public_id: str | None = None,
    delivery: str | None = None,
) -> None:
    logger.info(
        "instagram_automation_rule_evaluated",
        extra={
            "tenant_public_id": context.tenant_public_id,
            "store_public_id": context.store_public_id,
            "correlation_id": correlation_id,
            "automation_matched": matched,
            "automation_rule_public_id": rule_public_id,
            "automation_trigger_type": trigger,
            "automation_delivery_result": delivery,
            "ai_fallback": not matched,
        },
    )
