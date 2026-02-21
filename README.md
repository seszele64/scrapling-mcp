# Scrapling MCP Server

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Project Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/tr1x/mcp-scraper)

A Model Context Protocol (MCP) server that provides web scraping capabilities with an integrated stealth-aware scraping engine. Built on top of [FastMCP](https://github.com/jlowin/fastmcp) and leveraging the [Scrapling](https://github.com/D4Vinci/Scrapling) library.

## Overview

The Scrapling MCP Server enables AI agents to:
- Fetch web content reliably from websites with varying levels of anti-bot protection
- Render JavaScript when necessary to access dynamically loaded content
- Bypass common anti-bot measures through configurable stealth settings
- Handle session-based scraping for websites requiring authentication
- Extract structured data using CSS selectors from scraped pages

## Key Features

| Feature | Description |
|---------|-------------|
| **JavaScript Rendering** | Full browser-based rendering for dynamic content |
| **Stealth Modes** | Multiple pre-configured stealth levels (Minimal, Standard, Maximum) |
| **Cloudflare Support** | Automatic Cloudflare challenge detection and solving |
| **Session Management** | Persistent sessions for stateful scraping |
| **Proxy Rotation** | Support for proxy lists with automatic rotation |
| **Retry Logic** | Exponential backoff with configurable retry attempts |
| **CSS Extraction** | Structured data extraction using CSS selectors |
| **URL Validation** | Built-in SSRF protection and security checks |
| **MCP Integration** | Native MCP protocol support for AI agent integration |
| **Spider Framework** | Scrapy-like API with async callbacks and concurrent crawling |
| **Camoufox Integration** | Modified Firefox browser with stealth patches |

## Installation

```bash
# Clone the repository
git clone https://github.com/tr1x/mcp-scraper.git
cd mcp-scraper

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from mcp_scraper.stealth import scrape_with_retry, format_response, get_standard_stealth

async def scrape_example():
    # Use standard stealth settings
    config = get_standard_stealth()
    
    # Scrape a URL
    page = await scrape_with_retry(
        url="https://example.com",
        config=config,
        max_retries=3
    )
    
    # Format the response
    result = format_response(page, "https://example.com")
    print(f"Title: {result.get('title')}")
    print(f"Content: {result.get('text')[:200]}...")
```

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `scrape_simple` | Fast HTTP scraping with TLS fingerprinting |
| `scrape_stealth` | Browser automation with configurable stealth |
| `scrape_session` | Session-based scraping with persistent state |
| `extract_structured` | Extract structured data using CSS selectors |
| `scrape_batch` | Process multiple URLs in sequence |

For detailed documentation on all tools and their parameters, see [AGENTS.md](AGENTS.md).

## Documentation

- [AGENTS.md](AGENTS.md) - Comprehensive project documentation
- [docs/quickstart.md](docs/quickstart.md) - Quick start guide
- [VDD_TESTING.md](VDD_TESTING.md) - Testing guidelines

## Configuration

Create a `.env` file based on `.env.example`:

```bash
# Proxy URL for requests (optional)
PROXY_URL=

# Default timeout in seconds (1-300)
DEFAULT_TIMEOUT=30

# Logging level
LOG_LEVEL=INFO

# Maximum retry attempts (0-10)
MAX_RETRIES=3
```

## Stealth Levels

| Level | Use Case | Timeout |
|-------|----------|---------|
| **Minimal** | Fast, simple sites | 15s |
| **Standard** | Most scraping tasks | 30s |
| **Maximum** | Protected sites, Cloudflare | 60s |

## License

MIT License - see [LICENSE](LICENSE) for details.
