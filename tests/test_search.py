"""Unit tests for search tool handler."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from redmine_mcp_server.client import RedmineClient
from redmine_mcp_server.tools.search import register_search_tools


@pytest.fixture
def setup():
    """Create MCP server and client for testing."""
    mcp = FastMCP("test")
    client = RedmineClient(base_url="http://redmine.example.com", api_key="test-key")
    register_search_tools(mcp, client)
    return mcp, client



@pytest.fixture
def call_tool(setup):
    """Helper to call a tool by name."""
    mcp, _ = setup

    async def _call(name: str, **kwargs):
        tool = await mcp.get_tool(name)
        return await tool.fn(**kwargs)

    return _call


class TestSearch:
    async def test_rejects_empty_query(self, call_tool):
        result = await call_tool("search", query="")
        assert "error" in result
        assert "query" in result["error"]

    async def test_rejects_whitespace_query(self, call_tool):
        result = await call_tool("search", query="   ")
        assert "error" in result

    @respx.mock
    async def test_returns_paginated_results(self, call_tool):
        respx.get("http://redmine.example.com/search.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": 1,
                            "title": "Test Issue",
                            "type": "issue",
                            "url": "/issues/1",
                            "description": "match",
                            "datetime": "2024-01-15T10:30:00Z",
                        }
                    ],
                    "total_count": 1,
                    "offset": 0,
                    "limit": 25,
                },
            )
        )
        result = await call_tool("search", query="test")
        assert result["total_count"] == 1
        assert result["offset"] == 0
        assert result["limit"] == 25
        assert len(result["results"]) == 1
        assert result["results"][0]["type"] == "issue"

    @respx.mock
    async def test_limit_capped_at_100(self, call_tool):
        route = respx.get("http://redmine.example.com/search.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [],
                    "total_count": 0,
                    "offset": 0,
                    "limit": 100,
                },
            )
        )
        await call_tool("search", query="x", limit=999)
        assert "limit=100" in str(route.calls[0].request.url)

    @respx.mock
    async def test_scope_parameter_passed(self, call_tool):
        route = respx.get("http://redmine.example.com/search.json").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "total_count": 0, "offset": 0, "limit": 25},
            )
        )
        await call_tool("search", query="bug", scope="my_project")
        assert "scope=my_project" in str(route.calls[0].request.url)

    @respx.mock
    async def test_resource_type_filters(self, call_tool):
        route = respx.get("http://redmine.example.com/search.json").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "total_count": 0, "offset": 0, "limit": 25},
            )
        )
        await call_tool("search", query="test", issues=True, wiki_pages=True)
        url = str(route.calls[0].request.url)
        assert "issues=1" in url
        assert "wiki_pages=1" in url
