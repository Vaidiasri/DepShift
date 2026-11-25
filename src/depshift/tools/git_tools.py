"""Git safety inspection tools for DepShift."""

from pathlib import Path
from typing import Any, Dict, List
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
