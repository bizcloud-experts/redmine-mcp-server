# Requirements Document

## Introduction

This document defines the requirements for a Model Context Protocol (MCP) server that wraps the Redmine REST API. The server enables AI agents (Kiro, Claude, and other MCP-compatible tools) to interact with Redmine instances for issue tracking, project management, and search operations. The initial scope covers Issues, Projects, and Search API areas.

## Glossary

- **MCP_Server**: The Model Context Protocol server application that exposes Redmine operations as MCP tools
- **Redmine_Instance**: The target Redmine installation accessed via its REST API
- **AI_Agent**: Any MCP-compatible client (Kiro, Claude, etc.) that connects to the MCP_Server
- **Tool**: An MCP tool definition that maps to one or more Redmine API operations
- **API_Key**: A Redmine-issued authentication token used to authorize requests
- **Pagination**: The mechanism for retrieving large result sets in smaller chunks using offset and limit parameters

## Requirements

### Requirement 1: Server Configuration

**User Story:** As a developer, I want to configure the MCP server with my Redmine instance URL and API key, so that the server can authenticate and communicate with my Redmine installation.

#### Acceptance Criteria

1. WHEN the MCP_Server starts, THE MCP_Server SHALL read the Redmine instance URL from the REDMINE_URL environment variable
2. WHEN the MCP_Server starts, THE MCP_Server SHALL read the API_Key from the REDMINE_API_KEY environment variable
3. IF the REDMINE_URL environment variable is missing or empty, THEN THE MCP_Server SHALL log an error message identifying "REDMINE_URL" as the missing variable and fail to start
4. IF the REDMINE_API_KEY environment variable is missing or empty, THEN THE MCP_Server SHALL log an error message identifying "REDMINE_API_KEY" as the missing variable and fail to start
5. IF the REDMINE_URL value does not start with "http://" or "https://", THEN THE MCP_Server SHALL return a validation error indicating the URL format is invalid
6. THE MCP_Server SHALL authenticate all requests to the Redmine_Instance using the X-Redmine-API-Key HTTP header with the configured API_Key value

### Requirement 2: List Issues

**User Story:** As an AI agent, I want to list and filter issues from Redmine, so that I can help users find relevant issues based on various criteria.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the list-issues Tool without filter parameters, THE MCP_Server SHALL return a paginated list of issues from the Redmine_Instance with a default limit of 25 and offset of 0
2. WHEN the AI_Agent provides a project_id filter, THE MCP_Server SHALL return only issues belonging to that project
3. WHEN the AI_Agent provides a status_id filter, THE MCP_Server SHALL return only issues matching that status (open, closed, all, or a specific numeric status ID)
4. WHEN the AI_Agent provides an assigned_to_id filter, THE MCP_Server SHALL return only issues assigned to that user
5. WHEN the AI_Agent provides a tracker_id filter, THE MCP_Server SHALL return only issues of that tracker type
6. WHEN the AI_Agent provides sort parameters, THE MCP_Server SHALL return issues sorted by the specified column and direction (asc or desc)
7. WHEN the AI_Agent provides offset and limit parameters, THE MCP_Server SHALL return the corresponding page of results with limit capped at a maximum of 100
8. THE MCP_Server SHALL include total_count, offset, and limit in the list-issues response
9. THE MCP_Server SHALL return each issue in the list with at minimum: id, project, tracker, status, priority, subject, and updated_on fields
10. IF the AI_Agent provides an invalid filter value or a reference to a non-existent resource in a filter, THEN THE MCP_Server SHALL return an error indicating which filter parameter was invalid
11. WHEN the list-issues query matches zero issues, THE MCP_Server SHALL return an empty issues list with total_count of 0

### Requirement 3: Get Issue Details

