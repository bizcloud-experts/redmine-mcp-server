"""Time entry-related MCP tools for Redmine."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import RedmineClient
from ..exceptions import RedmineError


def register_time_entry_tools(mcp: FastMCP, client: RedmineClient) -> None:
    """Register all time entry-related tools with the MCP server."""

    @mcp.tool()
    async def list_time_entries(
        project_id: int | None = None,
        issue_id: int | None = None,
        user_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        offset: int = 0,
        limit: int = 100,
        fetch_all: bool = False,
    ) -> dict:
        """List time entries with optional filters and pagination.

        Args:
            project_id: Filter by project ID.
            issue_id: Filter by issue ID.
            user_id: Filter by user ID.
            from_date: Start date filter (YYYY-MM-DD).
            to_date: End date filter (YYYY-MM-DD).
            offset: Pagination offset (ignored when fetch_all=True).
            limit: Maximum number of results per page (max 100).
            fetch_all: If True, automatically paginates and returns all matching
                entries in a single response. Use this for reports/aggregations.
        """
        params: dict = {}
        if project_id is not None:
            params["project_id"] = project_id
        if issue_id is not None:
            params["issue_id"] = issue_id
        if user_id is not None:
            params["user_id"] = user_id
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date

        page_limit = min(limit, 100)

        if fetch_all:
            all_entries: list[dict] = []
            current_offset = 0

            while True:
                params["offset"] = current_offset
                params["limit"] = page_limit

                try:
                    data = await client.get("/time_entries.json", params=params)
                except RedmineError as e:
                    return e.to_dict()

                entries = data.get("time_entries", [])
                all_entries.extend(entries)

                total_count = data.get("total_count", 0)
                current_offset += len(entries)

                if not entries or current_offset >= total_count:
                    break

            return {
                "total_count": len(all_entries),
                "time_entries": all_entries,
            }

        # Standard single-page request
        params["offset"] = offset
        params["limit"] = page_limit

        try:
            data = await client.get("/time_entries.json", params=params)
        except RedmineError as e:
            return e.to_dict()

        return {
            "total_count": data.get("total_count", 0),
            "offset": data.get("offset", offset),
            "limit": data.get("limit", page_limit),
            "time_entries": data.get("time_entries", []),
        }

    @mcp.tool()
    async def get_time_entry(time_entry_id: int) -> dict:
        """Get detailed information about a specific time entry.

        Args:
            time_entry_id: The ID of the time entry to retrieve.
        """
        if not isinstance(time_entry_id, int) or time_entry_id <= 0:
            return {"error": "time_entry_id must be a positive integer", "details": []}

        try:
            data = await client.get(f"/time_entries/{time_entry_id}.json")
        except RedmineError as e:
            return e.to_dict()

        return data.get("time_entry", data)
