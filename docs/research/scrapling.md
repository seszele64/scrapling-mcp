# Research Report: Implementing Scrapling as an MCP Server for Undetectable Web Scraping

## Executive Summary

This report provides comprehensive guidance on implementing Scrapling (a powerful Python web scraping framework) as a Model Context Protocol (MCP) server with a focus on undetectable scraping capabilities. Scrapling already has built-in MCP server support and offers extensive stealth features including browser fingerprint spoofing, Cloudflare bypass, proxy rotation, and human-like behavior simulation. The integration leverages FastMCP for simplified MCP server development while utilizing Scrapling's advanced `StealthyFetcher` and `StealthySession` classes for anti-detection capabilities.

---

## 1. Scrapling Overview

### What is Scrapling?

Scrapling is an adaptive web scraping framework written in Python that handles everything from single requests to full-scale crawls. It boasts **9.1k GitHub stars** and is actively maintained with over 1,100 commits.

**Repository**: https://github.com/D4Vinci/Scrapling

### Key Features

#### 1.1 Multiple Fetcher Types

| Fetcher | Use Case |
|---------|----------|
| `Fetcher` | Fast HTTP requests with TLS fingerprinting and HTTP/3 support |
| `DynamicFetcher` | Full browser automation using Playwright |
| `StealthyFetcher` | Advanced anti-bot bypass using Camoufox (modified Firefox) |
| `AsyncStealthySession` | Concurrent stealth browsing with tab pooling |

#### 1.2 Spider Framework
- Scrapy-like API with async callbacks
- Concurrent crawling with configurable limits
- Multi-session support (HTTP + browser in single spider)
- Pause/resume with checkpoint persistence
- Streaming mode for real-time results

#### 1.3 Adaptive Parsing
- Smart element tracking that survives website design changes
- CSS, XPath, text search, and regex selectors
- Element similarity algorithms for auto-relocation
- 10x faster JSON serialization than standard library

#### 1.4 Stealth Capabilities (Built-in)
- **Camoufox integration**: Modified Firefox browser with stealth patches
- **Cloudflare bypass**: Automatic Turnstile/captcha solving
- **Fingerprint spoofing**: OS, WebGL, WebRTC randomization
- **Human-like behavior**: Cursor movement, scroll patterns
- **GeoIP matching**: Aligns browser locale with proxy IP
- **Proxy rotation**: Built-in `ProxyRotator` class

### Basic Usage Examples

```python
# Simple HTTP request
from scrapling.fetchers import Fetcher
page = Fetcher.get('https://example.com')
data = page.css('.selector::text').getall()

# Stealth browser request
from scrapling.fetchers import StealthyFetcher
page = StealthyFetcher.fetch('https://protected-site.com', 
                               solve_cloudflare=True,
                               humanize=True,
                               proxy='http://user:pass@proxy:port')

# Session-based (reuses browser)
from scrapling.fetchers import StealthySession
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page1 = session.fetch('https://site1.com')
    page2 = session.fetch('https://site2.com')
```

---

## 2. MCP Server Basics

### What is MCP (Model Context Protocol)?

MCP is an open protocol that standardizes how AI applications connect to external tools and data sources. It defines a client-server architecture where:

- **MCP Host**: AI application (Claude Desktop, Cursor, etc.)
- **MCP Client**: Communicates with servers on behalf of the host
- **MCP Server**: Provides tools, resources, and prompts to clients

### MCP Primitives

| Primitive | Description |
|-----------|-------------|
| **Tools** | Functions the LLM can invoke with parameters |
| **Resources** | Data templates the LLM can read |
| **Prompts** | Reusable prompt templates |

### FastMCP Framework

FastMCP is the recommended Python framework for building MCP servers. It handles all protocol complexity automatically.

**Installation**:
```bash
pip install fastmcp
```

**Basic Server Structure**:
```python
from fastmcp import FastMCP

mcp = FastMCP(name="My Server")

@mcp.tool
def my_tool(param: str) -> str:
    """Tool description"""
    return result

@mcp.resource("resource://config")
def get_config() -> dict:
    return {"key": "value"}

if __name__ == "__main__":
    mcp.run()
```

---

## 3. Undetectable Scraping Techniques

