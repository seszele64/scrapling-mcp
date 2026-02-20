# Verification-Driven Development (VDD) Guide for MCP Scraper

This document provides comprehensive verification criteria and testing guidelines for the Scrapling MCP Server project. It serves as a reference for agents implementing features to ensure their work meets all functional, security, and performance requirements.

## 1. Overview

### What is Verification-Driven Development?

Verification-Driven Development (VDD) is a methodology that emphasizes defining clear, executable verification criteria before and during implementation. Rather than treating testing as an afterthought, VDD integrates verification into every stage of the development process. For the MCP Scraper project, this means establishing concrete test cases and success criteria for each MCP tool, security mechanism, and performance characteristic before writing production code.

The core principle of VDD is simple: what gets measured gets done, and what gets verified gets trusted. When implementing an MCP server that handles web scraping with stealth capabilities, rigorous verification ensures that security boundaries are maintained, scraping reliability meets expectations, and the MCP protocol integration works correctly across different client scenarios.

### Why Verification Matters for MCP Servers

MCP servers occupy a unique position in software architecture—they act as bridges between AI agents and external systems. In the case of this scraper, the server exposes powerful web fetching capabilities that could be exploited if not properly validated. A single vulnerability in URL validation could allow Server-Side Request Forgery (SSRF) attacks. Improper error handling could leak sensitive information. Inconsistent MCP tool responses could break client integrations.

Verification becomes particularly critical because the scraper operates in a hostile environment. Target websites actively attempt to detect and block scrapers. The server must successfully mimic legitimate browser behavior while the verification suite must confirm that the implementation actually achieves this goal. Without comprehensive verification, small implementation errors can cascade into security vulnerabilities or reliability failures that only manifest in production.

The verification criteria in this document cover five essential dimensions. First, functional correctness ensures each MCP tool produces the expected output for given inputs. Second, security verification confirms that URL validation, protocol restrictions, and private network blocking work as designed. Third, performance testing validates that timeouts, retry logic, and resource cleanup function correctly. Fourth, integration testing verifies that the server correctly implements the MCP protocol and integrates with the FastMCP framework. Fifth, edge case handling ensures the implementation gracefully manages unexpected inputs, network failures, and boundary conditions.

## 2. Verification Criteria for Each MCP Tool

This section provides detailed verification criteria for each MCP tool defined in the project. Each tool includes test cases with expected inputs and outputs, edge cases to test, and explicit success criteria that must be satisfied for the implementation to be considered complete.

### 2.1 scrape_simple

The scrape_simple tool provides basic web scraping without stealth features. It uses the Fetcher class for fast HTTP requests with TLS fingerprinting and is designed for well-behaved websites that do not implement anti-bot protections.

#### Test Cases

**Test Case 1: Basic Static Page Fetch**

This test verifies the fundamental functionality of fetching a simple static webpage.

Input:

```json
{
  "url": "https://example.com",
  "timeout": 30000
}
```

Expected Output:

```json
{
  "success": true,
  "url": "https://example.com",
  "status": 200,
  "text": "<html>...content...</html>",
  "html": "<html>...content...</html>",
  "title": "Example Domain",
  "headers": {
    "content-type": "text/html"
  }
}
```

Verification Steps:

- Confirm that the response contains both text and html fields
- Verify that the status code is correctly captured
- Check that response headers are included in the output
- Validate that the title is extracted when present in the page

**Test Case 2: CSS Selector Extraction**

This test verifies that the optional selector parameter correctly extracts specific content from the page.

Input:

```json
{
  "url": "https://example.com",
  "selector": "h1",
  "extract": "text"
}
```

Expected Output should contain the text content of all h1 elements on the page. If no h1 elements exist, the selector field in the response should be empty or the tool should handle this gracefully without raising an error.

**Test Case 3: Different Extract Modes**

Test the three extract modes: "text", "html", and "both".

Input:

```json
{
  "url": "https://example.com",
  "selector": "p",
  "extract": "html"
}
```

Expected Output should contain the raw HTML of matching elements. When extract is set to "both", the response should include both text and html representations of the selected content.

