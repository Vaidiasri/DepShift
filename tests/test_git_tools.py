"""Unit tests for git_tools."""

from pathlib import Path
import git
import pytest

from depshift.tools.git_tools import (
    check_git_status,
    create_migration_branch,
    commit_migration_step,
)


def test_git_status_current_repo():
    """Verify check_git_status correctly identifies the current workspace git repository."""
    status = check_git_status(".")
    assert status["exists"] is True
    assert status["is_git_repo"] is True
    assert status["active_branch"] == "main"
    assert status["error"] is None


def test_git_status_clean_repo(tmp_path: Path):
    """Verify check_git_status reports is_clean=True for a clean repo with committed files."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    file = tmp_path / "init.txt"
    file.write_text("initial commit", encoding="utf-8")
    repo.index.add(["init.txt"])
    repo.index.commit("Initial commit")

    status = check_git_status(str(tmp_path))
    assert status["exists"] is True
    assert status["is_git_repo"] is True
    assert status["is_clean"] is True
    assert len(status["uncommitted_files"]) == 0
    assert len(status["untracked_files"]) == 0


def test_git_status_non_existent_path():
    """Verify non-existent directory is handled gracefully."""
    status = check_git_status("D:/non_existent_folder_xyz_123")
    assert status["exists"] is False
    assert status["is_git_repo"] is False
    assert status["is_clean"] is False
    assert "does not exist" in status["error"]


def test_git_status_dirty_working_tree(tmp_path: Path):
    """Verify untracked and modified files are detected as not clean."""
    repo = git.Repo.init(tmp_path)
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello", encoding="utf-8")

    status = check_git_status(str(tmp_path))
    assert status["is_git_repo"] is True
    assert status["is_clean"] is False
    assert "file1.txt" in status["untracked_files"]


def test_create_migration_branch(tmp_path: Path):
    """Verify creating and checking out a dedicated migration branch."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    f = tmp_path / "a.txt"
    f.write_text("a", encoding="utf-8")
    repo.index.add(["a.txt"])
    repo.index.commit("Initial")

    res = create_migration_branch(str(tmp_path), package_name="pydantic", target_version="2.0.0")
    assert res["success"] is True
    assert res["branch_name"] == "depshift/upgrade-pydantic-v2.0.0"
    assert repo.active_branch.name == "depshift/upgrade-pydantic-v2.0.0"


def test_commit_migration_step(tmp_path: Path):
    """Verify committing modified files."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    f = tmp_path / "test.txt"
    f.write_text("v1", encoding="utf-8")
    repo.index.add(["test.txt"])
    repo.index.commit("init")

    # Modify
    f.write_text("v2", encoding="utf-8")
    res = commit_migration_step(str(tmp_path), message="upgrade to v2")
    assert res["success"] is True
    assert res["commit_sha"] is not None
    assert "test.txt" in res["files_committed"]
