# Automated AI Agent Setup - Quick Start Guide

## 🤖 Goal
Set up AI agents to automatically handle:
1. CI failures (like the current `test_filter_tracked_jobs_by_status` flake)
2. Feature development tasks
3. Code reviews
4. Documentation updates

---

## 🚨 URGENT: Current CI Failure

**Issue:** `test_filter_tracked_jobs_by_status` failing on main after PR #65 merge
**Root Cause:** Test is still flaky despite xdist_group markers
**Fix Needed:** More robust test isolation

**Immediate Action Required:**
```bash
# Create fix branch
git checkout -b fix/test-tracker-flake-main
```

---

## 📋 Phase 1: GitHub Actions Workflows (Today)

### 1.1 Auto-Fix CI Failures

**File:** `.github/workflows/auto-fix-ci.yml`

**Triggers:**
- Workflow run completion (failed status)
- Specific test failures (pattern matching)

**Actions:**
1. Detect failure type
2. Create fix branch automatically
3. Apply known fixes (test isolation, imports, etc.)
4. Run tests locally
5. Create PR with fix
6. Request review

**Implementation:**
```yaml
name: Auto-Fix CI Failures

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

jobs:
  auto-fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Analyze Failure
        id: analyze
        run: |
          # Download logs, identify failure pattern
          # Set output: failure_type, test_name, suggested_fix

      - name: Apply Fix
        if: steps.analyze.outputs.failure_type == 'test_isolation'
        run: |
          # Apply test isolation fix
          # Run: python scripts/fix_test_isolation.py

      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          branch: auto-fix/${{ steps.analyze.outputs.test_name }}
          title: "fix: Auto-fix ${{ steps.analyze.outputs.test_name }}"
          body: |
            Automated fix for CI failure

            **Failure:** ${{ steps.analyze.outputs.test_name }}
            **Type:** ${{ steps.analyze.outputs.failure_type }}
            **Fix Applied:** ${{ steps.analyze.outputs.suggested_fix }}
```

---

### 1.2 AI Task Dispatcher

**File:** `.github/workflows/ai-task-dispatcher.yml`

**Triggers:**
- Issue created with label `ai-task`
- Comment on issue: `/ai-assign`

**Actions:**
1. Parse task from issue
2. Assign to appropriate AI agent (based on task type)
3. Create feature branch
4. Execute task
5. Create PR
6. Link back to issue

---

### 1.3 Auto Code Review

**File:** `.github/workflows/ai-code-review.yml`

**Triggers:**
- PR opened/updated

**Actions:**
1. Download PR diff
2. Check against `docs/02-pr-review-criteria.md`
3. Run automated checks:
   - Architecture compliance
   - Security scanning
   - Code quality (complexity, duplication)
   - Test coverage
4. Post review comments
5. Approve if all checks pass, or request changes

---

## 🛠️ Phase 2: AI Agent Scripts (Today)

### 2.1 Test Isolation Fixer

**File:** `scripts/fix_test_isolation.py`

