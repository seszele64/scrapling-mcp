"""Shared test data and mock objects for MCP Scraper tests.

This module provides reusable test fixtures and mock objects that can be
imported across unit and integration tests.
"""

import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock


# ============================================================================
# Sample URLs for Testing
# ============================================================================

VALID_URLS = [
    "https://example.com",
    "https://example.org",
    "https://httpbin.org/html",
    "https://httpbin.org/status/200",
    "https://httpbin.org/get",
    "https://www.wikipedia.org",
    "https://httpbin.org/headers",
    "https://example.com/page?param=value",
    "https://example.com/path/to/page",
    "https://subdomain.example.com",
    "https://example.com:8080",
    "https://example.com/path#anchor",
]

INVALID_URLS = [
    # Localhost variants
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://::1",
    "http://0.0.0.0",
    "http://::",
    "http://localhost.localdomain",
    # Private IP ranges
    "http://192.168.1.1",
    "http://192.168.0.1",
    "http://10.0.0.1",
    "http://10.10.10.10",
    "http://172.16.0.1",
    "http://172.17.0.1",
    "http://172.31.0.1",
    "http://169.254.0.1",  # Link-local
    # Internal hostnames
    "http://server.local",
    "http://machine.internal",
    "http://host.corp",
    "http://localhost.lan",
    # Dangerous protocols
    "file:///etc/passwd",
    "ftp://example.com",
    "ssh://example.com",
    "javascript:alert(1)",
]


EDGE_CASE_URLS = [
    # URL with special characters
    "https://example.com/path with spaces",
    "https://example.com/path?query=value with spaces",
    "https://example.com/utf8-ä-ü-ö",
    # Very long URL
    "https://example.com/" + ("a" * 1000),
    # URL without path
    "https://example.com",
    # URL with port and path
    "https://example.com:443/path",
    # IP address (should be valid if public)
    "https://93.184.216.34",  # example.com IP
]


# ============================================================================
# Sample HTML Content
# ============================================================================

SIMPLE_HTML = "<html><body><p>Hello World</p></body></html>"

BASIC_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
</head>
<body>
    <header>
        <h1>Welcome to Test Site</h1>
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

COMPLETE_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Complete Test Page</title>
    <meta name="description" content="A complete test page for scraping">
    <link rel="stylesheet" href="/styles.css">
    <script src="/app.js"></script>
</head>
<body>
    <header id="main-header">
        <nav class="navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
    </header>

    <main id="content">
        <section class="hero">
            <h1>Welcome to Our Site</h1>
            <p class="tagline">The best place for testing</p>
        </section>

        <section class="articles">
            <article class="blog-post" data-id="1">
                <h2 class="post-title">First Post</h2>
                <div class="post-content">
                    <p>Content of the first post.</p>
                </div>
                <div class="post-meta">
                    <span class="author">Jane Doe</span>
                    <time class="post-date" datetime="2024-01-01">January 1, 2024</time>
                </div>
            </article>

            <article class="blog-post" data-id="2">
                <h2 class="post-title">Second Post</h2>
                <div class="post-content">
                    <p>Content of the second post.</p>
                </div>
                <div class="post-meta">
                    <span class="author">John Smith</span>
                    <time class="post-date" datetime="2024-01-15">January 15, 2024</time>
                </div>
            </article>
        </section>

        <aside class="sidebar">
            <h3>Categories</h3>
            <ul class="categories">
                <li><a href="/category/tech">Technology</a></li>
                <li><a href="/category/science">Science</a></li>
            </ul>
        </aside>
    </main>

    <footer id="main-footer">
        <p>&copy; 2024 Test Site. All rights reserved.</p>
    </footer>
</body>
</html>"""

CLOUDFLARE_CHALLENGE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Just a moment...</title>
</head>
<body>
    <div id="cf-content">
        <div class="cf-browser-verification">
            <h1>Checking your browser before accessing...</h1>
            <p>This process is automatic. Your browser will redirect to your requested content once verified.</p>
            <div class="cf-spinner"></div>
        </div>
        <p>Cloudflare Ray ID: 1234567890</p>
    </div>
</body>
</html>"""

