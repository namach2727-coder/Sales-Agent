from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models import new_public_id, utc_now


class AutomationRule(Base):
    """Store-owned deterministic rule definition; execution belongs to Phase C."""

    __tablename__ = "automation_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ("store_id", "tenant_id"),
            ("stores.id", "stores.tenant_id"),
            name="fk_automation_rules_store_tenant",
        ),
        CheckConstraint(
            "trigger_type IN ('DM_KEYWORD', 'STORY_REPLY_KEYWORD', 'COMMENT_KEYWORD')",
            name="ck_automation_rules_trigger_type",
        ),
        CheckConstraint(
            "match_type IN ('EXACT', 'CONTAINS', 'STARTS_WITH')",
            name="ck_automation_rules_match_type",
        ),
        CheckConstraint(
            "action_type IN ('SEND_MESSAGE', 'SEND_PRIVATE_MESSAGE')",
            name="ck_automation_rules_action_type",
        ),
        CheckConstraint("priority >= 0 AND priority <= 10000", name="ck_automation_rules_priority"),
        CheckConstraint("revision >= 1", name="ck_automation_rules_revision"),
        Index("ix_automation_rules_tenant_store_priority", "tenant_id", "store_id", "priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), default=new_public_id, unique=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String(40))
    match_type: Mapped[str] = mapped_column(String(30))
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    action_type: Mapped[str] = mapped_column(String(40))
    action_payload: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
