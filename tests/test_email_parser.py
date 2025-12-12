"""Tests for email parser and classifier."""
from datetime import datetime

import pytest

from app.email_parser import EmailParser, EmailType


class TestEmailParser:
    """Test EmailParser classification and extraction."""

    def test_init(self):
        """Test parser initialization."""
        parser = EmailParser()
        assert parser is not None
        assert len(parser.job_listing_regex) > 0

    def test_detect_linkedin_job_listing(self):
        """Test LinkedIn job alert detection."""
        parser = EmailParser()

        subject = "10 new jobs for Software Engineer"
        body = "Here are jobs you might be interested in:\n\nSenior Software Engineer at TechCorp"
        from_addr = "jobs@linkedin.com"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.JOB_LISTING
        assert confidence > 0.5

    def test_detect_indeed_job_listing(self):
        """Test Indeed job alert detection."""
        parser = EmailParser()

        subject = "Daily Job Alert: Python Developer"
        body = "New jobs matching your search:\n\nPython Developer at StartupCo"
        from_addr = "noreply@indeed.com"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.JOB_LISTING
        assert confidence > 0.5

    def test_detect_workday_confirmation(self):
        """Test Workday application confirmation."""
        parser = EmailParser()

        subject = "Application received for Senior Engineer"
        body = "Thank you for applying to Senior Engineer at BigCompany"
        from_addr = "noreply@myworkdayjobs.com"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.APPLICATION_CONFIRM
        assert confidence > 0.5

    def test_detect_greenhouse_confirmation(self):
        """Test Greenhouse application confirmation."""
        parser = EmailParser()

        subject = "Application Status"
        body = "We received your application for Software Engineer"
        from_addr = "no-reply@greenhouse.io"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.APPLICATION_CONFIRM
        assert confidence > 0.5

    def test_detect_recruiter_outreach(self):
        """Test recruiter outreach detection."""
        parser = EmailParser()

        subject = "Exciting opportunity at TechCorp"
        body = "I came across your profile and thought you'd be interested in this role"
        from_addr = "recruiter@techcorp.com"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.RECRUITER_OUTREACH
        assert confidence > 0.0

    def test_detect_unknown_email(self):
        """Test unknown email type."""
        parser = EmailParser()

        subject = "Newsletter: Tech Industry Updates"
        body = "Here's what's happening in tech this week"
        from_addr = "newsletter@example.com"

        email_type, confidence = parser.detect_email_type(subject, body, from_addr)

        assert email_type == EmailType.UNKNOWN
        assert confidence == 0.0

    def test_extract_company_from_domain(self):
        """Test company extraction from email domain."""
        parser = EmailParser()

        company = parser.extract_company_name("", "recruiter@google.com")

        assert company == "Google"

    def test_extract_company_from_body(self):
        """Test company extraction from email body."""
        parser = EmailParser()

        body = "Apply for this position at Microsoft Corp"
        company = parser.extract_company_name(body, "jobs@linkedin.com")

        assert company == "Microsoft Corp"

    def test_extract_job_title_from_subject(self):
        """Test job title extraction from subject."""
        parser = EmailParser()

        subject = "Senior Software Engineer at TechCorp"
        body = ""

        title = parser.extract_job_title(subject, body)

        assert title is not None
        assert "Software Engineer" in title

    def test_extract_job_title_from_body(self):
        """Test job title extraction from body."""
        parser = EmailParser()

        subject = "Job opportunity"
        body = "We're hiring a Lead Data Scientist for our team"

        title = parser.extract_job_title(subject, body)

        assert title is not None
        assert "Data Scientist" in title

    def test_extract_linkedin_url(self):
        """Test LinkedIn job URL extraction."""
        parser = EmailParser()

        body = "Apply here: https://www.linkedin.com/jobs/view/123456789"

        urls = parser.extract_urls(body)

        assert len(urls) > 0
        assert "linkedin.com/jobs/view" in urls[0]

    def test_extract_indeed_url(self):
        """Test Indeed job URL extraction."""
        parser = EmailParser()

        body = "View job: https://www.indeed.com/viewjob?jk=abc123"

        urls = parser.extract_urls(body)

        assert len(urls) > 0
        assert "indeed.com/viewjob" in urls[0]

    def test_extract_greenhouse_url(self):
        """Test Greenhouse ATS URL extraction."""
        parser = EmailParser()

        body = "Apply at: https://boards.greenhouse.io/company/jobs/123456"

        urls = parser.extract_urls(body)

        assert len(urls) > 0
        assert "greenhouse.io" in urls[0]

    def test_parse_linkedin_alert(self):
        """Test full parsing of LinkedIn job alert."""
        parser = EmailParser()

        subject = "5 new jobs matching Software Engineer"
        from_addr = "jobs@linkedin.com"
        to_addr = "user-abc123@jobforge.com"
        date = datetime.now()
        body = """Here are jobs you might be interested in:

Senior Software Engineer at Google
https://www.linkedin.com/jobs/view/123456

Backend Engineer at Microsoft
https://www.linkedin.com/jobs/view/789012
"""

        parsed = parser.parse(subject, from_addr, to_addr, date, body)

        assert parsed.email_type == EmailType.JOB_LISTING
        assert parsed.confidence > 0.5
        assert parsed.application_url is not None
        assert "linkedin.com" in parsed.application_url

    def test_parse_workday_confirmation(self):
        """Test full parsing of Workday confirmation."""
        parser = EmailParser()

        subject = "Application Received: Senior Engineer"
        from_addr = "noreply@myworkdayjobs.com"
        to_addr = "user-abc123@jobforge.com"
        date = datetime.now()
        body = """Thank you for applying to the Senior Engineer position at Salesforce.

Your application has been successfully submitted.

Application ID: 12345
Position: Senior Engineer
Location: San Francisco, CA
"""

        parsed = parser.parse(subject, from_addr, to_addr, date, body)

        assert parsed.email_type == EmailType.APPLICATION_CONFIRM
        assert parsed.confidence > 0.5
        assert parsed.job_title is not None
        assert "Engineer" in parsed.job_title

    def test_parse_recruiter_outreach(self):
        """Test full parsing of recruiter outreach."""
        parser = EmailParser()

        subject = "Exciting opportunity at Netflix"
        from_addr = "recruiter@netflix.com"
        to_addr = "user-abc123@jobforge.com"
        date = datetime.now()
        body = """Hi there,

I came across your profile and thought you'd be a great fit for our
Staff Software Engineer position at Netflix.

We're looking for someone with your background in distributed systems.
Would you be interested in discussing this opportunity?

Best regards,
Jane Doe
Senior Technical Recruiter
"""

        parsed = parser.parse(subject, from_addr, to_addr, date, body)

        assert parsed.email_type == EmailType.RECRUITER_OUTREACH
        assert parsed.company_name == "Netflix"
        assert parsed.from_addr == from_addr

    def test_confidence_scoring(self):
        """Test confidence scoring with varying match counts."""
        parser = EmailParser()

        # High confidence - multiple patterns + domain match
        body1 = "New jobs alert! Here are jobs matching your preferences"
        type1, conf1 = parser.detect_email_type("", body1, "jobs@linkedin.com")

        # Medium confidence - one pattern
        body2 = "jobs you might be interested in"
        type2, conf2 = parser.detect_email_type("", body2, "sender@example.com")

        assert type1 == EmailType.JOB_LISTING
        assert type2 == EmailType.JOB_LISTING
        assert conf1 > conf2

    def test_extract_multiple_urls(self):
        """Test extraction of multiple URLs."""
        parser = EmailParser()

        body = """
        Job 1: https://www.linkedin.com/jobs/view/111
        Job 2: https://www.indeed.com/viewjob?jk=222
        Job 3: https://company.greenhouse.io/jobs/333
        """

        urls = parser.extract_urls(body)

        assert len(urls) >= 3
        assert any("linkedin" in url for url in urls)
        assert any("indeed" in url for url in urls)
        assert any("greenhouse" in url for url in urls)

    def test_parse_preserves_metadata(self):
        """Test that parsing preserves all metadata."""
        parser = EmailParser()

        subject = "Test Subject"
        from_addr = "test@example.com"
        to_addr = "user@jobforge.com"
        date = datetime.now()
        body = "Test body"

        parsed = parser.parse(subject, from_addr, to_addr, date, body)

        assert parsed.subject == subject
        assert parsed.from_addr == from_addr
        assert parsed.to_addr == to_addr
        assert parsed.date == date
        assert parsed.body == body
