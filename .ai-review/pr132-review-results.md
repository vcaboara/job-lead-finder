# Code Review: PR #132 - Version Bump Verification Script

## Issues Found

### 1. **Print Statements Instead of Logging** ❌
**Lines:** 151, 153, 158, 166, 167, 177-184, 191, 195-213, 220-247, 256-284

**Problem:** Uses `print()` throughout instead of proper logging module.

**Fix:**
```python
# Add at top of file:
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Replace all print() calls:
# Before:
print("🧪 Testing Version Bump Logic")
print(f"✅ Bump type: {actual_bump}")

# After:
logger.info("Testing Version Bump Logic")
logger.info(f"Bump type: {actual_bump}")
```

### 2. **Complex If/Else Chains** ⚠️
**Lines:** 43-51 (`determine_bump_type`)

**Problem:** Multiple conditions in if/elif can be simplified.

**Fix:**
```python
# Before:
def determine_bump_type(pr_title: str, pr_labels: list) -> str:
    labels_str = ",".join(pr_labels)
    if any(label in labels_str for label in ["major", "breaking-change"]) or "BREAKING CHANGE" in pr_title:
        return "major"
    elif any(label in labels_str for label in ["minor"]) or any(
        pr_title.startswith(prefix) for prefix in ["feat:", "feat("]
    ):
        return "minor"
    else:
        return "patch"

# After:
BUMP_TYPE_RULES = {
    "major": {
        "labels": ["major", "breaking-change"],
        "title_contains": ["BREAKING CHANGE"]
    },
    "minor": {
        "labels": ["minor"],
        "title_prefixes": ["feat:", "feat("]
    }
}

def determine_bump_type(pr_title: str, pr_labels: list) -> str:
    """Determine version bump type using rule-based approach."""
    labels_str = ",".join(pr_labels)

    for bump_type, rules in BUMP_TYPE_RULES.items():
        # Check labels
        if any(label in labels_str for label in rules.get("labels", [])):
            return bump_type
        # Check title keywords
        if any(keyword in pr_title for keyword in rules.get("title_contains", [])):
            return bump_type
        # Check title prefixes
        if any(pr_title.startswith(prefix) for prefix in rules.get("title_prefixes", [])):
            return bump_type

    return "patch"  # default
```

### 3. **Repeated Code** 🔄
**Lines:** 155-159, 220-224 (pyproject.toml reading)

**Problem:** Same code to read pyproject.toml duplicated.

**Fix:**
```python
def _read_pyproject() -> tuple[Path, str]:
    """Read pyproject.toml file and return path and content."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    return pyproject_path, pyproject_path.read_text()

# Use in test_version_bump_logic():
try:
    pyproject_path, original_content = _read_pyproject()
    current_version = get_current_version(original_content)
except FileNotFoundError as e:
    logger.error(str(e))
    return False
```

### 4. **Loop Improvements** 🔁
**Lines:** 162-177 (test scenario loop)

**Problem:** Loop does too much, hard to read.

**Fix:**
```python
def _test_single_scenario(scenario: dict, current_version: str) -> bool:
    """Test a single PR scenario for version bumping."""
    logger.info(f"Scenario: {scenario['title']}")
    logger.info(f"Labels: {scenario['labels']}")

    actual_bump = determine_bump_type(scenario["title"], scenario["labels"])
    expected_bump = scenario["expected_bump"]

    if actual_bump != expected_bump:
        logger.error(f"Bump type mismatch: expected {expected_bump}, got {actual_bump}")
        return False

    logger.info(f"✅ Bump type: {actual_bump}")
    new_version = increment_version(current_version, actual_bump)
    logger.info(f"   New version: {current_version} → {new_version}")
    return True

def test_version_bump_logic():
    """Test the core version bump logic with various scenarios."""
    logger.info("Testing Version Bump Logic")
    logger.info("=" * 50)

    try:
        _, original_content = _read_pyproject()
        current_version = get_current_version(original_content)
    except FileNotFoundError:
        return False

    logger.info(f"Current version: {current_version}")

    results = [
        _test_single_scenario(scenario, current_version)
        for scenario in TEST_PR_SCENARIOS
    ]

    return all(results)
```

### 5. **Error Handling** ⚠️
**Lines:** Multiple locations

**Problem:** Bare except clauses, not handling specific errors.

**Fix:**
```python
# Before (line 269):
try:
    subprocess.run(["gh", "--version"], capture_output=True, check=True)
    gh_available = True
except (subprocess.CalledProcessError, FileNotFoundError, OSError):
    gh_available = False

# After:
def _check_gh_cli_available() -> bool:
    """Check if GitHub CLI is available."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"gh command failed: {e}")
        return False
    except (FileNotFoundError, OSError) as e:
        logger.error(f"gh CLI not installed: {e}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("gh CLI check timed out")
        return False
```

## Summary

**Critical Issues:**
- ❌ All output uses `print()` instead of `logging`
- ⚠️ Complex conditionals in bump type detection
- 🔄 Duplicated pyproject.toml reading code

**Recommended Changes:**
1. Add logging module (priority 1)
2. Extract bump type rules to dictionary (priority 2)
3. Create helper functions to reduce duplication (priority 3)
4. Improve error handling with specific exceptions (priority 4)
5. Break down long functions into smaller testable units (priority 5)

**Est. Time:** 30-45 minutes to implement all improvements
