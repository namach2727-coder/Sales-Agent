from __future__ import annotations

from functools import lru_cache
import base64
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
DEPLOYED_ENVIRONMENTS = frozenset({"integration", "uat", "production"})
PLACEHOLDER_VALUES = frozenset({"", "replace-me", "changeme", "change-me", "secret"})


class Settings(BaseSettings):
    app_name: str = "Sales Assistant MVP"
    app_env: Literal["development", "test", "integration", "uat", "production", "demo"] = "development"
    app_version: str = "0.10.0"
    build_sha: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    web_concurrency: int = Field(default=2, ge=1, le=32)

    database_url: str = "sqlite:///./sales_assistant.db"
    database_url_file: str | None = None
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)
    database_pool_timeout: int = Field(default=30, ge=1, le=300)
    database_pool_recycle: int = Field(default=1800, ge=60, le=86400)
    database_connect_timeout: int = Field(default=10, ge=1, le=120)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["auto", "text", "json"] = "auto"
    trusted_hosts: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver", "*"])
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    forwarded_allow_ips: str = "127.0.0.1"
    force_https: bool = False
    security_headers_enabled: bool = True
    application_secret: SecretStr = SecretStr("")
    application_secret_file: str | None = None

    # Deprecated compatibility setting. Seed execution is now CLI-only.
    seed_demo_data: bool = False
    meta_verify_token: str = ""
    meta_access_token: str = ""
    meta_access_token_file: str | None = None
    meta_app_secret: str = ""
    meta_app_secret_file: str | None = None
    instagram_token_encryption_key: SecretStr = SecretStr("")
    instagram_token_encryption_key_file: str | None = None
    meta_ig_user_id: str = ""
    meta_api_version: str = "v24.0"
    meta_send_enabled: bool = False
    meta_signature_required: bool = True
    meta_content_publish_enabled: bool = False
    public_media_base_url: str = ""
    media_signing_secret: str = ""
    media_signing_secret_file: str | None = None
    media_storage_root: str = "./private_media"
    tenant_base_domain: str = ""
    tenant_url_scheme: Literal["http", "https"] = "https"
    telegram_bot_token: str = ""
    telegram_bot_token_file: str | None = None
    telegram_webhook_secret: str = ""
    telegram_webhook_secret_file: str | None = None
    telegram_send_enabled: bool = False
    telegram_polling_enabled: bool = False
    telegram_poll_timeout: int = 25
    manychat_dynamic_block_secret: str = ""
    manychat_dynamic_block_secret_file: str | None = None
    openai_api_key: str = ""
    openai_api_key_file: str | None = None

    authentication_enabled: bool = True
    legacy_admin_adapter_enabled: bool = True
    session_ttl_minutes: int = Field(default=480, ge=5, le=43200)
    session_cookie_name: str = Field(default="sales_agent_session", min_length=3, max_length=64)
    session_cookie_secure: bool = True
    session_cookie_samesite: Literal["lax", "strict"] = "lax"
    password_min_length: int = Field(default=12, ge=10, le=128)
    password_max_length: int = Field(default=1024, ge=128, le=4096)
    login_max_failures: int = Field(default=5, ge=2, le=100)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1440)

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def load_mounted_secrets(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        data = dict(values)
        mappings = {
            "database_url": "database_url_file",
            "application_secret": "application_secret_file",
            "meta_access_token": "meta_access_token_file",
            "meta_app_secret": "meta_app_secret_file",
            "instagram_token_encryption_key": "instagram_token_encryption_key_file",
            "media_signing_secret": "media_signing_secret_file",
            "telegram_bot_token": "telegram_bot_token_file",
            "telegram_webhook_secret": "telegram_webhook_secret_file",
            "manychat_dynamic_block_secret": "manychat_dynamic_block_secret_file",
            "openai_api_key": "openai_api_key_file",
        }
        for target, file_field in mappings.items():
            file_name = data.get(file_field)
            if not file_name or data.get(target):
                continue
            path = Path(str(file_name))
            try:
                if path.stat().st_size > 64 * 1024:
                    raise ValueError(f"{file_field} is too large")
                data[target] = path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise ValueError(f"could not read {file_field}") from exc
        return data

    @field_validator("trusted_hosts", "cors_allowed_origins", mode="before")
    @classmethod
    def parse_csv_list(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def deployed(self) -> bool:
        return self.app_env in DEPLOYED_ENVIRONMENTS

    @property
    def json_logs(self) -> bool:
        return self.log_format == "json" or (self.log_format == "auto" and self.deployed)


def validate_runtime_settings(settings: Settings) -> None:
    """Fail closed for integration/UAT/production deployment configuration."""

    if not settings.deployed:
        return
    errors: list[str] = []
    if not settings.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        errors.append("DATABASE_URL must use PostgreSQL")
    else:
        parsed = make_url(settings.database_url)
        if not parsed.username or not parsed.password or not parsed.host or not parsed.database:
            errors.append("DATABASE_URL must include database, host, username, and password")
        elif any(marker in parsed.password.casefold() for marker in ("replace", "change", "example")):
            errors.append("DATABASE_URL contains a placeholder password")
    secret = settings.application_secret.get_secret_value().strip()
    if (
        secret.casefold() in PLACEHOLDER_VALUES
        or any(marker in secret.casefold() for marker in ("replace", "change", "example"))
        or len(secret) < 32
    ):
        errors.append("APPLICATION_SECRET must contain at least 32 non-placeholder characters")
    if not settings.trusted_hosts or "*" in settings.trusted_hosts:
        errors.append("TRUSTED_HOSTS must be an explicit allowlist")
    if "*" in settings.cors_allowed_origins:
        errors.append("CORS_ALLOWED_ORIGINS cannot contain a wildcard")
    if settings.debug:
        errors.append("DEBUG must be disabled")
    if settings.app_env in {"uat", "production"}:
        if not settings.session_cookie_secure:
            errors.append("SESSION_COOKIE_SECURE must be enabled")
        if not settings.force_https:
            errors.append("FORCE_HTTPS must be enabled")
        if settings.legacy_admin_adapter_enabled:
            errors.append("LEGACY_ADMIN_ADAPTER_ENABLED must be disabled")
    encryption_key = (
        settings.instagram_token_encryption_key.get_secret_value().strip()
    )
    try:
        decoded_encryption_key = base64.b64decode(
            encryption_key.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (UnicodeEncodeError, ValueError):
        decoded_encryption_key = b""
    if len(encryption_key) != 44 or len(decoded_encryption_key) != 32:
        errors.append(
            "INSTAGRAM_TOKEN_ENCRYPTION_KEY must be a valid Fernet key"
        )
    if errors:
        raise ValueError("invalid deployment configuration: " + "; ".join(errors))


@lru_cache
def get_settings() -> Settings:
    return Settings()
