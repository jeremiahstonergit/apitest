# Contributing

## General rules

- Do not edit generated specs manually
- Update raw upstream snapshots first, then rebuild artifacts
- Keep commits focused: raw snapshot update, generator change, docs change

## Before opening a PR

Run:

```bash
python3 scripts/update_repo.py --rebuild-only
```

Then inspect:

- `notes/update-summary.latest.md`
- generated spec diffs
- operation maps
- examples
