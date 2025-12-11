#!/usr/bin/env python3
"""Email parser and classifier for job-related emails.

Classifies inbound emails into:
- job_listing: LinkedIn/Indeed/Monster job alerts
- application_confirm: Workday/Greenhouse/Lever receipts
- recruiter_outreach: Personal emails with job offers
"""
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmailType(Enum):
    """Email classification types."""

    JOB_LISTING = "job_listing"
    APPLICATION_CONFIRM = "application_confirm"
    RECRUITER_OUTREACH = "recruiter_outreach"
    UNKNOWN = "unknown"


@dataclass
class ParsedEmail:
    """Parsed email with extracted job information."""

    email_type: EmailType
    subject: str
    from_addr: str
    to_addr: str
    date: datetime
    body: str

    # Extracted fields
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    application_url: Optional[str] = None
    job_description: Optional[str] = None
    confidence: float = 0.0  # Classification confidence 0-1


class EmailParser:
    """Parser for job-related emails."""

    # Email type detection patterns
    JOB_LISTING_PATTERNS = [
        r"jobs? you might be interested in",
        r"new jobs? alert",
        r"recommended (for you|jobs?)",
        r"jobs? matching your",
        r"\d+ new jobs?",
        r"daily job alert",
        r"job recommendations",
    ]

    APPLICATION_CONFIRM_PATTERNS = [
        r"application (received|submitted|confirmed)",
        r"thank you for (applying|your application)",
        r"we (received|got) your application",
        r"application status",
        r"your application to",
        r"successfully applied",
    ]

    RECRUITER_OUTREACH_PATTERNS = [
        r"I came across your profile",
        r"interested in discussing",
        r"opportunity (that|I)",
        r"would you be interested",
        r"recruiting for",
        r"I'm reaching out",
    ]

    # Company extraction patterns
    COMPANY_PATTERNS = [
        r"at ([A-Z][A-Za-z0-9\s&]+(?:Inc|LLC|Ltd|Corp)?)",
        r"with ([A-Z][A-Za-z0-9\s&]+(?:Inc|LLC|Ltd|Corp)?)",
        r"from ([A-Z][A-Za-z0-9\s&]+(?:Inc|LLC|Ltd|Corp)?)",
    ]

    # Job title patterns
    TITLE_PATTERNS = [
        r"(?:position|role|opportunity):\s*([A-Z][A-Za-z\s]+(?:Engineer|Developer|Manager|Designer|Analyst|Scientist))",
        r"(?:applying|applied)\s+(?:to|for)\s+(?:the\s+)?([A-Z][A-Za-z\s]+(?:Engineer|Developer|Manager|Designer|Analyst|Scientist))",
        r"([A-Z][A-Za-z\s]+(?:Engineer|Developer|Manager|Designer|Analyst|Scientist))\s+(?:at|with|position)",
        r"(?:Senior|Junior|Lead|Staff|Principal)\s+([A-Z][A-Za-z\s]+)",
    ]

    # URL patterns for job boards
    URL_PATTERNS = [
        r"(https?://(?:www\.)?linkedin\.com/jobs/view/[^\s]+)",
        r"(https?://(?:www\.)?indeed\.com/(?:viewjob|rc/clk)[^\s]+)",
        r"(https?://(?:www\.)?glassdoor\.com/job[^\s]+)",
        r"(https?://[^\s]+/jobs?/[^\s]+)",
        r"(https?://[^\s]+\.(?:greenhouse|lever|workday)\.(?:io|com)[^\s]+)",
    ]

    # Known job board domains
    JOB_BOARD_DOMAINS = [
        "linkedin.com",
        "indeed.com",
        "monster.com",
        "glassdoor.com",
        "ziprecruiter.com",
        "dice.com",
        "simplyhired.com",
    ]

    # Known ATS domains
    ATS_DOMAINS = [
        "greenhouse.io",
        "lever.co",
        "workday.com",
        "icims.com",
        "myworkdayjobs.com",
        "ultipro.com",
        "jobvite.com",
    ]

    def __init__(self):
        """Initialize email parser."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.job_listing_regex = [re.compile(p, re.IGNORECASE) for p in self.JOB_LISTING_PATTERNS]
        self.application_confirm_regex = [re.compile(p, re.IGNORECASE) for p in self.APPLICATION_CONFIRM_PATTERNS]
        self.recruiter_outreach_regex = [re.compile(p, re.IGNORECASE) for p in self.RECRUITER_OUTREACH_PATTERNS]
        self.company_regex = [re.compile(p) for p in self.COMPANY_PATTERNS]
        self.title_regex = [re.compile(p) for p in self.TITLE_PATTERNS]
        self.url_regex = [re.compile(p) for p in self.URL_PATTERNS]

    def detect_email_type(self, subject: str, body: str, from_addr: str) -> tuple:
        """Classify email type.

        Args:
            subject: Email subject line
            body: Email body text
            from_addr: Sender email address

        Returns:
            Tuple of (EmailType, confidence)
        """
        text = f"{subject} {body}".lower()

        # Check for job listing patterns
        job_listing_score = sum(1 for p in self.job_listing_regex if p.search(text))
        # Check sender domain
        for domain in self.JOB_BOARD_DOMAINS:
            if domain in from_addr.lower():
                job_listing_score += 2

        # Check for application confirmation
        confirm_score = sum(1 for p in self.application_confirm_regex if p.search(text))
        for domain in self.ATS_DOMAINS:
            if domain in from_addr.lower():
                confirm_score += 2

        # Check for recruiter outreach
        recruiter_score = sum(1 for p in self.recruiter_outreach_regex if p.search(text))
        # Personal emails (not from job boards/ATS)
        is_personal = not any(d in from_addr.lower() for d in self.JOB_BOARD_DOMAINS + self.ATS_DOMAINS)
        if is_personal and recruiter_score > 0:
            recruiter_score += 1

        # Determine type with highest score
        scores = [
            (EmailType.JOB_LISTING, job_listing_score),
            (EmailType.APPLICATION_CONFIRM, confirm_score),
            (EmailType.RECRUITER_OUTREACH, recruiter_score),
        ]
        email_type, max_score = max(scores, key=lambda x: x[1])

        if max_score == 0:
            return EmailType.UNKNOWN, 0.0

        # Calculate confidence (normalize to 0-1)
        confidence = min(max_score / 5.0, 1.0)
        return email_type, confidence

    def extract_company_name(self, body: str, from_addr: str) -> Optional[str]:
        """Extract company name from email.

        Args:
            body: Email body text
            from_addr: Sender email address

        Returns:
            Company name if found
        """
        # Try extracting from email domain
        domain = from_addr.split("@")[-1].lower()
        if domain not in self.JOB_BOARD_DOMAINS + self.ATS_DOMAINS:
            # Personal/company domain
            company = domain.split(".")[0]
            if len(company) > 2:
                return company.title()

        # Try regex patterns in body
        for pattern in self.company_regex:
            match = pattern.search(body)
            if match:
                company = match.group(1).strip()
                # Filter out common false positives
                if len(company) > 2 and company.lower() not in ["the", "a", "an"]:
                    return company

        return None

    def extract_job_title(self, subject: str, body: str) -> Optional[str]:
        """Extract job title from email.

        Args:
            subject: Email subject line
            body: Email body text

        Returns:
            Job title if found
        """
        # Try subject first (most likely location)
        for pattern in self.title_regex:
            match = pattern.search(subject)
            if match:
                return match.group(1).strip()

        # Try body
        for pattern in self.title_regex:
            match = pattern.search(body[:500])  # First 500 chars
            if match:
                return match.group(1).strip()

        return None

    def extract_urls(self, body: str) -> List[str]:
        """Extract job-related URLs from email.

        Args:
            body: Email body text

        Returns:
            List of URLs found
        """
        urls = []
        for pattern in self.url_regex:
            matches = pattern.findall(body)
            urls.extend(matches)
        return list(set(urls))  # Remove duplicates

    def parse(
        self,
        subject: str,
        from_addr: str,
        to_addr: str,
        date: datetime,
        body: str,
    ) -> ParsedEmail:
        """Parse email and extract job information.

        Args:
            subject: Email subject
            from_addr: Sender address
            to_addr: Recipient address
            date: Email date
            body: Email body text

        Returns:
            Parsed email with extracted data
        """
        # Classify email type
        email_type, confidence = self.detect_email_type(subject, body, from_addr)

        # Extract job details
        company_name = self.extract_company_name(body, from_addr)
        job_title = self.extract_job_title(subject, body)
        urls = self.extract_urls(body)
        application_url = urls[0] if urls else None

        # Extract description (first paragraph or first 500 chars)
        lines = body.strip().split("\n")
        description_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:  # Skip short lines
                description_lines.append(line)
                if len("\n".join(description_lines)) > 500:
                    break
        job_description = "\n".join(description_lines[:5]) if description_lines else None

        parsed = ParsedEmail(
            email_type=email_type,
            subject=subject,
            from_addr=from_addr,
            to_addr=to_addr,
            date=date,
            body=body,
            company_name=company_name,
            job_title=job_title,
            application_url=application_url,
            job_description=job_description,
            confidence=confidence,
        )

        logger.info(
            "Parsed email: type=%s confidence=%.2f company=%s title=%s",
            email_type.value,
            confidence,
            company_name,
            job_title,
        )

        return parsed
