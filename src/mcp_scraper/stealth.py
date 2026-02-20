"""
Stealth Utilities Module for MCP Scraper.

This module provides stealth web scraping capabilities including:
- Configuration classes for different stealth levels
- Session management with anti-detection features
- Retry logic with exponential backoff
- Utility functions for scraping and URL validation
"""

import asyncio
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from urllib.parse import urlparse

try:
    from scrapling import Fetcher
    from scrapling import StealthySession as AsyncStealthySession
    from scrapling import Page
except ImportError:
    # Fallback for type hints if scrapling is not available
    Any = Any  # type: ignore
    AsyncStealthySession = Any  # type: ignore
    Page = Any  # type: ignore
    Fetcher = Any  # type: ignore

from loguru import logger


class StealthLevel(Enum):
    """Stealth level presets for different use cases.

    MINIMAL: Fast, basic anti-detection for simple sites
    STANDARD: Balanced speed and anonymity for most sites
    MAXIMUM: Maximum protection for heavily protected sites
    """

    MINIMAL = "minimal"
    STANDARD = "standard"
    MAXIMUM = "maximum"


@dataclass
class StealthConfig:
    """Configuration for stealth web scraping.

    Attributes:
        headless: Run browser in headless mode (default: True)
        solve_cloudflare: Attempt to solve Cloudflare challenges (default: False)
        humanize: Add human-like behavior patterns (default: True)
        geoip: Use geoip-based request routing (default: False)
        os_randomize: Randomize OS fingerprint (default: True)
        block_webrtc: Block WebRTC to prevent IP leaks (default: True)
        allow_webgl: Allow WebGL fingerprinting (default: False)
        google_search: Simulate Google Chrome browser (default: True)
        block_images: Block images to reduce bandwidth (default: False)
        disable_resources: Disable CSS and JS resources (default: False)
        timeout: Request timeout in seconds (default: 30)
        proxy: Proxy URL for requests (default: None)
    """

    headless: bool = True
    solve_cloudflare: bool = False
    humanize: bool = True
    geoip: bool = False
    os_randomize: bool = True
    block_webrtc: bool = True
    allow_webgl: bool = False
    google_search: bool = True
    block_images: bool = False
    disable_resources: bool = False
    timeout: int = 30
    proxy: Optional[str] = None

    def to_scrapling_options(self) -> dict[str, Any]:
        """Convert config to scrapling options format."""
        options: dict[str, Any] = {
            "headless": self.headless,
            "humanize": self.humanize,
            "timeout": self.timeout,
        }

        if self.solve_cloudflare:
            options["stealth"] = True

        if self.proxy:
            options["proxy"] = self.proxy

        if self.block_webrtc:
            options["block_webrtc"] = True

        if not self.allow_webgl:
            options["webgl"] = False

        if self.google_search:
            options["browser"] = "chrome"

        if self.block_images:
            options["block_images"] = True

        if self.disable_resources:
            options["disable_resources"] = True

        return options


# Global session storage
_session: Optional[AsyncStealthySession] = None
_config_cache: Optional[StealthConfig] = None


