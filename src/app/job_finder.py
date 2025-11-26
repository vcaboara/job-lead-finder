"""Job finder orchestration.

This module adapts legacy worker logic to the starter CLI. It attempts to
use the Gemini provider when available; otherwise falls back to local
sample search results.
"""
from typing import List, Dict, Any
from .gemini_provider import GeminiProvider
from .main import format_resume, fetch_jobs
import os


def generate_job_leads(query: str, resume_text: str, count: int = 5, model: str | None = None, verbose: bool = False) -> List[Dict[str, Any]]:
    """Generate job leads. Use GeminiProvider.generate_job_leads when possible.

    Returns a list of job dicts. On failure returns empty list.
    """
    # Try to use Gemini provider if API key and SDK present
    try:
        provider = GeminiProvider()
        print("job_finder: Using GeminiProvider")
    except Exception as e:
        provider = None
        print(f"job_finder: GeminiProvider unavailable ({e}); falling back to local search")

    if provider:
        try:
            leads = provider.generate_job_leads(query, resume_text, count=count, model=model, verbose=verbose)
            print(f"job_finder: Gemini returned {len(leads)} leads")
            return leads
        except Exception as e:
            # Provide diagnostics when verbose
            if os.getenv("VERBOSE") or verbose:
                import traceback

                print("job_finder: Exception while calling GeminiProvider:", e)
                traceback.print_exc()
            return []

    # Fallback: use simple local search
    sample = fetch_jobs(query)
    # Map to lead schema
    leads: List[Dict[str, Any]] = []
    for j in sample[:count]:
        leads.append({
            "title": j.get("title"),
            "company": j.get("company"),
            "location": j.get("location"),
            "summary": j.get("description"),
            "link": j.get("link", ""),
        })
    print(f"job_finder: Fallback returned {len(leads)} leads")
    return leads


def save_to_file(leads: List[Dict[str, Any]], path: str) -> None:
    import json

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(leads, fh, indent=2)
