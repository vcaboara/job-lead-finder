"""Comprehensive tests for job_finder module."""

import os
from unittest.mock import Mock, patch

import pytest

from app import job_finder
from app.gemini_provider import GeminiProvider


class TestGenerateJobLeads:
    """Tests for generate_job_leads function."""

    def test_generate_job_leads_fallback_no_provider(self):
        """Test fallback to local search when Gemini isn't configured."""
        with patch("app.job_finder.GeminiProvider", side_effect=Exception("No API key")):
            leads = job_finder.generate_job_leads("python", "Skills: Python", count=2)
            assert isinstance(leads, list)
            # Should return fallback results from fetch_jobs
            if len(leads) > 0:
                assert "title" in leads[0]
                assert "company" in leads[0]

    def test_generate_job_leads_with_gemini_provider(self):
        """Test using GeminiProvider when available."""
        mock_leads = [
            {
                "title": "Python Dev",
                "company": "TechCo",
                "location": "Remote",
                "summary": "Great job",
                "link": "http://test.com",
            }
        ]

        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.return_value = mock_leads

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            leads = job_finder.generate_job_leads("python", "Skills: Python", count=2, use_mcp=False)
            assert isinstance(leads, list)
            assert len(leads) == 1
            assert leads[0]["title"] == "Python Dev"

    def test_generate_job_leads_gemini_skip(self):
        """Test integration with Gemini if configured."""
        gen_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gen_key:
            pytest.skip("No Gemini API key; skipping integration test")
        leads = job_finder.generate_job_leads("python", "Skills: Python", count=1)
        assert isinstance(leads, list)

    def test_generate_job_leads_custom_count(self):
        """Test that count parameter is respected."""
        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.return_value = []

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            job_finder.generate_job_leads("python", "Skills: Python", count=10, use_mcp=False)
            # Verify count was passed to provider
            call_args = mock_provider.generate_job_leads.call_args
            assert call_args[1]["count"] == 10

    def test_generate_job_leads_custom_model(self):
        """Test that model parameter is passed to provider."""
        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.return_value = []

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            job_finder.generate_job_leads("python", "Skills: Python", model="custom-model", use_mcp=False)
            call_args = mock_provider.generate_job_leads.call_args
            assert call_args[1]["model"] == "custom-model"

    def test_generate_job_leads_verbose_mode(self):
        """Test verbose mode enables diagnostic output."""
        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.return_value = []

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            job_finder.generate_job_leads("python", "Skills: Python", verbose=True, use_mcp=False)
            call_args = mock_provider.generate_job_leads.call_args
            assert call_args[1]["verbose"] is True

    def test_generate_job_leads_with_evaluate(self):
        """Test evaluation adds score and reasoning to leads."""
        mock_leads = [
            {
                "title": "Python Dev",
                "company": "TechCo",
                "location": "Remote",
                "summary": "Great job",
                "link": "http://test.com",
            }
        ]

        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.return_value = mock_leads
        mock_provider.evaluate.return_value = {"score": 85, "reasoning": "Good match"}

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            leads = job_finder.generate_job_leads("python", "Skills: Python", evaluate=True)
            assert leads[0]["score"] == 85
            assert leads[0]["reasoning"] == "Good match"

    def test_generate_job_leads_handles_provider_exception(self):
        """Test graceful handling when provider raises exception."""
        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.generate_job_leads.side_effect = Exception("API error")

        with patch("app.job_finder.GeminiProvider", return_value=mock_provider):
            # Should fall back to local search when MCP and Gemini both fail
            leads = job_finder.generate_job_leads("python", "Skills: Python", use_mcp=False)
            # Fallback should return some local results
            assert isinstance(leads, list)
            # Should have expected fields
            if len(leads) > 0:
                assert "title" in leads[0]
                assert "source" in leads[0]
                assert leads[0]["source"] == "Local"

    def test_generate_job_leads_fallback_structure(self):
        """Test fallback results have correct structure."""
        with patch("app.job_finder.GeminiProvider", side_effect=Exception("No provider")):
            leads = job_finder.generate_job_leads("python", "Skills: Python", count=1)
            if len(leads) > 0:
                lead = leads[0]
                assert "title" in lead
                assert "company" in lead
                assert "location" in lead
                assert "summary" in lead
                assert "link" in lead


class TestEvaluateLeads:
    """Tests for _evaluate_leads helper function."""

    def test_evaluate_leads_adds_score_and_reasoning(self):
        """Test evaluation enriches leads with score and reasoning."""
        leads = [{"title": "Job 1", "company": "Co", "location": "Remote", "summary": "Python dev"}]

        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.evaluate.return_value = {"score": 90, "reasoning": "Perfect match"}

        result = job_finder._evaluate_leads(leads, "Skills: Python", mock_provider)

        assert result[0]["score"] == 90
        assert result[0]["reasoning"] == "Perfect match"

    def test_evaluate_leads_handles_missing_fields(self):
        """Test evaluation handles leads with missing fields gracefully."""
        leads = [{"title": "Job 1"}]

        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.evaluate.return_value = {"score": 50, "reasoning": "Incomplete"}

        result = job_finder._evaluate_leads(leads, "Skills: Python", mock_provider)

        assert len(result) == 1
        # Should still have score added
        assert "score" in result[0]

    def test_evaluate_leads_handles_evaluation_exception(self):
        """Test evaluation continues even if one evaluation fails."""
        leads = [
            {"title": "Job 1", "company": "Co1", "location": "Remote", "summary": "Desc 1"},
            {"title": "Job 2", "company": "Co2", "location": "Remote", "summary": "Desc 2"},
        ]

        mock_provider = Mock(spec=GeminiProvider)
        # First evaluation succeeds, second fails
        mock_provider.evaluate.side_effect = [
            {"score": 80, "reasoning": "Good"},
            Exception("API error"),
        ]

        result = job_finder._evaluate_leads(leads, "Skills: Python", mock_provider)

        # First lead should be evaluated
        assert result[0]["score"] == 80
        # Second lead should have default score of 50 when evaluation fails
        assert len(result) == 2
        assert result[1]["score"] == 50
        assert result[1]["reasoning"] == "Evaluation unavailable."


class TestSaveToFile:
    """Tests for save_to_file function."""

    def test_save_to_file_creates_json(self):
        """Test saving leads to JSON file."""
        from unittest.mock import mock_open

        leads = [{"title": "Job 1", "company": "Co"}]

        m = mock_open()
        with patch("builtins.open", m):
            job_finder.save_to_file(leads, "test.json")

        # Verify file was opened for writing (may include encoding parameter)
        assert m.called
        call_args = m.call_args
        assert call_args[0][0] == "test.json"
        assert "w" in call_args[0] or call_args[1].get("mode") == "w"
        # Verify JSON was written
        handle = m()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "Job 1" in written_content

    def test_save_to_file_pretty_prints(self):
        """Test that saved JSON is pretty-printed."""
        from unittest.mock import mock_open

        leads = [{"title": "Job 1"}]

        m = mock_open()
        with patch("builtins.open", m):
            job_finder.save_to_file(leads, "test.json")

        handle = m()
        # Check that indent parameter was used (pretty print)
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        # Pretty-printed JSON will have newlines
        assert "\n" in written_content
