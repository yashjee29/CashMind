"""
CashMind Core Configuration
Centralized settings management using Pydantic Settings.
"""

from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Server Info
    SERVICE_NAME: str = "cashmind"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Internal Authentication
    # If set, requests must include X-API-Key or Bearer token matching this value
    CASHMIND_API_KEY: Optional[str] = None

    # Groq API Key Pooling
    # Accepts comma-separated string, JSON array, or list of keys
    GROQ_API_KEYS: Union[str, List[str]] = Field(default="")

    # Model Routing Configuration (configured for active Groq account models)
    GROQ_MODEL_MODERATION: str = "openai/gpt-oss-20b"
    GROQ_MODEL_ANNOUNCEMENT_GEN: str = "openai/gpt-oss-120b"
    GROQ_MODEL_ANNOUNCEMENT_REW: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODEL: str = "openai/gpt-oss-20b"

    # Concurrency, Retries & Quota Management
    GROQ_MAX_CONCURRENCY: int = Field(default=10, ge=1, le=100)
    GROQ_REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=120.0)
    GROQ_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    KEY_COOLDOWN_SECONDS: float = Field(default=60.0, ge=5.0, le=3600.0)

    @property
    def groq_keys_list(self) -> List[str]:
        """Returns clean list of individual API keys."""
        val = self.GROQ_API_KEYS
        if isinstance(val, str):
            # Split by comma or whitespace
            return [k.strip() for k in val.split(",") if k.strip()]
        if isinstance(val, (list, tuple)):
            return [str(k).strip() for k in val if str(k).strip()]
        return []


# Global singleton settings instance
settings = Settings()
