"""Public REST schemas for Business Profile and Knowledge.

Internal database, Tenant, Store, and actor identifiers are intentionally absent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


KnowledgeStatus = Literal["draft", "published", "archived"]
PolicyType = Literal[
    "shipping",
    "returns",
    "refunds",
    "payment",
    "warranty",
    "service",
    "privacy",
    "custom",
]
EntryType = Literal["fact", "instruction", "reference", "custom"]
Keyword = Annotated[str, Field(min_length=1, max_length=100)]


class Page(BaseModel):
    page: int
    page_size: int
    total: int


class CreateRevision(BaseModel):
    expected_revision: Literal[0]


class UpdateRevision(BaseModel):
    expected_revision: int = Field(ge=1)


class LifecycleTransition(UpdateRevision):
    target_status: KnowledgeStatus


class BusinessProfileCreate(CreateRevision):
    display_name: str = Field(min_length=1, max_length=200)
    business_category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=20_000)
    support_phone: str | None = Field(default=None, max_length=64)
    support_email: str | None = Field(default=None, max_length=320)
    website_url: str | None = Field(default=None, max_length=2048)
    address_text: str | None = Field(default=None, max_length=4_000)
    working_hours_text: str | None = Field(default=None, max_length=4_000)


class BusinessProfileUpdate(UpdateRevision):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    business_category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=20_000)
    support_phone: str | None = Field(default=None, max_length=64)
    support_email: str | None = Field(default=None, max_length=320)
    website_url: str | None = Field(default=None, max_length=2048)
    address_text: str | None = Field(default=None, max_length=4_000)
    working_hours_text: str | None = Field(default=None, max_length=4_000)


class BusinessProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    display_name: str
    business_category: str | None
    description: str | None
    support_phone: str | None
    support_email: str | None
    website_url: str | None
    address_text: str | None
    working_hours_text: str | None
    status: KnowledgeStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class BusinessPolicyCreate(CreateRevision):
    code: str = Field(min_length=1, max_length=100)
    policy_type: PolicyType
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    priority: int = Field(default=100, ge=0, le=10_000)


class BusinessPolicyUpdate(UpdateRevision):
    code: str | None = Field(default=None, min_length=1, max_length=100)
    policy_type: PolicyType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20_000)
    priority: int | None = Field(default=None, ge=0, le=10_000)


class BusinessPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    code: str
    policy_type: PolicyType
    title: str
    content: str
    priority: int
    status: KnowledgeStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class BusinessPolicyPage(Page):
    items: list[BusinessPolicyRead]


class BusinessFAQCreate(CreateRevision):
    question: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=20_000)
    keywords: list[Keyword] = Field(default_factory=list, max_length=25)
    priority: int = Field(default=100, ge=0, le=10_000)


class BusinessFAQUpdate(UpdateRevision):
    question: str | None = Field(default=None, min_length=1, max_length=500)
    answer: str | None = Field(default=None, min_length=1, max_length=20_000)
    keywords: list[Keyword] | None = Field(default=None, max_length=25)
    priority: int | None = Field(default=None, ge=0, le=10_000)


class BusinessFAQRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    question: str
    answer: str
    keywords: list[str]
    priority: int
    status: KnowledgeStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class BusinessFAQPage(Page):
    items: list[BusinessFAQRead]


class BusinessKnowledgeEntryCreate(CreateRevision):
    slug: str = Field(min_length=1, max_length=100)
    entry_type: EntryType
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    keywords: list[Keyword] = Field(default_factory=list, max_length=25)
    priority: int = Field(default=100, ge=0, le=10_000)


class BusinessKnowledgeEntryUpdate(UpdateRevision):
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    entry_type: EntryType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=20_000)
    keywords: list[Keyword] | None = Field(default=None, max_length=25)
    priority: int | None = Field(default=None, ge=0, le=10_000)


class BusinessKnowledgeEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    slug: str
    entry_type: EntryType
    title: str
    content: str
    keywords: list[str]
    priority: int
    status: KnowledgeStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None


class BusinessKnowledgeEntryPage(Page):
    items: list[BusinessKnowledgeEntryRead]
