"""Tests for direct link finder functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.link_finder import (
    CAREERS_PATHS,
    build_careers_urls,
    extract_company_website,
    find_direct_link,
    find_direct_links_batch,
    is_aggregator,
)


class TestAggregatorDetection:
    """Tests for aggregator domain detection."""

    def test_is_aggregator_indeed(self):
        """Test detection of Indeed URLs."""
        assert is_aggregator("https://www.indeed.com/viewjob?jk=123") is True
        assert is_aggregator("https://indeed.com/jobs/python") is True

    def test_is_aggregator_linkedin(self):
        """Test detection of LinkedIn URLs."""
        assert is_aggregator("https://www.linkedin.com/jobs/view/123") is True
        assert is_aggregator("https://linkedin.com/jobs") is True

    def test_is_not_aggregator(self):
        """Test that direct company URLs are not flagged as aggregators."""
        assert is_aggregator("https://acme.com/careers") is False
        assert is_aggregator("https://example.com/jobs") is False

    def test_is_aggregator_invalid_url(self):
        """Test handling of invalid URLs."""
        assert is_aggregator("not-a-url") is False
        assert is_aggregator("") is False


class TestCompanyWebsiteExtraction:
    """Tests for company website extraction."""

    def test_extract_from_company_url_field(self):
        """Test extraction from direct company_url field."""
        job = {"company_url": "https://acme.com"}
        assert extract_company_website(job) == "https://acme.com"

    def test_extract_from_extensions(self):
        """Test extraction from extensions array."""
        job = {"extensions": ["Remote", "https://company.com", "Full-time"]}
        assert extract_company_website(job) == "https://company.com"

    def test_extract_skips_aggregators_in_extensions(self):
        """Test that aggregator URLs in extensions are skipped."""
        job = {"extensions": ["https://indeed.com/apply", "https://company.com"]}
        assert extract_company_website(job) == "https://company.com"

    def test_extract_no_website(self):
        """Test when no company website is found."""
        job = {"title": "Engineer", "company": "Acme"}
        assert extract_company_website(job) is None

    def test_extract_empty_extensions(self):
        """Test with empty extensions."""
        job = {"extensions": []}
        assert extract_company_website(job) is None


class TestCareersURLBuilder:
    """Tests for careers URL generation."""

    def test_build_careers_urls(self):
        """Test generating careers page URLs."""
        urls = build_careers_urls("https://acme.com")

        # Should include the base URL first
        assert urls[0] == "https://acme.com"

        # Should include common careers paths
        assert "https://acme.com/careers" in urls
        assert "https://acme.com/jobs" in urls
        assert "https://acme.com/join-us" in urls

        # Should have correct number of URLs (1 base + all paths)
        assert len(urls) == len(CAREERS_PATHS) + 1

    def test_build_careers_urls_with_path(self):
        """Test URL generation when given a full path."""
        urls = build_careers_urls("https://acme.com/some/path")

        # First URL should be the original (could be a specific page)
        assert urls[0] == "https://acme.com/some/path"
        # Other URLs should use base domain with careers paths
        assert "https://acme.com/careers" in urls

    def test_build_careers_urls_invalid(self):
        """Test handling of invalid URLs."""
        urls = build_careers_urls("not-a-url")
        assert urls == []


class TestFindDirectLink:
    """Tests for direct link finding."""

    @pytest.mark.asyncio
    async def test_find_direct_link_already_direct(self):
        """Test that direct links are returned as-is."""
        job = {"link": "https://acme.com/careers/123", "company": "Acme", "title": "Engineer"}

        result = await find_direct_link(job)

        assert result is not None
        assert result["direct_url"] == "https://acme.com/careers/123"
        assert result["source"] == "direct"
        assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_find_direct_link_no_company_website(self):
        """Test when no company website can be extracted."""
        job = {"link": "https://indeed.com/job/123", "company": "Acme", "title": "Engineer"}

        result = await find_direct_link(job)

        # Should return None when no company website is found
        assert result is None

    @pytest.mark.asyncio
    async def test_find_direct_link_careers_page_found(self):
        """Test successful careers page discovery."""
        job = {
            "link": "https://indeed.com/job/123",
            "company": "Acme",
            "title": "Engineer",
            "company_url": "https://acme.com",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Careers at Acme</h1><p>Join our team</p></body></html>"

        with patch("httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None
            mock_async_client.get.return_value = mock_response
            mock_client.return_value = mock_async_client

            result = await find_direct_link(job)

            assert result is not None
            assert "acme.com" in result["direct_url"]
            assert result["source"] in ["careers_page", "company_homepage"]

    @pytest.mark.asyncio
    async def test_find_direct_link_fallback_to_homepage(self):
        """Test fallback to company homepage when no careers page found."""
        job = {
            "link": "https://indeed.com/job/123",
            "company": "Acme",
            "title": "Engineer",
            "company_url": "https://acme.com",
        }

        mock_response = MagicMock()
        mock_response.status_code = 404  # All careers pages return 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None
            mock_async_client.get.return_value = mock_response
            mock_client.return_value = mock_async_client

            result = await find_direct_link(job)

            assert result is not None
            assert result["direct_url"] == "https://acme.com"
            assert result["source"] == "company_homepage"
            assert result["confidence"] == "low"

    @pytest.mark.asyncio
    async def test_find_direct_link_timeout(self):
        """Test that timeout is respected."""
        job = {
            "link": "https://indeed.com/job/123",
            "company": "Acme",
            "title": "Engineer",
            "company_url": "https://acme.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Verify timeout is passed
            await find_direct_link(job, timeout=5)
            mock_client.assert_called_once_with(timeout=5, follow_redirects=True)


class TestFindDirectLinksBatch:
    """Tests for batch direct link finding."""

    @pytest.mark.asyncio
    async def test_find_direct_links_batch_single_job(self):
        """Test batch processing with a single job."""
        jobs = [{"link": "https://acme.com/job", "company": "Acme", "title": "Engineer"}]

        with patch("app.link_finder.find_direct_link") as mock_find:
            mock_find.return_value = {"direct_url": "https://acme.com/job", "source": "direct", "confidence": "high"}

            results = await find_direct_links_batch(jobs)

            assert len(results) == 1
            mock_find.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_direct_links_batch_multiple_jobs(self):
        """Test batch processing with multiple jobs."""
        jobs = [
            {"link": "https://acme.com/job1", "company": "Acme", "title": "Engineer 1"},
            {"link": "https://example.com/job2", "company": "Example", "title": "Engineer 2"},
            {"link": "https://test.com/job3", "company": "Test", "title": "Engineer 3"},
        ]

        with patch("app.link_finder.find_direct_link") as mock_find:
            mock_find.return_value = {"direct_url": "test", "source": "direct", "confidence": "high"}

            results = await find_direct_links_batch(jobs)

            assert len(results) == 3
            assert mock_find.call_count == 3

    @pytest.mark.asyncio
    async def test_find_direct_links_batch_with_errors(self):
        """Test batch processing with some jobs failing."""
        jobs = [
            {"link": "https://acme.com/job1", "company": "Acme", "title": "Engineer 1"},
            {"link": "https://example.com/job2", "company": "Example", "title": "Engineer 2"},
        ]

        async def mock_find(job):
            if "acme" in job["link"]:
                raise Exception("Network error")
            return {"direct_url": job["link"], "source": "direct", "confidence": "high"}

        with patch("app.link_finder.find_direct_link", side_effect=mock_find):
            results = await find_direct_links_batch(jobs)

            # Should still return results for all jobs
            assert len(results) == 2

            # First job should have None due to error
            job1_id = list(results.keys())[0]
            assert results[job1_id] is None

    @pytest.mark.asyncio
    async def test_find_direct_links_batch_concurrency_limit(self):
        """Test that concurrency is limited."""
        jobs = [{"link": f"https://job{i}.com", "company": f"Company{i}", "title": f"Job{i}"} for i in range(10)]

        call_times = []

        async def mock_find(job):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)
            return {"direct_url": job["link"], "source": "direct", "confidence": "high"}

        with patch("app.link_finder.find_direct_link", side_effect=mock_find):
            results = await find_direct_links_batch(jobs, max_concurrent=3)

            # All jobs should have results
            assert len(results) == 10
