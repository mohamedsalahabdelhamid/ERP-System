"""Application configuration.

Settings are loaded from environment variables (and a local `.env` file in
development) using pydantic-settings. This is the single source of truth for
runtime configuration across the whole app.

The system ALWAYS runs on PostgreSQL — there is intentionally no SQLite
fallback here. Local experiments and CI tests use their own in-memory SQLite
engine created explicitly by the test suite, never this setting.
"""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors(v: str | None) -> list[str]:
    """Parse a comma-separated CORS origin list from the environment."""
    if not v:
        return []
    return [origin.strip() for origin in v.split(",") if origin.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application ----
    APP_NAME: str = "ERP System"
    APP_ENV: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    API_V1_PREFIX: str = "/api/v1"
    # Comma-separated list of allowed CORS origins.
    # e.g. CORS_ORIGINS=https://erp.example.com,https://admin.example.com
    CORS_ORIGINS: str = ""

    # ---- Auth ----
    # Lifetime of an access token / session, in minutes (default: 1 day).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ---- Login rate limiting (Redis-backed) ----
    # Failed attempts per (IP+email) and per IP within the sliding window.
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_MAX_IP_ATTEMPTS: int = 20
    LOGIN_WINDOW_SECONDS: int = 900  # 15 minutes
    LOGIN_LOCKOUT_SECONDS: int = 300  # 5 minutes

    # ---- PostgreSQL ----
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "erp"
    POSTGRES_USER: str = "erp"
    POSTGRES_PASSWORD: str = "erp_password_change_me"

    # ---- Redis ----
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # ---- Email / SMTP (for stock alerts and notifications) ----
    # Set SMTP_ENABLED=true to activate email sending.
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@erp-system.com"
    SMTP_FROM_NAME: str = "ERP System"

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Always PostgreSQL (psycopg3). Configured via POSTGRES_* vars."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field  # type: ignore[misc]
    @property
    def CORS_ALLOWED_ORIGINS(self) -> list[str]:
        origins = _parse_cors(self.CORS_ORIGINS)
        if self.APP_ENV == "local" and not origins:
            # Convenience defaults for local development only.
            origins = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
            ]
        return origins


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


settings = get_settings()