### 3.1 Browser Fingerprint Randomization

Scrapling's `StealthyFetcher` provides comprehensive fingerprint management:

```python
page = StealthyFetcher.fetch(
    'https://example.com',
    os_randomize=True,      # Randomize OS fingerprints
    block_webrtc=True,     # Block WebRTC (prevents IP leaks)
    allow_webgl=True,      # Keep WebGL enabled (WAFs check this)
    geoip=True,           # Match browser locale to proxy IP
)
```

**Key fingerprint elements to randomize**:
- User-Agent string
- Screen resolution
- Timezone and locale
- WebGL renderer
- Canvas fingerprint
- Audio context
- Hardware concurrency (CPU cores)

### 3.2 Request Rotation and Delays

```python
import asyncio
import random
from scrapling.fetchers import AsyncStealthySession

async def crawl_with_delay():
    async with AsyncStealthySession(
        max_pages=3,
        headless=True
    ) as session:
        urls = ['https://site.com/page1', 'https://site.com/page2']
        
        for url in urls:
            # Random delay between 2-5 seconds
            await asyncio.sleep(random.uniform(2, 5))
            
            page = await session.fetch(url)
            # Process page...
```

### 3.3 User-Agent Management

Scrapling handles this automatically through browser impersonation:

```python
# Uses Camoufox's built-in UA rotation
page = StealthyFetcher.fetch('https://example.com')

# Or specify via extra_headers
page = StealthyFetcher.fetch(
    'https://example.com',
    extra_headers={'User-Agent': 'Mozilla/5.0 (custom UA)...'}
)
```

### 3.4 Proxy/Tor Integration

```python
# Single proxy
page = StealthyFetcher.fetch(
    'https://example.com',
    proxy='http://username:password@host:port'
)

# Proxy as dictionary
page = StealthyFetcher.fetch(
    'https://example.com',
    proxy={
        'server': 'http://proxy:port',
        'username': 'user',
        'password': 'pass'
    }
)

# Built-in proxy rotation (cyclic)
from scrapling.fetchers import ProxyRotator

rotator = ProxyRotator([
    'http://proxy1:port',
    'http://proxy2:port',
    'http://proxy3:port',
])
```

### 3.5 JavaScript Execution Handling

```python
# Wait for full JS execution
page = StealthyFetcher.fetch(
    'https://example.com',
    load_dom=True,      # Wait for DOMContentLoaded
    network_idle=True,  # Wait for no network activity for 500ms
    wait_selector='#content',  # Wait for specific element
    wait_selector_state='visible'
)

# Custom page automation
def scroll_and_wait(page):
    page.mouse.wheel(0, 500)
    page.wait_for_timeout(1000)

page = StealthyFetcher.fetch(
    'https://example.com',
    page_action=scroll_and_wait
)
```

### 3.6 CAPTCHA Solving Approaches

```python
# Automatic Cloudflare Turnstile solving
page = StealthyFetcher.fetch(
    'https://protected-site.com',
    solve_cloudflare=True,  # Solves all 3 challenge types
    timeout=60000,          # 60s for complex challenges
    humanize=True           # Human-like behavior during solving
)
```

**Cloudflare challenges handled**:
- JavaScript challenges
- Interactive challenges (click verification)
- Invisible challenges (background verification)

### 3.7 Rate Limiting Strategies

```python
from scrapling.spiders import Spider, Request, Response

class RateLimitedSpider(Spider):
    name = "slow_spider"
    start_urls = ["https://example.com"]
    
    # Per-domain rate limiting
    per_domain_delay = 2.0  # 2 seconds between requests to same domain
    
    async def parse(self, response: Response):
        # Extract data...
        yield {"data": "value"}
        
        # Respect rate limits
        await asyncio.sleep(1)  # Additional delay

# Run with concurrency limits
result = RateLimitedSpider(
    concurrent_requests=5,  # Max concurrent requests
    download_delay=1.0       # Delay between requests
).start()
```

---

## 4. Integration Approach

### 4.1 Required MCP Tools/Resources to Expose

Based on Scrapling's capabilities, the following MCP primitives should be exposed:

