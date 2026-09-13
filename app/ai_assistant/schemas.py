from datetime import datetime

from pydantic import BaseModel, Field


class AISettingsRead(BaseModel):
    enabled: bool
    revision: int
    updated_at: datetime


class AISettingsUpdate(BaseModel):
    enabled: bool
    expected_revision: int = Field(ge=1)


class AIUsageRead(BaseModel):
    request_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_limit: int | None
    token_limit: int | None
    remaining_requests: int | None
    remaining_tokens: int | None
    period_start: datetime | None
    period_end: datetime | None