#### Edge Cases

Several edge cases require specific handling. First, invalid URLs should be rejected with a clear error message. URLs with missing schemes, malformed domain names, or unsupported protocols must trigger appropriate validation errors. Second, timeouts must be handled gracefully. When the timeout parameter is set to a very low value like 1 millisecond, the tool should either timeout quickly or reject the request with a validation error indicating the timeout is too short. Third, network errors must be caught and reported. Connection failures, DNS resolution errors, and refused connections should produce meaningful error messages rather than crashing the server. Fourth, empty responses need handling. Some pages return empty bodies, and the tool should handle this case without errors, returning an appropriate response indicating empty content.

#### Success Criteria

The scrape_simple tool implementation is considered complete when it correctly fetches static HTTP(S) pages and returns both text and HTML representations of the page content. The tool must properly handle the optional selector parameter for targeted extraction and support all three extract modes (text, html, both). Timeout parameters must be respected, and network errors must produce meaningful error messages without crashing the server. The implementation must also correctly set and report HTTP status codes in the response.

### 2.2 scrape_stealth

The scrape_stealth tool provides configurable anti-detection features using the StealthyFetcher class with Camoufox (modified Firefox) for maximum stealth capabilities. This tool is designed for websites with anti-bot measures, rate-limited endpoints, and Cloudflare-protected sites.

#### Test Cases

**Test Case 1: Minimal Stealth Level**

This test verifies scraping with minimal stealth settings.

Input:

```json
{
  "url": "https://example.com",
  "stealth_level": "minimal"
}
```

Expected Behavior:

- The request should complete successfully on simple websites
- Response time should be relatively fast compared to higher stealth levels
- The implementation should apply minimal stealth settings including headless mode, image blocking, and resource disabling

**Test Case 2: Standard Stealth Level**

This test verifies the default stealth configuration.

Input:

```json
{
  "url": "https://example.com",
  "stealth_level": "standard"
}
```

Expected Behavior:

- The request should enable humanize behavior with cursor movement simulation
- OS fingerprint randomization should be active
- WebRTC blocking should be enabled
- Chrome simulation should be active
- Network idle and DOM loading waits should be enabled

**Test Case 3: Maximum Stealth Level**

This test verifies the highest stealth configuration.

Input:

```json
{
  "url": "https://example.com",
  "stealth_level": "maximum",
  "timeout": 60000
}
```

Expected Behavior:

- All stealth features should be enabled including Cloudflare solving
- GeoIP routing should be active
- The wait_selector should be set to "body" with visible state
- Timeout should be extended to 60 seconds

**Test Case 4: Cloudflare Solving**

This test verifies Cloudflare challenge handling.

Input:

```json
{
  "url": "https://cloudflare-protected-example.com",
  "solve_cloudflare": true,
  "network_idle": true,
  "load_dom": true
}
```

Expected Behavior:

- When Cloudflare challenges are detected, the implementation should attempt to solve them
- The tool should wait for the network to be idle before returning
- DOMContentLoaded event should be waited for before extraction
- If Cloudflare solving fails, an appropriate error should be raised

**Test Case 5: Custom Stealth Configuration**

This test verifies custom stealth parameter overrides.

Input:

```json
{
  "url": "https://example.com",
  "stealth_level": "standard",
  "solve_cloudflare": true,
  "network_idle": false,
  "load_dom": false,
  "timeout": 45000,
  "proxy": "http://proxy.example.com:8080"
}
```

Expected Behavior:

- Custom parameters should override the stealth level defaults
- Proxy should be applied to the request
- The specified timeout should be used instead of the default

#### Edge Cases

Proxy handling requires careful testing. Invalid proxy URLs should be rejected with validation errors. When a proxy becomes unreachable during a request, the implementation should either fail gracefully or attempt retry logic depending on configuration. For proxy rotation, when one proxy fails, the implementation should rotate to the next proxy in the list if provided.

Browser automation edge cases include handling pages that hang during load. The timeout parameter must actually terminate the browser automation after the specified duration. JavaScript errors in the target page should not crash the scraper. Pages that redirect multiple times should be handled correctly with the final URL reflected in the response.

