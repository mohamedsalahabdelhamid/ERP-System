"""Application configuration.

Settings are loaded from environment variables (and a local `.env` file in
development) using pydantic-settings. This is the single source of truth for
runtime configuration across the whole app.
"""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application ----
    APP_NAME: str = "ERP System"
    APP_ENV: str = "local"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api/v1"

    # ---- Auth ----
    # Lifetime of an access token / session, in minutes (default: 1 day).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ---- PostgreSQL ----
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "erp"
    POSTGRES_USER: str = "erp"
    POSTGRES_PASSWORD: str = "erp"

    # ---- Redis ----
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy connection URL using the psycopg (v3) driver."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


settings = get_settings()
