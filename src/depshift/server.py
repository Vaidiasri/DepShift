"""Core FastMCP server implementation for DepShift."""

import sys
from typing import Any, Dict
from fastmcp import FastMCP

from depshift import __version__
from depshift.tools.git_tools import check_git_status
from depshift.tools.manifest_tools import inspect_dependencies
from depshift.tools.test_runner_tools import run_baseline_test

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


@mcp.tool()
def tool_check_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Inspects git status to verify the workspace exists, is a valid git repo, and has a clean working tree.

    Args:
        repo_path: Path to the target git repository (defaults to current directory).
    """
    return check_git_status(repo_path=repo_path)


@mcp.tool()
def tool_inspect_dependencies(repo_path: str = ".") -> Dict[str, Any]:
    """Inspects manifest files in a repository and extracts dependencies across Python and Node.js.

    Args:
        repo_path: Path to target repository directory (defaults to current directory).
    """
    return inspect_dependencies(repo_path=repo_path)


@mcp.tool()
def tool_run_baseline_test(
    repo_path: str = ".",
    test_command: str = "pytest",
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Executes the repository baseline test suite with security guardrails and timeout bounds.

    Args:
        repo_path: Directory of the target repository.
        test_command: Safe test runner command (e.g., 'pytest', 'npm test').
        timeout_seconds: Maximum allowed execution time in seconds.
    """
    return run_baseline_test(
        repo_path=repo_path,
        test_command=test_command,
        timeout_seconds=timeout_seconds,
    )


def main() -> None:
    """Entry point for running the DepShift MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
