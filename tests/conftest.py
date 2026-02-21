"""Pytest configuration and fixtures for MCP Scraper tests."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from scrapling import Selector as Page


# ============================================================================
# Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session.

    This fixture ensures async tests have access to a shared event loop,
    which is particularly useful for tests that involve async operations.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Page/Response Objects
# ============================================================================


class MockPage:
    """Mock scrapling Page/Response object.

    This mock mimics the scrapling Selector/Response interface with the
    key attributes and methods used in the codebase:
    - .body: raw HTML content
    - .status: HTTP status code
    - .get_all_text(): full page text content
    - .css_first(): get first element matching selector
    - .get(): get elements matching selector
    """

    def __init__(
        self,
        body: str = "",
        status: int = 200,
        url: str = "https://example.com",
        title: str = "Example Title",
    ):
        self._body = body
        self.status = status
        self.url = url
        self._title = title
        self._html = body
        self.playwright = MagicMock()

    @property
    def body(self) -> str:
        """Return raw HTML content."""
        return self._body

    @property
    def html(self) -> str:
        """Return HTML content (alias for body)."""
        return self._html

    @property
    def title(self) -> str:
        """Return page title."""
        return self._title

    def get_all_text(self, strip: bool = False) -> str:
        """Extract all text content from the page.

        Args:
            strip: Whether to strip whitespace from text

        Returns:
            Extracted text content
        """
        # Simple text extraction from HTML
        text = self._body
        # Remove script and style tags
        import re

        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        if strip:
            text = text.strip()
        return text

    def css_first(self, selector: str):
        """Get first element matching CSS selector.

        Args:
            selector: CSS selector string

        Returns:
            Mock element or None
        """
        return MockElement(selector=selector, parent=self)

    def get(self, selector: str):
        """Get all elements matching CSS selector.

        Args:
            selector: CSS selector string

        Returns:
            List of mock elements or empty list
        """
        # Simple mock - return list with one element if body contains selector
        if selector.lstrip(" .#") in self._body:
            return [MockElement(selector=selector, parent=self)]
        return []

    @property
    def text(self) -> str:
        """Alias for get_all_text()."""
        return self.get_all_text(strip=True)


class MockElement:
    """Mock element for CSS selector results."""

    def __init__(
        self,
        selector: str,
        parent: MockPage | None = None,
        text: str = "",
        html: str = "",
        attributes: dict[str, str] | None = None,
    ):
        self._selector = selector
        self._parent = parent
        self._text = text
        self._html = html
        self._attributes = attributes or {}

        # If we have a parent, try to extract content
        if parent and not text and not html:
            self._extract_from_parent()

    def _extract_from_parent(self) -> None:
        """Extract content from parent page based on selector."""
        import re

        if not self._parent:
            return

        body = self._parent._body

        # Simple extraction for common selectors
        if "title" in self._selector.lower():
            match = re.search(r"<title>([^<]+)</title>", body, re.IGNORECASE)
            if match:
                self._text = match.group(1)
                self._html = f"<title>{match.group(1)}</title>"

    @property
    def text(self) -> str:
        """Get text content of element."""
        return self._text

    @property
    def inner_text(self) -> str:
        """Get inner text content."""
        return self._text

    @property
    def html(self) -> str:
        """Get HTML content."""
        return self._html

    @property
    def innerHTML(self) -> str:
        """Get inner HTML (alias)."""
        return self._html

    def get_all_text(self, strip: bool = False) -> str:
        """Get all text content."""
        text = self._text
        if strip:
            text = text.strip()
        return text

    def get_attribute(self, attr: str) -> str | None:
        """Get attribute value."""
        return self._attributes.get(attr)

    def __str__(self) -> str:
        return self._text or self._html or ""


# ============================================================================
# Mock Session Fixtures
# ============================================================================


@pytest.fixture
def mock_session():
    """Create a mock AsyncStealthySession.

    Returns an async mock that simulates the scrapling session interface.
    """
    session = AsyncMock()
    session.fetch = AsyncMock()
    session.start = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.playwright = MagicMock()
    return session


@pytest.fixture
async def mock_stealth_session(mock_session):
    """Create a mock AsyncStealthySession with proper async context manager.

    Args:
        mock_session: The base mock session

    Yields:
        Configured mock session
    """
    # Setup async context manager behavior
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    yield mock_session
    # Cleanup
    await mock_session.__aexit__(None, None, None)


# ============================================================================
# StealthConfig Fixtures
# ============================================================================


@pytest.fixture
def minimal_stealth_config():
    """Get minimal stealth configuration for fast, basic anti-detection."""
    from mcp_scraper.config import StealthConfig

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
    )


@pytest.fixture
def standard_stealth_config():
    """Get standard stealth configuration for balanced speed and anonymity."""
    from mcp_scraper.config import StealthConfig

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
    )


@pytest.fixture
def maximum_stealth_config():
    """Get maximum stealth configuration for heavily protected sites."""
    from mcp_scraper.config import StealthConfig

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
    )


# ============================================================================
# HTML Content Fixtures
# ============================================================================


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
</head>
<body>
    <header>
        <h1>Welcome to Test Site</h1>
        <nav>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
    </header>
    <main>
        <article>
            <h2 class="article-title">Sample Article Title</h2>
            <p class="article-content">This is the article content with some text.</p>
            <span class="author-name">John Doe</span>
            <time class="publish-date">2024-01-15</time>
        </article>
        <div class="summary">This is a summary of the article.</div>
        <a class="read-more" href="/article/1">Read More</a>
    </main>
    <footer>
        <p>&copy; 2024 Test Site</p>
    </footer>
</body>
</html>"""


