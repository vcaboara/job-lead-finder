"""Tests for job tracking UI interactions."""

from unittest.mock import patch

from app.job_tracker import STATUS_APPLIED, STATUS_HIDDEN


def test_update_job_status(client, mock_search_response):
    """Test updating job status via API."""
    # First, create a job by searching
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response()["leads"]
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


def test_hide_job(client, mock_search_response):
    """Test hiding a job via API."""
    # Create a job
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(job_id="hide123")["leads"]
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


def test_save_job_notes(client, mock_search_response):
    """Test saving notes for a job."""
    # Create a job
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(job_id="notes123")["leads"]
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


def test_save_job_notes_exceeds_max_length(client, mock_search_response):
    """Test that notes exceeding max length are rejected."""
    # Create a job - mock both job fetching and filtering to avoid slow API calls
    with patch("app.ui_server.generate_job_leads") as mock_gen, patch(
        "app.ui_server._process_and_filter_leads"
    ) as mock_filter:
        mock_data = mock_search_response(job_id="notes_limit")
        mock_gen.return_value = mock_data["leads"]
        mock_filter.return_value = mock_data["leads"]  # Return leads as-is
        response = client.post(
            "/api/search",
            json={
                "query": "test",
                "count": 1,
                "evaluate": False,
                "min_score": 0,
            },
        )
    assert response.status_code == 200
    data = response.json()
    job = data["leads"][0]
    job_id = job.get("job_id")

    # Try to save notes that exceed 10000 characters
    too_long_notes = "x" * 10001
    response = client.post(f"/api/jobs/{job_id}/notes", json={"notes": too_long_notes})
    assert response.status_code == 422  # Validation error


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


def test_invalid_status_rejected(client, mock_search_response):
    """Test that invalid status values are rejected."""
    # Create a job
    with patch("app.ui_server._process_and_filter_leads") as mock_filter:
        mock_filter.return_value = mock_search_response(job_id="invalid123")["leads"]
        response = client.post(
            "/api/search",
            json={
                "query": "software engineer",
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


def test_get_tracked_jobs(client, mock_search_response):
    """Test retrieving all tracked jobs."""
    # Track multiple jobs
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
                client.post(f"/api/jobs/{job_id}/status", json={"status": STATUS_APPLIED})

    # Get all tracked jobs
    response = client.get("/api/jobs/tracked")
    assert response.status_code == 200
    tracked = response.json()
    assert "jobs" in tracked
    # Should have some tracked jobs
    assert len(tracked["jobs"]) > 0