Cloudflare edge cases include sites that present captcha challenges, which cannot be solved automatically and should produce a clear error indicating manual intervention is needed. Some Cloudflare configurations may continuously loop; the implementation should detect this condition and fail after a reasonable number of attempts.

#### Success Criteria

The scrape_stealth implementation is complete when all three stealth levels (minimal, standard, maximum) produce correctly configured browser sessions with appropriate stealth settings applied. The tool must respect individual parameter overrides that customize the stealth configuration. Proxy support must work correctly including single proxy and proxy list rotation. Cloudflare challenge detection and optional solving must function. Timeout handling must actually terminate long-running browser sessions. The implementation must handle browser automation errors gracefully without crashing the MCP server.

### 2.3 scrape_session

The scrape_session tool provides session-based scraping with persistent state. This is essential for websites requiring authentication, multi-step interactions, and maintaining login state across multiple requests.

#### Test Cases

**Test Case 1: Basic Session Creation**

This test verifies that a new session can be created and used for scraping.

Input:

```json
{
  "url": "https://example.com",
  "session_id": "test-session-001",
  "stealth_level": "standard"
}
```

Expected Behavior:

- A new session should be created with the specified session_id
- The session should be stored and associated with the session_id
- Subsequent requests with the same session_id should reuse the existing session

**Test Case 2: Session Persistence Across Requests**

This test verifies that cookies and state persist across multiple requests in the same session.

Input (Request 1):

```json
{
  "url": "https://example.com/set-cookie",
  "session_id": "test-session-002"
}
```

Input (Request 2):

```json
{
  "url": "https://example.com/check-cookie",
  "session_id": "test-session-002"
}
```

Expected Behavior:

- Cookies set in the first request should be present in the second request
- The session state should be maintained between requests
- The session should remain valid across multiple requests

**Test Case 3: Initial Cookies**

This test verifies that initial cookies can be provided when creating a session.

Input:

```json
{
  "url": "https://example.com",
  "session_id": "test-session-003",
  "cookies": {
    "auth_token": "abc123",
    "session_id": "user-456"
  }
}
```

Expected Behavior:

- The specified cookies should be set on the session before the first request
- These cookies should be present in the HTTP request to the target URL

**Test Case 4: Multiple Concurrent Sessions**

This test verifies that multiple session IDs can exist simultaneously without interfering with each other.

Input:

```json
{
  "url": "https://example.com",
  "session_id": "session-a"
}
```

Then simultaneously:

```json
{
  "url": "https://example.com",
  "session_id": "session-b"
}
```

Expected Behavior:

- Each session_id should maintain its own independent state
- Cookies from session-a should not appear in session-b requests and vice versa

#### Edge Cases

Session cleanup requires testing. When a session is not used for an extended period, it should either be cleaned up or the implementation should document the session timeout behavior. Invalid session IDs should be handled gracefully. Empty session_id values should either use a default session or produce a validation error.

Cookie handling edge cases include cookie rejection. Some cookies may be rejected by the target site due to invalid format or size limits; the implementation should handle this gracefully without crashing. Cookie expiration should be respected. The implementation should not attempt to send expired cookies unless the target site specifically requires them.

Session state corruption requires handling. If a session becomes corrupted or enters an invalid state, subsequent requests should either recover gracefully or produce a clear error message.

#### Success Criteria

The scrape_session implementation is complete when sessions are correctly created with specified session IDs. Cookie persistence must work across multiple requests in the same session. Initial cookies provided at session creation must be applied to requests. Multiple concurrent sessions must operate independently without state leakage. Session state must be properly maintained until explicitly closed or until the session expires.

### 2.4 extract_structured

The extract_structured tool enables extraction of specific data using CSS selectors. This tool is designed for extracting structured data from pages, building datasets, and targeted content acquisition.

#### Test Cases

**Test Case 1: Single Field Extraction**

This test verifies basic single-selector extraction.

Input:

```json
{
  "url": "https://example.com",
  "selectors": {
    "title": "h1"
  }
}
```

