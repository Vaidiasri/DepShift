"""Unit tests for manifest_tools."""

from pathlib import Path
import pytest
from depshift.tools.manifest_tools import inspect_dependencies, _parse_python_dep_string


def test_parse_python_dep_string():
    """Verify python requirement strings are parsed into name and constraint."""
    name, constraint = _parse_python_dep_string("fastmcp>=0.4.0")
    assert name == "fastmcp"
    assert constraint == ">=0.4.0"

    name, constraint = _parse_python_dep_string("requests")
    assert name == "requests"
    assert constraint == "*"


def test_inspect_current_repo():
    """Verify inspect_dependencies parses this repository's pyproject.toml."""
    info = inspect_dependencies(".")
    assert info["exists"] is True
    assert "python" in info["ecosystems"]
    assert "pyproject.toml" in info["manifest_files"]
    assert "fastmcp" in info["dependencies"]
    assert "pydantic" in info["dependencies"]
    assert "gitpython" in info["dependencies"]
    assert "httpx" in info["dependencies"]
    assert "pytest" in info["dev_dependencies"]
    assert info["total_dependencies"] >= 4
    assert info["error"] is None


def test_inspect_node_package_json(tmp_path: Path):
    """Verify inspect_dependencies correctly parses package.json."""
    pkg_file = tmp_path / "package.json"
    pkg_file.write_text(
        '{"dependencies": {"express": "^4.18.2"}, "devDependencies": {"jest": "^29.5.0"}}',
        encoding="utf-8",
    )
    info = inspect_dependencies(str(tmp_path))
    assert info["exists"] is True
    assert "node" in info["ecosystems"]
    assert "package.json" in info["manifest_files"]
    assert info["dependencies"]["express"] == "^4.18.2"
    assert info["dev_dependencies"]["jest"] == "^29.5.0"


def test_inspect_non_existent():
    """Verify non-existent directory returns appropriate error."""
    info = inspect_dependencies("D:/non_existent_folder_xyz_123")
    assert info["exists"] is False
    assert "does not exist" in info["error"]
