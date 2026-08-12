"""Public-only contracts for customer registration and SaaS commerce."""

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=4096)
    display_name: str = Field(min_length=2, max_length=200)
    tenant_name: str = Field(min_length=2, max_length=200)
    tenant_slug: str = Field(min_length=2, max_length=63)
    store_name: str = Field(min_length=2, max_length=200)
    store_slug: str = Field(min_length=2, max_length=63)


class RegisterResponse(BaseModel):
    email: str
    display_name: str
    tenant_public_id: str
    tenant_slug: str
    store_public_id: str
    store_slug: str


class PublicMembership(BaseModel):
    tenant_public_id: str
    tenant_slug: str
    status: str


class PublicPrincipal(BaseModel):
    email: str
    display_name: str
    session_public_id: str
    authenticated_at: datetime
    tenant_memberships: list[PublicMembership]


class PublicLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    principal: PublicPrincipal


class PlanRead(BaseModel):
    public_id: str
    code: str
    name: str
    price_amount: int
    currency: str
    reply_limit: int
    automation_limit: int
    instagram_account_limit: int
    duration_days: int | None


class OrderCreate(BaseModel):
    plan_public_id: str = Field(min_length=36, max_length=36)


class OrderRead(BaseModel):
    public_id: str
    tenant_public_id: str
    store_public_id: str
    plan_public_id: str
    plan_code: str
    status: str
    price_amount: int
    currency: str
    created_at: datetime


class CardTransferCreate(BaseModel):
    order_public_id: str = Field(min_length=36, max_length=36)


class PaymentRead(BaseModel):
    public_id: str
    order_public_id: str
    status: str
    amount: int
    currency: str
    revision: int
    receipt_configured: bool
    created_at: datetime


class CardTransferInstructions(BaseModel):
    payment: PaymentRead
    card_number: str
    account_number: str
    account_name: str
    bank_name: str
    instructions: str


class PaymentDecision(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=500)


class SubscriptionRead(BaseModel):
    public_id: str
    tenant_public_id: str
    store_public_id: str
    plan_public_id: str
    plan_code: str
    status: str
    limits: dict[str, int]
    starts_at: datetime
    current_period_end: datetime | None