Expected Output:

```json
{
  "success": true,
  "url": "https://example.com",
  "selectors": {
    "title": ["Example Title"]
  }
}
```

The selector field name (title) should map to an array of extracted values from matching elements.

**Test Case 2: Multiple Field Extraction**

This test verifies extraction of multiple fields simultaneously.

Input:

```json
{
  "url": "https://example.com",
  "selectors": {
    "heading": "h1",
    "paragraphs": "p",
    "links": "a@href"
  }
}
```

Expected Output should contain all three fields, each with their respective extracted values. Links should extract the href attribute due to the @href suffix.

**Test Case 3: Attribute Extraction**

This test verifies extraction of element attributes rather than text content.

Input:

```json
{
  "url": "https://example.com",
  "selectors": {
    "images": "img@src",
    "links": "a@href"
  }
}
```

Expected Output should contain the src attribute values for images and href attribute values for links.

**Test Case 4: Nested Element Extraction**

This test verifies extraction from nested structures.

Input:

```json
{
  "url": "https://example.com/articles",
  "selectors": {
    "article_titles": "article h2.title",
    "article_content": "article div.content",
    "authors": "article span.author"
  }
}
```

Expected Output should correctly extract from nested selectors, maintaining correspondence between related elements when possible.

**Test Case 5: No Matches**

This test verifies handling when selectors match nothing.

Input:

```json
{
  "url": "https://example.com",
  "selectors": {
    "nonexistent": "div.does-not-exist"
  }
}
```

Expected Output should include the field with an empty array rather than omitting the field or raising an error.

#### Edge Cases

Selector syntax edge cases include malformed CSS selectors, which should either be validated before use or produce meaningful error messages when they fail during execution. Special characters in selector values need proper escaping. Complex selectors like pseudo-classes (:first-child, :nth-of-type) should either be supported or produce clear error messages indicating limited selector support.

Empty page handling includes pages with no content matching the selectors, which should return empty arrays for those fields rather than errors. Completely empty responses from the server should be handled gracefully with appropriate error reporting.

Extraction performance requires consideration. Very complex pages with thousands of matching elements may impact performance; the implementation should either handle this gracefully with pagination options or document any practical limits.

#### Success Criteria

The extract_structured implementation is complete when it correctly extracts text content from elements matching CSS selectors. Attribute extraction using @attribute syntax must work correctly. Multiple selector fields must be processed in a single request. Non-matching selectors must return empty arrays rather than errors. The tool must properly handle nested element selectors. Response formatting must include the extracted selector data in a consistent, predictable structure.

### 2.5 scrape_batch

The scrape_batch tool processes multiple URLs in sequence, enabling bulk data collection and site-wide scraping operations.

#### Test Cases

**Test Case 1: Multiple Valid URLs**

This test verifies batch processing of multiple valid URLs.

Input:

```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
  ],
  "stealth_level": "minimal",
  "delay": 1.0
}
```

