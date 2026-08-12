from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
    role: Literal["customer", "assistant", "system"]
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
