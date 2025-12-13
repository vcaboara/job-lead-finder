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

### Async Test Failures - pytest-asyncio Configuration
**Status**: ⚠️ NEEDS FIX
**Issue**: Async tests in multiple files fail with "async def functions are not natively supported"
**Files Affected**:
- `tests/test_auto_discovery.py` (7 async tests)
- `tests/test_background_scheduler.py` (8+ async tests)
- `tests/test_link_finder.py` (9+ async tests)

**Root Cause**: `pytest-asyncio` is installed in dev/test dependencies but not properly configured in pytest.ini

**Error Message**:
```
async def functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio
  - pytest-asyncio
```

**Solution Required**:
1. Add `asyncio_mode = auto` to `[tool.pytest.ini_options]` in `pyproject.toml`
2. OR add `[pytest]` section with `asyncio_mode = auto` to `pytest.ini`
3. Verify all async tests pass after configuration

**Impact**: Pre-commit pytest hook fails, blocking commits without `--no-verify`

**Priority**: P1 - High (blocks normal git workflow)

**Copilot Task**: See `docs/TASKS/fix-async-tests.md` for detailed implementation guide

---

## Rulebook-AI Post-Merge Tasks

After PR #47 merges, complete the Memory Bank documentation:

### 1. Architecture Documentation
**File**: `memory/docs/architecture.md`
**Action**: Document system components, data flow, provider architecture
**Priority**: P0 - Required for AI context

### 2. Technical Documentation
**File**: `memory/docs/technical.md`
**Action**: Document dev environment (uv, Docker, pre-commit), tech stack, setup
**Priority**: P0 - Required for AI context

### 3. Task Planning
**File**: `memory/tasks/tasks_plan.md`
**Action**: Document current roadmap, in-progress work, known issues
**Priority**: P0 - Required for AI context

### 4. Resync AI Instructions
**Command**: `python -m rulebook_ai project sync`
**Action**: Regenerate GitHub Copilot instructions with populated context
**Priority**: P0 - Apply updated context

---

## Future Enhancements (Not for this PR)

### AI/ML Infrastructure & Automation

- [x] **Containerized AI Resource Monitor Dashboard**
  - Web-based graphical dashboard for monitoring AI usage
  - Real-time tracking of Copilot, Gemini, Ollama usage
  - GPU utilization and VRAM monitoring
  - Auto-refreshing charts (Chart.js)
  - Accessible at http://localhost:9000
  - No Node.js required - pure Python/Flask in container
  - **Status**: ✅ COMPLETE - Runs as Docker service

- [ ] **Email Server Integration for Aggregator Automation**
  - Setup mail server to receive and forward aggregator emails
  - Auto-evaluation of job postings from emails
  - Automatic resume generation tailored to job posting
  - Automatic cover letter generation
  - Extract and validate direct application links
  - **Priority**: High - Enables end-to-end automation

- [ ] **Learning from Job Suggestions**
  - Track which suggested jobs user applies to / is interested in
  - Build preference model from user feedback
  - Improve job matching algorithm based on historical data
  - Store acceptance/rejection patterns
  - **Priority**: Medium - Improves relevance over time

- [ ] **Provider-Agnostic AI Evaluation Framework**
  - Abstract AI provider interface for resume evaluation
  - Support multiple LLM backends (OpenAI, Anthropic, Gemini, Local, etc.)
  - Configurable provider selection per task type
  - Fallback provider chain for reliability
  - **Priority**: High - Reduces vendor lock-in

- [ ] **AI Profile System**
  - Create specialized AI profiles for different tasks:
    - Resume evaluation profile (critical, detailed analysis)
    - Resume generation profile (creative, marketing-focused)
    - Cover letter profile (persuasive, personalized)
    - Job matching profile (analytical, quick decisions)
  - Each profile has custom system instructions and parameters
  - **Priority**: Medium - Optimizes AI performance per task

- [ ] **Small Language Model Integration**
  - Identify simple tasks suitable for small LMs (classification, extraction)
  - Integrate efficient small models for:
    - Job title classification
    - Skills extraction from job descriptions
    - Basic text summarization
    - Duplicate detection
  - Cost-performance optimization: use small LMs where possible
  - **Priority**: Medium - Reduces API costs

- [ ] **Tech Demo Portfolio Generator**
  - For tech job seekers: auto-generate project ideas in their domain
  - Create GitHub repo templates with starter code
  - Generate README with project description and setup
  - Suggest tech stack based on job requirements
  - Link demos to resume/portfolio
  - **Priority**: Low - Nice-to-have for technical roles

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

---

## AI Assistant Integration

### Claude Code Settings - Agent Support

**Source**: <https://github.com/feiskyer/claude-code-settings?tab=readme-ov-file#agents>

**Description**: Investigate integrating Claude Code's agent system for autonomous task execution

**Potential Benefits**:

- Autonomous handling of routine development tasks
- Integration with Memory Bank for context-aware task execution
- Coordination with existing autonomous_task_executor.py

**Action**: Research agent configuration and evaluate compatibility with current workflow

**Priority**: P1 - High-Value (aligns with autonomous AI execution track)

### Copilot Usage Tracking API

**Issue**: Current estimation method doesn't provide actual Copilot usage data

**Proposal**: Access VS Code's Copilot API to get real usage metrics instead of estimating

**Scope**: Extend to all AI providers (Gemini, OpenAI, etc.) for unified usage tracking

**Benefits**:

- Accurate quota monitoring in dashboard
- Better resource allocation decisions
- Historical usage analytics

**Action**: Investigate VS Code extension APIs for Copilot and other AI provider usage data

**Priority**: P2 - Medium (dashboard enhancement)
