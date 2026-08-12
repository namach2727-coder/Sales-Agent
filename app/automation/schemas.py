from datetime import datetime

from pydantic import BaseModel, Field


class AutomationStateRead(BaseModel):
    enabled: bool
    revision: int
    updated_at: datetime


class AutomationStateUpdate(BaseModel):
    enabled: bool
    expected_revision: int = Field(ge=1)
