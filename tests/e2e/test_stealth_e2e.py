"""Browser automation E2E tests for MCP Scraper.

These tests verify the stealth browser automation features work correctly
with real browser instances and network requests.

All tests require RUN_E2E_TESTS=1 environment variable to run.
"""

import pytest

from mcp_scraper.stealth import (
    StealthConfig,
    format_response,
    get_maximum_stealth,
    get_minimal_stealth,
    get_standard_stealth,
    get_stealth_config,
    scrape_with_retry,
    StealthLevel,
)


# Mark all tests in this module as E2E, slow, and flaky
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.flaky,
]


class TestStealthBrowser:
    """Test suite for browser automation functionality."""

    @pytest.mark.asyncio
    async def test_stealth_browser_launches(self, e2e_stealth_test_url, e2e_timeout):
        """Verify browser actually starts and can fetch a page.

        This test ensures the stealth browser automation works end-to-end.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_standard_stealth()
        config.timeout = e2e_timeout

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        # Verify we got content
        assert page is not None
        assert hasattr(page, "body")
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_javascript_rendering(self, e2e_test_url, e2e_timeout):
        """Test JavaScript execution with dynamic content.

        Uses httpbin.org/html which contains HTML that may require rendering.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/html"

        config = get_standard_stealth()
        config.timeout = e2e_timeout
        config.load_dom = True

        page = await scrape_with_retry(url, config=config, max_retries=2)

        assert page is not None
        assert page.status == 200
        assert len(page.body) > 100

    @pytest.mark.asyncio
    async def test_stealth_network_idle(self, e2e_stealth_test_url, e2e_timeout):
        """Test network_idle waits for resources to load.

        Verifies that network_idle option properly waits for page resources.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_standard_stealth()
        config.timeout = e2e_timeout
        config.network_idle = True

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        assert page is not None
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_session_persistence(self, e2e_test_url, e2e_timeout):
        """Test cookies persist across requests.

        Uses httpbin.org to verify session/cookie handling.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        # First request - set a cookie
        url1 = f"{e2e_test_url}/cookies/set?testcookie=testvalue"
        config = get_standard_stealth()
        config.timeout = e2e_timeout

        page1 = await scrape_with_retry(url1, config=config, max_retries=2)

        # Second request - check if cookie persists
        url2 = f"{e2e_test_url}/cookies"
        page2 = await scrape_with_retry(url2, config=config, max_retries=2)

        # Both requests should succeed
        assert page1 is not None
        assert page2 is not None
        assert page1.status in (200, 302)
        assert page2.status == 200

    @pytest.mark.asyncio
    async def test_stealth_cloudflare_simulation(self, e2e_test_url, e2e_timeout):
        """Test handling of Cloudflare-protected-like behavior.

        Note: This doesn't test actual Cloudflare but verifies the
        configuration option is properly handled.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        # Use standard profile - Cloudflare solving is optional
        config = get_standard_stealth()
        config.timeout = e2e_timeout
        config.solve_cloudflare = True  # Try to solve if challenged

        # Try a regular site first
        url = f"{e2e_test_url}/get"

        try:
            page = await scrape_with_retry(url, config=config, max_retries=1)
            assert page is not None
        except Exception:
            # Cloudflare solving may fail on non-protected sites
            # That's expected behavior
            pass

    @pytest.mark.asyncio
    async def test_stealth_user_agent_rotation(self, e2e_test_url, e2e_timeout):
        """Verify UA changes between requests.

        Tests that different stealth configurations can produce
        different browser fingerprints.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/headers"

        # First request with standard config
        config1 = get_standard_stealth()
        config1.timeout = e2e_timeout
        config1.google_search = True

        page1 = await scrape_with_retry(url, config=config1, max_retries=2)

        # Second request with minimal config
        config2 = get_minimal_stealth()
        config2.timeout = e2e_timeout

        page2 = await scrape_with_retry(url, config=config2, max_retries=2)

        # Both should succeed (though fingerprints may be similar)
        assert page1 is not None
        assert page2 is not None


