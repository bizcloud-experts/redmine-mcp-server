"""Project-related MCP tools for Redmine."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import RedmineClient
from ..exceptions import RedmineError


def register_project_tools(mcp: FastMCP, client: RedmineClient) -> None:
    """Register all project-related tools with the MCP server."""

    @mcp.tool()
    async def list_projects(
        include: str | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> dict:
        """List all accessible projects with pagination."""
        supported_includes = {
            "trackers",
            "issue_categories",
            "enabled_modules",
            "time_entry_activities",
            "issue_custom_fields",
        }

        params: dict = {
            "offset": offset,
            "limit": min(limit, 100),
        }

        if include is not None:
            requested = {v.strip() for v in include.split(",")}
            invalid = requested - supported_includes
            if invalid:
                return {
                    "error": f"Unsupported include values: {sorted(invalid)}. "
                    f"Supported: {sorted(supported_includes)}",
                    "details": [],
                }
            params["include"] = include

        try:
            data = await client.get("/projects.json", params=params)
        except RedmineError as e:
            return e.to_dict()

        return {
            "total_count": data.get("total_count", 0),
            "offset": data.get("offset", offset),
            "limit": data.get("limit", params["limit"]),
            "projects": data.get("projects", []),
        }

    @mcp.tool()
    async def get_project(
        project_id: str,
        include: str | None = None,
    ) -> dict:
        """Get detailed information about a specific project."""
        supported_includes = {
            "trackers",
            "issue_categories",
            "enabled_modules",
            "time_entry_activities",
            "issue_custom_fields",
        }

        params: dict = {}
        if include is not None:
            requested = {v.strip() for v in include.split(",")}
            invalid = requested - supported_includes
            if invalid:
                return {
                    "error": f"Unsupported include values: {sorted(invalid)}. "
                    f"Supported: {sorted(supported_includes)}",
                    "details": [],
                }
            params["include"] = include

        try:
            data = await client.get(f"/projects/{project_id}.json", params=params)
        except RedmineError as e:
            return e.to_dict()

        return data.get("project", data)

    @mcp.tool()
    async def create_project(
        name: str,
        identifier: str,
        description: str | None = None,
        homepage: str | None = None,
        is_public: bool | None = None,
        parent_id: int | None = None,
        inherit_members: bool | None = None,
        default_assigned_to_id: int | None = None,
        default_version_id: int | None = None,
        tracker_ids: list[int] | None = None,
        enabled_module_names: list[str] | None = None,
        issue_custom_field_ids: list[int] | None = None,
        custom_field_values: dict | None = None,
    ) -> dict:
        """Create a new project."""
        if not name or not name.strip():
            return {"error": "name is required and cannot be empty", "details": []}
        if not identifier or not identifier.strip():
            return {"error": "identifier is required and cannot be empty", "details": []}

        project_data: dict = {
            "name": name,
            "identifier": identifier,
        }

        optional_fields = {
            "description": description,
            "homepage": homepage,
            "is_public": is_public,
            "parent_id": parent_id,
            "inherit_members": inherit_members,
            "default_assigned_to_id": default_assigned_to_id,
            "default_version_id": default_version_id,
            "tracker_ids": tracker_ids,
            "enabled_module_names": enabled_module_names,
            "issue_custom_field_ids": issue_custom_field_ids,
            "custom_field_values": custom_field_values,
        }

        for key, value in optional_fields.items():
            if value is not None:
                project_data[key] = value

        try:
            data = await client.post("/projects.json", {"project": project_data})
        except RedmineError as e:
            return e.to_dict()

        return data.get("project", data)

    @mcp.tool()
    async def update_project(
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        homepage: str | None = None,
        is_public: bool | None = None,
        parent_id: int | None = None,
        inherit_members: bool | None = None,
        default_assigned_to_id: int | None = None,
        default_version_id: int | None = None,
        tracker_ids: list[int] | None = None,
        enabled_module_names: list[str] | None = None,
        issue_custom_field_ids: list[int] | None = None,
        custom_field_values: dict | None = None,
    ) -> dict:
        """Update an existing project."""
        project_data: dict = {}

        optional_fields = {
            "name": name,
            "description": description,
            "homepage": homepage,
            "is_public": is_public,
            "parent_id": parent_id,
            "inherit_members": inherit_members,
            "default_assigned_to_id": default_assigned_to_id,
            "default_version_id": default_version_id,
            "tracker_ids": tracker_ids,
            "enabled_module_names": enabled_module_names,
            "issue_custom_field_ids": issue_custom_field_ids,
            "custom_field_values": custom_field_values,
        }

        for key, value in optional_fields.items():
            if value is not None:
                project_data[key] = value

        if not project_data:
            return {"error": "At least one field to update must be provided", "details": []}

        try:
            await client.put(f"/projects/{project_id}.json", {"project": project_data})
        except RedmineError as e:
            return e.to_dict()

        return {"status": "success", "project_id": project_id}

    @mcp.tool()
    async def delete_project(project_id: str) -> dict:
        """Delete a project permanently."""
        if not project_id or not str(project_id).strip():
            return {"error": "project_id is required", "details": []}

        try:
            await client.delete(f"/projects/{project_id}.json")
        except RedmineError as e:
            return e.to_dict()

        return {"status": "success", "deleted_project_id": project_id}

    @mcp.tool()
    async def archive_project(project_id: str) -> dict:
        """Archive a project."""
        if not project_id or not str(project_id).strip():
            return {"error": "project_id is required", "details": []}

        try:
            await client.put(f"/projects/{project_id}/archive.json")
        except RedmineError as e:
            return e.to_dict()

        return {"status": "success", "project_id": project_id, "action": "archived"}

    @mcp.tool()
    async def unarchive_project(project_id: str) -> dict:
        """Unarchive a project."""
        if not project_id or not str(project_id).strip():
            return {"error": "project_id is required", "details": []}

        try:
            await client.put(f"/projects/{project_id}/unarchive.json")
        except RedmineError as e:
            return e.to_dict()

        return {"status": "success", "project_id": project_id, "action": "unarchived"}
