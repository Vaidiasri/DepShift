# DepShift MCP: Granular Feature & Subfeature Roadmap

To ensure you have full control over the codebase, we will develop and review the project in **5 modular chunks**. Each subfeature will be coded, tested, reviewed by you, and committed before moving forward.

---

## Chunk 1: Project Scaffolding & MCP Server Foundation
*Goal: Establish the repo structure, environment, and verify the MCP handshake with Claude Desktop / Cursor.*

* **Subfeature 1.1: Environment & Project Scaffolding**
  * `pyproject.toml` configuration with dependencies (`fastmcp`, `pydantic`, `gitpython`, `httpx`).
  * Directory layout (`src/depshift/`, `src/depshift/tools/`, `tests/`).
* **Subfeature 1.2: Base MCP Server Skeleton**
  * Core `server.py` setup using FastMCP.
  * Diagnostic `ping` / `get_version` tool.
* **Subfeature 1.3: MCP Client Connection Guide & Verification**
  * Config snippet for Claude Desktop (`claude_desktop_config.json`) and Cursor.
  * Local connection test to confirm the client sees the server.

---

## Chunk 2: Workspace Inspection & Baseline Health Check
*Goal: Prevent breaking code prematurely by enforcing git safety and verifying tests already pass.*

* **Subfeature 2.1: Git Safety Checker (`git_tools.py`)**
  * Tool: `check_git_status(repo_path)`
  * Verifies the repository exists, is a valid git repo, and has a clean working tree (no uncommitted changes).
* **Subfeature 2.2: Manifest & Dependency Inspector (`manifest_tools.py`)**
  * Tool: `inspect_dependencies(repo_path)`
  * Identifies project ecosystem (Python `pyproject.toml` / `requirements.txt` vs. Node `package.json`).
  * Parses installed packages and detects current versions.
* **Subfeature 2.3: Baseline Test Runner (`test_runner_tools.py`)**
  * Tool: `run_baseline_test(repo_path, test_command)`
  * Executes the existing test suite (`pytest`, `npm test`) with strict timeouts.
  * Returns structured status: passes, fails, or command not found.

---

## Chunk 3: Documentation & Changelog Intelligence
*Goal: Equip the agent with knowledge of breaking changes before modifying code.*

* **Subfeature 3.1: Release Notes & Changelog Fetcher (`doc_tools.py`)**
  * Tool: `fetch_release_notes(package_name, from_version, to_version, ecosystem)`
  * Fetches GitHub Releases, PyPI/npm release notes via API/HTTP.
* **Subfeature 3.2: Breaking Change Summarizer**
  * Extracts sections labeled "Breaking Changes", "Deprecated", "Removed", or "Migration Guide" to feed clean, minimal tokens to the LLM.

---

## Chunk 4: Dependency Bumping & Precision Code Patching
*Goal: Enable version updates and safe, targeted code refactoring.*

* **Subfeature 4.1: Dependency Bumper (`manifest_tools.py`)**
  * Tool: `bump_dependency_version(repo_path, package_name, target_version)`
  * Safely updates `pyproject.toml`, `requirements.txt`, or `package.json`.
* **Subfeature 4.2: Precision Code Patcher (`patch_tools.py`)**
  * Tool: `read_source_file(file_path, start_line, end_line)`
  * Tool: `apply_code_patch(file_path, target_block, replacement_block)`
  * Ensures exact match replacement without corrupting file encoding or whitespace.
* **Subfeature 4.3: Isolated Test Execution Harness (`test_runner_tools.py`)**
  * Tool: `execute_test_suite(repo_path, test_command)`
  * Returns detailed stderr, stdout, failing test file names, and exit codes.

---

## Chunk 5: Autonomous Loop & PR Lifecycle
*Goal: Automate branch creation, intermediate commits, and migration report generation.*

* **Subfeature 5.1: Git Branch & Commit Manager (`git_tools.py`)**
  * Tool: `create_migration_branch(repo_path, package_name, target_version)`
  * Tool: `commit_migration_step(repo_path, message)`
* **Subfeature 5.2: Migration Report Generator**
  * Tool: `generate_migration_summary(repo_path)`
  * Produces markdown diff report, listing files modified, breaking changes resolved, and final passing test output.
* **Subfeature 5.3: End-to-End Test with Real Example**
  * Verification on a sample repository upgrading a real breaking package (e.g., Pydantic v1 to v2).