| Tool/Resource | Purpose |
|---------------|---------|
| `scrape_url` | Single URL scraping with CSS/XPath selectors |
| `scrape_stealth` | Stealth mode with Cloudflare bypass |
| `scrape_dynamic` | Full JavaScript rendering |
| `scrape_session` | Multi-page session with cookies |
| `extract_text` | Extract plain text from URL |
| `extract_html` | Extract raw HTML from URL |
| `config://stealth` | Current stealth configuration |
| `resource://proxies` | Proxy list management |

### 4.2 Configuration Options for Stealth Settings

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class StealthConfig:
    # Browser settings
    headless: bool = True
    block_images: bool = False
    disable_resources: bool = False
    
    # Stealth features
    solve_cloudflare: bool = False
    humanize: bool = True
    geoip: bool = True
    os_randomize: bool = True
    block_webrtc: bool = True
    allow_webgl: bool = True
    
    # Network
    proxy: Optional[str] = None
    timeout: int = 30000
    
    # Cloudflare specific
    cloudflare_timeout: int = 60000
    
    # Resource blocking
    block_ads: bool = True
    
    # Referer spoofing
    google_search: bool = True  # Sets Google referer
```

### 4.3 Error Handling and Retry Logic

```python
import asyncio
from typing import Optional

class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass

class BlockedError(ScrapingError):
    """Site blocked the request"""
    pass

class TimeoutError(ScrapingError):
    """Request timed out"""
    pass

