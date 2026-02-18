"""
Application configuration loaded from environment variables.
Never hardcode secrets — use a .env file or your deployment's secret manager.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API
    API_KEY_HEADER: str = "X-API-Key"
    SECRET_KEY: str = "change-me-in-production"          # used for signing, must be set via env
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8000"]

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60                           # seconds

    # Text processing
    MAX_TEXT_LENGTH: int = 10_000                         # characters
    MIN_TEXT_LENGTH: int = 10

    # Model / analyzer
    ANALYZER_N_FEATURES: int = 20

    # Logging
    LOG_LEVEL: str = "INFO"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()