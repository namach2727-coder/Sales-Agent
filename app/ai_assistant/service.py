"""Server-authoritative AI Assistant state and privacy-safe usage aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.conversation_core.models import ConversationMessage
from app.models import SaasPlan, Store, TenantAuditLog, TenantSubscription, utc_now
from app.module_catalog import effective_product_subscriptions


class AIAssistantError(Exception):
    code = "ai_assistant_error"


class AIAssistantConflict(AIAssistantError):
    code = "stale_revision"


@dataclass(frozen=True, slots=True)
class AIUsageSummary:
    request_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_limit: int | None
    token_limit: int | None
    period_start: datetime | None
    period_end: datetime | None


class AIAssistantService:
    def __init__(self, session: Session, *, tenant_id: int, store_id: int, actor_identity_id: int | None = None) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.store_id = store_id
        self.actor_identity_id = actor_identity_id

    def read(self) -> Store:
        store = self.session.get(Store, self.store_id)
        if store is None or store.tenant_id != self.tenant_id:
            raise AIAssistantError("store not found")
        return store

    def update(self, *, enabled: bool, expected_revision: int) -> Store:
        store = self.read()
        if store.ai_revision != expected_revision:
            raise AIAssistantConflict("AI settings revision does not match")
        changed_at = utc_now()
        result = self.session.execute(
            update(Store).where(Store.id == self.store_id, Store.tenant_id == self.tenant_id, Store.ai_revision == expected_revision).values(
                ai_enabled=enabled, ai_revision=expected_revision + 1, updated_at=changed_at
            )
        )
        if result.rowcount != 1:
            self.session.rollback()
            raise AIAssistantConflict("AI settings revision does not match")
        self.session.add(TenantAuditLog(
            tenant_id=self.tenant_id, store_id=self.store_id,
            actor_identity_id=self.actor_identity_id,
            action="store.ai_enabled" if enabled else "store.ai_disabled",
            target_type="store", target_public_id=store.public_id,
            details_json={"enabled": enabled, "previous_revision": expected_revision, "revision": expected_revision + 1},
        ))
        self.session.commit()
        self.session.expire(store)
        return self.read()

    def usage(self) -> AIUsageSummary:
        subscriptions = effective_product_subscriptions(self.session, tenant_id=self.tenant_id, store_id=self.store_id)
        eligible: list[tuple[TenantSubscription, SaasPlan]] = []
        for subscription in subscriptions:
            plan = self.session.get(SaasPlan, subscription.plan_id)
            if plan is not None and plan.product_family in {"AI_ASSISTANT", "LEGACY_BUNDLE"}:
                eligible.append((subscription, plan))
        period_start = min((item.starts_at for item, _ in eligible), default=None)
        period_end_values = [item.current_period_end for item, _ in eligible if item.current_period_end is not None]
        period_end = max(period_end_values, default=None)
        limits = [item.limits_json or {} for item, _ in eligible]
        request_limit = _combined_limit(limits, "ai_request_limit")
        token_limit = _combined_limit(limits, "ai_token_limit")
        statement = select(ConversationMessage.metadata_json).where(
            ConversationMessage.tenant_id == self.tenant_id,
            ConversationMessage.store_id == self.store_id,
            ConversationMessage.direction == "outbound",
        )
        if period_start is not None:
            statement = statement.where(ConversationMessage.occurred_at >= period_start)
        if period_end is not None:
            statement = statement.where(ConversationMessage.occurred_at < period_end)
        request_count = input_tokens = output_tokens = total_tokens = 0
        for metadata in self.session.scalars(statement).all():
            if not isinstance(metadata, dict) or metadata.get("source") != "ai_response_orchestrator":
                continue
            request_count += 1
            input_tokens += _safe_count(metadata.get("llm_input_tokens"))
            output_tokens += _safe_count(metadata.get("llm_output_tokens"))
            total_tokens += _safe_count(metadata.get("llm_total_tokens"))
        return AIUsageSummary(request_count, input_tokens, output_tokens, total_tokens, request_limit, token_limit, period_start, period_end)


def ai_is_enabled(session: Session, *, tenant_id: int, store_id: int) -> bool:
    store = session.get(Store, store_id)
    return bool(store is not None and store.tenant_id == tenant_id and store.ai_enabled)


def _safe_count(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _combined_limit(limits: list[dict[str, object]], key: str) -> int | None:
    values = [_safe_count(item[key]) for item in limits if key in item and item[key] is not None]
    return sum(values) if values else None
