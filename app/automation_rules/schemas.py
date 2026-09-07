from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TriggerType = Literal["DM_KEYWORD", "STORY_REPLY_KEYWORD", "COMMENT_KEYWORD"]
MatchType = Literal["EXACT", "CONTAINS", "STARTS_WITH"]
ActionType = Literal["SEND_MESSAGE", "SEND_PRIVATE_MESSAGE"]
Keyword = Annotated[str, Field(min_length=1, max_length=100)]


class ActionPayload(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("action text cannot be empty")
        return value


class RuleFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    trigger_type: TriggerType
    match_type: MatchType
    keywords: list[Keyword] = Field(min_length=1, max_length=25)
    action_type: ActionType
    action_payload: ActionPayload
    priority: int = Field(default=100, ge=0, le=10_000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("keywords cannot contain empty values")
        return cleaned

    @model_validator(mode="after")
    def validate_action(self):
        expected = "SEND_PRIVATE_MESSAGE" if self.trigger_type == "COMMENT_KEYWORD" else "SEND_MESSAGE"
        if self.action_type != expected:
            raise ValueError("action type is incompatible with trigger type")
        return self


class AutomationRuleCreate(RuleFields):
    expected_revision: Literal[0]


class AutomationRuleUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    enabled: bool | None = None
    trigger_type: TriggerType | None = None
    match_type: MatchType | None = None
    keywords: list[Keyword] | None = Field(default=None, min_length=1, max_length=25)
    action_type: ActionType | None = None
    action_payload: ActionPayload | None = None
    priority: int | None = Field(default=None, ge=0, le=10_000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("keywords cannot contain empty values")
        return cleaned


class AutomationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    name: str
    enabled: bool
    trigger_type: TriggerType
    match_type: MatchType
    keywords: list[str]
    action_type: ActionType
    action_payload: ActionPayload
    priority: int
    revision: int
    created_at: datetime
    updated_at: datetime


class AutomationRulePage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AutomationRuleRead]
