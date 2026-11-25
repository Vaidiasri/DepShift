"""Baseline test execution runner for DepShift with command safety guardrails."""

import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

# Allowed command prefixes to ensure no dangerous arbitrary code injection
ALLOWED_TEST_PREFIXES: List[str] = [
    "pytest",
    "python -m pytest",
    "py.test",
    "npm test",
    "npm run test",
    "npx vitest",
    "npx jest",
    "yarn test",
    "pnpm test",
    "cargo test",
    "go test",
]

# Disallowed dangerous shell characters
FORBIDDEN_CHARS = [";", "&", "|", "`", "$", ">", "<", "\n", "\r"]
MAX_OUTPUT_CHARS = 10000


def _is_safe_command(test_command: str) -> bool:
    """Verifies test command against the whitelist and checks for dangerous shell operators."""
    cmd_clean = test_command.strip()
    for char in FORBIDDEN_CHARS:
        if char in cmd_clean:
            return False

    return any(cmd_clean.startswith(prefix) for prefix in ALLOWED_TEST_PREFIXES)


def run_baseline_test(
    repo_path: str = ".",
    test_command: str = "pytest",
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Executes the repository's existing test suite to ensure tests pass before making upgrades.

    Args:
        repo_path: Directory of the target repository.
        test_command: Command to execute the test suite (e.g. 'pytest', 'npm test').
        timeout_seconds: Maximum execution time in seconds (defaults to 120s).

    Returns:
        Structured test result dictionary including pass/fail status, exit code,
        duration, stdout, and stderr.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        return {
            "success": False,
            "status": "error",
            "exit_code": -1,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": f"Repository directory '{repo_path}' does not exist.",
        }

    # Security check: whitelist validation
    if not _is_safe_command(test_command):
        return {
            "success": False,
            "status": "blocked",
            "exit_code": -1,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": (
                f"Command '{test_command}' was blocked by safety policy. "
                f"Allowed prefixes: {', '.join(ALLOWED_TEST_PREFIXES)}"
            ),
        }

    try:
        args = shlex.split(test_command, posix=False)
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "exit_code": -1,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": f"Failed to parse test command: {e}",
        }

    start_time = time.time()
    try:
        process = subprocess.run(
            args,
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration = round(time.time() - start_time, 2)
        success = process.returncode == 0
        stdout = process.stdout or ""
        stderr = process.stderr or ""

        # Bound output length to avoid flooding LLM token context
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n... [Truncated: {len(stdout) - MAX_OUTPUT_CHARS} characters]"
        if len(stderr) > MAX_OUTPUT_CHARS:
            stderr = stderr[:MAX_OUTPUT_CHARS] + f"\n... [Truncated: {len(stderr) - MAX_OUTPUT_CHARS} characters]"

        return {
            "success": success,
            "status": "passed" if success else "failed",
            "exit_code": process.returncode,
            "duration_seconds": duration,
            "stdout": stdout,
            "stderr": stderr,
        }

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        return {
            "success": False,
            "status": "timeout",
            "exit_code": -1,
            "duration_seconds": duration,
            "stdout": "",
            "stderr": f"Test execution timed out after {timeout_seconds} seconds.",
        }
    except FileNotFoundError as e:
        duration = round(time.time() - start_time, 2)
        return {
            "success": False,
            "status": "command_not_found",
            "exit_code": -1,
            "duration_seconds": duration,
            "stdout": "",
            "stderr": f"Command '{args[0]}' not found on host system: {e}",
        }
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return {
            "success": False,
            "status": "error",
            "exit_code": -1,
            "duration_seconds": duration,
            "stdout": "",
            "stderr": f"Unexpected execution failure: {e}",
        }
