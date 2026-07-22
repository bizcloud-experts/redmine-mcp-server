# Implementation Plan: Redmine MCP Server

## Overview

Implement a Python MCP server using FastMCP that wraps the Redmine REST API. The server exposes 15 tools across Issues (7), Projects (7), and Search (1) domains. The implementation follows a 3-layer architecture: FastMCP Server → Tool Handlers → RedmineClient, using httpx for HTTP communication and environment variables for configuration.

## Tasks

- [ ] 1. Set up project structure and core infrastructure
  - [x] 1.1 Create project skeleton with dependencies
    - Create `pyproject.toml` with dependencies: fastmcp, httpx, pytest, pytest-asyncio, hypothesis, respx
    - Create directory structure: `src/redmine_mcp_server/`, `tests/`
    - Create `src/redmine_mcp_server/__init__.py`
    - _Requirements: 16.1_

  - [ ] 1.2 Implement configuration and validation
    - Create `src/redmine_mcp_server/config.py`
    - Read `REDMINE_URL` and `REDMINE_API_KEY` from environment variables
    - Validate URL starts with "http://" or "https://"
    - Raise descriptive error if either variable is missing, empty, or invalid
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 1.3 Implement custom exception hierarchy
    - Create `src/redmine_mcp_server/exceptions.py`
    - Define `RedmineError` base class and subclasses: `RedmineAuthError`, `RedminePermissionError`, `RedmineNotFoundError`, `RedmineValidationError`, `RedmineConnectionError`, `RedmineTimeoutError`
    - Each exception carries status_code, message, and details where applicable
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.7, 15.8_

  - [ ] 1.4 Implement RedmineClient HTTP layer
    - Create `src/redmine_mcp_server/client.py`
    - Implement `RedmineClient` class with `get`, `post`, `put`, `delete` async methods
    - Set `X-Redmine-API-Key` header on all requests
    - Set `Content-Type: application/json` header
    - Configure httpx with 10s connect timeout, 30s read timeout
    - Implement `_handle_response` method that maps HTTP status codes to custom exceptions
    - Extract validation errors from 422 response bodies
    - Map connection errors and timeouts to appropriate exceptions
    - _Requirements: 1.6, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8_

- [ ] 2. Implement Issue tools
  - [ ] 2.1 Implement list_issues tool
    - Create `src/redmine_mcp_server/tools/issues.py`
    - Register `list_issues` tool with FastMCP decorator
    - Accept optional filters: project_id, status_id, assigned_to_id, tracker_id, sort, offset, limit
    - Default offset=0, limit=25; cap limit at 100
    - Return paginated response with total_count, offset, limit, and issues array
    - Each issue includes: id, project, tracker, status, priority, subject, updated_on
    - Return empty list with total_count=0 when no issues match
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11_

  - [ ] 2.2 Implement get_issue tool
    - Register `get_issue` tool with FastMCP decorator
    - Accept issue_id (positive integer, validated) and optional include parameter
    - Validate include values against supported set: children, attachments, relations, changesets, journals, watchers, allowed_statuses
    - Return full issue details with all required fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 2.3 Implement create_issue tool
    - Register `create_issue` tool with FastMCP decorator
    - Require project_id and subject; validate both are present and non-empty
    - Accept all optional fields: tracker_id, status_id, priority_id, description, category_id, fixed_version_id, assigned_to_id, parent_issue_id, custom_fields, watcher_user_ids, is_private, estimated_hours
    - Return created issue details including assigned ID
    - Handle and return Redmine validation errors
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 2.4 Implement update_issue tool
    - Register `update_issue` tool with FastMCP decorator
    - Accept issue_id and optional update fields including notes and private_notes
    - Include all provided fields in PUT request body
    - Return confirmation of successful update
    - Handle and return Redmine validation errors
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 2.5 Implement delete_issue tool
    - Register `delete_issue` tool with FastMCP decorator
    - Validate issue_id is a positive integer
    - Return confirmation including the deleted issue's ID
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 2.6 Implement add_watcher and remove_watcher tools
    - Register `add_watcher` tool: POST to `/issues/{id}/watchers.json`
    - Register `remove_watcher` tool: DELETE to `/issues/{id}/watchers/{user_id}.json`
    - Validate both issue_id and user_id are positive integers
    - Return confirmation of success
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 2.7 Write property tests for Issue tools
    - **Property 7: Non-Positive-Integer IDs Rejected** — Generate non-positive integers, floats, strings; verify validation error before HTTP request
    - **Property 8: Unsupported Include Values Rejected** — Generate random strings not in the supported issue include set; verify validation error
    - **Property 9: Optional Fields Included in Request Body** — Generate subsets of optional fields; verify all appear in outgoing request
    - **Validates: Requirements 3.4, 3.5, 4.2, 5.1, 5.2, 6.4**

