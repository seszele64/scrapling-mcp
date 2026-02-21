"""MCP Scraper Server - FastMCP server for stealth web scraping."""

import asyncio
import random
import signal
import sys
from datetime import datetime
from typing import Any

from fastmcp import FastMCP
from loguru import logger

from mcp_scraper import Settings
from mcp_scraper.stealth import (
    BlockedError,
    CloudflareError,
    ScrapeError,
    StealthConfig,
    close_session,
    extract_selectors,
    format_response,
    get_maximum_stealth,
    get_minimal_stealth,
    get_session,
    get_standard_stealth,
    scrape_with_retry,
    validate_url,
)
from mcp_scraper.stealth import (
    TimeoutError as ScrapeTimeoutError,
)

# Initialize settings
settings = Settings()

# Initialize FastMCP server
mcp = FastMCP("Scrapling MCP Server")

# Global flag for graceful shutdown
_shutdown_event: asyncio.Event | None = None


# T030: Input validation functions
def _validate_url_param(url: Any) -> str | None:
    """Validate URL parameter.

    Args:
        url: URL to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(url, str):
        return "URL must be a string"
    if not url or not url.strip():
        return "URL cannot be empty"
    return None


def _validate_timeout(timeout: Any) -> str | None:
    """Validate timeout parameter.

    Args:
        timeout: Timeout value in milliseconds

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(timeout, int):
        return "Timeout must be an integer"
    if timeout < 1000 or timeout > 300000:
        return "Timeout must be between 1000 and 300000 milliseconds"
    return None


def _validate_stealth_level(level: Any) -> str | None:
    """Validate stealth_level parameter.

    Args:
        level: Stealth level string

    Returns:
        Error message if invalid, None if valid
    """
    valid_levels = ["minimal", "standard", "maximum"]
    if not isinstance(level, str):
        return "Stealth level must be a string"
    if level.lower() not in valid_levels:
        return f"Stealth level must be one of: {', '.join(valid_levels)}"
    return None


def _validate_extract(extract: Any) -> str | None:
    """Validate extract parameter.

    Args:
        extract: Extract mode string

    Returns:
        Error message if invalid, None if valid
    """
    valid_modes = ["text", "html", "both"]
    if not isinstance(extract, str):
        return "Extract must be a string"
    if extract.lower() not in valid_modes:
        return f"Extract must be one of: {', '.join(valid_modes)}"
    return None


def _validate_delay(delay: Any) -> str | None:
    """Validate delay parameter.

    Args:
        delay: Delay value in seconds

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(delay, (int, float)):
        return "Delay must be a number"
    if delay < 0:
        return "Delay must be non-negative"
    return None


def _validate_urls_list(urls: Any) -> str | None:
    """Validate urls list parameter.

    Args:
        urls: List of URLs

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(urls, list):
        return "URLs must be a list"
    if len(urls) == 0:
        return "URLs list cannot be empty"
    if len(urls) > 100:
        return "URLs list cannot have more than 100 items"
    for url in urls:
        if not isinstance(url, str):
            return "All URLs must be strings"
    return None


def _validate_selector(selector: Any) -> str | None:
    """Validate selector parameter.

    Args:
        selector: CSS selector string

    Returns:
        Error message if invalid, None if valid
    """
    if selector is None:
        return None
    if not isinstance(selector, str):
        return "Selector must be a string"
    return None


# T015: Stealth level mapping function
def _get_stealth_config_by_level(level: str) -> StealthConfig:
    """Map stealth level string to configuration.

    Args:
        level: Stealth level string ("minimal", "standard", "maximum")

    Returns:
        StealthConfig for the specified level

    Raises:
        ValueError: If invalid stealth level is provided
    """
    level_map = {
        "minimal": get_minimal_stealth(),
        "standard": get_standard_stealth(),
        "maximum": get_maximum_stealth(),
    }

    config = level_map.get(level.lower())
    if config is None:
        raise ValueError(
            f"Invalid stealth level: '{level}'. Valid options are: minimal, standard, maximum"
        )
    return config


