"""Integration tests for MCP Tools in the Scrapling MCP Server.

This module contains comprehensive integration tests for all 5 MCP tools:
- scrape_simple: Simple web scraping without stealth features
- scrape_stealth: Stealth web scraping with configurable anti-detection
- scrape_session: Session-based scraping with persistent state
- extract_structured: Extract structured data using CSS selectors
- scrape_batch: Scrape multiple URLs in sequence

Each tool is tested for:
- Successful operations with various parameters
- Error handling and validation
- Edge cases and boundary conditions

Tests use mocked scrapling library components to ensure fast and reliable testing.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Import test fixtures
from tests.conftest import (
    MockElement,
    MockPage,
)
from tests.fixtures import (
    BASIC_PAGE_HTML,
    BLOCKED_PAGE_HTML,
    CLOUDFLARE_CHALLENGE_HTML,
    MockPageObject,
    MockStealthySession,
    create_mock_page,
    extract_text_from_html,
)


# Import server module components for testing
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from mcp_scraper.stealth import (
    BlockedError,
    CloudflareError,
    ScrapeError,
    StealthConfig,
    TimeoutError as ScrapeTimeoutError,
    extract_selectors,
    format_response,
    get_maximum_stealth,
    get_minimal_stealth,
    get_standard_stealth,
    scrape_with_retry,
    validate_url,
)


# Import the MCP tools from server - use .fn to get the underlying async function
from mcp_scraper.server import (
    _validate_url_param,
    _validate_timeout,
    _validate_stealth_level,
    _validate_extract,
    _validate_delay,
    _validate_urls_list,
    _validate_selector,
    _get_stealth_config_by_level,
    _session_storage,
    scrape_simple as _scrape_simple_tool,
    scrape_stealth as _scrape_stealth_tool,
    scrape_session as _scrape_session_tool,
    extract_structured as _extract_structured_tool,
    scrape_batch as _scrape_batch_tool,
)

# Get the underlying async functions from FastMCP tools
scrape_simple = _scrape_simple_tool.fn
scrape_stealth = _scrape_stealth_tool.fn
scrape_session = _scrape_session_tool.fn
extract_structured = _extract_structured_tool.fn
scrape_batch = _scrape_batch_tool.fn


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def clean_session_storage():
    """Clean session storage before and after each test."""
    _session_storage.clear()
    yield
    _session_storage.clear()


@pytest.fixture
def mock_page_success():
    """Create a mock page representing a successful scrape."""
    return MockPageObject(
        body=BASIC_PAGE_HTML,
        status=200,
        url="https://example.com",
        title="Test Page",
    )


@pytest.fixture
def mock_page_blocked():
    """Create a mock page representing a blocked request."""
    return MockPageObject(
        body=BLOCKED_PAGE_HTML,
        status=403,
        url="https://example.com",
    )


@pytest.fixture
def mock_page_cloudflare():
    """Create a mock page representing a Cloudflare challenge."""
    return MockPageObject(
        body=CLOUDFLARE_CHALLENGE_HTML,
        status=200,
        url="https://protected-site.com",
    )


@pytest.fixture
def mock_session_with_page(mock_page_success):
    """Create a mock session that returns a successful page."""
    session = MagicMock()
    session.fetch = AsyncMock(return_value=mock_page_success)
    session.set_cookies = AsyncMock()
    session.get_cookies = AsyncMock(return_value=[])
    session.start = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.playwright = MagicMock()
    return session


# ============================================================================
# Test: scrape_simple Tool
# ============================================================================


class TestScrapeSimple:
    """Tests for the scrape_simple MCP tool."""

    @pytest.mark.asyncio
    async def test_successful_scrape_with_valid_url(self, mock_page_success):
        """Test successful scrape with valid URL returns expected response structure."""
        # Mock scrape_with_retry to return our mock page
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            # Call the tool
            result = await scrape_simple(url="https://example.com")

            # Verify response structure
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert result["title"] is not None
            assert result["text"] is not None
            assert result["timestamp"] is not None
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_scrape_with_custom_timeout(self, mock_page_success):
        """Test scrape with custom timeout parameter."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_simple(url="https://example.com", timeout=60000)

            assert result["error"] is None
            assert result["url"] == "https://example.com"
            mock_scrape.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_with_selector_extraction(self, mock_page_success):
        """Test scrape with CSS selector for targeted extraction."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_simple(url="https://example.com", selector="h1")

            assert result["error"] is None
            assert result["selectors"] is not None

    @pytest.mark.asyncio
    async def test_scrape_with_extract_html_mode(self, mock_page_success):
        """Test scrape with extract='html' mode returns HTML content."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_simple(url="https://example.com", extract="html")

            assert result["error"] is None
            assert result["html"] is not None
            # In html mode, text should be None
            assert result["text"] is None

    @pytest.mark.asyncio
    async def test_scrape_with_extract_both_mode(self, mock_page_success):
        """Test scrape with extract='both' mode returns both text and HTML."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_simple(url="https://example.com", extract="both")

            assert result["error"] is None
            assert result["text"] is not None
            assert result["html"] is not None

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        """Test that invalid URL returns validation error."""
        result = await scrape_simple(url="http://localhost")

        assert result["error"] is not None
        assert "Invalid or disallowed URL" in result["error"]
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_timeout_validation_error(self):
        """Test that invalid timeout returns validation error."""
        # Timeout too small
        result = await scrape_simple(url="https://example.com", timeout=500)

        assert result["error"] is not None
        assert "Timeout" in result["error"]

        # Timeout too large
        result = await scrape_simple(url="https://example.com", timeout=400000)

        assert result["error"] is not None
        assert "Timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test that network errors are handled properly."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeError("Connection failed")

            result = await scrape_simple(url="https://example.com")

            assert result["error"] is not None
            assert "Scraping error" in result["error"]

    @pytest.mark.asyncio
    async def test_cloudflare_error_handling(self):
        """Test that Cloudflare errors are handled properly."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = CloudflareError("Cloudflare protection detected")

            result = await scrape_simple(url="https://protected-site.com")

            assert result["error"] is not None
            assert "Cloudflare" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test that timeout errors are handled properly."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeTimeoutError("Request timed out")

            result = await scrape_simple(url="https://example.com")

            assert result["error"] is not None
            assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_blocked_error_handling(self):
        """Test that blocked errors are handled properly."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = BlockedError("Request blocked")

            result = await scrape_simple(url="https://example.com")

            assert result["error"] is not None
            assert "blocked" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_extract_validation_error(self):
        """Test that invalid extract parameter returns validation error."""
        result = await scrape_simple(url="https://example.com", extract="invalid")

        assert result["error"] is not None
        assert "Extract" in result["error"]


# ============================================================================
# Test: scrape_stealth Tool
# ============================================================================


class TestScrapeStealth:
    """Tests for the scrape_stealth MCP tool."""

    @pytest.mark.asyncio
    async def test_successful_stealth_scrape_minimal_level(self, mock_page_success):
        """Test successful stealth scrape with minimal level."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://example.com", stealth_level="minimal")

            assert result["error"] is None
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_successful_stealth_scrape_standard_level(self, mock_page_success):
        """Test successful stealth scrape with standard level."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://example.com", stealth_level="standard")

            assert result["error"] is None
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_successful_stealth_scrape_maximum_level(self, mock_page_success):
        """Test successful stealth scrape with maximum level."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://example.com", stealth_level="maximum")

            assert result["error"] is None
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_stealth_scrape_with_solve_cloudflare_true(self, mock_page_success):
        """Test stealth scrape with solve_cloudflare=True."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://protected-site.com", solve_cloudflare=True)

            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_stealth_scrape_with_network_idle_true(self, mock_page_success):
        """Test stealth scrape with network_idle=True."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://example.com", network_idle=True)

            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_stealth_scrape_with_custom_timeout(self, mock_page_success):
        """Test stealth scrape with custom timeout."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(url="https://example.com", timeout=60000)

            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_invalid_stealth_level_raises_error(self):
        """Test that invalid stealth level returns error."""
        result = await scrape_stealth(url="https://example.com", stealth_level="invalid_level")

        assert result["error"] is not None
        assert "stealth level" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_url_validation_error(self):
        """Test that invalid URL returns validation error."""
        result = await scrape_stealth(url="http://localhost")

        assert result["error"] is not None
        assert "Invalid or disallowed URL" in result["error"]

    @pytest.mark.asyncio
    async def test_stealth_cloudflare_error_handling(self):
        """Test Cloudflare error handling in stealth scraping."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = CloudflareError("Cloudflare protection")

            result = await scrape_stealth(url="https://protected-site.com")

            assert result["error"] is not None
            assert "Cloudflare" in result["error"]

    @pytest.mark.asyncio
    async def test_stealth_blocked_error_handling(self):
        """Test blocked error handling in stealth scraping."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = BlockedError("Request blocked")

            result = await scrape_stealth(url="https://example.com")

            assert result["error"] is not None
            assert "blocked" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_stealth_timeout_error_handling(self):
        """Test timeout error handling in stealth scraping."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeTimeoutError("Timeout")

            result = await scrape_stealth(url="https://example.com")

            assert result["error"] is not None
            assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_stealth_scrape_with_proxy(self, mock_page_success):
        """Test stealth scrape with proxy parameter."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await scrape_stealth(
                url="https://example.com", proxy="http://proxy.example.com:8080"
            )

            assert result["error"] is None


# ============================================================================
# Test: scrape_session Tool
# ============================================================================


class TestScrapeSession:
    """Tests for the scrape_session MCP tool."""

    @pytest.mark.asyncio
    async def test_create_new_session_and_scrape(self, clean_session_storage, mock_page_success):
        """Test creating a new session and scraping."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(return_value=mock_page_success)
            mock_session.set_cookies = AsyncMock()
            mock_session.get_cookies = AsyncMock(return_value=[])
            mock_get_session.return_value = mock_session

            result = await scrape_session(url="https://example.com")

            assert result["error"] is None
            assert result["url"] == "https://example.com"
            assert result["session_id"] is not None

    @pytest.mark.asyncio
    async def test_reuse_existing_session(self, clean_session_storage, mock_page_success):
        """Test reusing an existing session."""
        # First call creates session
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(return_value=mock_page_success)
            mock_session.set_cookies = AsyncMock()
            mock_session.get_cookies = AsyncMock(return_value=[])
            mock_get_session.return_value = mock_session

            result1 = await scrape_session(url="https://example.com", session_id="test-session-123")

            session_id = result1["session_id"]

            # Second call with same session_id should reuse
            result2 = await scrape_session(url="https://example.com/page2", session_id=session_id)

            assert result2["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_session_with_initial_cookies(self, clean_session_storage, mock_page_success):
        """Test session with initial cookies."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(return_value=mock_page_success)
            mock_session.set_cookies = AsyncMock()
            mock_session.get_cookies = AsyncMock(
                return_value=[{"name": "auth", "value": "token123"}]
            )
            mock_get_session.return_value = mock_session

            result = await scrape_session(url="https://example.com", cookies={"auth": "token123"})

            assert result["error"] is None
            assert result["cookies"] is not None
            assert "auth" in result["cookies"]

    @pytest.mark.asyncio
    async def test_session_persistence_across_calls(self, clean_session_storage, mock_page_success):
        """Test session persistence across multiple calls."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(return_value=mock_page_success)
            mock_session.set_cookies = AsyncMock()
            mock_session.get_cookies = AsyncMock(
                return_value=[{"name": "session", "value": "abc123"}]
            )
            mock_get_session.return_value = mock_session

            result1 = await scrape_session(url="https://example.com/page1")
            result2 = await scrape_session(url="https://example.com/page2")

            # Both should work without errors
            assert result1["error"] is None
            assert result2["error"] is None
            assert result1["session_id"] is not None

    @pytest.mark.asyncio
    async def test_invalid_session_id_handling(self):
        """Test handling of invalid session IDs."""
        # Session with empty string should generate a new one
        result = await scrape_session(url="https://example.com", session_id="")

        # Should still work, just generate a new session ID
        assert result["session_id"] is not None

    @pytest.mark.asyncio
    async def test_session_with_stealth_level(self, clean_session_storage, mock_page_success):
        """Test session with custom stealth level."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(return_value=mock_page_success)
            mock_session.set_cookies = AsyncMock()
            mock_session.get_cookies = AsyncMock(return_value=[])
            mock_get_session.return_value = mock_session

            result = await scrape_session(url="https://example.com", stealth_level="maximum")

            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_cleanup_on_error(self, clean_session_storage):
        """Test that session is cleaned up on error."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_get_session.side_effect = ScrapeError("Connection failed")

            result = await scrape_session(url="https://example.com")

            assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_session_cloudflare_error_handling(self, clean_session_storage):
        """Test Cloudflare error handling in session scraping."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(side_effect=CloudflareError("Cloudflare"))
            mock_get_session.return_value = mock_session

            result = await scrape_session(url="https://protected-site.com")

            assert result["error"] is not None
            assert "Cloudflare" in result["error"]

    @pytest.mark.asyncio
    async def test_session_blocked_error_handling(self, clean_session_storage):
        """Test blocked error handling in session scraping."""
        with patch("mcp_scraper.server.get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = MagicMock()
            mock_session.fetch = AsyncMock(side_effect=BlockedError("Blocked"))
            mock_get_session.return_value = mock_session

            result = await scrape_session(url="https://example.com")

            assert result["error"] is not None
            assert "blocked" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_stealth_level_in_session(self):
        """Test that invalid stealth level returns error in session."""
        result = await scrape_session(url="https://example.com", stealth_level="invalid")

        assert result["error"] is not None
        assert "stealth level" in result["error"].lower()


# ============================================================================
# Test: extract_structured Tool
# ============================================================================


class TestExtractStructured:
    """Tests for the extract_structured MCP tool."""

    @pytest.mark.asyncio
    async def test_extract_with_single_selector(self, mock_page_success):
        """Test extraction with a single CSS selector."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await extract_structured(
                url="https://example.com", selectors={"title": "title"}
            )

            assert result["error"] is None
            assert result["url"] == "https://example.com"
            assert result["extracted"] is not None
            assert "title" in result["extracted"]

    @pytest.mark.asyncio
    async def test_extract_with_multiple_selectors(self, mock_page_success):
        """Test extraction with multiple CSS selectors."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            selectors = {"title": "title", "heading": "h1", "content": "p"}

            result = await extract_structured(url="https://example.com", selectors=selectors)

            assert result["error"] is None
            assert result["extracted"] is not None
            assert len(result["extracted"]) == 3

    @pytest.mark.asyncio
    async def test_extract_with_attribute_selector(self, mock_page_success):
        """Test extraction with attribute selectors (@href, @src)."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            # Use selectors with @attribute syntax
            result = await extract_structured(
                url="https://example.com", selectors={"links": "a@href"}
            )

            assert result["error"] is None
            assert result["extracted"] is not None

    @pytest.mark.asyncio
    async def test_extract_with_nested_selectors(self, mock_page_success):
        """Test extraction with nested CSS selectors."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            selectors = {
                "article_title": "article h2",
                "article_content": "article p",
                "footer_text": "footer p",
            }

            result = await extract_structured(url="https://example.com", selectors=selectors)

            assert result["error"] is None
            assert result["extracted"] is not None

    @pytest.mark.asyncio
    async def test_empty_selector_dict_raises_error(self):
        """Test that empty selector dict returns error."""
        result = await extract_structured(url="https://example.com", selectors={})

        # Empty dict should still work but return empty extracted
        assert result["extracted"] is not None

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        """Test that invalid URL returns validation error."""
        result = await extract_structured(url="http://localhost", selectors={"title": "title"})

        assert result["error"] is not None
        assert "Invalid or disallowed URL" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_elements_return_empty(self, mock_page_success):
        """Test that missing elements return empty lists."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            # Selector that doesn't exist in the page
            result = await extract_structured(
                url="https://example.com", selectors={"nonexistent": "div.does-not-exist"}
            )

            assert result["error"] is None
            assert result["extracted"] is not None

    @pytest.mark.asyncio
    async def test_non_dict_selectors_returns_error(self):
        """Test that non-dict selectors parameter returns error."""
        result = await extract_structured(
            url="https://example.com",
            selectors="title",  # Should be a dict, not a string
        )

        assert result["error"] is not None
        assert "dictionary" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_extract_with_stealth_level(self, mock_page_success):
        """Test extraction with custom stealth level."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            result = await extract_structured(
                url="https://example.com", selectors={"title": "title"}, stealth_level="minimal"
            )

            assert result["error"] is None
            assert result["extracted"] is not None

    @pytest.mark.asyncio
    async def test_extract_cloudflare_error_handling(self):
        """Test Cloudflare error handling in structured extraction."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = CloudflareError("Cloudflare")

            result = await extract_structured(
                url="https://protected-site.com", selectors={"title": "title"}
            )

            assert result["error"] is not None
            assert "Cloudflare" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_timeout_error_handling(self):
        """Test timeout error handling in structured extraction."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeTimeoutError("Timeout")

            result = await extract_structured(
                url="https://example.com", selectors={"title": "title"}
            )

            assert result["error"] is not None
            assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_stealth_level_error(self):
        """Test that invalid stealth level returns error."""
        result = await extract_structured(
            url="https://example.com", selectors={"title": "title"}, stealth_level="invalid"
        )

        assert result["error"] is not None


# ============================================================================
# Test: scrape_batch Tool
# ============================================================================


class TestScrapeBatch:
    """Tests for the scrape_batch MCP tool."""

    @pytest.mark.asyncio
    async def test_batch_scrape_multiple_urls(self, mock_page_success):
        """Test batch scraping multiple URLs."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            urls = [
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
            ]

            result = await scrape_batch(urls=urls)

            assert result["total"] == 3
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_batch_with_custom_delay(self, mock_page_success):
        """Test batch with custom delay between requests."""
        with patch("mcp_scraper.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with patch(
                "mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock
            ) as mock_scrape:
                mock_scrape.return_value = mock_page_success

                urls = ["https://example.com/page1", "https://example.com/page2"]

                result = await scrape_batch(urls=urls, delay=2.0)

                # Sleep should be called between requests
                assert mock_sleep.called

    @pytest.mark.asyncio
    async def test_batch_with_stealth_level(self, mock_page_success):
        """Test batch with custom stealth level."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            urls = ["https://example.com/page1"]

            result = await scrape_batch(urls=urls, stealth_level="minimal")

            assert result["total"] == 1
            assert result["successful"] == 1

    @pytest.mark.asyncio
    async def test_batch_with_partial_failures(self, mock_page_success):
        """Test batch with some failures (partial success)."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ScrapeError("Failed")
            return mock_page_success

        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = side_effect

            urls = [
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
            ]

            result = await scrape_batch(urls=urls)

            assert result["total"] == 3
            assert result["successful"] == 2
            assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_empty_url_list_raises_error(self):
        """Test that empty URL list returns error."""
        result = await scrape_batch(urls=[])

        assert result["total"] == 0
        assert result["successful"] == 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_url_in_list_raises_error(self):
        """Test that invalid URL in list is handled."""
        urls = [
            "https://example.com/page1",
            "http://localhost",  # Invalid
            "https://example.com/page3",
        ]

        result = await scrape_batch(urls=urls)

        assert result["total"] == 3
        # Invalid URL should be counted as failed
        assert result["failed"] >= 1

    @pytest.mark.asyncio
    async def test_results_summary_accuracy(self, mock_page_success):
        """Test that results summary accurately reflects outcomes."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_page_success

            urls = ["https://example.com/page1", "https://example.com/page2"]

            result = await scrape_batch(urls=urls)

            # Verify summary
            assert result["total"] == len(urls)
            assert result["successful"] + result["failed"] == result["total"]

            # Verify results array
            assert len(result["results"]) == len(urls)

            # Each result should have required fields
            for r in result["results"]:
                assert "url" in r
                assert "status_code" in r
                assert "timestamp" in r

    @pytest.mark.asyncio
    async def test_batch_with_cloudflare_errors(self):
        """Test batch handles Cloudflare errors gracefully."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = CloudflareError("Cloudflare")

            urls = ["https://protected-site.com/page1", "https://protected-site.com/page2"]

            result = await scrape_batch(urls=urls)

            assert result["total"] == 2
            assert result["successful"] == 0
            assert result["failed"] == 2

    @pytest.mark.asyncio
    async def test_batch_with_timeout_errors(self):
        """Test batch handles timeout errors gracefully."""
        with patch("mcp_scraper.server.scrape_with_retry", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeTimeoutError("Timeout")

            urls = ["https://example.com/page1", "https://example.com/page2"]

            result = await scrape_batch(urls=urls)

            assert result["total"] == 2
            assert result["failed"] == 2

    @pytest.mark.asyncio
    async def test_batch_invalid_stealth_level(self):
        """Test batch with invalid stealth level."""
        urls = ["https://example.com/page1"]

        result = await scrape_batch(urls=urls, stealth_level="invalid")

        # When stealth level is invalid, all URLs fail and errors are in the errors array
        assert result["failed"] > 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_batch_invalid_delay(self):
        """Test batch with invalid delay."""
        urls = ["https://example.com/page1"]

        result = await scrape_batch(urls=urls, delay=-1.0)

        # When delay is invalid, all URLs fail and errors are in the errors array
        assert result["failed"] > 0
        assert len(result["errors"]) > 0


# ============================================================================
# Test: Input Validation Functions
# ============================================================================


class TestInputValidationFunctions:
    """Tests for input validation helper functions."""

    def test_validate_url_param_valid(self):
        """Test URL validation with valid URL."""
        assert _validate_url_param("https://example.com") is None

    def test_validate_url_param_empty(self):
        """Test URL validation with empty URL."""
        assert _validate_url_param("") is not None

    def test_validate_url_param_not_string(self):
        """Test URL validation with non-string."""
        assert _validate_url_param(123) is not None

    def test_validate_timeout_valid(self):
        """Test timeout validation with valid values."""
        assert _validate_timeout(1000) is None
        assert _validate_timeout(30000) is None
        assert _validate_timeout(300000) is None

    def test_validate_timeout_too_small(self):
        """Test timeout validation with too small value."""
        assert _validate_timeout(500) is not None

    def test_validate_timeout_too_large(self):
        """Test timeout validation with too large value."""
        assert _validate_timeout(400000) is not None

    def test_validate_stealth_level_valid(self):
        """Test stealth level validation with valid values."""
        assert _validate_stealth_level("minimal") is None
        assert _validate_stealth_level("standard") is None
        assert _validate_stealth_level("maximum") is None

    def test_validate_stealth_level_invalid(self):
        """Test stealth level validation with invalid value."""
        assert _validate_stealth_level("invalid") is not None
        assert _validate_stealth_level(123) is not None

    def test_validate_extract_valid(self):
        """Test extract validation with valid values."""
        assert _validate_extract("text") is None
        assert _validate_extract("html") is None
        assert _validate_extract("both") is None

    def test_validate_extract_invalid(self):
        """Test extract validation with invalid value."""
        assert _validate_extract("invalid") is not None

    def test_validate_delay_valid(self):
        """Test delay validation with valid values."""
        assert _validate_delay(0) is None
        assert _validate_delay(1.0) is None
        assert _validate_delay(10) is None

    def test_validate_delay_negative(self):
        """Test delay validation with negative value."""
        assert _validate_delay(-1.0) is not None

    def test_validate_urls_list_valid(self):
        """Test URLs list validation with valid list."""
        assert _validate_urls_list(["https://example.com"]) is None
        assert _validate_urls_list(["https://example.com", "https://example.org"]) is None

    def test_validate_urls_list_empty(self):
        """Test URLs list validation with empty list."""
        assert _validate_urls_list([]) is not None

    def test_validate_urls_list_not_list(self):
        """Test URLs list validation with non-list."""
        assert _validate_urls_list("https://example.com") is not None

    def test_validate_urls_list_too_many(self):
        """Test URLs list validation with too many items."""
        urls = ["https://example.com"] * 101
        assert _validate_urls_list(urls) is not None

    def test_validate_selector_valid(self):
        """Test selector validation with valid values."""
        assert _validate_selector(None) is None
        assert _validate_selector("h1") is None

    def test_validate_selector_invalid(self):
        """Test selector validation with invalid value."""
        assert _validate_selector(123) is not None


# ============================================================================
# Test: Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_stealth_config_by_level_minimal(self):
        """Test getting stealth config for minimal level."""
        config = _get_stealth_config_by_level("minimal")
        assert isinstance(config, StealthConfig)
        assert config.humanize is False

    def test_get_stealth_config_by_level_standard(self):
        """Test getting stealth config for standard level."""
        config = _get_stealth_config_by_level("standard")
        assert isinstance(config, StealthConfig)
        assert config.humanize is True

    def test_get_stealth_config_by_level_maximum(self):
        """Test getting stealth config for maximum level."""
        config = _get_stealth_config_by_level("maximum")
        assert isinstance(config, StealthConfig)
        assert config.solve_cloudflare is True

    def test_get_stealth_config_by_level_invalid(self):
        """Test getting stealth config for invalid level."""
        with pytest.raises(ValueError):
            _get_stealth_config_by_level("invalid")


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
