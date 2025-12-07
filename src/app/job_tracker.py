"""Job tracking and status management.

Tracks job applications through the pipeline: New → Applied → Interviewing → Rejected/Offer
Also supports hiding unwanted jobs to prevent them from appearing in search results.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Job statuses
STATUS_NEW = "new"
STATUS_APPLIED = "applied"
STATUS_INTERVIEWING = "interviewing"
STATUS_REJECTED = "rejected"
STATUS_OFFER = "offer"
STATUS_HIDDEN = "hidden"

VALID_STATUSES = {STATUS_NEW, STATUS_APPLIED, STATUS_INTERVIEWING, STATUS_REJECTED, STATUS_OFFER, STATUS_HIDDEN}

# Persistence file - use absolute path in shared volume if available, else current dir
_DATA_DIR = Path("/app/data") if Path("/app/data").exists() else Path(".")
TRACKING_FILE = _DATA_DIR / "job_tracking.json"


def generate_job_id(job: Dict[str, Any]) -> str:
    """Generate a unique ID for a job based on title, company, and link.

    This allows us to track the same job across multiple searches.
    """
    # Use link as primary identifier (most unique)
    link = job.get("link", "")
    if link:
        # Hash the link to create a stable ID
        return hashlib.sha256(link.encode()).hexdigest()[:16]

    # Fallback: use title + company combination
    title = job.get("title", "").lower().strip()
    company = job.get("company", "").lower().strip()
    key = f"{company}::{title}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class JobTracker:
    """Manage job tracking and status updates."""

    def __init__(self, tracking_file: Path = TRACKING_FILE):
        self.tracking_file = tracking_file
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load job tracking data from file."""
        if not self.tracking_file.exists():
            self.jobs = {}
            return

        try:
            with open(self.tracking_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.jobs = data.get("jobs", {})
        except Exception as e:
            print(f"job_tracker: Failed to load {self.tracking_file}: {e}")
            self.jobs = {}

    def save(self) -> None:
        """Save job tracking data to file."""
        try:
            data = {"jobs": self.jobs, "last_updated": datetime.now(timezone.utc).isoformat()}
            with open(self.tracking_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"job_tracker: Failed to save {self.tracking_file}: {e}")

    def track_job(self, job: Dict[str, Any], status: str = STATUS_NEW) -> str:
        """Add a job to tracking or update existing entry.

        Returns the job_id.
        """
        job_id = generate_job_id(job)

        # If job already exists, preserve certain fields
        if job_id in self.jobs:
            existing = self.jobs[job_id]
            # Preserve user data
            notes = existing.get("notes", "")
            company_link = existing.get("company_link")
            applied_date = existing.get("applied_date")
            current_status = existing.get("status", STATUS_NEW)
        else:
            notes = ""
            company_link = None
            applied_date = None
            current_status = status

        # Update job data
        self.jobs[job_id] = {
            "job_id": job_id,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "summary": job.get("summary", ""),
            "link": job.get("link", ""),
            "source": job.get("source", ""),
            "status": current_status,
            "notes": notes,
            "company_link": company_link,  # Direct company career page link
            "applied_date": applied_date,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "first_seen": existing.get("first_seen") if job_id in self.jobs else datetime.now(timezone.utc).isoformat(),
        }

        self.save()
        return job_id

    def update_status(self, job_id: str, status: str, notes: str | None = None) -> bool:
        """Update job status and optionally add notes.

        Returns True if successful, False if job not found or invalid status.
        """
        if status not in VALID_STATUSES:
            print(f"job_tracker: Invalid status '{status}'")
            return False

        if job_id not in self.jobs:
            print(f"job_tracker: Job {job_id} not found")
            return False

        self.jobs[job_id]["status"] = status
        self.jobs[job_id]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Set applied_date when status changes to 'applied'
        if status == STATUS_APPLIED and not self.jobs[job_id].get("applied_date"):
            self.jobs[job_id]["applied_date"] = datetime.now(timezone.utc).isoformat()

        # Update notes if provided
        if notes is not None:
            self.jobs[job_id]["notes"] = notes

        self.save()
        return True

    def update_notes(self, job_id: str, notes: str) -> bool:
        """Update notes for a job.

        Returns True if successful, False if job not found.
        """
        if job_id not in self.jobs:
            print(f"job_tracker: Job {job_id} not found")
            return False

        self.jobs[job_id]["notes"] = notes
        self.jobs[job_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.save()
        return True

    def hide_job(self, job_id: str) -> bool:
        """Mark job as hidden (won't appear in search results)."""
        return self.update_status(job_id, STATUS_HIDDEN)

    def set_company_link(self, job_id: str, company_link: str) -> bool:
        """Set the direct company career page link for a job."""
        if job_id not in self.jobs:
            return False

        self.jobs[job_id]["company_link"] = company_link
        self.jobs[job_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.save()
        return True

    def get_job(self, job_id: str) -> Dict[str, Any] | None:
        """Get job data by ID."""
        return self.jobs.get(job_id)

    def get_all_jobs(
        self, status_filter: List[str] | None = None, include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all tracked jobs, optionally filtered by status.

        Args:
            status_filter: List of statuses to include. If None, include all.
            include_hidden: If False, exclude hidden jobs.

        Returns:
            List of job dicts sorted by last_updated (most recent first).
        """
        jobs = []
        for job_data in self.jobs.values():
            status = job_data.get("status", STATUS_NEW)

            # Filter by status
            if status_filter and status not in status_filter:
                continue

            # Exclude hidden unless explicitly requested
            if not include_hidden and status == STATUS_HIDDEN:
                continue

            jobs.append(job_data)

        # Sort by last_updated (most recent first)
        jobs.sort(key=lambda j: j.get("last_updated", ""), reverse=True)
        return jobs

    def get_hidden_job_ids(self) -> set:
        """Get set of all hidden job IDs for filtering search results."""
        return {job_id for job_id, data in self.jobs.items() if data.get("status") == STATUS_HIDDEN}

    def get_tracked_links(self) -> set:
        """Get set of all tracked job links (excluding hidden).

        Used to identify if a job from search results is already tracked.
        """
        links = set()
        for job_data in self.jobs.values():
            if job_data.get("status") != STATUS_HIDDEN:
                link = job_data.get("link")
                if link:
                    links.add(link)
        return links

    def is_job_hidden(self, job: Dict[str, Any]) -> bool:
        """Check if a job is hidden based on its link or title+company."""
        job_id = generate_job_id(job)
        return job_id in self.get_hidden_job_ids()

    def clear_all_jobs(self) -> None:
        """Clear all tracked jobs from the database."""
        self.jobs = {}
        self.save()


# Global tracker instance
_tracker: JobTracker | None = None


def get_tracker() -> JobTracker:
    """Get global job tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = JobTracker()
    return _tracker
