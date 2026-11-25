"""Core FastMCP server implementation for DepShift."""

import sys
from typing import Any, Dict, Optional
from fastmcp import FastMCP

from depshift import __version__
from depshift.tools.git_tools import check_git_status
from depshift.tools.manifest_tools import inspect_dependencies, bump_dependency_version
from depshift.tools.test_runner_tools import run_baseline_test, execute_test_suite
from depshift.tools.doc_tools import fetch_release_notes, extract_breaking_changes
from depshift.tools.patch_tools import read_source_file, apply_code_patch

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


@mcp.tool()
def tool_bump_dependency_version(
    repo_path: str,
    package_name: str,
    target_version: str,
) -> Dict[str, Any]:
    """Updates the specified package version in pyproject.toml, requirements.txt, or package.json.

    Args:
        repo_path: Path to the target repository directory.
        package_name: Package name to update.
        target_version: Target version string (e.g. '2.0.0', '>=2.0.0', '^2.0.0').
    """
    return bump_dependency_version(
        repo_path=repo_path,
        package_name=package_name,
        target_version=target_version,
    )


@mcp.tool()
def tool_read_source_file(
    file_path: str,
    start_line: Optional[int] = 1,
    end_line: Optional[int] = None,
) -> Dict[str, Any]:
    """Reads a source code file with optional line-range boundaries and line numbering.

    Args:
        file_path: Absolute or relative path to the file.
        start_line: 1-indexed start line (defaults to 1).
        end_line: 1-indexed end line (defaults to end of file).
    """
    return read_source_file(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
    )


@mcp.tool()
def tool_apply_code_patch(
    file_path: str,
    target_block: str,
    replacement_block: str,
) -> Dict[str, Any]:
    """Applies an exact search-and-replace patch to a file preserving indentation and formatting.

    Args:
        file_path: Path to target file.
        target_block: Exact block of characters/lines to be replaced.
        replacement_block: Exact replacement string.
    """
    return apply_code_patch(
        file_path=file_path,
        target_block=target_block,
        replacement_block=replacement_block,
    )


@mcp.tool()
def tool_execute_test_suite(
    repo_path: str = ".",
    test_command: str = "pytest",
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Executes the test suite with detailed output capture and structured failure extraction.

    Args:
        repo_path: Directory of the target repository.
        test_command: Safe test runner command (e.g., 'pytest', 'npm test').
        timeout_seconds: Maximum allowed execution time in seconds.
    """
    return execute_test_suite(
        repo_path=repo_path,
        test_command=test_command,
        timeout_seconds=timeout_seconds,
    )


def main() -> None:
    """Entry point for running the DepShift MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