BLOCKED_PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>403 Forbidden</title>
</head>
<body>
    <div class="error-container">
        <h1>Access Denied</h1>
        <p>You do not have permission to access this page.</p>
        <p class="rate-limit">Rate limit exceeded. Please wait before retrying.</p>
        <p>Error code: 403-001</p>
    </div>
</body>
</html>"""

EMPTY_PAGE_HTML = "<html><head><title>Empty</title></head><body></body></html>"

TABLE_HTML = """<!DOCTYPE html>
<html>
<body>
    <table id="data-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr class="data-row">
                <td class="name">Item 1</td>
                <td class="value">100</td>
            </tr>
            <tr class="data-row">
                <td class="name">Item 2</td>
                <td class="value">200</td>
            </tr>
        </tbody>
    </table>
</body>
</html>"""

FORM_HTML = """<!DOCTYPE html>
<html>
<body>
    <form id="login-form" action="/login" method="POST">
        <input type="text" name="username" id="username" placeholder="Username">
        <input type="password" name="password" id="password" placeholder="Password">
        <button type="submit" id="submit-btn">Login</button>
    </form>
</body>
</html>"""


# ============================================================================
# Sample CSS Selectors
# ============================================================================

ARTICLE_SELECTORS = {
    "title": "h2.article-title",
    "content": "p.article-content",
    "author": "span.author-name",
    "date": "time.publish-date",
}

BLOG_SELECTORS = {
    "titles": "article.blog-post h2.post-title",
    "authors": "article.blog-post .post-meta .author",
    "dates": "article.blog-post .post-meta .post-date",
    "contents": "article.blog-post .post-content p",
}

NAVIGATION_SELECTORS = {
    "links": "nav a@href",
    "link_text": "nav a",
    "active_link": "nav a.active@href",
}

TABLE_SELECTORS = {
    "rows": "table#data-table tr.data-row",
    "names": "table#data-table td.name",
    "values": "table#data-table td.value",
}

FORM_SELECTORS = {
    "username_input": "input#username@name",
    "password_input": "input#password@name",
    "submit_button": "button#submit-btn@type",
    "form_action": "form#login-form@action",
}

METADATA_SELECTORS = {
    "title": "title",
    "description": "meta[name=description]@content",
    "keywords": "meta[name=keywords]@content",
}


# ============================================================================
# Mock Response Objects
# ============================================================================


class MockResponse:
    """Mock HTTP response object for testing.

    Attributes:
        status: HTTP status code
        body: Response body content
        url: Requested URL
        headers: Response headers
    """

    def __init__(
        self,
        status: int = 200,
        body: str = "",
        url: str = "https://example.com",
        headers: dict[str, str] | None = None,
    ):
        self.status = status
        self.body = body
        self.url = url
        self.headers = headers or {"content-type": "text/html"}

    @property
    def text(self) -> str:
        """Return response body as text."""
        return self.body

    @property
    def html(self) -> str:
        """Return response body as HTML."""
        return self.body


class MockPageObject:
    """Mock scrapling Page/Selector object for testing.

    This class provides a more complete mock of the scrapling Selector
    interface used throughout the codebase.
    """

    def __init__(
        self,
        body: str = "",
        status: int = 200,
        url: str = "https://example.com",
        title: str = "Test Page",
    ):
        self._body = body
        self.status = status
        self.url = url
        self._title = title

    @property
    def body(self) -> str:
        """Return raw HTML content."""
        return self._body

    @property
    def html(self) -> str:
        """Return HTML content."""
        return self._body

    @property
    def title(self) -> str:
        """Return page title."""
        return self._title

    def get_all_text(self, strip: bool = False) -> str:
        """Extract all text content from the page.

        Args:
            strip: Whether to strip whitespace

        Returns:
            Extracted text content
        """
        text = self._body
        # Remove script and style tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        if strip:
            text = text.strip()
        return text

    @property
    def text(self) -> str:
        """Alias for get_all_text()."""
        return self.get_all_text(strip=True)

    def css_first(self, selector: str) -> "MockElement | None":
        """Get first element matching CSS selector."""
        if selector.lower() == "title":
            return MockElement(text=self._title)
        # Simple check if selector appears in body
        if selector.lstrip(" .#") in self._body:
            return MockElement(selector=selector, parent=self)
        return None

    def get(self, selector: str) -> list["MockElement"]:
        """Get all elements matching CSS selector."""
        # Simple mock - return element if body contains selector
        clean_selector = selector.replace("::html", "").split("@")[0]
        # Very basic check
        if clean_selector in self._body or clean_selector.lstrip(".#") in self._body:
            return [MockElement(selector=selector, parent=self)]
        return []


class MockElement:
    """Mock element for CSS selector results.

    Provides common properties and methods that scrapling elements have.
    """

    def __init__(
        self,
        text: str = "",
        html: str = "",
        selector: str = "",
        parent: MockPageObject | None = None,
        attributes: dict[str, str] | None = None,
    ):
        self._text = text
        self._html = html
        self._selector = selector
        self._parent = parent
        self._attributes = attributes or {}

        # Auto-extract if parent provided
        if parent and not text and not html:
            self._extract_from_parent()

    def _extract_from_parent(self) -> None:
        """Extract content from parent page based on selector."""
        if not self._parent:
            return

        import re

        body = self._parent.body

        # Very simple extraction for testing
        if "title" in self._selector.lower():
            match = re.search(r"<title>([^<]+)</title>", body, re.IGNORECASE)
            if match:
                self._text = match.group(1)
                self._html = f"<title>{match.group(1)}</title>"

    @property
    def text(self) -> str:
        """Get text content."""
        return self._text

    @property
    def inner_text(self) -> str:
        """Get inner text."""
        return self._text

    @property
    def html(self) -> str:
        """Get HTML content."""
        return self._html

    @property
    def innerHTML(self) -> str:
        """Get inner HTML."""
        return self._html

    @property
    def outerHTML(self) -> str:
        """Get outer HTML."""
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
# Mock Session Classes
# ============================================================================


class MockStealthySession:
    """Mock AsyncStealthySession for testing.

    Provides a simplified async context manager that can be used
    to test session-based scraping logic.
    """

    def __init__(self, page: MockPageObject | None = None, **kwargs):
        self._page = page or MockPageObject(body=BASIC_PAGE_HTML)
        self._kwargs = kwargs
        self.playwright = MagicMock()
        self._entered = False

    async def fetch(self, url: str, **kwargs) -> MockPageObject:
        """Mock fetch method."""
        self._page.url = url
        return self._page

    async def start(self) -> None:
        """Mock start method."""
        self._entered = True

    async def __aenter__(self) -> "MockStealthySession":
        """Async context manager entry."""
        self._entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self._entered = False


# ============================================================================
# Helper Functions for Tests
# ============================================================================


def create_mock_page(
    html: str = BASIC_PAGE_HTML, status: int = 200, url: str = "https://example.com"
) -> MockPageObject:
    """Create a mock page object with given parameters.

    Args:
        html: HTML content
        status: HTTP status code
        url: Page URL

    Returns:
        MockPageObject instance
    """
    return MockPageObject(body=html, status=status, url=url)


def create_mock_element(
    text: str = "", html: str = "", attributes: dict[str, str] | None = None
) -> MockElement:
    """Create a mock element with given parameters.

    Args:
        text: Text content
        html: HTML content
        attributes: Element attributes

    Returns:
        MockElement instance
    """
    return MockElement(text=text, html=html, attributes=attributes)


def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML string.

    Args:
        html: HTML string

    Returns:
        Plain text content
    """
    # Remove script and style tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================================
# Export all shared test data
# ============================================================================

__all__ = [
    # URLs
    "VALID_URLS",
    "INVALID_URLS",
    "EDGE_CASE_URLS",
    # HTML Content
    "SIMPLE_HTML",
    "BASIC_PAGE_HTML",
    "COMPLETE_PAGE_HTML",
    "CLOUDFLARE_CHALLENGE_HTML",
    "BLOCKED_PAGE_HTML",
    "EMPTY_PAGE_HTML",
    "TABLE_HTML",
    "FORM_HTML",
    # CSS Selectors
    "ARTICLE_SELECTORS",
    "BLOG_SELECTORS",
    "NAVIGATION_SELECTORS",
    "TABLE_SELECTORS",
    "FORM_SELECTORS",
    "METADATA_SELECTORS",
    # Mock Classes
    "MockResponse",
    "MockPageObject",
    "MockElement",
    "MockStealthySession",
    # Helper Functions
    "create_mock_page",
    "create_mock_element",
    "extract_text_from_html",
]
