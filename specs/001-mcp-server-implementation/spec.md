# Phase 2: MCP Server Implementation Specification

**Project**: Scrapling MCP Server  
**Phase**: 2 - MCP Server Implementation  
**Status**: Draft  
**Created**: 2026-02-20  
**Last Updated**: 2026-02-20  
**Version**: 1.0.0

---

## 1. Overview

This specification defines the implementation of the Scrapling MCP Server, a Model Context Protocol (MCP) server that provides web scraping capabilities. The server exposes five core scraping tools that AI agents can invoke to retrieve content from websites with varying levels of protection.

The server provides these core capabilities:
- Basic HTTP scraping for public, unprotected websites
- Stealth-aware scraping with configurable protection bypass
- Session-based scraping for maintaining login state
- Structured data extraction using CSS selectors
- Batch processing for multiple URLs in sequence

The implementation must adhere to the five constitutional principles established for the project:
- **Principle I**: MCP Protocol Compliance
- **Principle II**: Stealth-First Design
- **Principle III**: Security by Default
- **Principle IV**: Reliability Through Retry
- **Principle V**: Configuration Flexibility

---

## 2. User Stories

### US1: Simple Scraping (Priority: P1)

**As an** AI agent or developer,  
**I want to** perform basic HTTP scraping of static web pages without stealth features,  
**So that** I can quickly retrieve content from well-behaved websites that do not implement anti-bot protection.

**Why this priority**: Simple scraping represents the core functionality and default use case. Most AI agent tasks involve fetching public, unprotected content where stealth is unnecessary overhead.

**Independent Test**: Can be fully tested by invoking scrape_simple on example.com and verifying the response contains valid HTML and text content within 15 seconds.

**Acceptance Scenarios**:

1. **Given** a valid public URL (e.g., "https://example.com"), **When** the user invokes scrape_simple with no optional parameters, **Then** the tool returns JSON with url, status_code 200, title, text, and html fields.

2. **Given** a valid URL with a CSS selector parameter, **When** the user invokes scrape_simple with selector="h1", **Then** the response includes extracted text from all h1 elements under the "selectors" key.

3. **Given** a URL that returns a 404 status, **When** the user invokes scrape_simple, **Then** the tool returns status_code 404 with error message, not an exception.

---

### US2: Stealth Scraping (Priority: P2)

**As an** AI agent or developer,  
**I want to** scrape websites with anti-bot protection using configurable stealth settings,  
**So that** I can successfully retrieve content from protected sites and rate-limited endpoints while minimizing detection.

**Why this priority**: Stealth scraping is essential for accessing protected content that simple scraping cannot reach. This differentiates the tool from basic HTTP clients.

**Independent Test**: Can be tested by attempting to scrape a known protected site with maximum stealth level and verifying successful content retrieval.

**Acceptance Scenarios**:

1. **Given** a URL with anti-bot protection, **When** the user invokes scrape_stealth with solve_cloudflare=true, **Then** the tool solves the challenge and returns page content with status_code 200.

2. **Given** a URL with anti-bot protection, **When** the user invokes scrape_stealth with solve_cloudflare=false (default), **Then** the tool returns a protection error with descriptive message.

3. **Given** a URL, **When** the user specifies stealth_level="maximum", **Then** the configuration includes all maximum protection settings (challenge solving, human-like behavior, network wait, 60-second timeout).

---

### US3: Batch & Structured Extraction (Priority: P3)

**As an** AI agent or developer,  
**I want to** scrape multiple URLs in sequence and extract structured data using CSS selectors,  
**So that** I can efficiently gather and parse data from multiple web sources in a single operation.

**Why this priority**: Batch processing and structured extraction are productivity features that reduce the number of tool invocations needed for data collection tasks.

**Independent Test**: Can be tested by providing a list of 3-5 URLs to scrape_batch or selector mappings to extract_structured and verifying correct aggregated/extracted results.

**Acceptance Scenarios**:

1. **Given** a list of 5 URLs, **When** the user invokes scrape_batch, **Then** the response includes total count, successful count, failed count, and array of results with per-URL status.

2. **Given** a URL and selector mappings {"title": "h1", "links": "a@href"}, **When** the user invokes extract_structured, **Then** the response includes extracted data under "extracted" key with title and links fields.

3. **Given** a batch of URLs where 2 fail, **When** the user invokes scrape_batch, **Then** the 3 successful results are returned with failed results showing error details.

---

### Edge Cases

- **What happens when URL is internal/private?**: System blocks the request and returns error explaining that security validation prevented access to internal networks.
- **How does system handle timeout?**: Applies retry logic with exponential backoff; returns TimeoutError after max_retries attempts.
- **What happens with malformed HTML?**: Returns available content (text/HTML); logs warning without failing.
- **How does system handle network failures?**: Catches network exceptions, retries on transient failures, returns descriptive error after exhausting retries.
- **What happens when all proxies in rotation fail?**: Returns error indicating all proxies failed with last proxy error message.

---

## 3. Requirements

### Functional Requirements

- **FR-001**: The server MUST initialize as an MCP server application with proper logging and environment-based settings. Server name must be "Scrapling MCP Server". Must load configuration from environment variables (DEFAULT_TIMEOUT, MAX_RETRIES, LOG_LEVEL). Must use structured logging in JSON format with fields: timestamp (ISO 8601), level (DEBUG/INFO/WARNING/ERROR), message (string), context (object with tool_name, url, session_id when applicable).