@mcp.tool()
async def scrape_simple(
    url: str,
    selector: str | None = None,
    extract: str = "text",
    timeout: int = 30000,
) -> dict[str, Any]:
    """Simple web scraping without stealth features.

    Uses the Fetcher class for fast HTTP requests with TLS fingerprinting.
    Best for static content and well-behaved websites.

    Args:
        url: The URL to scrape.
        selector: Optional CSS selector for targeted extraction.
        extract: What to extract - "text", "html", or "both" (default: "text").
        timeout: Request timeout in milliseconds (default: 30000, range: 1000-300000).

    Returns:
        Dictionary containing:
            - url: Original URL
            - status_code: HTTP status code
            - title: Page title
            - text: Extracted text content
            - html: Full HTML content
            - headers: Response headers
            - selectors: Extracted selector data (if selector provided)
            - timestamp: ISO format timestamp
            - error: Error message (if any)

    Raises:
        ValueError: If input parameters are invalid.
    """
    # T031: Log tool entry with parameters
    logger.debug(
        f"scrape_simple called with: url={url}, selector={selector}, extract={extract}, timeout={timeout}"
    )

    # T030: Input validation
    if error_msg := _validate_url_param(url):
        logger.warning(f"URL validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "selectors": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_selector(selector):
        logger.warning(f"Selector validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "selectors": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_extract(extract):
        logger.warning(f"Extract validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "selectors": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_timeout(timeout):
        logger.warning(f"Timeout validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "selectors": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    # T010: URL validation (security check)
    if not validate_url(url):
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "selectors": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Invalid or disallowed URL. URLs must use http/https and cannot point to localhost or private IP addresses.",
        }

    # T011: Response formatting setup
    result: dict[str, Any] = {
        "url": url,
        "status_code": None,
        "title": None,
        "text": None,
        "html": None,
        "headers": None,
        "selectors": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": None,
    }

    # T012: Error handling
    try:
        # Use minimal stealth config for fast scraping
        config = get_minimal_stealth()
        config.timeout = timeout // 1000  # Convert ms to seconds for StealthConfig

        # Prepare selectors if provided
        selectors_dict: dict[str, str] | None = None
        if selector:
            selectors_dict = {"content": selector}

        # Scrape the page
        page = await scrape_with_retry(
            url=url,
            config=config,
            max_retries=settings.max_retries,
        )

        # T011: Use format_response from stealth module
        formatted = format_response(page, url, selectors_dict)

        # Build response based on extract parameter
        result["status_code"] = formatted.get("status")
        result["title"] = formatted.get("title")
        result["headers"] = {}  # Fetcher doesn't expose headers directly

        if extract in ("text", "both"):
            result["text"] = formatted.get("text", "")

        if extract in ("html", "both"):
            result["html"] = formatted.get("html", "")

        # Extract selector data if provided
        if selector and "selectors" in formatted:
            result["selectors"] = formatted["selectors"]

        # T031: Log successful completion
        logger.info(f"scrape_simple completed successfully for {url}")

    except CloudflareError as e:
        logger.error(f"Cloudflare error for {url}: {e}")
        result["error"] = f"Cloudflare protection detected: {str(e)}"
    except BlockedError as e:
        logger.error(f"Blocked error for {url}: {e}")
        result["error"] = f"Request blocked: {str(e)}"
    except ScrapeTimeoutError as e:
        logger.error(f"Timeout error for {url}: {e}")
        result["error"] = f"Request timed out: {str(e)}"
    except ScrapeError as e:
        logger.error(f"Scraping error for {url}: {e}")
        result["error"] = f"Scraping error: {str(e)}"
    except ValueError as e:
        logger.error(f"Validation error for {url}: {e}")
        result["error"] = f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {type(e).__name__}: {e}")
        result["error"] = f"Unexpected error: {str(e)}"

    return result


# T014: Implement scrape_stealth tool
@mcp.tool()
async def scrape_stealth(
    url: str,
    stealth_level: str = "standard",
    solve_cloudflare: bool = False,
    network_idle: bool = True,
    load_dom: bool = True,
    timeout: int = 30000,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Stealth web scraping with configurable anti-detection.

    Uses the StealthyFetcher class with Camoufox (modified Firefox)
    or Chrome for maximum stealth and anti-detection.

    Args:
        url: The URL to scrape.
        stealth_level: Stealth level - "minimal", "standard", or "maximum" (default: "standard").
        solve_cloudflare: Attempt Cloudflare challenges (default: False).
        network_idle: Wait for network inactivity before returning (default: True).
        load_dom: Wait for DOMContentLoaded event (default: True).
        timeout: Request timeout in milliseconds (default: 30000, range: 1000-300000).
        proxy: Proxy URL for requests (default: None).

    Returns:
        Dictionary containing:
            - url: Original URL
            - status_code: HTTP status code
            - title: Page title
            - text: Extracted text content
            - html: Full HTML content
            - headers: Response headers
            - timestamp: ISO format timestamp
            - error: Error message (if any)

    Raises:
        ValueError: If input parameters are invalid.
    """
    # T031: Log tool entry with parameters
    logger.debug(
        f"scrape_stealth called with: url={url}, stealth_level={stealth_level}, solve_cloudflare={solve_cloudflare}, network_idle={network_idle}, load_dom={load_dom}, timeout={timeout}, proxy={proxy}"
    )

    # T030: Input validation
    if error_msg := _validate_url_param(url):
        logger.warning(f"URL validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_stealth_level(stealth_level):
        logger.warning(f"Stealth level validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_timeout(timeout):
        logger.warning(f"Timeout validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    # T010: URL validation (security check)
    if not validate_url(url):
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Invalid or disallowed URL. URLs must use http/https and cannot point to localhost or private IP addresses.",
        }

    # T015: Get stealth config based on level
    try:
        config = _get_stealth_config_by_level(stealth_level)
    except ValueError as e:
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "headers": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
        }

    # T017: Override Cloudflare setting if specified
    config.solve_cloudflare = solve_cloudflare

    # T016 & T018: Configure network settings and proxy
    config.network_idle = network_idle
    config.load_dom = load_dom
    config.timeout = timeout // 1000  # Convert ms to seconds for StealthConfig
    if proxy:
        config.proxy = proxy

    # Response formatting setup
    result: dict[str, Any] = {
        "url": url,
        "status_code": None,
        "title": None,
        "text": None,
        "html": None,
        "headers": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": None,
    }

    try:
        # T016: Call scrape_with_retry with stealth config
        page = await scrape_with_retry(
            url=url,
            config=config,
            max_retries=settings.max_retries,
        )

        # Use format_response from stealth module
        formatted = format_response(page, url)

        result["status_code"] = formatted.get("status")
        result["title"] = formatted.get("title")
        result["text"] = formatted.get("text", "")
        result["html"] = formatted.get("html", "")

        # T031: Log successful completion
        logger.info(f"scrape_stealth completed successfully for {url}")

    except CloudflareError as e:
        logger.error(f"Cloudflare error for {url}: {e}")
        result["error"] = f"Cloudflare protection detected: {str(e)}"
    except BlockedError as e:
        logger.error(f"Blocked error for {url}: {e}")
        result["error"] = f"Request blocked: {str(e)}"
    except ScrapeTimeoutError as e:
        logger.error(f"Timeout error for {url}: {e}")
        result["error"] = f"Request timed out: {str(e)}"
    except ScrapeError as e:
        logger.error(f"Scraping error for {url}: {e}")
        result["error"] = f"Scraping error: {str(e)}"
    except ValueError as e:
        logger.error(f"Validation error for {url}: {e}")
        result["error"] = f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {type(e).__name__}: {e}")
        result["error"] = f"Unexpected error: {str(e)}"

    return result


# T019, T020, T021: Implement scrape_session tool with session management and cookie persistence
# Global session storage for session-based scraping
_session_storage: dict[str, Any] = {}


@mcp.tool()
async def scrape_session(
    url: str,
    session_id: str | None = None,
    cookies: dict[str, str] | None = None,
    stealth_level: str = "standard",
) -> dict[str, Any]:
    """Session-based scraping with persistent state.

    Maintains cookies and state across multiple requests for authenticated
    scraping or multi-step interactions.

    Args:
        url: The URL to scrape.
        session_id: Session identifier for persistence (default: auto-generated).
        cookies: Initial cookies to set (format: {"name": "value"}).
        stealth_level: Stealth level - "minimal", "standard", or "maximum" (default: "standard").

    Returns:
        Dictionary containing:
            - url: Original URL
            - session_id: Session identifier
            - status_code: HTTP status code
            - title: Page title
            - text: Extracted text content
            - html: Full HTML content
            - cookies: Current cookies from session
            - timestamp: ISO format timestamp
            - error: Error message (if any)

    Raises:
        ValueError: If input parameters are invalid.
    """
    # T031: Log tool entry with parameters
    logger.debug(
        f"scrape_session called with: url={url}, session_id={session_id}, cookies={cookies}, stealth_level={stealth_level}"
    )

    # T030: Input validation
    if error_msg := _validate_url_param(url):
        logger.warning(f"URL validation failed: {error_msg}")
        return {
            "url": url,
            "session_id": session_id,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "cookies": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_stealth_level(stealth_level):
        logger.warning(f"Stealth level validation failed: {error_msg}")
        return {
            "url": url,
            "session_id": session_id,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "cookies": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    # T010: URL validation (security check)
    if not validate_url(url):
        return {
            "url": url,
            "session_id": session_id,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "cookies": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Invalid or disallowed URL. URLs must use http/https and cannot point to localhost or private IP addresses.",
        }

    # Generate session ID if not provided
    if not session_id:
        session_id = (
            f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        )

    # T015: Get stealth config based on level
    try:
        config = _get_stealth_config_by_level(stealth_level)
    except ValueError as e:
        return {
            "url": url,
            "session_id": session_id,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "cookies": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
        }

    # Response formatting setup
    result: dict[str, Any] = {
        "url": url,
        "session_id": session_id,
        "status_code": None,
        "title": None,
        "text": None,
        "html": None,
        "cookies": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": None,
    }

    try:
        # T020: Session management - get or create session
        session = await get_session(config)

        # T021: Set initial cookies if provided
        if cookies:
            for name, value in cookies.items():
                # Set cookie on the session
                await session.set_cookies({name: value})  # type: ignore[attr-defined]
            logger.debug(f"Set initial cookies for session {session_id}: {list(cookies.keys())}")

        # Scrape the page
        page = await session.fetch(url, wait_for=2)  # type: ignore[call-arg,misc]

        # T017: Check for Cloudflare challenge
        from mcp_scraper.stealth import _detect_cloudflare

        if _detect_cloudflare(page):
            if config.solve_cloudflare:
                logger.info("Cloudflare challenge detected in session, attempting to solve...")
                await asyncio.sleep(3)
                page = await session.fetch(url, wait_for=5)  # type: ignore[call-arg,misc]
            else:
                raise CloudflareError("Cloudflare protection detected")

        # Format response
        formatted = format_response(page, url)

        result["status_code"] = formatted.get("status")
        result["title"] = formatted.get("title")
        result["text"] = formatted.get("text", "")
        result["html"] = formatted.get("html", "")

        # T021: Get cookies from session for persistence
        try:
            session_cookies = await session.get_cookies()  # type: ignore[attr-defined]
            if session_cookies:
                result["cookies"] = {cookie["name"]: cookie["value"] for cookie in session_cookies}
                logger.debug(
                    f"Retrieved {len(result['cookies'])} cookies from session {session_id}"
                )
        except Exception as e:
            logger.warning(f"Could not retrieve cookies from session: {e}")

        # Store session in global storage for reuse
        _session_storage[session_id] = {
            "session": session,
            "config": config,
        }

        # T031: Log successful completion
        logger.info(f"scrape_session completed successfully for {url} (session: {session_id})")

    except CloudflareError as e:
        logger.error(f"Cloudflare error for {url} in session {session_id}: {e}")
        result["error"] = f"Cloudflare protection detected: {str(e)}"
    except BlockedError as e:
        logger.error(f"Blocked error for {url} in session {session_id}: {e}")
        result["error"] = f"Request blocked: {str(e)}"
    except ScrapeTimeoutError as e:
        logger.error(f"Timeout error for {url} in session {session_id}: {e}")
        result["error"] = f"Request timed out: {str(e)}"
    except ScrapeError as e:
        logger.error(f"Scraping error for {url} in session {session_id}: {e}")
        result["error"] = f"Scraping error: {str(e)}"
    except ValueError as e:
        logger.error(f"Validation error for {url} in session {session_id}: {e}")
        result["error"] = f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error for {url} in session {session_id}: {type(e).__name__}: {e}")
        result["error"] = f"Unexpected error: {str(e)}"

    return result


# T022: Implement extract_structured tool
# T023: Add CSS selector extraction logic
@mcp.tool()
async def extract_structured(
    url: str,
    selectors: Any,  # Accept Any for validation
    stealth_level: str = "standard",
) -> dict[str, Any]:
    """Extract structured data from a webpage using CSS selectors.

    Uses the StealthyFetcher for anti-detection with configurable stealth level.
    Supports text extraction, HTML extraction, and attribute extraction.

    Selector Syntax:
    - "selector" - Extract text content (first match)
    - "selector::html" - Extract inner HTML
    - "selector@attr" - Extract attribute value (e.g., "a@href", "img@src")
    - "selector@attr1@attr2" - Extract multiple attributes as dict

    Args:
        url: The URL to scrape.
        selectors: Dict mapping names to CSS selectors.
                  Example: {"title": "h1", "links": "a@href", "content": "div.content"}
        stealth_level: Stealth level - "minimal", "standard", or "maximum" (default: "standard").

    Returns:
        Dictionary containing:
            - url: Original URL
            - status_code: HTTP status code
            - title: Page title
            - text: Page text content
            - extracted: Dict with extracted data from selectors
            - timestamp: ISO format timestamp
            - error: Error message (if any)

    Raises:
        ValueError: If input parameters are invalid.
    """
    # T030: Input validation - check selectors type FIRST to prevent 'str' object has no attribute 'keys' error
    if not isinstance(selectors, dict):
        logger.warning(f"Selectors must be a dictionary, got: {type(selectors).__name__}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "extracted": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Selectors must be a dictionary",
        }

    # T031: Log tool entry with parameters (after validation to avoid errors)
    logger.debug(
        f"extract_structured called with: url={url}, selectors={list(selectors.keys())}, stealth_level={stealth_level}"
    )

    # T030: Input validation - URL validation
    if error_msg := _validate_url_param(url):
        logger.warning(f"URL validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "extracted": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    if error_msg := _validate_stealth_level(stealth_level):
        logger.warning(f"Stealth level validation failed: {error_msg}")
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "extracted": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg,
        }

    # URL validation (T010)
    if not validate_url(url):
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "extracted": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Invalid or disallowed URL. URLs must use http/https and cannot point to localhost or private IP addresses.",
        }

    # Get stealth config based on level (T015)
    try:
        config = _get_stealth_config_by_level(stealth_level)
    except ValueError as e:
        return {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "extracted": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
        }

    # Response formatting setup
    result: dict[str, Any] = {
        "url": url,
        "status_code": None,
        "title": None,
        "text": None,
        "extracted": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": None,
    }

    try:
        # Scrape the page with retry
        page = await scrape_with_retry(
            url=url,
            config=config,
            max_retries=settings.max_retries,
        )

        # Format response
        formatted = format_response(page, url)

        result["status_code"] = formatted.get("status")
        result["title"] = formatted.get("title")
        result["text"] = formatted.get("text", "")

        # T023: Extract structured data using CSS selectors
        # Use the extract_selectors function which handles @attribute syntax
        result["extracted"] = extract_selectors(page, selectors)
        logger.debug(f"Extracted {len(result['extracted'])} selector groups from {url}")

        # T031: Log successful completion
        logger.info(f"extract_structured completed successfully for {url}")

    except CloudflareError as e:
        logger.error(f"Cloudflare error for {url}: {e}")
        result["error"] = f"Cloudflare protection detected: {str(e)}"
    except BlockedError as e:
        logger.error(f"Blocked error for {url}: {e}")
        result["error"] = f"Request blocked: {str(e)}"
    except ScrapeTimeoutError as e:
        logger.error(f"Timeout error for {url}: {e}")
        result["error"] = f"Request timed out: {str(e)}"
    except ScrapeError as e:
        logger.error(f"Scraping error for {url}: {e}")
        result["error"] = f"Scraping error: {str(e)}"
    except ValueError as e:
        logger.error(f"Validation error for {url}: {e}")
        result["error"] = f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {type(e).__name__}: {e}")
        result["error"] = f"Unexpected error: {str(e)}"

    # T028: Ensure JSON serialization - handle edge cases
    result = _ensure_json_serializable(result)

    return result


# T024-T028: Implement scrape_batch tool with all batch processing features
@mcp.tool()
async def scrape_batch(
    urls: list[str],
    stealth_level: str = "standard",
    delay: float = 1.0,
) -> dict[str, Any]:
    """Scrape multiple URLs in sequence.

    Processes URLs sequentially with a configurable delay between requests.
    Handles partial failures gracefully - continues processing remaining URLs.

    Args:
        urls: List of URLs to scrape (max 100 URLs).
        stealth_level: Stealth level - "minimal", "standard", or "maximum" (default: "standard").
        delay: Delay between requests in seconds (default: 1.0, must be non-negative).

    Returns:
        Dictionary containing:
            - total: Total number of URLs
            - successful: Number of successfully scraped URLs
            - failed: Number of failed URLs
            - results: List of individual scrape results
            - errors: List of errors encountered
            - timestamp: ISO format timestamp

    Raises:
        ValueError: If input parameters are invalid.
    """
    # T031: Log tool entry with parameters
    logger.debug(
        f"scrape_batch called with: urls_count={len(urls)}, stealth_level={stealth_level}, delay={delay}"
    )

    # T030: Input validation
    if error_msg := _validate_urls_list(urls):
        logger.warning(f"URLs list validation failed: {error_msg}")
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "errors": [{"error": error_msg}],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    if error_msg := _validate_stealth_level(stealth_level):
        logger.warning(f"Stealth level validation failed: {error_msg}")
        return {
            "total": len(urls),
            "successful": 0,
            "failed": len(urls),
            "results": [],
            "errors": [{"error": error_msg}],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    if error_msg := _validate_delay(delay):
        logger.warning(f"Delay validation failed: {error_msg}")
        return {
            "total": len(urls),
            "successful": 0,
            "failed": len(urls),
            "results": [],
            "errors": [{"error": error_msg}],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # Validate all URLs upfront
    validated_urls: list[tuple[int, str]] = []
    invalid_urls: list[dict[str, Any]] = []

    for idx, url in enumerate(urls):
        if validate_url(url):
            validated_urls.append((idx, url))
        else:
            invalid_urls.append(
                {
                    "index": idx,
                    "url": url,
                    "error": "Invalid or disallowed URL",
                }
            )

    # T026: Initialize batch result aggregation
    errors: list[dict[str, Any]] = []
    successful_count = 0
    failed_count = 0

    # Initialize results array with placeholders for all URLs
    # This maintains the original order
    results_placeholder: list[dict[str, Any] | None] = [None] * len(urls)

    # T025: Sequential URL processing with delay
    for idx, url in validated_urls:
        result: dict[str, Any] = {
            "url": url,
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": None,
        }

        # Get stealth config based on level (T015)
        try:
            config = _get_stealth_config_by_level(stealth_level)
        except ValueError as e:
            result["error"] = str(e)
            errors.append({"index": idx, "url": url, "error": str(e)})
            results_placeholder[idx] = result
            failed_count += 1
            continue

        try:
            # Scrape the page
            page = await scrape_with_retry(
                url=url,
                config=config,
                max_retries=settings.max_retries,
            )

            # Format response
            formatted = format_response(page, url)

            result["status_code"] = formatted.get("status")
            result["title"] = formatted.get("title")
            result["text"] = formatted.get("text", "")
            result["html"] = formatted.get("html", "")

            successful_count += 1
            logger.debug(f"Successfully scraped batch item {idx + 1}/{len(urls)}: {url}")

        except CloudflareError as e:
            logger.error(f"Cloudflare error for {url} in batch: {e}")
            result["error"] = f"Cloudflare protection detected: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Cloudflare protection: {str(e)}"})
            failed_count += 1
        except BlockedError as e:
            logger.error(f"Blocked error for {url} in batch: {e}")
            result["error"] = f"Request blocked: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Blocked: {str(e)}"})
            failed_count += 1
        except ScrapeTimeoutError as e:
            logger.error(f"Timeout error for {url} in batch: {e}")
            result["error"] = f"Request timed out: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Timeout: {str(e)}"})
            failed_count += 1
        except ScrapeError as e:
            logger.error(f"Scraping error for {url} in batch: {e}")
            result["error"] = f"Scraping error: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Scraping error: {str(e)}"})
            failed_count += 1
        except ValueError as e:
            logger.error(f"Validation error for {url} in batch: {e}")
            result["error"] = f"Validation error: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Validation: {str(e)}"})
            failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error for {url} in batch: {type(e).__name__}: {e}")
            result["error"] = f"Unexpected error: {str(e)}"
            errors.append({"index": idx, "url": url, "error": f"Unexpected: {str(e)}"})
            failed_count += 1

        # T027: Continue processing remaining URLs - don't stop on first error
        results_placeholder[idx] = result

        # Apply delay between requests (skip delay for last item)
        if idx < len(validated_urls) - 1:
            await asyncio.sleep(delay)

    # T026: Add invalid URLs to errors
    for invalid in invalid_urls:
        errors.append(invalid)
        # Add placeholder for invalid URL
        results_placeholder[invalid["index"]] = {
            "url": invalid["url"],
            "status_code": None,
            "title": None,
            "text": None,
            "html": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": invalid["error"],
        }

    # Build final response
    batch_result: dict[str, Any] = {
        "total": len(urls),
        "successful": successful_count,
        "failed": failed_count + len(invalid_urls),
        "results": results_placeholder,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # T028: Ensure JSON serialization - handle edge cases
    batch_result = _ensure_json_serializable(batch_result)

    logger.info(
        f"Batch scraping complete: {successful_count}/{len(urls)} successful, "
        f"{failed_count + len(invalid_urls)} failed"
    )

    return batch_result


def _ensure_json_serializable(data: Any) -> Any:
    """Ensure all data is JSON-serializable.

    Handles edge cases like:
    - None values (convert to null)
    - Special characters (ensure UTF-8 encoding)
    - Non-serializable types (convert to string)
    - NaN/Infinity values (replace with None)

    Args:
        data: Input data of any type

    Returns:
        JSON-serializable version of the data
    """
    if data is None:
        return None

    if isinstance(data, (str, int, float, bool)):
        # Handle special float values
        if isinstance(data, float):
            import math

            if math.isnan(data) or math.isinf(data):
                return None
        return data

    if isinstance(data, dict):
        return {k: _ensure_json_serializable(v) for k, v in data.items()}

    if isinstance(data, (list, tuple)):
        return [_ensure_json_serializable(item) for item in data]

    # For any other type, convert to string
    try:
        return str(data)
    except Exception:
        return None


def _setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown.

    Handles SIGINT and SIGTERM signals to ensure proper cleanup
    of sessions and browser resources.
    """

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received {signal_name} signal, initiating graceful shutdown...")

        # Schedule async cleanup if we're in an async context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_cleanup_on_shutdown())
            else:
                loop.run_until_complete(_cleanup_on_shutdown())
        except RuntimeError:
            # No event loop, just do sync cleanup
            pass

        logger.info("Cleanup complete, exiting.")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def _cleanup_on_shutdown() -> None:
    """Cleanup resources on shutdown.

    Closes all sessions and releases browser resources.
    """
    global _shutdown_event

    logger.info("Starting cleanup...")

    # Close stealth session
    try:
        await close_session()
        logger.debug("Stealth session closed")
    except Exception as e:
        logger.warning(f"Error closing stealth session: {e}")

    # Close any stored sessions
    try:
        for session_id in list(_session_storage.keys()):
            logger.debug(f"Closing stored session: {session_id}")
        _session_storage.clear()
    except Exception as e:
        logger.warning(f"Error clearing session storage: {e}")

    # Set shutdown event
    if _shutdown_event:
        _shutdown_event.set()

    logger.info("Cleanup completed")


def main():
    """Main entry point for the MCP server."""
    # T032: Setup graceful shutdown handlers
    _setup_signal_handlers()

    logger.info("Starting Scrapling MCP Server...")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Max retries: {settings.max_retries}")
    logger.info(f"Default timeout: {settings.default_timeout}s")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
