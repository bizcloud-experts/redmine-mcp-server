"""Search MCP tool for Redmine."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import RedmineClient
from ..exceptions import RedmineError


def register_search_tools(mcp: FastMCP, client: RedmineClient) -> None:
    """Register the search tool with the MCP server."""

    @mcp.tool()
    async def search(
        query: str,
        scope: str | None = None,
        all_words: bool | None = None,
        titles_only: bool | None = None,
        issues: bool | None = None,
        news: bool | None = None,
        documents: bool | None = None,
        changesets: bool | None = None,
        wiki_pages: bool | None = None,
        messages: bool | None = None,
        projects: bool | None = None,
        open_issues: bool | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> dict:
        """Search across Redmine resources."""
        if not query or not query.strip():
            return {"error": "query is required and cannot be empty", "details": []}

        params: dict = {
            "q": query,
            "offset": offset,
            "limit": min(limit, 100),
        }

        if scope is not None:
            params["scope"] = scope
        if all_words is not None:
            params["all_words"] = all_words
        if titles_only is not None:
            params["titles_only"] = titles_only
        if open_issues is not None:
            params["open_issues"] = 1 if open_issues else 0

        # Resource type filters
        resource_types = {
            "issues": issues,
            "news": news,
            "documents": documents,
            "changesets": changesets,
            "wiki_pages": wiki_pages,
            "messages": messages,
            "projects": projects,
        }

        for resource, enabled in resource_types.items():
            if enabled is not None:
                params[resource] = 1 if enabled else 0

        try:
            data = await client.get("/search.json", params=params)
        except RedmineError as e:
            return e.to_dict()

        return {
            "total_count": data.get("total_count", 0),
            "offset": data.get("offset", offset),
            "limit": data.get("limit", params["limit"]),
            "results": data.get("results", []),
        }
