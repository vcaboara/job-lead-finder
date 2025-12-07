"""Tests for MCP providers module."""

from unittest.mock import Mock, patch

from app.mcp_providers import (
    GitHubJobsMCP,
    IndeedMCP,
    LinkedInMCP,
    MCPAggregator,
    MCPProvider,
    WeWorkRemotelyMCP,
    generate_job_leads_via_mcp,
)


class TestMCPProviders:
    """Test MCP provider classes."""

    def test_linkedin_mcp_initialization(self):
        """Test LinkedInMCP initializes correctly."""
        mcp = LinkedInMCP()
        assert mcp.name == "LinkedIn"
        assert mcp.enabled is True
        assert "localhost:3000" in mcp.mcp_server_url

    def test_indeed_mcp_initialization(self):
        """Test IndeedMCP initializes correctly."""
        mcp = IndeedMCP()
        assert mcp.name == "Indeed"
        assert mcp.enabled is True
        assert "localhost:3001" in mcp.mcp_server_url

    def test_github_mcp_initialization(self):
        """Test GitHubJobsMCP initializes correctly."""
        mcp = GitHubJobsMCP()
        assert mcp.name == "GitHub"
        assert mcp.enabled is True
        # GitHub MCP uses GitHub API, not HTTP server
        assert hasattr(mcp, "github_token")

    @patch("httpx.get")
    def test_is_available_success(self, mock_get):
        """Test is_available returns True when MCP is healthy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        mcp = LinkedInMCP()
        assert mcp.is_available() is True

    @patch("httpx.get")
    def test_is_available_failure(self, mock_get):
        """Test is_available returns False when MCP is down."""
        mock_get.side_effect = Exception("Connection refused")

        mcp = LinkedInMCP()
        assert mcp.is_available() is False

    @patch("httpx.post")
    @patch("app.mcp_providers.LinkedInMCP.is_available")
    def test_search_jobs_success(self, mock_available, mock_post):
        """Test search_jobs returns normalized job data."""
        mock_available.return_value = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jobs": [
                {
                    "title": "Python Developer",
                    "company": "TechCorp",
                    "location": "Remote",
                    "description": "Build amazing things with Python",
                    "url": "https://linkedin.com/jobs/123",
                }
            ]
        }
        mock_post.return_value = mock_response

        mcp = LinkedInMCP()
        jobs = mcp.search_jobs("python developer", count=5)

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Python Developer"
        assert jobs[0]["company"] == "TechCorp"
        assert jobs[0]["source"] == "LinkedIn"
        assert jobs[0]["link"] == "https://linkedin.com/jobs/123"

    @patch("app.mcp_providers.LinkedInMCP.is_available")
    def test_search_jobs_unavailable(self, mock_available):
        """Test search_jobs returns empty list when MCP unavailable."""
        mock_available.return_value = False

        mcp = LinkedInMCP()
        jobs = mcp.search_jobs("python developer", count=5)

        assert jobs == []

    @patch("httpx.post")
    @patch("app.mcp_providers.LinkedInMCP.is_available")
    def test_search_jobs_api_error(self, mock_available, mock_post):
        """Test search_jobs handles API errors gracefully."""
        mock_available.return_value = True
        mock_post.side_effect = Exception("API Error")

        mcp = LinkedInMCP()
        jobs = mcp.search_jobs("python developer", count=5)

        assert jobs == []


class TestMCPAggregator:
    """Test MCPAggregator class."""

    @patch("app.config_manager.load_config")
    def test_aggregator_initialization(self, mock_load_config):
        """Test MCPAggregator initialization with default providers."""
        # Mock config with CompanyJobs disabled, RemoteOK and Remotive enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": False},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
            }
        }

        agg = MCPAggregator()
        # CompanyJobs disabled by default (slow), RemoteOK and Remotive enabled
        assert len(agg.providers) == 2  # RemoteOK and Remotive
        assert not any(p.name == "CompanyJobs" for p in agg.providers)  # Disabled by default
        assert any(p.name == "RemoteOK" for p in agg.providers)
        assert any(p.name == "Remotive" for p in agg.providers)

    def test_aggregator_custom_providers(self):
        """Test MCPAggregator with custom provider list."""
        mock_provider = Mock()
        mock_provider.name = "Custom"
        mock_provider.enabled = True

        agg = MCPAggregator(providers=[mock_provider])
        assert len(agg.providers) == 1
        assert agg.providers[0].name == "Custom"

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_get_available_providers(self, mock_load_config, mock_remoteok, mock_remotive, mock_companyjobs):
        """Test get_available_providers filters correctly."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
            }
        }

        # Only Remotive is available (others mocked as unavailable)
        mock_remotive.return_value = True
        mock_remoteok.return_value = False
        mock_companyjobs.return_value = False

        agg = MCPAggregator()
        available = agg.get_available_providers()

        assert len(available) == 1  # Only Remotive is available (others mocked as unavailable)
        assert any(p.name == "Remotive" for p in available)

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.search_jobs")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_search_jobs_aggregation(
        self, mock_load_config, mock_remoteok_avail, mock_remotive_avail, mock_search, mock_companyjobs_avail
    ):
        """Test search_jobs aggregates from multiple providers."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
            }
        }

        # Only Remotive available (CompanyJobs and RemoteOK mocked unavailable)
        mock_remotive_avail.return_value = True
        mock_remoteok_avail.return_value = False
        mock_companyjobs_avail.return_value = False

        mock_search.return_value = [
            {
                "title": "Job 1",
                "company": "Company A",
                "location": "Remote",
                "summary": "Test",
                "link": "https://example.com/1",
                "source": "Remotive",
            },
            {
                "title": "Job 2",
                "company": "Company B",
                "location": "NYC",
                "summary": "Test",
                "link": "https://example.com/2",
                "source": "Remotive",
            },
        ]

        agg = MCPAggregator()
        jobs = agg.search_jobs("python developer", count_per_provider=5)

        assert len(jobs) == 2
        assert jobs[0]["title"] == "Job 1"
        assert jobs[1]["title"] == "Job 2"

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.search_jobs")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_deduplication(
        self, mock_load_config, mock_remotive_avail, mock_remoteok_avail, mock_search, mock_companyjobs_avail
    ):
        """Test deduplication removes duplicate job links."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
            }
        }

        # Only RemoteOK available (Remotive and CompanyJobs unavailable)
        mock_remoteok_avail.return_value = True
        mock_remotive_avail.return_value = False
        mock_companyjobs_avail.return_value = False

        # Return duplicate jobs
        mock_search.return_value = [
            {
                "title": "Job 1",
                "company": "Company A",
                "location": "Remote",
                "summary": "Test",
                "link": "https://example.com/1",
                "source": "RemoteOK",
            },
            {
                "title": "Job 1 Duplicate",
                "company": "Company A",
                "location": "Remote",
                "summary": "Test duplicate",
                "link": "https://example.com/1",  # Same link
                "source": "RemoteOK",
            },
        ]

        agg = MCPAggregator()
        jobs = agg.search_jobs("python developer", count_per_provider=5)

        # Should deduplicate
        assert len(jobs) == 1
        assert jobs[0]["link"] == "https://example.com/1"

    @patch("app.mcp_providers.WeWorkRemotelyMCP.is_available")
    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.LinkedInMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    def test_no_providers_available(self, mock_remoteok, mock_remotive, mock_linkedin, mock_companyjobs, mock_wwr):
        """Test search_jobs returns empty list when no providers available."""
        mock_companyjobs.return_value = False
        mock_linkedin.return_value = False
        mock_remotive.return_value = False
        mock_remoteok.return_value = False
        mock_wwr.return_value = False

        agg = MCPAggregator()
        jobs = agg.search_jobs("python developer", count_per_provider=5)

        assert jobs == []

    def test_provider_diversity_round_robin(self):
        """Test that results include jobs from multiple providers (round-robin)."""
        # Create mock providers with different jobs
        provider1 = Mock(spec=MCPProvider)
        provider1.name = "RemoteOK"
        provider1.enabled = True
        provider1.is_available.return_value = True
        provider1.search_jobs.return_value = [
            {"title": "Job 1", "link": "https://remoteok.com/1", "source": "RemoteOK"},
            {"title": "Job 2", "link": "https://remoteok.com/2", "source": "RemoteOK"},
            {"title": "Job 3", "link": "https://remoteok.com/3", "source": "RemoteOK"},
        ]

        provider2 = Mock(spec=MCPProvider)
        provider2.name = "Remotive"
        provider2.enabled = True
        provider2.is_available.return_value = True
        provider2.search_jobs.return_value = [
            {"title": "Job A", "link": "https://remotive.io/a", "source": "Remotive"},
            {"title": "Job B", "link": "https://remotive.io/b", "source": "Remotive"},
            {"title": "Job C", "link": "https://remotive.io/c", "source": "Remotive"},
        ]

        provider3 = Mock(spec=MCPProvider)
        provider3.name = "WeWorkRemotely"
        provider3.enabled = True
        provider3.is_available.return_value = True
        provider3.search_jobs.return_value = [
            {"title": "Job X", "link": "https://wwr.com/x", "source": "WeWorkRemotely"},
            {"title": "Job Y", "link": "https://wwr.com/y", "source": "WeWorkRemotely"},
        ]

        agg = MCPAggregator(providers=[provider1, provider2, provider3])
        jobs = agg.search_jobs("python", count_per_provider=5, total_count=6)

        # Should get 6 jobs total, distributed across providers (round-robin)
        assert len(jobs) == 6

        # Count jobs per source
        sources = [job["source"] for job in jobs]
        source_counts = {
            "RemoteOK": sources.count("RemoteOK"),
            "Remotive": sources.count("Remotive"),
            "WeWorkRemotely": sources.count("WeWorkRemotely"),
        }

        # Each provider should contribute exactly 2 jobs (round-robin distribution)
        # With 6 total jobs and 3 providers, round-robin should distribute evenly
        assert source_counts["RemoteOK"] == 2
        assert source_counts["Remotive"] == 2
        assert source_counts["WeWorkRemotely"] == 2