async def scrape_with_retry(
    url: str,
    config: StealthConfig,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Optional[object]:
    """Scrape with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            page = await StealthyFetcher.async_fetch(
                url,
                headless=config.headless,
                solve_cloudflare=config.solve_cloudflare,
                humanize=config.humanize,
                geoip=config.geoip,
                os_randomize=config.os_randomize,
                proxy=config.proxy,
                timeout=config.timeout,
                block_webrtc=config.block_webrtc,
                allow_webgl=config.allow_webgl,
                google_search=config.google_search
            )
            return page
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'cloudflare' in error_msg or 'turnstile' in error_msg:
                # Increase timeout for Cloudflare
                config.timeout = int(config.timeout * backoff_factor)
                
            elif 'blocked' in error_msg or '403' in error_msg:
                # Switch proxy on block
                config.proxy = await rotate_proxy(config.proxy_list)
                
            if attempt == max_retries - 1:
                raise ScrapingError(f"Failed after {max_retries} attempts: {e}")
            
            # Exponential backoff
            wait_time = backoff_factor ** attempt
            await asyncio.sleep(wait_time)
    
    return None
```

### 4.4 Response Formatting

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ScrapedContent:
    url: str
    title: Optional[str]
    text: Optional[str]
    html: Optional[str]
    links: List[str]
    images: List[str]
    metadata: Dict[str, Any]
    selectors_used: List[str]
    fetch_time_ms: int
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "html": self.html,
            "links": self.links,
            "images": self.images,
            "metadata": self.metadata,
            "selectors": self.selectors_used,
            "fetch_time_ms": self.fetch_time_ms
        }

def format_response(page, url: str, selectors: List[str]) -> ScrapedContent:
    """Format Scrapling response into structured output"""
    
    import time
    
    return ScrapedContent(
        url=url,
        title=page.css_first('title::text').get() if page.css('title') else None,
        text=page.css('body::text').get(),
        html=str(page),
        links=page.css('a::attr(href)').getall(),
        images=page.css('img::attr(src)').getall(),
        metadata={
            "status": page.status if hasattr(page, 'status') else 200,
            "content_type": page.headers.get('content-type') if hasattr(page, 'headers') else None
        },
        selectors_used=selectors,
        fetch_time_ms=0  # Track separately
    )
```

---

## 5. Implementation Recommendations

### 5.1 Best Practices for Undetectable Scraping

1. **Always use sessions**: Reuse browser instances to maintain consistent fingerprints
2. **Enable geoip with proxies**: Match browser locale to proxy location
3. **Use solve_cloudflare cautiously**: Only when needed; increases detection surface
4. **Implement exponential backoff**: Start slow, increase speed gradually
5. **Rotate user agents**: Even with Camoufox, periodic rotation helps
6. **Monitor for blocks**: Track 403/429 responses and adjust strategy

### 5.2 Recommended Libraries and Dependencies

```toml
# pyproject.toml
[project]
name = "scrapling-mcp"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    "scrapling[all]",       # Core + all fetchers
    "fastmcp>=2.0",         # MCP server framework
    "httpx>=0.25",          # Async HTTP (for proxy rotation)
    "python-dotenv>=1.0",   # Environment variables
    "pydantic>=2.0",        # Data validation
    "loguru>=0.7",          # Logging
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "ruff>=0.1",
]
```

### 5.3 Configuration Patterns for Different Use Cases

```python
# Pattern 1: Simple static pages
simple_config = StealthConfig(
    headless=True,
    disable_resources=True,
    timeout=10000
)

# Pattern 2: Protected sites (Cloudflare)
protected_config = StealthConfig(
    headless=True,
    solve_cloudflare=True,
    humanize=True,
    geoip=True,
    os_randomize=True,
    timeout=60000,
    google_search=True
)

# Pattern 3: High-anonymity scraping
anonymous_config = StealthConfig(
    headless=True,
    block_webrtc=True,
    block_images=True,
    disable_resources=True,
    os_randomize=True,
    geoip=True,
    solve_cloudflare=True,
    humanize=True,
    proxy=rotation.next()  # Use rotating proxies
)

# Pattern 4: Debugging (visible browser)
debug_config = StealthConfig(
    headless=False,  # Visible browser
    timeout=120000   # Long timeout for manual intervention
)
```

### 5.4 Security Considerations

1. **Never hardcode credentials**: Use environment variables for proxy auth
2. **Validate URLs**: Prevent SSRF attacks via URL parameters
3. **Rate limit your server**: Prevent abuse of your MCP server
4. **Log responsibly**: Avoid logging sensitive data
5. **Respect robots.txt**: Check and honor site policies
6. **Legal compliance**: Ensure scraping is legal in your jurisdiction

---

## 6. Code Examples

### 6.1 Basic MCP Server Structure with Scrapling Integration

```python
"""
Scrapling MCP Server - Undetectable Web Scraping
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import Scrapling components
from scrapling.fetchers import (
    Fetcher,
    StealthyFetcher,
    AsyncStealthySession,
)
from scrapling.parser import Selector

# Create MCP server
mcp = FastMCP(name="Scrapling MCP Server")

# Configuration models
class ScrapeOptions(BaseModel):
    url: str = Field(..., description="URL to scrape")
    css_selector: Optional[str] = Field(None, description="CSS selector for extraction")
    xpath_selector: Optional[str] = Field(None, description="XPath selector for extraction")
    extract_text: bool = Field(True, description="Extract text content")
    extract_html: bool = Field(False, description="Extract HTML content")
    timeout: int = Field(30000, description="Request timeout in milliseconds")

class StealthOptions(BaseModel):
    """Stealth configuration for advanced scraping"""
    headless: bool = Field(True, description="Run browser in headless mode")
    solve_cloudflare: bool = Field(False, description="Solve Cloudflare challenges")
    humanize: bool = Field(True, description="Humanize mouse movements")
    geoip: bool = Field(True, description="Match browser locale to proxy IP")
    os_randomize: bool = Field(True, description="Randomize OS fingerprints")
    block_webrtc: bool = Field(True, description="Block WebRTC to prevent IP leaks")
    allow_webgl: bool = Field(True, description="Allow WebGL (WAFs check this)")
    google_search: bool = Field(True, description="Set Google referer")
    proxy: Optional[str] = Field(None, description="Proxy URL (http://user:pass@host:port)")
    timeout: int = Field(30000, description="Request timeout in milliseconds")
    block_images: bool = Field(False, description="Block images to save bandwidth")
    disable_resources: bool = Field(False, description="Disable fonts, images, media")

class ScrapeResult(BaseModel):
    """Structured scrape result"""
    url: str
    success: bool
    title: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    selected_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fetch_time_ms: int = 0
    status_code: int = 0


# Global session management
_session: Optional[AsyncStealthySession] = None

async def get_session(stealth: StealthOptions) -> AsyncStealthySession:
    """Get or create stealth session"""
    global _session
    if _session is None:
        _session = AsyncStealthySession(
            headless=stealth.headless,
            solve_cloudflare=stealth.solve_cloudflare,
            humanize=stealth.humanize,
            geoip=stealth.geoip,
            os_randomize=stealth.os_randomize,
            block_webrtc=stealth.block_webrtc,
            allow_webgl=stealth.allow_webgl,
            google_search=stealth.google_search,
            timeout=stealth.timeout,
            block_images=stealth.block_images,
            disable_resources=stealth.disable_resources,
        )
        await _session.__aenter__()
    return _session


# MCP Tools
@mcp.tool
async def scrape_simple(
    url: str,
    css_selector: Optional[str] = None,
    extract_text: bool = True,
    extract_html: bool = False
) -> dict:
    """
    Simple web scraping with basic HTTP request.
    Use for static pages without anti-bot protection.
    
    Args:
        url: Target URL to scrape
        css_selector: Optional CSS selector for targeted extraction
        extract_text: Extract text content
        extract_html: Extract HTML content
    
    Returns:
        Dictionary with scraped content
    """
    start_time = time.time()
    
    try:
        # Use Fetcher for simple requests
        page = Fetcher.get(url, impersonate='chrome')
        
        result = {
            "url": url,
            "success": True,
            "status_code": 200,
            "title": page.css_first('title::text').get() if page.css('title') else None,
            "links": page.css('a::attr(href)').getall(),
            "images": page.css('img::attr(src)').getall(),
        }
        
        if extract_text:
            if css_selector:
                result["text"] = page.css(css_selector).get()
            else:
                result["text"] = page.css('body::text').get()
        
        if extract_html:
            if css_selector:
                result["html"] = str(page.css(css_selector))
            else:
                result["html"] = str(page)
        
        if css_selector:
            result["selected_data"] = {
                "selector": css_selector,
                "matches": page.css(css_selector).getall()
            }
        
        result["fetch_time_ms"] = int((time.time() - start_time) * 1000)
        
        return result
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e),
            "fetch_time_ms": int((time.time() - start_time) * 1000)
        }


