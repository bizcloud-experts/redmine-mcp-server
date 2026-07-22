"""Unit tests for RedmineClient HTTP layer."""

from __future__ import annotations

import httpx
import pytest
import respx

from redmine_mcp_server.client import RedmineClient
from redmine_mcp_server.exceptions import (
    RedmineAuthError,
    RedmineConnectionError,
    RedmineError,
    RedmineNotFoundError,
    RedminePermissionError,
    RedmineTimeoutError,
    RedmineValidationError,
)


@pytest.fixture
def client():
    return RedmineClient(base_url="http://redmine.example.com", api_key="test-api-key")


class TestClientHeaders:
    """Test that correct headers are sent on all requests."""

    @respx.mock
    async def test_api_key_header_on_get(self, client):
        route = respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(200, json={"issues": []})
        )
        await client.get("/issues.json")
        assert route.calls[0].request.headers["X-Redmine-API-Key"] == "test-api-key"

    @respx.mock
    async def test_content_type_header_on_post(self, client):
        route = respx.post("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(201, json={"issue": {"id": 1}})
        )
        await client.post("/issues.json", {"issue": {"subject": "test"}})
        assert route.calls[0].request.headers["Content-Type"] == "application/json"

    @respx.mock
    async def test_api_key_header_on_put(self, client):
        route = respx.put("http://redmine.example.com/issues/1.json").mock(
            return_value=httpx.Response(204)
        )
        await client.put("/issues/1.json", {"issue": {"subject": "updated"}})
        assert route.calls[0].request.headers["X-Redmine-API-Key"] == "test-api-key"

    @respx.mock
    async def test_api_key_header_on_delete(self, client):
        route = respx.delete("http://redmine.example.com/issues/1.json").mock(
            return_value=httpx.Response(204)
        )
        await client.delete("/issues/1.json")
        assert route.calls[0].request.headers["X-Redmine-API-Key"] == "test-api-key"


class TestClientErrorMapping:
    """Test HTTP status code to exception mapping."""

    @respx.mock
    async def test_401_raises_auth_error(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(401)
        )
        with pytest.raises(RedmineAuthError):
            await client.get("/issues.json")

    @respx.mock
    async def test_403_raises_permission_error(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(403)
        )
        with pytest.raises(RedminePermissionError):
            await client.get("/issues.json")

    @respx.mock
    async def test_404_raises_not_found_error(self, client):
        respx.get("http://redmine.example.com/issues/999.json").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(RedmineNotFoundError):
            await client.get("/issues/999.json")

    @respx.mock
    async def test_422_raises_validation_error_with_details(self, client):
        respx.post("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(
                422,
                json={"errors": ["Subject cannot be blank", "Project is not valid"]},
            )
        )
        with pytest.raises(RedmineValidationError) as exc_info:
            await client.post("/issues.json", {"issue": {}})
        assert exc_info.value.details == [
            "Subject cannot be blank",
            "Project is not valid",
        ]

    @respx.mock
    async def test_422_with_no_json_body(self, client):
        respx.post("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(422, text="error")
        )
        with pytest.raises(RedmineValidationError) as exc_info:
            await client.post("/issues.json", {"issue": {}})
        assert exc_info.value.details == []

    @respx.mock
    async def test_500_raises_generic_redmine_error(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(RedmineError) as exc_info:
            await client.get("/issues.json")
        assert exc_info.value.status_code == 500
        assert "500" in exc_info.value.message

    @respx.mock
    async def test_timeout_raises_timeout_error(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        with pytest.raises(RedmineTimeoutError):
            await client.get("/issues.json")

    @respx.mock
    async def test_connection_error_raises_connection_error(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        with pytest.raises(RedmineConnectionError) as exc_info:
            await client.get("/issues.json")
        assert "redmine.example.com" in exc_info.value.message


class TestClientResponses:
    """Test successful response handling."""

    @respx.mock
    async def test_get_returns_parsed_json(self, client):
        respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(
                200, json={"issues": [{"id": 1}], "total_count": 1}
            )
        )
        result = await client.get("/issues.json")
        assert result == {"issues": [{"id": 1}], "total_count": 1}

    @respx.mock
    async def test_post_returns_parsed_json_on_201(self, client):
        respx.post("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(201, json={"issue": {"id": 42}})
        )
        result = await client.post("/issues.json", {"issue": {"subject": "test"}})
        assert result == {"issue": {"id": 42}}

    @respx.mock
    async def test_post_returns_empty_dict_on_201_no_body(self, client):
        respx.post("http://redmine.example.com/watchers.json").mock(
            return_value=httpx.Response(201)
        )
        result = await client.post("/watchers.json", {"user_id": 1})
        assert result == {}

    @respx.mock
    async def test_put_returns_none(self, client):
        respx.put("http://redmine.example.com/issues/1.json").mock(
            return_value=httpx.Response(204)
        )
        result = await client.put("/issues/1.json", {"issue": {"subject": "x"}})
        assert result is None

    @respx.mock
    async def test_delete_returns_none(self, client):
        respx.delete("http://redmine.example.com/issues/1.json").mock(
            return_value=httpx.Response(200)
        )
        result = await client.delete("/issues/1.json")
        assert result is None

    @respx.mock
    async def test_get_passes_query_params(self, client):
        route = respx.get("http://redmine.example.com/issues.json").mock(
            return_value=httpx.Response(200, json={"issues": []})
        )
        await client.get("/issues.json", params={"project_id": 5, "limit": 10})
        request = route.calls[0].request
        assert "project_id=5" in str(request.url)
        assert "limit=10" in str(request.url)


class TestClientInit:
    """Test client initialization."""

    def test_strips_trailing_slash_from_base_url(self):
        c = RedmineClient(base_url="http://redmine.example.com/", api_key="key")
        assert c.base_url == "http://redmine.example.com"

    def test_stores_api_key(self):
        c = RedmineClient(base_url="http://redmine.example.com", api_key="my-key")
        assert c.api_key == "my-key"
