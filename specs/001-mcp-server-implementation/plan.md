# Implementation Plan: MCP Server Implementation

**Branch**: `001-mcp-server-implementation` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-mcp-server-implementation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement a FastMCP-based MCP server exposing five web scraping tools (scrape_simple, scrape_stealth, scrape_session, extract_structured, scrape_batch) with configurable stealth levels, URL validation, retry logic, and session management. The server enables AI agents to scrape websites with varying levels of anti-bot protection.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10+ (already configured in pyproject.toml)
**Primary Dependencies**: FastMCP (MCP framework), Scrapling (scraping engine), Pydantic (config), Loguru (logging)
**Storage**: N/A - stateless server with optional session caching in memory
**Testing**: pytest with pytest-asyncio for async test support
**Target Platform**: Linux server (primary), cross-platform Python support
**Project Type**: Single project - MCP server library with CLI entry point
**Performance Goals**: <30s response time for standard scraping (95th percentile), support concurrent tool invocations
**Constraints**: Must handle browser resource cleanup, must validate all URLs for SSRF protection, must be installable via pip
**Scale/Scope**: Single-instance MCP server, handles moderate concurrent requests (10-50 concurrent scrapes)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. MCP Protocol Compliance | Does this feature expose tools via FastMCP with proper types? | [x] Yes - all 5 tools use @mcp.tool() decorator with typed parameters |
| II. Stealth-First Design | Are stealth configurations properly defined? | [x] Yes - StealthConfig with MINIMAL/STANDARD/MAXIMUM presets |
| III. Security by Default | Is URL validation and SSRF protection in place? | [x] Yes - validate_url() blocks private IPs, localhost, internal hostnames |
| IV. Reliability Through Retry | Is retry logic with exponential backoff implemented? | [x] Yes - scrape_with_retry() with configurable retries and backoff |
| V. Configuration Flexibility | Are all options configurable via environment/parameters? | [x] Yes - Settings class with .env support and tool parameters |

**Technology Standards**: Python 3.10+, type hints, async/await, Loguru, Pydantic

**Quality Gates**: Black (100 chars), Ruff, MyPy, docstrings, custom exceptions

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/mcp_scraper/
├── __init__.py          # Package exports
├── config.py            # Settings and StealthConfig (already exists)
├── stealth.py           # Core scraping logic (already exists)
└── server.py            # NEW: FastMCP server with tool definitions

tests/
├── unit/
│   ├── test_config.py   # Settings and StealthConfig tests
│   ├── test_stealth.py  # URL validation, retry logic tests
│   └── test_server.py   # MCP tool tests
├── integration/
│   └── test_scraping.py # End-to-end scraping tests
└── conftest.py          # pytest fixtures

pyproject.toml           # Entry point: mcp-scraper = "mcp_scraper.server:main"
```

**Structure Decision**: Single project structure. The existing src/mcp_scraper/ contains config.py and stealth.py. Add server.py for FastMCP server. Tests organized in tests/unit/ and tests/integration/.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

(End of file - total 114 lines)
