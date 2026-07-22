"""Configuration management for Redmine MCP Server.

Reads and validates environment variables required for connecting
to a Redmine instance.
"""

import os


class ConfigurationError(Exception):
    """Raised when server configuration is invalid or incomplete."""

    pass


def validate_url(url: str) -> str:
    """Validate that the URL starts with http:// or https://.

    Args:
        url: The URL string to validate.

    Returns:
        The validated URL string (with trailing slash stripped).

    Raises:
        ConfigurationError: If the URL does not start with http:// or https://.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        raise ConfigurationError(
            "REDMINE_URL must start with 'http://' or 'https://'. "
            f"Got: '{url}'"
        )
    return url.rstrip("/")


def load_config() -> dict:
    """Load and validate configuration from environment variables.

    Reads REDMINE_URL and REDMINE_API_KEY from the environment,
    validates that both are present and that the URL has a valid scheme.

    Returns:
        A dict with keys 'redmine_url' and 'redmine_api_key'.

    Raises:
        ConfigurationError: If any required variable is missing, empty,
            or fails validation.
    """
    redmine_url = os.environ.get("REDMINE_URL", "").strip()
    redmine_api_key = os.environ.get("REDMINE_API_KEY", "").strip()

    if not redmine_url:
        raise ConfigurationError(
            "REDMINE_URL environment variable is missing or empty. "
            "Please set it to your Redmine instance URL (e.g., 'https://redmine.example.com')."
        )

    if not redmine_api_key:
        raise ConfigurationError(
            "REDMINE_API_KEY environment variable is missing or empty. "
            "Please set it to your Redmine API key."
        )

    validated_url = validate_url(redmine_url)

    return {
        "redmine_url": validated_url,
        "redmine_api_key": redmine_api_key,
    }
