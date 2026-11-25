"""Manifest and dependency parser tools for DepShift (Python and Node.js ecosystems)."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import tomllib


def _parse_python_dep_string(dep_str: str) -> Tuple[str, str]:
    """Split a python requirement string into package name and version constraint.
    Example: 'fastmcp>=0.4.0' -> ('fastmcp', '>=0.4.0')
    """
    match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*(.*)$", dep_str.strip())
    if match:
        name = match.group(1).lower()
        constraint = match.group(2).strip()
        return name, constraint or "*"
    return dep_str.strip(), "*"


def _inspect_pyproject(path: Path) -> Dict[str, Any]:
    """Parse pyproject.toml dependencies."""
    deps: Dict[str, str] = {}
    dev_deps: Dict[str, str] = {}

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Standard PEP 621 dependencies
        project_data = data.get("project", {})
        for dep in project_data.get("dependencies", []):
            name, constraint = _parse_python_dep_string(dep)
            deps[name] = constraint

        optional_deps = project_data.get("optional-dependencies", {})
        for _, opt_list in optional_deps.items():
            for dep in opt_list:
                name, constraint = _parse_python_dep_string(dep)
                dev_deps[name] = constraint

        # Poetry dependencies
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for name, spec in poetry_deps.items():
            if name.lower() != "python":
                deps[name.lower()] = str(spec)

        poetry_dev = (
            data.get("tool", {})
            .get("poetry", {})
            .get("group", {})
            .get("dev", {})
            .get("dependencies", {})
        )
        for name, spec in poetry_dev.items():
            dev_deps[name.lower()] = str(spec)

        return {"deps": deps, "dev_deps": dev_deps, "error": None}
    except Exception as e:
        return {"deps": {}, "dev_deps": {}, "error": f"Failed to parse pyproject.toml: {e}"}


def _inspect_requirements(path: Path) -> Dict[str, Any]:
    """Parse requirements.txt dependencies."""
    deps: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                name, constraint = _parse_python_dep_string(line)
                deps[name] = constraint
        return {"deps": deps, "error": None}
    except Exception as e:
        return {"deps": {}, "error": f"Failed to parse requirements.txt: {e}"}


def _inspect_package_json(path: Path) -> Dict[str, Any]:
    """Parse package.json dependencies."""
    deps: Dict[str, str] = {}
    dev_deps: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        return {"deps": deps, "dev_deps": dev_deps, "error": None}
    except Exception as e:
        return {"deps": {}, "dev_deps": {}, "error": f"Failed to parse package.json: {e}"}


def inspect_dependencies(repo_path: str = ".") -> Dict[str, Any]:
    """Inspects manifest files in a repository and extracts dependencies across Python and Node.js.

    Args:
        repo_path: Path to target repository directory.

    Returns:
        Structured breakdown containing detected ecosystems, manifest files, dependencies,
        dev dependencies, and any parser warnings.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        return {
            "exists": False,
            "ecosystems": [],
            "manifest_files": [],
            "dependencies": {},
            "dev_dependencies": {},
            "error": f"Path '{repo_path}' does not exist.",
        }

    ecosystems: List[str] = []
    manifest_files: List[str] = []
    all_deps: Dict[str, str] = {}
    all_dev_deps: Dict[str, str] = {}
    warnings: List[str] = []

    # Check Python pyproject.toml
    pyproject_path = path / "pyproject.toml"
    if pyproject_path.exists():
        ecosystems.append("python")
        manifest_files.append("pyproject.toml")
        res = _inspect_pyproject(pyproject_path)
        all_deps.update(res["deps"])
        all_dev_deps.update(res["dev_deps"])
        if res["error"]:
            warnings.append(res["error"])

    # Check Python requirements.txt
    req_path = path / "requirements.txt"
    if req_path.exists():
        if "python" not in ecosystems:
            ecosystems.append("python")
        manifest_files.append("requirements.txt")
        res = _inspect_requirements(req_path)
        all_deps.update(res["deps"])
        if res["error"]:
            warnings.append(res["error"])

    # Check Node.js package.json
    pkg_path = path / "package.json"
    if pkg_path.exists():
        ecosystems.append("node")
        manifest_files.append("package.json")
        res = _inspect_package_json(pkg_path)
        all_deps.update(res["deps"])
        all_dev_deps.update(res["dev_deps"])
        if res["error"]:
            warnings.append(res["error"])

    ecosystems = sorted(list(set(ecosystems)))

    return {
        "exists": True,
        "ecosystems": ecosystems if ecosystems else ["unknown"],
        "manifest_files": manifest_files,
        "dependencies": all_deps,
        "dev_dependencies": all_dev_deps,
        "total_dependencies": len(all_deps),
        "total_dev_dependencies": len(all_dev_deps),
        "warnings": warnings,
        "error": None,
    }


