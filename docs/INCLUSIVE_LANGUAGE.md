# Inclusive Language Guide

This project uses automated checks to promote inclusive and welcoming language in our codebase and documentation.

## Why Inclusive Language Matters

Using inclusive language:
- Creates a welcoming environment for all contributors
- Improves clarity and precision in technical communication
- Aligns with industry best practices and modern standards
- Demonstrates respect for diverse backgrounds and experiences

## Automated Checking

The project includes a pre-commit hook (`inclusive-language`) that automatically scans changed files for potentially non-inclusive terms and suggests alternatives.

### How It Works

When you commit code, the checker runs automatically and will:
1. ✅ Allow the commit if no issues found
2. ⚠️  Block the commit if non-inclusive language detected
3. 💡 Suggest inclusive alternatives

### Common Replacements

| Avoid                    | Use Instead                    | Context             |
| ------------------------ | ------------------------------ | ------------------- |
| whitelist                | allowlist, passlist            | Access control      |
| blacklist                | denylist, blocklist            | Access control      |
| master (database/server) | primary, leader                | System architecture |
| slave (database/server)  | replica, secondary, follower   | System architecture |
| grandfathered            | legacy status, exempted        | Legacy systems      |
| man-hours                | person-hours, work-hours       | Time tracking       |
| sanity check             | confidence check, verification | Testing             |
| dummy data               | placeholder, sample, mock      | Test data           |

### Legitimate Exceptions

Some terms are acceptable in specific contexts:

**Git Branches:**
- ✅ `main` branch (preferred)
- ✅ `master` branch (legacy, transitioning)

**Proper Names:**
- ✅ "Task Master" (tool/extension name)
- ✅ "Scrum Master" (official role title)
- ✅ "React Native" (framework name)

**Technical Terms:**
- ✅ "native" when referring to built-in/core functionality

## Handling False Positives

If the checker flags legitimate usage, you have several options:

### 1. Inline Comment (Recommended)
Add a comment on the same line:
```python
master_config = load_config()  # inclusive-language: ignore
```

### 2. Update Exclusion Patterns
Edit `scripts/check_inclusive_language.py` and add to `EXCLUDE_PATTERNS`:
```python
EXCLUDE_PATTERNS = [
    r'(?:main|master)\s*[\'"]?\s*(?:branch)?',  # Git branches
    r'Your\s+Pattern\s+Here',  # Your justification
]
```

### 3. Configuration File
See `.github/inclusive-language.yaml` for comprehensive guidelines and exceptions.

## Manual Check

Run the checker manually on specific files:
```bash
python scripts/check_inclusive_language.py path/to/file.py
```

Run on all Python files:
```bash
python scripts/check_inclusive_language.py src/**/*.py
```

## Disable for Specific Commit

If you need to bypass the check (not recommended):
```bash
git commit --no-verify -m "Your message"
```

## Resources

- [Google Developer Documentation Style Guide - Inclusive Documentation](https://developers.google.com/style/inclusive-documentation)
- [Microsoft Style Guide - Bias-free Communication](https://docs.microsoft.com/en-us/style-guide/bias-free-communication)
- [Inclusive Naming Initiative](https://inclusivenaming.org/)

## Feedback

If you believe a term should be added to or removed from the checker, please:
1. Open an issue with your suggestion
2. Provide context and reasoning
3. Suggest the alternative terminology

We welcome feedback to make our language more inclusive and our tools more effective!
