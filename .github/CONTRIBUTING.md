# Contributing Guidelines

## Development Workflow

Follow these standards for all contributions to maintain code quality and project consistency.

### 1. Commit Standards

**One feature per commit:**
- Each commit should represent a single, atomic change
- Group related changes together (implementation + tests + docs)
- Use descriptive commit messages following conventional commits format

```bash
# Good examples:
feat: Add WeWorkRemotely RSS provider
fix: Extract company name from title in WeWorkRemotely RSS
docs: Update CHANGELOG and README for WeWorkRemotely
test: Add comprehensive tests for WeWorkRemotelyMCP
refactor: Move providers to modular package structure

# Bad examples:
git commit -m "fixes"
git commit -m "WIP"
git commit -m "updates"
```

**Conventional Commit Format:**
```
<type>: <description>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `security`

### 2. Documentation Requirements

**Update documentation with every code change:**

#### Required Documentation Updates:
- [ ] **CHANGELOG.md** - Add entry in `[Unreleased]` section
  - Use categories: Added, Changed, Fixed, Removed, Security, Deprecated
  - Include performance metrics for new providers
  - Document breaking changes clearly

- [ ] **README.md** - Update if user-facing changes
  - New features or providers
  - API endpoint changes
  - Configuration changes
  - Installation/setup changes

- [ ] **Code Comments** - Document complex logic
  - Why (not what) for non-obvious code
  - Edge cases and gotchas
  - External dependencies or API quirks

- [ ] **Docstrings** - All public APIs
  - Follow Google/NumPy style
  - Include Args, Returns, Raises sections
  - Add usage examples for complex functions

### 3. Testing Requirements

**All code changes must include tests:**

#### Test Coverage Expectations:
- [ ] **Unit tests** for new functions/classes
- [ ] **Integration tests** for provider interactions
- [ ] **Error handling tests** for failure scenarios
- [ ] **Edge case tests** (empty inputs, malformed data, etc.)

#### Test File Locations:
- Provider tests: `tests/test_mcp_providers.py`
- API tests: `tests/test_ui_server.py`
- Core logic: `tests/test_job_finder.py`, `tests/test_job_tracker.py`

#### Running Tests:
```bash
# Run all tests
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest

# Run specific test file
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest tests/test_mcp_providers.py

# Run specific test
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest tests/test_mcp_providers.py::TestWeWorkRemotelyMCP::test_weworkremotely_search_jobs_success

# With verbose output
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest -v
```

### 4. Smoke Testing

**Before committing, run smoke tests to verify live functionality:**

#### API Smoke Test (Live Data):
```powershell
# Start services
docker compose up -d

# Test API returns real jobs
$body = @{query="python";count=10} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/search" -Method POST -Body $body -ContentType "application/json"
Write-Host "Found $($response.jobs.Count) jobs"
$response.jobs | Select-Object -First 5 | ForEach-Object {
    Write-Host "`n$($_.title) at $($_.company) - Source: $($_.source)"
}

# Verify specific provider (e.g., WeWorkRemotely)
docker compose logs ui --tail 30 | Select-String "WeWorkRemotely"
```

**Expected results:**
- API returns jobs (count > 0)
- Company names are real companies (not "Unknown Company" or placeholders)
- Multiple providers return results
- Response time < 5 seconds

#### UI Smoke Test (Visual Verification):
```powershell
# Open UI in browser
Start-Process "http://localhost:8000"
```

**Manual verification checklist:**
- [ ] Page loads without errors (check browser console)
- [ ] Search form displays correctly
- [ ] Search returns results within reasonable time
- [ ] Jobs display with all fields (title, company, location, link)
- [ ] Provider badges show correctly (RemoteOK, Remotive, WeWorkRemotely, etc.)
- [ ] Job tracking features work (hide, status update)
- [ ] No UI layout issues or broken styling

### 5. CI/CD Requirements

**Keep CI passing at all times:**

#### Before Pushing:
```bash
# Verify all tests pass locally
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest

