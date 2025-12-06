"""Tests for JSearch discovery provider."""

from unittest.mock import MagicMock, patch

import pytest

from src.app.discovery.base_provider import IndustryType
from src.app.discovery.providers.jsearch_provider import JSearchProvider


@pytest.fixture
def mock_jsearch_response():
    """Mock JSearch API response data."""
    return {
        "status": "OK",
        "request_id": "test-123",
        "parameters": {
            "query": "python developer in remote",
            "page": 1,
            "num_pages": 1,
        },
        "data": [
            {
                "job_id": "job1",
                "employer_name": "TechCorp Inc",
                "employer_logo": "https://example.com/logo1.png",
                "employer_website": "https://techcorp.com",
                "job_title": "Senior Python Developer",
                "job_description": (
                    "Looking for a Python developer with AWS and Docker experience. "
                    "Build scalable APIs with FastAPI and PostgreSQL."
                ),
                "job_city": "San Francisco",
                "job_state": "CA",
                "job_country": "US",
                "job_is_remote": False,
                "job_posted_at_datetime_utc": "2024-01-15T10:30:00Z",
                "job_apply_link": "https://techcorp.com/careers/apply/123",
                "job_highlights": {
                    "Qualifications": [
                        "5+ years Python experience",
                        "Experience with AWS",
                        "Docker and Kubernetes knowledge",
                    ]
                },
            },
            {
                "job_id": "job2",
                "employer_name": "StartupXYZ",
                "employer_logo": "https://example.com/logo2.png",
                "employer_website": "https://startupxyz.io",
                "job_title": "Full Stack Engineer",
                "job_description": "Join our startup! We use React, Node.js, and MongoDB to build amazing products.",
                "job_city": None,
                "job_state": None,
                "job_country": None,
                "job_is_remote": True,
                "job_posted_at_datetime_utc": "2024-01-14T08:15:00Z",
                "job_apply_link": "https://startupxyz.io/jobs/apply/456",
                "job_highlights": {"Qualifications": ["JavaScript/TypeScript", "React experience"]},
            },
        ],
    }


@pytest.fixture
def provider_with_api_key(monkeypatch):
    """Create provider with mocked API key."""
    monkeypatch.setenv("RAPIDAPI_KEY", "test_api_key_123")
    return JSearchProvider()


class TestJSearchProvider:
    """Tests for JSearch provider initialization and metadata."""

    def test_initialization_requires_api_key(self, monkeypatch):
        """Test that provider requires RAPIDAPI_KEY environment variable."""
        monkeypatch.delenv("RAPIDAPI_KEY", raising=False)

        with pytest.raises(ValueError, match="RAPIDAPI_KEY environment variable is required"):
            JSearchProvider()

    def test_initialization_with_api_key(self, provider_with_api_key):
        """Test successful initialization with API key."""
        assert provider_with_api_key.api_key == "test_api_key_123"
        assert provider_with_api_key.provider_name == "jsearch"
        assert provider_with_api_key.headers["X-RapidAPI-Key"] == "test_api_key_123"
        assert provider_with_api_key.headers["X-RapidAPI-Host"] == "jsearch.p.rapidapi.com"

    def test_supported_industries(self, provider_with_api_key):
        """Test supported industries list."""
        industries = provider_with_api_key.supported_industries()
        assert IndustryType.TECH in industries
        assert IndustryType.OTHER in industries

    def test_get_metadata(self, provider_with_api_key):
        """Test provider metadata."""
        metadata = provider_with_api_key.get_metadata()
        assert metadata["name"] == "jsearch"
        assert metadata["requires_auth"] is True
        assert metadata["auth_type"] == "RapidAPI Key"
        assert "Real-time job listings" in metadata["features"]


