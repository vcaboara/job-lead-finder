"""Tests for base discovery provider interface."""

from datetime import UTC, datetime

import pytest

from app.discovery.base_provider import BaseDiscoveryProvider, Company, CompanySize, DiscoveryResult, IndustryType


class MockProvider(BaseDiscoveryProvider):
    """Mock provider for testing."""

    def __init__(self):
        super().__init__("mock_provider")

    def discover_companies(self, filters=None):
        """Return mock discovery result."""
        companies = [
            Company(
                name="Test Company",
                website="https://example.com",
                careers_url="https://example.com/careers",
                industry=IndustryType.TECH,
                size=CompanySize.STARTUP,
                description="A test company",
                tech_stack=["python", "docker"],
                locations=["remote", "seattle"],
                funding_stage="series-a",
                discovered_via=self.provider_name,
            )
        ]

        return DiscoveryResult(
            source=self.provider_name, companies=companies, total_found=1, timestamp=datetime.now(UTC)
        )

    def supported_industries(self):
        """Return supported industries."""
        return [IndustryType.TECH, IndustryType.HEALTHCARE]


def test_company_creation():
    """Test creating a Company instance."""
    company = Company(name="Acme Corp", website="https://acme.com")

    assert company.name == "Acme Corp"
    assert company.website == "https://acme.com"
    assert company.industry == IndustryType.OTHER
    assert company.size == CompanySize.UNKNOWN
    assert company.tech_stack == []
    assert company.locations == []
    assert company.metadata == {}
    assert isinstance(company.discovered_at, datetime)


def test_company_with_full_data():
    """Test creating a Company with all fields."""
    now = datetime.now(UTC)
    company = Company(
        name="Tech Startup",
        website="https://techstartup.com",
        careers_url="https://techstartup.com/jobs",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        description="An innovative tech company",
        tech_stack=["python", "react", "docker"],
        locations=["san-francisco", "remote"],
        funding_stage="seed",
        discovered_via="hn_whos_hiring",
        discovered_at=now,
        metadata={"hn_thread_id": "12345"},
    )

    assert company.name == "Tech Startup"
    assert company.website == "https://techstartup.com"
    assert company.careers_url == "https://techstartup.com/jobs"
    assert company.industry == IndustryType.TECH
    assert company.size == CompanySize.STARTUP
    assert company.description == "An innovative tech company"
    assert company.tech_stack == ["python", "react", "docker"]
    assert company.locations == ["san-francisco", "remote"]
    assert company.funding_stage == "seed"
    assert company.discovered_via == "hn_whos_hiring"
    assert company.discovered_at == now
    assert company.metadata == {"hn_thread_id": "12345"}


def test_discovery_result_creation():
    """Test creating a DiscoveryResult."""
    companies = [
        Company(name="Company 1", website="https://company1.com"),
        Company(name="Company 2", website="https://company2.com"),
    ]

    result = DiscoveryResult(source="test_source", companies=companies, total_found=2, timestamp=datetime.now(UTC))

    assert result.source == "test_source"
    assert len(result.companies) == 2
    assert result.total_found == 2
    assert isinstance(result.timestamp, datetime)
    assert result.errors == []
    assert result.metadata == {}


def test_discovery_result_with_errors():
    """Test DiscoveryResult with errors."""
    result = DiscoveryResult(
        source="test_source",
        companies=[],
        total_found=0,
        timestamp=datetime.now(UTC),
        errors=["Connection timeout", "Invalid response"],
        metadata={"retry_count": 3},
    )

    assert result.errors == ["Connection timeout", "Invalid response"]
    assert result.metadata == {"retry_count": 3}


def test_mock_provider_discover():
    """Test mock provider discovery."""
    provider = MockProvider()
    result = provider.discover_companies()

    assert result.source == "mock_provider"
    assert len(result.companies) == 1
    assert result.total_found == 1
    assert result.companies[0].name == "Test Company"
    assert result.companies[0].tech_stack == ["python", "docker"]


def test_provider_metadata():
    """Test provider metadata retrieval."""
    provider = MockProvider()
    metadata = provider.get_metadata()

    assert metadata["name"] == "mock_provider"
    assert metadata["enabled"] is True
    assert IndustryType.TECH.value in metadata["industries"]
    assert IndustryType.HEALTHCARE.value in metadata["industries"]
    assert metadata["requires_auth"] is False


def test_provider_supported_industries():
    """Test provider industry support."""
    provider = MockProvider()
    industries = provider.supported_industries()

    assert IndustryType.TECH in industries
    assert IndustryType.HEALTHCARE in industries
    assert len(industries) == 2


def test_validate_filters_success():
    """Test filter validation with valid filters."""
    provider = MockProvider()

    # No filters
    assert provider.validate_filters(None) is True

    # Valid industry filter
    assert provider.validate_filters({"industries": [IndustryType.TECH]}) is True
    assert provider.validate_filters({"industries": ["tech", "healthcare"]}) is True

    # Other filters (not validated yet)
    assert provider.validate_filters({"company_sizes": [CompanySize.STARTUP]}) is True
    assert provider.validate_filters({"locations": ["remote"]}) is True


def test_validate_filters_unsupported_industry():
    """Test filter validation with unsupported industry."""
    provider = MockProvider()

    # Finance not supported by MockProvider
    with pytest.raises(ValueError) as exc_info:
        provider.validate_filters({"industries": [IndustryType.FINANCE]})

    assert "does not support industries" in str(exc_info.value)
    assert "finance" in str(exc_info.value).lower()


def test_industry_type_enum():
    """Test IndustryType enum values."""
    assert IndustryType.TECH.value == "tech"
    assert IndustryType.HEALTHCARE.value == "healthcare"
    assert IndustryType.FINANCE.value == "finance"
    assert IndustryType.EDUCATION.value == "education"


def test_company_size_enum():
    """Test CompanySize enum values."""
    assert CompanySize.STARTUP.value == "startup"
    assert CompanySize.SMALL.value == "small"
    assert CompanySize.MEDIUM.value == "medium"
    assert CompanySize.LARGE.value == "large"
    assert CompanySize.UNKNOWN.value == "unknown"


def test_provider_enable_disable():
    """Test enabling/disabling provider."""
    provider = MockProvider()

    assert provider.enabled is True

    provider.enabled = False
    assert provider.enabled is False
    assert provider.get_metadata()["enabled"] is False
