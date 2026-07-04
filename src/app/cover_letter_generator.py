"""Cover letter generation using local Ollama with Claude API fallback.

Model routing:
  1. Ollama (OLLAMA_GENERATE_MODEL, default: gemma4:12b) — free, local, no quota
  2. Claude API (ANTHROPIC_API_KEY) — quality fallback when Ollama unavailable
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_MODEL = os.getenv("OLLAMA_GENERATE_MODEL", "gemma4:12b")
GENERATE_TIMEOUT = int(os.getenv("OLLAMA_GENERATE_TIMEOUT", "120"))

_COVER_LETTER_PROMPT = """You are writing a job application cover letter for a real candidate.

CANDIDATE RESUME:
{resume_text}

JOB DETAILS:
Title: {title}
Company: {company}
Location: {location}
Description:
{job_description}

Write a concise, professional cover letter (3 short paragraphs, under 300 words total) that:
1. Opens by naming the role and expressing genuine interest (1-2 sentences)
2. Highlights 2-3 specific resume experiences that match the job requirements
3. Closes with availability and a call to action

RULES:
- Do NOT invent experience not in the resume
- Do NOT use generic filler phrases ("I am excited to...", "I would be a great fit")
- Use plain text only, no markdown, no placeholders like [Your Name]
- Write as if the candidate is sending this directly

Cover letter:"""


def _ollama_generate(prompt: str) -> str:
    """Call Ollama generate API directly."""
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_GENERATE_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 512},
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
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip() if msg.content else ""
    except Exception as e:
        logger.warning("Claude fallback error: %s", e)
    return ""


def generate_cover_letter(
    job_description: str,
    candidate_info: dict[str, Any] | None = None,
    *,
    title: str = "",
    company: str = "",
    location: str = "",
    resume_text: str = "",
) -> str:
    """Generate a cover letter tailored to the job description.

    Tries Ollama first (free, local), falls back to Claude API.

    Args:
        job_description: Full job description text.
        candidate_info: Legacy dict form — merged into resume_text if provided.
        title: Job title (optional, improves output).
        company: Company name (optional, improves output).
        location: Job location (optional).
        resume_text: Candidate resume as plain text.

    Returns:
        Generated cover letter text, or empty string if all providers fail.
    """
    # Support legacy dict-style call: generate_cover_letter(jd, {"resume": "..."})
    if candidate_info and not resume_text:
        resume_text = candidate_info.get("resume", candidate_info.get("resume_text", str(candidate_info)))

    if not resume_text:
        resume_text = "(No resume provided — write a generic cover letter based on the job description only)"

    prompt = _COVER_LETTER_PROMPT.format(
        resume_text=resume_text[:3000],
        title=title or "the position",
        company=company or "your company",
        location=location or "remote",
        job_description=job_description[:2000],
    )

    result = _ollama_generate(prompt)
    if result:
        logger.info("Cover letter generated via Ollama (%s)", OLLAMA_GENERATE_MODEL)
        return result

    result = _claude_generate(prompt)
    if result:
        logger.info("Cover letter generated via Claude fallback")
        return result

    logger.error("All cover letter generation providers failed")
    return ""
