#!/usr/bin/env python3
"""Email integration for automated job application tracking.

This module provides IMAP integration to monitor sent emails and
automatically update job application status in the tracking system.

Features:
- IMAP connection to Gmail/Outlook
- Email parsing for application confirmations
- Auto-update job status when applications sent
- Email template system for outreach
"""
import email
import imaplib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from typing import Dict, List, Optional, Tuple

from app.job_tracker import JobTracker

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email server configuration."""

    imap_server: str
    email_address: str
    password: str
    port: int = 993
    use_ssl: bool = True
    folder: str = "INBOX"


@dataclass
class ParsedEmail:
    """Parsed email data."""

    subject: str
    from_addr: str
    to_addr: str
    date: datetime
    body: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    application_url: Optional[str] = None


class EmailIntegration:
    """Email integration for job application tracking."""

    def __init__(self, config: EmailConfig):
        """Initialize email integration.

        Args:
            config: Email server configuration
        """
        self.config = config
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.tracker = JobTracker()

    def connect(self) -> bool:
        """Connect to email server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.config.imap_server, self.config.port)
            else:
                self.connection = imaplib.IMAP4(self.config.imap_server, self.config.port)

            self.connection.login(self.config.email_address, self.config.password)
            logger.info(f"Connected to {self.config.imap_server}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False

    def disconnect(self):
        """Disconnect from email server."""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

    def fetch_recent_sent_emails(self, days: int = 7) -> List[ParsedEmail]:
        """Fetch recent sent emails.

        Args:
            days: Number of days to look back

        Returns:
            List of parsed emails
        """
        if not self.connection:
            logger.error("Not connected to email server")
            return []

        try:
            # Select sent folder (Gmail uses "[Gmail]/Sent Mail")
            sent_folders = ["INBOX.Sent", "[Gmail]/Sent Mail", "Sent", "Sent Items"]

            folder_selected = False
            for folder in sent_folders:
                try:
                    self.connection.select(folder)
                    folder_selected = True
                    logger.info(f"Selected folder: {folder}")
                    break
                except Exception:
                    continue

            if not folder_selected:
                logger.error("Could not select sent folder")
                return []

            # Search for emails from last N days
            from datetime import timedelta

            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            _, message_ids = self.connection.search(None, f"SINCE {since_date}")

            emails = []
            for msg_id in message_ids[0].split():
                try:
                    parsed = self._fetch_and_parse_email(msg_id)
                    if parsed:
                        emails.append(parsed)
                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {e}")
                    continue

            logger.info(f"Fetched {len(emails)} emails")
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    def _fetch_and_parse_email(self, msg_id: bytes) -> Optional[ParsedEmail]:
        """Fetch and parse a single email.

        Args:
            msg_id: Email message ID

        Returns:
            Parsed email or None
        """
        try:
            _, msg_data = self.connection.fetch(msg_id, "(RFC822)")
            email_body = msg_data[0][1]
            message = email.message_from_bytes(email_body)

            # Decode subject
            subject = self._decode_header(message.get("Subject", ""))
            from_addr = message.get("From", "")
            to_addr = message.get("To", "")
            date_str = message.get("Date", "")

            # Parse date
            try:
                date = email.utils.parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            # Extract body
            body = self._extract_body(message)

            # Extract job application details
            company_name = self._extract_company_name(to_addr, body)
            job_title = self._extract_job_title(subject, body)
            application_url = self._extract_application_url(body)

            return ParsedEmail(
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                date=date,
                body=body,
                company_name=company_name,
                job_title=job_title,
                application_url=application_url,
            )

        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """Decode email header.

        Args:
            header: Raw header string

        Returns:
            Decoded header
        """
        if not header:
            return ""

        decoded_parts = decode_header(header)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="ignore")
            else:
                result += part
        return result

    def _extract_body(self, message: email.message.Message) -> str:
        """Extract email body text.

        Args:
            message: Email message

        Returns:
            Body text
        """
        body = ""

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        continue
        else:
            try:
                body = message.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                pass

        return body

    def _extract_company_name(self, to_addr: str, body: str) -> Optional[str]:
        """Extract company name from email.

        Args:
            to_addr: Recipient email address
            body: Email body

        Returns:
            Company name if found
        """
        # Try to extract from email domain
        if "@" in to_addr:
            domain = to_addr.split("@")[1].split(".")[0]
            # Clean up common patterns
            domain = domain.replace("careers", "").replace("jobs", "")
            if domain and len(domain) > 2:
                return domain.capitalize()

        # Try to find company name in body
        patterns = [
            r"application at ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"position at ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"role at ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                return match.group(1)

        return None

    def _extract_job_title(self, subject: str, body: str) -> Optional[str]:
        """Extract job title from email.

        Args:
            subject: Email subject
            body: Email body

        Returns:
            Job title if found
        """
        # Common subject patterns
        patterns = [
            r"Application for (.+?)(?:\||$)",
            r"(.+?) - Job Application",
            r"(.+?) Position",
            r"Application: (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_application_url(self, body: str) -> Optional[str]:
        """Extract application URL from email body.

        Args:
            body: Email body

        Returns:
            Application URL if found
        """
        # Find URLs in body
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)

        # Filter for job-related URLs
        job_keywords = ["greenhouse", "lever", "workday", "careers", "jobs", "apply", "application", "taleo"]

        for url in urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in job_keywords):
                return url

        return None

    def match_emails_to_jobs(self, emails: List[ParsedEmail]) -> List[Tuple[ParsedEmail, Optional[str]]]:
        """Match sent emails to tracked jobs.

        Args:
            emails: List of parsed emails

        Returns:
            List of (email, job_id) tuples
        """
        matches = []
        tracked_jobs = self.tracker.get_all_jobs()

        for email_data in emails:
            job_id = None

            # Try to match by company name
            if email_data.company_name:
                for job in tracked_jobs:
                    if job.get("company", "").lower() == email_data.company_name.lower():
                        job_id = job.get("job_id")
                        break

            # Try to match by job title
            if not job_id and email_data.job_title:
                for job in tracked_jobs:
                    if email_data.job_title.lower() in job.get("title", "").lower():
                        job_id = job.get("job_id")
                        break

            # Try to match by URL
            if not job_id and email_data.application_url:
                for job in tracked_jobs:
                    job_link = job.get("link", "")
                    company_link = job.get("company_link", "")
                    if email_data.application_url in job_link or email_data.application_url in company_link:
                        job_id = job.get("job_id")
                        break

            matches.append((email_data, job_id))

        return matches

    def auto_update_job_status(self, days: int = 7) -> Dict[str, int]:
        """Automatically update job status from sent emails.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with update statistics
        """
        stats = {"emails_checked": 0, "jobs_updated": 0, "jobs_not_found": 0}

        if not self.connect():
            logger.error("Could not connect to email server")
            return stats

        try:
            # Fetch recent sent emails
            emails = self.fetch_recent_sent_emails(days)
            stats["emails_checked"] = len(emails)

            # Match emails to jobs
            matches = self.match_emails_to_jobs(emails)

            # Update job status
            for email_data, job_id in matches:
                if job_id:
                    self.tracker.update_job_status(
                        job_id, "applied", f"Auto-updated from email sent on {email_data.date.strftime('%Y-%m-%d')}"
                    )
                    stats["jobs_updated"] += 1
                    logger.info(f"Updated job {job_id} to 'applied'")
                else:
                    stats["jobs_not_found"] += 1
                    logger.warning(
                        f"Could not match email to job: " f"{email_data.company_name} - {email_data.job_title}"
                    )

            return stats

        finally:
            self.disconnect()


def create_email_config_from_env() -> Optional[EmailConfig]:
    """Create email configuration from environment variables.

    Returns:
        EmailConfig if credentials available, None otherwise
    """
    import os

    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if not email_address or not email_password:
        return None

    return EmailConfig(imap_server=imap_server, email_address=email_address, password=email_password)
