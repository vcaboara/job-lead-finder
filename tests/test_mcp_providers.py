"""Tests for MCP providers module."""

from unittest.mock import Mock, patch

from app.mcp_providers import (
    GitHubJobsMCP,
    IndeedMCP,
    LinkedInMCP,
    MCPAggregator,
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

    def test_weworkremotely_mcp_initialization(self):
        """Test WeWorkRemotelyMCP initializes correctly."""
        mcp = WeWorkRemotelyMCP()
        assert mcp.name == "WeWorkRemotely"
        assert mcp.is_available() is True  # RSS feeds are always available

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

    @patch("httpx.get")
    def test_weworkremotely_search_jobs_success(self, mock_get):
        """Test WeWorkRemotely search_jobs returns jobs from RSS feed."""
        # Mock RSS feed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>We Work Remotely</title>
    <item>
      <title>Senior Python Developer</title>
      <link>https://weworkremotely.com/remote-jobs/test-job</link>
      <description><![CDATA[<strong>TechCorp</strong> - Python backend position]]></description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Frontend Developer</title>
      <link>https://weworkremotely.com/remote-jobs/test-job2</link>
      <description><![CDATA[<strong>WebCo</strong> - React developer needed]]></description>
      <pubDate>Mon, 01 Jan 2024 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""
        mock_get.return_value = mock_response

        mcp = WeWorkRemotelyMCP()
        jobs = mcp.search_jobs("python developer", count=5)

        assert len(jobs) >= 1
        # Should find at least the Python job
        python_jobs = [j for j in jobs if "python" in j["title"].lower()]
        assert len(python_jobs) >= 1
        assert python_jobs[0]["source"] == "WeWorkRemotely"
        assert python_jobs[0]["location"] == "Remote"

    @patch("httpx.get")
    def test_weworkremotely_search_jobs_error(self, mock_get):
        """Test WeWorkRemotely handles errors gracefully."""
        mock_get.side_effect = Exception("Connection error")

        mcp = WeWorkRemotelyMCP()
        jobs = mcp.search_jobs("python developer", count=5)

        assert jobs == []


class TestMCPAggregator:
    """Test MCPAggregator class."""

    @patch("app.config_manager.load_config")
    def test_aggregator_initialization(self, mock_load_config):
        """Test MCPAggregator initialization with default providers."""
        # Mock config with CompanyJobs disabled, RemoteOK, Remotive, and WeWorkRemotely enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": False},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
                "weworkremotely": {"enabled": True},
            }
        }
        
        agg = MCPAggregator()
        # CompanyJobs disabled by default (slow), RemoteOK, Remotive, and WeWorkRemotely enabled
        assert len(agg.providers) == 3  # RemoteOK, Remotive, and WeWorkRemotely
        assert not any(p.name == "CompanyJobs" for p in agg.providers)  # Disabled by default
        assert any(p.name == "RemoteOK" for p in agg.providers)
        assert any(p.name == "Remotive" for p in agg.providers)
        assert any(p.name == "WeWorkRemotely" for p in agg.providers)

    def test_aggregator_custom_providers(self):
        """Test MCPAggregator with custom provider list."""
        mock_provider = Mock()
        mock_provider.name = "Custom"
        mock_provider.enabled = True

        agg = MCPAggregator(providers=[mock_provider])
        assert len(agg.providers) == 1
        assert agg.providers[0].name == "Custom"

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.WeWorkRemotelyMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_get_available_providers(
        self, mock_load_config, mock_remoteok, mock_remotive, mock_weworkremotely, mock_companyjobs
    ):
        """Test get_available_providers filters correctly."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
                "weworkremotely": {"enabled": True},
            }
        }
        
        # Only Remotive is available (others mocked as unavailable)
        mock_remotive.return_value = True
        mock_remoteok.return_value = False
        mock_weworkremotely.return_value = False
        mock_companyjobs.return_value = False

        agg = MCPAggregator()
        available = agg.get_available_providers()

        assert len(available) == 1  # Only Remotive is available (others mocked as unavailable)
        assert any(p.name == "Remotive" for p in available)

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.WeWorkRemotelyMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.search_jobs")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_search_jobs_aggregation(
        self,
        mock_load_config,
        mock_remoteok_avail,
        mock_remotive_avail,
        mock_search,
        mock_wwr_avail,
        mock_companyjobs_avail,
    ):
        """Test search_jobs aggregates from multiple providers."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
                "weworkremotely": {"enabled": True},
            }
        }
        
        # Only Remotive available (CompanyJobs, RemoteOK, and WWR mocked unavailable)
        mock_remotive_avail.return_value = True
        mock_remoteok_avail.return_value = False
        mock_wwr_avail.return_value = False
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
    @patch("app.mcp_providers.WeWorkRemotelyMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.search_jobs")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.config_manager.load_config")
    def test_deduplication(
        self,
        mock_load_config,
        mock_remotive_avail,
        mock_remoteok_avail,
        mock_search,
        mock_wwr_avail,
        mock_companyjobs_avail,
    ):
        """Test deduplication removes duplicate job links."""
        # Mock config with all providers enabled
        mock_load_config.return_value = {
            "providers": {
                "companyjobs": {"enabled": True},
                "remoteok": {"enabled": True},
                "remotive": {"enabled": True},
                "weworkremotely": {"enabled": True},
            }
        }
        
        # Only RemoteOK available (Remotive, WWR, and CompanyJobs unavailable)
        mock_remoteok_avail.return_value = True
        mock_remotive_avail.return_value = False
        mock_wwr_avail.return_value = False
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

    @patch("app.mcp_providers.CompanyJobsMCP.is_available")
    @patch("app.mcp_providers.LinkedInMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.mcp_providers.WeWorkRemotelyMCP.is_available")
    def test_no_providers_available(
        self, mock_weworkremotely, mock_remoteok, mock_remotive, mock_linkedin, mock_companyjobs
    ):
        """Test search_jobs returns empty list when no providers available."""
        mock_companyjobs.return_value = False
        mock_linkedin.return_value = False
        mock_remotive.return_value = False
        mock_remoteok.return_value = False
        mock_weworkremotely.return_value = False

        agg = MCPAggregator()
        jobs = agg.search_jobs("python developer", count_per_provider=5)

        assert jobs == []


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