@mcp.tool
async def scrape_stealth(
    url: str,
    css_selector: Optional[str] = None,
    xpath_selector: Optional[str] = None,
    solve_cloudflare: bool = False,
    humanize: bool = True,
    geoip: bool = True,
    os_randomize: bool = True,
    proxy: Optional[str] = None,
    timeout: int = 30000,
    headless: bool = True
) -> dict:
    """
    Stealth web scraping with anti-bot bypass capabilities.
    Uses Camoufox browser with fingerprint spoofing.
    
    Args:
        url: Target URL to scrape
        css_selector: Optional CSS selector for extraction
        xpath_selector: Optional XPath selector for extraction  
        solve_cloudflare: Automatically solve Cloudflare challenges
        humanize: Humanize cursor movements
        geoip: Match browser locale to proxy IP
        os_randomize: Randomize OS fingerprints
        proxy: Proxy URL (http://user:pass@host:port)
        timeout: Request timeout in milliseconds
        headless: Run browser in headless mode
    
    Returns:
        Dictionary with scraped content and metadata
    """
    start_time = time.time()
    
    try:
        # Use StealthyFetcher for protected sites
        page = await StealthyFetcher.async_fetch(
            url,
            headless=headless,
            solve_cloudflare=solve_cloudflare,
            humanize=humanize,
            geoip=geoip,
            os_randomize=os_randomize,
            proxy=proxy,
            timeout=timeout,
            block_webrtc=True,
            allow_webgl=True,
            google_search=True,
            network_idle=True,
            load_dom=True
        )
        
        result = {
            "url": url,
            "success": True,
            "status_code": 200,
            "title": page.css_first('title::text').get() if page.css('title') else None,
            "links": page.css('a::attr(href)').getall(),
            "images": page.css('img::attr(src)').getall(),
            "text": page.css('body::text').get() if page.css('body') else None,
            "html": str(page),
            "stealth_used": {
                "cloudflare_solved": solve_cloudflare,
                "humanized": humanize,
                "geoip_matched": geoip,
                "os_randomized": os_randomize
            }
        }
        
        # Apply custom selectors if provided
        if css_selector:
            result["css_selected"] = page.css(css_selector).getall()
        
        if xpath_selector:
            result["xpath_selected"] = page.xpath(xpath_selector).getall()
        
        result["fetch_time_ms"] = int((time.time() - start_time) * 1000)
        
        return result
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e),
            "fetch_time_ms": int((time.time() - start_time) * 1000)
        }


