"""Configuration module for MCP Scraper."""

from dataclasses import dataclass, field
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class StealthConfig:
    """Configuration for stealth/anti-detection settings.

    Attributes:
        headless: Run browser in headless mode (default: True)
        solve_cloudflare: Attempt Cloudflare challenges (default: False)
        humanize: Human-like behavior simulation (default: True)
        humanize_duration: Maximum cursor movement duration in seconds (default: 1.5)
        geoip: GeoIP-based routing (default: False)
        os_randomize: Randomize OS fingerprint (default: True)
        block_webrtc: Block WebRTC to prevent IP leaks (default: True)
        allow_webgl: Allow WebGL fingerprinting (default: True)
        google_search: Simulate Chrome browser (default: True)
        block_images: Block image loading (default: False)
        block_ads: Block advertisements (default: True)
        disable_resources: Disable CSS/JS resources (default: False)
        network_idle: Wait for network inactivity (default: False)
        load_dom: Wait for DOMContentLoaded (default: False)
        wait_selector: Wait for specific element to appear (default: None)
        wait_selector_state: Element state to wait for (default: None)
        timeout: Request timeout in milliseconds (default: 30000)
        proxy: Proxy URL for requests (default: None)
        enable_js: Enable JavaScript rendering.
        randomize_user_agent: Randomize User-Agent header per request.
        use_browser_pool: Use a pool of browser instances.
        disable_images: Disable image loading (deprecated, use block_images).
        disable_css: Disable CSS loading (deprecated, use disable_resources).
        block_trackers: Block known tracking domains.
        simulate_human_behavior: Simulate human-like mouse movements (deprecated, use humanize).
        random_delay: Add random delay between requests (in seconds).
        viewport_size: Browser viewport size (width, height).
        timezone: Timezone to simulate.
        language: Language to claim in headers.
        accept_language: Accept-Language header value.
    """

    # Core stealth settings (AGENTS.md spec)
    headless: bool = True
    solve_cloudflare: bool = False
    humanize: bool = True
    humanize_duration: float = 1.5
    geoip: bool = False
    os_randomize: bool = True
    block_webrtc: bool = True
    allow_webgl: bool = True
    google_search: bool = True
    block_images: bool = False
    block_ads: bool = True
    disable_resources: bool = False
    network_idle: bool = False
    load_dom: bool = False
    wait_selector: str | None = None
    wait_selector_state: str | None = None
    timeout: int = 30000
    proxy: str | None = None

    # Legacy/additional settings (kept for backward compatibility)
    enable_js: bool = True
    randomize_user_agent: bool = True
    use_browser_pool: bool = False
    disable_images: bool = False  # Deprecated: use block_images
    disable_css: bool = False  # Deprecated: use disable_resources
    block_trackers: bool = True
    simulate_human_behavior: bool = False  # Deprecated: use humanize
    random_delay: tuple[float, float] = (0.5, 2.0)
    viewport_size: tuple[int, int] = (1920, 1080)
    timezone: str = "UTC"
    language: str = "en-US"
    accept_language: str = "en-US,en;q=0.9"

    # Network settings
    cookies: list[dict[str, str]] = field(default_factory=list)
    extra_headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for scrapling engine."""
        return {
            # Core stealth settings (AGENTS.md spec)
            "headless": self.headless,
            "solve_cloudflare": self.solve_cloudflare,
            "humanize": self.humanize,
            "humanize_duration": self.humanize_duration,
            "geoip": self.geoip,
            "os_randomize": self.os_randomize,
            "block_webrtc": self.block_webrtc,
            "allow_webgl": self.allow_webgl,
            "google_search": self.google_search,
            "block_images": self.block_images,
            "block_ads": self.block_ads,
            "disable_resources": self.disable_resources,
            "network_idle": self.network_idle,
            "load_dom": self.load_dom,
            "wait_selector": self.wait_selector,
            "wait_selector_state": self.wait_selector_state,
            "timeout": self.timeout,
            "proxy": self.proxy,
            # Legacy mappings for backward compatibility
            "javascript": self.enable_js,
            "random_user_agent": self.randomize_user_agent,
            "browser_pool": self.use_browser_pool,
            "images": not self.disable_images,
            "css": not self.disable_css,
            "block_trackers": self.block_trackers,
            "human_behavior": self.simulate_human_behavior,
            "delay": self.random_delay,
            "viewport": self.viewport_size,
            "timezone": self.timezone,
            "locale": self.language,
            "accept_language": self.accept_language,
            "cookies": self.cookies,
            "extra_headers": self.extra_headers,
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

    proxy_url: str | None = Field(default=None, description="Proxy URL for requests")
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
            headless=True,
            solve_cloudflare=False,
            humanize=False,
            geoip=False,
            os_randomize=False,
            block_webrtc=False,
            allow_webgl=False,
            google_search=False,
            block_images=True,
            block_ads=True,
            disable_resources=True,
            network_idle=False,
            load_dom=False,
            timeout=15000,
            # Legacy fields
            enable_js=True,
            randomize_user_agent=True,
            use_browser_pool=False,
            disable_images=False,
            disable_css=False,
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
            headless=True,
            solve_cloudflare=False,
            humanize=True,
            humanize_duration=1.5,
            geoip=False,
            os_randomize=True,
            block_webrtc=True,
            allow_webgl=True,
            google_search=True,
            block_images=False,
            block_ads=True,
            disable_resources=False,
            network_idle=True,
            load_dom=True,
            timeout=30000,
            # Legacy fields
            enable_js=True,
            randomize_user_agent=True,
            use_browser_pool=False,
            disable_images=True,
            disable_css=False,
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
            headless=True,
            solve_cloudflare=True,
            humanize=True,
            humanize_duration=1.5,
            geoip=True,
            os_randomize=True,
            block_webrtc=True,
            allow_webgl=True,
            google_search=True,
            block_images=False,
            block_ads=True,
            disable_resources=False,
            network_idle=True,
            load_dom=True,
            wait_selector="body",
            wait_selector_state="visible",
            timeout=60000,
            # Legacy fields
            enable_js=True,
            randomize_user_agent=True,
            use_browser_pool=True,
            disable_images=True,
            disable_css=False,
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
            headless=True,
            solve_cloudflare=False,
            humanize=False,
            geoip=False,
            os_randomize=False,
            block_webrtc=False,
            allow_webgl=False,
            google_search=False,
            block_images=True,
            block_ads=False,
            disable_resources=False,
            network_idle=False,
            load_dom=False,
            timeout=15000,
            # Legacy fields
            enable_js=False,
            randomize_user_agent=True,
            use_browser_pool=False,
            disable_images=True,
            disable_css=False,
            block_trackers=False,
            simulate_human_behavior=False,
            random_delay=(0.1, 0.3),
        )
