"""Bounded no-code rules and full version snapshots."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
try:
    from .api_actions import ApiCallInput
except ImportError:
    from api_actions import ApiCallInput


class RuleInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    keyword: str = Field(min_length=1, max_length=120)
    match_mode: Literal['exact', 'contains'] = 'exact'
    response_text: str = Field(min_length=1, max_length=4096)
    action_type: Literal['text', 'api'] = 'text'
    enabled: bool = True
    show_button: bool | None = None
    api: ApiCallInput | None = None
    source_rule_id: UUID | None = None

    @model_validator(mode='after')
    def check_rule(self):
        if not self.keyword.strip() or not self.response_text.strip(): raise ValueError('Blank rule')
        if (self.action_type == 'api') != (self.api is not None): raise ValueError('Action settings mismatch')
        if self.show_button and len(self.keyword) > 64: raise ValueError('Button label too long')
        return self


class DraftInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    greeting: str = Field(min_length=1, max_length=4096)
    fallback_reply: str = Field(min_length=1, max_length=4096)
    replace_reply_buttons: bool = False
    rules: list[RuleInput] | None = Field(default=None, max_length=100)
    base_version: int | None = Field(default=None, ge=0)

    @model_validator(mode='after')
    def check_draft(self):
        if not self.greeting.strip() or not self.fallback_reply.strip(): raise ValueError('Blank message')
        if self.rules and sum(bool(r.show_button) for r in self.rules) > 12: raise ValueError('At most 12 menu buttons')
        return self


class PreviewInput(DraftInput):
    """An explicit unsaved snapshot; never loads saved API credentials."""
    rules: list[RuleInput] = Field(max_length=100)
    text: str = Field(min_length=1, max_length=4096)

    @model_validator(mode='after')
    def check_preview(self):
        if not self.text.strip():
            raise ValueError('Blank test message')
        return self
