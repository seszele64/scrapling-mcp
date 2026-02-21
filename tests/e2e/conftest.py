"""Pytest configuration and fixtures for E2E tests.

This module provides fixtures and utilities specifically for end-to-end
testing of the MCP scraper with real network requests and browser automation.

E2E tests require the RUN_E2E_TESTS environment variable to be set.
"""

import asyncio
import os
from typing import Any

import pytest


# ============================================================================
# E2E Test Configuration
# ============================================================================

# Default test URLs
DEFAULT_HTTPBIN_URL = "https://httpbin.org"
DEFAULT_STEALTH_TEST_URL = "https://example.com"


def is_e2e_enabled() -> bool:
    """Check if E2E tests are enabled via environment variable.

    Returns:
        True if RUN_E2E_TESTS environment variable is set to a truthy value
    """
    return os.environ.get("RUN_E2E_TESTS", "").lower() in ("1", "true", "yes")


# ============================================================================
# Pytest Markers
# ============================================================================


def pytest_configure(config: Any) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests that require network access and real services",
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take longer than usual to complete",
    )
    config.addinivalue_line(
        "markers",
        "flaky: Tests that may fail intermittently due to external dependencies",
    )


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Modify test collection to skip E2E tests when not enabled.

    This hook runs after test collection and adds skip conditions
    to all tests marked with @pytest.mark.e2e when RUN_E2E_TESTS is not set.
    """
    if is_e2e_enabled():
        return

    skip_e2e = pytest.mark.skip(reason="E2E tests not enabled. Set RUN_E2E_TESTS=1 to run.")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


# ============================================================================
# E2E-Specific Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def e2e_test_url() -> str:
    """Get the base URL for HTTP E2E tests.

    Uses httpbin.org by default, or the URL specified in E2E_TEST_URL env var.

    Returns:
        Base URL for HTTP testing (default: https://httpbin.org)
    """
    return os.environ.get("E2E_TEST_URL", DEFAULT_HTTPBIN_URL)


@pytest.fixture(scope="session")
def e2e_stealth_test_url() -> str:
    """Get the URL for stealth/browser E2E tests.

    Uses example.com by default, or the URL specified in E2E_STEALTH_TEST_URL env var.

    Returns:
        URL for stealth testing (default: https://example.com)
    """
    return os.environ.get("E2E_STEALTH_TEST_URL", DEFAULT_STEALTH_TEST_URL)


@pytest.fixture(scope="session")
def e2e_timeout() -> int:
    """Get the timeout value for E2E tests in seconds.

    Default is 30 seconds, but can be overridden with E2E_TIMEOUT env var.
    E2E tests typically need longer timeouts due to browser startup time.

    Returns:
        Timeout in seconds (default: 30)
    """
    env_timeout = os.environ.get("E2E_TIMEOUT")
    if env_timeout:
        try:
            return int(env_timeout)
        except ValueError:
            pass
    return 30


@pytest.fixture
async def cleanup_session():
    """Fixture that ensures sessions are properly cleaned up after each test.

    This fixture yields a cleanup function that should be called after
    the test completes. It handles proper closure of stealth sessions
    to prevent resource leaks.

    Yields:
        Function to call for cleanup after test completes
    """
    # Import here to avoid circular imports
    from mcp_scraper.stealth import close_session

    cleanup_funcs: list[callable] = []

    yield lambda: [func() for func in cleanup_funcs]

    # Perform cleanup
    for func in cleanup_funcs:
        try:
            func()
        except Exception:
            pass

    # Always close the global session after each test
    try:
        await close_session()
    except Exception:
        pass


def skip_if_no_e2e() -> None:
    """Helper to skip tests when RUN_E2E_TESTS is not set.

    Raises:
        pytest.skip: If E2E tests are not enabled
    """
    if not is_e2e_enabled():
        pytest.skip("E2E tests not enabled. Set RUN_E2E_TESTS=1 to run.")


@pytest.fixture
def check_network_available() -> bool:
    """Verify network connectivity before running tests.

    This fixture checks if we can reach external test services.
    It will skip the test if no network is available.

    Returns:
        True if network is available, otherwise skips the test

    Raises:
        pytest.skip: If network is not available
    """
    import socket

    # Try to resolve a known host
    test_hosts = ["httpbin.org", "example.com", "1.1.1.1"]
    for host in test_hosts:
        try:
            socket.setdefaulttimeout(5)
            socket.gethostbyname(host)
            return True
        except (socket.gaierror, socket.timeout):
            continue

    pytest.skip("Network connectivity not available")


@pytest.fixture
def e2e_mark_e2e():
    """Marker fixture that ensures E2E tests are properly marked.

    This fixture checks for the RUN_E2E_TESTS environment variable
    and will skip the test if it's not set.

    Raises:
        pytest.skip: If E2E tests are not enabled
    """
    skip_if_no_e2e()
    return True


# ============================================================================
# Session Fixtures for E2E Tests
# ============================================================================


@pytest.fixture
async def e2e_stealth_session():
    """Create a stealth session for E2E testing.

    This fixture creates a fresh AsyncStealthySession for each test
    and ensures proper cleanup afterwards.

    Yields:
        AsyncStealthySession instance

    Raises:
        pytest.skip: If E2E tests are not enabled
    """
    skip_if_no_e2e()

    from mcp_scraper.stealth import get_session, get_standard_stealth

    session = None
    try:
        # Create a new session with standard stealth settings
        config = get_standard_stealth()
        session = await get_session(config)
        yield session
    finally:
        # Cleanup
        from mcp_scraper.stealth import close_session

        try:
            await close_session()
        except Exception:
            pass


# ============================================================================
# Helper Functions for E2E Tests
# ============================================================================


def should_skip_slow_tests() -> bool:
    """Check if slow tests should be skipped.

    Returns:
        True if slow tests should be skipped
    """
    # Check for explicit skip
    if os.environ.get("SKIP_SLOW_TESTS", "").lower() in ("1", "true", "yes"):
        return True

    # Check for CI environment that might want to skip slow tests
    if os.environ.get("CI", "").lower() == "true":
        # In CI, we might want to skip unless explicitly enabled
        if not is_e2e_enabled():
            return True

    return False


# ============================================================================
# Async Event Loop for E2E Tests
# ============================================================================


@pytest.fixture(scope="function")
def e2e_event_loop():
    """Create an event loop for each E2E test function.

    This ensures each test has a fresh event loop, which is important
    for browser automation tests that may leave state.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================================
# Retry Configuration for Flaky Tests
# ============================================================================


@pytest.fixture
def e2e_retry_count() -> int:
    """Get the retry count for flaky E2E tests.

    Returns:
        Number of retries for flaky tests (default: 2)
    """
    env_retry = os.environ.get("E2E_RETRY_COUNT")
    if env_retry:
        try:
            return int(env_retry)
        except ValueError:
            pass
    return 2
