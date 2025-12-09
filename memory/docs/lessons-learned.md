# Lessons Learned

This is the learning journal for the job-lead-finder project. It captures important patterns, preferences, and project intelligence beyond what's in the code.

---

## AI Agent Workflows

### Command Verification is Mandatory
**Pattern**: Every command execution MUST be verified before proceeding.

**Why**: Multiple production issues (PR #67) occurred from assuming commands succeeded without checking output.

**Implementation**:
1. Check exit codes after every command
2. Read complete output for errors/warnings
3. If errors detected, STOP and investigate
4. Before git push: verify tests pass, config valid, build succeeds

**References**:
- `.github/copilot-instructions.md` Section II
- `error-documentation.md` 2025-12-09 entries

---

## pytest and Testing

### pytest-xdist Group Markers Require Configuration
**Pattern**: Custom pytest markers MUST be registered in config before use.

**Discovery**: Added `@pytest.mark.xdist_group(name="tracker")` to 13 tests across 3 PRs, but markers were silently ignored for weeks.

**Root Cause**: Marker not registered in `[tool.pytest.ini_options].markers`, and `--dist loadgroup` not enabled.

**Solution**:
```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "xdist_group: marks tests that must run in the same worker group (pytest-xdist)",
]
addopts = "-v ... -n auto --dist loadgroup ..."
```

**Verification**: Run `pytest --markers` to confirm registration.

**Reference**: PR #67, error-documentation.md

---

## Test Isolation

### File-Based State Requires Worker-Level Isolation
**Pattern**: Tests sharing file system state (like `job_tracking.json`) MUST run in the same pytest-xdist worker.

**Implementation**:
1. Mark all tests using shared files with `@pytest.mark.xdist_group(name="<group>")`
2. Ensure marker is registered (see pytest lesson above)
3. Use session-scoped cleanup fixtures for robustness
4. Add small delays (10ms) after file deletion for FS sync

**Tests Affected**:
- All tests in `test_tracked_jobs_ui.py` (5 tests)
- All tests in `test_ui_job_tracking.py` (8 tests)
- Total: 13 tests in `tracker` group

**Reference**: conftest.py fixtures, PR #60, #59, #66, #67

---

## CI/CD and GitHub Actions

### Branch Protection Requires Specific Check Names
**Pattern**: GitHub branch protection rules match exact workflow check names.

**Implementation**:
- Workflow job name: `build-and-test`
- Protection rule requires: `build-and-test` (exact match)
- Case-sensitive, must match precisely

**Reference**: PR #61, GitHub API configuration

---

## AI Productivity Metrics

### Tracking AI Impact for Advocacy
**Pattern**: Document AI acceleration metrics for accessibility/disability advocacy.

**Metrics Tracked** (as of Dec 9, 2025):
- 231 commits in 14 days (Nov 25 - Dec 8)
- 68K lines added
- 6.6x development acceleration
- 230K keystrokes saved
- 19.2 hours typing time avoided
- 98 total hours saved

**Purpose**: Support advocacy for AI tools as accessibility technology for people with disabilities.

**Reference**: `docs/TASKS/ai-metrics-tracking.md`

---

## Project Intelligence

### Development Environment
**Pattern**: This project uses:
- Python 3.12
- Flask for web UI
- pytest with pytest-xdist for parallel testing
- Docker for containerization
- GitHub Actions for CI/CD
- Pre-commit hooks for code quality

**Testing Philosophy**:
- Fast tests by default (skip `slow` marker)
- Parallel execution for speed (`-n auto`)
- Fail fast (`--maxfail=3`)
- Run failed tests first (`--ff`)

---

## User Preferences

### Communication Style
**Pattern**: User prefers:
- Direct, actionable responses
- Root cause analysis over quick fixes
- Documentation of lessons learned
- Multiple simultaneous PRs for parallel work
- AI-driven automation for repetitive tasks

### Workflow Preferences
**Pattern**: User workflow includes:
- Heavy use of GitHub CLI (`gh`)
- PowerShell as default shell
- Quick iteration with multiple feature branches
- CI must pass before merge (enforced by branch protection)

---

## Infrastructure Goals

### LeadForge Cluster Vision
**Pattern**: User is building comprehensive AI DevOps infrastructure.

**Phases**:
1. CI Auto-Fix Agents (automated test/build repair)
2. Feature Development Agents (parallel autonomous development)
3. Multi-Agent Orchestration (task decomposition & handoff)
4. Self-Improving System (learn from iterations)

**Status**: Planning complete (PR #65), blocked on stable CI

**Reference**: `docs/TASKS/leadforge-cluster-plan.md`

---

## Security & Privacy

### User Data Protection TODOs
**Pattern**: Security enhancements needed before production deployment.

**Critical Items**:
- Client-side encryption for resume data
- GDPR compliance audit
- Secure credential storage (vault integration)
- Privacy policy and consent management
- Data retention policies

**Reference**: `docs/TASKS/ai-metrics-tracking.md` Security section

---

## Template for Future Lessons

### [Pattern Name]
**Pattern**: [Brief description of the pattern/lesson]

**Discovery**: [How/when this was learned]

**Implementation**: [How to apply this lesson]

**Reference**: [Related PRs, files, or documentation]

---

**Last Updated**: 2025-12-09
**Total Lessons**: 9 patterns documented
