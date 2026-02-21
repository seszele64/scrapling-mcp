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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from loguru import logger

# Import scrapling types - use Any for compatibility
# The scrapling library returns Selector objects with .text, .html, .status, etc.
# Import core scrapling components
from scrapling import Selector as Page
from scrapling.fetchers import AsyncStealthySession


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
        humanize_duration: Maximum cursor movement duration in seconds (default: 1.5)
        geoip: Use geoip-based request routing (default: False)
        os_randomize: Randomize OS fingerprint (default: True)
        block_webrtc: Block WebRTC to prevent IP leaks (default: True)
        allow_webgl: Allow WebGL fingerprinting (default: False)
        google_search: Simulate Google Chrome browser (default: True)
        block_images: Block images to reduce bandwidth (default: False)
        block_ads: Block advertisements (default: True)
        disable_resources: Disable CSS and JS resources (default: False)
        network_idle: Wait for network inactivity (default: False)
        load_dom: Wait for DOMContentLoaded (default: False)
        wait_selector: Wait for specific element to appear (default: None)
        wait_selector_state: Element state to wait for (default: None)
        timeout: Request timeout in seconds (default: 30)
        proxy: Proxy URL for requests (default: None)
    """

    headless: bool = True
    solve_cloudflare: bool = False
    humanize: bool = True
    humanize_duration: float = 1.5
    geoip: bool = False
    os_randomize: bool = True
    block_webrtc: bool = True
    allow_webgl: bool = False
    google_search: bool = True
    block_images: bool = False
    block_ads: bool = True
    disable_resources: bool = False
    network_idle: bool = False
    load_dom: bool = False
    wait_selector: str | None = None
    wait_selector_state: str | None = None
    timeout: int = 30
    proxy: str | None = None

    def to_scrapling_options(self) -> dict[str, Any]:
        """Convert config to scrapling options format."""
        options: dict[str, Any] = {
            "headless": self.headless,
            "humanize": self.humanize,
            # Convert seconds to milliseconds for scrapling
            "timeout": self.timeout * 1000,
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

        # Additional stealth options
        if self.network_idle:
            options["network_idle"] = True

        if self.load_dom:
            options["load_dom"] = True

        if self.wait_selector:
            options["wait_selector"] = self.wait_selector

        if self.wait_selector_state:
            options["wait_selector_state"] = self.wait_selector_state

        if self.humanize_duration:
            options["humanize_duration"] = self.humanize_duration

        if self.geoip:
            options["geoip"] = True

        if self.os_randomize:
            options["os_randomize"] = True

        return options


# Global session storage
_session: AsyncStealthySession | None = None
_config_cache: StealthConfig | None = None


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


async def get_session(config: StealthConfig | None = None) -> AsyncStealthySession:
    """Get or create an async stealthy session.

    This function manages a global session instance. If a session exists
    with the same configuration, it returns the existing session.
    Otherwise, it creates a new one and properly enters the async context.

    Note: For one-off scraping, prefer using scrape_with_retry() which creates
    a fresh session for each request. Use this only when you need to maintain
    session state (cookies) across multiple requests.

    Args:
        config: Stealth configuration (default: standard stealth)

    Returns:
        AsyncStealthySession instance (entered and ready to use)

    Raises:
        RuntimeError: If session creation fails
    """
    global _session, _config_cache

    if config is None:
        config = get_standard_stealth()

    # Return existing session if config matches and session is still valid
    if _session is not None and _config_cache == config:
        # Verify session is still usable by checking if it has playwright
        if hasattr(_session, "playwright") and _session.playwright is not None:
            return _session
        # Session is dead, need to recreate
        logger.debug("Existing session is dead, recreating...")

    # Close existing session if config changed or session is dead
    if _session is not None:
        await close_session()

    try:
        options = config.to_scrapling_options()
        _session = AsyncStealthySession(**options)

        # Try to use start() method first (preferred method)
        if hasattr(_session, "start"):
            await _session.start()  # type: ignore[attr-defined]
        else:
            # Fall back to __aenter__ for older versions
            await _session.__aenter__()

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
            # Properly exit the async context manager to cleanup browser
            await _session.__aexit__(None, None, None)
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
    config: StealthConfig | None = None,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    proxy_list: list[str] | None = None,
    selectors: dict[str, str] | None = None,
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
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            # Apply proxy rotation if available
            if proxy_list and len(proxy_list) > 0:
                config.proxy = proxy_list[current_proxy_idx]
                logger.debug(f"Using proxy: {config.proxy}")

            # Create a new session for each attempt using async with
            # This ensures proper browser initialization and cleanup
            options = config.to_scrapling_options()
            async with AsyncStealthySession(**options) as session:
                # Attempt to fetch the page
                logger.info(f"Scraping attempt {attempt + 1}/{max_retries}: {url}")
                page = await session.fetch(url, wait_for=2)  # type: ignore[call-arg,misc]

                # Check for Cloudflare challenge
                if _detect_cloudflare(page):
                    if config.solve_cloudflare:
                        logger.info("Cloudflare challenge detected, attempting to solve...")
                        await asyncio.sleep(3)  # Wait for challenge
                        page = await session.fetch(url, wait_for=5)  # type: ignore[call-arg,misc]
                    else:
                        raise CloudflareError("Cloudflare protection detected")

                # Check if blocked
                if _detect_block(page):
                    raise BlockedError("Request blocked by anti-bot measures")

                logger.info(f"Successfully scraped: {url}")
                return page  # type: ignore[no-any-return]

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
            html = str(getattr(page, "html", "")).lower()
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
            html = str(getattr(page, "html", "")).lower()
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
    selectors: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Format scraping response into a structured dictionary.

    Args:
        page: Scraped page object (scrapling Response/Selector object)
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

    # Get status code - scrapling Response has .status attribute
    try:
        response["status"] = getattr(page, "status", None)
    except Exception:
        pass

    # Get page title - use CSS selector since Selector doesn't have .title property
    try:
        if hasattr(page, "css_first"):
            title_element = page.css_first("title")
            if title_element:
                # Get text content from title element
                if hasattr(title_element, "get_all_text"):
                    response["title"] = title_element.get_all_text(strip=True)
                elif hasattr(title_element, "text"):
                    response["title"] = title_element.text
                else:
                    response["title"] = str(title_element) if title_element else None
            else:
                response["title"] = None
        else:
            response["title"] = getattr(page, "title", None)
    except Exception as e:
        logger.debug(f"Error extracting title: {e}")
        response["title"] = None

    # Get HTML content - scrapling Response uses .body for raw HTML
    try:
        response["html"] = getattr(page, "body", None)
        # Fallback to html_content if body is not available
        if response["html"] is None:
            response["html"] = getattr(page, "html_content", None)
    except Exception:
        pass

    # Get text content - use get_all_text() method for full page text
    try:
        if hasattr(page, "get_all_text"):
            response["text"] = page.get_all_text(strip=True)
        elif hasattr(page, "text"):
            response["text"] = page.text
        else:
            response["text"] = ""
    except Exception as e:
        logger.debug(f"Error extracting text: {e}")
        response["text"] = ""

    # Extract specific selectors if provided
    if selectors:
        response["selectors"] = extract_selectors(page, selectors)

    return response


def extract_selectors(page: Page, selectors: dict[str, str]) -> dict[str, Any]:
    """Extract data from page using CSS selectors.

    Supports:
    - Text extraction: "selector" - extracts text content
    - HTML extraction: "selector::html" - extracts inner HTML
    - Attribute extraction: "selector@attrname" - extracts attribute value
    - Multiple elements: "selector" - returns list of values

    Args:
        page: Scraped page object
        selectors: Dict of {name: css_selector}

    Returns:
        Dict with extracted values for each selector name
    """
    extracted: dict[str, Any] = {}

    try:
        for name, selector in selectors.items():
            result = _extract_single_selector(page, selector)
            extracted[name] = result
    except Exception as e:
        logger.warning(f"Error extracting selectors: {e}")

    return extracted


def _extract_single_selector(page: Page, selector: str) -> Any:
    """Extract data from a single CSS selector.

    Supports:
    - "selector" - extract text content (first match)
    - "selector::html" - extract HTML content
    - "selector@attr" - extract attribute value
    - "selector@attr1@attr2" - extract multiple attributes as dict

    Args:
        page: Scraped page object
        selector: CSS selector with optional ::html or @attr suffix

    Returns:
        Extracted value (str, list, or dict)
    """
    # Parse selector for special syntax
    html_extraction = "::html" in selector
    attr_extraction = None

    if "@" in selector and not html_extraction:
        # Attribute extraction: "a@href" or "img@src@alt"
        parts = selector.rsplit("@", 1)
        selector = parts[0]
        attr_extraction = parts[1] if len(parts) > 1 else None

    # Remove ::html suffix if present
    clean_selector = selector.replace("::html", "")

    # Get elements matching selector
    try:
        if hasattr(page, "get"):
            # Use scrapling's get method which returns first match or list
            elements = page.get(clean_selector)  # type: ignore[call-arg]
        else:
            elements = None
    except Exception:
        elements = None

    if elements is None:
        return None

    # Handle single element vs multiple elements
    is_iterable = hasattr(elements, "__iter__") and not isinstance(elements, str)
    if is_iterable:
        # Multiple elements
        element_list = list(elements)
        if len(element_list) == 0:
            return None

        if html_extraction:
            return [get_element_html(el) for el in element_list]

        if attr_extraction:
            if "@" in attr_extraction:
                # Multiple attributes
                attrs = attr_extraction.split("@")
                result = []
                for el in element_list:
                    attr_dict = {}
                    for attr in attrs:
                        attr_dict[attr] = get_element_attribute(el, attr)
                    result.append(attr_dict)
                return result
            else:
                return [get_element_attribute(el, attr_extraction) for el in element_list]

        # Default: return text content
        return [get_element_text(el) for el in element_list]
    else:
        # Single element
        element = elements

        if html_extraction:
            return get_element_html(element)

        if attr_extraction:
            if "@" in attr_extraction:
                # Multiple attributes
                attrs = attr_extraction.split("@")
                return {attr: get_element_attribute(element, attr) for attr in attrs}
            else:
                return get_element_attribute(element, attr_extraction)

        # Default: return text content
        return get_element_text(element)


def get_element_text(element: Any) -> str | None:
    """Extract text content from an element."""
    try:
        if hasattr(element, "text"):
            return element.text  # type: ignore[no-any-return]
        elif hasattr(element, "inner_text"):
            return element.inner_text  # type: ignore[no-any-return]
        elif hasattr(element, "text_content"):
            return element.text_content  # type: ignore[no-any-return]
        elif hasattr(element, "textContent"):
            return element.textContent  # type: ignore[no-any-return]
        elif hasattr(element, "innerHTML"):
            return element.innerHTML  # type: ignore[no-any-return]
        return str(element) if element else None
    except Exception:
        return None


def get_element_html(element: Any) -> str | None:
    """Extract HTML content from an element."""
    try:
        if hasattr(element, "html"):
            return element.html  # type: ignore[no-any-return]
        elif hasattr(element, "innerHTML"):
            return element.innerHTML  # type: ignore[no-any-return]
        elif hasattr(element, "outerHTML"):
            return element.outerHTML  # type: ignore[no-any-return]
        return str(element) if element else None
    except Exception:
        return None


def get_element_attribute(element: Any, attr: str) -> str | None:
    """Extract attribute value from an element."""
    try:
        if hasattr(element, attr):
            return getattr(element, attr)  # type: ignore[no-any-return]
        elif hasattr(element, "get_attribute"):
            return element.get_attribute(attr)  # type: ignore[no-any-return]
        elif hasattr(element, "attributes") and isinstance(element.attributes, dict):
            return element.attributes.get(attr)
        return None
    except Exception:
        return None


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


def rotate_proxy(proxy_list: list[str]) -> str | None:
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
    "extract_selectors",
    "validate_url",
    "rotate_proxy",
    "cleanup_stealth",
]
