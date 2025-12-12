"""Tests for tracked jobs view UI."""

from unittest.mock import patch

import pytest

from app.job_tracker import STATUS_APPLIED, STATUS_INTERVIEWING

# Mark all tests in this module as slow - they make real API calls to Ollama
pytestmark = pytest.mark.slow


def _track_job_helper(client, job):
    """Helper to track a job from search results."""
    track_response = client.post(
        "/api/jobs/track",
        json={
            "title": job.get("title", "Test Job"),
            "company": job.get("company", "Test Company"),
            "location": job.get("location", "Remote"),
            "summary": job.get("summary", "Test summary"),
            "link": job.get("link", "https://example.com/job"),
            "source": job.get("source", ""),
        },
    )
    assert track_response.status_code == 200
    return track_response.json()


@pytest.mark.slow  # Makes real API calls to Ollama
@pytest.mark.xdist_group(name="tracker")
def test_tracked_jobs_endpoint_returns_all_jobs(client, mock_search_response):
    """Test that tracked jobs endpoint returns all tracked jobs."""
    # Track multiple jobs
    job_ids = []
    for i in range(3):
        with patch("app.ui_server._process_and_filter_leads") as mock_filter:
            mock_filter.return_value = mock_search_response(query=f"developer {i}", job_id=f"track{i}")["leads"]
            response = client.post(
                "/api/search",
                json={
                    "query": f"python developer {i}",
                    "count": 1,
                    "evaluate": False,
                    "min_score": 0,
                },
            )
        assert response.status_code == 200
        data = response.json()
        if data["leads"]:
            job = data["leads"][0]
            # Track the job
            track_result = _track_job_helper(client, job)
            job_id = track_result["job_id"]
            # Update status to applied
            client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})
            job_ids.append(job_id)

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    assert len(tracked["jobs"]) >= len(job_ids)


@pytest.mark.slow  # Makes real API calls to Ollama
@pytest.mark.xdist_group(name="tracker")
def test_tracked_jobs_includes_metadata(client, mock_search_response):
    """Test that tracked jobs include all necessary metadata."""
    # Create and track a job
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(query="python developer", job_id="meta123")["leads"]
        response = client.post(
            "/api/search",
            json={
                "query": "python developer",
                "count": 1,
                "evaluate": False,
                "min_score": 0,
            },
        )
    assert response.status_code == 200
    data = response.json()
    job = data["leads"][0]

    # Track the job first
    track_result = _track_job_helper(client, job)
    job_id = track_result["job_id"]

    # Update status and add notes
    client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_INTERVIEWING, "notes": "Phone screen scheduled"})

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()

    # Find our job
    tracked_job = next((j for j in tracked["jobs"] if j.get("job_id") == job_id), None)
    assert tracked_job is not None
    assert tracked_job["status"] == STATUS_INTERVIEWING
    assert "Phone screen scheduled" in tracked_job.get("notes", "")
    assert "title" in tracked_job
    assert "company" in tracked_job
    assert "link" in tracked_job
    assert "first_seen" in tracked_job
    assert "last_updated" in tracked_job


@pytest.mark.xdist_group(name="tracker")
def test_filter_tracked_jobs_by_status(client, mock_search_response):
    """Test that tracked jobs can be filtered by status (client-side filtering test via API)."""
    # Explicitly clear any existing tracked jobs to ensure clean state
    import os
    import time

    import app.job_tracker as job_tracker_module

    # Small delay to ensure other tests have finished writing
    time.sleep(0.1)

    # Force re-initialization of tracker to ensure clean state
    job_tracker_module._tracker = None  # noqa: SLF001

    # Get the actual tracking file path from the module
    tracking_file = job_tracker_module.TRACKING_FILE
    if tracking_file.exists():
        os.remove(tracking_file)

    # Re-initialize the tracker and clear all jobs
    job_tracker_module._tracker = None  # noqa: SLF001
    from app.job_tracker import get_tracker

    tracker = get_tracker()
    tracker.clear_all_jobs()  # Explicitly clear all jobs

    # Track two jobs with different statuses using mocked responses

    # First job - set to APPLIED
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(query="python developer", job_id="job1_applied")["leads"]
        response = client.post(
            "/api/search",
            json={"query": "python developer remote", "count": 1, "evaluate": False, "min_score": 0},
        )
    assert response.status_code == 200
    job1 = response.json()["leads"][0]

    # Track first job
    track_result1 = _track_job_helper(client, job1)
    job1_id = track_result1["job_id"]
    status_resp = client.post(f"/api/jobs/{job1_id}/status", json={"status": STATUS_APPLIED})
    assert status_resp.status_code == 200

    # Second job - set to INTERVIEWING
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(query="data engineer", job_id="job2_interviewing")["leads"]
        response = client.post(
            "/api/search",
            json={"query": "senior data engineer", "count": 1, "evaluate": False, "min_score": 0},
        )
    assert response.status_code == 200
    job2 = response.json()["leads"][0]

    # Track second job
    track_result2 = _track_job_helper(client, job2)
    job2_id = track_result2["job_id"]
    status_resp = client.post(f"/api/jobs/{job2_id}/status", json={"status": STATUS_INTERVIEWING})
    assert status_resp.status_code == 200

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()

    # Verify we can filter by status (simulating client-side filtering)
    applied_jobs = [j for j in tracked["jobs"] if j.get("status") == STATUS_APPLIED]
    interviewing_jobs = [j for j in tracked["jobs"] if j.get("status") == STATUS_INTERVIEWING]

    # Should have exactly one job in each category
    assert len(applied_jobs) == 1, f"Expected 1 applied job, got {len(applied_jobs)}"
    assert len(interviewing_jobs) == 1, f"Expected 1 interviewing job, got {len(interviewing_jobs)}"

    # Verify the specific jobs we tracked
    assert applied_jobs[0]["job_id"] == job1_id
    assert interviewing_jobs[0]["job_id"] == job2_id


@pytest.mark.xdist_group(name="tracker")
def test_tracked_jobs_empty_when_none_tracked(client):
    """Test that tracked jobs endpoint returns empty when no jobs are tracked."""
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    assert len(tracked["jobs"]) == 0


@pytest.mark.xdist_group(name="tracker")
def test_track_job_endpoint_creates_new_tracked_job(client):
    """Test that the /api/jobs/track endpoint creates a new tracked job."""
    job_data = {
        "title": "Senior Python Developer",
        "company": "Test Company Inc",
        "location": "Remote",
        "summary": "We are looking for a senior Python developer...",
        "link": "https://example.com/job/12345",
        "source": "TestBoard",
    }

    # Track the job
    response = client.post("/api/jobs/track", json=job_data)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "message" in data
    assert "job" in data
    assert "job_id" in data

    # Verify the tracked job has the correct data
    job = data["job"]
    assert job["title"] == job_data["title"]
    assert job["company"] == job_data["company"]
    assert job["location"] == job_data["location"]
    assert job["summary"] == job_data["summary"]
    assert job["link"] == job_data["link"]
    assert job["source"] == job_data["source"]
    assert job["status"] == "new"

    # Verify the job appears in tracked jobs
    tracked_response = client.get("/api/jobs/tracked")
    assert tracked_response.status_code == 200
    tracked = tracked_response.json()
    assert len(tracked["jobs"]) == 1
    assert tracked["jobs"][0]["job_id"] == data["job_id"]
