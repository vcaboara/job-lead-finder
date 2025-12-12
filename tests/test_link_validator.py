"""Comprehensive tests for link_validator module."""

from unittest.mock import Mock, patch

import pytest

from app.link_validator import REQUESTS_AVAILABLE, filter_valid_links, validate_leads, validate_link


class TestValidateLink:
    """Test cases for validate_link function."""

    def test_validate_link_with_invalid_url_none(self):
        """Test validation with None URL."""
        result = validate_link(None)
        assert result["valid"] is False
        assert result["error"] == "Invalid URL format"
        assert result["warning"] == "invalid url"

    def test_validate_link_with_empty_string(self):
        """Test validation with empty string URL."""
        result = validate_link("")
        assert result["valid"] is False
        assert result["error"] == "Invalid URL format"

    def test_validate_link_with_invalid_type(self):
        """Test validation with non-string URL."""
        result = validate_link(123)
        assert result["valid"] is False
        assert result["error"] == "Invalid URL format"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_adds_https_prefix(self):
        """Test that URLs without scheme get https:// added."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com"
            mock_requests.head.return_value = mock_resp

            result = validate_link("example.com")
            # Should have called with https:// prefix
            mock_requests.head.assert_called_once()
            assert result["valid"] is True

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_success_200(self):
        """Test successful validation with 200 status."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com"
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com")
            assert result["valid"] is True
            assert result["status_code"] == 200
            assert result["final_url"] == "https://example.com"
            assert result["error"] is None

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_redirect_301(self):
        """Test successful validation with redirect."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 301
            mock_resp.url = "https://example.com/new"
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com/old")
            assert result["valid"] is True
            assert result["status_code"] == 301

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_not_found_404(self):
        """Test validation with 404 status."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 404
            mock_resp.url = "https://example.com/missing"
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com/missing")
            assert result["valid"] is False
            assert result["status_code"] == 404
            assert result["warning"] == "not found (404)"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_forbidden_403(self):
        """Test validation with 403 status."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 403
            mock_resp.url = "https://example.com/forbidden"
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com/forbidden")
            # 403 now treated as present but restricted
            assert result["valid"] is True
            assert result["status_code"] == 403
            assert result["warning"] == "access forbidden (treated as present)"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_unauthorized_401(self):
        """Test validation with 401 status."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 401
            mock_resp.url = "https://example.com/private"
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com/private")
            assert result["valid"] is False
            assert result["status_code"] == 401
            assert result["warning"] == "requires authentication"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_server_error_500(self):
        """Test validation with 500 status."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 500
            mock_resp.url = "https://example.com/api/endpoint"  # Not caught by soft-404 detector
            mock_requests.head.return_value = mock_resp

            result = validate_link("https://example.com/api/endpoint")
            assert result["valid"] is False
            assert result["status_code"] == 500
            assert result["warning"] == "server error"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_head_fails_fallback_to_get(self):
        """Test that GET is used as fallback when HEAD fails."""
        with patch("app.link_validator.requests") as mock_requests:
            # HEAD raises exception
            import requests as req_module

            mock_requests.exceptions.RequestException = req_module.exceptions.RequestException
            mock_requests.head.side_effect = req_module.exceptions.RequestException("HEAD failed")

            # GET succeeds
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com"
            mock_requests.get.return_value = mock_resp

            result = validate_link("https://example.com")
            assert result["valid"] is True
            assert mock_requests.head.called
            assert mock_requests.get.called

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_both_requests_fail(self):
        """Test when both HEAD and GET fail."""
        with patch("app.link_validator.requests") as mock_requests:
            import requests as req_module

            mock_requests.exceptions.RequestException = req_module.exceptions.RequestException
            exception = req_module.exceptions.RequestException("Connection error")
            mock_requests.head.side_effect = exception
            mock_requests.get.side_effect = exception

            result = validate_link("https://example.com")
            assert result["valid"] is False
            assert result["error"] is not None
            assert "Connection error" in result["error"]

    def test_validate_link_without_requests_library(self):
        """Test behavior when requests library is not available."""
        with patch("app.link_validator.REQUESTS_AVAILABLE", False):
            result = validate_link("https://example.com")
            assert result["valid"] is None
            assert result["error"] == "requests library not installed; cannot validate"
            assert result["warning"] == "validator unavailable"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_link_verbose_output(self, capsys, caplog):
        """Test verbose output for successful validation."""
        import logging

        caplog.set_level(logging.INFO)

        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com"
            mock_requests.head.return_value = mock_resp

            validate_link("https://example.com", verbose=True)
            # Check that logging occurred
            assert len(caplog.records) > 0
            assert any("200" in record.message for record in caplog.records)


class TestValidateLeads:
    """Test cases for validate_leads function."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_leads_multiple_urls(self):
        """Test validating multiple URLs."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp1 = Mock()
            mock_resp1.status_code = 200
            mock_resp1.url = "https://example1.com"

            mock_resp2 = Mock()
            mock_resp2.status_code = 404
            mock_resp2.url = "https://example2.com"

            mock_requests.head.side_effect = [mock_resp1, mock_resp2]

            leads = [
                {"title": "Job 1", "company": "Co1", "link": "https://example1.com"},
                {"title": "Job 2", "company": "Co2", "link": "https://example2.com"},
            ]
            results = validate_leads(leads)

            assert len(results) == 2
            assert results[0]["link_valid"] is True
            assert results[1]["link_valid"] is False

    def test_validate_leads_empty_list(self):
        """Test validating empty list."""
        results = validate_leads([])
        assert results == []

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_leads_verbose_output(self, capsys, caplog):
        """Test verbose output for lead validation."""
        import logging

        caplog.set_level(logging.INFO)

        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com"
            mock_requests.head.return_value = mock_resp

            leads = [{"title": "Job", "company": "Co", "link": "https://example.com"}]
            validate_leads(leads, verbose=True)

            # Check that logging occurred
            assert len(caplog.records) > 0
            assert any("Validating" in record.message or "valid" in record.message for record in caplog.records)


class TestEnrichLeadsValidation:
    """Test cases for lead enrichment with validation."""

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_validate_leads_adds_validation_fields(self):
        """Test that enrichment adds validation fields to leads."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com/job1"
            mock_requests.head.return_value = mock_resp

            leads = [{"title": "Job 1", "company": "Co", "link": "https://example.com/job1"}]

            enriched = validate_leads(leads)

            assert len(enriched) == 1
            assert "link_valid" in enriched[0]
            assert "link_status_code" in enriched[0]
            assert "link_final_url" in enriched[0]
            assert enriched[0]["link_valid"] is True
            assert enriched[0]["link_status_code"] == 200

    def test_enrich_leads_empty_list(self):
        """Test enriching empty list."""
        enriched = validate_leads([])
        assert enriched == []

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_enrich_leads_missing_link_field(self):
        """Test enriching leads without link field."""
        leads = [{"title": "Job 1", "company": "Co"}]
        enriched = validate_leads(leads)

        # Should handle missing link gracefully
        assert len(enriched) == 1

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_enrich_leads_preserves_original_fields(self):
        """Test that enrichment preserves original lead data."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.url = "https://example.com/job1"
            mock_requests.head.return_value = mock_resp

            leads = [
                {
                    "title": "Python Developer",
                    "company": "TechCo",
                    "location": "Remote",
                    "summary": "Great job",
                    "link": "https://example.com/job1",
                }
            ]

            enriched = validate_leads(leads)

            assert enriched[0]["title"] == "Python Developer"
            assert enriched[0]["company"] == "TechCo"
            assert enriched[0]["location"] == "Remote"
            assert enriched[0]["summary"] == "Great job"

    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests library not installed")
    def test_enrich_leads_with_broken_links(self):
        """Test enrichment with broken links."""
        with patch("app.link_validator.requests") as mock_requests:
            mock_resp = Mock()
            mock_resp.status_code = 404
            mock_resp.url = "https://example.com/missing"
            mock_requests.head.return_value = mock_resp

            leads = [{"title": "Job 1", "company": "Co", "link": "https://example.com/missing"}]

            enriched = validate_leads(leads)

            assert enriched[0]["link_valid"] is False
            assert enriched[0]["link_status_code"] == 404
            assert enriched[0]["link_warning"] == "not found (404)"


class TestFilterValidLinks:
    """Test cases for filter_valid_links function."""

    def test_filter_valid_links_keeps_valid_only(self):
        """Test filtering keeps only valid links."""
        leads = [
            {"title": "Job 1", "company": "Co1", "link_valid": True},
            {"title": "Job 2", "company": "Co2", "link_valid": False},
            {"title": "Job 3", "company": "Co3", "link_valid": True},
        ]

        filtered = filter_valid_links(leads)
        assert len(filtered) == 2
        assert all(lead["link_valid"] for lead in filtered)

    def test_filter_valid_links_empty_list(self):
        """Test filtering empty list."""
        filtered = filter_valid_links([])
        assert filtered == []

    def test_filter_valid_links_all_invalid(self):
        """Test filtering when all links are invalid."""
        leads = [
            {"title": "Job 1", "company": "Co1", "link_valid": False},
            {"title": "Job 2", "company": "Co2", "link_valid": False},
        ]

        filtered = filter_valid_links(leads)
        assert filtered == []

    def test_filter_valid_links_missing_field(self):
        """Test filtering when link_valid field is missing."""
        leads = [{"title": "Job 1", "company": "Co1"}]

        filtered = filter_valid_links(leads)
        assert filtered == []
