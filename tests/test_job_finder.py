import os
import pytest

from app import job_finder


def test_generate_job_leads_fallback():
    """If Gemini isn't configured, the fallback should return a list (possibly empty)."""
    leads = job_finder.generate_job_leads("python", "Skills: Python", count=2)
    assert isinstance(leads, list)


def test_generate_job_leads_gemini_skip():
    # If GEMINI not configured, skip integration
    gen_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gen_key:
        pytest.skip("No Gemini API key; skipping integration test")
    leads = job_finder.generate_job_leads("python", "Skills: Python", count=1)
    assert isinstance(leads, list)
