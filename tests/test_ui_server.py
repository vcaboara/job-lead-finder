"""Comprehensive tests for ui_server module."""

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient

from app.ui_server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """Mock the GEMINI_API_KEY environment variable."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"}):
        yield


@pytest.fixture
def no_api_key():
    """Remove GEMINI_API_KEY from environment."""
    with patch.dict(os.environ, {}, clear=True):
        yield


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_with_api_key(self, client, mock_api_key):
        """Test health endpoint when API key is configured."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_key_configured"] is True

    def test_health_without_api_key(self, client, no_api_key):
        """Test health endpoint when API key is not configured."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_key_configured"] is False


class TestSearchEndpoint:
    """Tests for /api/search endpoint."""

    def test_search_without_api_key(self, client, no_api_key):
        """Search should succeed without API key using local fallback."""
        response = client.post(
            "/api/search",
            json={"query": "python", "count": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data.get("leads"), list)

    def test_search_with_api_key_success(self, client, mock_api_key):
        """Test successful search with API key."""
        mock_leads = [
            {
                "title": "Python Developer",
                "company": "TechCo",
                "location": "Remote",
                "summary": "Great job",
                "link": "https://greenhouse.io/company/jobs/python-developer-123456",
            }
        ]

        with patch("app.ui_server.generate_job_leads", return_value=mock_leads):
            with patch("app.ui_server.save_to_file") as mock_save:
                with patch("app.ui_server.validate_link", return_value={"valid": True, "status_code": 200}):
                    response = client.post(
                        "/api/search",
                        json={
                            "query": "python developer",
                            "resume": "I am a Python expert",
                            "count": 2,
                            "min_score": 0,  # Don't filter by score in this test
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "success"
                    assert data["query"] == "python developer"
                    # With retry logic, we get 1 job even though we requested 2
                    # because the mock only returns 1 and retries won't help
                    assert data["count"] == 1
                    assert len(data["leads"]) == 1
                    assert data["leads"][0]["title"] == "Python Developer"
                    # Verify search metadata from retry logic
                    assert "total_fetched" in data
                    assert "filtered_count" in data
                    mock_save.assert_called_once()

    def test_search_with_default_resume(self, client, mock_api_key):
        """Test search uses default resume when not provided."""
        with patch("app.ui_server.generate_job_leads", return_value=[]) as mock_gen:
            with patch("app.ui_server._process_and_filter_leads", return_value=[]):
                with patch("app.ui_server.save_to_file"):
                    with patch.object(Path, "exists", return_value=False):
                        response = client.post(
                            "/api/search",
                            json={"query": "python developer", "count": 2},
                        )

                        assert response.status_code == 200
                        # Check that generate_job_leads was called
                        assert mock_gen.called

    def test_search_with_model_parameter(self, client, mock_api_key):
        """Test search with custom model parameter."""
        with patch("app.ui_server.generate_job_leads", return_value=[]) as mock_gen:
            with patch("app.ui_server._process_and_filter_leads", return_value=[]):
                with patch("app.ui_server.save_to_file"):
                    response = client.post(
                        "/api/search",
                        json={
                            "query": "python developer",
                            "count": 2,
                            "model": "custom-model",
                        },
                    )

                    assert response.status_code == 200
                    call_args = mock_gen.call_args
                    assert call_args[1]["model"] == "custom-model"

    def test_search_with_evaluate_parameter(self, client, mock_api_key):
        """Test search with evaluate parameter."""
        with patch("app.ui_server.generate_job_leads", return_value=[]) as mock_gen:
            with patch("app.ui_server._process_and_filter_leads", return_value=[]):
                with patch("app.ui_server.save_to_file"):
                    response = client.post(
                        "/api/search",
                        json={
                            "query": "python developer",
                            "count": 2,
                            "evaluate": True,
                        },
                    )

                    assert response.status_code == 200
                    call_args = mock_gen.call_args
                    assert call_args[1]["evaluate"] is True

    def test_search_handles_exception(self, client, mock_api_key):
        """Test search endpoint handles exceptions gracefully."""
        with patch("app.ui_server.generate_job_leads", side_effect=Exception("Test error")):
            with patch("app.ui_server._process_and_filter_leads", return_value=[]):
                response = client.post(
                    "/api/search",
                    json={"query": "python developer", "count": 2},
                )

                assert response.status_code == 500
                assert "Test error" in response.json()["detail"]

    def test_search_validation_missing_query(self, client, mock_api_key):
        """Test search validates required query field."""
        response = client.post(
            "/api/search",
            json={"count": 2},
        )
        assert response.status_code == 422  # Validation error

    def test_search_validation_invalid_count(self, client, mock_api_key):
        """Test search validates count field type."""
        response = client.post(
            "/api/search",
            json={"query": "python developer", "count": "not-a-number"},
        )
        assert response.status_code == 422  # Validation error


class TestLeadsEndpoint:
    """Tests for /api/leads endpoint."""

    def test_get_leads_file_not_exists(self, client):
        """Test get_leads when leads.json doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            response = client.get("/api/leads")
            assert response.status_code == 200
            data = response.json()
            assert data["leads"] == []

    def test_get_leads_success(self, client):
        """Test get_leads returns saved leads."""
        mock_leads = [
            {"title": "Job 1", "company": "Co1"},
            {"title": "Job 2", "company": "Co2"},
        ]

        mock_file_data = json.dumps(mock_leads)
        with patch("builtins.open", mock_open(read_data=mock_file_data)):
            with patch.object(Path, "exists", return_value=True):
                response = client.get("/api/leads")
                assert response.status_code == 200
                data = response.json()
                assert len(data["leads"]) == 2
                assert data["leads"][0]["title"] == "Job 1"

    def test_get_leads_handles_invalid_json(self, client):
        """Test get_leads handles invalid JSON gracefully."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch.object(Path, "exists", return_value=True):
                response = client.get("/api/leads")
                assert response.status_code == 500
                assert "Error reading leads" in response.json()["detail"]

    def test_get_leads_handles_file_read_error(self, client):
        """Test get_leads handles file read errors."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            with patch.object(Path, "exists", return_value=True):
                response = client.get("/api/leads")
                assert response.status_code == 500
                assert "Error reading leads" in response.json()["detail"]


