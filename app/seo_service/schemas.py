from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SeoGoogleConnectRead(BaseModel):
    authorization_url: str
    expires_at: datetime


class SeoGoogleStatusRead(BaseModel):
    connected: bool
    status: str
    google_email: str | None = None
    connected_at: datetime | None = None
    property_count: int = 0
    selected_property: str | None = None


class SeoGooglePropertyRead(BaseModel):
    public_id: str
    property_uri: str
    permission_level: str
    is_selected: bool


class SeoSelectPropertyRequest(BaseModel):
    property_public_id: str = Field(min_length=36, max_length=36)


class SeoGoogleCallbackRead(BaseModel):
    connected: bool
    google_email: str | None
    discovered_properties: int
