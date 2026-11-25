"""Core FastMCP server implementation for DepShift."""

import sys
from typing import Any, Dict
from fastmcp import FastMCP

from depshift import __version__

# Initialize FastMCP Server
mcp = FastMCP(
    name="depshift",
    instructions=(
        "DepShift is an autonomous dependency migration and remediation agent. "
        "It inspects repositories, checks test baselines, fetches migration intelligence, "
        "bumps dependencies, and refactors breaking code changes until all tests pass."
    ),
)


@mcp.tool()
def ping() -> str:
    """Diagnostic health check tool to verify the DepShift MCP server connection."""
    return "pong"


@mcp.tool()
def get_version() -> Dict[str, Any]:
    """Retrieve the current DepShift version, Python runtime, and host platform information."""
    return {
        "name": "depshift",
        "version": __version__,
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
    }


def main() -> None:
    """Entry point for running the DepShift MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
