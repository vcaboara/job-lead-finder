# Error Documentation

This file documents critical errors encountered in the project and their resolutions. Use this as a reference to avoid repeating mistakes.

---

## 2025-12-09: xdist_group Markers Being Silently Ignored

### The Error
Test `test_filter_tracked_jobs_by_status` was failing intermittently with:
```
AssertionError: Expected 1 applied job, got 2
```

Despite adding `@pytest.mark.xdist_group(name="tracker")` markers to 13 tests across PR #60, #59, and #66, the test pollution continued.

### Root Cause
**The `xdist_group` marker was NOT registered in pytest configuration**, causing pytest-xdist to silently ignore all group markers. Additionally, pytest was using default `load` distribution mode instead of `loadgroup`, which is required for group-based test distribution.

### The Fix (PR #67)
1. **Register the marker** in `pyproject.toml`:
```toml
markers = [
    # ... existing markers ...
    "xdist_group: marks tests that must run in the same worker group (pytest-xdist)",
]
```

2. **Enable loadgroup distribution**:
```toml
addopts = "-v --tb=short -m 'not slow' -n auto --dist loadgroup --maxfail=3 --ff"
```

### Why Previous PRs Passed but Main Failed
PRs #60, #59, #66 all passed individually because of lucky test ordering, not actual test isolation. Different merge sequences triggered the race condition.

### Lesson Learned
**ALWAYS verify pytest markers are registered** before using them. Check:
1. Marker is listed in `[tool.pytest.ini_options].markers`
2. pytest-xdist is configured with correct distribution mode (`--dist loadgroup` for groups)
3. Run `pytest --markers` to verify marker registration

### Prevention
- Document all custom markers in pytest config
- Verify marker behavior with intentional test pollution scenarios
- Check pytest documentation for plugin-specific configuration requirements

---

## 2025-12-09: Failed to Verify Command Output Before Pushing

### The Error
In PR #67 first commit, removed `pytest_benchmark` warning filter from pyproject.toml, which broke CI because:
1. The filter IS needed in CI (pytest-benchmark is installed there)
2. Local environment didn't have pytest-benchmark, showing non-fatal warning
3. Pushed changes without verifying command output showed errors

### Root Cause
**Assumed pytest command worked** based on local behavior, didn't read full error output, didn't verify exit codes.

### The Fix
Restored the pytest_benchmark filter line in the second commit of PR #67.

### Lesson Learned
**MANDATORY VERIFICATION BEFORE PUSHING:**
1. ✅ Check exit codes (non-zero = failure)
2. ✅ Read command output COMPLETELY for errors/warnings
3. ✅ If output shows errors, STOP and investigate
4. ✅ Before pushing: verify tests pass, config is valid
5. ✅ Don't assume "it works locally" means "it works in CI"

### Prevention
This verification workflow is now embedded in:
- `.github/copilot-instructions.md` (Section II: Foundational Software Engineering)
- Implementation workflow (Rule: 01-code_v1.md, Step 2)
- Debugging workflow (Rule: 01-debug_v1.md, Step 4)

All AI agents MUST follow these verification steps.

---

## 2025-12-09: pytest-benchmark Incompatible with pytest-xdist

### The Error

CI failed with INTERNALERROR during pytest configuration:

```text
pytest_benchmark.logger.PytestBenchmarkWarning: Benchmarks are automatically disabled
because xdist plugin is active. Benchmarks cannot be performed reliably in a
parallelized environment.
```

### Root Cause

pytest-benchmark raises a warning during `pytest_configure` hook when it detects pytest-xdist is active. Our `filterwarnings = ["error", ...]` configuration treats ALL warnings as errors, causing fatal INTERNALERROR.

The warning filter in pyproject.toml (`ignore::pytest_benchmark.logger.PytestBenchmarkWarning`) cannot catch this because the warning is raised during pytest configuration, **before** warning filters are applied.

### The Fix (PR #67)

Disable pytest-benchmark plugin when using xdist with `-p no:benchmark`:

**.github/workflows/ci.yml**:

```yaml
pytest -n auto -p no:benchmark -m "" --cov=app --cov-report=xml --cov-report=term
```

**pyproject.toml**:

```toml
addopts = "-v --tb=short -m 'not slow' -n auto --dist loadgroup -p no:benchmark --maxfail=3 --ff"
```

### Lesson Learned

pytest-benchmark and pytest-xdist are **mutually exclusive**:
- pytest-benchmark: For performance benchmarking (requires serial execution)
- pytest-xdist: For parallel test execution

Cannot use both simultaneously. Benchmarks require deterministic, non-parallel environment.

### Prevention

- Document plugin incompatibilities in project docs
- Use `-p no:plugin_name` to disable conflicting plugins
- Be aware that warning filters don't catch configuration-time warnings
- Consider separate test suites for benchmarks vs. functional tests

---

## Template for Future Errors

### The Error
[Brief description of the error/symptom]

### Root Cause
[Underlying cause, not just symptoms]

### The Fix
[Specific solution with code examples if applicable]

### Lesson Learned
[Key takeaway to prevent recurrence]

### Prevention
[Process changes, documentation updates, or tooling]

---
