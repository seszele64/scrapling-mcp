<!--
  Sync Impact Report - Constitution Changes
  ==========================================
  
  Version Change: N/A → 1.0.0 (initial creation)
  
  List of Principles Established:
    I.   MCP Protocol Compliance
    II.  Stealth-First Design
    III. Security by Default
    IV.  Reliability Through Retry
    V.   Configuration Flexibility
  
  Templates Requiring Review:
    - AGENTS.md - Verify alignment with new constitutional principles
    - All tool implementations - Ensure MCP protocol compliance
    - Configuration modules - Validate against stealth-first design
    - Error handling - Confirm custom exception hierarchy usage
  
  Impact Summary:
    This initial constitution establishes the foundational principles for the MCP Scraper project.
    All future development must align with these principles.
-->

# MCP Scraper Constitution

**Project Name**: MCP Scraper (Scrapling MCP Server)

**Version**: 1.0.0  
**Ratified**: 2026-02-20  
**Last Amended**: 2026-02-20

---

## Core Principles

### I. MCP Protocol Compliance

All tools MUST follow the Model Context Protocol (MCP) standards. Tools MUST be exposed through FastMCP framework with proper type annotations. Input/output MUST be JSON-serializable for MCP protocol compatibility.

**Rationale**: The project's primary purpose is to enable AI agents to scrape web content through a standardized MCP interface.

---

### II. Stealth-First Design

Anti-detection features MUST be configurable through StealthConfig. Three preset levels MUST be available: MINIMAL, STANDARD, MAXIMUM. Default stealth level MUST be STANDARD for balanced protection. Human-like behavior simulation MUST be available for protected sites.

**Rationale**: Modern web scraping requires sophisticated anti-bot bypass capabilities.

---

### III. Security by Default

URL validation MUST be performed before any scraping operation. SSRF protection MUST block private IPs, localhost, and internal hostnames. Only HTTP/HTTPS protocols MUST be allowed. Proxy credentials MUST NOT be hardcoded in source.

**Rationale**: Security vulnerabilities in web scraping can lead to SSRF attacks and data exposure.

---

### IV. Reliability Through Retry

Exponential backoff MUST be implemented for failed requests. Maximum retries MUST be configurable (default: 3). Proxy rotation MUST be supported for block recovery. Cloudflare detection and optional solving MUST be available.

**Rationale**: Web scraping is inherently unreliable; robust retry mechanisms are essential.

---

### V. Configuration Flexibility

All stealth options MUST be individually configurable. Environment variables MUST be supported via .env files. Session management MUST allow persistent state across requests. Custom stealth profiles MUST be creatable beyond presets.

**Rationale**: Different scraping scenarios require different configurations.

---

## Section 2: Technology Standards

- Python 3.10+ required
- Type hints MUST be used for all public functions
- Async/await MUST be used for I/O operations
- Loguru MUST be used for logging
- Pydantic MUST be used for configuration validation

---

## Section 3: Quality Gates

- Code MUST pass Black formatting (100 char line length)
- Code MUST pass Ruff linting
- Code MUST pass MyPy type checking
- All public functions MUST have docstrings
- Error handling MUST use custom exception hierarchy (ScrapeError base)

---

## Governance

- Constitution supersedes all other development practices
- Amendments require documentation in Sync Impact Report
- All PRs MUST verify compliance with stealth and security principles
- Use AGENTS.md for comprehensive development guidance
