# Phase 0: Research & Technology Decisions

**Feature**: MCP Server Implementation  
**Date**: 2026-02-20  
**Status**: Complete

## Technology Stack Decisions

### MCP Framework: FastMCP

**Decision**: Use FastMCP (v2.0+) as the MCP server framework

**Rationale**:
- FastMCP is the modern, officially recommended Python framework for MCP servers
- Provides simple @mcp.tool() decorator for exposing functions as MCP tools
- Automatic type conversion between Python and JSON
- Built-in async support for concurrent operations
- Native integration with Pydantic for type validation

**Alternatives Considered**:
- Raw MCP SDK: More verbose, requires manual protocol handling
- Other frameworks: FastMCP is the standard for Python MCP servers

### Scraping Engine: Scrapling

**Decision**: Use Scrapling library (already in project)

**Rationale**:
- Scrapling provides AsyncStealthySession with built-in anti-detection
- Supports multiple fetcher types (Fetcher, StealthyFetcher, AsyncStealthySession)
- Already integrated in existing stealth.py module
- 9.1k GitHub stars, actively maintained

**Key Components**:
- Fetcher: Fast HTTP with TLS fingerprinting
- StealthyFetcher: Browser automation with anti-bot bypass
- AsyncStealthySession: Concurrent stealth browsing with tab pooling

### Configuration: Pydantic + pydantic-settings

**Decision**: Use Pydantic v2 with pydantic-settings for configuration

**Rationale**:
- Type-safe configuration with validation
- Automatic .env file loading
- Environment variable mapping
- Already used in existing config.py

### Logging: Loguru

**Decision**: Use Loguru for structured logging

**Rationale**:
- Modern Python logging with structured output
- Better async support than standard logging
- Already used in existing stealth.py
- Required by Constitution (Technology Standards)

## Architecture Patterns

### MCP Tool Design Pattern

Each scraping tool follows this pattern:
1. Accept typed parameters (url, optional configs)
2. Validate URL using validate_url()
3. Apply level
4. Execute scraping with retry stealth configuration based on logic
5. Return JSON-serializable response

### Error Handling Strategy

Custom exception hierarchy:
- ScrapeError (base)
  - CloudflareError (protection detected)
  - BlockedError (anti-bot blocked)
  - TimeoutError (request timeout)

All exceptions caught and converted to error responses with descriptive messages.

### Session Management

Global session cache pattern:
- Keyed by session_id for persistence
- Config-aware recreation when settings change
- Proper cleanup on close
- Cookie persistence across requests

## Best Practices Identified

1. **URL Validation**: Must occur before ANY network request
2. **Resource Cleanup**: Browser instances must be properly closed
3. **Async/Await**: All I/O operations must be async
4. **Type Hints**: All public functions must have complete type annotations
5. **JSON Serialization**: All responses must be JSON-serializable for MCP protocol

## Open Questions Resolved

None - all technical decisions were clear from existing codebase and constitution.
