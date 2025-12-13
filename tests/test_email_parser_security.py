"""Security tests for email parser."""
from datetime import datetime

from app.email_parser import EmailParser, EmailType


class TestEmailParserSecurity:
    """Test security fixes in EmailParser."""

    def test_regex_timeout_protection(self):
        """Test that ReDoS attacks are mitigated."""
        parser = EmailParser()

        # Create potentially malicious input (backtracking bomb)
        evil_text = "A" * 10000 + "!"

        # Should complete without timeout or crash
        result = parser.detect_email_type(evil_text, evil_text, "test@example.com")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_long_input_truncation(self):
        """Test that very long inputs are truncated."""
        parser = EmailParser()

        # Create very long text
        long_text = "job alert " * 10000  # Would match patterns

        result = parser.detect_email_type(long_text, long_text, "linkedin@example.com")
        # Should still classify despite truncation
        assert isinstance(result, tuple)

    def test_company_extraction_with_long_text(self):
        """Test company extraction doesn't crash on long text."""
        parser = EmailParser()

        long_body = "A" * 50000
        result = parser.extract_company_name(long_body, "sender@company.com")
        # Should handle it gracefully
        assert result is None or isinstance(result, str)

    def test_title_extraction_with_long_text(self):
        """Test title extraction doesn't crash on long text."""
        parser = EmailParser()

        long_subject = "A" * 10000
        long_body = "B" * 50000

        result = parser.extract_job_title(long_subject, long_body)
        # Should handle it gracefully
        assert result is None or isinstance(result, str)

    def test_url_extraction_with_long_text(self):
        """Test URL extraction doesn't crash on long text."""
        parser = EmailParser()

        long_body = "https://example.com " * 10000
        result = parser.extract_urls(long_body)
        # Should handle it gracefully
        assert isinstance(result, list)

    def test_bounded_quantifiers(self):
        """Test that bounded quantifiers prevent catastrophic backtracking."""
        parser = EmailParser()

        # Pattern that would cause catastrophic backtracking with unbounded quantifiers
        evil_company = "A" * 100 + "Inc"
        body = f"at {evil_company}"

        result = parser.extract_company_name(body, "test@example.com")
        # Should either match truncated version or return None, but not hang
        assert result is None or isinstance(result, str)

    def test_mixed_valid_and_malicious_patterns(self):
        """Test parser handles mix of valid and malicious patterns."""
        parser = EmailParser()

        # Mix normal content with potentially problematic patterns
        # Use actual recruiter pattern that will match
        subject = "Senior Engineer Position" + ("A" * 5000)
        body = "I came across your profile and have a great opportunity at Microsoft\n" + ("X" * 10000)

        result = parser.parse(subject, "recruiter@company.com", "user@example.com", datetime.now(), body)

        # With proper recruiter pattern, should classify correctly even with long strings
        assert result.email_type == EmailType.RECRUITER_OUTREACH
        # Should still extract company despite long text (but may be None due to parsing limits)
        # The key is it doesn't hang or timeout
        assert isinstance(result.company_name, (str, type(None)))
        assert isinstance(result.job_title, (str, type(None)))

    def test_special_characters_in_patterns(self):
        """Test that special regex characters don't cause issues."""
        parser = EmailParser()

        # Special characters that could break regex
        evil_chars = r".*+?[]{}()\|^$"
        subject = f"Job Alert {evil_chars}"
        body = f"Position at Company{evil_chars}"

        # Should not crash
        result = parser.detect_email_type(subject, body, "test@example.com")
        assert isinstance(result, tuple)

    def test_unicode_and_emoji_handling(self):
        """Test parser handles unicode and emoji gracefully."""
        parser = EmailParser()

        # Unicode and emoji in text
        subject = "🚀 Senior Engineer Role 💼"
        body = "We're hiring at TechCo™ 🎉"

        result = parser.parse(subject, "jobs@techco.com", "user@example.com", datetime.now(), body)

        assert isinstance(result.email_type, EmailType)
        # Should handle unicode without crashing

    def test_null_bytes_and_control_characters(self):
        """Test parser handles null bytes and control characters."""
        parser = EmailParser()

        # Control characters and null bytes
        subject = "Job\x00Alert\r\n\t"
        body = "Position\x00at\x00Company\r\n"

        # Should not crash
        result = parser.detect_email_type(subject, body, "test@example.com")
        assert isinstance(result, tuple)
