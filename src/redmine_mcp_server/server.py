"""Redmine MCP Server entry point.

This module creates the FastMCP server instance, validates configuration
at startup, and registers all tool handlers.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .client import RedmineClient
from .config import load_config
from .tools.issues import register_issue_tools
from .tools.projects import register_project_tools
from .tools.search import register_search_tools

# Validate configuration at import time (fail fast)
config = load_config()

# Create the MCP server
mcp = FastMCP("redmine-mcp-server")

# Create the shared Redmine API client
client = RedmineClient(base_url=config["redmine_url"], api_key=config["redmine_api_key"])

# Register all tool domains
register_issue_tools(mcp, client)
register_project_tools(mcp, client)
register_search_tools(mcp, client)


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
