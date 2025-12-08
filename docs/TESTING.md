# Fast Testing Guide

## Quick Start

### Fastest Workflows (by speed)

1. **Changed files only** (~10-30s) - RECOMMENDED for development
   ```powershell
   .\test.ps1 fast
   # or: pytest --picked
   ```

2. **Unit tests only** (~30-60s) - Pure logic, no I/O
   ```powershell
   .\test.ps1 unit
   # or: pytest -m unit
   ```

3. **Smoke test** (varies) - Run failed first, stop at first failure
   ```powershell
   .\test.ps1 smoke
   # or: pytest --ff --maxfail=1 -x
   ```

4. **Default** (~2min) - All non-slow tests in parallel
   ```powershell
   pytest
   ```

5. **Full suite** (~2.5min) - Everything including slow tests
   ```powershell
   .\test.ps1 all
   # or: pytest -m "" --slow
   ```

## Installation

Install fast testing tools:
```powershell
pip install pytest-picked pytest-sugar pytest-benchmark pytest-watch
```

## Testing Modes Explained

### 1. Changed Files Mode (pytest-picked)
**Target: <30 seconds**

Only runs tests in files that changed since last commit:
- Detects modified test files
- Detects tests covering modified source files
- Perfect for TDD/rapid iteration

```powershell
pytest --picked           # Changed files
pytest --picked --mode=branch  # Since branching point
```

### 2. Unit Test Mode
**Target: <60 seconds**

Mark pure unit tests with `@pytest.mark.unit`:
```python
@pytest.mark.unit
def test_pure_function():
    # No file I/O, no network, no database
    result = calculate_total([1, 2, 3])
    assert result == 6
```

### 3. Fail Fast Mode
**Target: Stop at first failure**

- `--ff`: Run previously failed tests first
- `--maxfail=1`: Stop after first failure
- `-x`: Same as --maxfail=1

Perfect for debugging specific failures.

### 4. Parallel Mode (default)
**Target: ~2 minutes for full suite**

- `-n auto`: Uses all CPU cores
- Automatically enabled in pytest.ini
- Requires proper test isolation

## Optimization Tips

### 1. Mark Slow Tests
```python
@pytest.mark.slow
def test_full_integration():
    # This won't run by default
    pass
```

### 2. Use Fixtures Efficiently
```python
@pytest.fixture(scope="session")  # Reuse across all tests
def expensive_setup():
    return create_database()

@pytest.fixture(scope="function")  # New for each test (default)
def clean_state():
    return {}
```

### 3. Mock External Dependencies
```python
@pytest.mark.unit
def test_api_call(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url: MockResponse())
    result = fetch_data("https://api.example.com")
    assert result is not None
```

### 4. Profile Slow Tests
```powershell
.\test.ps1 profile
# or: pytest --durations=20
```

## Test Execution Time Targets

| Mode | Target | Command |
|------|--------|---------|
| Changed files | <30s | `pytest --picked` |
| Unit tests | <60s | `pytest -m unit` |
| Smoke test | varies | `pytest --ff -x` |
| Default (CI) | <2min | `pytest` |
| Full suite | <2.5min | `pytest --slow` |

## CI/CD Integration

**.github/workflows** should use:
```yaml
- name: Run fast tests
  run: pytest --maxfail=3 --ff -n auto
```

## Pre-commit Hook

Already configured in `.pre-commit-config.yaml`:
- Runs on `git push`
- Uses default pytest config (~2min)
- Can skip with `git push --no-verify`

## Troubleshooting

### Tests are still slow
1. Profile with `.\test.ps1 profile`
2. Check for unmocked `asyncio.sleep`, file I/O, or network calls
3. Use `--picked` mode during development
4. Mark integration tests with `@pytest.mark.integration`

### Tests fail in parallel
1. Check for shared state (globals, class variables)
2. Use in-memory mocking for file I/O
3. Ensure test isolation with proper fixtures

### Changed file detection not working
```powershell
git add .  # Stage your changes first
pytest --picked  # Now it can detect changes
```
