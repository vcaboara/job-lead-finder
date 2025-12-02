"""Tests for tracked jobs view UI."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.job_tracker as jt
from app.job_tracker import STATUS_APPLIED, STATUS_INTERVIEWING
from app.ui_server import app


@pytest.fixture(autouse=True)
def clean_tracker():
    """Clean tracker state before and after each test."""
    tracking_file = Path("job_tracking.json")
    if tracking_file.exists():
        os.remove(tracking_file)
    jt._tracker = None

    yield

    if tracking_file.exists():
        os.remove(tracking_file)
    jt._tracker = None


@pytest.fixture
def client(clean_tracker):
    """Create test client after tracker cleanup."""
    return TestClient(app)


def test_tracked_jobs_endpoint_returns_all_jobs(client):
    """Test that tracked jobs endpoint returns all tracked jobs."""
    # Track multiple jobs
    job_ids = []
    for i in range(3):
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


def test_tracked_jobs_includes_metadata(client):
    """Test that tracked jobs include all necessary metadata."""
    # Create and track a job
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


def test_filter_tracked_jobs_by_status(client):
    """Test that tracked jobs can be filtered by status (client-side filtering test via API)."""
    # Track multiple jobs with different statuses
    tracked_job_ids = []

    # First job - set to APPLIED
    response = client.post(
        "/api/search",
        json={"query": "python developer remote", "count": 1, "evaluate": False, "min_score": 0},
    )
    assert response.status_code == 200
    job1 = response.json()["leads"][0]
    job1_id = job1["job_id"]
    status_resp = client.post(f"/api/jobs/{job1_id}/status", json={"status": STATUS_APPLIED})
    assert status_resp.status_code == 200, f"Failed to update status for job1: {status_resp.json()}"
    tracked_job_ids.append((job1_id, STATUS_APPLIED))

    # Second job - set to INTERVIEWING
    response = client.post(
        "/api/search",
        json={"query": "senior data engineer", "count": 1, "evaluate": False, "min_score": 0},
    )
    assert response.status_code == 200
    job2 = response.json()["leads"][0]
    job2_id = job2["job_id"]

    # If we got the same job, update status to interviewing (will override previous status)
    if job2_id == job1_id:
        # Same job, just verify we have one job with interviewing status
        status_resp = client.post(f"/api/jobs/{job2_id}/status", json={"status": STATUS_INTERVIEWING})
        assert status_resp.status_code == 200

        # Get all tracked jobs
        response = client.get("/api/jobs/tracked")
        assert response.status_code == 200
        tracked = response.json()

        # Should have exactly one job with interviewing status
        assert len(tracked["jobs"]) == 1
        assert tracked["jobs"][0]["status"] == STATUS_INTERVIEWING
    else:
        # Different jobs, proceed with normal test
        status_resp = client.post(f"/api/jobs/{job2_id}/status", json={"status": STATUS_INTERVIEWING})
        assert status_resp.status_code == 200, f"Failed to update status for job2: {status_resp.json()}"
        tracked_job_ids.append((job2_id, STATUS_INTERVIEWING))

        # Get all tracked jobs
        response = client.get("/api/jobs/tracked")
        assert response.status_code == 200
        tracked = response.json()

        # Verify we can filter by status (simulating client-side filtering)
        applied_jobs = [j for j in tracked["jobs"] if j.get("status") == STATUS_APPLIED]
        interviewing_jobs = [j for j in tracked["jobs"] if j.get("status") == STATUS_INTERVIEWING]

        # Should have at least one job in each category
        assert len(applied_jobs) >= 1, f"Expected at least 1 applied job, got {len(applied_jobs)}"
        assert len(interviewing_jobs) >= 1, f"Expected at least 1 interviewing job, got {len(interviewing_jobs)}"

        # Verify the specific jobs we tracked
        applied_ids = {j["job_id"] for j in applied_jobs}
        interviewing_ids = {j["job_id"] for j in interviewing_jobs}
        assert job1_id in applied_ids, f"Job {job1_id} should be in applied status"
        assert job2_id in interviewing_ids, f"Job {job2_id} should be in interviewing status"


def test_tracked_jobs_empty_when_none_tracked(client):
    """Test that tracked jobs endpoint returns empty when no jobs are tracked."""
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    assert len(tracked["jobs"]) == 0
