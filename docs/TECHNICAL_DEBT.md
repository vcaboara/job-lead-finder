# Technical Debt & Code Quality Notes

## Performance Optimizations (Low Priority)

### PDF Text Cleaning (ui_server.py:771-777)
**Issue**: Multiple string `.replace()` calls create new string objects repeatedly
**Impact**: Minor performance hit on large PDFs (>100 pages)
**Suggestion**: Use regex pattern with translation table for single-pass cleaning
**Effort**: Medium (requires testing mojibake patterns)
**Priority**: Low - Current implementation works fine for typical resume PDFs

```python
# Current: Multiple replace calls
cleaned_text = cleaned_text.replace('â€"', '—')    # em dash
cleaned_text = cleaned_text.replace('â€"', '–')    # en dash
# ... more replacements

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

## PR Scope Management Learnings

**Past Experience**: +820 -95 lines, 15+ files
**Result**: 3 rounds of Copilot reviews with diminishing returns

**Best Practices for Future PRs**:
1. **Lines changed**: Keep under 300-400 lines total
2. **Files modified**: 3-5 files maximum
3. **Single responsibility**: One feature or fix per PR
4. **Test-to-code ratio**: Aim for 1:1 or less

**Key Insight**: AI reviewers provide iterative feedback as code evolves. Large PRs create feedback loops where each fix generates new comments. Smaller PRs = faster convergence.
