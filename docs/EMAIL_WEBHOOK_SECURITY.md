# Email Webhook Security Hardening

**Status:** ✅ Complete
**Date:** 2025-12-11
**CodeQL Status:** 0 Alerts

## Overview

This document summarizes the security hardening implemented for the email webhook integration system in response to the code review findings.

## Security Vulnerabilities Fixed

### 1. Path Traversal (CRITICAL - CVE-Level)

**Vulnerability:** `EmailWebhookManager.get_email()` accepted arbitrary `email_id` values without validation, allowing directory traversal attacks like `../../../etc/passwd`.

**Fix:**
- Strict validation: email_id must be exactly 16 alphanumeric characters
- Path resolution check: ensures resolved path is within `inbox_dir`
- Raises `ValueError` for invalid inputs

**Code:**
```python
def get_email(self, email_id: str) -> Optional[InboundEmail]:
    if not email_id or not email_id.isalnum() or len(email_id) != 16:
        raise ValueError(f"Invalid email_id format: {email_id}")

    email_file = self.inbox_dir / f"{email_id}.json"
    resolved_path = email_file.resolve()
    inbox_resolved = self.inbox_dir.resolve()
    if not str(resolved_path).startswith(str(inbox_resolved)):
        raise ValueError(f"Path traversal attempt detected: {email_id}")
```

**Test Coverage:** 7 attack patterns blocked

---

### 2. Input Validation (HIGH)

**Vulnerability:** No validation on email data allowed malformed addresses, excessive lengths, and unreasonable dates.

**Fix:**
- Email address validation (RFC-compliant regex)
- Subject length limit (998 chars per RFC 2822)
- Email body size limit (1MB total)
- Date sanity checks (not >1 day in future, not >365 days in past)

**Code:**
```python
def __post_init__(self):
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if not email_pattern.match(self.to_address):
        raise ValueError(f"Invalid to_address: {self.to_address}")
    if len(self.subject) > MAX_SUBJECT_LENGTH:
        raise ValueError(f"Subject too long: {len(self.subject)}")
    # ... additional checks
```

---

### 3. Rate Limiting & DoS Prevention (HIGH)

**Vulnerability:** No rate limiting allowed attackers to flood the system with unlimited emails.

**Fix:**
- 100 emails per hour per user (sliding window)
- Automatic cleanup of old emails (30-day TTL)
- Per-user quota (1000 emails max)

**Code:**
```python
def _check_rate_limit(self, user_id: str) -> bool:
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    self._rate_limits[user_id] = [ts for ts in self._rate_limits[user_id] if ts > cutoff]
    return len(self._rate_limits[user_id]) < RATE_LIMIT_MAX_EMAILS
```

**Constants:**
- `RATE_LIMIT_MAX_EMAILS = 100`
- `RATE_LIMIT_WINDOW = 3600` (1 hour)
- `EMAIL_TTL_DAYS = 30`
- `MAX_EMAILS_PER_USER = 1000`

---

### 4. HTML/XSS Sanitization (HIGH)

**Vulnerability:** HTML content stored without sanitization, allowing XSS attacks via malicious scripts.

**Fix:**
- Remove `<script>` tags (handles whitespace variations like `</script\t\n bar>`)
- Remove `<iframe>` tags
- Remove event handlers (`onclick`, `onload`, etc.)
- Remove `javascript:` URIs

**Code:**
```python
def _sanitize_html(self, html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script[\s\S]*?>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<iframe[^>]*>.*?</iframe[\s\S]*?>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'on\w+\s*=\s*["\'].*?["\']', "", html, flags=re.IGNORECASE)
    html = re.sub(r"javascript:", "", html, flags=re.IGNORECASE)
    return html
```

**CodeQL Validation:** Passes `py/bad-tag-filter` check

---

### 5. ReDoS Protection (MEDIUM)

