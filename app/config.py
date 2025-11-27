"""
Centralized application configuration using environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "ASB Secure Gateway"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    opa_url: str = "http://opa:8181"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com"

    database_url: str = (
        "postgresql://postgres:postgres@postgres:5432/asb_gateway"
    )
    rag_table: str = "documents"
    rag_vector_column: str = "embedding"
    rag_text_column: str = "content"
    rag_metadata_column: str = "metadata"
    rag_top_k_default: int = 5

    agent_allowed_tools: List[str] = Field(
        default_factory=lambda: ["ping", "whoami"]
    )

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("agent_allowed_tools", mode="before")
    @classmethod
    def split_agent_tools(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

