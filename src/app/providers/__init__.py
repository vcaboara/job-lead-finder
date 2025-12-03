"""Job search MCP providers package.

This package contains modular job search providers. Each provider implements
the MCPProvider interface defined in base.py.

To add a new provider:
1. Create a new file (e.g., my_provider.py)
2. Implement a class that inherits from MCPProvider
3. Import and export it here
4. Register in MCPAggregator provider_map (mcp_providers.py)

Currently available providers:
- WeWorkRemotely: RSS-based remote jobs (fast, no auth)
- RemoteOK: Public API for remote jobs (fast, no auth)
- Remotive: REST API for remote jobs (fast, no auth)
- CompanyJobs: Gemini-powered company career page search (slow, requires API key)
- DuckDuckGo: Web search fallback (medium speed, no auth)
- LinkedIn: Browser-based scraping (requires cookies, disabled by default)
- Indeed: Browser-based scraping (requires cookies, disabled by default)
- GitHub: GitHub Jobs API (deprecated, kept for reference)
"""

# Import base classes
from .base import MCPProvider, HTTPX_AVAILABLE, BS4_AVAILABLE

# Import new modular providers
from .weworkremotely import WeWorkRemotelyMCP

# Re-export legacy providers from mcp_providers.py until fully migrated
# This maintains backward compatibility
try:
    from ..mcp_providers import (
        LinkedInMCP,
        IndeedMCP,
        GitHubJobsMCP,
        DuckDuckGoMCP,
        CompanyJobsMCP,
        RemoteOKMCP,
        RemotiveMCP,
        MCPAggregator,
        generate_job_leads_via_mcp,
    )
except ImportError:
    # During migration, some imports might fail
    pass

__all__ = [
    # Base classes
    "MCPProvider",
    "HTTPX_AVAILABLE",
    "BS4_AVAILABLE",
    
    # Modular providers (new structure)
    "WeWorkRemotelyMCP",
    
    # Legacy providers (to be migrated)
    "LinkedInMCP",
    "IndeedMCP",
    "GitHubJobsMCP",
    "DuckDuckGoMCP",
    "CompanyJobsMCP",
    "RemoteOKMCP",
    "RemotiveMCP",
    
    # Aggregator and utilities
    "MCPAggregator",
    "generate_job_leads_via_mcp",
]
