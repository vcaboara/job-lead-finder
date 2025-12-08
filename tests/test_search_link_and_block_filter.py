"""Tests for /api/search link validation and block list filtering.

We monkeypatch generate_job_leads and validate_link to simulate various
scenarios without external network calls.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ui_server import app

CONFIG_FILE = Path("config.json")


# In-memory config storage for tests
_test_config_data = {}


def _write_config(data: dict):  # noqa: ANN001
    """Write config to in-memory storage instead of disk."""
    _test_config_data["config"] = data


@pytest.fixture(autouse=True)
def mock_config_file_io(monkeypatch):
    """Mock config.json file I/O to use in-memory storage."""
    global _test_config_data
    _test_config_data.clear()

    # Initialize with empty config
    _test_config_data["config"] = {}

    def mock_exists(self):
        return "config" in _test_config_data and _test_config_data["config"] is not None

    # Mock open() to intercept config.json reads/writes
    original_open = open

    def mock_open_func(file, mode="r", *args, **kwargs):
        # Convert Path to string for comparison
        file_str = str(file)
        if "config.json" in file_str:
            if "r" in mode:
                # Return in-memory config
                from io import StringIO

                config_str = json.dumps(_test_config_data.get("config", {}))
                return StringIO(config_str)
            elif "w" in mode:
                # Capture writes to in-memory storage
                from io import StringIO

                buffer = StringIO()
                original_write = buffer.write

                def capture_write(content):
                    result = original_write(content)
                    # Store in memory
                    try:
                        _test_config_data["config"] = json.loads(buffer.getvalue())
                    except (json.JSONDecodeError, KeyError):
                        pass
                    return result

                buffer.write = capture_write
                return buffer
        return original_open(file, mode, *args, **kwargs)

    # Patch Path.exists and open()
    monkeypatch.setattr(Path, "exists", mock_exists)
    monkeypatch.setattr("builtins.open", mock_open_func)

    yield

    _test_config_data.clear()


def setup_function():  # noqa: D401
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def teardown_function():  # noqa: D401
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def test_search_marks_invalid_links(monkeypatch):
    client = TestClient(app)

    def fake_generate(*args, **kwargs):  # noqa: ANN001
        return [
            {
                "title": "Valid Job",
                "company": "GoodCo",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://good.example/jobs/engineer-12345",
            },
            {
                "title": "Bad Link Job",
                "company": "BadCo",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://bad.example/jobs/dev-67890",
            },
        ]

    def fake_validate(url: str, timeout: int = 5, verbose: bool = False):  # noqa: ANN001
        if "good.example" in url:
            return {"url": url, "valid": True, "status_code": 200, "final_url": url, "error": None}
        return {"url": url, "valid": False, "status_code": 404, "final_url": url, "error": "not found"}

    monkeypatch.setattr("app.ui_server.generate_job_leads", fake_generate)
    monkeypatch.setattr("app.ui_server.validate_link", fake_validate)

    resp = client.post(
        "/api/search",
        json={"query": "engineer", "resume": None, "count": 5, "evaluate": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Now only the valid link should appear since the invalid one is filtered out
    assert data["count"] == 1
    assert len(data["leads"]) == 1
    # Find good lead
    good = data["leads"][0]
    assert good["company"] == "GoodCo"
    assert good["link_valid"] is True


def test_search_filters_blocked_site(monkeypatch):
    client = TestClient(app)
    _write_config(
        {"system_instructions": "", "blocked_entities": [{"type": "site", "value": "blocked.com"}], "region": ""}
    )

    def fake_generate(*args, **kwargs):  # noqa: ANN001
        return [
            {
                "title": "Site Blocked",
                "company": "SiteCo",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://blocked.com/jobs/position-456",
            },
            {
                "title": "Site Allowed",
                "company": "OtherCo",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://allowed.com/jobs/position-123",
            },
        ]

    def fake_validate(url: str, timeout: int = 5, verbose: bool = False):  # noqa: ANN001
        return {"url": url, "valid": True, "status_code": 200, "error": None}

    monkeypatch.setattr("app.ui_server.generate_job_leads", fake_generate)
    monkeypatch.setattr("app.ui_server.validate_link", fake_validate)

    resp = client.post(
        "/api/search",
        json={"query": "engineer", "resume": None, "count": 5, "evaluate": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    titles = {lead["title"] for lead in data["leads"]}
    assert "Site Blocked" not in titles
    assert "Site Allowed" in titles


def test_search_filters_blocked_employer(monkeypatch):
    client = TestClient(app)
    _write_config(
        {"system_instructions": "", "blocked_entities": [{"type": "employer", "value": "BadCorp"}], "region": ""}
    )

    def fake_generate(*args, **kwargs):  # noqa: ANN001
        return [
            {
                "title": "Employer Blocked",
                "company": "BadCorp",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://ok.com/jobs/bad-123",
            },
            {
                "title": "Employer Allowed",
                "company": "GoodCorp",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://ok.com/jobs/good-456",
            },
        ]

    def fake_validate(url: str, timeout: int = 5, verbose: bool = False):  # noqa: ANN001
        return {"url": url, "valid": True, "status_code": 200, "error": None}

    monkeypatch.setattr("app.ui_server.generate_job_leads", fake_generate)
    monkeypatch.setattr("app.ui_server.validate_link", fake_validate)

    resp = client.post(
        "/api/search",
        json={"query": "engineer", "resume": None, "count": 5, "evaluate": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    companies = {lead["company"] for lead in data["leads"]}
    assert "BadCorp" not in companies
    assert "GoodCorp" in companies


def test_search_filters_hidden_jobs(monkeypatch):
    """Test that hidden jobs don't appear in search results."""
    client = TestClient(app)
    from app.job_tracker import generate_job_id, get_tracker

    def fake_generate(*args, **kwargs):  # noqa: ANN001
        return [
            {
                "title": "Job1",
                "company": "Company1",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://example.com/jobs/1",
            },
            {
                "title": "Job2 (will be hidden)",
                "company": "Company2",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://example.com/jobs/2",
            },
            {
                "title": "Job3",
                "company": "Company3",
                "location": "Remote",
                "summary": "Desc",
                "link": "https://example.com/jobs/3",
            },
        ]

    def fake_validate(url: str, timeout: int = 5, verbose: bool = False):  # noqa: ANN001
        return {"url": url, "valid": True, "status_code": 200, "error": None}

    monkeypatch.setattr("app.ui_server.generate_job_leads", fake_generate)
    monkeypatch.setattr("app.ui_server.validate_link", fake_validate)

    # Hide one job before searching
    tracker = get_tracker()
    hidden_job = {"title": "Job2 (will be hidden)", "link": "https://example.com/jobs/2"}
    tracker.track_job(hidden_job)
    tracker.hide_job(generate_job_id(hidden_job))

    resp = client.post(
        "/api/search",
        json={"query": "engineer", "resume": None, "count": 3, "evaluate": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should only return 2 jobs (Job1 and Job3), not the hidden one
    titles = {lead["title"] for lead in data["leads"]}
    assert "Job1" in titles
    assert "Job2 (will be hidden)" not in titles
    assert "Job3" in titles
    # Requested 3 but only 2 non-hidden available
    assert len(data["leads"]) == 2