@mcp.tool
async def scrape_session(
    urls: List[str],
    solve_cloudflare: bool = False,
    proxy: Optional[str] = None,
    concurrent: bool = False
) -> List[dict]:
    """
    Multi-page scraping with session persistence.
    Reuses browser instance for better performance and consistency.
    
    Args:
        urls: List of URLs to scrape
        solve_cloudflare: Solve Cloudflare challenges
        proxy: Proxy URL
        concurrent: Scrape URLs concurrently
    
    Returns:
        List of scraped results
    """
    results = []
    
    try:
        async with AsyncStealthySession(
            headless=True,
            solve_cloudflare=solve_cloudflare,
            humanize=True,
            geoip=True,
            os_randomize=True,
            proxy=proxy,
            max_pages=3
        ) as session:
            
            if concurrent:
                # Concurrent scraping
                tasks = [session.fetch(url) for url in urls]
                pages = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, page in zip(urls, pages):
                    if isinstance(page, Exception):
                        results.append({"url": url, "success": False, "error": str(page)})
                    else:
                        results.append({
                            "url": url,
                            "success": True,
                            "text": page.css('body::text').get(),
                            "links": page.css('a::attr(href)').getall()
                        })
            else:
                # Sequential scraping
                for url in urls:
                    page = await session.fetch(url)
                    results.append({
                        "url": url,
                        "success": True,
                        "title": page.css_first('title::text').get(),
                        "text": page.css('body::text').get()
                    })
                    # Small delay between requests
                    await asyncio.sleep(1)
        
        return results
        
    except Exception as e:
        return [{"error": str(e), "success": False}]


@mcp.tool
async def extract_content(
    url: str,
    selectors: Dict[str, str],
    stealth: bool = False,
    solve_cloudflare: bool = False
) -> dict:
    """
    Extract specific content using multiple selectors.
    
    Args:
        url: Target URL
        selectors: Dictionary of name -> CSS selector pairs
        stealth: Use stealth mode
        solve_cloudflare: Solve Cloudflare challenges
    
    Returns:
        Dictionary with extracted data
    """
    try:
        if stealth:
            page = await StealthyFetcher.async_fetch(
                url,
                solve_cloudflare=solve_cloudflare,
                humanize=True,
                network_idle=True
            )
        else:
            page = Fetcher.get(url, impersonate='chrome')
        
        extracted = {}
        for name, selector in selectors.items():
            elements = page.css(selector)
            # Get both single value and all values
            extracted[name] = {
                "first": elements.get(),
                "all": elements.getall(),
                "count": len(elements)
            }
        
        return {
            "url": url,
            "success": True,
            "extracted": extracted,
            "page_title": page.css_first('title::text').get()
        }
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e)
        }


# MCP Resources
@mcp.resource("resource://stealth-config")
def get_stealth_config() -> dict:
    """Get default stealth configuration"""
    return {
        "headless": True,
        "solve_cloudflare": False,
        "humanize": True,
        "geoip": True,
        "os_randomize": True,
        "block_webrtc": True,
        "allow_webgl": True,
        "google_search": True,
        "default_timeout": 30000,
        "cloudflare_timeout": 60000
    }


@mcp.resource("resource://available-browsers")
def get_available_browsers() -> dict:
    """Get available browser types for scraping"""
    return {
        "browsers": [
            {
                "name": "chrome",
                "type": "http",
                "stealth_level": "basic",
                "description": "Fast HTTP requests with Chrome TLS fingerprint"
            },
            {
                "name": "firefox", 
                "type": "http",
                "stealth_level": "basic",
                "description": "Firefox TLS fingerprint"
            },
            {
                "name": "stealthy",
                "type": "browser",
                "stealth_level": "maximum",
                "description": "Camoufox browser with full stealth capabilities"
            }
        ]
    }


