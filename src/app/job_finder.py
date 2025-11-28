"""Job finder orchestration.

This module orchestrates job search across multiple sources:
1. MCP providers (LinkedIn, Indeed, GitHub) - primary source
2. Gemini provider - fallback if MCPs unavailable
3. Local sample data - final fallback

Priority: MCP > Gemini > Local
"""

import os
from typing import Any, Dict, List

from .gemini_provider import GeminiProvider
from .main import fetch_jobs


def generate_job_leads(
    query: str,
    resume_text: str,
    count: int = 5,
    model: str | None = None,
    verbose: bool = False,
    evaluate: bool = False,
    use_mcp: bool = True,
) -> List[Dict[str, Any]]:
    """Generate job leads using MCP providers, Gemini, or local fallback.

    Priority:
    1. MCP providers (if use_mcp=True and MCPs available)
    2. Gemini provider (if API key configured)
    3. Local sample data (final fallback)

    Args:
        query: Job search query.
        resume_text: Candidate's resume/profile text.
        count: Number of leads to return.
        model: Optional model name override (for Gemini).
        verbose: Print verbose diagnostics.
        evaluate: If True, score each job against the resume (0-100).
        use_mcp: If True, try MCP providers first (default: True).

    Returns a list of job dicts. On failure returns empty list.
    """
    leads: List[Dict[str, Any]] = []

    # 1. Try MCP providers first
    if use_mcp:
        try:
            from .mcp_providers import generate_job_leads_via_mcp

            location = os.getenv("DEFAULT_LOCATION", "United States")
            count_per_mcp = int(os.getenv("JOBS_PER_MCP", str(count)))

            print("job_finder: Trying MCP providers...")
            leads = generate_job_leads_via_mcp(
                query=query, count=count, count_per_provider=count_per_mcp, location=location
            )

            if leads:
                print(f"job_finder: MCP providers returned {len(leads)} leads")
                # Evaluate if requested
                if evaluate:
                    # Try to get Gemini provider for evaluation
                    try:
                        provider = GeminiProvider()
                        leads = _evaluate_leads(leads, resume_text, provider, model, verbose)
                    except Exception as e:
                        if verbose:
                            print(f"job_finder: Evaluation unavailable (no Gemini): {e}")
                return leads
            else:
                print("job_finder: No results from MCP providers, trying Gemini...")

        except Exception as e:
            if verbose:
                import traceback

                print(f"job_finder: MCP providers failed: {e}")
                traceback.print_exc()
            print("job_finder: MCP unavailable, falling back to Gemini")

    # 2. Try Gemini provider
    try:
        provider = GeminiProvider()
        print("job_finder: Using GeminiProvider")
    except Exception as e:
        provider = None
        if verbose:
            print(f"job_finder: GeminiProvider unavailable ({e}); falling back to local search")

    if provider:
        try:
            leads = provider.generate_job_leads(query, resume_text, count=count, model=model, verbose=verbose)
            print(f"job_finder: Gemini returned {len(leads)} leads")
            # If Gemini returned results, use them
            if leads:
                # Evaluate each lead if requested
                if evaluate:
                    leads = _evaluate_leads(leads, resume_text, provider, model, verbose)
                return leads
            else:
                print("job_finder: Gemini returned 0 leads, using local fallback")
        except Exception as e:
            # Provide diagnostics when verbose
            if os.getenv("VERBOSE") or verbose:
                import traceback

                print("job_finder: Exception while calling GeminiProvider:", e)
                traceback.print_exc()
            print("job_finder: Gemini failed, using local fallback")

    # 3. Fallback: use simple local search
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
                "source": "Local",
            }
        )
    print(f"job_finder: Fallback returned {len(leads)} leads")
    # Evaluate each lead if requested (requires Gemini)
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
