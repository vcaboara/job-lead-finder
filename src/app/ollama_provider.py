"""Ollama local LLM provider for job evaluation.

This provider runs models locally via Ollama for resume matching and job scoring.
No API keys or quotas - completely free and private.

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: `ollama pull llama3.2:3b`
    3. Set OLLAMA_MODEL env var (optional, defaults to llama3.2:3b)
    4. Ollama server runs on http://localhost:11434 by default
"""

import json
import logging
import os
import time
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Ollama local LLM provider for job evaluation.

    Runs models locally with no API costs or quotas.
    Recommended models:
        - llama3.2:3b (2GB VRAM, fast, good quality)
        - qwen2.5:7b (4GB VRAM, better quality)
        - llama3.1:8b (5GB VRAM, best balance)
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        request_timeout: int = 90
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2:3b)
            request_timeout: Request timeout in seconds (default: 90)
        """
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.request_timeout = request_timeout

        # Don't fail initialization if Ollama not running - check in is_available() instead

    def _check_connection(self) -> bool:
        """Check if Ollama server is accessible.

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def evaluate(self, job: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
        """Evaluate a job using Ollama.

        Args:
            job: Job dictionary with title, company, description, etc.
            resume_text: Candidate's resume text

        Returns:
            Dict with 'score' (0-100) and 'reasoning'
        """
        prompt = (
            "You are a career advisor. Evaluate this job-candidate match and respond with ONLY valid JSON.\n\n"
            f"CANDIDATE RESUME:\n{resume_text[:1500]}\n\n"
            f"JOB: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}\n"
            f"Description: {job.get('description', job.get('summary', ''))[:500]}\n\n"
            "Scoring criteria (0-100 total):\n"
            "- Skills match (40pts): Required technical skills the candidate has\n"
            "- Experience level (25pts): Junior/Mid/Senior alignment\n"
            "- Domain knowledge (20pts): Industry experience\n"
            "- Role fit (15pts): Career trajectory match\n\n"
            "CRITICAL: Respond with ONLY this exact JSON format, nothing else:\n"
            '{"score": 75, "reasoning": "Python, AWS, Docker match. Senior level fits. Missing Kubernetes."}\n\n'
            "Your JSON response:"
        )

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Request JSON format output
                    "options": {
                        "temperature": 0.2,  # Lower temperature for more consistent scoring
                        "num_predict": 256   # Shorter responses for JSON
                    }
                },
                timeout=self.request_timeout
            )

            if response.status_code != 200:
                return {
                    "score": 0,
                    "reasoning": f"Ollama error: HTTP {response.status_code}"
                }

            result = response.json()
            text = result.get("response", "")

            # Parse JSON from response
            return self._parse_json_response(text)

        except httpx.TimeoutException:
            return {
                "score": 0,
                "reasoning": f"Ollama timeout after {self.request_timeout}s"
            }
        except Exception as e:
            return {
                "score": 0,
                "reasoning": f"Ollama error: {str(e)}"
            }

    def batch_evaluate(
        self,
        jobs: list[Dict[str, Any]],
        resume_text: str,
        verbose: bool = False
    ) -> list[Dict[str, Any]]:
        """Evaluate multiple jobs in batch.

        Args:
            jobs: List of job dictionaries
            resume_text: Candidate's resume text
            verbose: Print progress if True

        Returns:
            List of jobs with 'score' and 'reasoning' added
        """
        if verbose:
            print(f"Evaluating {len(jobs)} jobs with Ollama ({self.model})...")

        start_time = time.time()
        scored_jobs = []

        for i, job in enumerate(jobs):
            if verbose and i > 0 and i % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = avg_time * (len(jobs) - i)
                print(
                    f"  Progress: {i}/{len(jobs)} jobs ({elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining)")

            result = self.evaluate(job, resume_text)
            job_with_score = {**job, **result}
            scored_jobs.append(job_with_score)

        if verbose:
            elapsed = time.time() - start_time
            print(
                f"Batch evaluation complete: {len(jobs)} jobs in {elapsed:.1f}s ({elapsed/len(jobs):.2f}s/job)")

        return scored_jobs

    def rank_jobs_batch(
        self,
        jobs: list[Dict[str, Any]],
        resume_text: str,
        top_n: int = 10
    ) -> list[Dict[str, Any]]:
        """Rank jobs and return top N with scores (compatible with GeminiProvider API).

        Args:
            jobs: List of job dictionaries
            resume_text: Candidate's resume text
            top_n: Number of top jobs to return

        Returns:
            Top N jobs sorted by score descending with 'score' and 'reasoning' added
        """
        logger.info(
            f"Ranking {len(jobs)} jobs with Ollama, returning top {top_n}")

        # Evaluate all jobs
        scored_jobs = self.batch_evaluate(jobs, resume_text, verbose=False)

        # Sort by score descending
        scored_jobs.sort(key=lambda j: j.get("score", 0), reverse=True)

        # Return top N
        result = scored_jobs[:top_n]
        logger.info(
            f"Ollama ranking complete: top score={result[0].get('score', 0) if result else 0}")

        return result

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from Ollama response text.

        Ollama responses may include extra text before/after JSON.
        This extracts the JSON object.
        """
        # Try to find JSON object in response
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            return {
                "score": 0,
                "reasoning": "Could not parse JSON from Ollama response"
            }

        json_str = text[start_idx:end_idx]

        try:
            data = json.loads(json_str)

            # Validate score is in range
            score = int(data.get("score", 0))
            score = max(0, min(100, score))  # Clamp to 0-100

            return {
                "score": score,
                "reasoning": data.get("reasoning", "No reasoning provided")
            }
        except (json.JSONDecodeError, ValueError, KeyError):
            return {
                "score": 0,
                "reasoning": f"Invalid JSON response from Ollama: {json_str[:100]}"
            }

    def is_available(self) -> bool:
        """Check if Ollama is available and model is pulled."""
        logger.debug(f"Checking Ollama availability at {self.base_url}")

        if not self._check_connection():
            logger.warning(f"Cannot connect to Ollama at {self.base_url}")
            return False

        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.warning(
                    f"Ollama server returned status {response.status_code}")
                return False

            tags = response.json()
            models = [m.get("name", "") for m in tags.get("models", [])]

            # Check if our model is available
            available = any(self.model in m for m in models)
            if available:
                logger.info(f"Ollama is available with model {self.model}")
            else:
                logger.warning(
                    f"Model {self.model} not found. Available models: {models}")
            return available
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False


def simple_ollama_query(prompt: str, model: str | None = None) -> str:
    """Simple helper for one-off Ollama queries.

    Args:
        prompt: Text prompt to send to Ollama
        model: Model name (default: llama3.2:3b)

    Returns:
        Generated text response
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        if response.status_code != 200:
            return ""

        result = response.json()
        return result.get("response", "")
    except Exception:
        return ""