# Main entry point
if __name__ == "__main__":
    # Run with stdio transport (for Claude Desktop, etc.)
    mcp.run()
    
    # Or run with HTTP transport:
    # mcp.run(transport="http", host="0.0.0.0", port=8000)
```

### 6.2 Stealth Configuration Options

```python
"""
Stealth Configuration Examples
"""

# Minimal stealth - just enough to avoid basic detection
minimal_stealth = {
    "headless": True,
    "block_webrtc": True,
    "google_search": True,
    "timeout": 15000
}

# Standard stealth - good balance of speed and anonymity
standard_stealth = {
    "headless": True,
    "solve_cloudflare": False,
    "humanize": True,
    "geoip": True,
    "os_randomize": True,
    "block_webrtc": True,
    "allow_webgl": True,
    "google_search": True,
    "timeout": 30000,
    "network_idle": True
}

# Maximum stealth - for heavily protected sites
maximum_stealth = {
    "headless": True,
    "solve_cloudflare": True,      # Solve Cloudflare
    "humanize": True,              # Human mouse movements
    "humanize_duration": 1.5,      # Max 1.5s cursor movement
    "geoip": True,                 # Match locale to proxy
    "os_randomize": True,          # Randomize OS fingerprint
    "block_webrtc": True,           # Block WebRTC
    "allow_webgl": True,            # Keep WebGL (WAFs check this!)
    "google_search": True,         # Google referer
    "block_images": True,          # Block images
    "disable_resources": True,     # Block fonts/media
    "timeout": 60000,              # 60s for Cloudflare
    "network_idle": True,
    "load_dom": True,
    "wait_selector": "body",
    "wait_selector_state": "visible"
}

# Custom proxy configuration
proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "your_username",
    "password": "your_password"
}

# Use with stealth fetcher
page = StealthyFetcher.fetch(
    'https://example.com',
    proxy=proxy_config,  # Pass as dict
    geoip=True,          # Will use proxy location for locale
    solve_cloudflare=True
)
```

### 6.3 Tool Definitions for Common Scraping Operations

```python
"""
Complete MCP Tool Definitions with Full Type Hints
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

mcp = FastMCP(name="Scrapling Tools")

# ========== Input Models ==========

class SimpleScrapeInput(BaseModel):
    """Input for simple scrape tool"""
    url: str = Field(..., description="The URL to scrape")
    selector: Optional[str] = Field(None, description="CSS selector to extract")
    extract: Literal["text", "html", "both"] = Field("text", description="What to extract")

class StealthScrapeInput(BaseModel):
    """Input for stealth scrape tool"""
    url: str = Field(..., description="The URL to scrape")
    selector: Optional[str] = Field(None, description="CSS selector to extract")
    solve_cloudflare: bool = Field(False, description="Solve Cloudflare challenges")
    proxy: Optional[str] = Field(None, description="Proxy URL")
    timeout: int = Field(30000, description="Timeout in ms")
    headless: bool = Field(True, description="Run headless")

class BatchScrapeInput(BaseModel):
    """Input for batch scraping"""
    urls: List[str] = Field(..., description="List of URLs to scrape")
    selector: Optional[str] = Field(None, description="CSS selector for all URLs")
    stealth: bool = Field(False, description="Use stealth mode")
    delay: float = Field(1.0, description="Delay between requests (seconds)")

class ExtractInput(BaseModel):
    """Input for multi-field extraction"""
    url: str = Field(..., description="The URL to scrape")
    fields: Dict[str, str] = Field(..., description="Field name -> CSS selector mapping")
    stealth: bool = Field(False, description="Use stealth mode")


# ========== Tool Implementations ==========

@mcp.tool
async def scrape(
    url: str,
    selector: Optional[str] = None,
    extract: Literal["text", "html", "both"] = "text"
) -> Dict[str, Any]:
    """
    Scrape a URL using simple HTTP request.
    
    Best for: Static websites without anti-bot protection.
    Speed: Fast (~100-500ms per page)
    Detection risk: Low
    """
    try:
        page = Fetcher.get(url, impersonate='chrome')
        
        result = {
            "url": url,
            "success": True,
            "status": 200,
            "title": page.css_first('title::text').get()
        }
        
        if extract in ("text", "both"):
            result["text"] = page.css(selector or 'body::text').get()
        
        if extract in ("html", "both"):
            result["html"] = str(page.css(selector or 'body'))
        
        return result
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e)
        }


@mcp.tool  
async def scrape_protected(
    url: str,
    selector: Optional[str] = None,
    solve_cloudflare: bool = False,
    proxy: Optional[str] = None,
    timeout: int = 30000
) -> Dict[str, Any]:
    """
    Scrape a protected URL using stealth browser.
    
    Best for: Cloudflare-protected sites, anti-bot systems.
    Speed: Slow (~5-30s per page, more with Cloudflare)
    Detection risk: Very low (uses Camoufox)
    """
    try:
        page = await StealthyFetcher.async_fetch(
            url,
            solve_cloudflare=solve_cloudflare,
            humanize=True,
            geoip=bool(proxy),
            os_randomize=True,
            proxy=proxy,
            timeout=timeout,
            network_idle=True,
            load_dom=True
        )
        
        return {
            "url": url,
            "success": True,
            "status": 200,
            "title": page.css_first('title::text').get(),
            "text": page.css(selector or 'body::text').get(),
            "html": str(page),
            "cloudflare_solved": solve_cloudflare
        }
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e)
        }


@mcp.tool
async def scrape_batch(
    urls: List[str],
    selector: Optional[str] = None,
    stealth: bool = False,
    delay: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Scrape multiple URLs in batch.
    
    Best for: Crawling multiple pages efficiently.
    Handles: Rate limiting, error recovery.
    """
    import asyncio
    
    results = []
    
    async with AsyncStealthySession(
        headless=True,
        solve_cloudflare=stealth,
        max_pages=3
    ) as session:
        
        for url in urls:
            try:
                page = await session.fetch(url)
                
                results.append({
                    "url": url,
                    "success": True,
                    "title": page.css_first('title::text').get(),
                    "content": page.css(selector or 'body::text').get() if selector else None
                })
                
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
            
            # Respectful delay
            await asyncio.sleep(delay)
    
    return results


