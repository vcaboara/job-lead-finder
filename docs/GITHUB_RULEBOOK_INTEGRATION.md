# GitHub Integration with Rulebook-AI

## Overview

GitHub can leverage rulebook-ai files to provide better AI-assisted code review, automated checks, and context-aware suggestions in pull requests.

## Current GitHub Copilot Integration

### `.github/copilot-instructions.md` ✅ Active

This file is **automatically read by GitHub Copilot** and provides:
- Project-specific coding standards
- Memory Bank system documentation
- Workflow modes (Planning/Implementation/Debugging)
- General software engineering principles

**How it works:**
- Generated from rulebook-ai packs via `python -m rulebook_ai project sync --assistant copilot`
- Read by Copilot in PR reviews, inline suggestions, and chat
- Updates automatically when memory files change and you resync

### `.github/COPILOT_TASK_ACTIVE.md` ✅ Active

Task files like this are referenced in PR descriptions using:
```markdown
@copilot Please implement the optimizations described in .github/COPILOT_TASK_ACTIVE.md
```

## Potential GitHub Actions Integration

### 1. Auto-Sync Rulebook on Memory Changes

Create `.github/workflows/rulebook-sync.yml`:

```yaml
name: Rulebook AI Sync

on:
  push:
    paths:
      - 'memory/docs/**'
      - 'memory/tasks/**'
    branches:
      - main

jobs:
  sync-rulebook:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --extra rulebook

      - name: Sync rulebook AI
        run: python -m rulebook_ai project sync --assistant copilot

      - name: Commit updated instructions
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .github/copilot-instructions.md
          git diff --quiet && git diff --staged --quiet || \
            git commit -m "chore: auto-sync rulebook AI instructions" && \
            git push
```

**Benefit**: Copilot instructions stay in sync with documentation changes

### 2. PR Context Validator

Ensure PRs update memory files when making architectural changes:

```yaml
name: Memory Documentation Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-memory-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check for architectural changes
        id: check_changes
        run: |
          # Check if src/app/ files changed
          if git diff --name-only origin/main...HEAD | grep -q "^src/app/"; then
            echo "code_changed=true" >> $GITHUB_OUTPUT
          fi

          # Check if memory files changed
          if git diff --name-only origin/main...HEAD | grep -q "^memory/"; then
            echo "memory_changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Validate memory updates
        if: steps.check_changes.outputs.code_changed == 'true' && steps.check_changes.outputs.memory_changed != 'true'
        run: |
          echo "::warning::Code changed but memory/ documentation not updated. Consider updating:"
          echo "  - memory/docs/architecture.md (for architectural changes)"
          echo "  - memory/docs/technical.md (for tech stack changes)"
          echo "  - memory/tasks/active_context.md (for current work context)"
```

**Benefit**: Reminds developers to keep AI context current

### 3. Profile-Based CI Checks

Run different test suites based on changed files:

```yaml
name: Smart CI

on: [push, pull_request]

jobs:
  determine-profile:
    runs-on: ubuntu-latest
    outputs:
      profile: ${{ steps.detect.outputs.profile }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect changed profile
        id: detect
        run: |
          if git diff --name-only HEAD~1 | grep -q "^src/app/templates/"; then
            echo "profile=frontend" >> $GITHUB_OUTPUT
          elif git diff --name-only HEAD~1 | grep -q "^src/app/.*\.py$"; then
            echo "profile=backend" >> $GITHUB_OUTPUT
          elif git diff --name-only HEAD~1 | grep -q "^tests/"; then
            echo "profile=testing" >> $GITHUB_OUTPUT
          elif git diff --name-only HEAD~1 | grep -q "Dockerfile\|docker-compose"; then
            echo "profile=docker" >> $GITHUB_OUTPUT
          else
            echo "profile=all" >> $GITHUB_OUTPUT
          fi

  test:
    needs: determine-profile
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run profile-specific tests
        run: |
          echo "Running tests for profile: ${{ needs.determine-profile.outputs.profile }}"
          # Run tests specific to the changed area
          case "${{ needs.determine-profile.outputs.profile }}" in
            frontend)
              pytest tests/test_ui_* -v
              ;;
            backend)
              pytest tests/test_*_provider.py tests/test_job_*.py -v
              ;;
            testing)
              pytest tests/ -v
              ;;
            *)
              pytest tests/ -v
              ;;
          esac
```

**Benefit**: Faster CI by running relevant tests first

### 4. Memory File Validation

Ensure memory files follow expected structure:

```yaml
name: Validate Memory Files

on:
  pull_request:
    paths:
      - 'memory/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check required memory files exist
        run: |
          required_files=(
            "memory/docs/product_requirement_docs.md"
            "memory/docs/architecture.md"
            "memory/docs/technical.md"
            "memory/tasks/tasks_plan.md"
            "memory/tasks/active_context.md"
          )

          missing=false
          for file in "${required_files[@]}"; do
            if [ ! -f "$file" ]; then
              echo "::error::Required memory file missing: $file"
              missing=true
            fi
          done

          if [ "$missing" = true ]; then
            exit 1
          fi

      - name: Validate markdown structure
        run: |
          # Check that files have proper headings
          for file in memory/docs/*.md memory/tasks/*.md; do
            if ! grep -q "^#" "$file"; then
              echo "::warning::$file has no markdown headings"
            fi
          done
```

**Benefit**: Ensures AI context files maintain quality

## GitHub Copilot Features Already Using Rulebook Files

### 1. Pull Request Summaries
Copilot reads `.github/copilot-instructions.md` when generating PR descriptions and understands:
- Project goals from PRD
- Architecture constraints
- Coding standards
- Current active context

### 2. Code Review Comments
When reviewing PRs, Copilot can reference:
- Memory Bank for architectural decisions
- Technical constraints from `technical.md`
- Known issues from `tasks_plan.md`

### 3. Inline Suggestions
While coding, Copilot uses:
- General principles from rulebook
- Project-specific patterns
- Security guidelines
- Testing best practices

## Recommended Setup

### Immediate Actions

1. **Add `.github/workflows/rulebook-sync.yml`** (optional, automated)
   - Auto-updates Copilot instructions when memory changes
   - Requires: `rulebook` optional dependency in pyproject.toml ✅

2. **Update `.github/copilot-instructions.md`** (manual, as needed)
   - Run: `python -m rulebook_ai project sync --assistant copilot`
   - After updating: `memory/docs/architecture.md`, `memory/docs/technical.md`, etc.

3. **Reference Task Files in PRs** (manual)
   - Use `@copilot` mentions with `.github/COPILOT_TASK_*.md` files
   - Example: See PR #45 for test optimization task

### Future Enhancements

- **Smart PR Labels**: Auto-label PRs based on changed profiles (frontend/backend/docker/etc.)
- **Context-Aware Reviews**: Use memory files to generate review checklists
- **Automated Documentation**: Generate CHANGELOG entries from `active_context.md`

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Rulebook-AI Tutorial](https://github.com/botingw/rulebook-ai/blob/main/memory/docs/user_guide/tutorial.md)

## Decision: Manual vs Automated Sync

**Recommendation**: Start with **manual sync** for now:
- `python -m rulebook_ai project sync` after significant memory updates
- Avoid committing `.github/copilot-instructions.md` (git-ignored)
- Let each developer generate their own local version

**Rationale**:
- Prevents merge conflicts on auto-generated files
- Developers can use different profiles per task
- Cleaner git history
- Can enable automated sync later if needed
