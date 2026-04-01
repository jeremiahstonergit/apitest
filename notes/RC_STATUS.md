# Repository status

Date: 2026-04-01

## Current status

- Repository is production-usable for agentic coding under controlled rollout.
- Repository is update-ready: raw snapshot changes can be imported or rebuilt through `scripts/update_repo.py`.
- Generated artifacts are now treated as rebuildable outputs, not hand-edited files.

## Update entry points

- `python3 scripts/update_repo.py --rebuild-only`
- `python3 scripts/update_repo.py --source-dir /path/to/snapshot`
- `python3 scripts/update_repo.py --source-archive /path/to/snapshot.tar.gz`

## CI/release

- CI rebuilds the repository from current raw sources and validates consistency.
- Release workflow rebuilds artifacts and packages a versioned tarball on tag push.