def get_minimal_stealth() -> StealthConfig:
    """Get minimal stealth configuration for fast, basic anti-detection.

    Best for:
    - Simple websites without anti-bot protection
    - High-speed scraping where stealth is not critical
    - Testing and development

    Returns:
        StealthConfig with minimal protection settings
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
        disable_resources=True,
        timeout=15,
        proxy=None,
    )


def get_standard_stealth() -> StealthConfig:
    """Get standard stealth configuration for balanced speed and anonymity.

    Best for:
    - Most web scraping tasks
    - Sites with basic anti-bot protection
    - General purpose scraping

    Returns:
        StealthConfig with balanced settings
    """
    return StealthConfig(
        headless=True,
        solve_cloudflare=False,
        humanize=True,
        geoip=False,
        os_randomize=True,
        block_webrtc=True,
        allow_webgl=False,
        google_search=True,
        block_images=False,
        disable_resources=False,
        timeout=30,
        proxy=None,
    )


def get_maximum_stealth() -> StealthConfig:
    """Get maximum stealth configuration for heavily protected sites.

    Best for:
    - Sites with strong anti-bot protection
    - Cloudflare-protected sites
    - Rate-limited endpoints
    - Maximum anonymity required

    Returns:
        StealthConfig with maximum protection settings
    """
    return StealthConfig(
        headless=True,
        solve_cloudflare=True,
        humanize=True,
        geoip=True,
        os_randomize=True,
        block_webrtc=True,
        allow_webgl=False,
        google_search=True,
        block_images=False,
        disable_resources=False,
        timeout=60,
        proxy=None,
    )


def get_stealth_config(level: StealthLevel) -> StealthConfig:
    """Get stealth configuration by level.

    Args:
        level: The stealth level to use

    Returns:
        StealthConfig for the specified level
    """
    configs = {
        StealthLevel.MINIMAL: get_minimal_stealth(),
        StealthLevel.STANDARD: get_standard_stealth(),
        StealthLevel.MAXIMUM: get_maximum_stealth(),
    }
    return configs[level]


async def get_session(config: Optional[StealthConfig] = None) -> AsyncStealthySession:
    """Get or create an async stealthy session.

    This function manages a global session instance. If a session exists
    with the same configuration, it returns the existing session.
    Otherwise, it creates a new one.

    Args:
        config: Stealth configuration (default: standard stealth)

    Returns:
        AsyncStealthySession instance

    Raises:
        RuntimeError: If session creation fails
    """
    global _session, _config_cache

    if config is None:
        config = get_standard_stealth()

    # Return existing session if config matches
    if _session is not None and _config_cache == config:
        return _session

    # Close existing session if config changed
    if _session is not None:
        await close_session()

    try:
        options = config.to_scrapling_options()
        _session = AsyncStealthySession(**options)
        _config_cache = config
        logger.debug(f"Created new stealth session with config: {config}")
        return _session
    except Exception as e:
        logger.error(f"Failed to create stealth session: {e}")
        raise RuntimeError(f"Session creation failed: {e}") from e


async def close_session() -> None:
    """Close and cleanup the global stealth session.

    This should be called when done scraping to properly
    release resources and close browser instances.
    """
    global _session, _config_cache

    if _session is not None:
        try:
            await _session.close()
            logger.debug("Stealth session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        finally:
            _session = None
            _config_cache = None


class ScrapeError(Exception):
    """Base exception for scraping errors."""

    pass


class CloudflareError(ScrapeError):
    """Exception raised when Cloudflare protection blocks the request."""

    pass


class BlockedError(ScrapeError):
    """Exception raised when the request is blocked by anti-bot measures."""

    pass


class TimeoutError(ScrapeError):
    """Exception raised when request times out."""

    pass


async def scrape_with_retry(
    url: str,
    config: Optional[StealthConfig] = None,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    proxy_list: Optional[list[str]] = None,
    selectors: Optional[dict[str, str]] = None,
) -> Page:
    """Scrape a URL with retry logic and exponential backoff.

    This function handles various error types and implements:
    - Exponential backoff between retries
    - Proxy rotation on block detection
    - Cloudflare challenge handling
    - Timeout handling

    Args:
        url: URL to scrape
        config: Stealth configuration (default: standard)
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 1.5)
        proxy_list: List of proxy URLs for rotation (default: None)
        selectors: Optional CSS selectors to extract (default: None)

    Returns:
        Page object with scraped content

    Raises:
        CloudflareError: If Cloudflare protection cannot be solved
        BlockedError: If request is blocked after all retries
        TimeoutError: If request times out
        ScrapeError: For other scraping errors
        ValueError: If URL validation fails
    """
    # Validate URL first
    if not validate_url(url):
        raise ValueError(f"Invalid or disallowed URL: {url}")

    if config is None:
        config = get_standard_stealth()

    current_proxy_idx = 0
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            # Apply proxy rotation if available
            if proxy_list and len(proxy_list) > 0:
                config.proxy = proxy_list[current_proxy_idx]
                logger.debug(f"Using proxy: {config.proxy}")

            # Get or create session
            session = await get_session(config)

            # Attempt to fetch the page
            logger.info(f"Scraping attempt {attempt + 1}/{max_retries}: {url}")
            page = await session.fetch(url, wait_for=2)

            # Check for Cloudflare challenge
            if _detect_cloudflare(page):
                if config.solve_cloudflare:
                    logger.info("Cloudflare challenge detected, attempting to solve...")
                    await asyncio.sleep(3)  # Wait for challenge
                    page = await session.fetch(url, wait_for=5)
                else:
                    raise CloudflareError("Cloudflare protection detected")

            # Check if blocked
            if _detect_block(page):
                raise BlockedError("Request blocked by anti-bot measures")

            logger.info(f"Successfully scraped: {url}")
            return page

        except CloudflareError:
            logger.warning(f"Cloudflare error on attempt {attempt + 1}")
            last_error = CloudflareError("Cloudflare challenge could not be solved")

        except BlockedError:
            logger.warning(f"Blocked on attempt {attempt + 1}")
            # Try rotating proxy
            if proxy_list and len(proxy_list) > 1:
                current_proxy_idx = (current_proxy_idx + 1) % len(proxy_list)
                logger.info(f"Rotating to proxy {current_proxy_idx + 1}/{len(proxy_list)}")
            last_error = BlockedError("Request blocked")

        except asyncio.TimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1}")
            last_error = TimeoutError(f"Request timed out after {config.timeout}s")

        except Exception as e:
            logger.warning(f"Error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            last_error = ScrapeError(f"Scraping failed: {e}")

        # Exponential backoff
        if attempt < max_retries - 1:
            delay = backoff_factor**attempt + random.uniform(0, 1)
            logger.debug(f"Waiting {delay:.2f}s before retry...")
            await asyncio.sleep(delay)

    # All retries exhausted
    raise last_error or ScrapeError("Max retries exceeded")


def _detect_cloudflare(page: Page) -> bool:
    """Detect if page contains Cloudflare challenge.

    Args:
        page: Scraped page object

    Returns:
        True if Cloudflare challenge detected
    """
    try:
        # Check for Cloudflare-specific elements
        if hasattr(page, "html"):
            html = page.html.lower()
            cloudflare_indicators = [
                "cloudflare",
                "checking your browser",
                "just a moment",
                "enable cookies",
                "ray id",
            ]
            return any(indicator in html for indicator in cloudflare_indicators)
        return False
    except Exception:
        return False


def _detect_block(page: Page) -> bool:
    """Detect if request was blocked.

    Args:
        page: Scraped page object

    Returns:
        True if blocked detected
    """
    try:
        if hasattr(page, "html"):
            html = page.html.lower()
            block_indicators = [
                "access denied",
                "forbidden",
                "rate limit",
                "blocked",
                "captcha",
                "please wait",
                "too many requests",
            ]
            return any(indicator in html for indicator in block_indicators)
        return False
    except Exception:
        return False


def format_response(
    page: Page,
    url: str,
    selectors: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Format scraping response into a structured dictionary.

    Args:
        page: Scraped page object
        url: Original URL that was scraped
        selectors: Optional dict of {name: css_selector} to extract

    Returns:
        Dictionary containing:
            - url: Original URL
            - status: HTTP status code (if available)
            - title: Page title
            - html: Full HTML content
            - text: Extracted text content
            - selectors: Dict of extracted selector values
            - timestamp: ISO format timestamp
    """
    response: dict[str, Any] = {
        "url": url,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Get page title
    try:
        if hasattr(page, "title"):
            response["title"] = page.title
    except Exception:
        pass

    # Get status code
    try:
        if hasattr(page, "status"):
            response["status"] = page.status
    except Exception:
        pass

    # Get HTML content
    try:
        if hasattr(page, "html"):
            response["html"] = page.html
    except Exception:
        pass

    # Get text content
    try:
        if hasattr(page, "text"):
            response["text"] = page.text
    except Exception:
        pass

    # Extract specific selectors if provided
    if selectors:
        extracted: dict[str, Any] = {}
        try:
            for name, selector in selectors.items():
                if hasattr(page, "get"):
                    element = page.get(selector)
                    if element:
                        extracted[name] = element.text
                    else:
                        extracted[name] = None
        except Exception as e:
            logger.warning(f"Error extracting selectors: {e}")
        response["selectors"] = extracted

    return response


def validate_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks.

    This function checks for:
    - Valid URL format
    - Allowed protocols (http, https)
    - No private/internal IP addresses
    - No localhost variants
    - No file:// or other dangerous schemes

    Args:
        url: URL to validate

    Returns:
        True if URL is safe to scrape
    """
    try:
        parsed = urlparse(url)

        # Check protocol
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"Disallowed URL scheme: {parsed.scheme}")
            return False

        # Check for empty host
        if not parsed.netloc:
            logger.warning("URL has no host")
            return False

        # Get hostname (without port)
        hostname = parsed.netloc.split(":")[0].lower()

        # Block localhost variants
        localhost_patterns = [
            "localhost",
            "127.0.0.1",
            "::1",
            "0.0.0.0",
            "::",
            "localhost.localdomain",
        ]
        if hostname in localhost_patterns:
            logger.warning(f"Blocked localhost URL: {hostname}")
            return False

        # Block private IP ranges (basic check)
        private_patterns = [
            "^10\\.",
            "^172\\.(1[6-9]|2[0-9]|3[0-1])\\.",
            "^192\\.168\\.",
            "^169\\.254\\.",  # Link-local
            "^127\\.",  # Loopback
        ]
        for pattern in private_patterns:
            if re.match(pattern, hostname):
                logger.warning(f"Blocked private IP: {hostname}")
                return False

        # Block internal hostnames
        internal_patterns = [
            "^.*\\.local$",
            "^.*\\.internal$",
            "^.*\\.corp$",
            "^.*\\.lan$",
        ]
        for pattern in internal_patterns:
            if re.match(pattern, hostname):
                logger.warning(f"Blocked internal hostname: {hostname}")
                return False

        return True

    except Exception as e:
        logger.warning(f"URL validation error: {e}")
        return False


def rotate_proxy(proxy_list: list[str]) -> Optional[str]:
    """Simple proxy rotation function.

    Returns a random proxy from the list.

    Args:
        proxy_list: List of proxy URLs (format: "http://user:pass@host:port")

    Returns:
        Random proxy URL or None if list is empty
    """
    if not proxy_list:
        return None

    return random.choice(proxy_list)


async def cleanup_stealth() -> None:
    """Async context manager cleanup helper.

    This function can be used to ensure proper cleanup
    of stealth sessions.
    """
    await close_session()


# Export commonly used items
__all__ = [
    # Enums
    "StealthLevel",
    # Classes
    "StealthConfig",
    "ScrapeError",
    "CloudflareError",
    "BlockedError",
    "TimeoutError",
    # Preset functions
    "get_minimal_stealth",
    "get_standard_stealth",
    "get_maximum_stealth",
    "get_stealth_config",
    # Session functions
    "get_session",
    "close_session",
    # Core scraping
    "scrape_with_retry",
    # Utilities
    "format_response",
    "validate_url",
    "rotate_proxy",
    "cleanup_stealth",
]
