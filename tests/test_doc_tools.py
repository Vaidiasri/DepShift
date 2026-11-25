"""Unit tests for doc_tools and breaking change intelligence."""

import pytest
import httpx
from depshift.tools.doc_tools import (
    extract_breaking_changes,
    fetch_release_notes,
    _extract_github_owner_repo,
)

SAMPLE_MARKDOWN_WITH_BREAKING = """
# Release v2.0.0

## Features
- Added new fast parser
- Support for Python 3.13

## Breaking Changes
- Method `old_parse()` was removed; use `parse()` instead.
- Renamed parameter `timeout_ms` to `timeout_seconds`.

## Migration Guide
Follow these steps to upgrade:
1. Replace all imports of `foo.legacy` with `foo.core`.
"""

SAMPLE_MARKDOWN_WITHOUT_BREAKING = """
# Release v1.1.1
## Bugfixes
- Fixed minor typo in error message.
- Improved documentation styling.
"""


def test_extract_breaking_changes_positive():
    """Verify breaking change headers and migration sections are extracted."""
    result = extract_breaking_changes(SAMPLE_MARKDOWN_WITH_BREAKING)
    assert result["has_breaking_changes"] is True
    assert len(result["extracted_sections"]) >= 2
    titles = [s["title"].lower() for s in result["extracted_sections"]]
    assert any("breaking" in t for t in titles)
    assert any("migration" in t for t in titles)
    assert "old_parse()" in result["summary"]


def test_extract_breaking_changes_negative():
    """Verify release notes without breaking changes are reported accurately."""
    result = extract_breaking_changes(SAMPLE_MARKDOWN_WITHOUT_BREAKING)
    assert result["has_breaking_changes"] is False
    assert len(result["extracted_sections"]) == 0
    assert "No explicit breaking changes" in result["summary"]


def test_extract_breaking_changes_empty():
    """Verify empty or None inputs return graceful results."""
    assert extract_breaking_changes("")["has_breaking_changes"] is False
    assert extract_breaking_changes("   ")["has_breaking_changes"] is False


def test_extract_github_owner_repo():
    """Verify GitHub owner/repo parsing from URLs."""
    assert _extract_github_owner_repo("https://github.com/pydantic/pydantic") == "pydantic/pydantic"
    assert _extract_github_owner_repo("https://github.com/fastmcp/fastmcp.git") == "fastmcp/fastmcp"
    assert _extract_github_owner_repo("git+https://github.com/expressjs/express") == "expressjs/express"
    assert _extract_github_owner_repo("https://google.com") is None
    assert _extract_github_owner_repo(None) is None


def test_fetch_release_notes_with_mock_client():
    """Verify fetch_release_notes works with a mock client returning PyPI and GitHub data."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "pypi.org" in url:
            return httpx.Response(
                200,
                json={
                    "info": {
                        "name": "example-lib",
                        "version": "2.0.0",
                        "description": SAMPLE_MARKDOWN_WITH_BREAKING,
                        "project_urls": {"Source": "https://github.com/example/example-lib"},
                    }
                },
            )
        elif "api.github.com" in url:
            return httpx.Response(
                200,
                json=[
                    {
                        "tag_name": "v2.0.0",
                        "body": "## Breaking Changes\n- Removed deprecated config.",
                    }
                ],
            )
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=mock_transport)

    res = fetch_release_notes("example-lib", client=client)
    assert res["package_name"] == "example-lib"
    assert res["error"] is None
    assert "GitHub Releases" in res["source"]
    assert res["breaking_changes"]["has_breaking_changes"] is True


def test_fetch_release_notes_not_found():
    """Verify graceful handling when package is not found."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=mock_transport)

    res = fetch_release_notes("non-existent-pkg-404", client=client)
    assert res["error"] is not None
    assert res["breaking_changes"]["has_breaking_changes"] is False
