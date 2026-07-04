"""Background job scheduler for periodic tasks.

This module handles background tasks that run when the container is idle:
- Finding direct links for tracked jobs
- Discovering new jobs from small companies
- Crawling company career pages
- Auto-updating job statuses
- Automated job discovery based on user's resume
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Resume file location (shared with UI server)
RESUME_FILE = Path("resume.txt")


class BackgroundScheduler:
    """Manages background tasks for job discovery and updates."""

    def __init__(self):
        """Initialize the background scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def find_direct_links_for_tracked_jobs(self):
        """Find direct links for all tracked jobs that don't have them."""
        from app.job_tracker import JobTracker
        from app.link_finder import find_direct_link

        logger.info("Starting direct link discovery for tracked jobs...")

        tracker = JobTracker()
        tracked_jobs = tracker.get_all_jobs(include_hidden=False)

        # Filter jobs that don't have a direct link yet and are from aggregators
        jobs_needing_links = [
            job for job in tracked_jobs if not job.get("company_link") and job.get("source") != "CompanyJobs"
        ]

        if not jobs_needing_links:
            logger.info("No jobs need direct link discovery")
            return

        logger.info(f"Finding direct links for {len(jobs_needing_links)} jobs")

        for job in jobs_needing_links:
            try:
                result = await find_direct_link(job, timeout=5)

                if result and result.get("direct_url"):
                    tracker.set_company_link(job["job_id"], result["direct_url"])
                    logger.info(
                        f"Found direct link for {job.get('title', 'Unknown')}: "
                        f"{result['direct_url']} ({result['confidence']} confidence)"
                    )
            except Exception as e:
                logger.error(f"Error finding link for {job.get('job_id')}: {e}")

            # Rate limiting - wait between requests
            await asyncio.sleep(2)

        logger.info("Completed direct link discovery")

    async def cleanup_old_hidden_jobs(self):
        """Remove hidden jobs older than 30 days to keep database clean."""
        from datetime import timedelta

        from app.job_tracker import STATUS_HIDDEN, JobTracker

        logger.info("Cleaning up old hidden jobs...")

        tracker = JobTracker()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        hidden_jobs = tracker.get_all_jobs(status_filter=[STATUS_HIDDEN], include_hidden=True)

        removed_count = 0
        for job in hidden_jobs:
            last_updated = job.get("last_updated", "")
            try:
                updated_date = datetime.fromisoformat(last_updated)
                if updated_date < cutoff_date:
                    job_id = job["job_id"]
                    # Remove from tracker
                    if job_id in tracker.jobs:
                        del tracker.jobs[job_id]
                        removed_count += 1
            except (ValueError, KeyError):
                continue

        if removed_count > 0:
            tracker.save()
            logger.info(f"Removed {removed_count} old hidden jobs")
        else:
            logger.info("No old hidden jobs to remove")

    async def discover_jobs_from_resume(self):
        """Automatically discover and track new jobs based on user's resume.

        This function:
        1. Reads the user's resume file
        2. Extracts key search terms (skills, job titles, domains) using AI
        3. Performs automated job searches
        4. Tracks new jobs automatically
        """
        logger.info("Starting automated job discovery from resume...")

        # Check if resume exists
        if not RESUME_FILE.exists():
            logger.info("No resume file found - skipping automated discovery")
            return

        try:
            # Read resume
            resume_text = RESUME_FILE.read_text(encoding="utf-8")
            if len(resume_text.strip()) < 100:
                logger.info("Resume too short - skipping automated discovery")
                return

            # Use configured queries first, fall back to Ollama extraction from resume
            search_queries = self._get_search_queries(resume_text)
            if not search_queries:
                logger.warning("No search queries available — set TARGET_SEARCH_QUERIES in .env")
                return

            logger.info(f"Using {len(search_queries)} search queries: {search_queries}")

            # Perform searches for each query
            from app.job_finder import generate_job_leads
            from app.job_tracker import JobTracker

            tracker = JobTracker()
            new_jobs_count = 0

            # Limit to top 3 queries to avoid rate limits
            for query in search_queries[:3]:
                try:
                    logger.info(f"Searching for: {query}")

                    # Search for jobs (5 per query, with evaluation)
                    jobs = generate_job_leads(
                        query=query, resume_text=resume_text, count=5, evaluate=True, use_mcp=True, verbose=False
                    )

                    # Track new jobs (score >= configured threshold)
                    min_score = int(os.getenv("AUTO_TRACK_MIN_SCORE", "65"))
                    for job in jobs:
                        score = job.get("score", 0)
                        if score >= min_score:
                            # Check if already tracked
                            job_id = self._generate_job_id(job)
                            if job_id not in tracker.jobs:
                                tracker.track_job(job)
                                new_jobs_count += 1
                                logger.info(
                                    f"Auto-tracked: {job.get('title')} at {job.get('company')} (score: {score})"
                                )

                    # Rate limiting between searches
                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Error searching for '{query}': {e}")
                    continue

            if new_jobs_count > 0:
                logger.info(f"Automated discovery complete: added {new_jobs_count} new jobs")
            else:
                logger.info("Automated discovery complete: no new high-scoring jobs found")

        except Exception as e:
            logger.error(f"Error in automated job discovery: {e}", exc_info=True)

    def _get_search_queries(self, resume_text: str) -> list[str]:
        """Return search queries from env config, falling back to Ollama extraction.

        Priority:
          1. TARGET_SEARCH_QUERIES env var (comma-separated) — deterministic, no LLM cost
          2. Ollama extraction from resume — free, local
          3. Hard-coded DevOps/Python defaults — always works
        """
        configured = os.getenv("TARGET_SEARCH_QUERIES", "").strip()
        if configured:
            queries = [q.strip() for q in configured.split(",") if q.strip()]
            logger.info(f"Using {len(queries)} configured search queries from TARGET_SEARCH_QUERIES")
            return queries

        # Try Ollama extraction
        ollama_queries = self._extract_queries_via_ollama(resume_text)
        if ollama_queries:
            return ollama_queries

        # Hard fallback
        logger.warning("Falling back to default search queries")
        return [
            "Sr DevOps Engineer remote",
            "CI/CD Engineer remote",
            "Sr Python Automation Engineer remote",
            "Platform Engineer Python Docker remote",
        ]

    def _extract_queries_via_ollama(self, resume_text: str) -> list[str]:
        """Extract job search queries from resume using local Ollama."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        prompt = (
            "Analyze this resume and return 4-6 job search queries as a JSON array.\n"
            "Each query should combine a job title and 'remote'.\n"
            "Focus on CI/CD, DevOps, Python automation, and platform engineering.\n\n"
            f"Resume:\n{resume_text[:2000]}\n\n"
            'Return ONLY a JSON array, e.g.: ["Sr DevOps Engineer remote", "CI/CD Engineer remote"]'
        )

        try:
            resp = httpx.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2, "num_predict": 256},
                },
                timeout=60,
            )
            if resp.status_code != 200:
                return []

            text = resp.json().get("response", "")
            start, end = text.find("["), text.rfind("]")
            if start == -1 or end == -1:
                return []

            queries = json.loads(text[start : end + 1])
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return [q.strip() for q in queries if len(q.strip()) > 3]
        except Exception as e:
            logger.warning(f"Ollama query extraction failed: {e}")
        return []

    async def _extract_search_queries_from_resume(self, resume_text: str) -> list[str]:
        """Deprecated: use _get_search_queries instead."""
        return self._get_search_queries(resume_text)

    def _generate_job_id(self, job: dict) -> str:
        """Generate a unique job ID (same logic as JobTracker)."""
        import hashlib

        link = job.get("link", "")
        if link:
            return hashlib.md5(link.encode()).hexdigest()[:16]

        # Fallback to title + company
        title = job.get("title", "")
        company = job.get("company", "")
        combined = f"{title}_{company}".lower()
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def start(
        self,
        find_links_interval_minutes: int = 60,
        cleanup_interval_hours: int = 24,
        auto_discover_interval_hours: int = 6,
    ):
        """Start the background scheduler.

        Args:
            find_links_interval_minutes: How often to search for direct links (default: hourly)
            cleanup_interval_hours: How often to cleanup old jobs (default: daily)
            auto_discover_interval_hours: How often to auto-discover jobs from resume (default: every 6 hours)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Schedule direct link discovery (hourly by default)
        self.scheduler.add_job(
            self.find_direct_links_for_tracked_jobs,
            trigger=IntervalTrigger(minutes=find_links_interval_minutes),
            id="find_direct_links",
            name="Find direct links for tracked jobs",
            replace_existing=True,
        )

        # Schedule cleanup (daily by default)
        self.scheduler.add_job(
            self.cleanup_old_hidden_jobs,
            trigger=IntervalTrigger(hours=cleanup_interval_hours),
            id="cleanup_hidden_jobs",
            name="Cleanup old hidden jobs",
            replace_existing=True,
        )

        # Schedule automated job discovery (every 6 hours by default)
        self.scheduler.add_job(
            self.discover_jobs_from_resume,
            trigger=IntervalTrigger(hours=auto_discover_interval_hours),
            id="auto_discover_jobs",
            name="Auto-discover jobs from resume",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        logger.info("Background scheduler started:")
        logger.info(f"  - Direct link discovery: every {find_links_interval_minutes} minutes")
        logger.info(f"  - Hidden job cleanup: every {cleanup_interval_hours} hours")
        logger.info(f"  - Automated job discovery: every {auto_discover_interval_hours} hours")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Background scheduler stopped")

    def run_now(self, job_id: str):
        """Manually trigger a background job immediately.

        Args:
            job_id: The job ID to run ('find_direct_links', 'cleanup_hidden_jobs', or 'auto_discover_jobs')
        """
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Triggered {job_id} to run immediately")
        else:
            logger.warning(f"Job {job_id} not found in scheduler")


# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get the global background scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def reset_scheduler() -> None:
    """Reset the global scheduler instance (primarily for testing)."""
    global _scheduler
    _scheduler = None
