from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    app_name: str = "Sales Assistant MVP"
    app_env: str = "development"
    database_url: str = "sqlite:///./sales_assistant.db"
    # Deprecated compatibility setting. Seed execution is now CLI-only.
    seed_demo_data: bool = False
    meta_verify_token: str = ""
    meta_access_token: str = ""
    meta_app_secret: str = ""
    meta_ig_user_id: str = ""
    meta_api_version: str = "v24.0"
    meta_send_enabled: bool = False
    meta_signature_required: bool = True
    meta_content_publish_enabled: bool = False
    public_media_base_url: str = ""
    media_signing_secret: str = ""
    media_storage_root: str = "./private_media"
    tenant_base_domain: str = ""
    tenant_url_scheme: str = "https"
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_send_enabled: bool = False
    telegram_polling_enabled: bool = False
    telegram_poll_timeout: int = 25
    manychat_dynamic_block_secret: str = ""
    openai_api_key: str = ""
    authentication_enabled: bool = True
    legacy_admin_adapter_enabled: bool = True
    session_ttl_minutes: int = Field(default=480, ge=5, le=43200)
    session_cookie_name: str = Field(default="sales_agent_session", min_length=3, max_length=64)
    session_cookie_secure: bool = True
    password_min_length: int = Field(default=12, ge=10, le=128)
    password_max_length: int = Field(default=1024, ge=128, le=4096)
    login_max_failures: int = Field(default=5, ge=2, le=100)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1440)

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
