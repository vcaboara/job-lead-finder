#!/usr/bin/env python3
"""Email processing service for job tracking integration.

Integrates EmailParser with JobTracker to automatically:
- Create jobs from job listing emails
- Update job status from application confirmations
- Handle recruiter outreach
"""
import logging
from typing import Dict, Optional

from .email_parser import EmailParser, EmailType, ParsedEmail
from .email_webhook import InboundEmail
from .job_tracker import STATUS_APPLIED, STATUS_NEW, JobTracker, get_tracker

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Process inbound emails and update job tracking."""

    def __init__(self, job_tracker: Optional[JobTracker] = None):
        """Initialize email processor.

        Args:
            job_tracker: JobTracker instance (uses global if not provided)
        """
        self.parser = EmailParser()
        self.tracker = job_tracker or get_tracker()

    def process_inbound_email(self, email: InboundEmail) -> Dict:
        """Process inbound email and update job tracking.

        Args:
            email: Inbound email data

        Returns:
            Processing result dict with actions taken
        """
        # Parse email
        parsed = self.parser.parse(
            subject=email.subject,
            from_addr=email.from_address,
            to_addr=email.to_address,
            date=email.received_at,
            body=email.body_text or "",
        )

        result = {
            "email_type": parsed.email_type.value,
            "confidence": parsed.confidence,
            "action": None,
            "job_id": None,
        }

        # Route based on email type
        if parsed.email_type == EmailType.JOB_LISTING:
            result.update(self._process_job_listing(parsed))
        elif parsed.email_type == EmailType.APPLICATION_CONFIRM:
            result.update(self._process_application_confirm(parsed))
        elif parsed.email_type == EmailType.RECRUITER_OUTREACH:
            result.update(self._process_recruiter_outreach(parsed))
        else:
            logger.info("Unknown email type, skipping: %s", email.subject)
            result["action"] = "skipped"

        return result

    def _process_job_listing(self, parsed: ParsedEmail) -> Dict:
        """Create job from job listing email.

        Args:
            parsed: Parsed email data

        Returns:
            Result dict with job_id and action
        """
        # Only process if confidence is high enough
        if parsed.confidence < 0.5:
            logger.info("Low confidence (%.2f), skipping job creation", parsed.confidence)
            return {"action": "skipped_low_confidence"}

        # Build job dict for tracker
        job_data = {
            "title": parsed.job_title or "Job from Email",
            "company": parsed.company_name or "Unknown Company",
            "location": "",  # Not extracted from email
            "summary": parsed.job_description or parsed.subject,
            "link": parsed.application_url or "",
            "source": f"email:{parsed.from_addr}",
        }

        # Track job
        job_id = self.tracker.track_job(job_data, status=STATUS_NEW)

        logger.info(
            "Created job %s from listing email: %s at %s",
            job_id,
            job_data["title"],
            job_data["company"],
        )

        return {
            "action": "created_job",
            "job_id": job_id,
            "title": job_data["title"],
            "company": job_data["company"],
        }

    def _process_application_confirm(self, parsed: ParsedEmail) -> Dict:
        """Update job status from application confirmation.

        Args:
            parsed: Parsed email data

        Returns:
            Result dict with job_id and action
        """
        # Try to match to existing job
        job_id = self._find_matching_job(parsed)

        if job_id:
            # Update status to applied
            success = self.tracker.update_status(
                job_id,
                STATUS_APPLIED,
                notes=f"Application confirmed via email on {parsed.date.isoformat()}",
            )

            if success:
                logger.info("Updated job %s to 'applied' from confirmation email", job_id)
                return {
                    "action": "updated_status",
                    "job_id": job_id,
                    "new_status": STATUS_APPLIED,
                }
        else:
            # Create new job in 'applied' status
            job_data = {
                "title": parsed.job_title or "Job from Application",
                "company": parsed.company_name or "Unknown Company",
                "location": "",
                "summary": parsed.job_description or parsed.subject,
                "link": parsed.application_url or "",
                "source": f"email:{parsed.from_addr}",
            }

            job_id = self.tracker.track_job(job_data, status=STATUS_APPLIED)

            logger.info(
                "Created job %s in 'applied' status from confirmation: %s at %s",
                job_id,
                job_data["title"],
                job_data["company"],
            )

            return {
                "action": "created_job_applied",
                "job_id": job_id,
                "title": job_data["title"],
                "company": job_data["company"],
            }

        return {"action": "no_match"}

    def _process_recruiter_outreach(self, parsed: ParsedEmail) -> Dict:
        """Handle recruiter outreach email.

        Args:
            parsed: Parsed email data

        Returns:
            Result dict with job_id and action
        """
        # Create job with high priority marker in notes
        job_data = {
            "title": parsed.job_title or "Recruiter Opportunity",
            "company": parsed.company_name or "Unknown Company",
            "location": "",
            "summary": parsed.job_description or parsed.subject,
            "link": parsed.application_url or "",
            "source": f"email:{parsed.from_addr}",
        }

        job_id = self.tracker.track_job(job_data, status=STATUS_NEW)

        # Add high-priority note
        self.tracker.update_notes(
            job_id,
            f"🔥 HIGH PRIORITY - Recruiter outreach from {parsed.from_addr}\n"
            f"Received: {parsed.date.isoformat()}\n"
            f"Original subject: {parsed.subject}",
        )

        logger.info(
            "Created high-priority job %s from recruiter outreach: %s",
            job_id,
            parsed.from_addr,
        )

        return {
            "action": "created_job_priority",
            "job_id": job_id,
            "title": job_data["title"],
            "company": job_data["company"],
            "from": parsed.from_addr,
        }

    def _find_matching_job(self, parsed: ParsedEmail) -> Optional[str]:
        """Find existing job that matches this email.

        Args:
            parsed: Parsed email data

        Returns:
            Job ID if found, None otherwise
        """
        # Get all tracked jobs (excluding hidden)
        all_jobs = self.tracker.get_all_jobs(include_hidden=False)

        # Match by URL first (most reliable)
        if parsed.application_url:
            for job in all_jobs:
                if job.get("link") == parsed.application_url:
                    return job["job_id"]

        # Match by company + title
        if parsed.company_name and parsed.job_title:
            company_lower = parsed.company_name.lower()
            title_lower = parsed.job_title.lower()

            for job in all_jobs:
                job_company = job.get("company", "").lower()
                job_title = job.get("title", "").lower()

                if company_lower in job_company and title_lower in job_title:
                    return job["job_id"]

        return None

    def store_training_data(self, email: InboundEmail, parsed: ParsedEmail) -> str:
        """Store email as ML training data.

        Args:
            email: Original inbound email
            parsed: Parsed email data

        Returns:
            Training data ID

        Note:
            This is a placeholder for future ML training data pipeline.
            Implementation would involve:
            - Storing email samples with classifications
            - Building labeled dataset for model improvement
            - Tracking classification accuracy over time
            - See GitHub issue #TBD for implementation roadmap
        """
        logger.debug("Training data storage not yet implemented")
        return ""
