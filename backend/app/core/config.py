from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Expiry Notification API"
    app_version: str = "0.1.0"
    app_environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://expiry_app:expiry_dev_password@localhost:5432/expiry_notification",
        description="SQLAlchemy-compatible PostgreSQL connection URL.",
    )
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_timeout_seconds: int = Field(default=30, ge=1)

    oidc_issuer_url: str = Field(
        default="https://identity.example.invalid/",
        description="Expected issuer claim for incoming OIDC access tokens.",
    )
    oidc_audience: str = Field(
        default="expiry-notification-api",
        description="Expected API audience claim for incoming access tokens.",
    )
    oidc_jwks_url: str = Field(
        default="https://identity.example.invalid/.well-known/jwks.json",
        description="Identity-provider JSON Web Key Set endpoint.",
    )
    oidc_algorithms: str = Field(
        default="RS256",
        description="Comma-separated asymmetric JWT signing algorithms accepted by the API.",
    )
    oidc_jwks_cache_seconds: int = Field(default=300, ge=30)


@lru_cache
def get_settings() -> Settings:
    return Settings()