Expected Output:

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com/page1",
      "success": true,
      "status": 200,
      "text": "..."
    },
    {
      "url": "https://example.com/page2",
      "success": true,
      "status": 200,
      "text": "..."
    },
    {
      "url": "https://example.com/page3",
      "success": true,
      "status": 200,
      "text": "..."
    }
  ],
  "total": 3,
  "successful": 3,
  "failed": 0
}
```

Each URL should produce its own result object within the results array.

**Test Case 2: Mixed Success and Failure**

This test verifies handling when some URLs in the batch fail.

Input:

```json
{
  "urls": [
    "https://example.com/valid",
    "https://invalid-domain-that-does-not-exist.com",
    "https://example.com/also-valid"
  ],
  "stealth_level": "minimal"
}
```

Expected Output should include success entries for valid URLs and failure entries with error information for invalid URLs. The total, successful, and failed counts should accurately reflect the outcomes.

**Test Case 3: Rate Limiting with Delay**

This test verifies that the delay parameter controls the rate of requests.

Input:

```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "delay": 2.0
}
```

Expected Behavior should include approximately 2 seconds between consecutive request initiations. The implementation should not make concurrent requests when delay is specified.

**Test Case 4: Empty URL List**

This test verifies handling of an empty URL list.

Input:

```json
{
  "urls": []
}
```

Expected Output should indicate success with zero results rather than producing an error.

**Test Case 5: Single URL in Batch**

This test verifies that a single URL in the batch works correctly.

Input:

```json
{
  "urls": ["https://example.com"]
}
```

Expected Output should be functionally equivalent to a single scrape operation but formatted with the batch response structure.

#### Edge Cases

Batch size limits require consideration. Very large batches (hundreds or thousands of URLs) may require chunking, pagination, or size limits. The implementation should either handle large batches gracefully or document any size limitations.

Partial failure handling must be tested. When some URLs in a batch fail, the remaining URLs should continue to be processed. The implementation should not abort the entire batch due to one failure.

Request cancellation requires handling. If the MCP request is cancelled mid-batch, the implementation should handle this gracefully without leaving resources in an inconsistent state.

#### Success Criteria

The scrape_batch implementation is complete when it processes multiple URLs and returns individual results for each URL. The delay parameter must control the rate of requests between consecutive fetches. Partial failures must not abort the entire batch; successful URLs should continue to be processed. Response structure must include results array, total count, successful count, and failed count. The tool must handle empty URL lists gracefully without errors.

## 3. Integration Verification

Integration verification ensures that the MCP server correctly implements the Model Context Protocol and integrates properly with the FastMCP framework. These tests verify end-to-end functionality from MCP client request to server response.

### 3.1 MCP Protocol Compliance

The server must correctly implement the MCP specification to ensure compatibility with MCP clients. Several key aspects require verification.

**Tool Registration Verification**

The server must register all tools with correct names and parameter schemas. Each tool should be discoverable through MCP protocol introspection. Tool descriptions should match the actual functionality. Parameter types should match what the implementation expects (string, integer, boolean, object, array).

Test this by starting the MCP server and using an MCP client to list available tools. Verify that scrape_simple, scrape_stealth, scrape_session, extract_structured, and scrape_batch all appear in the tool list with correct parameter schemas.

**Request-Response Format Verification**

MCP requests and responses must follow the JSON-RPC 2.0 format. Request payloads should include the correct method name, parameters object, and id field. Responses should include the correct result field for successful requests or error field for failures. Error responses should include code, message, and optionally data fields.

Test this by sending MCP requests using a testing client or curl against the server's MCP endpoint. Verify that responses conform to the expected JSON-RPC 2.0 structure.

**Streaming and Pagination Verification**

If the implementation includes streaming responses or pagination, these features must follow MCP conventions. Streaming responses should use the correct notification format. Pagination parameters should be consistently named and typed.

### 3.2 FastMCP Integration

The server uses FastMCP framework for MCP protocol handling. Integration verification ensures the framework is used correctly.

**FastMCP Server Initialization**

The server should initialize without errors. Run the server startup command and verify no exceptions are raised. The server should bind to the expected port or stdio channel.

```bash
python -m mcp_scraper  # or appropriate startup command
```

**Decorator-Based Tool Definition**

Tools should be defined using FastMCP's @mcp.tool() decorator. Verify that each tool function is properly decorated and will be registered with FastMCP at server startup.

**Async Support Verification**

FastMCP supports async tools. Verify that async tool functions work correctly. Test a simple async tool call and confirm the response is returned correctly.

### 3.3 End-to-End Workflow Tests

End-to-end tests verify complete workflows from client request through server processing to response.

**Complete Scraping Workflow**

This test verifies a complete scraping workflow from start to finish.

Steps:

1. Start the MCP server
2. Send a scrape_simple request for https://example.com
3. Verify the response contains valid HTML and text content
4. Verify the response structure matches MCP conventions
5. Verify no errors are logged

Expected Result: A successful JSON response with scraped content, proper HTTP status, and complete metadata.

**Stealth Scraping Workflow**

This test verifies the stealth scraping workflow including browser automation.

Steps:

1. Start the MCP server
2. Send a scrape_stealth request with stealth_level: "standard"
3. Verify the response returns successfully (may be slower than simple)
4. Verify browser automation completed (check logs if available)

Expected Result: A successful response from the stealth scraping tool with content.

**Error Propagation Workflow**

This test verifies that errors are correctly propagated to clients.

Steps:

1. Start the MCP server
2. Send a request with an invalid URL (e.g., file:///etc/passwd)
3. Verify an appropriate error response is returned
4. Verify the error message is user-friendly

Expected Result: An error response with a clear message about invalid URL, not a server crash.

## 4. Security Verification

Security verification is critical for a web scraping server that could be targeted for SSRF attacks. The implementation must include robust security measures and these must be verified to be working correctly.

### 4.1 URL Validation Tests

The validate_url() function must prevent SSRF attacks by blocking requests to internal and dangerous URLs.

**Test: HTTP Protocol Only**

Input:

```python
validate_url("http://example.com")  # Should pass
validate_url("https://example.com")  # Should pass
```

Expected: Both return True.

**Test: Dangerous Protocols Blocked**

Input:

```python
validate_url("file:///etc/passwd")
validate_url("ftp://example.com")
validate_url("gopher://example.com")
validate_url("javascript:alert(1)")
validate_url("data:text/html,<script>alert(1)</script>")
```

Expected: All return False with appropriate error messages.

**Test: Private IP Addresses Blocked**

Input:

```python
validate_url("http://10.0.0.1")
validate_url("http://10.255.255.255")
validate_url("http://172.16.0.1")
validate_url("http://172.31.255.255")
validate_url("http://192.168.0.1")
validate_url("http://192.168.255.255")
validate_url("http://127.0.0.1")
validate_url("http://localhost")
```

Expected: All return False.

**Test: IPv6 Private Addresses Blocked**

Input:

```python
validate_url("http://[::1]")
validate_url("http://[fe80::1]")
```

Expected: All return False.

**Test: Internal Hostnames Blocked**

Input:

```python
validate_url("http://localhost")
validate_url("http://localhost.localdomain")
validate_url("http://machine.internal")
validate_url("http://machine.corp")
validate_url("http://machine.local")
validate_url("http://metadata.google.internal")
```

Expected: All return False.

**Test: Link-Local Addresses Blocked**

Input:

```python
validate_url("http://169.254.169.254")  # AWS metadata endpoint
validate_url("http://169.254.0.1")
```

Expected: All return False (169.254.0.0/16 is link-local).

**Test: Valid Public URLs Allowed**

Input:

```python
validate_url("https://example.com")
validate_url("https://www.example.com")
validate_url("https://subdomain.example.com")
validate_url("https://example.com:8080")
validate_url("https://93.184.216.34")  # Public IP
```

Expected: All return True.

### 4.2 Protocol Restrictions

The server must only allow HTTP and HTTPS protocols. Any other protocol must be rejected before making network requests.

**Test: Invalid Protocol Rejection**

Input:

```json
{
  "url": "ftp://example.com/file",
  "stealth_level": "minimal"
}
```

Expected: The tool should reject this with a validation error before attempting any network request.

### 4.3 Input Sanitization

Beyond URL validation, other inputs may require sanitization.

**Test: Selector Injection**

Input:

```json
{
  "url": "https://example.com",
  "selectors": {
    "malicious": "<script>alert(1)</script>"
  }
}
```

Expected: The implementation should treat this as a literal CSS selector, not as HTML. If the selector is invalid CSS, return an appropriate error rather than executing the selector.

**Test: Cookie Value Sanitization**

Input:

```json
{
  "url": "https://example.com",
  "session_id": "test",
  "cookies": {
    "malicious": "value<script>alert(1)</script>"
  }
}
```

Expected: Cookie values should be treated as data, not executable content. The implementation should not render or execute these values.

## 5. Performance Verification

Performance verification ensures the implementation handles timeouts correctly, implements retry logic properly, and cleans up resources to prevent memory leaks.

### 5.1 Timeout Handling Tests

Timeout handling is critical for a scraping server that may encounter slow or unresponsive websites.

**Test: Request Timeout Enforcement**

Input:

```json
{
  "url": "https://slow-server.example.com",
  "timeout": 1000
}
```

Setup: Configure a test server that responds very slowly (longer than 1 second).

Expected: The request should timeout after approximately 1 second and return an error indicating timeout. The implementation should not hang indefinitely.

**Test: Minimum Timeout Validation**

Input:

```json
{
  "url": "https://example.com",
  "timeout": 0
}
```

Expected: Either reject with validation error or use a reasonable minimum timeout. The implementation should not accept zero or negative timeouts.

**Test: Maximum Timeout Handling**

Input:

```json
{
  "url": "https://example.com",
  "timeout": 300000
}
```

Expected: The timeout should be accepted. Verify that the actual timeout used does not exceed reasonable limits (some implementations may cap maximum timeout).

### 5.2 Retry Logic Tests

The implementation should include retry logic for transient failures.

**Test: Automatic Retry on Failure**

Setup: Configure a test that fails initially but succeeds on retry.

Input:

```json
{
  "url": "https://flaky-server.example.com",
  "max_retries": 3
}
```

Expected: The first request should fail, then retry up to 3 times. If the server eventually succeeds, the final response should contain the successful content.

**Test: Retry Exhaustion**

Setup: Configure a test server that always fails.

Input:

```json
{
  "url": "https://always-fail.example.com",
  "max_retries": 3
}
```

Expected: After exhausting all retries, an error should be returned indicating the maximum retries were exceeded.

**Test: Exponential Backoff**

Input:

```json
{
  "url": "https://flaky-server.example.com",
  "max_retries": 3,
  "backoff_factor": 2.0
}
```

Expected: Delays between retries should increase exponentially. If base delay is 1 second, subsequent delays should be approximately 1s, 2s, 4s (or similar exponential pattern).

### 5.3 Resource Cleanup Tests

Proper resource cleanup prevents memory leaks and ensures the server remains stable over time.

**Test: Browser Session Cleanup**

Steps:

1. Make several scrape_stealth requests
2. Monitor memory usage or open browser processes
3. Verify that browser resources are released after each request

Expected: Browser processes or contexts should be closed after each request completes. No accumulation of zombie browser processes.

**Test: Session Cleanup**

Steps:

1. Create several scrape_session sessions
2. Let sessions remain idle
3. Verify that old sessions are cleaned up or resources are released

Expected: Resources associated with old sessions should eventually be cleaned up.

**Test: Server Shutdown Cleanup**

Steps:

1. Start the MCP server
2. Make several scraping requests
3. Terminate the server
4. Verify no hanging processes or unclosed connections

Expected: Server shutdown should cleanly close all connections and browser contexts.

## 6. Verification Scripts

This section provides concrete commands and scripts to run verification tests.

### 6.1 Running Unit Tests

The project should include unit tests for core functionality.

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validation.py -v

# Run tests with coverage
pytest tests/ --cov=mcp_scraper --cov-report=html
```

