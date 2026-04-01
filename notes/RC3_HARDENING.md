# RC3 Hardening Summary

Date: 2026-04-01

## Completed

1. Validator v2
- Added strict nullability checks (null rejected unless nullable).
- Added required field checks.
- Added enum/type/array item validation.
- Result: catches invalid examples like `id: null` for non-nullable string params.

2. Weak result schemas tightening
- Added `scripts/tighten_results_from_examples.py`.
- Auto-infers result schema from examples for weak operations.
- Run result (current): tightened 22 weak result schemas.

3. Tool-native tuning
- Added `.claude/settings.json`.
- Added Copilot path-specific instructions:
  - `.github/instructions/python.instructions.md`
  - `.github/instructions/typescript.instructions.md`

4. Minimal MCP server
- Added `mcp/server.py` with tools:
  - `search_operation`
  - `get_schema`
  - `get_example`
- Added `mcp/README.md`.

5. CI update
- `.github/workflows/validate.yml` now runs:
  1) build
  2) tighten
  3) validate

## Verified commands

```bash
python3 scripts/build_mvp.py --limit 60
python3 scripts/tighten_results_from_examples.py
python3 scripts/validate_mvp.py
```

Expected:
- `Tightened 22 weak result schemas`
- `VALIDATION OK`
- `Checked operations: 61`
