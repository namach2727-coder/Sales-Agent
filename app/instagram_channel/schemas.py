"""Public-only REST schemas for the Instagram channel boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


ConnectionStatus = Literal[
    "pending", "active", "degraded", "disconnected", "revoked", "archived"
]
DeliveryStatus = Literal[
    "received", "rejected", "duplicate", "accepted", "processed", "failed", "ignored"
]
EventType = Literal["messaging", "comments", "unsupported"]
EventStatus = Literal["ready", "ignored", "failed"]


class Page(BaseModel):
    page: int
    page_size: int
    total: int


class InstagramConnectionCreate(BaseModel):
    expected_revision: Literal[0]
    meta_app_id: str | None = Field(default=None, max_length=100)
    facebook_page_id: str | None = Field(default=None, max_length=200)
    instagram_account_id: str = Field(min_length=1, max_length=200)
    instagram_username: str | None = Field(default=None, max_length=100)
    external_account_name: str | None = Field(default=None, max_length=200)


class InstagramConnectionUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    meta_app_id: str | None = Field(default=None, max_length=100)
    facebook_page_id: str | None = Field(default=None, max_length=200)
    instagram_account_id: str | None = Field(default=None, max_length=200)
    instagram_username: str | None = Field(default=None, max_length=100)
    external_account_name: str | None = Field(default=None, max_length=200)
    status_reason: str | None = Field(default=None, max_length=500)


class InstagramTokenRotate(BaseModel):
    expected_revision: int = Field(ge=1)
    access_token: SecretStr
    token_type: str | None = Field(default=None, max_length=50)
    token_expires_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list, max_length=100)


class InstagramConnectionAction(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=500)


class InstagramConnectionRead(BaseModel):
    public_id: str
    meta_app_id: str | None
    facebook_page_id: str | None
    instagram_account_id: str
    instagram_username: str | None
    external_account_name: str | None
    status: ConnectionStatus
    status_reason: str | None
    connected_at: datetime | None
    disconnected_at: datetime | None
    last_verified_at: datetime | None
    last_webhook_received_at: datetime | None
    token_configured: bool
    token_type: str | None
    token_expires_at: datetime | None
    token_scopes: list[str]
    token_updated_at: datetime | None
    revision: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class InstagramConnectionPage(Page):
    items: list[InstagramConnectionRead]


class InstagramWebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    provider: str
    external_delivery_key: str | None
    payload_hash: str
    signature_algorithm: str | None
    signature_valid: bool
    verification_state: str
    processing_status: DeliveryStatus
    failure_category: str | None
    safe_failure_detail: str | None
    received_at: datetime
    processed_at: datetime | None
    retry_count: int
    correlation_id: str | None


class InstagramWebhookDeliveryPage(Page):
    items: list[InstagramWebhookDeliveryRead]


class InstagramInboundEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    provider: str
    provider_event_id: str | None
    event_type: EventType
    object_type: str
    external_object_id: str | None
    external_sender_id: str | None
    external_recipient_id: str | None
    provider_event_at: datetime | None
    normalized_payload: dict[str, object]
    processing_status: EventStatus
    occurred_at: datetime
    received_at: datetime
    created_at: datetime


class InstagramInboundEventPage(Page):
    items: list[InstagramInboundEventRead]


class InstagramAIFlowReceipt(BaseModel):
    acknowledged: bool
    inbound_status: str
    ai_status: Literal["not_started", "skipped", "completed", "failed"]
    delivery_status: Literal["not_started", "skipped", "sent", "failed"]
    duplicate: bool
    ignored: bool
    correlation_id: str
    conversation_public_id: str | None = None
    inbound_message_public_id: str | None = None
    assistant_message_public_id: str | None = None
    safe_reason: str | None = None


class InstagramWebhookReceipt(BaseModel):
    status: Literal["accepted", "duplicate", "ignored"]
    duplicate: bool
    event_count: int = Field(ge=0)
    flows: list[InstagramAIFlowReceipt] = Field(default_factory=list)
