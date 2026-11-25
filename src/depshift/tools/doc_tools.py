"""Changelog and release notes intelligence tools for DepShift."""

import re
from typing import Any, Dict, List, Optional
import httpx

BREAKING_PATTERNS = [
    r"breaking\s*(?:change|changes)?",
    r"migration\s*(?:guide|notes)?",
    r"deprecated|deprecation",
    r"removed|dropped",
    r"backward\s*incompatible",
    r"upgrade\s*guide",
]

COMPILED_BREAKING_REGEX = re.compile("|".join(BREAKING_PATTERNS), re.IGNORECASE)


def extract_breaking_changes(text: str) -> Dict[str, Any]:
    """Scans release notes or markdown documentation for breaking changes, deprecations, and migration guides.

    Args:
        text: Raw release notes or documentation markdown.

    Returns:
        Structured dictionary containing extracted sections, bullet items, and a consolidated summary.
    """
    if not text or not text.strip():
        return {
            "has_breaking_changes": False,
            "extracted_sections": [],
            "summary": "No release notes content provided.",
        }

    lines = text.splitlines()
    extracted_sections: List[Dict[str, Any]] = []
    current_section_title = "General"
    current_section_lines: List[str] = []
    is_capturing = False

    for line in lines:
        stripped = line.strip()
        # Check if line is a markdown heading
        if stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip()
            if COMPILED_BREAKING_REGEX.search(heading_text):
                # Save previous if captured
                if is_capturing and current_section_lines:
                    extracted_sections.append({
                        "title": current_section_title,
                        "content": "\n".join(current_section_lines).strip(),
                    })
                    current_section_lines = []
                current_section_title = heading_text
                is_capturing = True
            else:
                if is_capturing and current_section_lines:
                    extracted_sections.append({
                        "title": current_section_title,
                        "content": "\n".join(current_section_lines).strip(),
                    })
                    current_section_lines = []
                is_capturing = False
        elif is_capturing:
            current_section_lines.append(line)
        else:
            # Check individual bullet points if outside a dedicated breaking header
            if stripped.startswith(("-", "*", "•")) and COMPILED_BREAKING_REGEX.search(stripped):
                extracted_sections.append({
                    "title": "Inline Warning",
                    "content": stripped,
                })

    # Flush final section if still capturing
    if is_capturing and current_section_lines:
        extracted_sections.append({
            "title": current_section_title,
            "content": "\n".join(current_section_lines).strip(),
        })

    has_breaking = len(extracted_sections) > 0
    if has_breaking:
        summary_parts = [f"### {sec['title']}\n{sec['content']}" for sec in extracted_sections]
        summary = "\n\n".join(summary_parts)
    else:
        summary = "No explicit breaking changes or deprecations identified in release notes."

    return {
        "has_breaking_changes": has_breaking,
        "extracted_sections": extracted_sections,
        "summary": summary,
    }


def _extract_github_owner_repo(repo_url: Optional[str]) -> Optional[str]:
    """Helper to extract 'owner/repo' from a GitHub URL."""
    if not repo_url:
        return None
    match = re.search(r"github\.com/([^/]+)/([^/#\s\.]+)", repo_url)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None


def fetch_release_notes(
    package_name: str,
    from_version: Optional[str] = None,
    to_version: Optional[str] = None,
    ecosystem: str = "python",
    github_repo: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """Fetches changelogs or release notes for a package from PyPI, npm, or GitHub Releases.

    Args:
        package_name: Name of package (e.g. 'pydantic', 'fastmcp', 'express').
        from_version: Currently installed version.
        to_version: Target version upgrading to.
        ecosystem: 'python' or 'node'.
        github_repo: Optional 'owner/repo' override (e.g. 'pydantic/pydantic').
        client: Optional httpx Client (useful for dependency injection in tests).

    Returns:
        Structured dictionary containing raw release notes, detected source, and extracted breaking changes.
    """
    pkg_clean = package_name.strip()
    eco_clean = ecosystem.lower().strip()
    close_client = False
    if client is None:
        client = httpx.Client(timeout=10.0, follow_redirects=True)
        close_client = True

    raw_notes = ""
    source = "unknown"
    resolved_github_repo = github_repo

    try:
        if eco_clean == "python":
            pypi_url = f"https://pypi.org/pypi/{pkg_clean}/json"
            response = client.get(pypi_url)
            if response.status_code == 200:
                data = response.json()
                info = data.get("info", {})
                raw_notes = info.get("description", "")
                source = f"PyPI ({info.get('version', '')})"
                # Try finding github repo from project urls
                if not resolved_github_repo:
                    urls = info.get("project_urls") or {}
                    for u in urls.values():
                        gh = _extract_github_owner_repo(u)
                        if gh:
                            resolved_github_repo = gh
                            break
                    if not resolved_github_repo:
                        resolved_github_repo = _extract_github_owner_repo(info.get("home_page"))

        elif eco_clean in ("node", "javascript", "npm"):
            npm_url = f"https://registry.npmjs.org/{pkg_clean}"
            response = client.get(npm_url)
            if response.status_code == 200:
                data = response.json()
                raw_notes = data.get("readme", "")
                latest_ver = data.get("dist-tags", {}).get("latest", "")
                source = f"npm ({latest_ver})"
                if not resolved_github_repo:
                    repo_info = data.get("repository", {})
                    repo_url = repo_info.get("url") if isinstance(repo_info, dict) else str(repo_info)
                    resolved_github_repo = _extract_github_owner_repo(repo_url)

        # If a GitHub repo was discovered or provided, attempt to fetch GitHub Releases notes
        if resolved_github_repo:
            gh_url = f"https://api.github.com/repos/{resolved_github_repo}/releases"
            gh_resp = client.get(
                gh_url,
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "DepShift-MCP"},
            )
            if gh_resp.status_code == 200:
                releases = gh_resp.json()
                if isinstance(releases, list) and releases:
                    gh_notes_list = []
                    for rel in releases[:5]:
                        tag = rel.get("tag_name", "Release")
                        body = rel.get("body", "")
                        gh_notes_list.append(f"## Version {tag}\n{body}")
                    raw_notes = "\n\n".join(gh_notes_list)
                    source = f"GitHub Releases ({resolved_github_repo})"

        if not raw_notes:
            return {
                "package_name": pkg_clean,
                "from_version": from_version,
                "to_version": to_version,
                "source": "none",
                "raw_notes": "",
                "breaking_changes": {
                    "has_breaking_changes": False,
                    "extracted_sections": [],
                    "summary": f"Could not locate release notes or documentation for package '{pkg_clean}'.",
                },
                "error": f"No release notes found for '{pkg_clean}'.",
            }

        breaking = extract_breaking_changes(raw_notes)

        return {
            "package_name": pkg_clean,
            "from_version": from_version,
            "to_version": to_version,
            "source": source,
            "raw_notes_preview": raw_notes[:2000] if len(raw_notes) > 2000 else raw_notes,
            "breaking_changes": breaking,
            "error": None,
        }

    except Exception as e:
        return {
            "package_name": pkg_clean,
            "from_version": from_version,
            "to_version": to_version,
            "source": "error",
            "raw_notes_preview": "",
            "breaking_changes": {
                "has_breaking_changes": False,
                "extracted_sections": [],
                "summary": f"Error occurred: {e}",
            },
            "error": str(e),
        }
    finally:
        if close_client:
            client.close()
