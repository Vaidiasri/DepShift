"""Core FastMCP server implementation for DepShift."""

import sys
from typing import Any, Dict, Optional
from fastmcp import FastMCP

from depshift import __version__
from depshift.tools.git_tools import check_git_status
from depshift.tools.manifest_tools import inspect_dependencies
from depshift.tools.test_runner_tools import run_baseline_test
from depshift.tools.doc_tools import fetch_release_notes, extract_breaking_changes

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


@mcp.tool()
def tool_fetch_release_notes(
    package_name: str,
    from_version: Optional[str] = None,
    to_version: Optional[str] = None,
    ecosystem: str = "python",
    github_repo: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetches changelogs or release notes for a package from PyPI, npm, or GitHub Releases.

    Args:
        package_name: Name of package (e.g. 'pydantic', 'fastmcp', 'express').
        from_version: Currently installed version.
        to_version: Target version upgrading to.
        ecosystem: 'python' or 'node'.
        github_repo: Optional 'owner/repo' override (e.g. 'pydantic/pydantic').
    """
    return fetch_release_notes(
        package_name=package_name,
        from_version=from_version,
        to_version=to_version,
        ecosystem=ecosystem,
        github_repo=github_repo,
    )


@mcp.tool()
def tool_extract_breaking_changes(text: str) -> Dict[str, Any]:
    """Scans release notes or documentation text to extract breaking changes and migration notices.

    Args:
        text: Raw release notes or markdown text.
    """
    return extract_breaking_changes(text=text)


def main() -> None:
    """Entry point for running the DepShift MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
