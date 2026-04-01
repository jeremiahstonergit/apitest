# RC4 Focused Hardening

Date: 2026-04-01

## Scope delivered

1. Claude tuning hygiene
- Removed speculative `.claude/settings.json`.
- Added `.claude/README.md` and kept `CLAUDE.md` as canonical instruction source.

2. Validator upgrade (request + response + transport consistency)
- `scripts/validate_mvp.py` now validates:
  - request examples against request params schema,
  - response examples against result schema,
  - projection↔transport upstream path consistency,
  - operationId uniqueness.

3. MCP expansion
- Added tools:
  - `list_operations_by_namespace`
  - `resolve_transport_call`
- Existing tools preserved:
  - `search_operation`, `get_schema`, `get_example`

4. Coverage expansion
- Build limit increased to 120 (`TARGET_METHODS = 120`).
- Current generated surface: **121 operations** (including auth operation).

5. Schema tightening pass
- `scripts/tighten_results_from_examples.py` updated and applied.
- Latest run tightened **42 weak result schemas** for 121 ops.

## Validation run

```bash
python3 scripts/build_mvp.py --limit 120
python3 scripts/tighten_results_from_examples.py
python3 scripts/validate_mvp.py
```

Result:
- `VALIDATION OK`
- `Checked operations: 121`

## Notes
- Response validation intentionally allows nullable/missing variability in examples while still checking core type consistency.
- Transport spec remains object-endpoint executable contract by design; projection spec remains virtual planning layer.
