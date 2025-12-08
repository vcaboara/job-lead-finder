# Fix Async Tests Configuration

## Problem
The project has conflicting pytest configuration files that cause pytest to ignore the `asyncio_mode = auto` setting in `pytest.ini`. This results in:

1. **Configuration Conflict**: Three pytest-related config files exist:
   - `pytest.ini` (intended main configuration)
   - `pyproject.toml` (has `[tool.pytest.ini_options]` section)
   - `pytest.toml` (just a reference file, not a valid pytest config)

2. **Warning Message**: When running tests, pytest shows:
   ```
   WARNING: ignoring pytest config in pytest.ini, pyproject.toml!
   ```

3. **Mode Mismatch**: 
   - `pytest.ini` specifies `asyncio_mode = auto`
   - But pytest is using `mode=Mode.STRICT` (the default for pytest-asyncio >= 1.0.0)
   - This happens because pyproject.toml takes precedence but doesn't specify asyncio_mode

## Impact
While all tests currently pass, the configuration inconsistency could cause issues:
- Async tests without `@pytest.mark.asyncio` won't be automatically discovered in strict mode
- Future developers might be confused by the configuration conflict
- Some async fixtures might not work as expected

## Solution
Fix the configuration conflict by consolidating pytest settings into a single authoritative source.

### Option 1: Use pyproject.toml (Recommended)
Move all pytest configuration from `pytest.ini` to `pyproject.toml` and remove `pytest.ini`.

### Option 2: Use pytest.ini only
Remove the `[tool.pytest.ini_options]` section from `pyproject.toml` so pytest reads from `pytest.ini`.

## Implementation

Implement Option 1 (use pyproject.toml) because:
- It's the modern Python standard (PEP 518)
- Consolidates all tool configuration in one place
- Most Python projects are moving to pyproject.toml

### Steps:
1. Copy all settings from `pytest.ini` to `[tool.pytest.ini_options]` in `pyproject.toml`
2. Ensure `asyncio_mode = "auto"` is specified in pyproject.toml
3. Remove `pytest.ini` to eliminate the conflict
4. Keep `pytest.toml` as it's just a reference file (rename to avoid confusion if needed)
5. Verify tests still pass and warning is gone

## Verification
After implementation:
```bash
# Should show no configuration warnings
python3 -m pytest tests/test_auto_discovery.py -v

# Should show asyncio: mode=Mode.AUTO instead of Mode.STRICT
python3 -m pytest --collect-only tests/test_auto_discovery.py 2>&1 | grep asyncio

# All async tests should still pass
python3 -m pytest tests/test_auto_discovery.py tests/test_background_scheduler.py tests/test_link_finder.py -v
```

## Files to Modify
1. `pyproject.toml` - Add complete pytest configuration
2. `pytest.ini` - Delete this file
3. (Optional) `pytest.toml` - Rename to `pytest-commands.md` to clarify it's just a reference
