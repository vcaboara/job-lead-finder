"""Tests for the gemini_provider fallback logic."""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from app import gemini_provider


def test_gemini_provider_fallback_when_tool_returns_zero():
    """Test that the provider retries without tools when google_search returns 0 jobs."""
    # Skip if no SDK or key
    genai = getattr(gemini_provider, "genai", None)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if genai is None or not key:
        pytest.skip("Gemini SDK or API key not available; skipping integration test")

    # Mock the client to simulate tool call returning empty, then fallback succeeding
    with patch.object(genai, "Client") as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        # First call (with tools) returns empty text
        mock_resp1 = Mock()
        mock_resp1.text = "[]"
        
        # Second call (fallback without tools) returns jobs
        mock_resp2 = Mock()
        mock_resp2.text = '[{"title": "Test Job", "company": "TestCo", "location": "Remote", "summary": "A test", "link": "http://test.com"}]'
        
        # Setup generate_content to return different responses
        mock_client_instance.models.generate_content.side_effect = [mock_resp1, mock_resp2]
        
        prov = gemini_provider.GeminiProvider(api_key=key)
        jobs = prov.generate_job_leads("python developer", "Senior Python dev", count=1, verbose=True)
        
        # Should have called generate_content twice (tool attempt + fallback)
        assert mock_client_instance.models.generate_content.call_count == 2
        # Should return the fallback results
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Test Job"


def test_gemini_provider_no_fallback_when_tool_succeeds():
    """Test that fallback is not triggered when tool call returns results."""
    genai = getattr(gemini_provider, "genai", None)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if genai is None or not key:
        pytest.skip("Gemini SDK or API key not available; skipping integration test")

    with patch.object(genai, "Client") as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        # First call (with tools) returns jobs
        mock_resp = Mock()
        mock_resp.text = '[{"title": "Tool Job", "company": "ToolCo", "location": "Remote", "summary": "From tool", "link": "http://tool.com"}]'
        mock_client_instance.models.generate_content.return_value = mock_resp
        
        prov = gemini_provider.GeminiProvider(api_key=key)
        jobs = prov.generate_job_leads("python developer", "Senior Python dev", count=1, verbose=False)
        
        # Fallback should not be triggered - the important check is that we got results
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Tool Job"


def test_gemini_provider_returns_empty_when_both_fail():
    """Test that provider returns empty list when both tool and fallback fail."""
    genai = getattr(gemini_provider, "genai", None)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if genai is None or not key:
        pytest.skip("Gemini SDK or API key not available; skipping integration test")

    with patch.object(genai, "Client") as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        # Both calls return empty
        mock_resp1 = Mock()
        mock_resp1.text = "[]"
        mock_resp2 = Mock()
        mock_resp2.text = "[]"
        mock_client_instance.models.generate_content.side_effect = [mock_resp1, mock_resp2]
        
        prov = gemini_provider.GeminiProvider(api_key=key)
        jobs = prov.generate_job_leads("python developer", "Senior Python dev", count=1, verbose=False)
        
        assert mock_client_instance.models.generate_content.call_count == 2
        assert len(jobs) == 0