@mcp.tool
async def extract_structured(
    url: str,
    fields: Dict[str, str],
    stealth: bool = False
) -> Dict[str, Any]:
    """
    Extract structured data using multiple field selectors.
    
    Best for: Product pages, listings, structured content.
    Returns: Dictionary mapping field names to extracted values.
    """
    try:
        if stealth:
            page = await StealthyFetcher.async_fetch(
                url,
                solve_cloudflare=True,
                humanize=True,
                network_idle=True
            )
        else:
            page = Fetcher.get(url)
        
        extracted = {}
        for field_name, css_selector in fields.items():
            elements = page.css(css_selector)
            extracted[field_name] = {
                "first": elements.get(),
                "all": elements.getall(),
                "count": len(elements)
            }
        
        return {
            "url": url,
            "success": True,
            "title": page.css_first('title::text').get(),
            "data": extracted
        }
        
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run()
```

---

## Sources

1. **Scrapling GitHub Repository**: https://github.com/D4Vinci/Scrapling
2. **Scrapling Documentation**: https://scrapling.readthedocs.io/
3. **StealthyFetcher Guide**: https://scrapling.readthedocs.io/en/v0.3.4/fetching/stealthy/
4. **FastMCP Documentation**: https://gofastmcp.com/
5. **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
6. **Camoufox Browser**: https://github.com/daijro/camoufox
7. **Playwright Python API**: https://playwright.dev/python/docs/intro

---

## Summary

Implementing Scrapling as an MCP server for undetectable web scraping is highly achievable due to Scrapling's built-in MCP support and comprehensive stealth features. Key recommendations:

1. **Use FastMCP** for simplified MCP server development
2. **Leverage StealthyFetcher** with Camoufox for maximum stealth
3. **Implement session management** for better performance and fingerprint consistency
4. **Configure geoip + proxy** together for location spoofing
5. **Use solve_cloudflare sparingly** as it increases detection surface
6. **Implement proper error handling** with exponential backoff for production use
7. **Always respect robots.txt** and site terms of service

The provided code examples offer a complete starting point for building a production-ready undetectable scraping MCP server.