**User Story:** As an AI agent, I want to retrieve detailed information about a specific issue, so that I can provide comprehensive context about that issue to the user.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the get-issue Tool with an issue ID (positive integer), THE MCP_Server SHALL return the issue details including at minimum: id, project, tracker, status, priority, author, subject, description, start_date, due_date, done_ratio, estimated_hours, spent_hours, created_on, updated_on, and closed_on fields
2. WHEN the AI_Agent specifies include parameters, THE MCP_Server SHALL return the issue with the requested associated data (children, attachments, relations, changesets, journals, watchers, allowed_statuses)
3. IF the specified issue does not exist, THEN THE MCP_Server SHALL return an error indicating the issue was not found
4. IF the AI_Agent provides an issue ID that is not a positive integer, THEN THE MCP_Server SHALL return a validation error indicating the issue ID format is invalid
5. IF the AI_Agent specifies an include parameter value not in the supported set (children, attachments, relations, changesets, journals, watchers, allowed_statuses), THEN THE MCP_Server SHALL return a validation error indicating the unsupported include value

### Requirement 4: Create Issue

**User Story:** As an AI agent, I want to create new issues in Redmine, so that I can help users quickly log bugs, tasks, and feature requests.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the create-issue Tool with a project_id and subject, THE MCP_Server SHALL create a new issue in the Redmine_Instance
2. WHEN the AI_Agent provides optional fields (tracker_id, status_id, priority_id, description, category_id, fixed_version_id, assigned_to_id, parent_issue_id, custom_fields, watcher_user_ids, is_private, estimated_hours), THE MCP_Server SHALL include those fields in the created issue
3. WHEN the issue is created successfully, THE MCP_Server SHALL return the created issue details including at minimum the assigned ID, project, subject, tracker, status, and priority fields
4. IF the project_id is missing or the subject is missing or the subject is empty, THEN THE MCP_Server SHALL return a validation error listing the missing or invalid fields
5. IF the Redmine_Instance returns validation errors, THEN THE MCP_Server SHALL return each validation error message from the response as a structured list
6. IF the specified project_id does not exist or is not accessible, THEN THE MCP_Server SHALL return an error indicating the project was not found

### Requirement 5: Update Issue

**User Story:** As an AI agent, I want to update existing issues in Redmine, so that I can help users modify issue attributes and add notes.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the update-issue Tool with an issue ID and update fields, THE MCP_Server SHALL update the specified issue in the Redmine_Instance and return a confirmation that the issue was updated successfully
2. WHEN the AI_Agent provides optional update fields (subject, tracker_id, status_id, priority_id, description, category_id, fixed_version_id, assigned_to_id, parent_issue_id, custom_fields, is_private, estimated_hours, notes, private_notes), THE MCP_Server SHALL include those fields in the update request
3. WHEN the AI_Agent provides notes in the update, THE MCP_Server SHALL add those notes as a journal entry on the issue
4. IF the specified issue does not exist, THEN THE MCP_Server SHALL return an error indicating the issue was not found
5. IF the Redmine_Instance returns validation errors, THEN THE MCP_Server SHALL return those errors as an array of validation error messages extracted from the Redmine response

### Requirement 6: Delete Issue

**User Story:** As an AI agent, I want to delete issues from Redmine, so that I can help users remove issues that were created in error.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the delete-issue Tool with a valid issue ID (positive integer), THE MCP_Server SHALL send a delete request for that issue to the Redmine_Instance
2. WHEN the Redmine_Instance successfully deletes the issue, THE MCP_Server SHALL return a confirmation response that includes the deleted issue's ID
3. IF the specified issue does not exist, THEN THE MCP_Server SHALL return an error indicating the issue was not found
4. IF the AI_Agent provides an issue ID that is not a positive integer, THEN THE MCP_Server SHALL return a validation error indicating the issue ID is invalid

### Requirement 7: Manage Issue Watchers

**User Story:** As an AI agent, I want to add and remove watchers on issues, so that I can help users manage notification subscriptions for issues.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the add-watcher Tool with an issue ID and user ID, THE MCP_Server SHALL add that user as a watcher on the issue and return a confirmation of success
2. WHEN the AI_Agent invokes the remove-watcher Tool with an issue ID and user ID, THE MCP_Server SHALL remove that user from the watchers of the issue and return a confirmation of success
3. IF the specified issue does not exist, THEN THE MCP_Server SHALL return an error indicating the issue was not found
4. IF the specified user ID does not exist, THEN THE MCP_Server SHALL return an error indicating the user was not found

