"""Unit tests for project tool handlers."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from redmine_mcp_server.client import RedmineClient
from redmine_mcp_server.tools.projects import register_project_tools


@pytest.fixture
def setup():
    """Create MCP server and client for testing."""
    mcp = FastMCP("test")
    client = RedmineClient(base_url="http://redmine.example.com", api_key="test-key")
    register_project_tools(mcp, client)
    return mcp, client


@pytest.fixture
def call_tool(setup):
    """Helper to call a tool by name."""
    mcp, _ = setup

    async def _call(tool_name: str, **kwargs):
        tool = await mcp.get_tool(tool_name)
        return await tool.fn(**kwargs)

    return _call


class TestListProjects:
    @respx.mock
    async def test_default_pagination(self, call_tool):
        respx.get("http://redmine.example.com/projects.json").mock(
            return_value=httpx.Response(
                200,
                json={"projects": [], "total_count": 0, "offset": 0, "limit": 25},
            )
        )
        result = await call_tool("list_projects")
        assert result["offset"] == 0
        assert result["limit"] == 25
        assert result["total_count"] == 0

    @respx.mock
    async def test_limit_capped_at_100(self, call_tool):
        route = respx.get("http://redmine.example.com/projects.json").mock(
            return_value=httpx.Response(
                200,
                json={"projects": [], "total_count": 0, "offset": 0, "limit": 100},
            )
        )
        await call_tool("list_projects", limit=999)
        assert "limit=100" in str(route.calls[0].request.url)

    async def test_rejects_invalid_include(self, call_tool):
        result = await call_tool("list_projects", include="invalid_field")
        assert "error" in result
        assert "Unsupported" in result["error"]

    @respx.mock
    async def test_valid_include(self, call_tool):
        route = respx.get("http://redmine.example.com/projects.json").mock(
            return_value=httpx.Response(
                200,
                json={"projects": [], "total_count": 0, "offset": 0, "limit": 25},
            )
        )
        await call_tool("list_projects", include="trackers,enabled_modules")
        assert "include=trackers" in str(route.calls[0].request.url)


class TestGetProject:
    @respx.mock
    async def test_returns_project_details(self, call_tool):
        respx.get("http://redmine.example.com/projects/myproject.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "project": {
                        "id": 1,
                        "name": "My Project",
                        "identifier": "myproject",
                        "description": "A project",
                        "status": 1,
                        "is_public": True,
                    }
                },
            )
        )
        result = await call_tool("get_project", project_id="myproject")
        assert result["id"] == 1
        assert result["identifier"] == "myproject"

    async def test_rejects_invalid_include(self, call_tool):
        result = await call_tool(
            "get_project", project_id="test", include="bad_value"
        )
        assert "error" in result


class TestCreateProject:
    @respx.mock
    async def test_creates_project_with_required_fields(self, call_tool):
        respx.post("http://redmine.example.com/projects.json").mock(
            return_value=httpx.Response(
                201,
                json={
                    "project": {
                        "id": 10,
                        "name": "New Project",
                        "identifier": "new-project",
                    }
                },
            )
        )
        result = await call_tool(
            "create_project", name="New Project", identifier="new-project"
        )
        assert result["id"] == 10

    async def test_rejects_empty_name(self, call_tool):
        result = await call_tool("create_project", name="", identifier="test")
        assert "error" in result
        assert "name" in result["error"]

    async def test_rejects_empty_identifier(self, call_tool):
        result = await call_tool("create_project", name="Test", identifier="")
        assert "error" in result
        assert "identifier" in result["error"]

    @respx.mock
    async def test_optional_fields_in_body(self, call_tool):
        route = respx.post("http://redmine.example.com/projects.json").mock(
            return_value=httpx.Response(201, json={"project": {"id": 1}})
        )
        await call_tool(
            "create_project",
            name="Test",
            identifier="test",
            description="Desc",
            is_public=False,
            parent_id=5,
        )
        body = json.loads(route.calls[0].request.content)
        assert body["project"]["description"] == "Desc"
        assert body["project"]["is_public"] is False
        assert body["project"]["parent_id"] == 5


class TestUpdateProject:
    @respx.mock
    async def test_updates_successfully(self, call_tool):
        respx.put("http://redmine.example.com/projects/myproj.json").mock(
            return_value=httpx.Response(204)
        )
        result = await call_tool(
            "update_project", project_id="myproj", name="Updated Name"
        )
        assert result["status"] == "success"

    async def test_rejects_empty_update(self, call_tool):
        result = await call_tool("update_project", project_id="myproj")
        assert "error" in result
        assert "At least one field" in result["error"]


class TestDeleteProject:
    @respx.mock
    async def test_deletes_successfully(self, call_tool):
        respx.delete("http://redmine.example.com/projects/myproj.json").mock(
            return_value=httpx.Response(200)
        )
        result = await call_tool("delete_project", project_id="myproj")
        assert result["status"] == "success"
        assert result["deleted_project_id"] == "myproj"


class TestArchiveUnarchive:
    @respx.mock
    async def test_archive_correct_path(self, call_tool):
        route = respx.put(
            "http://redmine.example.com/projects/myproj/archive.json"
        ).mock(return_value=httpx.Response(204))
        result = await call_tool("archive_project", project_id="myproj")
        assert result["action"] == "archived"
        assert route.called

    @respx.mock
    async def test_unarchive_correct_path(self, call_tool):
        route = respx.put(
            "http://redmine.example.com/projects/myproj/unarchive.json"
        ).mock(return_value=httpx.Response(204))
        result = await call_tool("unarchive_project", project_id="myproj")
        assert result["action"] == "unarchived"
        assert route.called
