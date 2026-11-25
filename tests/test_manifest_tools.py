"""Unit tests for manifest_tools."""

import json
from pathlib import Path
import pytest
from depshift.tools.manifest_tools import (
    inspect_dependencies,
    bump_dependency_version,
    _parse_python_dep_string,
)


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


def test_bump_dependency_pyproject(tmp_path: Path):
    """Verify bump_dependency_version correctly updates pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\ndependencies = [\n    "fastmcp>=0.4.0",\n    "httpx",\n]\n',
        encoding="utf-8",
    )

    res = bump_dependency_version(str(tmp_path), "fastmcp", ">=2.0.0")
    assert res["success"] is True
    assert "pyproject.toml" in res["modified_files"]
    content = pyproject.read_text(encoding="utf-8")
    assert '"fastmcp>=2.0.0"' in content
    assert '"httpx"' in content


def test_bump_dependency_requirements_txt(tmp_path: Path):
    """Verify bump_dependency_version correctly updates requirements.txt."""
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.28.0\nflask>=2.0.0\n", encoding="utf-8")

    res = bump_dependency_version(str(tmp_path), "requests", "2.31.0")
    assert res["success"] is True
    assert "requirements.txt" in res["modified_files"]
    content = req.read_text(encoding="utf-8")
    assert "requests>=2.31.0" in content
    assert "flask>=2.0.0" in content


def test_bump_dependency_package_json(tmp_path: Path):
    """Verify bump_dependency_version correctly updates package.json."""
    pkg = tmp_path / "package.json"
    pkg.write_text(
        '{"dependencies": {"lodash": "^4.17.20"}}',
        encoding="utf-8",
    )

    res = bump_dependency_version(str(tmp_path), "lodash", "4.17.21")
    assert res["success"] is True
    assert "package.json" in res["modified_files"]
    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data["dependencies"]["lodash"] == "^4.17.21"


def test_bump_dependency_not_found(tmp_path: Path):
    """Verify bumping non-existent package returns error."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies = ["requests"]\n', encoding="utf-8")
    res = bump_dependency_version(str(tmp_path), "unknown-pkg", "1.0.0")
    assert res["success"] is False
    assert "not found in any manifest file" in res["error"]