# Check for any Python errors
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci python -m py_compile src/app/*.py
```

#### CI Pipeline Checks:
- [ ] All tests pass (172+ tests)
- [ ] No syntax errors
- [ ] Code coverage maintained (if coverage enabled)
- [ ] Docker build succeeds

#### If CI Fails:
1. Pull latest main: `git pull origin main`
2. Fix the issue locally
3. Run full test suite
4. Commit fix with descriptive message
5. Push and verify CI passes

### 6. Pull Request Process

**Address all PR feedback promptly:**

#### PR Preparation:
- [ ] Update branch from main: `git fetch origin; git merge origin/main`
- [ ] All commits follow commit standards
- [ ] Documentation updated (CHANGELOG, README)
- [ ] Tests added and passing
- [ ] Smoke tests completed
- [ ] CI passing

#### Creating PR:
```bash
# Push branch
git push origin feature/your-feature-name

# Create PR via GitHub UI or CLI
```

**PR Description Template:**
```markdown
## Summary
Brief description of what this PR does

## Changes
- Bullet list of key changes
- New files/features added
- Modified behavior

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Smoke test completed (live API working)
- [ ] UI tested manually

## Documentation
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] Code comments added for complex logic

## Performance Impact
- Expected response time: X.Xs
- Jobs returned: ~X-X per search
```

#### Addressing PR Comments:
1. **Read all comments** thoroughly before making changes
2. **Make independent commits** for each distinct feedback item
3. **Test after each change** - don't batch untested changes
4. **Document your fixes** in commit messages
5. **Respond to comments** - explain your approach or ask for clarification
6. **Re-run smoke tests** after addressing feedback
7. **Request re-review** when all comments addressed

#### Example Feedback Resolution:
```bash
# Copilot comment: "Use defusedxml for XXE protection"
# 1. Make the change
# 2. Add dependency to pyproject.toml
# 3. Update tests if needed
# 4. Commit
git add src/app/providers/weworkremotely.py pyproject.toml
git commit -m "security: Use defusedxml to prevent XXE attacks

- Replace xml.etree.ElementTree with defusedxml.ElementTree
- Add defusedxml>=0.7.0 to dependencies
- Include fallback for backward compatibility"

# 5. Run tests
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest tests/test_mcp_providers.py::TestWeWorkRemotelyMCP

# 6. Push
git push
```

### 7. Pre-Commit Checklist

Before every commit, verify:

```bash
# 1. Tests pass
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci pytest

# 2. No syntax errors
docker run --rm -v ${PWD}:/workspace -w /workspace job-starter-ci python -m py_compile src/app/**/*.py

# 3. Smoke test (if touching providers or API)
docker compose up -d
# ... run smoke test commands ...

# 4. Documentation updated
git status  # Check if CHANGELOG.md modified

# 5. Commit with meaningful message
git add <files>
git commit -m "type: descriptive message"
```

### 8. Common Patterns

#### Adding a New Provider:
1. Create provider class in `src/app/providers/yourprovider.py`
2. Add tests in `tests/test_mcp_providers.py`
3. Update `src/app/providers/__init__.py` to export
4. Add to default config in `src/app/config_manager.py`
5. Document in `CHANGELOG.md` and `docs/STRATEGY.md`
6. Run smoke test to verify real jobs return
7. Commit: `feat: Add YourProvider job aggregator`

#### Fixing a Bug:
1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify test now passes
4. Add regression test if needed
5. Update CHANGELOG under `### Fixed`
6. Commit: `fix: Correct company extraction in RSS parser`

#### Refactoring:
1. Ensure all tests pass before starting
2. Make incremental changes
3. Run tests after each change
4. Keep commits focused (one refactoring per commit)
5. Update documentation if behavior changes
6. Commit: `refactor: Extract providers to modular package`

## Questions?

If you're unsure about any of these guidelines, ask before making changes. It's better to clarify expectations upfront than to redo work later.

## Summary Checklist

For every PR, ensure:
- [ ] Single feature per commit with descriptive messages
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if user-facing changes)
- [ ] Tests added for all new code
- [ ] All tests passing locally and in CI
- [ ] API smoke test completed (live data verified)
- [ ] UI smoke test completed (visual verification)
- [ ] All PR comments addressed in separate commits
- [ ] Documentation is accurate and complete
