"""Tests for /api/search link validation and block list filtering.

We monkeypatch generate_job_leads and validate_link to simulate various
scenarios without external network calls.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.ui_server import app

CONFIG_FILE = Path("config.json")


def _write_config(data: dict):  # noqa: ANN001
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


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
