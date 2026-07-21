"""Sanitized authentication API contracts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=4096)


class MembershipRead(BaseModel):
    tenant_id: int
    tenant_slug: str
    status: str


class PrincipalRead(BaseModel):
    user_id: int
    email: str
    display_name: str
    session_id: str
    authenticated_at: datetime
    tenant_memberships: list[MembershipRead]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    principal: PrincipalRead


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None


class OperationResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    code: str
    message: str
