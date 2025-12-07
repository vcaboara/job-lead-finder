"""Base MCP provider interface and utilities.

This module defines the base MCPProvider class that all job search providers
must implement. Each provider should be a separate module in this package.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Optional dependency checks - imports are used to set availability flags
# exported by __init__.py and used by provider implementations
try:
    import httpx  # noqa: F401

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup  # noqa: F401

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class MCPProvider(ABC):
    """Base class for MCP providers.

    To add a new provider:
    1. Create a new file in app/providers/ (e.g., remote_ok.py)
    2. Subclass MCPProvider
    3. Implement search_jobs() and is_available()
    4. Import and register in __init__.py
    """

    def __init__(self, name: str, enabled: bool = True):
        """Initialize provider.

        Args:
            name: Provider name (e.g., "RemoteOK")
            enabled: Whether provider is enabled by default
        """
        self.name = name
        self.enabled = enabled

    @abstractmethod
    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search for jobs using this provider.

        Args:
            query: Job search query (e.g., "python developer")
            count: Number of jobs to return
            location: Optional location filter
            **kwargs: Additional provider-specific parameters

        Returns:
            List of job dictionaries with keys:
            - title: Job title
            - company: Company name
            - location: Job location
            - summary: Job description/summary
            - link: URL to job posting
            - source: Provider name
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and configured.

        Returns:
            True if provider can be used, False otherwise
        """
        pass