### 6.2 MCP Server Startup Verification

Verify the server starts correctly before running integration tests.

```bash
# Check server can be imported without errors
python -c "from mcp_scraper import mcp; print('Import successful')"

# Start server in test mode (if available)
python -m mcp_scraper --help

# Check configuration loads correctly
python -c "from mcp_scraper.config import Settings; s = Settings(); print(f'Default timeout: {s.DEFAULT_TIMEOUT}')"
```

### 6.3 MCP Client Testing

Test the server using an MCP client.

```python
# Example MCP client test using the official MCP Python SDK
from mcp import ClientSession, StdioServerParameters
import asyncio

async def test_scrape_simple():
    params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_scraper"],
    )
    
    async with ClientSession(params) as session:
        await session.initialize()
        
        # Test scrape_simple
        result = await session.call_tool("scrape_simple", {
            "url": "https://example.com"
        })
        print(f"Result: {result}")
```

### 6.4 Manual Verification Commands

For quick manual verification, use these curl commands.

```bash
# If server exposes HTTP endpoint
curl -X POST http://localhost:8000/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "scrape_simple",
    "arguments": {"url": "https://example.com"}
  }'
```

## 7. Self-Verification Checklist

Agents implementing features should use this checklist to verify their work before considering it complete.

### 7.1 Functional Verification

