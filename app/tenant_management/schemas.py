from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=63)


class TenantBootstrap(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=200)
    tenant_slug: str = Field(min_length=2, max_length=63)
    store_name: str = Field(min_length=2, max_length=200)
    store_slug: str = Field(min_length=2, max_length=63)
    owner_email: str = Field(min_length=3, max_length=320)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=63)


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime
    suspended_at: datetime | None
    archived_at: datetime | None


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=63)
    timezone: str = Field(default="Asia/Tehran", max_length=64)
    locale: str = Field(default="fa-IR", max_length=16)
    currency_code: str = Field(default="IRR", min_length=3, max_length=3)
    subdomain: str | None = Field(default=None, max_length=63)
    custom_domain: str | None = Field(default=None, max_length=255)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=63)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    subdomain: str | None = Field(default=None, max_length=63)
    custom_domain: str | None = Field(default=None, max_length=255)


class StoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    slug: str
    status: str
    timezone: str
    locale: str
    currency_code: str
    subdomain: str | None
    custom_domain: str | None
    created_at: datetime
    updated_at: datetime
    suspended_at: datetime | None
    archived_at: datetime | None


class MembershipCreate(BaseModel):
    identity_email: str = Field(min_length=3, max_length=320)
    role_codes: list[str] = Field(min_length=1, max_length=10)
    all_store_access: bool = False
    store_public_ids: list[str] = Field(default_factory=list, max_length=100)
    status: str = Field(default="active", pattern="^(invited|active)$")

    @field_validator("identity_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().casefold()


class MembershipStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|suspended|revoked)$")


class MembershipRead(BaseModel):
    public_id: str
    display_name: str
    status: str
    all_store_access: bool
    role_codes: list[str]
    store_public_ids: list[str]


class Page(BaseModel):
    page: int
    page_size: int
    total: int


class TenantPage(Page):
    items: list[TenantRead]


class StorePage(Page):
    items: list[StoreRead]
