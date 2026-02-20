---

description: "Task list for MCP Server Implementation"
---

# Tasks: MCP Server Implementation

**Input**: Design documents from `/specs/001-mcp-server-implementation/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/

**Tests**: Test infrastructure (conftest.py) required for async testing support. Implementation tasks only - no test cases required.

**Organization**: Tasks are grouped by user story to enable independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Minimal setup - project already initialized

- [ ] T001 [P] Verify existing project structure in src/mcp_scraper/
- [ ] T002 [P] Verify pyproject.toml has required dependencies (FastMCP, Scrapling, Pydantic, Loguru) in pyproject.toml
- [ ] T003 [P] Create tests/ directory structure (tests/unit/, tests/integration/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create tests/conftest.py with pytest fixtures for async testing
- [ ] T005 [P] Update src/mcp_scraper/__init__.py to export server components
- [ ] T006 [P] Add any missing StealthConfig fields to src/mcp_scraper/config.py per data-model.md specifications
- [ ] T007 Implement any missing functions in src/mcp_scraper/stealth.py (scrape_with_retry, validate_url, format_response, get_session, etc.) per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simple Scraping (Priority: P1) 🎯 MVP

**Goal**: Implement scrape_simple tool for basic HTTP scraping of static content

**Independent Test**: Invoke scrape_simple on example.com and verify response contains valid HTML and text content within 15 seconds.

### Implementation for User Story 1

- [ ] T008 [US1] Create src/mcp_scraper/server.py with FastMCP server initialization
- [ ] T009 [US1] Implement scrape_simple tool in src/mcp_scraper/server.py with parameters: url, selector, extract, timeout
- [ ] T010 [US1] Add URL validation integration in scrape_simple tool
- [ ] T011 [US1] Add response formatting for scrape_simple (url, status_code, title, text, html, headers, selectors, timestamp)
- [ ] T012 [US1] Add error handling for scrape_simple (invalid URL, timeout, HTTP errors)
- [ ] T013 [US1] Add console script entry point in pyproject.toml: mcp-scraper = "mcp_scraper.server:main"

**Checkpoint**: At this point, User Story 1 should be fully functional. Test with: `mcp-scraper --transport stdio` and call scrape_simple tool.

---

## Phase 4: User Story 2 - Stealth Scraping (Priority: P2)

**Goal**: Implement scrape_stealth tool with configurable anti-detection for protected sites

**Independent Test**: Attempt to scrape a known protected site with maximum stealth level and verify successful content retrieval.

### Implementation for User Story 2

- [ ] T014 [US2] Implement scrape_stealth tool in src/mcp_scraper/server.py with parameters: url, stealth_level, solve_cloudflare, network_idle, load_dom, timeout, proxy
- [ ] T015 [US2] Add stealth level mapping (minimal/standard/maximum) to StealthConfig presets in src/mcp_scraper/server.py
- [ ] T016 [US2] Integrate scrape_with_retry() with stealth configuration in scrape_stealth in src/mcp_scraper/server.py
- [ ] T017 [US2] Add Cloudflare challenge detection and solving logic in scrape_stealth in src/mcp_scraper/server.py
- [ ] T018 [US2] Add proxy support integration in scrape_stealth tool in src/mcp_scraper/server.py
- [ ] T019 [US2] Implement scrape_session tool in src/mcp_scraper/server.py with parameters: url, session_id, cookies, stealth_level
- [ ] T020 [US2] Add session management integration (get_session, close_session) in scrape_session in src/mcp_scraper/server.py
- [ ] T021 [US2] Add cookie persistence across session requests in src/mcp_scraper/server.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Test scrape_stealth and scrape_session tools.

---

## Phase 5: User Story 3 - Batch & Structured Extraction (Priority: P3)

**Goal**: Implement extract_structured and scrape_batch tools for efficient data collection

**Independent Test**: Provide a list of 3-5 URLs to scrape_batch or selector mappings to extract_structured and verify correct aggregated/extracted results.

### Implementation for User Story 3

- [ ] T022 [US3] Implement extract_structured tool in src/mcp_scraper/server.py with parameters: url, selectors, stealth_level
- [ ] T023 [US3] Add CSS selector extraction logic supporting text, HTML, and attribute extraction (@attribute syntax) in src/mcp_scraper/server.py
- [ ] T024 [US3] Implement scrape_batch tool in src/mcp_scraper/server.py with parameters: urls, stealth_level, delay
- [ ] T025 [US3] Add sequential URL processing with configurable delay in scrape_batch in src/mcp_scraper/server.py
- [ ] T026 [US3] Add batch result aggregation (total, successful, failed counts) in scrape_batch in src/mcp_scraper/server.py
- [ ] T027 [US3] Add error handling for partial batch failures (continue processing remaining URLs) in src/mcp_scraper/server.py
- [ ] T028 [P] Add JSON serialization validation for all tool responses to ensure FR-009 compliance in src/mcp_scraper/server.py

**Checkpoint**: All user stories should now be independently functional. Test extract_structured and scrape_batch tools.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Add comprehensive docstrings to all tools following Google style in src/mcp_scraper/server.py
- [ ] T030 [P] Add input validation for all tool parameters (type checking, range validation) in src/mcp_scraper/server.py
- [ ] T031 [P] Add logging integration for all tool invocations (entry, success, error) in src/mcp_scraper/server.py
- [ ] T032 [P] Add graceful shutdown handling for browser cleanup in src/mcp_scraper/server.py
- [ ] T033 [P] Run Black formatter on all files in src/mcp_scraper/
- [ ] T034 [P] Run Ruff linter and fix any issues on all files in src/mcp_scraper/
- [ ] T035 [P] Run MyPy type checker and fix any issues on all files in src/mcp_scraper/
- [ ] T036 [P] Update quickstart.md with final usage examples in specs/001-mcp-server-implementation/quickstart.md
- [ ] T037 [P] Validate all tools work via quickstart.md examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Server initialization before tool implementation
- Tool implementation before error handling
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All Polish tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tasks together:
Task: "Create src/mcp_scraper/server.py with FastMCP server initialization"
Task: "Implement scrape_simple tool in src/mcp_scraper/server.py"
Task: "Add URL validation integration in scrape_simple tool"
Task: "Add response formatting for scrape_simple"
Task: "Add error handling for scrape_simple"
Task: "Add console script entry point in pyproject.toml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
