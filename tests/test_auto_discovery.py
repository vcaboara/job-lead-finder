"""Tests for automated job discovery from resume."""

from unittest.mock import patch

import pytest

from app.background_scheduler import BackgroundScheduler


@pytest.fixture
def scheduler():
    """Create a test scheduler instance."""
    return BackgroundScheduler()


@pytest.fixture
def mock_resume(tmp_path):
    """Create a temporary resume file."""
    resume_file = tmp_path / "resume.txt"
    resume_content = """
John Doe
Senior Software Engineer

EXPERIENCE:
- 5+ years of Python development
- Django and FastAPI frameworks
- PostgreSQL, Redis, Docker
- AWS cloud infrastructure
- CI/CD with GitHub Actions

SKILLS:
- Languages: Python, JavaScript, SQL
- Frameworks: Django, FastAPI, React
- Tools: Docker, Kubernetes, Git
- Cloud: AWS (EC2, S3, Lambda)
"""
    resume_file.write_text(resume_content)
    return resume_file


class TestAutoDiscovery:
    """Test automated job discovery functionality."""

    @pytest.mark.asyncio
    async def test_extract_search_queries_from_resume(self, scheduler, mock_resume):
        """Test that search queries can be extracted from resume."""
        resume_text = mock_resume.read_text()

        with patch("app.gemini_provider.GeminiProvider") as MockProvider:
            mock_provider = MockProvider.return_value
            mock_provider.call_llm.return_value = (
                '["Senior Python Engineer", "Python Backend Developer", "Senior Software Engineer Python"]'
            )

            queries = await scheduler._extract_search_queries_from_resume(resume_text)

            assert len(queries) == 3
            assert "Senior Python Engineer" in queries
            assert all(isinstance(q, str) for q in queries)
            mock_provider.call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_search_queries_handles_invalid_json(self, scheduler):
        """Test handling of invalid JSON response from AI."""
        with patch("app.gemini_provider.GeminiProvider") as MockProvider:
            mock_provider = MockProvider.return_value
            mock_provider.call_llm.return_value = "This is not JSON"

            queries = await scheduler._extract_search_queries_from_resume("Sample resume text")

            assert queries == []

    @pytest.mark.asyncio
    async def test_discover_jobs_skips_if_no_resume(self, scheduler, tmp_path):
        """Test that discovery is skipped if resume file doesn't exist."""
        with patch("app.background_scheduler.RESUME_FILE", tmp_path / "nonexistent.txt"):
            # Should return early without errors
            await scheduler.discover_jobs_from_resume()
            # No exception means test passes

    @pytest.mark.asyncio
    async def test_discover_jobs_skips_short_resume(self, scheduler, tmp_path):
        """Test that discovery is skipped if resume is too short."""
        short_resume = tmp_path / "short.txt"
        short_resume.write_text("Too short")

        with patch("app.background_scheduler.RESUME_FILE", short_resume):
            await scheduler.discover_jobs_from_resume()
            # Should complete without errors

    @pytest.mark.asyncio
    async def test_discover_jobs_full_workflow(self, scheduler, mock_resume):
        """Test complete auto-discovery workflow."""
        with patch("app.background_scheduler.RESUME_FILE", mock_resume):
            with patch("app.gemini_provider.GeminiProvider") as MockProvider:
                mock_provider = MockProvider.return_value
                mock_provider.call_llm.return_value = '["Python Developer", "Django Engineer"]'

                with patch("app.job_finder.generate_job_leads") as mock_search:
                    # Mock job search results
                    mock_search.return_value = [
                        {
                            "title": "Senior Python Developer",
                            "company": "TechCorp",
                            "link": "https://example.com/job1",
                            "location": "Remote",
                            "summary": "Great job",
                            "score": 85,
                        },
                        {
                            "title": "Python Engineer",
                            "company": "StartupCo",
                            "link": "https://example.com/job2",
                            "location": "NYC",
                            "summary": "Another job",
                            "score": 70,
                        },
                        {
                            "title": "Junior Python Dev",
                            "company": "MegaCorp",
                            "link": "https://example.com/job3",
                            "location": "SF",
                            "summary": "Low score",
                            "score": 45,  # Below threshold
                        },
                    ]

                    with patch("app.job_tracker.JobTracker") as MockTracker:
                        mock_tracker = MockTracker.return_value
                        mock_tracker.jobs = {}

                        await scheduler.discover_jobs_from_resume()

                        # Should search for extracted queries
                        assert mock_search.call_count == 2  # Two queries

                        # Should track high-scoring jobs only
                        assert mock_tracker.track.call_count == 4  # 2 queries × 2 jobs each (score >= 60)

    def test_generate_job_id(self, scheduler):
        """Test job ID generation."""
        job_with_link = {
            "title": "Test Job",
            "company": "Test Co",
            "link": "https://example.com/job",
        }

        job_without_link = {
            "title": "Test Job",
            "company": "Test Co",
        }

        # IDs should be consistent
        id1 = scheduler._generate_job_id(job_with_link)
        id2 = scheduler._generate_job_id(job_with_link)
        assert id1 == id2

        # Different jobs should have different IDs
        id3 = scheduler._generate_job_id(job_without_link)
        assert id1 != id3

        # IDs should be 16 chars
        assert len(id1) == 16


class TestSchedulerConfiguration:
    """Test scheduler configuration and job scheduling."""

    @pytest.mark.asyncio
    async def test_scheduler_adds_auto_discovery_job(self):
        """Test that scheduler adds auto-discovery job when started."""
        scheduler = BackgroundScheduler()

        scheduler.start(
            find_links_interval_minutes=60,
            cleanup_interval_hours=24,
            auto_discover_interval_hours=6,
        )

        try:
            # Check that auto-discovery job is scheduled
            job = scheduler.scheduler.get_job("auto_discover_jobs")
            assert job is not None
            assert job.name == "Auto-discover jobs from resume"
        finally:
            scheduler.stop()

    @pytest.mark.asyncio
    async def test_run_now_triggers_auto_discovery(self):
        """Test that run_now can trigger auto-discovery immediately."""
        scheduler = BackgroundScheduler()

        scheduler.start(auto_discover_interval_hours=999)  # Long interval

        try:
            job = scheduler.scheduler.get_job("auto_discover_jobs")
            original_next_run = job.next_run_time

            # Trigger to run now
            scheduler.run_now("auto_discover_jobs")

            # Next run time should be updated
            updated_job = scheduler.scheduler.get_job("auto_discover_jobs")
            assert updated_job.next_run_time != original_next_run
        finally:
            scheduler.stop()
