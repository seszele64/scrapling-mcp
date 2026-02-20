# MCP Scraper Quickstart Guide

This guide provides quick examples for using all MCP scraping tools.

## Installation

```bash
pip install mcp-scraper
```

## Configuration

Create a `.env` file:

```bash
# Optional proxy
PROXY_URL=

# Request timeout in seconds (1-300)
DEFAULT_TIMEOUT=30

# Logging level
LOG_LEVEL=INFO

# Max retry attempts (0-10)
MAX_RETRIES=3
```

## MCP Tools

The server exposes 5 MCP tools for web scraping:

---

## 1. scrape_simple

Simple web scraping without stealth features. Best for static content and well-behaved websites.

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `url` | string | Yes | URL to scrape | - |
| `selector` | string | No | CSS selector for targeted extraction | None |
| `extract` | string | No | What to extract: "text", "html", or "both" | "text" |
| `timeout` | integer | No | Request timeout in milliseconds (1000-300000) | 30000 |

### Example

```python
# Simple usage
result = await scrape_simple(url="https://example.com")

# With selector and HTML extraction
result = await scrape_simple(
    url="https://example.com",
    selector="h1.title",
    extract="both",
    timeout=15000
)
```

### Response

```json
{
    "url": "https://example.com",
    "status_code": 200,
    "title": "Example Domain",
    "text": "Example text content...",
    "html": "<html>...</html>",
    "headers": {},
    "selectors": {"content": "Title Text"},
    "timestamp": "2024-01-01T00:00:00Z",
    "error": null
}
```

---

## 2. scrape_stealth

Stealth web scraping with configurable anti-detection features. Uses browser automation for maximum success rate.

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `url` | string | Yes | URL to scrape | - |
| `stealth_level` | string | No | "minimal", "standard", or "maximum" | "standard" |
| `solve_cloudflare` | boolean | No | Attempt Cloudflare challenges | false |
| `network_idle` | boolean | No | Wait for network inactivity | true |
| `load_dom` | boolean | No | Wait for DOMContentLoaded | true |
| `timeout` | integer | No | Request timeout in milliseconds | 30000 |
| `proxy` | string | No | Proxy URL (e.g., http://proxy:8080) | None |

### Example

```python
# Standard stealth scraping
result = await scrape_stealth(url="https://example.com")

# Maximum stealth with Cloudflare solving
result = await scrape_stealth(
    url="https://protected-site.com",
    stealth_level="maximum",
    solve_cloudflare=True,
    network_idle=True,
    load_dom=True,
    timeout=60000,
    proxy="http://my-proxy:8080"
)
```

### Stealth Levels

- **minimal**: Fast, basic anti-detection. Good for simple sites.
- **standard**: Balanced speed and anonymity. Good for most sites.
- **maximum**: Highest protection, slower. Good for protected sites.

---

## 3. scrape_session

Session-based scraping with persistent state. Maintains cookies across requests.

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `url` | string | Yes | URL to scrape | - |
| `session_id` | string | No | Session identifier | auto-generated |
| `cookies` | object | No | Initial cookies {"name": "value"} | None |
| `stealth_level` | string | No | "minimal", "standard", or "maximum" | "standard" |

### Example

```python
# Simple session scraping
result = await scrape_session(url="https://example.com/dashboard")

# With session persistence
result = await scrape_session(
    url="https://example.com/profile",
    session_id="user-session-123",
    cookies={"auth": "token-value"},
    stealth_level="standard"
)
```

### Response

```json
{
    "url": "https://example.com/dashboard",
    "session_id": "user-session-123",
    "status_code": 200,
    "title": "Dashboard",
    "text": "...",
    "html": "...",
    "cookies": {"session": "abc123"},
    "timestamp": "2024-01-01T00:00:00Z",
    "error": null
}
```

---

## 4. extract_structured

Extract structured data using CSS selectors. Supports text, HTML, and attribute extraction.

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `url` | string | Yes | URL to scrape | - |
| `selectors` | object | Yes | Map of name → CSS selector | - |
| `stealth_level` | string | No | "minimal", "standard", or "maximum" | "standard" |

### Selector Syntax

- `"selector"` - Extract text content
- `"selector::html"` - Extract inner HTML
- `"selector@attr"` - Extract attribute (e.g., `"a@href"`)
- `"selector@attr1@attr2"` - Extract multiple attributes

### Example

```python
result = await extract_structured(
    url="https://example.com/blog",
    selectors={
        "title": "h1.article-title",
        "content": "div.article-content",
        "links": "a.read-more@href",
        "images": "img.post-image@src@alt"
    }
)
```

### Response

```json
{
    "url": "https://example.com/blog",
    "status_code": 200,
    "title": "Blog",
    "text": "Full page text...",
    "extracted": {
        "title": "My Blog Post",
        "content": "Article content here...",
        "links": ["/post/1", "/post/2", "/post/3"],
        "images": [
            {"src": "/img1.jpg", "alt": "Image 1"},
            {"src": "/img2.jpg", "alt": "Image 2"}
        ]
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "error": null
}
```

---

## 5. scrape_batch

Scrape multiple URLs in sequence with configurable delay.

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `urls` | array | Yes | List of URLs (max 100) | - |
| `stealth_level` | string | No | "minimal", "standard", or "maximum" | "standard" |
| `delay` | float | No | Delay between requests in seconds | 1.0 |

### Example

```python
result = await scrape_batch(
    urls=[
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ],
    stealth_level="minimal",
    delay=2.0
)
```

### Response

```json
{
    "total": 3,
    "successful": 3,
    "failed": 0,
    "results": [
        {"url": "...", "status_code": 200, "title": "Page 1", "text": "...", "error": null},
        {"url": "...", "status_code": 200, "title": "Page 2", "text": "...", "error": null},
        {"url": "...", "status_code": 200, "title": "Page 3", "text": "...", "error": null}
    ],
    "errors": [],
    "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Error Handling

All tools return an `error` field that contains error information if something goes wrong.

### Common Errors

```python
# Invalid URL
{"error": "URL cannot be empty"}

# Invalid parameters
{"error": "Timeout must be between 1000 and 300000 milliseconds"}

# Security block
{"error": "Invalid or disallowed URL..."}

# Scraping errors
{"error": "Cloudflare protection detected"}
{"error": "Request blocked"}
{"error": "Request timed out"}
```

### Best Practices

1. **Validate inputs**: Check URL format before scraping
2. **Use appropriate stealth level**: Start with "minimal", increase as needed
3. **Handle partial failures**: `scrape_batch` continues on error
4. **Set reasonable timeouts**: Higher for complex pages
5. **Use sessions**: For authenticated requests

---

## Running the Server

```bash
# Start the MCP server
mcp-scraper

# Or run directly
python -m mcp_scraper.server
```

The server runs on stdio by default and communicates via MCP protocol.
