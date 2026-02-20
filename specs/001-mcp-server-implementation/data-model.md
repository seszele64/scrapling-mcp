# Data Model: MCP Server Implementation

**Feature**: MCP Server Implementation  
**Date**: 2026-02-20  
**Version**: 1.0.0

## Entities

### ScrapingRequest

Represents a request to scrape a URL with associated parameters.

**Fields**:
- `url` (str, required): Target URL to scrape
- `selector` (str, optional): CSS selector for targeted extraction
- `extract` (str, optional): What to extract - "text", "html", or "both" (default: "text")
- `timeout` (int, optional): Request timeout in milliseconds (default: 30000)
- `stealth_level` (str, optional): Stealth level - "minimal", "standard", or "maximum" (default: "standard")
- `session_id` (str, optional): Session identifier for persistent state
- `cookies` (dict, optional): Initial cookies to set for session
- `proxy` (str, optional): Proxy URL for requests
- `solve_cloudflare` (bool, optional): Attempt Cloudflare challenges (default: false)
- `network_idle` (bool, optional): Wait for network inactivity (default: true)
- `load_dom` (bool, optional): Wait for DOMContentLoaded (default: true)

**Validation Rules**:
- URL must pass validate_url() security checks
- timeout must be between 1000 and 300000 ms
- stealth_level must be one of: "minimal", "standard", "maximum"

---

### ScrapingResponse

Represents the response from a scraping operation.

**Fields**:
- `url` (str, required): Original URL that was scraped
- `status_code` (int, required): HTTP status code (200, 404, 500, etc.)
- `title` (str, optional): Page title when available
- `text` (str, optional): Extracted text content
- `html` (str, optional): Full HTML content
- `headers` (dict, optional): Response headers
- `selectors` (dict, optional): Extracted selector values {name: value}
- `error` (str, optional): Error message if scraping failed
- `timestamp` (str, required): ISO 8601 timestamp of response

**Validation Rules**:
- status_code must be valid HTTP status (100-599)
- At least one of text or html must be present on success
- timestamp must be valid ISO 8601 format

---

### StealthConfig

Configuration for stealth/anti-detection settings.

**Fields**:
- `headless` (bool): Run browser in headless mode (default: true)
- `solve_cloudflare` (bool): Attempt Cloudflare challenges (default: false)
- `humanize` (bool): Add human-like behavior patterns (default: true)
- `humanize_duration` (float): Maximum cursor movement duration in seconds (default: 1.5)
- `geoip` (bool): Use geoip-based request routing (default: false)
- `os_randomize` (bool): Randomize OS fingerprint (default: true)
- `block_webrtc` (bool): Block WebRTC to prevent IP leaks (default: true)
- `allow_webgl` (bool): Allow WebGL fingerprinting (default: false)
- `google_search` (bool): Simulate Google Chrome browser (default: true)
- `block_images` (bool): Block images to reduce bandwidth (default: false)
- `block_ads` (bool): Block advertisements (default: true)
- `disable_resources` (bool): Disable CSS and JS resources (default: false)
- `network_idle` (bool): Wait for network inactivity (default: true)
- `load_dom` (bool): Wait for DOMContentLoaded (default: true)
- `wait_selector` (str, optional): Wait for specific element to appear
- `wait_selector_state` (str): Element state to wait for - "visible", "hidden", "attached"
- `timeout` (int): Request timeout in milliseconds (default: 30000)
- `proxy` (str, optional): Proxy URL for requests

**State Transitions**:
- Config is immutable once created
- Changes require creating new StealthConfig instance
- Session recreates when config changes

---

### Session

Represents a persistent scraping session.

**Fields**:
- `session_id` (str, required): Unique session identifier
- `config` (StealthConfig, required): Session configuration
- `cookies` (list[dict], required): Session cookies
- `created_at` (datetime, required): Session creation timestamp
- `last_used` (datetime, required): Last activity timestamp

**Methods**:
- `fetch(url, **options)`: Execute scraping request
- `close()`: Close session and cleanup resources
- `is_valid()`: Check if session is still valid (not expired)

**Lifecycle**:
1. Created on first request with new session_id
2. Reused for subsequent requests with same session_id
3. Recreated if config changes
4. Closed explicitly or on server shutdown

---

### BatchResult

Represents results from batch scraping operation.

**Fields**:
- `total` (int, required): Total number of URLs processed
- `successful` (int, required): Number of successful scrapes
- `failed` (int, required): Number of failed scrapes
- `results` (list[ScrapingResponse], required): Array of individual results
- `errors` (list[dict], optional): Array of error details for failed URLs

**Validation Rules**:
- total == successful + failed
- results length equals total
