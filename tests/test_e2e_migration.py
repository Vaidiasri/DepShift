"""End-to-End integration test verifying the autonomous dependency migration loop."""

from pathlib import Path
import git
import pytest

from depshift.tools.git_tools import check_git_status, create_migration_branch, commit_migration_step
from depshift.tools.manifest_tools import inspect_dependencies, bump_dependency_version
from depshift.tools.patch_tools import read_source_file, apply_code_patch
from depshift.tools.report_tools import generate_migration_summary


def test_e2e_autonomous_migration_loop(tmp_path: Path):
    """Simulates a full end-to-end migration lifecycle:
    1. Pre-flight check (git clean, manifest discovered)
    2. Branch creation
    3. Version bump in manifest
    4. Code inspection & precision refactoring
    5. Test suite verification
    6. Commit step & PR migration report generation
    """
    # Step 0: Scaffold a realistic target repository
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "DepShift Bot").release()
    repo.config_writer().set_value("user", "email", "bot@depshift.com").release()

    # Manifest with older version
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "my-service"\nversion = "1.0.0"\ndependencies = [\n    "pydantic>=1.10.0",\n]\n',
        encoding="utf-8",
    )

    # Legacy code using older deprecated API
    service_code = tmp_path / "service.py"
    service_code.write_text(
        '# Legacy Pydantic v1 model\n'
        'from pydantic import BaseModel, validator\n\n'
        'class UserModel(BaseModel):\n'
        '    name: str\n\n'
        '    @validator("name")\n'
        '    def check_name(cls, v):\n'
        '        return v.title()\n',
        encoding="utf-8",
    )

    # Initial commit to simulate main branch
    repo.index.add(["pyproject.toml", "service.py"])
    repo.index.commit("Initial commit on main")

    # --- Phase 1: Pre-flight & Git Safety Check ---
    status = check_git_status(str(tmp_path))
    assert status["is_git_repo"] is True
    assert status["is_clean"] is True

    manifest = inspect_dependencies(str(tmp_path))
    assert "pydantic" in manifest["dependencies"]
    assert "pyproject.toml" in manifest["manifest_files"]

    # --- Phase 2: Create Migration Branch ---
    branch_res = create_migration_branch(
        str(tmp_path),
        package_name="pydantic",
        target_version="2.0.0",
    )
    assert branch_res["success"] is True
    assert "depshift/upgrade-pydantic-v2.0.0" in branch_res["branch_name"]

    # --- Phase 3: Bump Dependency in Manifest ---
    bump_res = bump_dependency_version(
        str(tmp_path),
        package_name="pydantic",
        target_version=">=2.0.0",
    )
    assert bump_res["success"] is True
    assert "pyproject.toml" in bump_res["modified_files"]
    assert '"pydantic>=2.0.0"' in pyproject.read_text(encoding="utf-8")

    # --- Phase 4: Precision Code Patching (Refactor v1 @validator to v2 @field_validator) ---
    read_res = read_source_file(str(service_code), start_line=1, end_line=12)
    assert read_res["success"] is True
    assert "@validator" in read_res["raw_content"]

    target_code = (
        'from pydantic import BaseModel, validator\n\n'
        'class UserModel(BaseModel):\n'
        '    name: str\n\n'
        '    @validator("name")\n'
        '    def check_name(cls, v):'
    )
    replacement_code = (
        'from pydantic import BaseModel, field_validator\n\n'
        'class UserModel(BaseModel):\n'
        '    name: str\n\n'
        '    @field_validator("name")\n'
        '    @classmethod\n'
        '    def check_name(cls, v):'
    )
    patch_res = apply_code_patch(str(service_code), target_code, replacement_code)
    assert patch_res["success"] is True
    assert patch_res["occurrences"] == 1
    assert "@field_validator" in service_code.read_text(encoding="utf-8")

    # --- Phase 5: Commit Migration Step ---
    commit_res = commit_migration_step(
        str(tmp_path),
        message="feat(migration): upgrade pydantic to v2 and refactor validators",
    )
    assert commit_res["success"] is True
    assert commit_res["commit_sha"] is not None
    assert len(commit_res["files_committed"]) >= 2

    # --- Phase 6: Generate Migration Summary Report ---
    report_res = generate_migration_summary(
        str(tmp_path),
        package_name="pydantic",
        from_version="1.10.0",
        to_version="2.0.0",
        test_suite_status="passed",
    )
    assert report_res["success"] is True
    assert "pydantic (1.10.0 → 2.0.0)" in report_res["markdown_report"]
    assert "pyproject.toml" in report_res["modified_files"]
    assert "service.py" in report_res["modified_files"]
    assert "✅ **PASSED**" in report_res["markdown_report"]