- [ ] 3. Implement Project tools
  - [ ] 3.1 Implement list_projects tool
    - Create `src/redmine_mcp_server/tools/projects.py`
    - Register `list_projects` tool with FastMCP decorator
    - Accept optional include, offset, limit parameters
    - Default offset=0, limit=25; cap limit at 100
    - Validate include values against supported set: trackers, issue_categories, enabled_modules, time_entry_activities, issue_custom_fields
    - Return paginated response with total_count, offset, limit, and projects array
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 3.2 Implement get_project tool
    - Register `get_project` tool with FastMCP decorator
    - Accept project_id (numeric or string identifier) and optional include parameter
    - Validate include values against supported project set
    - Return full project details with all required fields: id, name, identifier, description, homepage, status, is_public, created_on, updated_on
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 3.3 Implement create_project tool
    - Register `create_project` tool with FastMCP decorator
    - Require name and identifier; validate both are present and non-empty
    - Accept all optional fields: description, homepage, is_public, parent_id, inherit_members, default_assigned_to_id, default_version_id, tracker_ids, enabled_module_names, issue_custom_field_ids, custom_field_values
    - Return created project details including assigned ID, name, identifier
    - Handle and return Redmine validation errors
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 3.4 Implement update_project tool
    - Register `update_project` tool with FastMCP decorator
    - Accept project_id (numeric or string) and optional update fields
    - Validate at least one update field is provided
    - Return updated project details on success
    - Handle and return Redmine validation errors
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ] 3.5 Implement delete_project tool
    - Register `delete_project` tool with FastMCP decorator
    - Accept project_id (numeric or string identifier)
    - Return confirmation including the deleted project's identifier
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ] 3.6 Implement archive_project and unarchive_project tools
    - Register `archive_project` tool: PUT to `/projects/{id}/archive.json`
    - Register `unarchive_project` tool: PUT to `/projects/{id}/unarchive.json`
    - Return confirmation of success
    - _Requirements: 13.1, 13.2, 13.3_

  - [ ]* 3.7 Write property tests for Project tools
    - **Property 8: Unsupported Include Values Rejected** — Generate random strings not in the supported project include set; verify validation error
    - **Property 9: Optional Fields Included in Request Body** — Generate subsets of optional project fields; verify all appear in outgoing request
    - **Property 11: Delete Confirmations Include Identifier** — Generate identifier strings; verify confirmation response includes identifier
    - **Validates: Requirements 9.4, 10.2, 11.1, 12.2**

- [ ] 4. Implement Search tool
  - [ ] 4.1 Implement search tool
    - Create `src/redmine_mcp_server/tools/search.py`
    - Register `search` tool with FastMCP decorator
    - Require query string (validate non-empty)
    - Accept optional filters: scope (all, my_project, subprojects), resource types, open_issues, offset, limit
    - Default offset=0, limit=25; cap limit at 100
    - Return paginated response with total_count, offset, limit
    - Each result includes: id, title, type, url, description, datetime
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

  - [ ]* 4.2 Write property tests for Search tool
    - **Property 3: Query Parameters Passed Through** — Generate valid filter param combinations; verify each appears in outgoing HTTP request
    - **Property 5: Paginated Responses Include Metadata** — Generate dicts with total_count/offset/limit; verify all three fields in response
    - **Validates: Requirements 14.2, 14.3, 14.5, 14.7**

