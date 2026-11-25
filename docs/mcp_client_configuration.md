# DepShift MCP Client Configuration Guide

To connect **DepShift MCP Server** to your AI client (Claude Desktop, Cursor, or any MCP-compatible environment), use the following configuration snippets.

---

## 1. Claude Desktop Configuration

Open your Claude Desktop configuration file:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add `depshift` to the `mcpServers` object:

```json
{
  "mcpServers": {
    "depshift": {
      "command": "d:\\depshift\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "depshift.server"
      ]
    }
  }
}
```

> **Note:** If you run with uv or in a different environment, specify the full path to your virtual environment Python binary.

---

## 2. Cursor IDE Configuration

1. In Cursor, open **Settings** (`Ctrl+,` or `Cmd+,`).
2. Navigate to **Features** $\rightarrow$ **MCP**.
3. Click **Add New MCP Server**:
   - **Name:** `depshift`
   - **Type:** `command`
   - **Command:** `d:\depshift\.venv\Scripts\python.exe -m depshift.server`

---

## 3. Testing the Connection

Once configured and the client is restarted, ask your client:
> *"Call ping or get_version from depshift MCP"*

You should receive:
- `ping`: `"pong"`
- `get_version`: JSON payload containing version `0.1.0`, Python version, and OS platform.
