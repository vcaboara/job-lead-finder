"""Tests for tracked jobs view UI."""

from unittest.mock import patch

import pytest

from app.job_tracker import STATUS_APPLIED, STATUS_INTERVIEWING


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
            job_id = job.get("job_id")
            if job_id:
                # Update status to track it
                client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})
                job_ids.append(job_id)

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    assert len(tracked["jobs"]) >= len(job_ids)


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
    job_id = job.get("job_id")

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


def test_filter_tracked_jobs_by_status(client, mock_search_response):
    """Test that tracked jobs can be filtered by status (client-side filtering test via API)."""
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
    job1_id = job1["job_id"]
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
    job2_id = job2["job_id"]
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


def test_tracked_jobs_empty_when_none_tracked(client):
    """Test that tracked jobs endpoint returns empty when no jobs are tracked."""
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    assert len(tracked["jobs"]) == 0