@pytest.fixture
def sample_html_with_title():
    """HTML content with specific title for testing."""
    return """<!DOCTYPE html>
<html>
<head><title>Specific Test Title</title></head>
<body><h1>Content</h1></body>
</html>"""


@pytest.fixture
def sample_html_minimal():
    """Minimal HTML content for basic tests."""
    return "<html><body><p>Hello World</p></body></html>"


@pytest.fixture
def cloudflare_challenge_html():
    """HTML content representing a Cloudflare challenge page."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Just a moment...</title>
</head>
<body>
    <div class="cf-browser-verification">
        <h1>Cloudflare - Checking your browser before accessing...</h1>
        <p>This process is automatic. Your browser will redirect to your requested content once verified.</p>
    </div>
    <p>Cloudflare Ray ID: 1234567890</p>
</body>
</html>"""


@pytest.fixture
def blocked_html():
    """HTML content representing a blocked/access denied page."""
    return """<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body>
    <h1>403 Forbidden</h1>
    <p>Access to this page is denied.</p>
    <p>Rate limit exceeded. Please wait before retrying.</p>
</body>
</html>"""


# ============================================================================
# Mock Page Fixtures
# ============================================================================


@pytest.fixture
def mock_page(sample_html):
    """Create a mock page with sample HTML content."""
    return MockPage(body=sample_html, status=200, url="https://example.com", title="Test Page")


@pytest.fixture
def mock_page_with_title(sample_html_with_title):
    """Create a mock page with specific title."""
    return MockPage(
        body=sample_html_with_title,
        status=200,
        url="https://example.com",
        title="Specific Test Title",
    )


@pytest.fixture
def mock_page_404():
    """Create a mock page representing a 404 response."""
    return MockPage(
        body="<html><body><h1>404 Not Found</h1></body></html>",
        status=404,
        url="https://example.com/not-found",
    )


@pytest.fixture
def mock_page_cloudflare(cloudflare_challenge_html):
    """Create a mock page with Cloudflare challenge."""
    return MockPage(body=cloudflare_challenge_html, status=200, url="https://protected-site.com")


@pytest.fixture
def mock_page_blocked(blocked_html):
    """Create a mock page representing a blocked request."""
    return MockPage(body=blocked_html, status=403, url="https://example.com")


# ============================================================================
# Selector Fixtures
# ============================================================================


@pytest.fixture
def sample_selectors():
    """Sample CSS selectors for structured extraction."""
    return {
        "title": "h2.post-title",
        "titles": "h2.post-title",
        "content": "p.summary",
        "authors": "span.author",
        "dates": "time.published",
        "summaries": "p.summary",
        "links": "a.read-more@href",
    }


@pytest.fixture
def article_selectors():
    """CSS selectors for article content."""
    return {
        "title": "h2.article-title",
        "content": "p.article-content",
        "author": "span.author-name",
        "date": "time.publish-date",
    }


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def valid_urls():
    """List of valid URLs for testing."""
    return [
        "https://example.com",
        "https://example.org",
        "https://httpbin.org/html",
        "https://httpbin.org/status/200",
    ]


@pytest.fixture
def invalid_urls():
    """List of invalid URLs that should be rejected."""
    return [
        "http://localhost",
        "http://127.0.0.1",
        "http://::1",
        "http://192.168.1.1",
        "http://10.0.0.1",
        "http://172.16.0.1",
        "https://example.local",
        "file:///etc/passwd",
        "ftp://example.com",
    ]


@pytest.fixture
def proxy_list():
    """Sample proxy list for rotation testing."""
    return [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080",
    ]
