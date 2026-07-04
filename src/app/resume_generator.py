"""Resume tailoring using local Ollama with Claude API fallback.

Produces job-specific highlights from the candidate's resume —
not a full resume rewrite, but a targeted summary for the application.

Model routing:
  1. Ollama (OLLAMA_GENERATE_MODEL, default: gemma4:12b) — free, local
  2. Claude API (ANTHROPIC_API_KEY) — fallback when Ollama unavailable
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_MODEL = os.getenv("OLLAMA_GENERATE_MODEL", "gemma4:12b")
GENERATE_TIMEOUT = int(os.getenv("OLLAMA_GENERATE_TIMEOUT", "120"))

_RESUME_HIGHLIGHTS_PROMPT = """You are a career coach helping tailor a resume for a specific job application.

CANDIDATE RESUME:
{resume_text}

TARGET JOB:
Title: {title}
Company: {company}
Description:
{job_description}

Produce a short "Why I'm a fit" section (3-5 bullet points, plain text) that:
- Pulls specific experiences/skills from the resume that match job requirements
- Uses concrete numbers or outcomes where the resume has them
- Does NOT invent anything not in the resume
- Each bullet is one sentence, starting with a past-tense action verb

Output ONLY the bullet points, one per line, starting with "- ".

Tailored highlights:"""


def _ollama_generate(prompt: str) -> str:
    """Call Ollama generate API directly."""
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_GENERATE_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 384},
            },
            timeout=GENERATE_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
        logger.warning("Ollama generate returned HTTP %s", resp.status_code)
    except httpx.TimeoutException:
        logger.warning("Ollama generate timed out after %ss", GENERATE_TIMEOUT)
    except Exception as e:
        logger.warning("Ollama generate error: %s", e)
    return ""


def _claude_generate(prompt: str) -> str:
    """Call Claude API as fallback."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip() if msg.content else ""
    except Exception as e:
        logger.warning("Claude fallback error: %s", e)
    return ""


def generate_resume(
    job_description: str,
    candidate_info: dict[str, Any] | None = None,
    *,
    title: str = "",
    company: str = "",
    resume_text: str = "",
) -> str:
    """Generate tailored resume highlights for a specific job.

    Extracts and formats the most relevant experience bullets from the
    candidate's resume for a given job description.

    Args:
        job_description: Full job description text.
        candidate_info: Legacy dict form — merged into resume_text if provided.
        title: Job title.
        company: Company name.
        resume_text: Candidate resume as plain text.

    Returns:
        Bullet-point highlights string, or empty string if all providers fail.
    """
    if candidate_info and not resume_text:
        resume_text = candidate_info.get("resume", candidate_info.get("resume_text", str(candidate_info)))

    if not resume_text:
        return ""

    prompt = _RESUME_HIGHLIGHTS_PROMPT.format(
        resume_text=resume_text[:3000],
        title=title or "the position",
        company=company or "the company",
        job_description=job_description[:2000],
    )

    result = _ollama_generate(prompt)
    if result:
        logger.info("Resume highlights generated via Ollama (%s)", OLLAMA_GENERATE_MODEL)
        return result

    result = _claude_generate(prompt)
    if result:
        logger.info("Resume highlights generated via Claude fallback")
        return result

    logger.error("All resume generation providers failed")
    return ""
