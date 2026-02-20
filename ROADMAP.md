# Scrapling MCP Server - Project Roadmap

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Phases](#2-project-phases)
3. [Detailed Tasks](#3-detailed-tasks)
4. [Milestones](#4-milestones)
5. [Timeline Estimates](#5-timeline-estimates)
6. [Risk Assessment](#6-risk-assessment)
7. [Next Actions](#7-next-actions)

---

## 1. Project Overview

### Project Vision

Build a production-ready MCP (Model Context Protocol) server for web scraping using the Scrapling library with FastMCP framework. The server enables AI agents to perform stealth web scraping with configurable anti-detection features, JavaScript rendering, and structured data extraction.

### Current Status

| Component | Status | Location |
|-----------|--------|----------|
| Core Logic | Complete | `src/mcp_scraper/` |
| Configuration | Complete | `pyproject.toml`, `.env.example` |
| Documentation | Complete | `AGENTS.md`, `VDD.md`, `docs/` |
| MCP Server | Not Started | `server.py` (to be created) |
| Tests | Not Started | `tests/` (to be created) |
| CI/CD | Not Started | `.github/workflows/` (to be created) |

### Key Dependencies

- **FastMCP** (>=2.0) - MCP server framework
- **Scrapling** (with all extras) - Adaptive web scraping framework
- **Pydantic** (>=2.0) - Data validation
- **Loguru** (>=0.7) - Logging

---

## 2. Project Phases

### Phase 1: Foundation (COMPLETED)

**Objective:** Establish core scraping infrastructure and documentation.

**Deliverables:**
- Core scraping logic (`src/mcp_scraper/stealth.py`)
- Configuration system (`src/mcp_scraper/config.py`)
- Package initialization (`src/mcp_scraper/__init__.py`)
- Project documentation (`AGENTS.md`)
- Development guide (`VDD.md`)
- Research documentation (`docs/research/scrapling.md`)
- Project configuration (`pyproject.toml`, `.env.example`, `.gitignore`)

### Phase 2: MCP Server Implementation (CURRENT PHASE)

**Objective:** Build the MCP server with tool definitions and entry point.

**Deliverables:**
- `server.py` - FastMCP server implementation
- MCP tools: `scrape_simple`, `scrape_stealth`, `scrape_session`, `extract_structured`, `scrape_batch`
- Console script entry point
- Basic error handling

### Phase 3: Testing & Quality

**Objective:** Establish comprehensive test coverage and code quality standards.

**Deliverables:**
- Unit tests for core modules
- Integration tests for MCP tools
- Security tests for URL validation
- Code linting and formatting configuration
- Type checking configuration

### Phase 4: Documentation & Examples

**Objective:** Create user-facing documentation and usage examples.

**Deliverables:**
- `README.md` - Project overview and quick start
- API documentation
- Usage examples
- Configuration guide

### Phase 5: Release & Deployment

**Objective:** Prepare for production release and community distribution.

**Deliverables:**
- GitHub Actions CI/CD workflow
- Release process documentation
- Version management
- Package publishing setup

---

## 3. Detailed Tasks

### Phase 2: MCP Server Implementation

#### Task 2.1: Create Server Entry Point

- **Description:** Create `server.py` with FastMCP server initialization and basic structure
- **Priority:** Critical
- **Dependencies:** None
- **Verification Criteria:**
  - Server starts without errors
  - MCP protocol handshake works
  - Basic logging is functional

#### Task 2.2: Implement scrape_simple Tool

- **Description:** Create `scrape_simple` MCP tool for basic HTTP scraping without stealth features
- **Priority:** Critical
- **Dependencies:** Task 2.1
- **Verification Criteria:**
  - Tool accepts URL and optional timeout parameters
  - Returns HTML content, text content, and status code
  - URL validation is enforced
  - Error handling returns meaningful messages

#### Task 2.3: Implement scrape_stealth Tool

- **Description:** Create `scrape_stealth` MCP tool with configurable stealth levels
- **Priority:** Critical
- **Dependencies:** Task 2.1
- **Verification Criteria:**
  - Tool accepts stealth_level parameter (minimal/standard/maximum)
  - Supports solve_cloudflare, network_idle, load_dom options
  - Returns full page content with metadata
  - Session management works correctly

#### Task 2.4: Implement scrape_session Tool

- **Description:** Create `scrape_session` MCP tool for session-based scraping
- **Priority:** High
- **Dependencies:** Task 2.3
- **Verification Criteria:**
  - Supports session_id for session persistence
  - Accepts initial cookies
  - Maintains state across multiple requests
  - Proper session cleanup on errors

#### Task 2.5: Implement extract_structured Tool

- **Description:** Create `extract_structured` MCP tool for CSS selector-based extraction
- **Priority:** High
- **Dependencies:** Task 2.1
- **Verification Criteria:**
  - Accepts selectors dictionary (name -> CSS selector)
  - Returns extracted data as structured dictionary
  - Handles missing elements gracefully
  - Supports attribute extraction (e.g., `@href`)

#### Task 2.6: Implement scrape_batch Tool

- **Description:** Create `scrape_batch` MCP tool for processing multiple URLs
- **Priority:** Medium
- **Dependencies:** Task 2.3
- **Verification Criteria:**
  - Accepts array of URLs
  - Configurable delay between requests
  - Returns results for all URLs
  - Handles partial failures gracefully

#### Task 2.7: Add Console Script Entry Point

- **Description:** Configure console script in pyproject.toml to run the server
- **Priority:** High
- **Dependencies:** Task 2.1
- **Verification Criteria:**
  - `mcp-scraper` command starts the server
  - Server listens on stdio by default (MCP standard)
  - Supports `--help` flag
  - Environment variables are loaded correctly

#### Task 2.8: Implement MCP Resources

- **Description:** Add MCP resources for configuration and status
- **Priority:** Medium
- **Dependencies:** Task 2.1
- **Verification Criteria:**
  - Resource for current stealth profiles
  - Resource for server status
  - Resources are discoverable by MCP clients

---

### Phase 3: Testing & Quality

#### Task 3.1: Set Up Test Infrastructure

- **Description:** Create test directory structure and configuration
- **Priority:** Critical
- **Dependencies:** Phase 2 completion
- **Verification Criteria:**
  - `tests/` directory created with proper structure
  - pytest configuration works
  - Test discovery finds all tests
  - Async tests run correctly

#### Task 3.2: Write Unit Tests for config.py

- **Description:** Test configuration classes and settings
- **Priority:** High
- **Dependencies:** Task 3.1
- **Verification Criteria:**
  - StealthConfig dataclass tests
  - Settings loading from environment
  - StealthProfiles presets tests
  - Edge cases covered

#### Task 3.3: Write Unit Tests for stealth.py

- **Description:** Test core scraping functions and utilities
- **Priority:** High
- **Dependencies:** Task 3.1
- **Verification Criteria:**
  - URL validation tests (positive and negative cases)
  - Response formatting tests
  - Proxy rotation tests
  - Error detection tests (Cloudflare, blocked)

#### Task 3.4: Write Integration Tests for MCP Tools

- **Description:** Test MCP tools end-to-end with mock servers
- **Priority:** High
- **Dependencies:** Task 3.1, Tasks 2.2-2.6
- **Verification Criteria:**
  - Each tool has at least one integration test
  - Tests verify correct response format
  - Error handling is tested
  - Tool parameters are validated

#### Task 3.5: Write Security Tests

- **Description:** Test URL validation and SSRF protection
- **Priority:** Critical
- **Dependencies:** Task 3.3
- **Verification Criteria:**
  - Private IP addresses are blocked
  - Localhost variants are blocked
  - Internal hostnames are blocked
  - Invalid protocols are rejected

#### Task 3.6: Configure Pre-commit Hooks

- **Description:** Set up pre-commit configuration for code quality
- **Priority:** Medium
- **Dependencies:** Task 3.1
- **Verification Criteria:**
  - Black formatting on commit
  - Ruff linting on commit
  - MyPy type checking on commit
  - All checks pass locally

---

### Phase 4: Documentation & Examples

#### Task 4.1: Create README.md

- **Description:** Write project README with installation and quick start
- **Priority:** Critical
- **Dependencies:** Phase 2 completion
- **Verification Criteria:**
  - Installation instructions
  - Quick start guide
  - Environment configuration
  - Basic usage examples

#### Task 4.2: Create API Documentation

- **Description:** Document all MCP tools and their parameters
- **Priority:** High
- **Dependencies:** Phase 2 completion
- **Verification Criteria:**
  - All tools documented with parameters
  - Return types documented
  - Error cases documented
  - Examples provided

#### Task 4.3: Create Usage Examples

- **Description:** Add comprehensive usage examples to documentation
- **Priority:** Medium
- **Dependencies:** Task 4.1
- **Verification Criteria:**
  - Basic scraping example
  - Stealth scraping example
  - Structured extraction example
  - Batch scraping example
  - Custom configuration example

#### Task 4.4: Create Configuration Guide

- **Description:** Document all configuration options
- **Priority:** Medium
- **Dependencies:** Task 4.1
- **Verification Criteria:**
  - Environment variables documented
  - Stealth levels explained
  - Proxy configuration explained
  - Timeout settings explained

---

### Phase 5: Release & Deployment

#### Task 5.1: Set Up GitHub Actions CI

- **Description:** Create CI workflow for automated testing
- **Priority:** Critical
- **Dependencies:** Phase 3 completion
- **Verification Criteria:**
  - Runs on push and pull requests
  - Tests against multiple Python versions
  - Runs linting and type checking
  - Reports coverage

#### Task 5.2: Set Up Release Workflow

- **Description:** Create release workflow for publishing to PyPI
- **Priority:** High
- **Dependencies:** Task 5.1
- **Verification Criteria:**
  - Semantic versioning
  - Changelog generation
  - PyPI publication
  - GitHub release creation

#### Task 5.3: Set Up Pre-release Checks

- **Description:** Create pre-release checklist and validation
- **Priority:** Medium
- **Dependencies:** Task 5.1
- **Verification Criteria:**
  - All tests pass
  - Type checking passes
  - Documentation builds successfully
  - Package installs correctly

#### Task 5.4: Version Bump to 1.0.0

- **Description:** Bump version to stable release
- **Priority:** High
- **Dependencies:** Task 5.2
- **Verification Criteria:**
  - Version is 1.0.0
  - All features from roadmap implemented
  - Documentation complete
  - First stable release published

---

## 4. Milestones

### Milestone M1: MCP Server Alpha

**Target:** End of Phase 2

**Deliverables:**
- [ ] Server starts successfully
- [ ] At least 3 MCP tools implemented
- [ ] Basic error handling works
- [ ] Entry point configured

**Success Criteria:**
- Server can be started with `mcp-scraper` command
- At least `scrape_simple`, `scrape_stealth`, `extract_structured` tools work
- Tools return expected response format

### Milestone M2: Test Coverage Complete

**Target:** End of Phase 3

**Deliverables:**
- [ ] Unit tests for all core modules
- [ ] Integration tests for all MCP tools
- [ ] Security tests for URL validation
- [ ] Pre-commit hooks configured

**Success Criteria:**
- Minimum 80% code coverage
- All critical paths tested
- Security tests pass
- Code passes linting and type checking

### Milestone M3: Documentation Complete

**Target:** End of Phase 4

**Deliverables:**
- [ ] README.md with quick start
- [ ] API documentation
- [ ] Usage examples
- [ ] Configuration guide

**Success Criteria:**
- New users can install and run the server
- All tools have documentation
- Examples are tested and work correctly

### Milestone M4: First Stable Release

**Target:** End of Phase 5

**Deliverables:**
- [ ] CI/CD workflow configured
- [ ] Release workflow configured
- [ ] Package published to PyPI
- [ ] Version 1.0.0 released

**Success Criteria:**
- Automated CI passes
- Release can be published with single command
- Package installs correctly from PyPI

---

## 5. Timeline Estimates

### Phase 2: MCP Server Implementation

| Task | Estimate | Dependencies |
|------|----------|--------------|
| Task 2.1: Server Entry Point | 2 hours | None |
| Task 2.2: scrape_simple Tool | 3 hours | 2.1 |
| Task 2.3: scrape_stealth Tool | 4 hours | 2.1 |
| Task 2.4: scrape_session Tool | 3 hours | 2.3 |
| Task 2.5: extract_structured Tool | 3 hours | 2.1 |
| Task 2.6: scrape_batch Tool | 2 hours | 2.3 |
| Task 2.7: Console Entry Point | 1 hour | 2.1 |
| Task 2.8: MCP Resources | 2 hours | 2.1 |

**Phase 2 Total:** ~20 hours

### Phase 3: Testing & Quality

| Task | Estimate | Dependencies |
|------|----------|--------------|
| Task 3.1: Test Infrastructure | 2 hours | Phase 2 |
| Task 3.2: config.py Tests | 3 hours | 3.1 |
| Task 3.3: stealth.py Tests | 4 hours | 3.1 |
| Task 3.4: MCP Tool Tests | 6 hours | 3.1, Phase 2 |
| Task 3.5: Security Tests | 3 hours | 3.3 |
| Task 3.6: Pre-commit Hooks | 1 hour | 3.1 |

**Phase 3 Total:** ~19 hours

### Phase 4: Documentation & Examples

| Task | Estimate | Dependencies |
|------|----------|--------------|
| Task 4.1: README.md | 3 hours | Phase 2 |
| Task 4.2: API Documentation | 4 hours | Phase 2 |
| Task 4.3: Usage Examples | 3 hours | 4.1 |
| Task 4.4: Configuration Guide | 2 hours | 4.1 |

**Phase 4 Total:** ~12 hours

### Phase 5: Release & Deployment

| Task | Estimate | Dependencies |
|------|----------|--------------|
| Task 5.1: GitHub Actions CI | 4 hours | Phase 3 |
| Task 5.2: Release Workflow | 3 hours | 5.1 |
| Task 5.3: Pre-release Checks | 2 hours | 5.1 |
| Task 5.4: Version Bump | 1 hour | 5.2 |

**Phase 5 Total:** ~10 hours

### Total Timeline

| Phase | Estimated Hours |
|-------|-----------------|
| Phase 1: Foundation | Completed |
| Phase 2: MCP Server | 20 hours |
| Phase 3: Testing | 19 hours |
| Phase 4: Documentation | 12 hours |
| Phase 5: Release | 10 hours |
| **Total** | **~61 hours** |

### Critical Path

The critical path for the project is:

1. **Phase 2: MCP Server Implementation** (20 hours)
   - Task 2.1 → Task 2.2 → Task 2.3 → Task 2.4
   - Must complete before testing can fully begin

2. **Phase 3: Testing** (19 hours)
   - Task 3.1 → Task 3.3 → Task 3.4
   - Depends on Phase 2 completion

3. **Phase 5: Release** (10 hours)
   - Task 5.1 → Task 5.2 → Task 5.4
   - Depends on Phase 3 completion

---

## 6. Risk Assessment

### Risk 1: Scrapling Library Compatibility

**Description:** The scrapling library may have API changes or breaking updates that affect the implementation.

**Likelihood:** Medium

**Impact:** High - Could require significant refactoring

**Mitigation:**
- Pin to specific version in pyproject.toml
- Create abstraction layer for scrapling calls
- Test with beta versions before upgrading

### Risk 2: FastMCP API Changes

**Description:** FastMCP is a relatively new framework and may have breaking changes.

**Likelihood:** Low

**Impact:** Medium - Tool definitions may need updates

**Mitigation:**
- Pin FastMCP version (>=2.0)
- Monitor FastMCP releases and changelog
- Test with latest stable version

### Risk 3: Browser Automation Dependencies

**Description:** Camoufox/Playwright dependencies may not install correctly on all platforms.

**Likelihood:** Medium

**Impact:** High - Stealth features may not work

**Mitigation:**
- Use `scrapling[all]` to include all extras
- Document system dependencies
- Provide fallback to simple HTTP mode

### Risk 4: SSRF Validation Bypass

**Description:** URL validation may have edge cases that allow SSRF attacks.

**Likelihood:** Low

**Impact:** Critical - Security vulnerability

**Mitigation:**
- Extensive security testing (Task 3.5)
- Use Python's urlparse for validation
- Block known dangerous patterns
- Regular security audits

### Risk 5: Cloudflare Challenge Handling

**Description:** Cloudflare may change their challenge mechanism, breaking solve_cloudflare feature.

**Likelihood:** Medium

**Impact:** Medium - Feature may stop working

**Mitigation:**
- Make Cloudflare solving optional (disabled by default)
- Log warnings when challenges are detected
- Provide manual fallback options

### Risk 6: Test Environment Limitations

**Description:** Running full browser automation tests in CI may be slow or resource-constrained.

**Likelihood:** High

**Impact:** Medium - Test execution time

**Mitigation:**
- Use pytest markers to separate slow tests
- Mock external dependencies where possible
- Use lightweight browser options for testing

---

## 7. Next Actions

### Immediate Priority (This Week)

1. **Start Task 2.1: Create Server Entry Point**
   - Create `server.py` with FastMCP initialization
   - Set up basic logging
   - Verify server starts correctly

2. **Start Task 2.2: Implement scrape_simple Tool**
   - Connect to core scraping logic
   - Add URL validation
   - Define tool parameters and return type

### Short-term (Next 2 Weeks)

3. **Complete Task 2.3-2.6: Implement Remaining Tools**
   - scrape_stealth with stealth levels
   - scrape_session with state management
   - extract_structured with CSS selectors
   - scrape_batch for multiple URLs

4. **Complete Task 2.7: Console Entry Point**
   - Configure pyproject.toml scripts
   - Test command-line execution

### Medium-term (This Month)

5. **Start Phase 3: Testing & Quality**
   - Set up test infrastructure
   - Write unit tests for core modules
   - Implement security tests

6. **Start Phase 4: Documentation**
   - Create README.md
   - Document all tools and parameters

### Long-term (This Quarter)

7. **Complete Phase 5: Release & Deployment**
   - Set up CI/CD workflows
   - Create release process
   - Publish first stable version

---

## Appendix A: Verification References

This roadmap references the Verification-Driven Development (VDD) approach documented in `VDD.md`. Each task's verification criteria should be implemented as test cases following the VDD methodology.

Key verification principles:
1. Define verification criteria **before** implementation
2. Write tests that verify success conditions
3. Self-verify with automated tests
4. Iterate until verification passes

## Appendix B: Related Documentation

- `AGENTS.md` - Comprehensive project documentation
- `VDD.md` - Verification-Driven Development guide
- `docs/research/scrapling.md` - Scrapling library research

---

*Last Updated: 2026-02-20*
*Version: 0.1.0*
