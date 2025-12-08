"""Tests for /api/search link validation and block list filtering.

We monkeypatch generate_job_leads and validate_link to simulate various
scenarios without external network calls.
"""

from fastapi.testclient import TestClient

from app.ui_server import app


def test_search_marks_invalid_links(monkeypatch, mock_config_manager):  # noqa: ARG001
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


def test_search_filters_blocked_site(monkeypatch, mock_config_manager):
    # Set config before creating TestClient so it loads properly
    mock_config_manager["config"] = {
        "system_instructions": "",
        "blocked_entities": [{"type": "site", "value": "blocked.com"}],
        "region": "",
    }
    client = TestClient(app)

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


def test_search_filters_blocked_employer(monkeypatch, mock_config_manager):
    # Set config before creating TestClient so it loads properly
    mock_config_manager["config"] = {
        "system_instructions": "",
        "blocked_entities": [{"type": "employer", "value": "BadCorp"}],
        "region": "",
    }
    client = TestClient(app)

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


def test_search_filters_hidden_jobs(monkeypatch, mock_config_manager):  # noqa: ARG001
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
