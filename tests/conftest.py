"""Pytest configuration and fixtures."""

import os
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to Python path so 'app' module can be imported
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Try to import PDF/DOCX libraries for testing
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document

    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

import app.job_tracker as job_tracker_module  # noqa: E402
from app.ui_server import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_tracker():
    """Clean tracker state before and after each test."""
    # Check both old and new locations to support tests
    tracking_files = [
        Path("job_tracking.json"),  # Old location (tests)
        Path("/app/data/job_tracking.json"),  # New production location
    ]

    for tracking_file in tracking_files:
        if tracking_file.exists():
            os.remove(tracking_file)
    job_tracker_module._tracker = None

    yield

    for tracking_file in tracking_files:
        if tracking_file.exists():
            os.remove(tracking_file)
    job_tracker_module._tracker = None


@pytest.fixture
def client(clean_tracker):  # noqa: ARG001
    """Create test client after tracker cleanup."""
    return TestClient(app)


@pytest.fixture
def mock_search_response():
    """Mock search response to avoid real API calls."""

    def _mock_search(query="python developer", job_id="test123"):
        now = datetime.now(timezone.utc).isoformat()
        return {
            "leads": [
                {
                    "job_id": job_id,
                    "title": f"Senior {query}",
                    "company": "Tech Corp",
                    "location": "Remote",
                    "summary": f"Great opportunity for {query}",
                    # Use real domain to pass validation
                    "link": f"https://github.com/jobs/{job_id}",
                    "source": "TestSource",
                    "status": "new",
                    "notes": "",
                    "first_seen": now,
                    "last_updated": now,
                }
            ],
            "count": 1,
        }

    return _mock_search


@pytest.fixture
def create_test_pdf():
    """Factory fixture to create test PDF files.

    Returns:
        Callable that takes text and returns PDF bytes
    """
    if not REPORTLAB_AVAILABLE:
        pytest.skip("reportlab not installed")

    def _create_pdf(text: str) -> bytes:
        """Create a PDF from text for testing.

        Args:
            text: Text content to put in PDF

        Returns:
            PDF bytes
        """
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Write text to PDF (simple line-by-line)
        y_position = 750
        for line in text.split("\n")[:50]:  # Max 50 lines to fit on page
            if y_position < 50:  # Don't go off page
                break
            can.drawString(50, y_position, line)
            y_position -= 15

        can.save()
        return packet.getvalue()

    return _create_pdf


@pytest.fixture
def create_test_docx():
    """Factory fixture to create test DOCX files.

    Returns:
        Callable that takes text and returns DOCX bytes
    """
    if not PYTHON_DOCX_AVAILABLE:
        pytest.skip("python-docx not installed")

    def _create_docx(text: str) -> bytes:
        """Create a DOCX from text for testing.

        Args:
            text: Text content to put in DOCX

        Returns:
            DOCX bytes
        """
        doc = Document()
        for para in text.split("\n"):
            if para.strip():
                doc.add_paragraph(para)

        packet = BytesIO()
        doc.save(packet)
        packet.seek(0)
        return packet.getvalue()

    return _create_docx


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    for file in [Path("resume.txt"), Path("leads.json")]:
        if file.exists():
            try:
                file.unlink()
            except FileNotFoundError:
                pass  # File already deleted or never created


@pytest.fixture
def mock_resume_file(monkeypatch):
    """Create a mock RESUME_FILE for testing.

    Returns:
        MagicMock: Mock Path object that can be configured per test
    """
    from unittest.mock import MagicMock

    mock_file = MagicMock()
    monkeypatch.setattr("app.ui_server.RESUME_FILE", mock_file)
    return mock_file


@pytest.fixture
def mock_config_manager(monkeypatch):
    """Mock config.json file I/O to prevent disk access and parallel test conflicts.

    Uses in-memory storage to avoid race conditions in parallel test execution.
    This fixture replaces duplicated config mocking code across multiple test files.

    Returns:
        dict: In-memory config data storage for test manipulation
    """

    # Mock config data storage (in-memory)
    config_data = {"config": {}}  # Initialize with empty config

    def mock_load_config():
        """Mock load_config() to return in-memory config."""
        from app.config_manager import DEFAULT_CONFIG

        if "config" in config_data and config_data["config"]:
            # Deep merge with defaults (same logic as real load_config)
            merged = DEFAULT_CONFIG.copy()
            for key, value in config_data["config"].items():
                if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value
            return merged
        return DEFAULT_CONFIG.copy()

    def mock_save_config(config):
        """Mock save_config() to store in memory."""
        config_data["config"] = config
        return True

    # Patch the config functions directly
    monkeypatch.setattr("app.config_manager.load_config", mock_load_config)
    monkeypatch.setattr("app.config_manager.save_config", mock_save_config)
    # Also patch in ui_server since it imports load_config
    monkeypatch.setattr("app.ui_server.load_config", mock_load_config)

    yield config_data

    # Cleanup in-memory config
    config_data.clear()
