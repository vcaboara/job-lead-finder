"""Tests for job tracking and status management."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.job_tracker import STATUS_APPLIED, STATUS_HIDDEN, STATUS_INTERVIEWING, STATUS_NEW, JobTracker, generate_job_id
from app.ui_server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_tracker(tmp_path):
    """Create a temporary job tracker with isolated storage."""
    tracking_file = tmp_path / "test_tracking.json"
    tracker = JobTracker(tracking_file=tracking_file)
    yield tracker
    # Cleanup
    if tracking_file.exists():
        tracking_file.unlink()


@pytest.fixture
def sample_job():
    """Sample job data for testing."""
    return {
        "title": "Senior Python Engineer",
        "company": "Acme Corp",
        "location": "Remote",
        "summary": "We are looking for a Python developer...",
        "link": "https://acme.com/careers/12345",
        "source": "RemoteOK",
    }


class TestJobIDGeneration:
    """Tests for job ID generation."""

    def test_generate_id_from_link(self):
        """Test that job ID is generated from link."""
        job = {"link": "https://example.com/job/123", "title": "Engineer", "company": "Test"}
        job_id = generate_job_id(job)
        assert len(job_id) == 16  # SHA256 hash truncated to 16 chars
        assert job_id.isalnum()

    def test_generate_id_consistent(self):
        """Test that same job produces same ID."""
        job = {"link": "https://example.com/job/123", "title": "Engineer", "company": "Test"}
        id1 = generate_job_id(job)
        id2 = generate_job_id(job)
        assert id1 == id2

    def test_generate_id_fallback_to_title_company(self):
        """Test that ID is generated from title+company when no link."""
        job = {"title": "Engineer", "company": "Test Corp"}
        job_id = generate_job_id(job)
        assert len(job_id) == 16
        # Same title+company should produce same ID
        job2 = {"title": "Engineer", "company": "Test Corp"}
        assert generate_job_id(job2) == job_id

    def test_different_jobs_different_ids(self):
        """Test that different jobs produce different IDs."""
        job1 = {"link": "https://example.com/job/123"}
        job2 = {"link": "https://example.com/job/456"}
        assert generate_job_id(job1) != generate_job_id(job2)


class TestJobTracker:
    """Tests for JobTracker class."""

    def test_track_new_job(self, temp_tracker, sample_job):
        """Test tracking a new job."""
        job_id = temp_tracker.track_job(sample_job)
        assert job_id is not None
        job = temp_tracker.get_job(job_id)
        assert job is not None
        assert job["title"] == sample_job["title"]
        assert job["company"] == sample_job["company"]
        assert job["status"] == STATUS_NEW

    def test_track_job_preserves_existing_data(self, temp_tracker, sample_job):
        """Test that re-tracking a job preserves user data."""
        # Track job and add notes
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.update_status(job_id, STATUS_APPLIED, notes="Applied via LinkedIn")

        # Track same job again (e.g., from new search)
        temp_tracker.track_job(sample_job)

        # Check that status and notes are preserved
        job = temp_tracker.get_job(job_id)
        assert job["status"] == STATUS_APPLIED
        assert job["notes"] == "Applied via LinkedIn"

    def test_update_status(self, temp_tracker, sample_job):
        """Test updating job status."""
        job_id = temp_tracker.track_job(sample_job)
        success = temp_tracker.update_status(job_id, STATUS_APPLIED)
        assert success is True
        job = temp_tracker.get_job(job_id)
        assert job["status"] == STATUS_APPLIED

    def test_update_status_sets_applied_date(self, temp_tracker, sample_job):
        """Test that updating to 'applied' sets applied_date."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.update_status(job_id, STATUS_APPLIED)
        job = temp_tracker.get_job(job_id)
        assert job["applied_date"] is not None

    def test_update_status_with_notes(self, temp_tracker, sample_job):
        """Test updating status with notes."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.update_status(job_id, STATUS_INTERVIEWING, notes="Phone screen scheduled")
        job = temp_tracker.get_job(job_id)
        assert job["status"] == STATUS_INTERVIEWING
        assert job["notes"] == "Phone screen scheduled"

    def test_update_invalid_status(self, temp_tracker, sample_job):
        """Test that invalid status is rejected."""
        job_id = temp_tracker.track_job(sample_job)
        success = temp_tracker.update_status(job_id, "invalid_status")
        assert success is False

    def test_update_nonexistent_job(self, temp_tracker):
        """Test updating a job that doesn't exist."""
        success = temp_tracker.update_status("fake_id", STATUS_APPLIED)
        assert success is False

    def test_hide_job(self, temp_tracker, sample_job):
        """Test hiding a job."""
        job_id = temp_tracker.track_job(sample_job)
        success = temp_tracker.hide_job(job_id)
        assert success is True
        job = temp_tracker.get_job(job_id)
        assert job["status"] == STATUS_HIDDEN

    def test_set_company_link(self, temp_tracker, sample_job):
        """Test setting company link."""
        job_id = temp_tracker.track_job(sample_job)
        company_link = "https://acme.com/careers/direct/12345"
        success = temp_tracker.set_company_link(job_id, company_link)
        assert success is True
        job = temp_tracker.get_job(job_id)
        assert job["company_link"] == company_link

    def test_get_all_jobs(self, temp_tracker, sample_job):
        """Test getting all jobs."""
        temp_tracker.track_job(sample_job)
        job2 = sample_job.copy()
        job2["link"] = "https://acme.com/careers/67890"
        temp_tracker.track_job(job2)

        jobs = temp_tracker.get_all_jobs()
        assert len(jobs) == 2

    def test_get_all_jobs_filters_hidden_by_default(self, temp_tracker, sample_job):
        """Test that hidden jobs are excluded by default."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.hide_job(job_id)

        job2 = sample_job.copy()
        job2["link"] = "https://acme.com/careers/67890"
        temp_tracker.track_job(job2)

        jobs = temp_tracker.get_all_jobs()
        assert len(jobs) == 1  # Only non-hidden job

    def test_get_all_jobs_include_hidden(self, temp_tracker, sample_job):
        """Test getting all jobs including hidden."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.hide_job(job_id)

        jobs = temp_tracker.get_all_jobs(include_hidden=True)
        assert len(jobs) == 1
        assert jobs[0]["status"] == STATUS_HIDDEN

    def test_get_all_jobs_status_filter(self, temp_tracker, sample_job):
        """Test filtering jobs by status."""
        job_id1 = temp_tracker.track_job(sample_job)
        temp_tracker.update_status(job_id1, STATUS_APPLIED)

        job2 = sample_job.copy()
        job2["link"] = "https://acme.com/careers/67890"
        job_id2 = temp_tracker.track_job(job2)
        temp_tracker.update_status(job_id2, STATUS_INTERVIEWING)

        applied_jobs = temp_tracker.get_all_jobs(status_filter=[STATUS_APPLIED])
        assert len(applied_jobs) == 1
        assert applied_jobs[0]["status"] == STATUS_APPLIED

    def test_get_hidden_job_ids(self, temp_tracker, sample_job):
        """Test getting hidden job IDs."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.hide_job(job_id)

        hidden_ids = temp_tracker.get_hidden_job_ids()
        assert job_id in hidden_ids

    def test_is_job_hidden(self, temp_tracker, sample_job):
        """Test checking if job is hidden."""
        job_id = temp_tracker.track_job(sample_job)
        temp_tracker.hide_job(job_id)

        assert temp_tracker.is_job_hidden(sample_job) is True

        # Different job should not be hidden
        other_job = sample_job.copy()
        other_job["link"] = "https://other.com/job/123"
        assert temp_tracker.is_job_hidden(other_job) is False

    def test_persistence(self, temp_tracker, sample_job):
        """Test that data is persisted to file."""
        job_id = temp_tracker.track_job(sample_job)

        # Create new tracker instance with same file
        new_tracker = JobTracker(tracking_file=temp_tracker.tracking_file)
        job = new_tracker.get_job(job_id)
        assert job is not None
        assert job["title"] == sample_job["title"]

    def test_clear_all_jobs(self, temp_tracker, sample_job):
        """Test clearing all tracked jobs."""
        # Track some jobs
        job_id1 = temp_tracker.track_job(sample_job)
        job_id2 = temp_tracker.track_job({**sample_job, "link": "https://example.com/job2"})

        # Verify jobs exist
        assert len(temp_tracker.get_all_jobs()) == 2

        # Clear all jobs
        temp_tracker.clear_all_jobs()

        # Verify all jobs are cleared
        assert len(temp_tracker.get_all_jobs()) == 0
        assert temp_tracker.get_job(job_id1) is None
        assert temp_tracker.get_job(job_id2) is None


class TestJobTrackingAPIEndpoints:
    """Tests for job tracking API endpoints."""

    def test_get_tracked_jobs_empty(self, client):
        """Test getting tracked jobs when none exist."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_all_jobs.return_value = []
            response = client.get("/api/jobs/tracked")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["jobs"] == []

    def test_get_tracked_jobs(self, client):
        """Test getting tracked jobs."""
        sample_jobs = [
            {
                "job_id": "abc123",
                "title": "Engineer",
                "company": "Acme",
                "status": "applied",
            }
        ]
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_all_jobs.return_value = sample_jobs
            response = client.get("/api/jobs/tracked")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert len(data["jobs"]) == 1

    def test_get_tracked_jobs_with_status_filter(self, client):
        """Test getting tracked jobs filtered by status."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_all_jobs.return_value = []
            response = client.get("/api/jobs/tracked?status=applied,interviewing")
            assert response.status_code == 200
            # Verify status_filter was passed correctly
            mock_tracker.return_value.get_all_jobs.assert_called_once()
            call_args = mock_tracker.return_value.get_all_jobs.call_args
            assert call_args[1]["status_filter"] == ["applied", "interviewing"]

    def test_get_job_details(self, client):
        """Test getting details for a specific job."""
        sample_job = {
            "job_id": "abc123",
            "title": "Engineer",
            "company": "Acme",
            "status": "new",
        }
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = sample_job
            response = client.get("/api/jobs/abc123")
            assert response.status_code == 200
            data = response.json()
            assert data["job"]["job_id"] == "abc123"

    def test_get_job_details_not_found(self, client):
        """Test getting details for non-existent job."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = None
            response = client.get("/api/jobs/fake_id")
            assert response.status_code == 404

    def test_update_job_status(self, client):
        """Test updating job status."""
        sample_job = {"job_id": "abc123", "status": "applied"}
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.update_status.return_value = True
            mock_tracker.return_value.get_job.return_value = sample_job
            response = client.post("/api/jobs/abc123/status", json={"status": "applied", "notes": "Applied today"})
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_update_job_status_invalid(self, client):
        """Test updating job with invalid status."""
        with patch("app.ui_server.get_tracker"):
            response = client.post("/api/jobs/abc123/status", json={"status": "invalid_status"})
            assert response.status_code == 400

    def test_hide_job(self, client):
        """Test hiding a job."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.hide_job.return_value = True
            response = client.post("/api/jobs/abc123/hide")
            assert response.status_code == 200

    def test_hide_job_not_found(self, client):
        """Test hiding non-existent job."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.hide_job.return_value = False
            response = client.post("/api/jobs/fake_id/hide")
            assert response.status_code == 404

    def test_set_company_link(self, client):
        """Test setting company link."""
        sample_job = {"job_id": "abc123", "company_link": "https://company.com/job/123"}
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.set_company_link.return_value = True
            mock_tracker.return_value.get_job.return_value = sample_job
            response = client.post(
                "/api/jobs/abc123/company-link", json={"company_link": "https://company.com/job/123"}
            )
            assert response.status_code == 200

    def test_set_company_link_invalid_url(self, client):
        """Test setting invalid company link."""
        with patch("app.ui_server.get_tracker"):
            response = client.post("/api/jobs/abc123/company-link", json={"company_link": "not-a-url"})
            assert response.status_code == 400

    def test_generate_cover_letter(self, client):
        """Test generating cover letter."""
        sample_job = {"job_id": "abc123", "title": "Engineer", "company": "Acme", "summary": "We need an engineer..."}
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = sample_job
            with patch("app.ui_server.RESUME_FILE") as mock_resume:
                mock_resume.exists.return_value = True
                mock_resume.read_text.return_value = "My resume text..."
                with patch("app.gemini_provider.simple_gemini_query") as mock_query:
                    mock_query.return_value = "Dear Hiring Manager..."
                    response = client.post(
                        "/api/jobs/abc123/cover-letter", json={"job_description": "Full job description..."}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "cover_letter" in data

    def test_generate_cover_letter_no_resume(self, client):
        """Test generating cover letter without resume."""
        sample_job = {"job_id": "abc123"}
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = sample_job
            with patch("app.ui_server.RESUME_FILE") as mock_resume:
                mock_resume.exists.return_value = False
                response = client.post(
                    "/api/jobs/abc123/cover-letter", json={"job_description": "Full job description..."}
                )
                assert response.status_code == 400

    def test_find_company_link(self, client):
        """Test finding company link for aggregator job."""
        sample_job = {
            "job_id": "abc123",
            "title": "Engineer",
            "company": "Acme Corp",
            "link": "https://remoteok.com/job/123",
            "location": "Remote",
        }
        company_jobs = [
            {
                "title": "Engineer",
                "company": "Acme Corp",
                "link": "https://acme.com/careers/456",
                "source": "CompanyJobs",
            }
        ]
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = sample_job
            with patch("app.mcp_providers.generate_job_leads_via_mcp") as mock_search:
                mock_search.return_value = company_jobs
                response = client.post("/api/jobs/find-company-link/abc123")
                assert response.status_code == 200
                data = response.json()
                assert data["found"] is True
                assert "company_link" in data

    def test_find_company_link_not_found(self, client):
        """Test finding company link when none exist."""
        sample_job = {"job_id": "abc123", "company": "Acme Corp", "title": "Engineer"}
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_tracker.return_value.get_job.return_value = sample_job
            with patch("app.mcp_providers.generate_job_leads_via_mcp") as mock_search:
                mock_search.return_value = []  # No results
                response = client.post("/api/jobs/find-company-link/abc123")
                assert response.status_code == 200
                data = response.json()
                assert data["found"] is False

    def test_clear_all_tracked_jobs(self, client):
        """Test clearing all tracked jobs via API."""
        with patch("app.ui_server.get_tracker") as mock_tracker:
            mock_instance = mock_tracker.return_value
            response = client.delete("/api/jobs/tracked/clear")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "All tracked jobs cleared"
            assert data["count"] == 0
            mock_instance.clear_all_jobs.assert_called_once()


class TestJobTrackingIntegration:
    """Integration tests for job tracking in search flow."""

    def test_search_automatically_tracks_jobs(self, client):
        """Test that search results automatically track jobs."""
        # This would require mocking the entire search flow
        # For now, this is a placeholder for integration tests
        pass

    def test_search_filters_hidden_jobs(self, client):
        """Test that search excludes hidden jobs."""
        # Integration test placeholder
        pass