```python
#!/usr/bin/env python3
"""
Automatically fix test isolation issues.
Adds @pytest.mark.xdist_group markers to tests that modify shared state.
"""

import ast
import re
from pathlib import Path

def detect_shared_state_tests(file_path):
    """Detect tests that modify tracker, database, or file system."""
    with open(file_path) as f:
        content = f.read()

    # Patterns indicating shared state
    patterns = [
        r'job_tracker',
        r'\.post\(.*/api/jobs',
        r'JobTracker\(',
        r'TRACKING_FILE',
    ]

    # Parse AST to find test functions
    tree = ast.parse(content)
    tests_needing_marker = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            func_source = ast.get_source_segment(content, node)
            if any(re.search(pattern, func_source) for pattern in patterns):
                # Check if already has marker
                has_marker = any(
                    isinstance(d, ast.Name) and 'xdist_group' in ast.unparse(d)
                    for d in node.decorator_list
                )
                if not has_marker:
                    tests_needing_marker.append(node.name)

    return tests_needing_marker

def add_markers(file_path, test_names, group_name="tracker"):
    """Add @pytest.mark.xdist_group marker to specified tests."""
    with open(file_path) as f:
        lines = f.readlines()

    # Find test definitions and add marker
    for test_name in test_names:
        for i, line in enumerate(lines):
            if f'def {test_name}(' in line:
                # Insert marker before function
                indent = len(line) - len(line.lstrip())
                marker = ' ' * indent + f'@pytest.mark.xdist_group(name="{group_name}")\n'
                if marker not in lines[i-1]:
                    lines.insert(i, marker)
                break

    with open(file_path, 'w') as f:
        f.writelines(lines)

    return len(test_names)

if __name__ == '__main__':
    test_dir = Path('tests')
    fixed_count = 0

    for test_file in test_dir.rglob('test_*.py'):
        tests = detect_shared_state_tests(test_file)
        if tests:
            count = add_markers(test_file, tests)
            print(f"Added markers to {count} tests in {test_file}")
            fixed_count += count

    print(f"\nTotal: Fixed {fixed_count} tests")
```

---

### 2.2 CI Failure Analyzer

**File:** `scripts/analyze_ci_failure.py`

```python
#!/usr/bin/env python3
"""
Analyze CI failure logs and suggest fixes.
"""

import json
import re
import sys

KNOWN_PATTERNS = {
    'test_isolation': {
        'pattern': r'Expected \d+ .+, got \d+',
        'fix': 'add_xdist_group_markers',
        'script': 'scripts/fix_test_isolation.py'
    },
    'import_error': {
        'pattern': r'ImportError:|ModuleNotFoundError:',
        'fix': 'check_requirements',
        'script': 'scripts/fix_imports.py'
    },
    'async_mode': {
        'pattern': r'asyncio.*mode',
        'fix': 'update_pytest_config',
        'script': 'scripts/fix_async_config.py'
    }
}

def analyze_log(log_content):
    """Analyze failure log and identify issue type."""
    for issue_type, config in KNOWN_PATTERNS.items():
        if re.search(config['pattern'], log_content, re.IGNORECASE):
            return {
                'type': issue_type,
                'fix': config['fix'],
                'script': config['script'],
                'confidence': 'high'
            }

    return {
        'type': 'unknown',
        'fix': 'manual_investigation_needed',
        'confidence': 'low'
    }

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdin'

    with open(log_file) if log_file != '/dev/stdin' else sys.stdin as f:
        log_content = f.read()

    result = analyze_log(log_content)
    print(json.dumps(result, indent=2))
```

---

## 🎯 Immediate Actions (Next 30 Minutes)

### Fix Current CI Failure

```bash
# 1. Create fix branch
git checkout main
git pull
git checkout -b fix/test-tracker-flake-robust

# 2. Apply more robust fix to test_filter_tracked_jobs_by_status
# Add fixture-level cleanup, not just test-level
```

### Set Up First AI Agent

```bash
# 1. Create auto-fix workflow
touch .github/workflows/auto-fix-ci.yml

# 2. Create fixer scripts
mkdir -p scripts
touch scripts/fix_test_isolation.py
touch scripts/analyze_ci_failure.py
chmod +x scripts/*.py

# 3. Test locally
python scripts/fix_test_isolation.py
```

---

## 📊 Success Metrics

**By End of Today:**
- [ ] Current CI failure fixed
- [ ] Auto-fix workflow created
- [ ] At least 1 AI agent script working
- [ ] Documentation for adding new agents

**By End of Week:**
- [ ] 3+ AI agents operational
- [ ] Auto-fix handles 80% of common failures
- [ ] Feature development tasks automated
- [ ] Code review automation live

---

## 🚀 Next Steps

1. **Immediate:** Fix the flaky test (stronger isolation)
2. **Morning:** Create auto-fix workflow
3. **Afternoon:** Build AI task dispatcher
4. **Evening:** Test full automation pipeline

---

**Let's start with fixing the current issue, then build the automation so this doesn't happen again!**
