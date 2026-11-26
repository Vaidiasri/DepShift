"""Unit tests for report_tools."""

from pathlib import Path
import git
import pytest

from depshift.tools.report_tools import generate_migration_summary


def test_generate_migration_summary_non_git():
    """Verify non-git path returns error gracefully."""
    res = generate_migration_summary("D:/non_existent_path_xyz")
    assert res["success"] is False
    assert "Invalid git repository" in res["error"]


def test_generate_migration_summary_git_repo(tmp_path: Path):
    """Verify markdown report generation with git diff."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Tester").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Initial file
    f = tmp_path / "app.py"
    f.write_text("print('version 1')\n", encoding="utf-8")
    repo.index.add(["app.py"])
    repo.index.commit("Initial commit")

    # Modify file
    f.write_text("print('version 2 upgraded')\n", encoding="utf-8")
    repo.index.add(["app.py"])
    repo.index.commit("Upgrade package")

    res = generate_migration_summary(
        str(tmp_path),
        package_name="test-lib",
        from_version="1.0.0",
        to_version="2.0.0",
        test_suite_status="passed",
    )
    assert res["success"] is True
    assert "test-lib" in res["markdown_report"]
    assert "1.0.0 → 2.0.0" in res["markdown_report"]
    assert "✅ **PASSED**" in res["markdown_report"]
    assert "app.py" in res["modified_files"]
