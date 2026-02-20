"""Pytest configuration and fixtures for MCP Scraper tests."""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session.

    This fixture ensures async tests have access to a shared event loop,
    which is particularly useful for tests that involve async operations.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
