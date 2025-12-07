"""Tests for background scheduler functionality."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.background_scheduler import BackgroundScheduler, get_scheduler


@pytest.fixture
def scheduler():
    """Create a fresh scheduler instance for each test."""
    scheduler = BackgroundScheduler()
    yield scheduler
    # Cleanup - stop scheduler if running
    if scheduler.is_running:
        scheduler.stop()


class TestBackgroundScheduler:
    """Tests for BackgroundScheduler class."""

    def test_scheduler_initialization(self, scheduler):
        """Test that scheduler initializes correctly."""
        assert scheduler.scheduler is not None
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler):
        """Test starting the scheduler."""
        scheduler.start(find_links_interval_minutes=60, cleanup_interval_hours=24)

        assert scheduler.is_running is True
        assert scheduler.scheduler.running is True

        # Check that jobs were scheduled
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 3  # find_direct_links, cleanup_hidden_jobs, auto_discover_jobs

        job_ids = [job.id for job in jobs]
        assert "find_direct_links" in job_ids
        assert "cleanup_hidden_jobs" in job_ids
        assert "auto_discover_jobs" in job_ids

        # Clean up
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_scheduler_already_running(self, scheduler, caplog):
        """Test that starting already running scheduler logs warning."""
        scheduler.start()
        scheduler.start()  # Try to start again

        assert "already running" in caplog.text.lower()

        # Clean up
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler):
        """Test stopping the scheduler."""
        scheduler.start()
        assert scheduler.is_running is True

        # Give time for scheduler to actually start
        await asyncio.sleep(0.1)

        scheduler.stop()
        assert scheduler.is_running is False
        # Note: scheduler.running may still be True right after shutdown call
        # so we just check is_running flag

    @pytest.mark.asyncio
    async def test_run_now_existing_job(self, scheduler):
        """Test manually triggering a job."""
        scheduler.start()

        # Mock the job modification
        job = scheduler.scheduler.get_job("find_direct_links")
        assert job is not None

        original_next_run = job.next_run_time
        scheduler.run_now("find_direct_links")

        # The next run time should be updated
        updated_job = scheduler.scheduler.get_job("find_direct_links")
        assert updated_job.next_run_time != original_next_run

        # Clean up
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_run_now_nonexistent_job(self, scheduler, caplog):
        """Test triggering a job that doesn't exist."""
        scheduler.start()
        scheduler.run_now("nonexistent_job")

        assert "not found" in caplog.text.lower()

        # Clean up
        scheduler.stop()


class TestSchedulerFunctions:
    """Tests for scheduler background functions."""

    @pytest.mark.asyncio
    async def test_find_direct_links_no_jobs(self, scheduler, caplog):
        """Test link discovery when no jobs need links."""
        with patch("app.job_tracker.JobTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.get_all_jobs.return_value = []
            mock_tracker_class.return_value = mock_tracker

            await scheduler.find_direct_links_for_tracked_jobs()

            assert "no jobs need direct link discovery" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_find_direct_links_with_jobs(self, scheduler):
        """Test link discovery for jobs needing links."""
        mock_jobs = [
            {
                "job_id": "test123",
                "title": "Python Engineer",
                "company": "Acme",
                "link": "https://indeed.com/job/123",
                "source": "JSearch",
            }
        ]

        with (
            patch("app.job_tracker.JobTracker") as mock_tracker_class,
            patch("app.link_finder.find_direct_link") as mock_find_link,
        ):
            mock_tracker = MagicMock()
            mock_tracker.get_all_jobs.return_value = mock_jobs
            mock_tracker_class.return_value = mock_tracker

            mock_find_link.return_value = {"direct_url": "https://acme.com/careers", "confidence": "high"}

            await scheduler.find_direct_links_for_tracked_jobs()

            mock_find_link.assert_called_once()
            mock_tracker.set_company_link.assert_called_once_with("test123", "https://acme.com/careers")

    @pytest.mark.asyncio
    async def test_find_direct_links_skips_company_jobs(self, scheduler):
        """Test that direct link discovery skips CompanyJobs source."""
        mock_jobs = [
            {
                "job_id": "test123",
                "title": "Python Engineer",
                "company": "Acme",
                "link": "https://acme.com/careers",
                "source": "CompanyJobs",
            }
        ]

        with (
            patch("app.job_tracker.JobTracker") as mock_tracker_class,
            patch("app.link_finder.find_direct_link") as mock_find_link,
        ):
            mock_tracker = MagicMock()
            mock_tracker.get_all_jobs.return_value = mock_jobs
            mock_tracker_class.return_value = mock_tracker

            await scheduler.find_direct_links_for_tracked_jobs()

            # Should not call find_direct_link for CompanyJobs
            mock_find_link.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_old_hidden_jobs(self, scheduler):
        """Test cleanup of old hidden jobs."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        mock_jobs = [
            {"job_id": "old_job", "status": "hidden", "last_updated": old_date},
            {"job_id": "recent_job", "status": "hidden", "last_updated": recent_date},
        ]

        with (
            patch("app.job_tracker.JobTracker") as mock_tracker_class,
            patch("app.job_tracker.STATUS_HIDDEN", "hidden"),
        ):
            mock_tracker = MagicMock()
            mock_tracker.get_all_jobs.return_value = mock_jobs
            mock_tracker.jobs = {"old_job": mock_jobs[0], "recent_job": mock_jobs[1]}
            mock_tracker_class.return_value = mock_tracker

            await scheduler.cleanup_old_hidden_jobs()

            # Old job should be removed, recent one should remain
            assert "old_job" not in mock_tracker.jobs
            assert "recent_job" in mock_tracker.jobs
            mock_tracker.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_no_old_jobs(self, scheduler, caplog):
        """Test cleanup when no old jobs exist."""
        with patch("app.job_tracker.JobTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.get_all_jobs.return_value = []
            mock_tracker_class.return_value = mock_tracker

            await scheduler.cleanup_old_hidden_jobs()

            assert "no old hidden jobs" in caplog.text.lower()
            mock_tracker.save.assert_not_called()


class TestSchedulerSingleton:
    """Tests for scheduler singleton pattern."""

    def test_get_scheduler_returns_singleton(self):
        """Test that get_scheduler returns the same instance."""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2

    def test_get_scheduler_creates_new_instance(self):
        """Test that first call creates a new scheduler."""
        from app.background_scheduler import reset_scheduler

        # Reset global state using public API
        reset_scheduler()

        scheduler = get_scheduler()
        assert isinstance(scheduler, BackgroundScheduler)
