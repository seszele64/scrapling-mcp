# VDD Testing Instructions for MCP Scraper

This document provides comprehensive testing instructions for the Scrapling MCP Server project following Verification-Driven Development (VDD) principles. It serves as the authoritative guide for implementing, verifying, and maintaining tests for all project components.

## Table of Contents

1. [VDD Overview for This Project](#1-vdd-overview-for-this-project)
2. [Test Categories & Priorities](#2-test-categories--priorities)
3. [Test Structure](#3-test-structure)
4. [Mocking Strategy](#4-mocking-strategy)
5. [Verification Criteria Templates](#5-verification-criteria-templates)
6. [Running Tests](#6-running-tests)
7. [E2E Testing Guidelines](#7-e2e-testing-guidelines)
8. [Example Test Cases](#8-example-test-cases)

---

## 1. VDD Overview for This Project

### 1.1 What VDD Means for the MCP Scraper

Verification-Driven Development (VDD) for this MCP scraper project means:

- **Pre-implementation verification criteria**: Before writing any feature code, define concrete test cases that verify the feature works correctly
- **Executable specifications**: Tests serve as living documentation of expected behavior
- **Security-first validation**: Every feature must pass security tests before functionality tests
- **Failure-driven design**: Tests define how the code should fail, not just succeed

### 1.2 Why We're Using VDD Approach

The MCP scraper project has unique requirements that make VDD essential:

1. **Security criticality**: The server makes HTTP requests to arbitrary URLs - SSRF vulnerabilities are catastrophic
2. **Complex stealth features**: Anti-detection settings must be verified to actually be applied
3. **Integration complexity**: Multiple layers (MCP protocol, scrapling library, browser automation) must work together
4. **Error handling diversity**: Many failure modes (Cloudflare, blocking, timeouts) must be handled gracefully

### 1.3 How to Verify Implementations

For each feature, follow this verification workflow:

```
1. Define verification criteria (this document)
   └─> Write test cases that fail first
2. Implement the feature
   └─> Run tests to verify implementation
3. Refactor with confidence
   └─> Tests ensure behavior preservation
4. Add edge cases
   └─> Expand test coverage
```

---

## 2. Test Categories & Priorities

### Priority 1: Security Tests (Critical)

Security tests must pass 100% before any other testing. These prevent catastrophic vulnerabilities.

#### URL Validation (`validate_url`)

**Location**: `src/mcp_scraper/stealth.py:746`

**What to test**:
- Allowed protocols (http, https)
- Blocked protocols (file, ftp, gopher, javascript, data)
- Private IP addresses (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
- Localhost variants (localhost, 127.0.0.1, ::1, 0.0.0.0)
- Internal hostnames (*.local, *.internal, *.corp, *.lan)
- Link-local addresses (169.254.x.x)
- Public IPs and domains (should pass)

**Expected behavior**:
- Returns `True` for safe URLs
- Returns `False` for dangerous URLs
- Logs warnings for blocked URLs

**Critical test cases**:
```python
# MUST ALL RETURN FALSE
validate_url("file:///etc/passwd")           # Dangerous protocol
validate_url("ftp://example.com")             # Dangerous protocol
validate_url("http://localhost")              # Localhost
validate_url("http://127.0.0.1")             # Loopback
validate_url("http://10.0.0.1")              # Private IP (10.0.0.0/8)
validate_url("http://172.16.0.1")             # Private IP (172.16.0.0/12)
validate_url("http://192.168.0.1")            # Private IP (192.168.0.0/16)
validate_url("http://169.254.169.254")        # Link-local (AWS metadata)
validate_url("http://machine.local")          # Internal hostname
validate_url("http://api.internal")           # Internal hostname

# MUST ALL RETURN TRUE
validate_url("https://example.com")           # Standard HTTPS
validate_url("http://example.com")            # Standard HTTP
validate_url("https://subdomain.example.com") # Subdomain
validate_url("https://93.184.216.34")        # Public IP
validate_url("https://example.com:8080")      # Non-standard port
```

#### Input Validation (MCP Tools)

**Location**: `src/mcp_scraper/server.py:43-161` (validation functions)

**What to test**:
- URL parameter validation (`_validate_url_param`)
- Timeout parameter validation (`_validate_timeout`)
- Stealth level validation (`_validate_stealth_level`)
- Extract parameter validation (`_validate_extract`)
- Delay parameter validation (`_validate_delay`)
- URLs list validation (`_validate_urls_list`)
- Selector parameter validation (`_validate_selector`)

**Expected behavior**:
- Returns `None` for valid inputs
- Returns error message string for invalid inputs

#### Proxy Validation

**What to test**:
- Valid proxy formats are accepted
- Invalid proxy formats are rejected
- Proxy credentials in URL are handled

---

### Priority 2: Unit Tests (High)

Unit tests verify individual functions and classes in isolation.

#### 2.1 Configuration Classes

**StealthConfig (config.py)** - `src/mcp_scraper/config.py:10`

**Location**: `tests/unit/test_config.py` (create this file)

**What to test**:
- Default values are correct
- `to_dict()` produces correct output format
- All 40+ configuration attributes are present

**Test template**:
```python
def test_stealth_config_defaults():
    config = StealthConfig()
    
    # Core stealth settings
    assert config.headless is True
    assert config.solve_cloudflare is False
    assert config.humanize is True
    assert config.humanize_duration == 1.5
    assert config.timeout == 30000
    assert config.proxy is None
    
    # Network settings
    assert config.cookies == []
    assert config.extra_headers == {}

def test_stealth_config_to_dict():
    config = StealthConfig(
        headless=True,
        timeout=45000,
        proxy="http://proxy:8080"
    )
    result = config.to_dict()
    
    assert result["headless"] is True
    assert result["timeout"] == 45000
    assert result["proxy"] == "http://proxy:8080"
```

#### 2.2 Stealth Profiles

**Location**: `src/mcp_scraper/config.py:148-287` (`StealthProfiles` class)

**What to test**:
- `StealthProfiles.minimal()` returns correct configuration
- `StealthProfiles.standard()` returns correct configuration
- `StealthProfiles.maximum()` returns correct configuration
- `StealthProfiles.no_js()` returns correct configuration

**Profile verification matrix**:

| Setting | minimal | standard | maximum | no_js |
|---------|---------|----------|---------|-------|
| headless | True | True | True | True |
| solve_cloudflare | False | False | True | False |
| humanize | False | True | True | False |
| timeout | 15000 | 30000 | 60000 | 15000 |
| enable_js | True | True | True | **False** |
| block_webrtc | False | True | True | False |

**Test template**:
```python
def test_stealth_profiles_minimal():
    config = StealthProfiles.minimal()
    
    assert config.headless is True
    assert config.solve_cloudflare is False
    assert config.humanize is False
    assert config.timeout == 15000
    assert config.block_webrtc is False
    assert config.os_randomize is False

def test_stealth_profiles_maximum():
    config = StealthProfiles.maximum()
    
    assert config.headless is True
    assert config.solve_cloudflare is True
    assert config.humanize is True
    assert config.geoip is True
    assert config.timeout == 60000
    assert config.wait_selector == "body"
    assert config.wait_selector_state == "visible"
```

#### 2.3 Response Formatting

**Location**: `src/mcp_scraper/stealth.py:503`

**Function**: `format_response(page, url, selectors)`

**What to test**:
- Returns URL in response
- Returns timestamp in ISO format
- Extracts title correctly
- Extracts text content
- Extracts HTML content
- Handles missing attributes gracefully

**Mock page object structure**:
```python
class MockPage:
    def __init__(self):
        self.status = 200
        self.body = "<html><body><h1>Test</h1></body></html>"
    
    def css_first(self, selector):
        return MockElement("Test Title")
    
    def get_all_text(self, strip=True):
        return "Test content"
```

#### 2.4 CSS Selector Extraction

**Location**: `src/mcp_scraper/stealth.py:584`

**Function**: `extract_selectors(page, selectors)`

**What to test**:
- Text extraction: `"h1"` returns text content
- HTML extraction: `"div::html"` returns inner HTML
- Attribute extraction: `"a@href"` returns href attribute
- Multiple attributes: `"img@src@alt"` returns dict
- No matches returns empty list or None

**Selector syntax tests**:
```python
# Test data structure
selectors = {
    "titles": "h1",
    "links": "a@href",
    "content_html": "div.content::html",
    "images_data": "img@src@alt",
    "empty": "div.does-not-exist"
}
```

---

### Priority 3: Integration Tests (Medium)

Integration tests verify end-to-end MCP tool flows.

#### 3.1 MCP Tool End-to-End Flows

**Tools to test**:
1. `scrape_simple` - Simple HTTP scraping
2. `scrape_stealth` - Browser automation with stealth
3. `scrape_session` - Session-based scraping
4. `extract_structured` - CSS selector extraction
5. `scrape_batch` - Multiple URL processing

**For each tool, test**:
- Valid input produces success response
- Invalid input produces error response
- Response structure matches specification
- Error messages are user-friendly

#### 3.2 Session Management

**Location**: `src/mcp_scraper/stealth.py:245`

**Functions**:
- `get_session(config)` - Get or create session
- `close_session()` - Close and cleanup session

**What to test**:
- Session is created with correct config
- Same config returns cached session
- Different config creates new session
- Session cleanup releases resources

#### 3.3 Error Handling

**Exception classes** (in `src/mcp_scraper/stealth.py:321-342`):
- `ScrapeError` - Base exception
- `CloudflareError` - Cloudflare protection detected
- `BlockedError` - Request blocked by anti-bot
- `TimeoutError` - Request timed out

**What to test**:
- Correct exception type is raised for each failure mode
- Exceptions contain helpful messages
- Exceptions are caught and handled gracefully in MCP tools

---

### Priority 4: E2E Tests (Low but Critical for Releases)

E2E tests verify the complete system works with real external dependencies. These are slow but essential for release validation.

#### E2E Test Requirements

**What makes an E2E test:**
- Uses real HTTP requests (not mocked)
- Tests against actual websites or local test server
- Verifies complete tool workflows
- Tests real browser automation (when applicable)

**When to run E2E tests:**
- Before releases
- After major changes to stealth/scraping logic
- In CI/CD pipelines (nightly or pre-release)
- Not during regular development (too slow)

**E2E Test Categories:**

1. **Live HTTP Tests**
   - Test against httpbin.org or similar
   - Verify request/response cycle works
   - Test timeout handling with real delays
   - Test redirect following

2. **Real Website Tests** (Optional/Conditional)
   - Test against known stable sites
   - Verify stealth features work in practice
   - Test Cloudflare bypass (if applicable)
   - **Must be skippable** (use pytest markers)

3. **Browser Automation Tests**
   - Test Playwright/Camoufox integration
   - Verify JavaScript rendering
   - Test stealth fingerprinting
   - Test session persistence

4. **Error Scenario Tests**
   - Test actual timeout behavior
   - Test DNS failure handling
   - Test SSL certificate errors
   - Test 4xx/5xx responses

#### E2E Test Markers

All E2E tests MUST be marked:
```python
@pytest.mark.e2e
@pytest.mark.slow  # If test takes >5 seconds
@pytest.mark.flaky  # If test depends on external services
@pytest.mark.skipif(not os.getenv("RUN_E2E_TESTS"), reason="E2E tests disabled")
```

#### E2E Test Isolation

- Each E2E test must be independent
- Tests must clean up resources (close browsers, sessions)
- Tests must handle external service failures gracefully
- Tests must not rely on specific external content

---

## 3. Test Structure

### 3.1 Directory Layout

```
tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_config.py          # Configuration tests
│   ├── test_validation.py      # URL validation tests
│   ├── test_stealth_profiles.py # Stealth profile tests
│   ├── test_response.py        # Response formatting tests
│   ├── test_selectors.py       # CSS selector extraction tests
│   └── test_exceptions.py      # Exception tests
├── integration/
│   ├── __init__.py
│   ├── test_tools.py           # MCP tool integration tests
│   ├── test_session.py         # Session management tests
│   └── test_error_handling.py  # Error propagation tests
├── security/
│   ├── __init__.py
│   ├── test_ssrf_blocking.py   # SSRF protection tests
│   └── test_input_sanitization.py # Input validation tests
└── e2e/
    ├── __init__.py
    ├── conftest.py              # E2E-specific fixtures
    ├── test_live_http.py        # Real HTTP tests
    ├── test_stealth_e2e.py     # Browser automation tests
    └── test_error_scenarios.py  # Real error handling
```

### 3.2 Naming Conventions

| File | Purpose | Example |
|------|---------|---------|
| `test_*.py` | Test module | `test_config.py` |
| `test_function_name` | Test function | `test_validate_url_blocks_localhost` |
| `test_class_method` | Class method test | `test_stealth_config_to_dict` |
| `test_integration_*` | Integration test | `test_integration_scrape_simple` |

### 3.3 Fixture Organization

**In `tests/conftest.py`**:

```python
"""Shared pytest fixtures for MCP Scraper tests."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from typing import Any

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock page fixture
@pytest.fixture
def mock_page() -> MagicMock:
    """Create a mock page object for testing."""
    page = MagicMock()
    page.status = 200
    page.body = "<html><body><h1>Test Title</h1><p>Content</p></body></html>"
    page.css_first = MagicMock(return_value=MagicMock(text="Test Title"))
    page.get_all_text = MagicMock(return_value="Test Title Content")
    return page

# Mock stealth config fixture
@pytest.fixture
def mock_stealth_config() -> MagicMock:
    """Create a mock StealthConfig."""
    config = MagicMock()
    config.headless = True
    config.solve_cloudflare = False
    config.humanize = True
    config.timeout = 30
    config.proxy = None
    config.to_scrapling_options.return_value = {
        "headless": True,
        "humanize": True,
        "timeout": 30000,
    }
    return config
```

---

## 4. Mocking Strategy

### 4.1 How to Mock Scrapling Library

The scrapling library is the core dependency that needs mocking for unit tests.

```python
# tests/unit/mocks.py
"""Mock objects for scrapling library."""

from unittest.mock import MagicMock, AsyncMock
from typing import Any

class MockPage:
    """Mock page object that mimics scrapling Selector."""
    
    def __init__(
        self,
        status: int = 200,
        body: str = "<html><body>Test</body></html>",
        title: str = "Test Title"
    ):
        self.status = status
        self.body = body
        self._title = title
    
    def css_first(self, selector: str) -> "MockElement | None":
        """Return mock element for CSS selector."""
        return MockElement(self._title)
    
    def get(self, selector: str) -> list["MockElement"] | "MockElement | None":
        """Return elements matching selector."""
        return MockElement("Matched content")
    
    def get_all_text(self, strip: bool = True) -> str:
        """Return all text content."""
        return "Test page content"


class MockElement:
    """Mock element for selector results."""
    
    def __init__(self, text: str = "", html: str = "", **attrs):
        self.text = text
        self.html = html
        self._attrs = attrs
    
    def __str__(self):
        return self.text or self.html or ""
    
    def get_attribute(self, name: str) -> str | None:
        """Get element attribute."""
        return self._attrs.get(name)


class MockAsyncStealthySession:
    """Mock AsyncStealthySession for testing."""
    
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self.playwright = MagicMock()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def fetch(self, url: str, **kwargs) -> MockPage:
        """Return mock page for URL."""
        return MockPage()
    
    async def start(self):
        """Start the session."""
        pass
    
    async def set_cookies(self, cookies: dict):
        """Set cookies."""
        pass
    
    async def get_cookies(self) -> list[dict]:
        """Get cookies."""
        return []


# Fixture for patching scrapling
@pytest.fixture
def mock_scrapling(monkeypatch):
    """Patch scrapling imports in stealth module."""
    import tests.unit.mocks as mocks
    
    monkeypatch.setattr(
        "scrapling.Selector",
        mocks.MockPage
    )
    monkeypatch.setattr(
        "scrapling.fetchers.AsyncStealthySession",
        mocks.MockAsyncStealthySession
    )
```

### 4.2 Mock HTTP Responses

For testing error handling without making actual requests:

```python
# Create specific error scenarios
def create_mock_page_with_cloudflare():
    """Create a page that triggers Cloudflare detection."""
    html = """
    <html>
    <head>
        <title>Checking your browser</title>
        <script src="/cdn-cgi/apps/head/..."></script>
    </head>
    <body>
        <h1>Checking your browser before accessing...</h1>
        <p>Cloudflare</p>
    </body>
    </html>
    """
    return MockPage(body=html)


def create_mock_page_blocked():
    """Create a page that shows access denied."""
    html = """
    <html>
    <body>
        <h1>403 Forbidden</h1>
        <p>Access denied</p>
    </body>
    </html>
    """
    return MockPage(status=403, body=html)


def create_mock_page_timeout():
    """Create a page that simulates timeout."""
    raise asyncio.TimeoutError("Request timed out")
```

### 4.3 Mock Browser Sessions

For testing session-based scraping:

```python
@pytest.fixture
def mock_browser_session():
    """Create a mock browser session with cookies."""
    
    class BrowserSession:
        def __init__(self):
            self._cookies = {}
            self._page = MockPage()
        
        async def fetch(self, url):
            return self._page
        
        async def set_cookies(self, cookies: dict):
            self._cookies.update(cookies)
        
        async def get_cookies(self) -> list[dict]:
            return [{"name": k, "value": v} for k, v in self._cookies.items()]
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
    
    return BrowserSession()
```

---

## 5. Verification Criteria Templates

### 5.1 URL Validation

**What to test**: Security-critical URL validation function

| Test Case | Input | Expected | Edge Cases |
|-----------|-------|----------|------------|
| HTTP allowed | `"http://example.com"` | `True` | - |
| HTTPS allowed | `"https://example.com"` | `True` | - |
| File protocol | `"file:///etc/passwd"` | `False` | - |
| FTP protocol | `"ftp://example.com"` | `False` | - |
| Localhost string | `"http://localhost"` | `False` | - |
| 127.0.0.1 | `"http://127.0.0.1"` | `False` | - |
| Private 10.x | `"http://10.0.0.1"` | `False` | 10.0.0.1 - 10.255.255.255 |
| Private 172.16-31 | `"http://172.16.0.1"` | `False` | 172.16.0.0 - 172.31.255.255 |
| Private 192.168 | `"http://192.168.0.1"` | `False` | 192.168.0.0 - 192.168.255.255 |
| Link-local | `"http://169.254.169.254"` | `False` | AWS metadata endpoint |
| Internal hostname | `"http://api.internal"` | `False` | Also .local, .corp, .lan |
| IPv6 loopback | `"http://[::1]"` | `False` | - |
| Valid public IP | `"http://93.184.216.34"` | `True` | - |

**Success criteria**:
- [ ] All blocked URLs return `False`
- [ ] All allowed URLs return `True`
- [ ] Blocking is logged with warnings
- [ ] Function handles malformed URLs without crashing

### 5.2 Stealth Configuration

**What to test**: Configuration classes and profiles

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Default config | `StealthConfig()` | All defaults set correctly |
| Custom timeout | `StealthConfig(timeout=45000)` | `to_dict()` returns 45000 |
| Minimal profile | `StealthProfiles.minimal()` | humanize=False, timeout=15000 |
| Standard profile | `StealthProfiles.standard()` | humanize=True, timeout=30000 |
| Maximum profile | `StealthProfiles.maximum()` | solve_cloudflare=True, timeout=60000 |

**Success criteria**:
- [ ] All 40+ config attributes have correct defaults
- [ ] `to_dict()` produces correct format for scrapling
- [ ] All four profiles return expected values
- [ ] Deprecated fields are properly mapped

### 5.3 MCP Tool: scrape_simple

**What to test**: Basic scraping tool

| Test Case | Input | Expected |
|-----------|-------|----------|
| Valid URL | `{"url": "https://example.com"}` | Success with content |
| Invalid URL | `{"url": "http://localhost"}` | Error response |
| With selector | `{"url": "...", "selector": "h1"}` | Selector data in response |
| Invalid timeout | `{"url": "...", "timeout": -1}` | Validation error |
| Extract modes | `{"extract": "text\|html\|both"}` | Correct fields in response |

**Response structure verification**:
```python
expected_keys = {
    "url", "status_code", "title", "text", "html",
    "headers", "selectors", "timestamp", "error"
}
```

**Success criteria**:
- [ ] Valid URL returns 200 with content
- [ ] Invalid URL returns error (not crash)
- [ ] All response keys present
- [ ] Selector extraction works
- [ ] Extract modes work correctly

### 5.4 MCP Tool: scrape_stealth

**What to test**: Stealth scraping with browser automation

| Test Case | Input | Expected |
|-----------|-------|----------|
| Minimal level | `{"stealth_level": "minimal"}` | Config with minimal settings |
| Standard level | `{"stealth_level": "standard"}` | Config with standard settings |
| Maximum level | `{"stealth_level": "maximum"}` | Config with maximum settings |
| Invalid level | `{"stealth_level": "invalid"}` | Validation error |
| With proxy | `{"proxy": "http://proxy:8080"}` | Proxy in config |
| Cloudflare solve | `{"solve_cloudflare": true}` | Override applied |

**Success criteria**:
- [ ] All three stealth levels produce correct configs
- [ ] Custom parameters override defaults
- [ ] Proxy is applied to request
- [ ] Invalid stealth level returns error

### 5.5 CSS Selector Extraction

**What to test**: Selector-based data extraction

| Test Case | Input | Expected |
|-----------|-------|----------|
| Text extraction | `{"selectors": {"h1": "h1"}}` | Text content returned |
| HTML extraction | `{"selectors": {"html": "div::html"}}` | HTML string returned |
| Attribute single | `{"selectors": {"links": "a@href"}}` | Attribute value |
| Attribute multiple | `{"selectors": {"img": "img@src@alt"}}` | Dict of attributes |
| No matches | `{"selectors": {"empty": ".nonexistent"}}` | Empty list or None |

**Success criteria**:
- [ ] Text extraction returns string
- [ ] HTML extraction returns HTML string
- [ ] Single attribute returns value
- [ ] Multiple attributes returns dict
- [ ] Non-matching returns None/[]

### 5.6 JSON String Selectors Parsing

**What to test**: The `selectors` parameter accepts both dict and JSON string formats

| Test Case | Input | Expected |
|-----------|-------|----------|
| Dict input | `{"selectors": {"title": "h1"}}` | Parsed as dict |
| JSON string | `{"selectors": "{\"title\": \"h1\"}"}` | Parsed as dict |
| Invalid JSON string | `{"selectors": "{not valid"}` | Validation error |
| Empty string | `{"selectors": ""}` | Validation error |

**Test implementation**:
```python
def test_selectors_json_string_parsing():
    """Test that selectors parameter accepts both dict and JSON string."""
    from mcp_scraper.server import _validate_selector
    
    # Dict input should work
    result = _validate_selector({"title": "h1"})
    assert result is None  # No error
    
    # JSON string should be parsed
    result = _validate_selector('{"title": "h1"}')
    assert result is None  # No error
    
    # Invalid JSON should return error
    result = _validate_selector("{invalid}")
    assert result is not None  # Error expected
```

**Success criteria**:
- [ ] Dict input is accepted and parsed correctly
- [ ] JSON string input is parsed into dict
- [ ] Invalid JSON returns validation error
- [ ] Empty string returns validation error

### 5.7 CSS Selector Extraction with page.css()

**What to test**: Using scrapling's css() method for element selection

| Test Case | Input | Expected |
|-----------|-------|----------|
| Single element | `page.css("h1")` | Returns element with .text |
| Multiple elements | `page.css("li")` | Returns list of elements |
| No match | `page.css(".nonexistent")` | Returns empty list |
| Nested selector | `page.css("ul > li")` | Returns matching elements |

**Test implementation**:
```python
class MockSelectorElement:
    """Mock element returned by page.css()."""
    def __init__(self, text="", html="", **attrs):
        self.text = text
        self.html = html
        self._attrs = attrs
    
    def get_all_text(self, strip=True):
        return self.text
    
    def __getitem__(self, key):
        return self._attrs.get(key)
    
    def get_attribute(self, name):
        return self._attrs.get(name)


class MockPageWithCss:
    """Mock page with css() method."""
    def __init__(self):
        self.body = "<html><body><h1>Title</h1></body></html>"
    
    def css(self, selector):
        if selector == "h1":
            return MockSelectorElement(text="Title", html="<h1>Title</h1>")
        elif selector == "li":
            return [
                MockSelectorElement(text="Item 1"),
                MockSelectorElement(text="Item 2"),
            ]
        return []  # No match


def test_css_method_returns_elements():
    """Test that page.css() returns usable elements."""
    page = MockPageWithCss()
    
    # Single element
    result = page.css("h1")
    assert len(result) == 1
    assert result[0].text == "Title"
    
    # Multiple elements
    result = page.css("li")
    assert len(result) == 2
    assert result[0].text == "Item 1"
    assert result[1].text == "Item 2"
    
    # No match
    result = page.css(".nonexistent")
    assert len(result) == 0
```

**Success criteria**:
- [ ] page.css() returns elements with .text property
- [ ] Multiple elements are returned as a list
- [ ] Non-matching selectors return empty list
- [ ] Elements support get_all_text() method

### 5.8 Element Extraction Helper Functions

**What to test**: Helper functions for extracting data from page elements

| Test Case | Input | Expected |
|-----------|-------|----------|
| get_element_text with .text | `get_element_text(el)` where `el.text = "Hello"` | Returns "Hello" |
| get_element_text with .inner_text | `get_element_text(el)` where `el.inner_text = "Hello"` | Returns "Hello" |
| get_element_text fallback | `get_element_text(el)` with no text props | Returns str(el) |
| get_element_html with .html | `get_element_html(el)` where `el.html = "<b>Hi</b>"` | Returns "<b>Hi</b>" |
| get_element_html with .innerHTML | `get_element_html(el)` where `el.innerHTML = "<b>Hi</b>"` | Returns "<b>Hi</b>" |
| get_element_html fallback | `get_element_html(el)` with no html props | Returns "" |
| get_element_attribute with get_attribute | `get_element_attribute(el, "href")` | Returns attribute value |
| get_element_attribute with property | `get_element_attribute(el, "href")` where `el.href = "..."` | Returns attribute value |
| get_element_attribute not found | `get_element_attribute(el, "nonexistent")` | Returns None |

**Test implementation**:
```python
from mcp_scraper.stealth import (
    get_element_text,
    get_element_html,
    get_element_attribute,
)


class TestGetElementText:
    """Tests for get_element_text() function."""
    
    def test_text_property(self):
        """Test extraction via .text property."""
        class MockElement:
            text = "Hello World"
        
        assert get_element_text(MockElement()) == "Hello World"
    
    def test_inner_text_property(self):
        """Test extraction via .inner_text property."""
        class MockElement:
            inner_text = "Hello World"
        
        assert get_element_text(MockElement()) == "Hello World"
    
    def test_fallback_to_str(self):
        """Test fallback to str()."""
        class MockElement:
            pass  # No text properties
        
        result = get_element_text(MockElement())
        assert isinstance(result, str)


class TestGetElementHtml:
    """Tests for get_element_html() function."""
    
    def test_html_property(self):
        """Test extraction via .html property."""
        class MockElement:
            html = "<div>Content</div>"
        
        assert get_element_html(MockElement()) == "<div>Content</div>"
    
    def test_innerHTML_property(self):
        """Test extraction via .innerHTML property."""
        class MockElement:
            innerHTML = "<div>Content</div>"
        
        assert get_element_html(MockElement()) == "<div>Content</div>"
    
    def test_fallback_empty_string(self):
        """Test fallback to empty string."""
        class MockElement:
            pass  # No html properties
        
        result = get_element_html(MockElement())
        assert result == ""


class TestGetElementAttribute:
    """Tests for get_element_attribute() function."""
    
    def test_get_attribute_method(self):
        """Test extraction via .get_attribute() method."""
        class MockElement:
            def get_attribute(self, name):
                return "https://example.com"
        
        assert get_element_attribute(MockElement(), "href") == "https://example.com"
    
    def test_direct_property(self):
        """Test extraction via direct property access."""
        class MockElement:
            href = "https://example.com"
        
        assert get_element_attribute(MockElement(), "href") == "https://example.com"
    
    def test_attribute_not_found(self):
        """Test returns None when attribute doesn't exist."""
        class MockElement:
            pass  # No href property
        
        assert get_element_attribute(MockElement(), "href") is None
```

**Success criteria**:
- [ ] get_element_text() extracts text via .text property
- [ ] get_element_text() falls back to .inner_text
- [ ] get_element_text() falls back to str()
- [ ] get_element_html() extracts HTML via .html property
- [ ] get_element_html() falls back to .innerHTML
- [ ] get_element_html() returns "" as fallback
- [ ] get_element_attribute() extracts via .get_attribute()
- [ ] get_element_attribute() falls back to direct property access
- [ ] get_element_attribute() returns None when not found

---

## 6. Running Tests

### 6.1 Test Commands

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run by priority (security first!)
pytest tests/security/ -v          # Security tests
pytest tests/unit/ -v              # Unit tests  
pytest tests/integration/ -v       # Integration tests

# Run specific test file
pytest tests/unit/test_config.py -v

# Run specific test
pytest tests/unit/test_validation.py::test_validate_url_blocks_localhost -v

# Run with coverage
pytest tests/ --cov=mcp_scraper --cov-report=html --cov-report=term

# Run with coverage and fail on low coverage
pytest tests/ --cov=mcp_scraper --cov-fail-under=80
```

### 6.2 Coverage Requirements

| Module | Minimum Coverage | Critical Functions |
|--------|------------------|-------------------|
| `stealth.py` | 80% | `validate_url`, `scrape_with_retry`, `format_response`, `extract_selectors` |
| `config.py` | 90% | All configuration classes |
| `server.py` | 70% | All MCP tools |

### 6.3 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run security tests first
        run: pytest tests/security/ -v --tb=short
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --tb=short
      
      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short
      
       - name: Check coverage
        run: |
          pytest tests/ \
            --cov=mcp_scraper \
            --cov-fail-under=80 \
            --cov-report=xml \
            --cov-report=term-missing
```

### E2E Test Execution

E2E tests are NOT run by default. To run them:

```bash
# Enable E2E tests
export RUN_E2E_TESTS=1

# Run E2E tests only
pytest tests/e2e/ -v

# Run all tests including E2E
pytest tests/ -v
```

**Note:** E2E tests require network access and may fail due to external factors. They should not block development but must pass before releases.

---

## 7. E2E Testing Guidelines

### 7.1 E2E Test Structure

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py              # E2E-specific fixtures
│   ├── test_live_http.py        # Real HTTP tests
│   ├── test_stealth_e2e.py     # Browser automation tests
│   └── test_error_scenarios.py  # Real error handling
```

### 7.2 Writing E2E Tests

**Template for Live HTTP Test:**
```python
import pytest
import os

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.getenv("RUN_E2E_TESTS"),
        reason="Set RUN_E2E_TESTS=1 to run E2E tests"
    ),
]

@pytest.mark.asyncio
async def test_live_http_request():
    """Test actual HTTP request to real endpoint."""
    from mcp_scraper.server import scrape_simple
    
    # Use httpbin.org for predictable responses
    result = await scrape_simple(url="https://httpbin.org/get")
    
    assert result["error"] is None
    assert result["status_code"] == 200
    assert "httpbin.org" in result.get("text", "")
```

**Template for Stealth E2E Test:**
```python
@pytest.mark.asyncio
async def test_stealth_browser_launch():
    """Test that browser actually launches and renders JS."""
    from mcp_scraper.server import scrape_stealth
    
    # Test against a site with JavaScript
    result = await scrape_stealth(
        url="https://example.com",
        stealth_level="minimal",
        network_idle=True
    )
    
    assert result["error"] is None
    assert result["status_code"] == 200
    # Verify content was actually rendered
    assert len(result.get("text", "")) > 0
```

### 7.3 E2E Test Configuration

**Environment Variables:**
```bash
# Required to run E2E tests
export RUN_E2E_TESTS=1

# Optional: Specific test sites
export E2E_TEST_URL=https://httpbin.org
export E2E_STEALTH_TEST_URL=https://example.com

# Optional: Skip slow tests
export SKIP_SLOW_TESTS=1
```

**pytest.ini Configuration:**
```ini
[pytest]
markers =
    e2e: End-to-end tests with real external services
    slow: Tests that take >5 seconds
    flaky: Tests that may fail due to external factors
    network: Tests requiring network access
```

### 7.4 Running E2E Tests

```bash
# Run only E2E tests
RUN_E2E_TESTS=1 pytest tests/e2e/ -v

# Run E2E tests with coverage
RUN_E2E_TESTS=1 pytest tests/e2e/ --cov=mcp_scraper --cov-report=html

# Skip slow E2E tests
RUN_E2E_TESTS=1 SKIP_SLOW_TESTS=1 pytest tests/e2e/ -v

# Run all tests including E2E
RUN_E2E_TESTS=1 pytest tests/ -v

# Run only unit and integration (default)
pytest tests/unit tests/integration -v
```

### 7.5 E2E Test Best Practices

1. **Use Stable Test Targets**
   - Prefer httpbin.org, postman-echo.com, or similar
   - Avoid testing against production sites
   - Consider running local test server

2. **Handle External Failures**
   ```python
   @pytest.mark.flaky(reruns=3)
   async def test_external_service():
       try:
           result = await scrape_simple(url="https://example.com")
       except NetworkError:
           pytest.skip("External service unavailable")
   ```

3. **Resource Cleanup**
   ```python
   @pytest.fixture(autouse=True)
   async def cleanup():
       yield
       # Cleanup after each test
       from mcp_scraper.stealth import close_session
       await close_session()
   ```

4. **Test Data Independence**
   - Don't rely on specific content from external sites
   - Test structure/behavior, not content
   - Use regex or partial matching

### 7.6 E2E Verification Checklist

Before marking E2E tests complete:

- [ ] Test runs successfully 3 times in a row
- [ ] Test cleans up all resources
- [ ] Test handles external service downtime gracefully
- [ ] Test is marked with appropriate pytest markers
- [ ] Test doesn't take >30 seconds (unless marked slow)
- [ ] Test doesn't rely on specific external content
- [ ] Test works in CI environment
- [ ] Test documents its external dependencies

---

## 8. Example Test Cases

### 8.1 validate_url() Function

**File**: `tests/unit/test_validation.py`

```python
"""Unit tests for URL validation function."""

import pytest
from mcp_scraper.stealth import validate_url


class TestURLValidation:
    """Test suite for validate_url() security function."""
    
    # === ALLOWED URLS ===
    
    @pytest.mark.parametrize("url", [
        "https://example.com",
        "http://example.com",
        "https://www.example.com",
        "https://subdomain.example.com",
        "https://example.com:8080",
        "https://example.com:443/path",
        "https://example.com/path?query=1",
        "https://93.184.216.34",  # Public IP
        "https://93.184.216.34:8080",
    ])
    def test_valid_urls_allowed(self, url):
        """Valid public URLs should be allowed."""
        assert validate_url(url) is True
    
    # === BLOCKED PROTOCOLS ===
    
    @pytest.mark.parametrize("url", [
        "file:///etc/passwd",
        "ftp://example.com",
        "gopher://example.com",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ssh://example.com",
    ])
    def test_dangerous_protocols_blocked(self, url):
        """Non-HTTP protocols should be blocked."""
        assert validate_url(url) is False
    
    # === LOCALHOST VARIANTS ===
    
    @pytest.mark.parametrize("url", [
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://[::1]",
        "http://0.0.0.0",
        "http://::",
        "http://localhost.localdomain",
    ])
    def test_localhost_blocked(self, url):
        """All localhost variants should be blocked."""
        assert validate_url(url) is False
    
    # === PRIVATE IP ADDRESSES ===
    
    @pytest.mark.parametrize("url", [
        # 10.0.0.0/8 range
        "http://10.0.0.1",
        "http://10.255.255.255",
        "http://10.128.0.1",
        
        # 172.16.0.0/12 range
        "http://172.16.0.1",
        "http://172.31.255.255",
        "http://172.17.0.1",
        "http://172.20.0.1",
        "http://172.30.0.1",
        
        # 192.168.0.0/16 range
        "http://192.168.0.1",
        "http://192.168.255.255",
        "http://192.168.1.100",
        
        # Loopback
        "http://127.0.0.1",
        "http://127.1.2.3",
    ])
    def test_private_ips_blocked(self, url):
        """Private IP address ranges should be blocked."""
        assert validate_url(url) is False
    
    # === LINK-LOCAL ADDRESSES ===
    
    @pytest.mark.parametrize("url", [
        "http://169.254.169.254",  # AWS metadata
        "http://169.254.0.1",
        "http://169.254.169.253",
    ])
    def test_linklocal_blocked(self, url):
        """Link-local addresses should be blocked."""
        assert validate_url(url) is False
    
    # === INTERNAL HOSTNAMES ===
    
    @pytest.mark.parametrize("url", [
        "http://machine.local",
        "http://api.internal",
        "http://server.corp",
        "http://computer.lan",
        "http://db.internal",
    ])
    def test_internal_hostnames_blocked(self, url):
        """Internal hostnames should be blocked."""
        assert validate_url(url) is False
    
    # === EDGE CASES ===
    
    def test_empty_url(self):
        """Empty URL should be rejected."""
        assert validate_url("") is False
    
    def test_url_without_scheme(self):
        """URL without scheme should be rejected."""
        assert validate_url("example.com") is False
    
    def test_url_with_only_path(self):
        """URL with only path should be rejected."""
        assert validate_url("/path/to/page") is False
    
    def test_malformed_url_handled(self):
        """Malformed URLs should not crash."""
        # Should return False, not raise exception
        assert validate_url("not-a-valid-url") is False
        assert validate_url("://") is False
        assert validate_url("http://") is False
```

### 8.2 StealthConfig Class

**File**: `tests/unit/test_config.py`

```python
"""Unit tests for configuration classes."""

import pytest
from mcp_scraper.config import StealthConfig, Settings, StealthProfiles


class TestStealthConfig:
    """Test suite for StealthConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are correct."""
        config = StealthConfig()
        
        # Core stealth settings
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is True
        assert config.humanize_duration == 1.5
        assert config.geoip is False
        assert config.os_randomize is True
        assert config.block_webrtc is True
        assert config.allow_webgl is True
        assert config.google_search is True
        assert config.block_images is False
        assert config.block_ads is True
        assert config.disable_resources is False
        assert config.network_idle is False
        assert config.load_dom is False
        assert config.wait_selector is None
        assert config.wait_selector_state is None
        assert config.timeout == 30000
        assert config.proxy is None
        
        # Legacy fields
        assert config.enable_js is True
        assert config.randomize_user_agent is True
        assert config.random_delay == (0.5, 2.0)
        assert config.viewport_size == (1920, 1080)
    
    def test_custom_values(self):
        """Test that custom values are set correctly."""
        config = StealthConfig(
            headless=False,
            timeout=60000,
            proxy="http://proxy:8080",
            solve_cloudflare=True,
        )
        
        assert config.headless is False
        assert config.timeout == 60000
        assert config.proxy == "http://proxy:8080"
        assert config.solve_cloudflare is True
    
    def test_to_dict_format(self):
        """Test that to_dict produces correct format."""
        config = StealthConfig(
            timeout=45000,
            proxy="http://proxy:8080",
            solve_cloudflare=True,
        )
        
        result = config.to_dict()
        
        # Check required keys exist
        assert "headless" in result
        assert "timeout" in result
        assert "proxy" in result
        assert "solve_cloudflare" in result
        
        # Check correct values
        assert result["headless"] is True
        assert result["timeout"] == 45000
        assert result["proxy"] == "http://proxy:8080"
        assert result["solve_cloudflare"] is True
        
        # Check legacy mappings
        assert result["javascript"] is True  # maps to enable_js
        assert result["images"] is True  # maps to not disable_images
    
    def test_cookies_and_headers(self):
        """Test network settings."""
        config = StealthConfig(
            cookies=[{"name": "session", "value": "abc123"}],
            extra_headers={"X-Custom": "value"},
        )
        
        result = config.to_dict()
        
        assert result["cookies"] == [{"name": "session", "value": "abc123"}]
        assert result["extra_headers"] == {"X-Custom": "value"}


class TestStealthProfiles:
    """Test suite for pre-configured stealth profiles."""
    
    def test_minimal_profile(self):
        """Test minimal stealth profile."""
        config = StealthProfiles.minimal()
        
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is False
        assert config.geoip is False
        assert config.os_randomize is False
        assert config.block_webrtc is False
        assert config.allow_webgl is False
        assert config.google_search is False
        assert config.block_images is True
        assert config.disable_resources is True
        assert config.network_idle is False
        assert config.load_dom is False
        assert config.timeout == 15000
    
    def test_standard_profile(self):
        """Test standard stealth profile."""
        config = StealthProfiles.standard()
        
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is True
        assert config.humanize_duration == 1.5
        assert config.geoip is False
        assert config.os_randomize is True
        assert config.block_webrtc is True
        assert config.allow_webgl is True
        assert config.google_search is True
        assert config.block_images is False
        assert config.disable_resources is False
        assert config.network_idle is True
        assert config.load_dom is True
        assert config.timeout == 30000
    
    def test_maximum_profile(self):
        """Test maximum stealth profile."""
        config = StealthProfiles.maximum()
        
        assert config.headless is True
        assert config.solve_cloudflare is True
        assert config.humanize is True
        assert config.humanize_duration == 1.5
        assert config.geoip is True
        assert config.os_randomize is True
        assert config.block_webrtc is True
        assert config.allow_webgl is True
        assert config.google_search is True
        assert config.block_images is False
        assert config.disable_resources is False
        assert config.network_idle is True
        assert config.load_dom is True
        assert config.wait_selector == "body"
        assert config.wait_selector_state == "visible"
        assert config.timeout == 60000
    
    def test_no_js_profile(self):
        """Test no-JS profile."""
        config = StealthProfiles.no_js()
        
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is False
        assert config.enable_js is False
        assert config.timeout == 15000


class TestSettings:
    """Test suite for application settings."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.proxy_url is None
        assert settings.default_timeout == 30
        assert settings.log_level == "INFO"
        assert settings.max_retries == 3
    
    def test_timeout_bounds(self):
        """Test timeout validation."""
        # Valid range
        settings = Settings(default_timeout=60)
        assert settings.default_timeout == 60
        
        # Below minimum - should raise
        with pytest.raises(ValueError):
            Settings(default_timeout=0)
        
        # Above maximum - should raise
        with pytest.raises(ValueError):
            Settings(default_timeout=500)
    
    def test_retries_bounds(self):
        """Test retries validation."""
        # Valid range
        settings = Settings(max_retries=5)
        assert settings.max_retries == 5
        
        # Below minimum
        with pytest.raises(ValueError):
            Settings(max_retries=-1)
        
        # Above maximum
        with pytest.raises(ValueError):
            Settings(max_retries=15)
```

### 8.3 MCP Tool Validation

**File**: `tests/integration/test_tools.py`

```python
"""Integration tests for MCP tools."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from mcp_scraper.server import (
    scrape_simple,
    scrape_stealth,
    scrape_session,
    extract_structured,
    scrape_batch,
)
from mcp_scraper.stealth import (
    MockPage,
    MockAsyncStealthySession,
)


class TestScrapeSimple:
    """Test suite for scrape_simple MCP tool."""
    
    @pytest.mark.asyncio
    async def test_valid_url_returns_content(self):
        """Test that valid URL returns success response."""
        mock_page = MockPage(
            status=200,
            body="<html><body><h1>Test</h1></body></html>",
            title="Test Page"
        )
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            mock_scrape.return_value = mock_page
            
            result = await scrape_simple(url="https://example.com")
            
            assert result["error"] is None
            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert "text" in result or "html" in result
    
    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        """Test that invalid URL returns error response."""
        result = await scrape_simple(url="http://localhost")
        
        assert result["error"] is not None
        assert "Invalid or disallowed" in result["error"]
        assert result["status_code"] is None
    
    @pytest.mark.asyncio
    async def test_empty_url_returns_error(self):
        """Test that empty URL returns validation error."""
        result = await scrape_simple(url="")
        
        assert result["error"] is not None
    
    @pytest.mark.asyncio
    async def test_invalid_timeout_rejected(self):
        """Test that invalid timeout is rejected."""
        result = await scrape_simple(
            url="https://example.com",
            timeout=500  # Below minimum of 1000
        )
        
        assert result["error"] is not None
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_selector_extraction(self):
        """Test that selector parameter extracts data."""
        mock_page = MagicMock()
        mock_page.status = 200
        mock_page.body = "<html><body><h1>Title</h1></body></html>"
        
        mock_element = MagicMock()
        mock_element.text = "Title"
        mock_page.css_first = MagicMock(return_value=mock_element)
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            mock_scrape.return_value = mock_page
            
            result = await scrape_simple(
                url="https://example.com",
                selector="h1"
            )
            
            assert "selectors" in result
    
    @pytest.mark.asyncio
    async def test_extract_modes(self):
        """Test different extract modes."""
        mock_page = MockPage()
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            mock_scrape.return_value = mock_page
            
            # Test text mode
            result = await scrape_simple(
                url="https://example.com",
                extract="text"
            )
            assert "text" in result
            
            # Test html mode
            result = await scrape_simple(
                url="https://example.com",
                extract="html"
            )
            assert "html" in result
            
            # Test both mode
            result = await scrape_simple(
                url="https://example.com",
                extract="both"
            )
            assert "text" in result
            assert "html" in result


class TestScrapeStealth:
    """Test suite for scrape_stealth MCP tool."""
    
    @pytest.mark.asyncio
    async def test_stealth_level_minimal(self):
        """Test minimal stealth level."""
        mock_page = MockPage()
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            with patch("mcp_scraper.server._get_stealth_config_by_level") as mock_config:
                mock_config.return_value = MagicMock(
                    solve_cloudflare=False,
                    humanize=False,
                    timeout=15,
                )
                mock_scrape.return_value = mock_page
                
                result = await scrape_stealth(
                    url="https://example.com",
                    stealth_level="minimal"
                )
                
                assert "error" not in result or result["error"] is None
    
    @pytest.mark.asyncio
    async def test_stealth_level_invalid(self):
        """Test that invalid stealth level returns error."""
        result = await scrape_stealth(
            url="https://example.com",
            stealth_level="invalid_level"
        )
        
        assert result["error"] is not None
    
    @pytest.mark.asyncio
    async def test_cloudflare_override(self):
        """Test that solve_cloudflare overrides profile."""
        mock_page = MockPage()
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            with patch("mcp_scraper.server._get_stealth_config_by_level") as mock_config:
                config_mock = MagicMock()
                config_mock.solve_cloudflare = False
                config_mock.network_idle = True
                config_mock.load_dom = True
                config_mock.timeout = 30
                config_mock.proxy = None
                mock_config.return_value = config_mock
                mock_scrape.return_value = mock_page
                
                result = await scrape_stealth(
                    url="https://example.com",
                    solve_cloudflare=True  # Override
                )
                
                # Config should have been modified
                assert config_mock.solve_cloudflare is True


class TestScrapeBatch:
    """Test suite for scrape_batch MCP tool."""
    
    @pytest.mark.asyncio
    async def test_multiple_valid_urls(self):
        """Test batch processing of multiple URLs."""
        mock_page = MockPage()
        
        with patch("mcp_scraper.server.scrape_with_retry") as mock_scrape:
            mock_scrape.return_value = mock_page
            
            result = await scrape_batch(
                urls=[
                    "https://example.com/page1",
                    "https://example.com/page2",
                    "https://example.com/page3",
                ]
            )
            
            assert result["total"] == 3
            assert result["successful"] >= 0
            assert len(result["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_urls(self):
        """Test handling of mixed valid/invalid URLs."""
        with patch("mcp_scraper.server.validate_url") as mock_validate:
            def validate_side_effect(url):
                return "valid" in url
            
            mock_validate.side_effect = validate_side_effect
            
            result = await scrape_batch(
                urls=[
                    "https://example.com/valid",
                    "http://localhost",  # Invalid
                    "https://example.com/also-valid",
                ]
            )
            
            assert result["total"] == 3
            assert result["failed"] >= 1
    
    @pytest.mark.asyncio
    async def test_empty_url_list(self):
        """Test handling of empty URL list."""
        result = await scrape_batch(urls=[])
        
        assert result["total"] == 0
        assert result["successful"] == 0
    
    @pytest.mark.asyncio
    async def test_url_list_limit(self):
        """Test that URL list over limit returns error."""
        # Create list of 101 URLs (over limit of 100)
        urls = [f"https://example.com/{i}" for i in range(101)]
        
        result = await scrape_batch(urls=urls)
        
        assert result["error"] is not None
        assert "100" in result["error"]
```

---

## Appendix: Quick Reference

### Test Discovery

```bash
# Find all tests
pytest --collect-only

# Find tests in specific module
pytest --collect-only tests/unit/test_config.py

# Find tests matching pattern
pytest -k "test_validate"
```

### Running Specific Test Categories

```bash
# Security tests only
pytest tests/security/ -v

# URL validation tests only
pytest tests/ -k "validate_url" -v

# Configuration tests only
pytest tests/ -k "config" -v

# MCP tool tests
pytest tests/integration/ -v
```

### Debugging Failed Tests

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Stop after first failure
pytest -x

# Show full diff on assertion errors
pytest --fulltrace
```

---

*This VDD testing document provides comprehensive guidance for testing the MCP Scraper project. All team members should use this document to ensure consistent, thorough testing across all components.*
