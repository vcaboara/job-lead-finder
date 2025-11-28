"""MCP (Model Context Protocol) providers for job search.

This module provides a unified interface for multiple job search MCPs:
- LinkedIn MCP
- Indeed MCP (if available)
- GitHub Jobs MCP
- Custom job board MCPs

Each MCP can be queried independently and results can be aggregated.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MCPProvider(ABC):
    """Base class for MCP providers."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    @abstractmethod
    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search for jobs using this MCP.

        Args:
            query: Job search query (e.g., "python developer")
            count: Number of jobs to return
            location: Optional location filter
            **kwargs: Additional provider-specific parameters

        Returns:
            List of job dictionaries with keys: title, company, location, summary, link
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this MCP is available and configured."""
        pass


class LinkedInMCP(MCPProvider):
    """LinkedIn MCP provider."""

    def __init__(self):
        super().__init__("LinkedIn")
        self.mcp_server_url = os.getenv("LINKEDIN_MCP_URL", "http://localhost:3000")

    def is_available(self) -> bool:
        """Check if LinkedIn MCP server is running."""
        try:
            import httpx

            resp = httpx.get(f"{self.mcp_server_url}/health", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search LinkedIn jobs via MCP."""
        if not self.is_available():
            print(f"LinkedIn MCP not available at {self.mcp_server_url}")
            return []

        try:
            import httpx

            payload = {"query": query, "count": count, "location": location or "United States"}

            resp = httpx.post(f"{self.mcp_server_url}/search/jobs", json=payload, timeout=30.0)
            resp.raise_for_status()

            jobs = resp.json().get("jobs", [])
            # Normalize to our schema
            return [
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "summary": job.get("description", "")[:500],
                    "link": job.get("url", ""),
                    "source": "LinkedIn",
                }
                for job in jobs[:count]
            ]
        except Exception as e:
            print(f"LinkedIn MCP error: {e}")
            return []


class IndeedMCP(MCPProvider):
    """Indeed MCP provider (if available)."""

    def __init__(self):
        super().__init__("Indeed")
        self.mcp_server_url = os.getenv("INDEED_MCP_URL", "http://localhost:3001")

    def is_available(self) -> bool:
        """Check if Indeed MCP server is running."""
        try:
            import httpx

            resp = httpx.get(f"{self.mcp_server_url}/health", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search Indeed jobs via MCP."""
        if not self.is_available():
            print(f"Indeed MCP not available at {self.mcp_server_url}")
            return []

        try:
            import httpx

            payload = {"query": query, "count": count, "location": location or "United States"}

            resp = httpx.post(f"{self.mcp_server_url}/search/jobs", json=payload, timeout=30.0)
            resp.raise_for_status()

            jobs = resp.json().get("jobs", [])
            return [
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "summary": job.get("description", "")[:500],
                    "link": job.get("url", ""),
                    "source": "Indeed",
                }
                for job in jobs[:count]
            ]
        except Exception as e:
            print(f"Indeed MCP error: {e}")
            return []


class GitHubJobsMCP(MCPProvider):
    """GitHub Jobs MCP provider."""

    def __init__(self):
        super().__init__("GitHub")
        self.mcp_server_url = os.getenv("GITHUB_JOBS_MCP_URL", "http://localhost:3002")

    def is_available(self) -> bool:
        """Check if GitHub Jobs MCP server is running."""
        try:
            import httpx

            resp = httpx.get(f"{self.mcp_server_url}/health", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search GitHub jobs via MCP."""
        if not self.is_available():
            print(f"GitHub Jobs MCP not available at {self.mcp_server_url}")
            return []

        try:
            import httpx

            payload = {"query": query, "count": count, "location": location}

            resp = httpx.post(f"{self.mcp_server_url}/search/jobs", json=payload, timeout=30.0)
            resp.raise_for_status()

            jobs = resp.json().get("jobs", [])
            return [
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "summary": job.get("description", "")[:500],
                    "link": job.get("url", ""),
                    "source": "GitHub",
                }
                for job in jobs[:count]
            ]
        except Exception as e:
            print(f"GitHub Jobs MCP error: {e}")
            return []


class MCPAggregator:
    """Aggregates results from multiple MCP providers."""

    def __init__(self, providers: Optional[List[MCPProvider]] = None):
        self.providers = providers or [LinkedInMCP(), IndeedMCP(), GitHubJobsMCP()]

    def get_available_providers(self) -> List[MCPProvider]:
        """Get list of available MCP providers."""
        return [p for p in self.providers if p.enabled and p.is_available()]

    def search_jobs(
        self,
        query: str,
        count_per_provider: int = 5,
        total_count: Optional[int] = None,
        location: Optional[str] = None,
        providers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search jobs across multiple MCPs.

        Args:
            query: Job search query
            count_per_provider: Number of jobs to request from each MCP
            total_count: Total number of jobs to return (None = all)
            location: Optional location filter
            providers: Optional list of provider names to use (None = all available)

        Returns:
            Aggregated and deduplicated list of jobs
        """
        available = self.get_available_providers()

        if providers:
            # Filter to requested providers
            available = [p for p in available if p.name in providers]

        if not available:
            print("No MCP providers available")
            return []

        print(f"Searching {len(available)} MCP providers: {[p.name for p in available]}")

        all_jobs = []
        for provider in available:
            try:
                jobs = provider.search_jobs(query, count_per_provider, location)
                print(f"  {provider.name}: found {len(jobs)} jobs")
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"  {provider.name}: error - {e}")

        # Deduplicate by link
        seen_links = set()
        unique_jobs = []
        for job in all_jobs:
            link = job.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique_jobs.append(job)

        # Return requested count
        if total_count:
            return unique_jobs[:total_count]
        return unique_jobs


def generate_job_leads_via_mcp(
    query: str,
    count: int = 5,
    count_per_provider: Optional[int] = None,
    location: Optional[str] = None,
    providers: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Generate job leads using MCP providers.

    Args:
        query: Job search query
        count: Total number of jobs to return
        count_per_provider: Jobs per MCP (default: count)
        location: Optional location filter
        providers: Optional list of provider names

    Returns:
        List of job dictionaries
    """
    aggregator = MCPAggregator()

    # Default: request 'count' from each provider to ensure we get enough after dedup
    if count_per_provider is None:
        count_per_provider = count

    return aggregator.search_jobs(
        query=query,
        count_per_provider=count_per_provider,
        total_count=count,
        location=location,
        providers=providers,
    )