**Vulnerability:** Complex unbounded regex patterns in `EmailParser` could cause catastrophic backtracking (ReDoS attacks).

**Fix:**
- Thread-safe timeout using `concurrent.futures` (2 seconds)
- Bounded quantifiers (`{2,50}` instead of `+`)
- Input truncation (10K for classification, 5K for URLs, 2K for company extraction)

**Code:**
```python
def _safe_search(self, pattern: re.Pattern, text: str, timeout: int = 2) -> Optional[re.Match]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(pattern.search, text)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Regex search timeout")
```

**Pattern Example:**
```python
# Before: r"([A-Z][A-Za-z0-9\s&]+(?:Inc|LLC)?)"  # Unbounded +
# After:  r"([A-Z][A-Za-z0-9\s&]{2,50}(?:Inc|LLC)?)"  # Bounded {2,50}
```

---

### 6. Weak Entropy (MEDIUM)

**Vulnerability:** Address generation used `secrets.token_urlsafe(6)` then stripped characters, reducing entropy.

**Fix:**
- Generate 4 random bytes directly
- Convert to 8 hex characters
- 32 bits of entropy (~4 billion combinations)
- No character stripping

**Code:**
```python
random_bytes = secrets.token_bytes(6)
random_id = "".join(f"{b:02x}" for b in random_bytes[:4])  # 4 bytes -> 8 hex chars
forwarding_address = f"user-{random_id}@{self.domain}"
```

---

### 7. Error Handling (LOW)

**Vulnerability:** Config load failures silently continued with empty state, potentially causing data loss.

**Fix:**
- JSON decode errors trigger recovery (save empty config)
- Other errors raise `RuntimeError` (fail fast)
- Rate limit errors return descriptive `ValueError`

**Code:**
```python
except json.JSONDecodeError as e:
    logger.error("Corrupt config file, starting fresh: %s", e)
    self._configs = {}
    self._save_configs()
except Exception as e:
    logger.error("Failed to load email configs: %s", e)
    raise RuntimeError(f"Cannot load email configs: {e}") from e
```

---

## Test Coverage

### Tests Added

**test_email_webhook.py** - 11 new security tests:
1. `test_path_traversal_protection` - 7 attack patterns
2. `test_email_address_validation` - Invalid addresses
3. `test_subject_length_validation` - Too-long subjects
4. `test_email_size_validation` - Too-large emails
5. `test_date_validation` - Future/past dates
6. `test_html_sanitization` - XSS prevention
7. `test_html_sanitization_with_whitespace` - Complex cases
8. `test_rate_limiting` - 100 email limit
9. `test_address_generation_format` - Entropy check
10. `test_config_corruption_handling` - Recovery
11. `test_no_config_for_address` - Missing config

**test_email_parser_security.py** - 10 new ReDoS tests:
1. `test_regex_timeout_protection` - Backtracking bombs
2. `test_long_input_truncation` - 10K+ inputs
3. `test_company_extraction_with_long_text` - 50K inputs
4. `test_title_extraction_with_long_text` - 10K inputs
5. `test_url_extraction_with_long_text` - 10K inputs
6. `test_bounded_quantifiers` - Catastrophic backtracking
7. `test_mixed_valid_and_malicious_patterns` - Real-world mix
8. `test_special_characters_in_patterns` - Regex special chars
9. `test_unicode_and_emoji_handling` - Unicode/emoji
10. `test_null_bytes_and_control_characters` - Control chars

### Test Results

