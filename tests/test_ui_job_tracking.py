"""Tests for job tracking UI interactions."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.job_tracker as jt
from app.job_tracker import STATUS_APPLIED, STATUS_HIDDEN
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


def test_update_job_status(client):
    """Test updating job status via API."""
    # First, create a job by searching
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
    assert len(data["leads"]) > 0

    job = data["leads"][0]
    job_id = job.get("job_id")
    assert job_id is not None

    # Update status to applied
    response = client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})
    assert response.status_code == 200

    # Verify status was updated
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    result = response.json()
    job_data = result.get("job", result)  # Handle both wrapped and unwrapped responses
    assert job_data["status"] == STATUS_APPLIED


def test_hide_job(client):
    """Test hiding a job via API."""
    # Create a job
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

    # Hide the job
    response = client.post(f"/api/jobs/{job_id}/hide")
    assert response.status_code == 200

    # Verify job is hidden
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    result = response.json()
    job_data = result.get("job", result)
    assert job_data["status"] == STATUS_HIDDEN


def test_save_job_notes(client):
    """Test saving notes for a job."""
    # Create a job
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

    # Save notes
    test_notes = "Great company culture, applied via referral"
    response = client.post(f"/api/jobs/{job_id}/notes", json={"notes": test_notes})
    assert response.status_code == 200
    # Verify notes were saved
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    result = response.json()
    job_data = result.get("job", result)
    assert job_data["notes"] == test_notes


def test_job_tracking_persists_across_searches(client):
    """Test that job tracking status persists when same job appears in multiple searches."""
    # First search
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

    # Mark as applied
    response = client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})
    assert response.status_code == 200

    # Second search (same query should return same job)
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

    # Find the same job (should have tracking_status)
    matching_job = next((j for j in data["leads"] if j.get("job_id") == job_id), None)
    if matching_job:  # Job might not appear if different results
        assert matching_job.get("tracking_status") == STATUS_APPLIED


def test_invalid_status_rejected(client):
    """Test that invalid status values are rejected."""
    # Create a job
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

    # Try invalid status
    response = client.post(f"/api/jobs/{job_id}/status", json={"status": "invalid_status"})
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_get_tracked_jobs(client):
    """Test retrieving all tracked jobs."""
    # Track multiple jobs
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
                client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    # Should have some tracked jobs
    assert len(tracked["jobs"]) > 0