class TestIndexEndpoint:
    """Tests for / (index) endpoint."""

    def test_index_returns_html(self, client):
        """Test index endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Job Lead Finder" in response.text

    def test_index_contains_api_endpoints(self, client):
        """Test index HTML references API endpoints."""
        response = client.get("/")
        assert "/api/search" in response.text
        assert "/api/leads" in response.text

    def test_index_contains_form_elements(self, client):
        """Test index HTML contains expected form elements."""
        response = client.get("/")
        # Check for key UI elements
        assert "query" in response.text.lower()
        assert "search" in response.text.lower()

    def test_index_template_packaged_correctly(self, client):
        """Test that HTML template is properly packaged and accessible."""
        response = client.get("/")
        assert response.status_code == 200
        # Ensure we get actual HTML content, not 404 or 500
        assert len(response.text) > 1000
        assert "<!DOCTYPE html>" in response.text
        assert "</html>" in response.text


class TestChangelogEndpoint:
    """Tests for /api/changelog endpoint."""

    def test_changelog_success(self, client):
        """Test successful retrieval of changelog content."""
        response = client.get("/api/changelog")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Verify changelog follows Keep a Changelog format
        assert "# Changelog" in response.text or "## [" in response.text

    def test_changelog_not_found(self, client):
        """Test 404 when CHANGELOG.md is not found."""
        with patch.object(Path, "read_text", side_effect=FileNotFoundError()):
            response = client.get("/api/changelog")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_changelog_content_validation(self, client):
        """Test changelog contains expected version and format information."""
        response = client.get("/api/changelog")
        assert response.status_code == 200
        text = response.text
        # Should contain version information
        assert len(text) > 100  # Non-trivial content
        # Should be plain text format
        assert isinstance(text, str)


class TestAppMetadata:
    """Tests for app metadata and configuration."""

    def test_app_title(self):
        """Test app has correct title."""
        assert app.title == "Job Lead Finder"

    def test_app_version(self):
        """Test app has version set."""
        assert app.version == "0.1.1"
