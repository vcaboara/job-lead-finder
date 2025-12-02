"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to Python path so 'app' module can be imported
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import app.job_tracker as job_tracker_module
from app.ui_server import app


@pytest.fixture(autouse=True)
def clean_tracker():
    """Clean tracker state before and after each test."""
    tracking_file = Path("job_tracking.json")
    if tracking_file.exists():
        os.remove(tracking_file)
    job_tracker_module._tracker = None

    yield

    if tracking_file.exists():
        os.remove(tracking_file)
    job_tracker_module._tracker = None


@pytest.fixture
def client(clean_tracker):
    """Create test client after tracker cleanup."""
    return TestClient(app)


@pytest.fixture
def mock_search_response():
    """Mock search response to avoid real API calls."""

    def _mock_search(query="python developer", job_id="test123"):
        return {
            "leads": [
                {
                    "job_id": job_id,
                    "title": f"Senior {query}",
                    "company": "Tech Corp",
                    "location": "Remote",
                    "summary": f"Great opportunity for {query}",
                    "link": f"https://github.com/jobs/{job_id}",  # Use real domain to pass validation
                    "source": "TestSource",
                    "status": "new",
                    "notes": "",
                    "first_seen": "2025-12-01T00:00:00+00:00",
                    "last_updated": "2025-12-01T00:00:00+00:00",
                }
            ],
            "count": 1,
        }

    return _mock_search
