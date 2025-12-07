# Active Copilot Task: Test Runtime Optimization

## Objective
Reduce test suite runtime from ~30+ seconds to <5 seconds to make it suitable for pre-commit hooks.

## Context
- **Current State:** 304 tests pass but take too long for pre-commit workflow
- **Target:** <5 seconds total runtime
- **Pre-commit Config:** `.pre-commit-config.yaml` runs `pytest tests/ -v --tb=short -m "not slow"`
- **Key Files to Optimize:**
  - `tests/test_upload_resume.py` (file I/O heavy)
  - `tests/test_pdf_extraction.py` (file I/O heavy)
  - `tests/test_mcp_providers.py` (API calls)
  - `tests/test_gemini_provider.py` (API calls)
  - Any other tests with I/O or network operations

## Strategy

### 1. Mock File I/O Operations
Replace actual file writes/reads with in-memory operations using `BytesIO`:

**Before:**
```python
def test_upload_file():
    with open("/tmp/test.txt", "w") as f:
        f.write("test content")
    # test code
```

**After:**
```python
from io import BytesIO

def test_upload_file(mocker):
    mock_file = BytesIO(b"test content")
    mocker.patch("builtins.open", return_value=mock_file)
    # test code
```

### 2. Mock External API Calls
Use `pytest-mock` to mock all HTTP requests:

**Before:**
```python
def test_api_call():
    response = requests.get("https://api.example.com/data")
    # test code
```

**After:**
```python
def test_api_call(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.status_code = 200
    mocker.patch("requests.get", return_value=mock_response)
    # test code
```

### 3. Use In-Memory SQLite Database
Replace persistent database with `:memory:`:

**Before:**
```python
@pytest.fixture
def db():
    tracker = JobTracker("test.db")
    yield tracker
    os.remove("test.db")
```

**After:**
```python
@pytest.fixture
def db():
    tracker = JobTracker(":memory:")
    yield tracker
    # No cleanup needed
```

### 4. Enable Parallel Test Execution
Already configured in `pytest.ini`:
```ini
[pytest]
addopts = -n auto
```

### 5. Mark Slow Tests
Keep integration tests separate:
```python
@pytest.mark.slow
def test_actual_api_integration():
    # Real API call for integration testing
    pass
```

## Implementation Checklist

### Phase 1: File I/O Mocking
- [ ] Update `tests/test_upload_resume.py` to use `BytesIO` for file operations
- [ ] Update `tests/test_pdf_extraction.py` to use `BytesIO` for PDF content
- [ ] Mock `pathlib.Path.write_text/read_text` where used
- [ ] Mock `os.makedirs`, `os.path.exists` to avoid filesystem operations

### Phase 2: API Mocking
- [ ] Mock all `requests.get/post` calls in `tests/test_mcp_providers.py`
- [ ] Mock Gemini API calls in `tests/test_gemini_provider.py`
- [ ] Mock any MCP server interactions (mcp_providers.py)
- [ ] Ensure mock responses match real API structure

### Phase 3: Database Optimization
- [ ] Verify all JobTracker instances use `:memory:` in tests
- [ ] Remove any `os.remove` cleanup for database files
- [ ] Check `conftest.py` for any persistent DB fixtures

### Phase 4: Validation
- [ ] Run `pytest tests/ -v --tb=short -m "not slow"` and verify <5s runtime
- [ ] Ensure all 304 tests still pass
- [ ] Run `pre-commit run pytest --all-files` to verify pre-commit compatibility
- [ ] Spot check that mocked tests still validate actual behavior

## Success Criteria
- ✅ Test suite completes in <5 seconds
- ✅ All existing tests pass (304 tests)
- ✅ No logic changes to production code (only test modifications)
- ✅ Pre-commit pytest hook runs successfully
- ✅ Tests still validate actual behavior (mocks match reality)

## Dependencies Already Installed
- `pytest` - Core testing framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking support (provides `mocker` fixture)
- `pytest-xdist` - Parallel execution

## Notes
- Focus on **test code only** - no changes to `src/app/` files
- Keep test assertions and logic unchanged - only replace I/O operations
- Use `mocker.patch()` instead of `unittest.mock` for consistency
- Test actual behavior validation should remain - we're speeding up, not removing coverage

## Example: Complete Before/After

### Before (Slow - ~2s per test)
```python
def test_upload_resume_txt(client):
    resume_content = "My resume content"
    temp_file = "/tmp/test_resume.txt"
    with open(temp_file, "w") as f:
        f.write(resume_content)

    with open(temp_file, "rb") as f:
        response = client.post("/upload_resume", files={"file": f})

    os.remove(temp_file)
    assert response.status_code == 200
```

### After (Fast - <0.01s per test)
```python
def test_upload_resume_txt(client, mocker):
    from io import BytesIO

    resume_content = b"My resume content"
    mock_file = BytesIO(resume_content)
    mock_file.name = "test_resume.txt"

    response = client.post("/upload_resume", files={"file": ("test_resume.txt", mock_file, "text/plain")})

    assert response.status_code == 200
```

## How to Start
1. Read the detailed guide in `.github/copilot-task-test-optimization.md`
2. Start with `tests/test_upload_resume.py` (likely biggest time sink)
3. Run tests after each file to verify they still pass
4. Move to API mocking in MCP and Gemini tests
5. Validate final runtime with `time pytest tests/ -v --tb=short -m "not slow"`

---

**Status:** 🟡 IN PROGRESS (assigned to GitHub Copilot)
**Branch:** `feature/enhanced-resume-upload` (will create `fix/test-runtime-optimization` if needed)
**Estimated Time:** 30-60 minutes for Copilot to complete all changes
**Priority:** HIGH (blocks pre-commit workflow efficiency)
