from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.automation_rules.models import AutomationRule
from app.models import TenantAuditLog, utc_now
from app.module_catalog import effective_subscription, has_capability


class AutomationRuleError(Exception):
    code = "automation_rule_error"


class AutomationRuleNotFound(AutomationRuleError):
    code = "not_found"


class AutomationRuleForbidden(AutomationRuleError):
    code = "capability_required"


class AutomationRuleConflict(AutomationRuleError):
    code = "stale_revision"


class AutomationRuleLimitReached(AutomationRuleError):
    code = "automation_limit_reached"


class AutomationRuleValidation(AutomationRuleError):
    code = "validation_error"


class AutomationRuleService:
    def __init__(self, session: Session, *, tenant_id: int, store_id: int, actor_identity_id: int | None):
        self.session = session
        self.tenant_id = tenant_id
        self.store_id = store_id
        self.actor_identity_id = actor_identity_id

    def _authorize(self) -> None:
        if not has_capability(
            self.session,
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            capability_code="instagram_automation",
        ):
            raise AutomationRuleForbidden("instagram automation capability is required")

    def _resource(self, public_id: str) -> AutomationRule:
        self._authorize()
        item = self.session.scalar(select(AutomationRule).where(
            AutomationRule.public_id == public_id,
            AutomationRule.tenant_id == self.tenant_id,
            AutomationRule.store_id == self.store_id,
        ))
        if item is None:
            raise AutomationRuleNotFound("resource not found")
        return item

    @staticmethod
    def _validate_combination(trigger_type: str, action_type: str) -> None:
        expected = "SEND_PRIVATE_MESSAGE" if trigger_type == "COMMENT_KEYWORD" else "SEND_MESSAGE"
        if action_type != expected:
            raise AutomationRuleValidation("action type is incompatible with trigger type")

    def _audit(self, action: str, item: AutomationRule, details: dict[str, object]) -> None:
        self.session.add(TenantAuditLog(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            actor_identity_id=self.actor_identity_id,
            action=action,
            target_type="automation_rule",
            target_public_id=item.public_id,
            details_json=details,
        ))

    def list(self, *, page: int, page_size: int) -> tuple[list[AutomationRule], int]:
        self._authorize()
        condition = (AutomationRule.tenant_id == self.tenant_id, AutomationRule.store_id == self.store_id)
        total = self.session.scalar(select(func.count(AutomationRule.id)).where(*condition)) or 0
        items = list(self.session.scalars(select(AutomationRule).where(*condition).order_by(
            AutomationRule.priority.desc(), AutomationRule.id.asc()
        ).offset((page - 1) * page_size).limit(page_size)).all())
        return items, total

    def get(self, public_id: str) -> AutomationRule:
        return self._resource(public_id)

    def create(self, **values) -> AutomationRule:
        self._authorize()
        if values.pop("expected_revision") != 0:
            raise AutomationRuleConflict("new resources require expected_revision 0")
        subscription = effective_subscription(self.session, tenant_id=self.tenant_id, store_id=self.store_id)
        limit = None if subscription is None else (subscription.limits_json or {}).get("automation_limit")
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise AutomationRuleForbidden("effective automation limit is unavailable")
        count = self.session.scalar(select(func.count(AutomationRule.id)).where(
            AutomationRule.tenant_id == self.tenant_id, AutomationRule.store_id == self.store_id
        )) or 0
        if count >= limit:
            raise AutomationRuleLimitReached("automation rule limit reached")
        action_payload = values["action_payload"]
        values["action_payload"] = (
            action_payload.model_dump()
            if hasattr(action_payload, "model_dump")
            else dict(action_payload)
        )
        self._validate_combination(values["trigger_type"], values["action_type"])
        item = AutomationRule(tenant_id=self.tenant_id, store_id=self.store_id, **values)
        self.session.add(item)
        self.session.flush()
        self._audit("automation_rule.created", item, {"revision": 1})
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(self, public_id: str, **values) -> AutomationRule:
        item = self._resource(public_id)
        expected_revision = values.pop("expected_revision")
        if item.revision != expected_revision:
            raise AutomationRuleConflict("resource revision does not match")
        supplied = {key: value for key, value in values.items() if value is not None}
        trigger = supplied.get("trigger_type", item.trigger_type)
        action = supplied.get("action_type", item.action_type)
        self._validate_combination(trigger, action)
        if "action_payload" in supplied:
            action_payload = supplied["action_payload"]
            supplied["action_payload"] = (
                action_payload.model_dump()
                if hasattr(action_payload, "model_dump")
                else dict(action_payload)
            )
        if not supplied:
            raise AutomationRuleValidation("at least one field must be updated")
        result = self.session.execute(update(AutomationRule).where(
            AutomationRule.id == item.id,
            AutomationRule.tenant_id == self.tenant_id,
            AutomationRule.store_id == self.store_id,
            AutomationRule.revision == expected_revision,
        ).values(**supplied, revision=expected_revision + 1, updated_at=utc_now()))
        if result.rowcount != 1:
            self.session.rollback()
            raise AutomationRuleConflict("resource revision does not match")
        self._audit("automation_rule.updated", item, {"revision": expected_revision + 1})
        self.session.commit()
        return self._resource(public_id)

    def delete(self, public_id: str, *, expected_revision: int) -> None:
        item = self._resource(public_id)
        if item.revision != expected_revision:
            raise AutomationRuleConflict("resource revision does not match")
        self._audit("automation_rule.deleted", item, {"revision": item.revision})
        self.session.execute(delete(AutomationRule).where(
            AutomationRule.id == item.id,
            AutomationRule.tenant_id == self.tenant_id,
            AutomationRule.store_id == self.store_id,
            AutomationRule.revision == expected_revision,
        ))
        self.session.commit()
