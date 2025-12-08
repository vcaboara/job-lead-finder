# Automated Versioning Workflow

## Overview

This project uses automated semantic versioning through GitHub Actions. When a PR is merged to `main`, the version is automatically bumped and a git tag is created.

## Version Bump Rules

The version bump type is determined by:

### Major Version (x.0.0)
- PR has label `major`
- PR title contains `BREAKING CHANGE`

### Minor Version (0.x.0)
- PR has label `minor`
- PR title starts with `feat:` or `feat(`
- Default for feature additions

### Patch Version (0.0.x)
- All other PRs (fixes, chores, docs, refactors)
- Default bump type

## Workflow

1. **Create PR** with descriptive title using conventional commits:
   - `feat: Add new feature` → Minor bump
   - `fix: Fix bug` → Patch bump
   - `docs: Update documentation` → Patch bump
   - `refactor: Improve code` → Patch bump
   - `chore: Update dependencies` → Patch bump

2. **Add Labels** (optional) to override default behavior:
   - `major` → Force major version bump
   - `minor` → Force minor version bump

3. **Merge PR** to main:
   - GitHub Action automatically:
     - Determines version bump type
     - Updates `pyproject.toml`
     - Creates git commit with version bump
     - Creates git tag `vX.Y.Z`
     - Pushes tag to GitHub
     - Creates GitHub Release with notes

## Manual Versioning

If you need to manually create a version:

```bash
# Update version in pyproject.toml
# Then create tag
git tag -a v0.15.0 -m "Release v0.15.0: Description"
git push origin v0.15.0
```

## Version History

See all versions:
```bash
git tag -l
```

See version details:
```bash
git show v0.14.0
```

## Current Version

The current version is always in `pyproject.toml`:
```bash
grep "^version" pyproject.toml
```

## Example PR Titles

- `feat: Add resume upload feature` → v0.13.0 → v0.14.0
- `fix: Resolve CSS variable bug` → v0.14.0 → v0.14.1
- `docs: Update README` → v0.14.1 → v0.14.2
- `feat!: BREAKING CHANGE: Redesign API` → v0.14.2 → v1.0.0
- `refactor: Improve code quality` → v1.0.0 → v1.0.1

## Troubleshooting

### Version Not Bumped
- Check if PR was merged (not closed without merging)
- Check GitHub Actions logs for errors
- Verify PR title follows conventions

### Wrong Version Bump
- Use labels `major` or `minor` to override
- Update PR title to match convention before merging

### Manual Fix Required
If automation fails:
```bash
# Checkout main
git checkout main
git pull

# Update pyproject.toml version manually
# Commit and tag
git add pyproject.toml
git commit -m "chore: bump version to vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push && git push origin vX.Y.Z
```