### Requirement 8: List Projects

**User Story:** As an AI agent, I want to list projects from Redmine, so that I can help users discover and navigate available projects.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the list-projects Tool, THE MCP_Server SHALL return a paginated list of accessible projects from the Redmine_Instance with a default limit of 25 and offset of 0
2. WHEN the AI_Agent provides offset and limit parameters, THE MCP_Server SHALL return the corresponding page of results with limit capped at a maximum of 100
3. WHEN the AI_Agent specifies include parameters, THE MCP_Server SHALL return projects with the requested associated data (trackers, issue_categories, enabled_modules, time_entry_activities, issue_custom_fields)
4. THE MCP_Server SHALL include total_count, offset, and limit in the list-projects response

### Requirement 9: Get Project Details

**User Story:** As an AI agent, I want to retrieve detailed information about a specific project, so that I can provide comprehensive context about that project.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the get-project Tool with a project ID (numeric) or identifier (string slug), THE MCP_Server SHALL return the project details including at minimum: id, name, identifier, description, homepage, status, is_public, created_on, and updated_on fields
2. WHEN the AI_Agent specifies include parameters, THE MCP_Server SHALL return the project with the requested associated data (trackers, issue_categories, enabled_modules, time_entry_activities, issue_custom_fields)
3. IF the specified project does not exist, THEN THE MCP_Server SHALL return an error indicating the project was not found
4. IF the AI_Agent provides an invalid include parameter value not in the supported set (trackers, issue_categories, enabled_modules, time_entry_activities, issue_custom_fields), THEN THE MCP_Server SHALL return a validation error listing the supported include values

### Requirement 10: Create Project

**User Story:** As an AI agent, I want to create new projects in Redmine, so that I can help users set up project structures.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the create-project Tool with a name and identifier, THE MCP_Server SHALL create a new project in the Redmine_Instance
2. WHEN the AI_Agent provides optional fields (description, homepage, is_public, parent_id, inherit_members, default_assigned_to_id, default_version_id, tracker_ids, enabled_module_names, issue_custom_field_ids, custom_field_values), THE MCP_Server SHALL include those fields in the created project
3. WHEN the project is created successfully, THE MCP_Server SHALL return the created project details including at minimum the assigned ID, name, and identifier fields
4. IF the name is missing or the identifier is missing or the identifier is empty, THEN THE MCP_Server SHALL return a validation error listing the missing or invalid fields
5. IF the Redmine_Instance returns validation errors (e.g., duplicate identifier), THEN THE MCP_Server SHALL return each validation error message from the response as a structured list

### Requirement 11: Update Project

**User Story:** As an AI agent, I want to update existing projects in Redmine, so that I can help users modify project settings.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the update-project Tool with a project ID or identifier and one or more update fields (name, description, homepage, is_public, parent_id, inherit_members, default_assigned_to_id, default_version_id, tracker_ids, enabled_module_names, issue_custom_field_ids, custom_field_values), THE MCP_Server SHALL update the specified project in the Redmine_Instance
2. WHEN the project is updated successfully, THE MCP_Server SHALL return the updated project details
3. IF the specified project does not exist, THEN THE MCP_Server SHALL return an error indicating the project was not found
4. IF the Redmine_Instance returns validation errors, THEN THE MCP_Server SHALL return those errors in a structured format that includes each field-level error message
5. IF the AI_Agent invokes the update-project Tool without providing any update fields, THEN THE MCP_Server SHALL return a validation error indicating that at least one update field is required

### Requirement 12: Delete Project

**User Story:** As an AI agent, I want to delete projects from Redmine, so that I can help users remove projects that are no longer needed.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the delete-project Tool with a project ID or string identifier, THE MCP_Server SHALL delete that project from the Redmine_Instance
2. WHEN the project is deleted successfully, THE MCP_Server SHALL return a confirmation including the identifier of the deleted project
3. IF the specified project does not exist, THEN THE MCP_Server SHALL return an error indicating the project was not found
4. IF the Redmine_Instance returns validation errors when attempting to delete the project, THEN THE MCP_Server SHALL return those errors in a readable format