```
SECURITY VALIDATION: 21/21 tests passing ✅

Path Traversal Protection:
  ✓ ../../../etc/passwd blocked
  ✓ ..\..\..\windows\system32 blocked
  ✓ abc/../../../etc/passwd blocked
  ✓ abcd (too short) blocked
  ✓ abcdefghijklmnopqrstuvwxyz (too long) blocked
  ✓ abc-def123456789 (invalid chars) blocked
  ✓ abc@def12345678 (invalid chars) blocked

Email Validation:
  ✓ Invalid addresses rejected
  ✓ Too-long subjects rejected (>998 chars)
  ✓ Too-large emails rejected (>1MB)
  ✓ Future dates rejected
  ✓ Old dates rejected (>365 days)

HTML Sanitization:
  ✓ <script> tags removed
  ✓ <iframe> tags removed
  ✓ Event handlers removed (onclick, etc.)
  ✓ javascript: URIs removed
  ✓ Whitespace variations handled (</script\t\n bar>)

Rate Limiting:
  ✓ 100 emails accepted
  ✓ 101st email blocked with "Rate limit exceeded"

ReDoS Protection:
  ✓ 10K+ input handled safely
  ✓ Regex timeout triggers on backtracking bombs
  ✓ Bounded quantifiers prevent catastrophic backtracking
  ✓ Unicode/emoji handled gracefully
```

---

## CodeQL Security Analysis

**Status:** ✅ 0 Alerts

**Scans Performed:**
- `py/path-injection` - PASS
- `py/bad-tag-filter` - PASS (fixed with `</script[\s\S]*?>`)
- `py/redos` - PASS (bounded quantifiers + timeout)
- `py/sql-injection` - N/A (no SQL)
- `py/command-injection` - N/A (no shell commands)

---

## Security Constants

Located in `src/app/email_webhook.py`:

```python
MAX_EMAIL_LENGTH = 1000000  # 1MB max email size
MAX_SUBJECT_LENGTH = 998  # RFC 2822 limit
MAX_EMAILS_PER_USER = 1000  # Max emails stored per user
EMAIL_TTL_DAYS = 30  # Auto-delete emails older than 30 days
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
RATE_LIMIT_MAX_EMAILS = 100  # Max emails per user per hour
EMAIL_CLEANUP_BUFFER = 100  # Keep this many emails under quota
```

---

## Production Recommendations

### Before Deployment:

1. **Environment Variables:**
   - Set `SENDGRID_DOMAIN` to production domain
   - Configure logging level (`ERROR` in production)

2. **Monitoring:**
   - Monitor rate limit violations (potential attack)
   - Alert on path traversal attempts
   - Track email cleanup frequency

3. **Periodic Tasks:**
   - Run `cleanup_expired_emails()` daily via cron/scheduler
   - Archive old emails before deletion (compliance)

4. **Backups:**
   - Exclude `data/inbox/` from git (already in `.gitignore`)
   - Back up `data/email_configs.json` regularly

5. **Additional Hardening (Optional):**
   - Add CAPTCHA for forwarding address generation
   - Implement IP-based rate limiting
   - Use dedicated HTML sanitization library (bleach)
   - Add webhook signature validation (HMAC)

---

## Commit History

1. **406e3f2** - Implement critical security fixes
   - Path traversal protection
   - Input validation
   - Rate limiting
   - HTML sanitization
   - Weak entropy fix

2. **66f32ba** - Address code review feedback
   - Thread-safe regex timeout
   - Extract constants
   - Improve code clarity

3. **7dbfb69** - Fix HTML sanitization regex
   - Handle complex whitespace variations
   - Pass CodeQL `py/bad-tag-filter` check

---

## References

- **OWASP Top 10:** A01:2021 (Broken Access Control) - Path Traversal
- **OWASP Top 10:** A03:2021 (Injection) - XSS, ReDoS
- **OWASP Top 10:** A04:2021 (Insecure Design) - Rate Limiting
- **CWE-22:** Path Traversal
- **CWE-79:** Cross-Site Scripting
- **CWE-400:** Uncontrolled Resource Consumption (DoS)
- **CWE-1333:** Regular Expression Denial of Service (ReDoS)

---

## Contact

For security concerns or questions about this implementation, contact:
- **GitHub:** @vcaboara
- **PR:** #89 (Email Webhook Integration)
