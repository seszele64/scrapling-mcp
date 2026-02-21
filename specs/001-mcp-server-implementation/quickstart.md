# Quickstart: MCP Server Implementation

**Feature**: MCP Server Implementation  
**Date**: 2026-02-20  
**Version**: 1.0.0

## Installation

```bash
# Install from source
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Running the Server

### Development Mode

```bash
# Run with auto-reload
mcp-scraper --transport sse --port 3000

# Or using Python module
python -m mcp_scraper.server --transport sse --port 3000
```

### Production Mode

```bash
# Standard input/output (for MCP clients)
mcp-scraper --transport stdio

# Server-Sent Events (for HTTP clients)
mcp-scraper --transport sse --host 0.0.0.0 --port 3000
```

## Environment Configuration

Create a `.env` file:

```bash
# Proxy settings (optional)
PROXY_URL=http://proxy.example.com:8080

# Default timeout (seconds)
DEFAULT_TIMEOUT=30

# Max retries for failed requests
MAX_RETRIES=3

# Logging level
LOG_LEVEL=INFO
```

## Using the Tools

### Example 1: Simple Scraping

```python
# Using MCP client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to server
server_params = StdioServerParameters(
    command="mcp-scraper",
    args=["--transport", "stdio"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()
        
        # Call scrape_simple
        result = await session.call_tool("scrape_simple", {
            "url": "https://example.com",
            "extract": "text"
        })
        
        print(result.content[0].text)
```

### Example 2: Stealth Scraping

```python
result = await session.call_tool("scrape_stealth", {
    "url": "https://protected-site.com",
    "stealth_level": "maximum",
    "solve_cloudflare": True,
    "timeout": 60000
})
```

### Example 3: Structured Extraction

```python
result = await session.call_tool("extract_structured", {
    "url": "https://news.example.com/article",
    "selectors": {
        "title": "h1.article-title",
        "author": ".author-name",
        "date": "time.publish-date",
        "content": ".article-body"
    }
})
```

### Example 4: Batch Scraping

```python
result = await session.call_tool("scrape_batch", {
    "urls": [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ],
    "stealth_level": "minimal",
    "delay": 2.0
})
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_scraper --cov-report=html

# Run specific test file
pytest tests/unit/test_server.py -v
```

## Troubleshooting

### URL Validation Errors

If you get "Invalid URL" errors, check:
- URL uses http:// or https:// protocol
- URL is not a private IP (10.x.x.x, 192.168.x.x, etc.)
- URL is not localhost or 127.0.0.1

### Timeout Errors

Increase timeout for slow sites:
```python
{"url": "https://slow-site.com", "timeout": 60000}
```

### Cloudflare Protection

Enable challenge solving:
```python
{"url": "https://cloudflare-site.com", "stealth_level": "maximum", "solve_cloudflare": True}
```

## Next Steps

- Review the full specification: `specs/001-mcp-server-implementation/spec.md`
- Check implementation plan: `specs/001-mcp-server-implementation/plan.md`
- See API contracts: `specs/001-mcp-server-implementation/contracts/mcp-tools.json`
