# TODO: Make Security Constants Configurable

**Priority**: P3 (Future Enhancement)
**Complexity**: Medium
**Estimated Time**: 2-3 hours

## Context

PR #94 introduced security hardening with bounded quantifiers to prevent ReDoS attacks in `src/app/email_parser.py`. The regex patterns use hardcoded limits like `{2,50}` for matching company names, job titles, etc.

**Current Pattern Constants:**

```python
_COMPANY_NAME = r"[A-Z][A-Za-z0-9\s&]{2,50}(?:Inc|LLC|Ltd|Corp)?"
_JOB_ROLE = r"Engineer|Developer|Manager|Designer|Analyst|Scientist"
_TITLE_BASE = r"[A-Z][A-Za-z\s]{2,50}"
_SENIORITY = r"Senior|Junior|Lead|Staff|Principal"
```

## Problem

1. **Hardcoded Limits**: The `{2,50}` bounds are security measures but may be too restrictive for some use cases
2. **No Customization**: Users can't adjust security vs. flexibility tradeoff
3. **Different Risk Profiles**: Some deployments need tighter security, others need broader matching

## Proposed Solution

### 1. Add Security Configuration Section to config.json

```json
{
  "security": {
    "regex_bounds": {
      "company_name_min": 2,
      "company_name_max": 50,
      "title_min": 2,
      "title_max": 50,
      "enabled": true
    },
    "redos_protection": {
      "enabled": true,
      "max_backtracking": 10000
    }
  }
}
```

### 2. Update email_parser.py to Use Configuration

```python
from app.config_manager import load_config

config = load_config()
security_config = config.get("security", {})
regex_bounds = security_config.get("regex_bounds", {})

# Get configurable bounds with secure defaults
company_min = regex_bounds.get("company_name_min", 2)
company_max = regex_bounds.get("company_name_max", 50)
title_min = regex_bounds.get("title_min", 2)
title_max = regex_bounds.get("title_max", 50)

# Pattern components with configurable bounds
_COMPANY_NAME = rf"[A-Z][A-Za-z0-9\s&]{{{company_min},{company_max}}}(?:Inc|LLC|Ltd|Corp)?"
_TITLE_BASE = rf"[A-Z][A-Za-z\s]{{{title_min},{title_max}}}"
```

### 3. Add Validation

```python
def validate_regex_bounds(config: dict) -> None:
    """Validate security configuration bounds."""
    bounds = config.get("security", {}).get("regex_bounds", {})

    # Minimum values must be at least 1
    if bounds.get("company_name_min", 2) < 1:
        raise ValueError("company_name_min must be at least 1")

    # Maximum values must be reasonable (prevent ReDoS)
    if bounds.get("company_name_max", 50) > 200:
        logger.warning("company_name_max > 200 may cause ReDoS issues")

    # Min must be less than max
    if bounds.get("company_name_min", 2) >= bounds.get("company_name_max", 50):
        raise ValueError("company_name_min must be less than company_name_max")
```

### 4. Documentation

Update `docs/SECURITY.md`:

```markdown
## Configurable Security Settings

### Regex Bounds (ReDoS Protection)

The email parser uses bounded quantifiers to prevent Regular Expression Denial of Service (ReDoS) attacks. These bounds are configurable in `config.json`:

**Default Settings (Recommended):**
- Company name: 2-50 characters
- Job title: 2-50 characters

**Adjusting for Your Use Case:**
- **Tighter Security**: Reduce max values (e.g., 30)
- **Broader Matching**: Increase max values (up to 200, with caution)
- **Disable**: Set `enabled: false` (NOT recommended for production)

**Risk Assessment:**
- Bounds < 100: Low ReDoS risk
- Bounds 100-200: Medium risk (monitor performance)
- Bounds > 200: High risk (may cause significant slowdowns)
```

## Implementation Steps

- [ ] Add `security` section to `config.json` schema
- [ ] Update `config_manager.py` with validation
- [ ] Modify `email_parser.py` to use configurable bounds
- [ ] Add tests for configuration validation
- [ ] Add tests for different bound settings
- [ ] Update `docs/SECURITY.md` with configuration guide
- [ ] Update `.env.example` if needed
- [ ] Add migration guide for existing deployments

## Related TODOs

- **email_parser.py line 84**: Make `_JOB_ROLE` and `_SENIORITY` configurable per industry
- **email_parser.py line 113**: Make `JOB_BOARD_DOMAINS` configurable
- **email_parser.py line 126**: Make `ATS_DOMAINS` configurable

## Testing Strategy

```python
def test_custom_regex_bounds():
    """Test email parser with custom security bounds."""
    config = {
        "security": {
            "regex_bounds": {
                "company_name_min": 3,
                "company_name_max": 30,
                "enabled": True
            }
        }
    }
    # Test with 2-char company name (should fail with min=3)
    # Test with 50-char company name (should fail with max=30)
    # Test with valid 15-char company name (should pass)
```

## Benefits

1. **Flexibility**: Users can adjust security vs. matching tradeoff
2. **Risk Management**: Different deployments have different threat models
3. **Testing**: Easier to test edge cases by adjusting bounds
4. **Future-Proof**: Can adapt to new threat patterns without code changes

## Risks

1. **Misconfiguration**: Users might disable protection inadvertently
2. **Complexity**: More configuration surface area
3. **Documentation Burden**: Need clear guidance on safe values

## Mitigation

- Set secure defaults (current values)
- Add validation with warnings
- Provide risk assessment in documentation
- Log configuration at startup