class TestWeWorkRemotelyMCP:
    """Test We Work Remotely MCP provider."""

    def test_weworkremotely_initialization(self):
        """Test WeWorkRemotelyMCP initializes correctly."""
        provider = WeWorkRemotelyMCP()
        assert provider.name == "WeWorkRemotely"
        assert provider.is_available() is True

    @patch("httpx.get")
    def test_weworkremotely_search_jobs_success(self, mock_get):
        """Test WeWorkRemotelyMCP RSS feed parsing with mocked response."""
        # Mock RSS response (matches actual WWR format: "Company: Job Title")
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Remote Programming Jobs</title>
    <item>
      <title>TestCorp: Senior Python Developer</title>
      <link>https://weworkremotely.com/remote-jobs/test-company-python-dev</link>
      <description>Looking for Python expert</description>
      <pubDate>Mon, 01 Dec 2025 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>GoTech: Go Backend Engineer</title>
      <link>https://weworkremotely.com/remote-jobs/go-company-backend</link>
      <description>Backend role with Go</description>
      <pubDate>Mon, 01 Dec 2025 11:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = WeWorkRemotelyMCP()
        jobs = provider.search_jobs("python", count=10)

        # Should find Python job (query filtering)
        assert len(jobs) >= 1
        assert any("Python" in job["title"] for job in jobs)

        # Check job structure
        for job in jobs:
            assert "title" in job
            assert "company" in job
            assert "link" in job
            assert "summary" in job
            assert "source" in job
            assert job["source"] == "WeWorkRemotely"
            assert job["location"] == "Remote"

        # Verify company extraction works
        python_job = [j for j in jobs if "Python" in j["title"]][0]
        assert python_job["company"] == "TestCorp"
        assert python_job["title"] == "Senior Python Developer"  # Company prefix removed

    @patch("httpx.get")
    def test_weworkremotely_query_filtering(self, mock_get):
        """Test query filtering supports short tech terms like Go, R, UI."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Company: Go Developer</title>
      <link>https://weworkremotely.com/job1</link>
      <description>Go programming</description>
      <pubDate>Mon, 01 Dec 2025 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>DesignCo: UI Designer</title>
      <link>https://weworkremotely.com/job2</link>
      <description>UI/UX work</description>
      <pubDate>Mon, 01 Dec 2025 11:00:00 +0000</pubDate>
    </item>
    <item>
      <title>JavaCo: Java Developer</title>
      <link>https://weworkremotely.com/job3</link>
      <description>Java backend</description>
      <pubDate>Mon, 01 Dec 2025 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = WeWorkRemotelyMCP()

        # Test short term "Go"
        jobs = provider.search_jobs("Go", count=10)
        assert len(jobs) >= 1
        assert any("Go" in job["title"] or "Go" in job["summary"] for job in jobs)

        # Test short term "UI"
        jobs = provider.search_jobs("UI", count=10)
        assert len(jobs) >= 1
        assert any("UI" in job["title"] or "UI" in job["summary"] for job in jobs)

    @patch("httpx.get")
    def test_weworkremotely_error_handling(self, mock_get):
        """Test error handling when RSS feed is unavailable."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")

        provider = WeWorkRemotelyMCP()
        jobs = provider.search_jobs("python", count=5)

        # Should return empty list on error
        assert jobs == []

    @patch("httpx.get")
    def test_weworkremotely_malformed_xml(self, mock_get):
        """Test handling of malformed XML responses."""
        mock_response = Mock()
        mock_response.text = "Not valid XML at all!"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = WeWorkRemotelyMCP()
        jobs = provider.search_jobs("python", count=5)

        # Should return empty list on parse error
        assert jobs == []

    @patch("httpx.get")
    def test_weworkremotely_company_extraction(self, mock_get):
        """Test company name extraction from title."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>AcmeCorp: Python Dev</title>
      <link>https://weworkremotely.com/job1</link>
      <description>Great job at Acme</description>
      <pubDate>Mon, 01 Dec 2025 10:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = WeWorkRemotelyMCP()
        jobs = provider.search_jobs("python", count=1)

        assert len(jobs) == 1
        assert jobs[0]["company"] == "AcmeCorp"


class TestGenerateJobLeadsViaMCP:
    """Test generate_job_leads_via_mcp function."""

    @patch("app.mcp_providers.MCPAggregator.search_jobs")
    def test_generate_job_leads_via_mcp(self, mock_search):
        """Test generate_job_leads_via_mcp wrapper function."""
        mock_search.return_value = [
            {
                "title": "Python Developer",
                "company": "TechCorp",
                "location": "Remote",
                "summary": "Build things",
                "link": "https://example.com/1",
                "source": "LinkedIn",
            }
        ]

        jobs = generate_job_leads_via_mcp("python developer", count=5)

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Python Developer"
        mock_search.assert_called_once()
