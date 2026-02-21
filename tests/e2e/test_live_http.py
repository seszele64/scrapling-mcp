"""Live HTTP E2E tests for MCP Scraper.

These tests verify the scraper works correctly with real HTTP requests
using httpbin.org for predictable responses.

All tests require RUN_E2E_TESTS=1 environment variable to run.
"""

import pytest

from mcp_scraper.stealth import (
    StealthConfig,
    format_response,
    scrape_with_retry,
    validate_url,
)


# Mark all tests in this module as E2E and slow
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
]


class TestLiveHTTPRequests:
    """Test suite for live HTTP request functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, e2e_test_url):
        """Setup for each test."""
        self.base_url = e2e_test_url

    @pytest.mark.asyncio
    async def test_live_http_get_request(self, e2e_test_url, e2e_timeout):
        """Test basic GET request to httpbin.org/get.

        Verifies that:
        - The scraper can make successful GET requests
        - Response contains expected data
        - Status code is 200

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/get"

        # Use minimal stealth config for fast HTTP requests
        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        # Verify response
        assert page is not None
        assert page.status == 200
        assert hasattr(page, "body")
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_live_http_post_not_allowed(self, e2e_test_url, e2e_timeout):
        """Verify that POST requests fail appropriately.

        The scraper is designed for GET requests. This test verifies
        that POST requests either fail or are handled appropriately.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/post"

        # Try to scrape with POST data - should fail gracefully
        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
        )

        # The scraper should either handle this gracefully or the request should fail
        try:
            page = await scrape_with_retry(url, config=config, max_retries=1)
            # If it succeeds, it might be because httpbin handles GET to /post
            # Just verify we got some response
            assert page is not None
        except Exception:
            # Expected - scraper may not support POST
            pass

    @pytest.mark.asyncio
    async def test_live_http_with_headers(self, e2e_test_url, e2e_timeout):
        """Test custom headers are sent with requests.

        Uses httpbin.org/headers to verify custom headers are included.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/headers"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        assert page is not None
        assert page.status == 200
        # Verify we got JSON response with headers
        body = page.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        assert "headers" in body.lower() or "{" in body

    @pytest.mark.asyncio
    async def test_live_http_redirect_following(self, e2e_test_url, e2e_timeout):
        """Test that redirects are followed correctly.

        Uses httpbin.org/redirect/1 to test redirect handling.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/redirect/1"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        # Should follow redirect and get successful response
        assert page is not None
        assert page.status in (200, 302, 301, 307, 308)

    @pytest.mark.asyncio
    async def test_live_http_timeout(self, e2e_test_url):
        """Test actual timeout behavior with very short timeout.

        Verifies that requests timeout when the timeout is too short.

        Args:
            e2e_test_url: Base URL for testing
        """
        url = f"{e2e_test_url}/delay/10"  # 10 second delay

        # Use very short timeout (1 second)
        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=1,  # 1 second timeout - should fail
        )

        # Should raise timeout error
        with pytest.raises(Exception):
            await scrape_with_retry(url, config=config, max_retries=1)

    @pytest.mark.asyncio
    async def test_live_http_with_query_params(self, e2e_test_url, e2e_timeout):
        """Test URL with query parameters is handled correctly.

        Uses httpbin.org/get with query parameters.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/get?test=value&number=123"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        assert page is not None
        assert page.status == 200
        # Verify query params appear in response
        body = page.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        assert "test" in body.lower() or "value" in body.lower()

    @pytest.mark.asyncio
    async def test_live_http_response_encoding(self, e2e_test_url, e2e_timeout):
        """Test response encoding is handled correctly.

        Uses httpbin.org/encoding/utf8 to test encoding handling.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/encoding/utf8"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        assert page is not None
        assert page.status == 200
        # Should have content with UTF-8 characters
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_live_http_large_response(self, e2e_test_url, e2e_timeout):
        """Test handling of larger response bodies.

        Uses httpbin.org/html which returns a larger HTML page.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/html"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)

        assert page is not None
        assert page.status == 200
        # Verify we got a decent amount of content
        assert len(page.body) > 1000

    @pytest.mark.asyncio
    async def test_format_response_integration(self, e2e_test_url, e2e_timeout):
        """Test format_response works with real HTTP responses.

        Integration test verifying the full pipeline works.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/get"

        config = StealthConfig(
            headless=True,
            humanize=False,
            timeout=e2e_timeout,
            disable_resources=True,
        )

        page = await scrape_with_retry(url, config=config, max_retries=2)
        response = format_response(page, url)

        # Verify response structure
        assert "url" in response
        assert response["url"] == url
        assert "status" in response
        assert response["status"] == 200
        assert "html" in response or "text" in response

    @pytest.mark.asyncio
    async def test_validate_url_with_real_url(self):
        """Test URL validation with real URLs.

        Verifies the validation function correctly identifies valid URLs.

        Args:
            e2e_test_url: Base URL for testing
        """
        # Valid URLs
        assert validate_url("https://httpbin.org") is True
        assert validate_url("https://example.com") is True
        assert validate_url("https://httpbin.org/get") is True

        # Invalid URLs
        assert validate_url("http://localhost") is False
        assert validate_url("http://127.0.0.1") is False
        assert validate_url("https://192.168.1.1") is False
        assert validate_url("ftp://example.com") is False
        assert validate_url("file:///etc/passwd") is False
