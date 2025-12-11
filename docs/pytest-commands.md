# Pytest Quick Reference & Commands
# All pytest configuration is now in pyproject.toml under [tool.pytest.ini_options]

[command-aliases]
# Fast feedback - Run only changed tests
fast = "pytest --picked --maxfail=1 --ff"

# Unit tests only - Pure functions, no I/O (<30s target)
unit = "pytest -m unit -n auto --maxfail=3"

# Quick smoke test - Run failed tests first, stop at first failure
smoke = "pytest --ff --maxfail=1 -x"

# Full suite - All tests including slow ones
all = "pytest -m '' --slow"

# Coverage - Run with coverage report
cov = "pytest --cov=src/app --cov-report=term-missing --cov-report=html"

# Profile - Find slowest tests
profile = "pytest --durations=20 --durations-min=1.0"

# Watch mode - Rerun on file changes (requires pytest-watch)
watch = "ptw -- --maxfail=1 --ff"

[quick-commands]
# Quick test commands (copy-paste ready)
# pytest --picked           # Only changed files (FASTEST - ~10-30s)
# pytest -m unit           # Unit tests only (~30-60s)
# pytest --ff --maxfail=1  # Failed first, stop fast (~varies)
# pytest -m "not slow"     # Skip slow tests (DEFAULT - ~2min)
# pytest                   # Full suite (~2.5min)
# pytest --durations=20    # Profile slowest tests

[notes]
# Configuration has been consolidated into pyproject.toml
# See [tool.pytest.ini_options] section in pyproject.toml for all settings
# This file is just a reference for commonly used commands
