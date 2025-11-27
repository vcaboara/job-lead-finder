import os
import pytest

from app import gemini_provider


def test_gemini_provider_skipped_if_missing():
    """This test ensures the provider can be imported but skips if SDK/key missing."""
    genai = getattr(gemini_provider, "genai", None)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if genai is None or not key:
        pytest.skip("Gemini SDK or API key not available; skipping integration test")

    prov = gemini_provider.GeminiProvider()
    # Use a tiny fake job and resume; don't assert on score value (networked)
    out = prov.evaluate(
        {"title": "Test", "company": "X", "location": "Remote", "description": "Python"}, "Skills: Python"
    )
    assert isinstance(out, dict)
    assert "score" in out and "reasoning" in out