def bump_dependency_version(
    repo_path: str,
    package_name: str,
    target_version: str,
) -> Dict[str, Any]:
    """Updates the specified package version in pyproject.toml, requirements.txt, or package.json.

    Args:
        repo_path: Path to repository root.
        package_name: Package name to upgrade.
        target_version: New version string (e.g. '2.0.0', '>=2.0.0', '^2.0.0').

    Returns:
        Structured result indicating success, modified files, and applied version specifier.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        return {
            "success": False,
            "modified_files": [],
            "package_name": package_name,
            "target_version": target_version,
            "error": f"Path '{repo_path}' does not exist.",
        }

    pkg_clean = package_name.strip()
    target_clean = target_version.strip()
    # Normalize version specifier if bare version provided
    py_spec = target_clean if any(target_clean.startswith(op) for op in ("==", ">=", "<=", "~=", "^")) else f">={target_clean}"
    node_spec = target_clean if any(target_clean.startswith(op) for op in ("^", "~", ">=", "<=", "=")) else f"^{target_clean}"

    modified_files: List[str] = []

    # 1. Check pyproject.toml
    pyproject_file = path / "pyproject.toml"
    if pyproject_file.exists():
        content = pyproject_file.read_text(encoding="utf-8")
        # Match "package" or 'package' with optional version constraints
        pattern = re.compile(rf"""(["']){re.escape(pkg_clean)}(?:[><=~!^][^"']*)?\1""", re.IGNORECASE)
        if pattern.search(content):
            new_content = pattern.sub(rf'\g<1>{pkg_clean}{py_spec}\g<1>', content)
            if new_content != content:
                pyproject_file.write_text(new_content, encoding="utf-8")
                modified_files.append("pyproject.toml")

    # 2. Check requirements.txt
    req_file = path / "requirements.txt"
    if req_file.exists():
        lines = req_file.read_text(encoding="utf-8").splitlines()
        new_lines: List[str] = []
        changed = False
        req_pattern = re.compile(rf"^{re.escape(pkg_clean)}(?:\s*[><=~!^].*)?$", re.IGNORECASE)
        for line in lines:
            if req_pattern.match(line.strip()):
                new_lines.append(f"{pkg_clean}{py_spec}")
                changed = True
            else:
                new_lines.append(line)
        if changed:
            req_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            modified_files.append("requirements.txt")

    # 3. Check package.json
    pkg_json_file = path / "package.json"
    if pkg_json_file.exists():
        try:
            data = json.loads(pkg_json_file.read_text(encoding="utf-8"))
            changed = False
            if "dependencies" in data and pkg_clean in data["dependencies"]:
                data["dependencies"][pkg_clean] = node_spec
                changed = True
            if "devDependencies" in data and pkg_clean in data["devDependencies"]:
                data["devDependencies"][pkg_clean] = node_spec
                changed = True
            if changed:
                pkg_json_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                modified_files.append("package.json")
        except Exception:
            pass

    if not modified_files:
        return {
            "success": False,
            "modified_files": [],
            "package_name": pkg_clean,
            "target_version": target_clean,
            "error": f"Package '{pkg_clean}' not found in any manifest file.",
        }

    return {
        "success": True,
        "modified_files": modified_files,
        "package_name": pkg_clean,
        "target_version": py_spec,
        "error": None,
    }
