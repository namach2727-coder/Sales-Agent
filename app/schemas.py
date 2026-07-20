from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: float
    is_available: bool
    created_at: datetime


class FAQRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_user_id: str
    name: str | None
    phone: str
    created_at: datetime


class OrderRead(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    phone: str
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    status: str
    created_at: datetime


class ChatRequest(BaseModel):
    instagram_user_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4096)
    customer_name: str | None = Field(default=None, max_length=200)


class ChatResponse(BaseModel):
    reply: str
    customer_id: int
    product: ProductRead | None = None
    order: OrderRead | None = None
    phone_saved: bool = False
    needs_human: bool = False


class InstagramStatus(BaseModel):
    mode: str
    webhook_path: str
    api_version: str
    verify_token_configured: bool
    app_secret_configured: bool
    access_token_configured: bool
    instagram_user_id_configured: bool
    signature_required: bool
    send_enabled: bool
    ready_to_receive: bool
    ready_to_send: bool


class TelegramStatus(BaseModel):
    mode: str
    receive_mode: str
    webhook_path: str
    bot_token_configured: bool
    webhook_secret_configured: bool
    polling_enabled: bool
    send_enabled: bool
    ready_to_receive: bool
    ready_to_send: bool
