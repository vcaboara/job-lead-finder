"""Tests for /api/validate-link endpoint.

We monkeypatch validate_link to avoid network dependency and ensure
the endpoint returns expected structure.
"""

from fastapi.testclient import TestClient

from app.ui_server import app


def test_validate_link_success(monkeypatch):
    def mock_validate(url: str, verbose: bool = False):  # noqa: ANN001
        return {"url": url, "valid": True, "status_code": 200, "error": None}

    monkeypatch.setattr("app.ui_server.validate_link", mock_validate)
    client = TestClient(app)
    resp = client.post("/api/validate-link", json={"url": "https://example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["status_code"] == 200
    assert data["error"] is None


def test_validate_link_failure(monkeypatch):
    def mock_validate(url: str, verbose: bool = False):  # noqa: ANN001
        return {"url": url, "valid": False, "status_code": None, "error": "unreachable"}

    monkeypatch.setattr("app.ui_server.validate_link", mock_validate)
    client = TestClient(app)
    resp = client.post("/api/validate-link", json={"url": "https://bad.example"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["error"] == "unreachable"
