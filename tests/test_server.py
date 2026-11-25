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
    """Verify the FastMCP server instance is correctly initialized with registered tools."""
    assert mcp.name == "depshift"
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "ping" in tool_names
    assert "get_version" in tool_names
