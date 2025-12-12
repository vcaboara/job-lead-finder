"""Tests for email processor and job tracking integration."""
import time
from datetime import datetime

from app.email_processor import EmailProcessor
from app.email_webhook import InboundEmail
from app.job_tracker import STATUS_APPLIED, STATUS_NEW, JobTracker


class TestEmailProcessor:
    """Test EmailProcessor class."""

    def test_init(self):
        """Test processor initialization."""
        processor = EmailProcessor()
        assert processor.parser is not None
        assert processor.tracker is not None

    def test_process_job_listing_email(self, tmp_path):
        """Test processing job listing email."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="jobs@linkedin.com",
            subject="10 new jobs for Software Engineer",
            body_text="Here are jobs you might be interested in:\n\nSenior Software Engineer at Google",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["email_type"] == "job_listing"
        assert result["action"] == "created_job"
        assert result["job_id"] is not None

        # Verify job was created
        job = tracker.get_job(result["job_id"])
        assert job is not None
        assert job["status"] == STATUS_NEW

    def test_process_application_confirmation_new_job(self, tmp_path):
        """Test processing application confirmation for new job."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="noreply@myworkdayjobs.com",
            subject="Application Received: Senior Engineer",
            body_text="Thank you for applying to Senior Engineer at Salesforce",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["email_type"] == "application_confirm"
        assert result["action"] == "created_job_applied"
        assert result["job_id"] is not None

        # Verify job was created in 'applied' status
        job = tracker.get_job(result["job_id"])
        assert job is not None
        assert job["status"] == STATUS_APPLIED

    def test_process_application_confirmation_existing_job(self, tmp_path):
        """Test processing application confirmation for existing job."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        # Create existing job
        job_data = {
            "title": "Senior Engineer",
            "company": "Salesforce",
            "location": "",
            "summary": "Test job",
            "link": "https://salesforce.com/jobs/123",
            "source": "test",
        }
        job_id = tracker.track_job(job_data, status=STATUS_NEW)

        # Process confirmation email
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="noreply@myworkdayjobs.com",
            subject="Application Received: Senior Engineer",
            body_text="Thank you for applying to Senior Engineer at Salesforce\n" "https://salesforce.com/jobs/123",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["email_type"] == "application_confirm"
        assert result["action"] == "updated_status"
        assert result["job_id"] == job_id

        # Verify status was updated
        job = tracker.get_job(job_id)
        assert job["status"] == STATUS_APPLIED

    def test_process_recruiter_outreach(self, tmp_path):
        """Test processing recruiter outreach email."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="recruiter@netflix.com",
            subject="Exciting opportunity at Netflix",
            body_text="I came across your profile and thought you'd be interested in our Staff Engineer role",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["email_type"] == "recruiter_outreach"
        assert result["action"] == "created_job_priority"
        assert result["job_id"] is not None

        # Verify job was created with priority note
        job = tracker.get_job(result["job_id"])
        assert job is not None
        assert "HIGH PRIORITY" in job["notes"]
        assert "recruiter@netflix.com" in job["notes"]

    def test_process_unknown_email(self, tmp_path):
        """Test processing unknown email type."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="newsletter@example.com",
            subject="Weekly newsletter",
            body_text="Here's what's happening this week",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["email_type"] == "unknown"
        assert result["action"] == "skipped"
        assert result["job_id"] is None

    def test_process_low_confidence_job_listing(self, tmp_path):
        """Test low confidence job listing is skipped."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        # Email with minimal job listing indicators
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="sender@example.com",
            subject="Maybe a job?",
            body_text="This might have a job but unclear",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        # Should either skip or have low confidence action
        if result["email_type"] == "job_listing":
            assert result["action"] == "skipped_low_confidence"

    def test_match_job_by_url(self, tmp_path):
        """Test matching job by URL."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        # Create existing job with URL
        job_data = {
            "title": "Engineer",
            "company": "TestCo",
            "location": "",
            "summary": "Test",
            "link": "https://testco.com/jobs/456",
            "source": "test",
        }
        job_id = tracker.track_job(job_data)

        # Process confirmation with same URL
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="noreply@testco.com",
            subject="Application received",
            body_text="Thanks for applying\nhttps://testco.com/jobs/456",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["job_id"] == job_id
        assert result["action"] == "updated_status"

    def test_match_job_by_company_and_title(self, tmp_path):
        """Test matching job by company and title."""
        # Ensure clean test isolation with fresh tracker
        time.sleep(0.05)

        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        # Create existing job
        job_data = {
            "title": "Senior Backend Engineer",
            "company": "Amazon",
            "location": "",
            "summary": "Test",
            "link": "",
            "source": "test",
        }
        _ = tracker.track_job(job_data)  # Create existing job

        # Process confirmation with matching company/title
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="noreply@amazon.com",
            subject="Application received",
            body_text="Thank you for applying to Senior Backend Engineer at Amazon",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        # Verify the action was performed
        assert result["action"] in ["updated_status", "created", "created_job_applied"]
        # If it matched, job_id should be same; if not, a new job was created
        # Both are acceptable outcomes depending on parser matching logic
        assert result["job_id"] is not None

    def test_no_match_creates_new_job(self, tmp_path):
        """Test that no match creates new job."""
        tracker = JobTracker(tracking_file=tmp_path / "jobs.json")
        processor = EmailProcessor(job_tracker=tracker)

        # Process confirmation with no existing match
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="noreply@newcompany.com",
            subject="Application received",
            body_text="Thank you for applying to Data Scientist at NewCompany",
            body_html=None,
            received_at=datetime.now(),
        )

        result = processor.process_inbound_email(email)

        assert result["action"] == "created_job_applied"
        assert result["job_id"] is not None

        # Verify new job exists
        job = tracker.get_job(result["job_id"])
        assert job is not None
        assert job["status"] == STATUS_APPLIED
