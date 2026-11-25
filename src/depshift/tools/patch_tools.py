"""Precision code reading and patch application tools for safe refactoring."""

from pathlib import Path
from typing import Any, Dict, Optional


def read_source_file(
    file_path: str,
    start_line: Optional[int] = 1,
    end_line: Optional[int] = None,
) -> Dict[str, Any]:
    """Reads a source code file with optional line-range boundaries and line numbering.

    Args:
        file_path: Absolute or relative path to the file.
        start_line: 1-indexed start line (defaults to 1).
        end_line: 1-indexed end line (defaults to end of file).

    Returns:
        Structured response with total lines, content, and line range.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return {
            "success": False,
            "file_path": str(file_path),
            "content": "",
            "total_lines": 0,
            "error": f"File '{file_path}' does not exist.",
        }

    if not path.is_file():
        return {
            "success": False,
            "file_path": str(file_path),
            "content": "",
            "total_lines": 0,
            "error": f"Path '{file_path}' is not a file.",
        }

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except Exception as e:
            return {
                "success": False,
                "file_path": str(file_path),
                "content": "",
                "total_lines": 0,
                "error": f"Unable to decode file '{file_path}': {e}",
            }

    lines = content.splitlines()
    total_lines = len(lines)

    s_line = max(1, start_line or 1)
    e_line = min(total_lines, end_line if end_line is not None else total_lines)

    if s_line > total_lines:
        slice_lines = []
    else:
        slice_lines = lines[s_line - 1 : e_line]

    # Form formatted line-numbered text
    numbered_lines = [
        f"{idx + s_line:4d} | {line}" for idx, line in enumerate(slice_lines)
    ]

    return {
        "success": True,
        "file_path": str(path),
        "total_lines": total_lines,
        "start_line": s_line,
        "end_line": e_line,
        "raw_content": "\n".join(slice_lines),
        "numbered_content": "\n".join(numbered_lines),
        "error": None,
    }


def apply_code_patch(
    file_path: str,
    target_block: str,
    replacement_block: str,
) -> Dict[str, Any]:
    """Applies a precision search-and-replace patch to a file.

    Requires target_block to match existing file content exactly (including whitespace/indentation).

    Args:
        file_path: Path to target file.
        target_block: Exact block of characters/lines to be replaced.
        replacement_block: Exact replacement string.

    Returns:
        Structured result indicating success, occurrences replaced, and error if unmatched.
    """
    path = Path(file_path).resolve()
    if not path.exists() or not path.is_file():
        return {
            "success": False,
            "file_path": str(file_path),
            "occurrences": 0,
            "error": f"File '{file_path}' does not exist or is not a file.",
        }

    if not target_block:
        return {
            "success": False,
            "file_path": str(file_path),
            "occurrences": 0,
            "error": "target_block cannot be empty.",
        }

    try:
        content = path.read_text(encoding="utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")
        encoding = "latin-1"

    # Normalize CRLF in memory to ensure match across platforms
    norm_content = content.replace("\r\n", "\n")
    norm_target = target_block.replace("\r\n", "\n")
    norm_replacement = replacement_block.replace("\r\n", "\n")

    occurrences = norm_content.count(norm_target)
    if occurrences == 0:
        return {
            "success": False,
            "file_path": str(file_path),
            "occurrences": 0,
            "error": "target_block was not found in the file. Ensure whitespace and indentation match exactly.",
        }

    # Perform replacement
    new_norm_content = norm_content.replace(norm_target, norm_replacement)

    # Preserve CRLF if original content had CRLF
    if "\r\n" in content:
        final_content = new_norm_content.replace("\n", "\r\n")
    else:
        final_content = new_norm_content

    path.write_text(final_content, encoding=encoding)

    return {
        "success": True,
        "file_path": str(path),
        "occurrences": occurrences,
        "error": None,
    }
