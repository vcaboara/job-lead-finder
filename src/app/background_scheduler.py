"""Background job scheduler for periodic tasks.

This module handles background tasks that run when the container is idle:
- Finding direct links for tracked jobs
- Discovering new jobs from small companies
- Crawling company career pages
- Auto-updating job statuses
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


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

    def start(self, find_links_interval_minutes: int = 60, cleanup_interval_hours: int = 24):
        """Start the background scheduler.

        Args:
            find_links_interval_minutes: How often to search for direct links (default: hourly)
            cleanup_interval_hours: How often to cleanup old jobs (default: daily)
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

        self.scheduler.start()
        self.is_running = True

        logger.info("Background scheduler started:")
        logger.info(f"  - Direct link discovery: every {find_links_interval_minutes} minutes")
        logger.info(f"  - Hidden job cleanup: every {cleanup_interval_hours} hours")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Background scheduler stopped")

    def run_now(self, job_id: str):
        """Manually trigger a background job immediately.

        Args:
            job_id: The job ID to run ('find_direct_links' or 'cleanup_hidden_jobs')
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
