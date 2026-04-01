# Update process

## Source of truth

Do not edit generated artifacts manually.

Generated artifacts:

- `spec/openapi.llm-projection.yaml`
- `spec/openapi.transport.yaml`
- `examples/examples.jsonl`
- `client/python/operations.generated.json`
- `client/ts/operations.generated.json`
- `notes/update-summary.latest.json`
- `notes/update-summary.latest.md`
- `sources/manifest.json`

Hand-written layer:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/**`
- `.cursor/**`
- `.windsurf/**`
- `README.md`
- `docs/**`
- `mcp/**`
- `client/python/transport.py`
- `client/ts/transport.ts`
- `scripts/**`

Raw upstream sources:

- `notes/raw/schema/openrpc*.json`
- optional auth snippets in `notes/raw/`

## Recommended update flow

### A. Rebuild from current raw sources

Use this when raw OpenRPC files are already updated in the repository.

```bash
python3 scripts/update_repo.py --rebuild-only
```

### B. Import a new snapshot directory

Use this when you received a folder with fresh `openrpc*.json` files.

```bash
python3 scripts/update_repo.py --source-dir /path/to/snapshot
```

### C. Import a new snapshot archive

Use this when you received an archive from the API team.

```bash
python3 scripts/update_repo.py --source-archive /path/to/snapshot.tar.gz
```

## What the update script does

1. Optionally imports new raw snapshot files into `notes/raw/schema/`
2. Rebuilds projection and transport specs
3. Rebuilds examples
4. Rebuilds Python and TypeScript operation maps
5. Tightens weak response schemas from examples
6. Validates the repository state
7. Updates `sources/manifest.json`
8. Writes `notes/update-summary.latest.json` and `.md`

## Review checklist after update

- Check `notes/update-summary.latest.md`
- Check added/removed/changed operations
- Inspect generated spec diff
- Inspect auth flow if upstream auth changed
- Run smoke tests if test credentials are available
- Merge only after CI passes

## Versioning guidance

PATCH:
- schema fixes
- example cleanup
- documentation updates
- CI/tooling fixes

MINOR:
- new methods
- new namespaces
- additional optional fields
- broader API coverage

MAJOR:
- breaking transport changes
- auth flow changes
- removed or renamed operations
- incompatible method semantics
