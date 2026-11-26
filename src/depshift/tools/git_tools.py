"""Git safety inspection, branch management, and commit tools for DepShift."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import git


def check_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Inspects the git status of a repository to verify it is clean and safe for modifications.

    Args:
        repo_path: Path to the target git repository (defaults to current directory).

    Returns:
        Structured dictionary indicating whether repository exists, is valid git,
        working tree cleanliness, active branch, and lists of modified/untracked files.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        return {
            "exists": False,
            "is_git_repo": False,
            "is_clean": False,
            "active_branch": None,
            "uncommitted_files": [],
            "untracked_files": [],
            "error": f"Path '{repo_path}' does not exist.",
        }

    try:
        repo = git.Repo(path, search_parent_directories=True)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        return {
            "exists": True,
            "is_git_repo": False,
            "is_clean": False,
            "active_branch": None,
            "uncommitted_files": [],
            "untracked_files": [],
            "error": f"Directory '{path}' is not a valid git repository.",
        }

    try:
        active_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD"
    except Exception:
        active_branch = None

    # Check for staged or unstaged changes
    uncommitted_files: List[str] = [item.a_path for item in repo.index.diff(None)]
    try:
        uncommitted_files.extend([item.a_path for item in repo.index.diff("HEAD")])
    except Exception:
        # Repository has no commits yet
        pass
    uncommitted_files = sorted(list(set(filter(None, uncommitted_files))))

    untracked_files: List[str] = sorted(repo.untracked_files)
    is_clean = len(uncommitted_files) == 0 and len(untracked_files) == 0

    return {
        "exists": True,
        "is_git_repo": True,
        "is_clean": is_clean,
        "repo_root": str(repo.working_tree_dir),
        "active_branch": active_branch,
        "uncommitted_files": uncommitted_files,
        "untracked_files": untracked_files,
        "error": None,
    }


def create_migration_branch(
    repo_path: str = ".",
    package_name: str = "",
    target_version: str = "",
    branch_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates and checks out a new git branch for the migration work.

    Args:
        repo_path: Path to target git repository.
        package_name: Name of package being upgraded (e.g. 'pydantic').
        target_version: Target version (e.g. '2.0.0').
        branch_name: Optional custom branch name override.

    Returns:
        Structured result with active branch name and previous branch.
    """
    path = Path(repo_path).resolve()
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except Exception as e:
        return {
            "success": False,
            "branch_name": None,
            "previous_branch": None,
            "error": f"Invalid git repository: {e}",
        }

    try:
        previous_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD"
    except Exception:
        previous_branch = None

    if not branch_name:
        clean_pkg = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", package_name.strip()).strip("-")
        clean_ver = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", target_version.strip()).strip("-")
        if clean_pkg and clean_ver:
            branch_name = f"depshift/upgrade-{clean_pkg}-v{clean_ver}"
        elif clean_pkg:
            branch_name = f"depshift/upgrade-{clean_pkg}"
        else:
            branch_name = "depshift/migration"

    try:
        # Check if branch exists
        existing_branches = [b.name for b in repo.branches]
        if branch_name in existing_branches:
            repo.git.checkout(branch_name)
        else:
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

        return {
            "success": True,
            "branch_name": branch_name,
            "previous_branch": previous_branch,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "branch_name": branch_name,
            "previous_branch": previous_branch,
            "error": f"Failed to create or checkout branch '{branch_name}': {e}",
        }


def commit_migration_step(
    repo_path: str = ".",
    message: str = "chore(depshift): automated migration step",
    files_to_commit: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Stages files and creates a git commit for an intermediate migration step.

    Args:
        repo_path: Path to target git repository.
        message: Informative commit message.
        files_to_commit: Optional explicit list of file paths to stage.

    Returns:
        Structured result with commit hash and committed files.
    """
    path = Path(repo_path).resolve()
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except Exception as e:
        return {
            "success": False,
            "commit_sha": None,
            "files_committed": [],
            "error": f"Invalid git repository: {e}",
        }

    try:
        if files_to_commit:
            repo.index.add(files_to_commit)
        else:
            # Stage all untracked and modified files
            repo.git.add(A=True)

        # Check if there is anything to commit
        has_staged_diff = False
        try:
            has_staged_diff = bool(repo.index.diff("HEAD"))
        except Exception:
            # First commit
            has_staged_diff = True

        if not has_staged_diff and not repo.untracked_files:
            return {
                "success": False,
                "commit_sha": None,
                "files_committed": [],
                "error": "Nothing to commit, working tree is clean.",
            }

        commit = repo.index.commit(message)
        parent = commit.parents[0] if commit.parents else None
        if parent:
            committed_files = [item.a_path for item in parent.diff(commit)]
        else:
            committed_files = [item.path for item in commit.tree.traverse() if item.type == "blob"]

        return {
            "success": True,
            "commit_sha": commit.hexsha,
            "commit_short_sha": commit.hexsha[:7],
            "message": message,
            "files_committed": committed_files,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "commit_sha": None,
            "files_committed": [],
            "error": f"Failed to commit changes: {e}",
        }
