# GitHub Copilot Task: Optimize Test Suite Runtime with Better Mocking

## Objective
Reduce test runtime from current duration to **<5 seconds** by improving mocking patterns, eliminating I/O operations, and optimizing test fixtures.

## Context
- **Current State**: Tests run but take too long for pre-commit hook
- **Target**: Fast enough for pre-commit (ideally <5s for non-slow tests)
- **Framework**: pytest with pytest-asyncio

## Files to Optimize

### High Priority (Likely Slow)
1. `tests/test_upload_resume.py` - File I/O, PDF/DOCX processing
2. `tests/test_pdf_extraction.py` - PDF extraction tests
3. `tests/test_mcp_providers.py` - External API calls
4. `tests/test_provider_fallback.py` - Provider chain testing
5. `tests/test_gemini_provider.py` - API calls to Gemini

### Medium Priority
6. `tests/test_job_finder.py` - Multi-provider coordination
7. `tests/test_ui_server.py` - HTTP requests
8. `tests/test_job_tracker.py` - Database operations

## Required Changes

### 1. Mock File I/O Operations
**Problem**: Tests reading/writing actual files from disk

**Solution**:
```python
# Before: Actual file operations
def test_upload_pdf():
    with open('test.pdf', 'rb') as f:
        result = process_pdf(f)

# After: Mock file objects
from io import BytesIO
def test_upload_pdf():
    mock_pdf = BytesIO(b'%PDF-1.4...')  # Minimal valid PDF
    result = process_pdf(mock_pdf)
```

**Files to update**:
- `tests/test_upload_resume.py` - Mock PDF/DOCX file objects
- `tests/test_pdf_extraction.py` - Use BytesIO for PDF content

### 2. Mock External API Calls
**Problem**: Tests making real HTTP requests or waiting for responses

**Solution**:
```python
# Use pytest-mock or unittest.mock
@pytest.fixture
def mock_gemini_response(mocker):
    return mocker.patch('app.gemini_provider.genai.Client')

def test_job_ranking(mock_gemini_response):
    mock_gemini_response.return_value.models.generate_content.return_value = MockResponse(...)
    # Test runs instantly without API call
```

**Files to update**:
- `tests/test_gemini_provider.py` - Mock all genai API calls
- `tests/test_mcp_providers.py` - Mock MCP server responses
- `tests/test_provider_fallback.py` - Mock provider HTTP requests

### 3. Use In-Memory Database
**Problem**: SQLite file I/O operations

**Solution**:
```python
# In conftest.py or test file
@pytest.fixture
def in_memory_db():
    """Use SQLite in-memory database for tests"""
    import sqlite3
    conn = sqlite3.connect(':memory:')
    # Setup schema
    yield conn
    conn.close()
```

**Files to update**:
- `tests/test_job_tracker.py` - Use `:memory:` database
- Any tests using JobTracker

### 4. Optimize Fixtures with Appropriate Scope
**Problem**: Fixtures recreated for every test

**Solution**:
```python
# Before: function scope (default)
@pytest.fixture
def expensive_setup():
    return setup_complex_thing()

# After: session or module scope when safe
@pytest.fixture(scope="module")
def expensive_setup():
    return setup_complex_thing()
```

**File to update**:
- `tests/conftest.py` - Review all fixtures, use broader scope where safe

### 5. Mock PDF/DOCX Processing Libraries
**Problem**: Actually parsing PDF/DOCX files with pypdf/python-docx

**Solution**:
```python
# Mock pypdf PdfReader
@pytest.fixture
def mock_pdf_reader(mocker):
    mock = mocker.patch('pypdf.PdfReader')
    mock.return_value.pages = [MockPage(text="Resume content")]
    return mock

# Mock python-docx Document
@pytest.fixture
def mock_docx(mocker):
    mock = mocker.patch('docx.Document')
    mock.return_value.paragraphs = [MockParagraph("Resume text")]
    return mock
```

**Files to update**:
- `tests/test_upload_resume.py` - Mock pypdf.PdfReader and docx.Document
- `tests/test_pdf_extraction.py` - Mock all PDF parsing

### 6. Parallelize Independent Tests
**Problem**: Tests run sequentially

**Solution**:
```bash
# Install pytest-xdist
pip install pytest-xdist

# Update .pre-commit-config.yaml
args: [tests/, -v, --tb=short, -m, "not slow", -n, auto]
```

**File to update**:
- `.pre-commit-config.yaml` - Add `-n auto` flag

## Implementation Steps

1. **Identify slowest tests**:
   ```bash
   pytest --durations=10 -m "not slow"
   ```

2. **Mock external dependencies**:
   - Add `@pytest.fixture` for mocked APIs/files
   - Use `mocker.patch()` to replace real implementations

3. **Convert file I/O to in-memory**:
   - Use `BytesIO` for file-like objects
   - Use `:memory:` for SQLite

4. **Add pytest-xdist**:
   - Install dependency
   - Update pre-commit config

5. **Verify improvements**:
   ```bash
   pytest --durations=10 -m "not slow"  # Should show <5s total
   ```

## Success Criteria
- [ ] All non-slow tests complete in <5 seconds
- [ ] No external API calls during test run
- [ ] No file system I/O (except fixtures if necessary)
- [ ] All tests still pass
- [ ] Test coverage maintained or improved

## Testing Verification

After changes, run:
```bash
# Ensure all tests pass
pytest -v -m "not slow"

# Check for any remaining I/O or network calls
pytest -v -m "not slow" --capture=no  # Watch for delays

# Verify pre-commit speed
pre-commit run pytest --all-files
```

## Common Pitfalls to Avoid

❌ **Don't** remove test coverage - maintain assertions
❌ **Don't** skip important edge case tests
❌ **Don't** mock so aggressively that tests become meaningless
✅ **Do** mock external dependencies (APIs, files, network)
✅ **Do** use in-memory alternatives (BytesIO, :memory: DB)
✅ **Do** maintain test intent and coverage

## Example: Before/After

### Before (Slow)
```python
def test_upload_pdf_file():
    # Actually writes to disk
    with open('test.pdf', 'wb') as f:
        f.write(generate_pdf())

    # Makes real HTTP request
    response = client.post('/api/resume', files={'file': open('test.pdf', 'rb')})

    # Parses actual PDF
    assert response.status_code == 200
```

### After (Fast)
```python
@pytest.fixture
def mock_pdf_content():
    """Minimal valid PDF bytes"""
    return b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF'

def test_upload_pdf_file(client, mocker, mock_pdf_content):
    # Mock PDF parsing
    mock_reader = mocker.patch('pypdf.PdfReader')
    mock_reader.return_value.pages[0].extract_text.return_value = "Resume text"

    # Use in-memory file
    from io import BytesIO
    pdf_file = BytesIO(mock_pdf_content)

    # Test runs instantly
    response = client.post('/api/resume', files={'file': pdf_file})
    assert response.status_code == 200
```

## Notes
- Focus on mocking I/O and network operations
- Keep business logic tests intact
- Use `pytest --durations=10` to identify bottlenecks
- Consider adding `pytest-benchmark` for performance regression detection
