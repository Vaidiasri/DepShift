"""Unit tests for patch_tools."""

from pathlib import Path
import pytest
from depshift.tools.patch_tools import read_source_file, apply_code_patch


def test_read_source_file_full(tmp_path: Path):
    """Verify read_source_file reads whole file with line numbering."""
    file = tmp_path / "sample.py"
    file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    res = read_source_file(str(file))
    assert res["success"] is True
    assert res["total_lines"] == 2
    assert "1 | def hello():" in res["numbered_content"]
    assert "2 |     return 'world'" in res["numbered_content"]


def test_read_source_file_range(tmp_path: Path):
    """Verify read_source_file slices specific line ranges."""
    file = tmp_path / "sample.py"
    file.write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")

    res = read_source_file(str(file), start_line=2, end_line=4)
    assert res["success"] is True
    assert res["start_line"] == 2
    assert res["end_line"] == 4
    assert res["raw_content"] == "line2\nline3\nline4"


def test_read_source_file_not_found():
    """Verify non-existent file returns success=False."""
    res = read_source_file("non_existent_file_xyz.py")
    assert res["success"] is False
    assert "does not exist" in res["error"]


def test_apply_code_patch_success(tmp_path: Path):
    """Verify precision patch replaces target block exactly."""
    file = tmp_path / "models.py"
    file.write_text("from pydantic import BaseModel\n\nclass User(BaseModel):\n    name: str\n", encoding="utf-8")

    target = "from pydantic import BaseModel"
    replacement = "from pydantic import BaseModel, Field"

    res = apply_code_patch(str(file), target, replacement)
    assert res["success"] is True
    assert res["occurrences"] == 1
    assert file.read_text(encoding="utf-8") == "from pydantic import BaseModel, Field\n\nclass User(BaseModel):\n    name: str\n"


def test_apply_code_patch_target_not_found(tmp_path: Path):
    """Verify unmatched target returns helpful error without corrupting file."""
    file = tmp_path / "models.py"
    original = "x = 1\ny = 2\n"
    file.write_text(original, encoding="utf-8")

    res = apply_code_patch(str(file), "z = 99", "z = 100")
    assert res["success"] is False
    assert "was not found" in res["error"]
    assert file.read_text(encoding="utf-8") == original


def test_apply_code_patch_empty_target(tmp_path: Path):
    """Verify empty target is rejected."""
    file = tmp_path / "dummy.txt"
    file.write_text("content", encoding="utf-8")
    res = apply_code_patch(str(file), "", "replacement")
    assert res["success"] is False
    assert "cannot be empty" in res["error"]
