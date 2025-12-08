# Task: Fix Async Test Configuration

## Problem Statement

Multiple test files contain async test functions that fail during pre-commit pytest hooks with the error:

```text
async def functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio
  - pytest-asyncio
```

This blocks normal git workflow, requiring `--no-verify` flag to bypass pre-commit hooks.

## Current State

### Dependencies
- `pytest-asyncio>=0.21.0` is already installed via `dev` and `test` optional dependencies in `pyproject.toml`
- Tests are marked with `@pytest.mark.asyncio` decorator

### Affected Files
1. `tests/test_auto_discovery.py` - 7 async tests
2. `tests/test_background_scheduler.py` - 8+ async tests
3. `tests/test_link_finder.py` - 9+ async tests

### Example Failure
```python
# tests/test_auto_discovery.py:45
@pytest.mark.asyncio
async def test_extract_search_queries_from_resume(self, scheduler, mock_resume):
    # Test code...
```

Fails with: `async def functions are not natively supported`

## Root Cause

`pytest-asyncio` requires explicit configuration to automatically detect and run async tests. Without configuration, pytest doesn't recognize the plugin.

## Solution

Configure pytest to use `pytest-asyncio` in auto mode by adding configuration to **one** of these files:

### Option 1: pyproject.toml (RECOMMENDED)

Add to existing `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"  # ADD THIS LINE
```

### Option 2: pytest.ini

Add new section to `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
```

## Implementation Steps

1. **Choose configuration location**: Use `pyproject.toml` (Option 1) to keep all Python config centralized

2. **Add configuration**:
   - Open `pyproject.toml`
   - Locate `[tool.pytest.ini_options]` section (around line 59)
   - Add `asyncio_mode = "auto"` line

3. **Test the fix**:
   ```powershell
   # Run affected test files
   pytest tests/test_auto_discovery.py -v
   pytest tests/test_background_scheduler.py -v
   pytest tests/test_link_finder.py -v

   # Run pre-commit hooks to verify fix
   git add .
   git commit -m "test commit"  # Should not fail on pytest hook
   ```

4. **Verify pre-commit works**:
   - Make a trivial change (add comment to any file)
   - Stage and attempt commit without `--no-verify`
   - Pre-commit pytest hook should pass

## Expected Outcome

- All async tests in the 3 affected files pass
- Pre-commit pytest hook succeeds
- No need for `--no-verify` flag on commits
- Git workflow returns to normal

## Testing Checklist

- [ ] Configuration added to `pyproject.toml`
- [ ] `pytest tests/test_auto_discovery.py` passes (0 failures)
- [ ] `pytest tests/test_background_scheduler.py` passes (0 failures)
- [ ] `pytest tests/test_link_finder.py` passes (0 failures)
- [ ] Pre-commit hooks pass without `--no-verify`
- [ ] All async tests show as passed (not skipped)

## Additional Context

### Current pyproject.toml pytest config
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

### pytest-asyncio Documentation
- Auto mode: Automatically applies asyncio fixture to all async test functions
- No need for explicit `@pytest.mark.asyncio` with auto mode (but won't hurt)
- Reference: <https://pytest-asyncio.readthedocs.io/en/latest/reference/configuration.html>

## Success Criteria

1. Zero test failures in affected files
2. Pre-commit hooks complete successfully
3. No warnings about unknown `pytest.mark.asyncio` marks
4. Git commits work without `--no-verify` flag

## Estimated Effort

- **Implementation**: 2 minutes (one-line config change)
- **Testing**: 5 minutes (run test suites + pre-commit)
- **Total**: ~7 minutes

## Priority

**P1 - High**: Blocks normal development workflow
