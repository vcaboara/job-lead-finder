# Technical Debt & Future Improvements

## Performance Optimizations (Low Priority)

### PDF Text Cleaning (ui_server.py:771-777)
**Issue**: Multiple string `.replace()` calls create new string objects repeatedly
**Impact**: Minor performance hit on large PDFs (>100 pages)
**Suggestion**: Use regex pattern with translation table for single-pass cleaning
**Effort**: Medium (requires testing mojibake patterns)
**Priority**: Low - Current implementation works fine for typical resume PDFs

```python
# Current: Multiple replace calls
cleaned_text = cleaned_text.replace('â€”', '—')    # em dash
cleaned_text = cleaned_text.replace('â€“', '–')    # en dash
cleaned_text = cleaned_text.replace('â€˜', '‘')    # left single quote
cleaned_text = cleaned_text.replace('â€™', '’')    # right single quote
cleaned_text = cleaned_text.replace('â€œ', '“')    # left double quote
cleaned_text = cleaned_text.replace('â€�', '”')    # right double quote
cleaned_text = cleaned_text.replace('â€¢', '•')    # bullet

# Proposed: Single-pass regex
mojibake_map = {...}
pattern = re.compile('|'.join(re.escape(k) for k in mojibake_map))
cleaned_text = pattern.sub(lambda m: mojibake_map[m.group(0)], cleaned_text)
```

**Decision**: Skip for now - adds complexity without meaningful benefit for resume-sized files

---

## Code Quality

### Mojibake Pattern Validation
**Issue**: Some mojibake patterns may have incorrect byte sequences
**Current Status**: Patterns work for common PDFs we've tested
**Action**: Monitor for encoding issues in production, adjust patterns as needed
**Priority**: Low - reactive fix if users report issues

---

## Testing

### Integration Test CI Isolation
**Status**: ✅ COMPLETE - Tests marked with `@pytest.mark.integration`
**File**: `tests/test_pdf_extraction.py`
**Skip in CI**: `pytest -m "not integration"` or set `CI=true` environment variable

---

## Future Enhancements (Not for this PR)

### Developer Experience
- [ ] Cross-platform setup utility (`setup_dev.py`)
  - Automated virtual environment creation
  - Dependency installation (dev, web, test, gemini)
  - Pre-commit hooks setup (pre-commit + pre-push)
  - .env file creation from template
  - Git configuration verification
  - Works on Windows (PowerShell/CMD) and Unix (bash)

### Resume Format Support
- [ ] Support `.rtf` (Rich Text Format) - requires `striprtf` package
- [ ] Support `.odt` (OpenDocument) - requires `odfpy` package
- [ ] OCR for image-based PDFs - requires `pytesseract`

### Security Hardening
- [ ] Sandboxed parsing (run pypdf/docx in isolated subprocess)
- [ ] File size limits per format (e.g., 2MB for PDF, 1MB for DOCX)
- [ ] Rate limiting on upload endpoint

### User Experience
- [ ] Resume preview in UI before saving
- [ ] Support multiple resumes (resume library)
- [ ] Resume version history

---

## PR Scope Management Learnings

**This PR**: +820 -95 lines, 15+ files
**Result**: 3 rounds of Copilot reviews with diminishing returns

**Best Practices for Future PRs**:
1. **Lines changed**: Keep under 300-400 lines total
2. **Files modified**: 3-5 files maximum
3. **Single responsibility**: One feature or fix per PR
4. **Test-to-code ratio**: Aim for 1:1 or less

**How this PR could have been split**:
- PR #1: Basic PDF/DOCX upload support (file handling only)
- PR #2: Security scanning layer (malicious content detection)
- PR #3: GET/DELETE endpoints for resume management

**Key Insight**: AI reviewers provide iterative feedback as code evolves. Large PRs create feedback loops where each fix generates new comments. Smaller PRs = faster convergence.
