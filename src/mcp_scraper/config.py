"""Configuration module for MCP Scraper."""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class StealthConfig:
    """Configuration for stealth/anti-detection settings.

    Attributes:
        enable_js: Enable JavaScript rendering (increases detectability).
        randomize_user_agent: Randomize User-Agent header per request.
        use_browser_pool: Use a pool of browser instances to avoid detection.
        headless: Run browser in headless mode.
        disable_images: Disable image loading to reduce footprint.
        disable_css: Disable CSS loading.
        block_ads: Block known ad domains.
        blockackers: Block known tracking domains.
        simulate_human_be_trhavior: Simulate human-like mouse movements.
        random_delay: Add random delay between requests (in seconds).
        viewport_size: Browser viewport size (width, height).
        timezone: Timezone to simulate.
        language: Language to claim in headers.
        accept_language: Accept-Language header value.
    """

    enable_js: bool = True
    randomize_user_agent: bool = True
    use_browser_pool: bool = False
    headless: bool = True
    disable_images: bool = False
    disable_css: bool = False
    block_ads: bool = True
    block_trackers: bool = True
    simulate_human_behavior: bool = False
    random_delay: tuple[float, float] = (0.5, 2.0)
    viewport_size: tuple[int, int] = (1920, 1080)
    timezone: str = "UTC"
    language: str = "en-US"
    accept_language: str = "en-US,en;q=0.9"

    # Advanced options
    cookies: list[dict[str, str]] = field(default_factory=list)
    extra_headers: dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for scrapling engine."""
        return {
            "javascript": self.enable_js,
            "random_user_agent": self.randomize_user_agent,
            "browser_pool": self.use_browser_pool,
            "headless": self.headless,
            "images": not self.disable_images,
            "css": not self.disable_css,
            "ad_block": self.block_ads,
            "block_trackers": self.block_trackers,
            "human_behavior": self.simulate_human_behavior,
            "delay": self.random_delay,
            "viewport": self.viewport_size,
            "timezone": self.timezone,
            "locale": self.language,
            "accept_language": self.accept_language,
            "cookies": self.cookies,
            "extra_headers": self.extra_headers,
            "proxy": self.proxy,
        }


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

    proxy_url: Optional[str] = Field(default=None, description="Proxy URL for requests")
    default_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    log_level: str = Field(default="INFO", description="Logging level")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")


# Pre-configured stealth profiles
class StealthProfiles:
    """Pre-configured stealth profiles for different use cases."""

    @staticmethod
    def minimal() -> StealthConfig:
        """Minimal stealth - basic anti-detection, fast performance.

        Suitable for: Simple scraping tasks, well-behaved sites.
        """
        return StealthConfig(
            enable_js=True,
            randomize_user_agent=True,
            headless=True,
            disable_images=False,
            disable_css=False,
            block_ads=False,
            block_trackers=False,
            simulate_human_behavior=False,
            random_delay=(0.1, 0.5),
        )

    @staticmethod
    def standard() -> StealthConfig:
        """Standard stealth - balanced stealth and performance.

        Suitable for: Most scraping tasks, sites with basic anti-bot measures.
        """
        return StealthConfig(
            enable_js=True,
            randomize_user_agent=True,
            headless=True,
            disable_images=True,
            disable_css=False,
            block_ads=True,
            block_trackers=True,
            simulate_human_behavior=False,
            random_delay=(0.5, 2.0),
            viewport_size=(1920, 1080),
        )

    @staticmethod
    def maximum() -> StealthConfig:
        """Maximum stealth - highest protection, slower performance.

        Suitable for: Sites with aggressive anti-bot measures, sensitive scraping.
        """
        return StealthConfig(
            enable_js=True,
            randomize_user_agent=True,
            use_browser_pool=True,
            headless=True,
            disable_images=True,
            disable_css=True,
            block_ads=True,
            block_trackers=True,
            simulate_human_behavior=True,
            random_delay=(2.0, 5.0),
            viewport_size=(1920, 1080),
            timezone="America/New_York",
            language="en-US",
            accept_language="en-US,en;q=0.9",
        )

    @staticmethod
    def no_js() -> StealthConfig:
        """No JavaScript - fastest, but no JS rendering.

        Suitable for: Static content, APIs, simple pages.
        """
        return StealthConfig(
            enable_js=False,
            randomize_user_agent=True,
            headless=True,
            disable_images=True,
            disable_css=False,
            block_ads=False,
            block_trackers=False,
            simulate_human_behavior=False,
            random_delay=(0.1, 0.3),
        )
