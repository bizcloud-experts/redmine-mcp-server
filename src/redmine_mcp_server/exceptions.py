"""Custom exception hierarchy for Redmine MCP Server."""

from __future__ import annotations


class RedmineError(Exception):
    """Base exception for all Redmine API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: list[str] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or []

    def to_dict(self) -> dict:
        """Convert exception to a structured error response dict."""
        result: dict = {"error": self.message}
        if self.status_code is not None:
            result["status_code"] = self.status_code
        if self.details:
            result["details"] = self.details
        return result


class RedmineAuthError(RedmineError):
    """Raised when authentication fails (HTTP 401)."""

    def __init__(self, message: str = "Authentication failed: invalid or expired API key"):
        super().__init__(message, status_code=401)


class RedminePermissionError(RedmineError):
    """Raised when the user lacks permissions (HTTP 403)."""

    def __init__(
        self, message: str = "Permission denied: insufficient privileges for this operation"
    ):
        super().__init__(message, status_code=403)


class RedmineNotFoundError(RedmineError):
    """Raised when a resource is not found (HTTP 404)."""

    def __init__(self, resource_type: str = "Resource"):
        message = f"{resource_type} not found"
        super().__init__(message, status_code=404)


class RedmineValidationError(RedmineError):
    """Raised when Redmine returns validation errors (HTTP 422)."""

    def __init__(self, details: list[str] | None = None):
        message = "Validation failed"
        super().__init__(message, status_code=422, details=details)


class RedmineConnectionError(RedmineError):
    """Raised when the connection to Redmine fails."""

    def __init__(self, url: str = ""):
        message = f"Connection failed: unable to reach {url}" if url else "Connection failed"
        super().__init__(message)


class RedmineTimeoutError(RedmineError):
    """Raised when a request to Redmine times out."""

    def __init__(self):
        super().__init__("Request timed out after 30 seconds")
