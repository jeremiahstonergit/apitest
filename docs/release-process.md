# Release process

## Preconditions

- `python3 scripts/update_repo.py --rebuild-only` passes
- CI is green
- Generated artifacts and manifest are committed
- Update summary is reviewed

## Release steps

1. Update `CHANGELOG.md`
2. Create a tag using semantic versioning
3. Push the tag
4. Let GitHub Actions build the release archive
5. Attach release notes with:
   - operation count
   - added/removed/changed operations
   - any auth or transport changes

## Suggested release note structure

- Scope of update
- API coverage before/after
- Added operations
- Removed operations
- Changed operations
- Breaking changes
- Notes for agent users
