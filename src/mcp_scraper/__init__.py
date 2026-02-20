"""MCP Scraper - A Scrapling MCP server for web scraping with stealth capabilities."""

__version__ = "0.1.0"

from mcp_scraper.config import Settings
from mcp_scraper.stealth import (
    BlockedError,
    CloudflareError,
    ScrapeError,
    StealthConfig,
    StealthLevel,
    cleanup_stealth,
    close_session,
    format_response,
    get_maximum_stealth,
    get_minimal_stealth,
    get_session,
    get_standard_stealth,
    get_stealth_config,
    scrape_with_retry,
    validate_url,
)

__all__ = [
    # Version
    "__version__",
    # Settings
    "Settings",
    # Config and Levels
    "StealthConfig",
    "StealthLevel",
    # Preset functions
    "get_minimal_stealth",
    "get_standard_stealth",
    "get_maximum_stealth",
    "get_stealth_config",
    # Session functions
    "get_session",
    "close_session",
    "cleanup_stealth",
    # Core scraping
    "scrape_with_retry",
    # Utilities
    "format_response",
    "validate_url",
    # Exceptions
    "ScrapeError",
    "CloudflareError",
    "BlockedError",
]
