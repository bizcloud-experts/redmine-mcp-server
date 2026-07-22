"""Async HTTP client for the Redmine REST API."""

from __future__ import annotations

import httpx

from .exceptions import (
    RedmineAuthError,
    RedmineConnectionError,
    RedmineNotFoundError,
    RedminePermissionError,
    RedmineTimeoutError,
    RedmineValidationError,
    RedmineError,
)


class RedmineClient:
    """Lightweight async HTTP client for Redmine API communication.

    Handles authentication, request building, response parsing, and error mapping.
    """

    def __init__(self, base_url: str, api_key: str):
        """Initialize with Redmine base URL and API key.

        Args:
            base_url: The Redmine instance URL (no trailing slash).
            api_key: The Redmine API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-Redmine-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
        )

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Send a GET request to the Redmine API.

        Args:
            path: API endpoint path (e.g., '/issues.json').
            params: Optional query parameters.

        Returns:
            Parsed JSON response body as a dict.
        """
        response = await self._request("GET", path, params=params)
        return response.json()

    async def post(self, path: str, data: dict) -> dict:
        """Send a POST request to the Redmine API.

        Args:
            path: API endpoint path (e.g., '/issues.json').
            data: Request body as a dict.

        Returns:
            Parsed JSON response body as a dict.
        """
        response = await self._request("POST", path, json=data)
        if response.status_code == 201 and response.content:
            return response.json()
        return {}

    async def put(self, path: str, data: dict | None = None) -> None:
        """Send a PUT request to the Redmine API.

        Args:
            path: API endpoint path (e.g., '/issues/1.json').
            data: Optional request body as a dict.
        """
        await self._request("PUT", path, json=data)

    async def delete(self, path: str) -> None:
        """Send a DELETE request to the Redmine API.

        Args:
            path: API endpoint path (e.g., '/issues/1.json').
        """
        await self._request("DELETE", path)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request and handle errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API endpoint path.
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            The httpx Response object.

        Raises:
            RedmineAuthError: On 401 responses.
            RedminePermissionError: On 403 responses.
            RedmineNotFoundError: On 404 responses.
            RedmineValidationError: On 422 responses.
            RedmineError: On other 4xx/5xx responses.
            RedmineConnectionError: On connection failures.
            RedmineTimeoutError: On request timeouts.
        """
        try:
            response = await self._client.request(
                method, path, params=params, json=json
            )
        except httpx.TimeoutException:
            raise RedmineTimeoutError()
        except httpx.ConnectError:
            raise RedmineConnectionError(self.base_url)
        except httpx.HTTPError:
            raise RedmineConnectionError(self.base_url)

        self._handle_response(response)
        return response

    def _handle_response(self, response: httpx.Response) -> None:
        """Check response status and raise appropriate exceptions.

        Args:
            response: The httpx Response to check.

        Raises:
            RedmineAuthError: On 401 status.
            RedminePermissionError: On 403 status.
            RedmineNotFoundError: On 404 status.
            RedmineValidationError: On 422 status.
            RedmineError: On other error statuses.
        """
        if response.is_success:
            return

        status = response.status_code

        if status == 401:
            raise RedmineAuthError()
        elif status == 403:
            raise RedminePermissionError()
        elif status == 404:
            raise RedmineNotFoundError()
        elif status == 422:
            details = self._extract_validation_errors(response)
            raise RedmineValidationError(details=details)
        else:
            body = response.text[:500] if response.text else ""
            raise RedmineError(
                message=f"Redmine server error (HTTP {status}): {body}",
                status_code=status,
            )

    def _extract_validation_errors(self, response: httpx.Response) -> list[str]:
        """Extract validation error messages from a 422 response body.

        Args:
            response: The 422 response from Redmine.

        Returns:
            List of error message strings.
        """
        try:
            body = response.json()
            errors = body.get("errors", [])
            if isinstance(errors, list):
                return [str(e) for e in errors]
            return [str(errors)]
        except Exception:
            return []

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
