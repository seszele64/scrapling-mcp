"""Configuration module for MCP Scraper."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        proxy_url: Optional proxy URL for all requests.
        default_timeout: Default timeout for requests in seconds.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_retries: Maximum number of retries for failed requests.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    proxy_url: str | None = Field(default=None, description="Proxy URL for requests")
    default_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    log_level: str = Field(default="INFO", description="Logging level")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
