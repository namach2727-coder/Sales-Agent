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
    platform_role_codes: list[str] = Field(default_factory=list)


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
    product_family: str
    description: str | None
    billing_unit: str
    ai_request_limit: int | None
    ai_token_limit: int | None


class AdminPlanWrite(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,49}$")
    name: str = Field(min_length=1, max_length=120)
    product_family: str
    description: str | None = Field(default=None, max_length=1000)
    price_amount: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    duration_days: int | None = Field(default=None, ge=1)
    billing_unit: str = Field(default="day", pattern=r"^(day|month)$")
    automation_limit: int = Field(default=0, ge=0)
    reply_limit: int = Field(default=0, ge=0)
    instagram_account_limit: int = Field(default=1, ge=0)
    ai_request_limit: int | None = Field(default=None, ge=0)
    ai_token_limit: int | None = Field(default=None, ge=0)
    is_active: bool = False
    is_purchasable: bool = False
    display_order: int = Field(default=0, ge=0)
    trial_eligible: bool = False


class AdminPlanUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price_amount: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    duration_days: int | None = Field(default=None, ge=1)
    billing_unit: str | None = Field(default=None, pattern=r"^(day|month)$")
    automation_limit: int | None = Field(default=None, ge=0)
    reply_limit: int | None = Field(default=None, ge=0)
    instagram_account_limit: int | None = Field(default=None, ge=0)
    ai_request_limit: int | None = Field(default=None, ge=0)
    ai_token_limit: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_purchasable: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    trial_eligible: bool | None = None


class AdminPlanRead(PlanRead):
    is_active: bool
    is_purchasable: bool
    display_order: int
    trial_eligible: bool
    revision: int


class AdminGrantCreate(BaseModel):
    tenant_public_id: str = Field(min_length=36, max_length=36)
    store_public_id: str = Field(min_length=36, max_length=36)
    plan_public_id: str = Field(min_length=36, max_length=36)
    expires_at: datetime | None = None


class AdminRevokeInput(BaseModel):
    expected_status: str = "active"


class AdminSubscriptionRead(BaseModel):
    public_id: str
    tenant_public_id: str
    store_public_id: str
    plan_public_id: str
    plan_code: str
    product_family: str
    source: str
    status: str
    limits: dict[str, int]
    starts_at: datetime
    current_period_end: datetime | None


class AdminCustomerStoreRead(BaseModel):
    tenant_public_id: str
    tenant_name: str
    store_public_id: str
    store_name: str
    store_status: str
    effective_capabilities: list[str]


class AdminCommerceAuditRead(BaseModel):
    source: str
    actor_display_name: str | None
    action: str
    target_type: str
    target_public_id: str
    changed_fields: list[str] = Field(default_factory=list)
    before: dict[str, object] = Field(default_factory=dict)
    after: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class ProductSubscriptionRead(BaseModel):
    product_family: str
    active: bool
    subscription_public_id: str | None = None
    plan_public_id: str | None = None
    plan_code: str | None = None
    source: str | None = None
    status: str | None = None
    limits: dict[str, int] = Field(default_factory=dict)
    starts_at: datetime | None = None
    current_period_end: datetime | None = None


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


class AdminPaymentRead(PaymentRead):
    tenant_name: str
    store_name: str
    plan_code: str
    product_family: str
    order_status: str
    submitted_at: datetime | None


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
    effective_capabilities: list[str]
    products: list[ProductSubscriptionRead] = Field(default_factory=list)
    legacy_bundle: ProductSubscriptionRead | None = None
