# DepShift

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)

**DepShift** is an autonomous, context-aware dependency migration and security remediation agent packaged as a Model Context Protocol (MCP) server.

DepShift bridges the gap between *knowing* a dependency has breaking changes or vulnerabilities (Dependabot / Snyk) and *actually fixing the breaking code changes* required to upgrade it and pass the test suite.

---

## Architecture & Roadmap
Detailed documentation is maintained in the [`docs/`](file:///d:/depshift/docs) directory:
- [DepShift Architecture Specification](file:///d:/depshift/docs/depshift_architecture_spec.md)
- [Granular Feature & Subfeature Roadmap](file:///d:/depshift/docs/depshift_feature_roadmap.md)

---

## Installation & Setup

1. **Clone & Setup Virtual Environment:**
   ```powershell
   git clone <repo-url> depshift
   cd depshift
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e .[dev]
   ```

2. **Run Tests:**
   ```powershell
   pytest
   ```

3. **Run the MCP Server:**
   ```powershell
   python -m depshift.server
   ```
