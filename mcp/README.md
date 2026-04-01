# MCP Server (minimal)

This repository includes a minimal stdio MCP server:

- `mcp/server.py`
- tools:
  - `search_operation`
  - `get_schema`
  - `get_example`
  - `list_operations_by_namespace`
  - `resolve_transport_call`

## Run locally

```bash
python mcp/server.py
```

## Suggested config snippets

### Codex / OpenClaw style
Use stdio command:

```json
{
  "command": "python",
  "args": ["/absolute/path/to/sweb-api-llm-spec/mcp/server.py"]
}
```

### GitHub Copilot coding agent (repo MCP)
Point repository MCP config to the same stdio command.

### Cursor/Windsurf
Add MCP server entry using stdio and the same script path.

## Notes
- This is a lightweight server for operation/schema/example lookup.
- It does not execute remote API calls directly.
- For execution use transport adapters in `client/python` or `client/ts`.