- [ ] 5. Checkpoint - Verify all tools register and basic flow works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement cross-cutting concerns and server entry point
  - [ ] 6.1 Wire all tools into the FastMCP server
    - Create `src/redmine_mcp_server/server.py` as main entry point
    - Import and register all tool modules (issues, projects, search)
    - Validate configuration at startup (fail fast if env vars missing)
    - Expose `mcp` instance for FastMCP stdio transport
    - Ensure all tool names follow snake_case pattern and docstrings ≤ 200 chars
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 6.2 Implement error response formatting
    - Create consistent error response structure: `{"error": ..., "status_code": ..., "details": [...]}`
    - Ensure all tool handlers catch RedmineError exceptions and format them uniformly
    - Ensure FastMCP propagates errors with `isError: true` flag
    - _Requirements: 15.7, 15.8, 16.4_

  - [ ]* 6.3 Write property tests for core infrastructure
    - **Property 1: URL Validation Rejects Invalid Schemes** — Generate strings with/without http(s):// prefix; verify accept/reject behavior
    - **Property 2: API Key Header Always Present** — Generate arbitrary API key strings; verify X-Redmine-API-Key header on all requests
    - **Property 4: Pagination Limit Capped at 100** — Generate integers 0-10000; verify effective limit is min(value, 100)
    - **Property 10: Redmine Validation Errors Extracted** — Generate error message lists; verify all extracted from 422 response
    - **Property 12: All Error Responses Include HTTP Status Code** — Generate 4xx/5xx codes; verify status_code present in error response
    - **Property 13: Tool Naming Convention** — Introspect registered tools; verify snake_case regex and docstring ≤ 200 chars
    - **Validates: Requirements 1.5, 1.6, 2.7, 8.2, 14.5, 4.5, 5.5, 10.5, 11.4, 15.4, 15.7, 15.8, 16.5**

- [ ] 7. Write unit tests for key behaviors
  - [ ]* 7.1 Write unit tests for configuration and client
    - Test missing/empty REDMINE_URL raises error with variable name
    - Test missing/empty REDMINE_API_KEY raises error with variable name
    - Test invalid URL scheme raises validation error
    - Test valid config initializes without error
    - Test HTTP error mapping: 401→auth, 403→permission, 404→not found, 422→validation
    - Test connection error and timeout handling
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 15.1, 15.2, 15.3, 15.5, 15.6_

  - [ ]* 7.2 Write unit tests for issue tools
    - Test list_issues with default pagination (offset=0, limit=25)
    - Test list_issues with filters passed through as query params
    - Test get_issue returns all required detail fields
    - Test create_issue validates required fields (project_id, subject)
    - Test update_issue with notes adds journal entry
    - Test delete_issue returns confirmation with ID
    - Test watcher add/remove use correct HTTP paths
    - _Requirements: 2.1, 2.9, 3.1, 4.4, 5.3, 6.2, 7.1, 7.2_

  - [ ]* 7.3 Write unit tests for project and search tools
    - Test list_projects with default pagination
    - Test get_project returns all required detail fields
    - Test create_project validates name and identifier required
    - Test update_project rejects empty update fields
    - Test delete_project returns confirmation with identifier
    - Test archive/unarchive use correct PUT paths
    - Test search validates non-empty query string
    - Test search returns results with required fields
    - _Requirements: 8.1, 9.1, 10.4, 11.5, 12.2, 13.1, 13.2, 14.6, 14.8_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design's 13 properties
- Unit tests validate specific examples and edge cases
- The design specifies Python explicitly — all code uses Python with FastMCP, httpx, and hypothesis
- `respx` or `pytest-httpx` should be used for mocking HTTP requests in tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4"] },
    { "id": 3, "tasks": ["2.1", "3.1", "4.1"] },
    { "id": 4, "tasks": ["2.2", "2.3", "3.2", "3.3"] },
    { "id": 5, "tasks": ["2.4", "2.5", "2.6", "3.4", "3.5", "3.6"] },
    { "id": 6, "tasks": ["2.7", "3.7", "4.2"] },
    { "id": 7, "tasks": ["6.1"] },
    { "id": 8, "tasks": ["6.2"] },
    { "id": 9, "tasks": ["6.3", "7.1", "7.2", "7.3"] }
  ]
}
```