### Requirement 13: Archive and Unarchive Project

**User Story:** As an AI agent, I want to archive and unarchive projects, so that I can help users manage project lifecycle without permanent deletion.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the archive-project Tool with a project ID, THE MCP_Server SHALL archive that project in the Redmine_Instance and return a confirmation of success
2. WHEN the AI_Agent invokes the unarchive-project Tool with a project ID, THE MCP_Server SHALL unarchive that project in the Redmine_Instance and return a confirmation of success
3. IF the specified project does not exist, THEN THE MCP_Server SHALL return an error indicating the project was not found

### Requirement 14: Search Redmine

**User Story:** As an AI agent, I want to search across Redmine resources, so that I can help users quickly find issues, wiki pages, documents, and other content.

#### Acceptance Criteria

1. WHEN the AI_Agent invokes the search Tool with a query string, THE MCP_Server SHALL return matching results from the Redmine_Instance
2. WHEN the AI_Agent provides scope filters (all, my_project, subprojects), THE MCP_Server SHALL limit search results to the specified scope
3. WHEN the AI_Agent provides resource type filters (issues, news, documents, changesets, wiki_pages, messages, projects, attachments), THE MCP_Server SHALL return only results of the specified types
4. WHEN the AI_Agent specifies open_issues filter, THE MCP_Server SHALL return only open issues in the search results
5. WHEN the AI_Agent provides offset and limit parameters, THE MCP_Server SHALL return the corresponding page of search results with a default limit of 25 and maximum limit of 100
6. THE MCP_Server SHALL return each search result with id, title, type, url, description, and datetime fields
7. THE MCP_Server SHALL include total_count, offset, and limit in the search response
8. IF the query string is missing or empty, THEN THE MCP_Server SHALL return a validation error indicating that a query string is required

### Requirement 15: Error Handling

**User Story:** As an AI agent, I want clear and informative error messages, so that I can understand failures and communicate them to the user.

#### Acceptance Criteria

1. IF the Redmine_Instance returns an HTTP 401 status, THEN THE MCP_Server SHALL return an error indicating authentication failure with the API_Key
2. IF the Redmine_Instance returns an HTTP 403 status, THEN THE MCP_Server SHALL return an error indicating insufficient permissions for the requested operation
3. IF the Redmine_Instance returns an HTTP 404 status, THEN THE MCP_Server SHALL return an error indicating the requested resource was not found
4. IF the Redmine_Instance returns an HTTP 422 status, THEN THE MCP_Server SHALL return the validation errors from the response body
5. IF the Redmine_Instance is unreachable due to DNS resolution failure, connection refused, or connection timeout exceeding 30 seconds, THEN THE MCP_Server SHALL return an error indicating a connection failure with the configured URL
6. IF the Redmine_Instance does not respond within 30 seconds of receiving a request, THEN THE MCP_Server SHALL return a timeout error indicating the request exceeded the allowed duration
7. IF the Redmine_Instance returns an unexpected HTTP status code (5xx or any unhandled status), THEN THE MCP_Server SHALL return an error including the HTTP status code and any response body content
8. THE MCP_Server SHALL include the HTTP status code and Redmine error details in all error responses

### Requirement 16: MCP Protocol Compliance

**User Story:** As a developer, I want the server to comply with MCP standards, so that it works seamlessly with any MCP-compatible client.

#### Acceptance Criteria

1. THE MCP_Server SHALL be implemented in Python using the FastMCP library and communicate over the stdio transport
2. THE MCP_Server SHALL expose each Redmine operation as a named Tool with typed parameters and a docstring description for AI agent comprehension
3. WHEN a Tool invocation succeeds, THE MCP_Server SHALL return the result as a string or structured content that FastMCP serializes as an MCP response
4. IF a Tool invocation fails due to a Redmine API error or validation failure, THEN THE MCP_Server SHALL raise an error or return error details that FastMCP propagates to the client with the isError flag set to true
5. THE MCP_Server SHALL assign each Tool a descriptive name using snake_case convention (e.g., "list_issues", "get_project") and a docstring of no more than 200 characters that states what operation the tool performs
