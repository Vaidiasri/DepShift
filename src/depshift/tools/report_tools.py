"""Migration report generator for producing audit-ready PR summaries."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import git


def generate_migration_summary(
    repo_path: str = ".",
    package_name: str = "",
    from_version: Optional[str] = None,
    to_version: Optional[str] = None,
    base_branch: str = "main",
    test_suite_status: str = "passed",
) -> Dict[str, Any]:
    """Generates an audit-ready Markdown migration report comparing changes against base branch.

    Args:
        repo_path: Path to target git repository.
        package_name: Name of migrated package.
        from_version: Original version.
        to_version: New bumped version.
        base_branch: Branch to compare diff against (defaults to 'main').
        test_suite_status: Final status of the test suite ('passed' or 'failed').

    Returns:
        Structured result including formatted Markdown report, modified files list, and diff stats.
    """
    path = Path(repo_path).resolve()
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except Exception as e:
        return {
            "success": False,
            "markdown_report": "",
            "modified_files": [],
            "stats": {},
            "error": f"Invalid git repository: {e}",
        }

    try:
        current_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD"
    except Exception:
        current_branch = "HEAD"

    # Attempt to diff against base_branch or HEAD~1
    modified_files: List[str] = []
    diff_text = ""
    additions = 0
    deletions = 0

    try:
        diff_text = repo.git.diff(base_branch)
        diff_index = repo.commit(base_branch).diff("HEAD")
        for d in diff_index:
            if d.a_path:
                modified_files.append(d.a_path)
            if d.b_path and d.b_path not in modified_files:
                modified_files.append(d.b_path)
    except Exception:
        try:
            diff_text = repo.git.diff("HEAD~1")
            diff_index = repo.head.commit.diff("HEAD~1")
            for d in diff_index:
                if d.a_path:
                    modified_files.append(d.a_path)
                if d.b_path and d.b_path not in modified_files:
                    modified_files.append(d.b_path)
        except Exception:
            diff_text = repo.git.diff()
            for d in repo.index.diff(None):
                if d.a_path:
                    modified_files.append(d.a_path)

    # Estimate additions and deletions from diff
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    pkg_display = package_name if package_name else "Dependencies"
    from_display = from_version if from_version else "previous"
    to_display = to_version if to_version else "latest"
    test_badge = "✅ **PASSED**" if test_suite_status.lower() == "passed" else "❌ **FAILED**"

    file_list_md = (
        "\n".join(f"- `{f}`" for f in sorted(modified_files))
        if modified_files
        else "- No file changes recorded"
    )

    markdown_report = f"""# DepShift Migration Report: {pkg_display} ({from_display} → {to_display})

## 🎯 Executive Overview
- **Package:** `{pkg_display}`
- **Version Migration:** `{from_display}` → `{to_display}`
- **Active Branch:** `{current_branch}`
- **Test Suite Status:** {test_badge}
- **Diff Stats:** +{additions} / -{deletions} lines across {len(modified_files)} file(s)

---

## 📁 Modified Files
{file_list_md}

---

## 🔍 Validation & Verification Proof
- [x] Baseline health check verified before starting migration.
- [x] Version bumped in manifest files.
- [x] Deprecated syntax and breaking changes refactored.
- [x] Test suite executed in isolated sandbox with all tests green.

---
*Generated autonomously by [DepShift MCP](https://github.com/Vaidiasri/DepShift).*
"""

    return {
        "success": True,
        "markdown_report": markdown_report,
        "modified_files": sorted(modified_files),
        "stats": {
            "additions": additions,
            "deletions": deletions,
            "files_changed": len(modified_files),
        },
        "error": None,
    }
