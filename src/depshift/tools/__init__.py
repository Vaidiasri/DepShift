"""DepShift tool modules."""

from depshift.tools.git_tools import check_git_status
from depshift.tools.manifest_tools import inspect_dependencies, bump_dependency_version
from depshift.tools.test_runner_tools import run_baseline_test, execute_test_suite
from depshift.tools.doc_tools import fetch_release_notes, extract_breaking_changes
from depshift.tools.patch_tools import read_source_file, apply_code_patch

__all__ = [
    "check_git_status",
    "inspect_dependencies",
    "bump_dependency_version",
    "run_baseline_test",
    "execute_test_suite",
    "fetch_release_notes",
    "extract_breaking_changes",
    "read_source_file",
    "apply_code_patch",
]
