"""Tests for DepShift base MCP server and diagnostic tools."""

import pytest
from depshift import __version__
from depshift.server import ping, get_version, mcp


def test_ping():
    """Verify the diagnostic ping tool returns 'pong'."""
    assert ping() == "pong"


def test_get_version():
    """Verify get_version returns server metadata and current version."""
    info = get_version()
    assert isinstance(info, dict)
    assert info["name"] == "depshift"
    assert info["version"] == __version__
    assert "python_version" in info
    assert "platform" in info


@pytest.mark.asyncio
async def test_mcp_instance():
    """Verify the FastMCP server instance is correctly initialized with all registered tools."""
    assert mcp.name == "depshift"
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "ping",
        "get_version",
        "tool_check_git_status",
        "tool_inspect_dependencies",
        "tool_run_baseline_test",
        "tool_fetch_release_notes",
        "tool_extract_breaking_changes",
    ]
    for expected in expected_tools:
        assert expected in tool_names