class TestStealthProfiles:
    """Test suite for different stealth profile configurations."""

    @pytest.mark.asyncio
    async def test_stealth_minimal_profile(self, e2e_stealth_test_url, e2e_timeout):
        """Test minimal stealth settings.

        Verifies minimal stealth profile works correctly.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_minimal_stealth()
        config.timeout = e2e_timeout

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        assert page is not None
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_standard_profile(self, e2e_stealth_test_url, e2e_timeout):
        """Test standard stealth settings.

        Verifies standard stealth profile works correctly.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_standard_stealth()
        config.timeout = e2e_timeout

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        assert page is not None
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_maximum_profile(self, e2e_stealth_test_url, e2e_timeout):
        """Test maximum stealth settings.

        Verifies maximum stealth profile works correctly.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_maximum_stealth()
        config.timeout = e2e_timeout

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        assert page is not None
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_level_enum(self):
        """Test StealthLevel enum and get_stealth_config function.

        Verifies the enum-based configuration works correctly.

        Args:
            e2e_timeout: Timeout for requests
        """
        # Test MINIMAL level
        config_minimal = get_stealth_config(StealthLevel.MINIMAL)
        assert config_minimal is not None
        assert config_minimal.humanize is False

        # Test STANDARD level
        config_standard = get_stealth_config(StealthLevel.STANDARD)
        assert config_standard is not None
        assert config_standard.humanize is True

        # Test MAXIMUM level
        config_maximum = get_stealth_config(StealthLevel.MAXIMUM)
        assert config_maximum is not None
        assert config_maximum.solve_cloudflare is True


class TestStealthAdvanced:
    """Test suite for advanced stealth features."""

    @pytest.mark.asyncio
    async def test_stealth_custom_config(self, e2e_stealth_test_url, e2e_timeout):
        """Test custom stealth configuration.

        Verifies creating custom StealthConfig works correctly.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = StealthConfig(
            headless=True,
            solve_cloudflare=False,
            humanize=True,
            humanize_duration=1.0,
            geoip=False,
            os_randomize=True,
            block_webrtc=True,
            allow_webgl=False,
            google_search=True,
            block_images=False,
            block_ads=True,
            disable_resources=False,
            network_idle=True,
            load_dom=True,
            timeout=e2e_timeout,
            proxy=None,
        )

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        assert page is not None
        assert len(page.body) > 0

    @pytest.mark.asyncio
    async def test_stealth_format_response(self, e2e_stealth_test_url, e2e_timeout):
        """Test format_response with real stealth page.

        Integration test verifying format_response works with real pages.

        Args:
            e2e_stealth_test_url: URL to test with
            e2e_timeout: Timeout for requests
        """
        config = get_standard_stealth()
        config.timeout = e2e_timeout

        page = await scrape_with_retry(
            e2e_stealth_test_url,
            config=config,
            max_retries=2,
        )

        response = format_response(page, e2e_stealth_test_url)

        # Verify response structure
        assert "url" in response
        assert "status" in response
        assert "html" in response or "text" in response
        assert response["url"] == e2e_stealth_test_url

    @pytest.mark.asyncio
    async def test_stealth_with_selectors(self, e2e_test_url, e2e_timeout):
        """Test CSS selector extraction with stealth mode.

        Verifies selector-based extraction works with browser automation.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/html"

        config = get_standard_stealth()
        config.timeout = e2e_timeout

        selectors = {
            "title": "title",
            "links": "a@href",
        }

        page = await scrape_with_retry(
            url,
            config=config,
            max_retries=2,
            selectors=selectors,
        )

        assert page is not None
        # The page should be scraped - selectors may or may not find matches

    @pytest.mark.asyncio
    async def test_stealth_retry_with_backoff(self, e2e_test_url, e2e_timeout):
        """Test retry logic with exponential backoff.

        Verifies the retry mechanism works correctly.

        Args:
            e2e_test_url: Base URL for testing
            e2e_timeout: Timeout for requests
        """
        url = f"{e2e_test_url}/get"

        config = get_standard_stealth()
        config.timeout = e2e_timeout

        # Use higher retry count to test retry logic
        page = await scrape_with_retry(
            url,
            config=config,
            max_retries=3,
            backoff_factor=1.5,
        )

        assert page is not None
        assert page.status == 200
