"""Public-only Instagram onboarding contracts."""

from datetime import datetime

from pydantic import BaseModel


class InstagramConnectResponse(BaseModel):
    authorization_url: str
    expires_at: datetime


class InstagramAccountRead(BaseModel):
    connection_public_id: str
    instagram_username: str | None
    status: str
    token_configured: bool
    connected_at: datetime | None


class InstagramStatusResponse(BaseModel):
    entitled: bool
    account_limit: int
    connected_accounts: int
    accounts: list[InstagramAccountRead]


class InstagramCallbackResponse(BaseModel):
    connection_public_id: str
    tenant_public_id: str
    store_public_id: str
    instagram_username: str | None
    status: str
