"""Application configuration loaded from environment variables.

This module is the single place where the backend reads PostgreSQL
connection settings. Other layers must import ``get_settings`` instead of
reading ``os.environ`` directly."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from psycopg.conninfo import make_conninfo


class Settings(BaseSettings):
    """Runtime settings for the backend.

    Values are resolved in this order (highest priority first):
    1. Real environment variables.
    2. ``backend/.env`` when the process runs from ``backend/``.
    3. Repository-root ``.env`` (``../.env`` from ``backend/``).
    4. The development defaults declared below."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # PostgreSQL connection. Names match .env.example on purpose.
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        validation_alias="POSTGRES_PORT",
    )
    postgres_db: str = Field(default="basedebatos", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="basedebatos", validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr("basedebatos"),
        validation_alias="POSTGRES_PASSWORD",
    )

    # Pool sizing. These describe the API process, not the database container.
    db_pool_min_size: int = Field(
        default=1,
        ge=0,
        validation_alias="DB_POOL_MIN_SIZE",
    )
    db_pool_max_size: int = Field(
        default=10,
        ge=1,
        validation_alias="DB_POOL_MAX_SIZE",
    )
    db_pool_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        validation_alias="DB_POOL_TIMEOUT_SECONDS",
    )
    db_connect_timeout_seconds: int = Field(
        default=5,
        ge=1,
        validation_alias="DB_CONNECT_TIMEOUT_SECONDS",
    )

    @model_validator(mode="after")
    def _validate_pool_bounds(self) -> "Settings":
        if self.db_pool_max_size < self.db_pool_min_size:
            raise ValueError(
                "DB_POOL_MAX_SIZE must be greater than or equal to "
                "DB_POOL_MIN_SIZE"
            )
        return self

    @property
    def database_url(self) -> str:
        """Return a libpq connection string built from the environment.

        ``make_conninfo`` quotes every value, so passwords containing spaces,
        quotes or backslashes remain valid. The password is stored as a
        ``SecretStr`` and is only unwrapped here. Do not log this value.
        """
        return make_conninfo(
            host=self.postgres_host,
            port=self.postgres_port,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            connect_timeout=self.db_connect_timeout_seconds,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()