class TestJSearchDiscovery:
    """Tests for company discovery via JSearch API."""

    @patch("httpx.Client")
    def test_discover_companies_basic(self, mock_client_class, provider_with_api_key, mock_jsearch_response):
        """Test basic company discovery."""
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jsearch_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        # Run discovery
        result = provider_with_api_key.discover_companies(
            {"query": "python developer", "locations": ["remote"], "limit": 10}
        )

        # Verify results
        assert len(result.companies) == 2
        assert result.source == "jsearch"

        # Check first company
        company1 = result.companies[0]
        assert company1.name == "TechCorp Inc"
        assert company1.website == "https://techcorp.com"
        assert company1.industry == IndustryType.TECH
        assert "python" in company1.tech_stack
        assert "aws" in company1.tech_stack
        assert "docker" in company1.tech_stack

        # Check second company
        company2 = result.companies[1]
        assert company2.name == "StartupXYZ"
        assert "Remote" in company2.locations
        assert "react" in company2.tech_stack
        assert "node.js" in company2.tech_stack
        assert "mongodb" in company2.tech_stack

    @patch("httpx.Client")
    def test_discover_companies_deduplication(self, mock_client_class, provider_with_api_key, mock_jsearch_response):
        """Test that duplicate companies are filtered out."""
        # Add duplicate company to response
        duplicate_job = mock_jsearch_response["data"][0].copy()
        duplicate_job["job_id"] = "job3"
        duplicate_job["job_title"] = "Junior Python Developer"
        mock_jsearch_response["data"].append(duplicate_job)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jsearch_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        result = provider_with_api_key.discover_companies({"limit": 10})

        # Should still only have 2 unique companies (TechCorp and StartupXYZ)
        assert len(result.companies) == 2
        company_names = [c.name for c in result.companies]
        assert "TechCorp Inc" in company_names
        assert "StartupXYZ" in company_names

    @patch("httpx.Client")
    def test_discover_companies_api_error(self, mock_client_class, provider_with_api_key):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 429  # Rate limit
        mock_response.text = "Rate limit exceeded"

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        result = provider_with_api_key.discover_companies()

        # Should return empty result on error
        assert len(result.companies) == 0

    @patch("httpx.Client")
    def test_discover_companies_pagination(self, mock_client_class, provider_with_api_key, mock_jsearch_response):
        """Test pagination to fetch more results."""
        # First page response
        page1_response = mock_jsearch_response.copy()

        # Second page response
        page2_response = {
            "status": "OK",
            "data": [
                {
                    "job_id": "job3",
                    "employer_name": "AnotherCorp",
                    "employer_website": "https://anothercorp.com",
                    "job_title": "DevOps Engineer",
                    "job_description": "Terraform and Kubernetes expert needed.",
                    "job_is_remote": True,
                    "job_posted_at_datetime_utc": "2024-01-13T12:00:00Z",
                    "job_apply_link": "https://anothercorp.com/jobs/789",
                    "job_highlights": {"Qualifications": ["Terraform", "Kubernetes"]},
                }
            ],
        }

        mock_responses = [
            MagicMock(status_code=200, json=lambda: page1_response),
            MagicMock(status_code=200, json=lambda: page2_response),
            # Empty page to stop pagination
            MagicMock(status_code=200, json=lambda: {
                      "status": "OK", "data": []}),
        ]

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = mock_responses

        mock_client_class.return_value = mock_client

        result = provider_with_api_key.discover_companies({"limit": 50})

        # Should have fetched from all pages (including empty page that stops pagination)
        assert len(result.companies) == 3
        assert mock_client.get.call_count == 3

    @patch("httpx.Client")
    def test_discover_companies_with_filters(self, mock_client_class, provider_with_api_key, mock_jsearch_response):
        """Test discovery with various filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jsearch_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = mock_response

        mock_client_class.return_value = mock_client

        filters = {
            "query": "machine learning engineer",
            "locations": ["new york", "boston"],
            "limit": 20,
            "date_posted": "3days",
            "employment_types": ["FULLTIME", "CONTRACTOR"],
            "remote_jobs_only": True,
        }

        provider_with_api_key.discover_companies(filters)

        # Verify API was called with correct parameters
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]

        assert "machine learning engineer" in params["query"]
        assert "new york, boston" in params["query"]
        assert params["date_posted"] == "3days"
        assert params["remote_jobs_only"] == "true"
        assert params["employment_types"] == "FULLTIME,CONTRACTOR"

    def test_extract_company_from_job(self, provider_with_api_key):
        """Test company extraction from job data."""
        job_data = {
            "employer_name": "TestCo",
            "employer_website": "https://testco.com",
            "employer_logo": "https://testco.com/logo.png",
            "job_title": "Python Developer",
            "job_description": "We need a Python developer with React and PostgreSQL experience.",
            "job_city": "Austin",
            "job_state": "TX",
            "job_is_remote": False,
            "job_posted_at_datetime_utc": "2024-01-01T00:00:00Z",
            "job_id": "test123",
            "job_apply_link": "https://testco.com/careers/apply",
            "job_highlights": {"Qualifications": ["Python", "React"]},
        }

        company = provider_with_api_key._extract_company_from_job(job_data)

        assert company is not None
        assert company.name == "TestCo"
        assert company.website == "https://testco.com"
        assert "Austin" in company.locations
        assert company.industry == IndustryType.TECH
        assert "python" in company.tech_stack
        assert "react" in company.tech_stack
        assert "postgresql" in company.tech_stack
        assert company.metadata["job_title"] == "Python Developer"

    def test_extract_company_missing_name(self, provider_with_api_key):
        """Test extraction fails gracefully when employer name is missing."""
        job_data = {"job_title": "Developer",
                    "job_description": "Some description"}

        company = provider_with_api_key._extract_company_from_job(job_data)
        assert company is None

    def test_infer_industry(self, provider_with_api_key):
        """Test industry inference from job data."""
        tech_job = {
            "job_title": "Software Engineer",
            "job_description": "Build scalable applications with Python and AWS.",
        }

        industry = provider_with_api_key._infer_industry(tech_job)
        assert industry == IndustryType.TECH

        other_job = {
            "job_title": "Sales Manager",
            "job_description": "Manage sales team and drive revenue.",
        }

        industry = provider_with_api_key._infer_industry(other_job)
        assert industry == IndustryType.OTHER

    def test_extract_tech_stack(self, provider_with_api_key):
        """Test technology extraction from job description."""
        job_data = {
            "job_description": (
                "We use Python, React, PostgreSQL, Docker, and AWS. " "Looking for Node.js and Kubernetes experience."
            ),
            "job_highlights": {"Qualifications": ["TypeScript is a plus"]},
        }

        tech_stack = provider_with_api_key._extract_tech_stack(job_data)

        assert "python" in tech_stack
        assert "react" in tech_stack
        assert "postgresql" in tech_stack
        assert "docker" in tech_stack
        assert "aws" in tech_stack
        assert "node.js" in tech_stack
        assert "kubernetes" in tech_stack
