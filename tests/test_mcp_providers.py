"""Tests for MCP providers module."""

from unittest.mock import Mock, patch

from app.mcp_providers import GitHubJobsMCP, IndeedMCP, LinkedInMCP, MCPAggregator, generate_job_leads_via_mcp


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

    def test_aggregator_initialization(self):
        """Test MCPAggregator initialization with default providers."""
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

    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    def test_get_available_providers(self, mock_remoteok, mock_remotive):
        """Test get_available_providers filters correctly."""
        # CompanyJobs disabled by default in config, RemoteOK and Remotive enabled
        mock_remotive.return_value = True
        mock_remoteok.return_value = False

        agg = MCPAggregator()
        available = agg.get_available_providers()

        assert len(available) == 1  # Only Remotive is available (RemoteOK mocked as unavailable)
        assert any(p.name == "Remotive" for p in available)

    @patch("app.mcp_providers.RemotiveMCP.search_jobs")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    def test_search_jobs_aggregation(self, mock_remoteok_avail, mock_remotive_avail, mock_search):
        """Test search_jobs aggregates from multiple providers."""
        # Only Remotive available (CompanyJobs disabled by default)
        mock_remotive_avail.return_value = True
        mock_remoteok_avail.return_value = False

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

    @patch("app.mcp_providers.RemoteOKMCP.search_jobs")
    @patch("app.mcp_providers.RemoteOKMCP.is_available")
    @patch("app.mcp_providers.RemotiveMCP.is_available")
    def test_deduplication(self, mock_remotive_avail, mock_remoteok_avail, mock_search):
        """Test deduplication removes duplicate job links."""
        # Only RemoteOK available
        mock_remoteok_avail.return_value = True
        mock_remotive_avail.return_value = False

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
    def test_no_providers_available(self, mock_remoteok, mock_remotive, mock_linkedin, mock_companyjobs):
        """Test search_jobs returns empty list when no providers available."""
        mock_companyjobs.return_value = False
        mock_linkedin.return_value = False
        mock_remotive.return_value = False
        mock_remoteok.return_value = False

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