- **FR-002**: All scraping tools MUST validate URLs before making requests to prevent unauthorized access to internal systems. Must implement URL validation that blocks non-HTTP(S) protocols, private IP addresses (10.x.x.x, 172.16-31.x.x, 192.168.x.x), localhost variants (localhost, 127.0.0.1, ::1), internal hostnames (*.local, *.internal, *.corp), and link-local addresses (169.254.x.x).

- **FR-003**: The scrape_simple tool MUST provide basic HTTP scraping capability. Required parameter: url. Optional parameters: selector, extract (default "text"), timeout (default 30000ms). Must return JSON with url, status_code, title, text, html, headers, and optionally selectors.

- **FR-004**: The scrape_stealth tool MUST provide stealth-aware scraping with configurable protection bypass. Required parameter: url. Optional parameters: stealth_level (minimal/standard/maximum, default standard), solve_cloudflare (default false), network_idle (default true), load_dom (default true), timeout, proxy. Must map stealth levels to pre-configured profiles with appropriate protection settings.

- **FR-005**: The scrape_session tool MUST provide session-based scraping with persistent state. Required parameter: url. Optional parameters: session_id, cookies, stealth_level. Must maintain global session cache keyed by session_id. Must persist cookies across requests within same session. Must recreate session when configuration changes.

- **FR-006**: The extract_structured tool MUST provide structured data extraction using CSS selectors. Required parameters: url, selectors (object mapping name to CSS selector). Optional parameter: stealth_level. Must support text extraction, HTML extraction, and attribute extraction (@attribute syntax). Must return extracted data under "extracted" key in response.

- **FR-007**: The scrape_batch tool MUST provide batch processing of multiple URLs. Required parameter: urls (array, max 100 URLs). Optional parameters: stealth_level, delay (default 1.0 seconds). Must process URLs sequentially with configurable delay. Must report total, successful, and failed counts. Must continue processing remaining URLs if some fail.

- **FR-008**: The system MUST implement error handling with retry logic. Must implement custom exception hierarchy: ScrapeError (base), CloudflareError, BlockedError, TimeoutError. Must implement exponential backoff: delay = backoff_factor ^ retry_count with default backoff_factor of 1.5. Must support proxy rotation with proxy_list parameter. Must detect block patterns (403, 429 status codes).

- **FR-009**: All tools MUST return JSON-serializable responses. Must include original URL, HTTP status code, page title when available, extracted text and/or HTML, error information when applicable. Must use consistent response formatting across all tools.

- **FR-010**: The system MUST implement configuration with environment-based settings and stealth profiles. Must support .env file loading. Must provide StealthConfig data structure and preset stealth levels (minimal, standard, maximum).

---

## 4. Key Entities

- **ScrapingRequest**: Represents a request to scrape a URL with associated parameters including url, selector, extract, timeout, stealth_level, session_id, cookies, proxy, solve_cloudflare, network_idle, load_dom.

- **ScrapingResponse**: Represents the response from a scraping operation including url, status_code, title, text, html, headers, selectors, error, and timestamp.

- **StealthConfig**: Configuration for stealth options including headless, solve_cloudflare, humanize, humanize_duration, geoip, os_randomize, block_webrtc, allow_webgl, google_search, block_images, block_ads, disable_resources, network_idle, load_dom, wait_selector, wait_selector_state, timeout, proxy.

- **Session**: Represents a persistent scraping session with session_id, config, cookies, created_at, last_used, and methods fetch(), close(), is_valid().

---

## 5. Success Criteria

### Measurable Outcomes

- **SC-001**: AI agents can successfully scrape a standard URL using scrape_simple in under 30 seconds (95th percentile). Measurement: Time from tool invocation to response receipt for well-behaved websites.

- **SC-002**: The scrape_simple tool achieves 95% success rate on websites without anti-bot protection. Measurement: Success rate over 100 test URLs from public lists excluding known protected sites.

- **SC-003**: All tool responses are valid JSON and can be parsed by MCP clients without errors. Measurement: Parse all response objects with json.loads() without exceptions.

- **SC-004**: The scrape_stealth tool with maximum stealth level successfully scrapes at least 70% of websites with anti-bot protection. Measurement: Success rate on a curated list of known protected websites.

- **SC-005**: All error conditions return structured error messages containing: error type classification (invalid_url, timeout, blocked, protection_error), the URL that was attempted, HTTP status code when applicable, and actionable guidance for resolution. Measurement: 100% of errors include all four required fields; error messages rated as "helpful" by 90% of test users.

---

## 6. Assumptions

**A1**: The server will run in an environment with internet access and the ability to make outbound HTTP/HTTPS requests. Web scraping requires network connectivity.

**A2**: The environment has or can install required browser binaries (Chrome/Firefox) for browser-based scraping. The implementation will handle missing browsers gracefully.

**A3**: Public test sites (example.com, httpbin.org) will remain accessible for testing throughout development. These are industry standards.

**A4**: For batch operations, partial success is preferred over complete failure. The system should continue processing remaining URLs even if some fail.

**A5**: Users understand that stealth scraping features may violate some websites' Terms of Service. The implementation provides tools but does not actively bypass authentication or paid access controls.

**A6**: Default timeout of 30 seconds and max_retries of 3 provide good balance between reliability and responsiveness for most use cases.

---

**End of Specification**
