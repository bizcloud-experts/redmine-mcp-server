"""Property-based tests for Redmine MCP Server.

Each test validates a correctness property from the design document
using the hypothesis library.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from redmine_mcp_server.client import RedmineClient
from redmine_mcp_server.config import ConfigurationError, validate_url
from redmine_mcp_server.exceptions import (
    RedmineError,
    RedmineValidationError,
)
from redmine_mcp_server.tools.issues import register_issue_tools


# Feature: redmine-mcp-server, Property 1: URL Validation Rejects Invalid Schemes
class TestProperty1URLValidation:
    @given(url=st.text(alphabet=st.characters(codec="ascii")))
    @settings(max_examples=100)
    def test_rejects_invalid_schemes(self, url):
        """URLs without http:// or https:// prefix are rejected."""
        assume(not url.startswith("http://") and not url.startswith("https://"))
        with pytest.raises(ConfigurationError):
            validate_url(url)

    @given(path=st.text(min_size=1, alphabet=st.characters(codec="ascii")).filter(lambda s: s[0] not in "/\x00"))
    @settings(max_examples=100)
    def test_accepts_http_scheme(self, path):
        """URLs with http:// prefix are accepted."""
        url = f"http://{path}"
        result = validate_url(url)
        assert result.startswith("http://")

    @given(path=st.text(min_size=1, alphabet=st.characters(codec="ascii")).filter(lambda s: s[0] not in "/\x00"))
    @settings(max_examples=100)
    def test_accepts_https_scheme(self, path):
        """URLs with https:// prefix are accepted."""
        url = f"https://{path}"
        result = validate_url(url)
        assert result.startswith("https://")



# Feature: redmine-mcp-server, Property 2: API Key Header Always Present
class TestProperty2APIKeyHeader:
    @given(api_key=st.text(min_size=1, alphabet=st.characters(codec="ascii", categories=("L", "N", "P", "S"))))
    @settings(max_examples=100)
    @respx.mock
    async def test_api_key_header_present_on_all_requests(self, api_key):
        """X-Redmine-API-Key header matches configured key on every request."""
        client = RedmineClient(base_url="http://redmine.example.com", api_key=api_key)
        route = respx.get("http://redmine.example.com/test.json").mock(
            return_value=httpx.Response(200, json={})
        )
        await client.get("/test.json")
        assert route.calls[0].request.headers["X-Redmine-API-Key"] == api_key


# Feature: redmine-mcp-server, Property 4: Pagination Limit Capped at 100
class TestProperty4PaginationLimit:
    @given(limit=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    @respx.mock
    async def test_limit_capped_at_100(self, limit):
        """Effective limit sent to Redmine is min(limit, 100)."""
        mcp = FastMCP("test")
        client = RedmineClient(
            base_url="http://redmine.example.com", api_key="key"
        )
        register_issue_tools(mcp, client)

        expected = min(limit, 100)
        route = respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(
                200,
                json={"issues": [], "total_count": 0, "offset": 0, "limit": expected},
            )
        )

        tool = await mcp.get_tool("list_issues")
        await tool.fn(limit=limit)

        url = str(route.calls[0].request.url)
        assert f"limit={expected}" in url



# Feature: redmine-mcp-server, Property 7: Non-Positive-Integer IDs Rejected
class TestProperty7IDValidation:
    @given(bad_id=st.integers(max_value=0))
    @settings(max_examples=100)
    async def test_non_positive_ids_rejected_get_issue(self, bad_id):
        """Non-positive integer IDs produce validation error before HTTP call."""
        mcp = FastMCP("test")
        client = RedmineClient(
            base_url="http://redmine.example.com", api_key="key"
        )
        register_issue_tools(mcp, client)

        tool = await mcp.get_tool("get_issue")
        result = await tool.fn(issue_id=bad_id)
        assert "error" in result
        assert "positive integer" in result["error"]

    @given(bad_id=st.integers(max_value=0))
    @settings(max_examples=100)
    async def test_non_positive_ids_rejected_delete_issue(self, bad_id):
        """Non-positive integer IDs produce validation error for delete."""
        mcp = FastMCP("test")
        client = RedmineClient(
            base_url="http://redmine.example.com", api_key="key"
        )
        register_issue_tools(mcp, client)

        tool = await mcp.get_tool("delete_issue")
        result = await tool.fn(issue_id=bad_id)
        assert "error" in result


# Feature: redmine-mcp-server, Property 10: Redmine Validation Errors Extracted
class TestProperty10ValidationErrors:
    @given(errors=st.lists(st.text(min_size=1, alphabet=st.characters(codec="ascii")), min_size=1, max_size=10))
    @settings(max_examples=100)
    @respx.mock
    async def test_all_errors_extracted_from_422(self, errors):
        """Every error message from a 422 response is extracted."""
        client = RedmineClient(
            base_url="http://redmine.example.com", api_key="key"
        )
        respx.post("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(422, json={"errors": errors})
        )
        with pytest.raises(RedmineValidationError) as exc_info:
            await client.post("/issues.json", {"issue": {}})
        assert exc_info.value.details == errors


# Feature: redmine-mcp-server, Property 12: All Error Responses Include HTTP Status Code
class TestProperty12ErrorStatusCode:
    @given(status_code=st.sampled_from([400, 401, 403, 404, 405, 409, 422, 500, 502, 503]))
    @settings(max_examples=100)
    @respx.mock
    async def test_error_includes_status_code(self, status_code):
        """All HTTP error responses carry the status code."""
        client = RedmineClient(
            base_url="http://redmine.example.com", api_key="key"
        )
        json_body = {"errors": ["err"]} if status_code == 422 else {}
        respx.get("http://redmine.example.com/test.json").mock(
            return_value=httpx.Response(status_code, json=json_body)
        )
        with pytest.raises(RedmineError) as exc_info:
            await client.get("/test.json")
        assert exc_info.value.status_code == status_code
