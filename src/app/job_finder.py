"""Job finder orchestration.

This module adapts legacy worker logic to the starter CLI. It attempts to
use the Gemini provider when available; otherwise falls back to local
sample search results.
"""

from typing import List, Dict, Any
from .gemini_provider import GeminiProvider
from .main import format_resume, fetch_jobs
import os


def generate_job_leads(
    query: str,
    resume_text: str,
    count: int = 5,
    model: str | None = None,
    verbose: bool = False,
    evaluate: bool = False,
) -> List[Dict[str, Any]]:
    """Generate job leads. Use GeminiProvider.generate_job_leads when possible.

    Args:
        query: Job search query.
        resume_text: Candidate's resume/profile text.
        count: Number of leads to return.
        model: Optional model name override.
        verbose: Print verbose diagnostics.
        evaluate: If True, score each job against the resume (0-100).

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
            # Evaluate each lead if requested
            if evaluate:
                leads = _evaluate_leads(leads, resume_text, provider, model, verbose)
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
        leads.append(
            {
                "title": j.get("title"),
                "company": j.get("company"),
                "location": j.get("location"),
                "summary": j.get("description"),
                "link": j.get("link", ""),
            }
        )
    print(f"job_finder: Fallback returned {len(leads)} leads")
    # Evaluate each lead if requested
    if evaluate and provider:
        leads = _evaluate_leads(leads, resume_text, provider, model, verbose)
    return leads


def _evaluate_leads(
    leads: List[Dict[str, Any]],
    resume_text: str,
    provider: GeminiProvider,
    model: str | None = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """Evaluate each lead against resume and add score/reasoning."""
    evaluated = []
    for lead in leads:
        try:
            job_dict = {
                "title": lead.get("title", ""),
                "company": lead.get("company", ""),
                "location": lead.get("location", ""),
                "description": lead.get("summary", ""),
            }
            evaluation = provider.evaluate(job_dict, resume_text)
            # Add evaluation to lead
            lead["score"] = evaluation.get("score", 0)
            lead["reasoning"] = evaluation.get("reasoning", "")
        except Exception as e:
            if verbose:
                print(f"job_finder: evaluation failed for {lead.get('title', '?')}: {e}")
            # Default to neutral score if evaluation fails
            lead["score"] = 50
            lead["reasoning"] = "Evaluation unavailable."
        evaluated.append(lead)
    return evaluated


def save_to_file(leads: List[Dict[str, Any]], path: str) -> None:
    """Save leads to JSON file (creates or overwrites)."""
    import json

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(leads, fh, indent=2)
    print(f"job_finder: saved {len(leads)} leads to {path}")
