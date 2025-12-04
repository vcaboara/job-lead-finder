"""Base classes and interfaces for company discovery providers.

Provides an abstract base class that all discovery sources must implement,
ensuring consistent interface across different data sources (HN, YC, GitHub, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Optional


class IndustryType(str, Enum):
    """Supported industry types for discovery."""

    TECH = "tech"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    NON_PROFIT = "non_profit"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    OTHER = "other"


class CompanySize(str, Enum):
    """Company size categories."""

    STARTUP = "startup"  # 1-50 employees
    SMALL = "small"  # 51-200 employees
    MEDIUM = "medium"  # 201-1000 employees
    LARGE = "large"  # 1001+ employees
    UNKNOWN = "unknown"


@dataclass
class Company:
    """Represents a discovered company.

    Attributes:
        name: Company name
        website: Primary company website URL
        careers_url: Direct link to careers/jobs page (if known)
        industry: Primary industry category
        size: Estimated company size
        description: Brief description of the company
        tech_stack: List of technologies/languages used (if known)
        locations: List of office locations or "remote"
        funding_stage: Funding stage if applicable (seed, series-a, etc.)
        discovered_via: Source that discovered this company
        discovered_at: When the company was first discovered
        metadata: Additional provider-specific data
    """

    name: str
    website: str
    careers_url: Optional[str] = None
    industry: IndustryType = IndustryType.OTHER
    size: CompanySize = CompanySize.UNKNOWN
    description: str = ""
    tech_stack: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    funding_stage: Optional[str] = None
    discovered_via: str = ""
    discovered_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.tech_stack is None:
            self.tech_stack = []
        if self.locations is None:
            self.locations = []
        if self.metadata is None:
            self.metadata = {}
        if self.discovered_at is None:
            self.discovered_at = datetime.now(UTC)


@dataclass
class DiscoveryResult:
    """Result of a discovery operation.

    Attributes:
        source: Name of the discovery source
        companies: List of discovered companies
        total_found: Total number of companies found
        timestamp: When the discovery was performed
        errors: List of any errors encountered
        metadata: Additional result metadata (e.g., page URLs, API calls made)
    """

    source: str
    companies: list[Company]
    total_found: int
    timestamp: datetime
    errors: Optional[list[str]] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class BaseDiscoveryProvider(ABC):
    """Abstract base class for company discovery providers.

    All discovery sources (HN, YC, GitHub, etc.) must implement this interface
    to ensure consistent behavior and easy extensibility.

    Example:
        ```python
        class HNProvider(BaseDiscoveryProvider):
            def __init__(self):
                super().__init__("hn_whos_hiring")

            def discover_companies(self, filters=None):
                # Implementation here
                pass

            def supported_industries(self):
                return [IndustryType.TECH]
        ```
    """

    def __init__(self, provider_name: str):
        """Initialize the provider.

        Args:
            provider_name: Unique identifier for this provider
        """
        self.provider_name = provider_name
        self.enabled = True

    @abstractmethod
    def discover_companies(self, filters: Optional[dict] = None) -> DiscoveryResult:
        """Discover companies from this source.

        Args:
            filters: Optional filters to apply during discovery. Common filters:
                - industries: List of IndustryType to filter by
                - company_sizes: List of CompanySize to filter by
                - locations: List of location strings (e.g., ["remote", "seattle"])
                - tech_stack: List of required technologies
                - limit: Maximum number of companies to return

        Returns:
            DiscoveryResult containing discovered companies and metadata

        Raises:
            Exception: If discovery fails (network issues, API errors, etc.)
        """
        pass

    @abstractmethod
    def supported_industries(self) -> list[IndustryType]:
        """Return list of industries this provider can discover companies for.

        Returns:
            List of IndustryType values this provider supports
        """
        pass

    def get_metadata(self) -> dict:
        """Return provider metadata and capabilities.

        Returns:
            Dictionary with provider information:
                - name: Provider name
                - enabled: Whether provider is enabled
                - industries: Supported industries
                - rate_limit: Any rate limiting info
                - requires_auth: Whether provider requires API keys
        """
        return {
            "name": self.provider_name,
            "enabled": self.enabled,
            "industries": [ind.value for ind in self.supported_industries()],
            "requires_auth": False,
        }

    def validate_filters(self, filters: Optional[dict]) -> bool:
        """Validate that provided filters are compatible with this provider.

        Args:
            filters: Filter dictionary to validate

        Returns:
            True if filters are valid for this provider

        Raises:
            ValueError: If filters contain invalid values
        """
        if filters is None:
            return True

        # Validate industry filter
        if "industries" in filters:
            supported = self.supported_industries()
            requested = [IndustryType(ind) if isinstance(ind, str) else ind for ind in filters["industries"]]
            unsupported = [ind for ind in requested if ind not in supported]
            if unsupported:
                raise ValueError(
                    f"Provider {self.provider_name} does not support industries: {unsupported}. "
                    f"Supported: {supported}"
                )

        return True