- [ ] All MCP tools are registered and visible to MCP clients
- [ ] Each tool responds with correct JSON structure
- [ ] Required parameters are enforced (tool fails without them)
- [ ] Optional parameters have correct default values
- [ ] Response includes all documented fields for each tool
- [ ] Error responses include meaningful error messages

### 7.2 Security Verification

- [ ] URL validation is called before every scraping request
- [ ] Private IP addresses (10.x.x.x, 172.16-31.x.x, 192.168.x.x) are blocked
- [ ] Localhost variants (localhost, 127.0.0.1, ::1) are blocked
- [ ] Internal hostnames (*.local, *.internal, *.corp) are blocked
- [ ] Link-local addresses (169.254.x.x) are blocked
- [ ] Dangerous protocols (file://, ftp://, gopher://) are blocked
- [ ] Only HTTP and HTTPS protocols are allowed

### 7.3 Performance Verification

- [ ] Timeout parameter actually terminates long-running requests
- [ ] Retry logic is implemented with configurable max_retries
- [ ] Exponential backoff is implemented
- [ ] Browser resources are cleaned up after each request
- [ ] Session resources are cleaned up appropriately

### 7.4 Integration Verification

- [ ] Server starts without errors
- [ ] All tools respond correctly to MCP requests
- [ ] FastMCP decorators are correctly applied
- [ ] Async/await patterns are used correctly

### 7.5 Common Issues and Detection

Several common issues frequently arise during implementation. Review this list to avoid common mistakes.

**Issue: URL validation not called**

Detection: Test with http://127.0.0.1 and verify it is blocked. If the request proceeds, validation is not being called.

**Issue: Response format inconsistent**

Detection: Compare responses from different tools. They should follow consistent patterns (success boolean, url field, data fields).

**Issue: Resources not cleaned up**

Detection: Run multiple requests and check system resources (ps aux for processes, memory usage). Resources should not accumulate.

**Issue: Timeout not enforced**

Detection: Set a very short timeout (1 second) and request a slow endpoint. Request should fail fast, not hang.

**Issue: Retry logic not working**

Detection: Configure max_retries: 1 and use a failing endpoint. Verify that exactly one retry occurs before failure.

**Issue: Stealth settings not applied**

Detection: Check logs or add debugging to verify stealth settings (headless, humanize, etc.) are passed to the scrapling library.

## 8. Success Metrics

These metrics define what "done" means for this project. Implementations should meet or exceed these requirements.

### 8.1 Functional Requirements

The implementation must provide working versions of all five MCP tools: scrape_simple, scrape_stealth, scrape_session, extract_structured, and scrape_batch. Each tool must handle both success and error cases correctly. The implementation must correctly apply stealth configurations for all three stealth levels.

### 8.2 Security Requirements

URL validation must block 100% of SSRF attempts using the test cases in Section 4. No private IP addresses, internal hostnames, or dangerous protocols should ever reach the network layer. The implementation must not leak sensitive information in error messages.

### 8.3 Coverage Requirements

Unit test coverage should exceed 80% for core modules (config.py, stealth.py). All security validation functions must have dedicated unit tests. All MCP tool functions must have integration tests.

### 8.4 Performance Benchmarks

Simple scraping (scrape_simple) should complete in under 2 seconds for typical web pages. Stealth scraping (scrape_stealth) should complete in under 30 seconds for typical pages. Session initialization should take under 5 seconds. Memory usage should remain stable during sustained operation (no memory leaks).

### 8.5 Protocol Compliance

The server must correctly implement the MCP protocol as specified by the Model Context Protocol specification. Tool names, parameter schemas, and response formats must match MCP conventions. The server must be compatible with standard MCP clients.

---

*This VDD guide was created to ensure comprehensive verification of the Scrapling MCP Server implementation. All agents should use this document to verify their work before submission.*
