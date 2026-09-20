from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConversationRead(BaseModel):
    public_id: str
    status: str
    subject: str | None
    participant_display_name: str | None
    participant_username: str | None
    last_message_at: datetime | None
    last_inbound_message_at: datetime | None
    last_outbound_message_at: datetime | None
    message_count: int
    revision: int
    created_at: datetime
    updated_at: datetime


class ConversationPage(BaseModel):
    items: list[ConversationRead]
    page: int
    page_size: int
    total: int


class ConversationMessageRead(BaseModel):
    public_id: str
    direction: Literal["inbound", "outbound", "system"]
    role: Literal["customer", "assistant", "human", "system"]
    content_type: str
    content: str | None
    delivery_status: str | None
    occurred_at: datetime
    created_at: datetime


class ConversationMessagePage(BaseModel):
    items: list[ConversationMessageRead]
    page: int
    page_size: int
    total: int


class ManualMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )


class OutboundReconciliationDecision(BaseModel):
    decision: Literal[
        "CONFIRM_SENT", "CONFIRM_NOT_SENT", "LEAVE_UNRESOLVED"
    ]


class OutboundReconciliationRead(BaseModel):
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
    allowed_actions: list[str]
