"""MCP (Model Context Protocol) providers for job search.

This module provides a unified interface for multiple job search MCPs:
- DuckDuckGo Search MCP (primary - no auth required)
- GitHub Jobs (via GitHub API)
- LinkedIn MCP (requires browser cookies - disabled by default)

Each MCP can be queried independently and results can be aggregated.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup4 not available. DuckDuckGo search will be disabled.")


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
    """GitHub Jobs MCP provider - uses GitHub API to search for job postings."""

    def __init__(self):
        super().__init__("GitHub")
        # GitHub Jobs can be found in repos with 'jobs' or 'careers' in issues/discussions
        # Or in dedicated job board repos
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.job_repos = [
            "remoteintech/remote-jobs",
            "lukasz-madon/awesome-remote-job",
            "engineerapart/TheRemoteFreelancer",
        ]

    def is_available(self) -> bool:
        """Check if GitHub API is accessible."""
        if not self.github_token:
            return False
        try:
            import httpx

            headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json"}
            resp = httpx.get("https://api.github.com/user", headers=headers, timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search GitHub for job postings."""
        if not self.is_available():
            print(f"GitHub MCP not available (token: {'set' if self.github_token else 'missing'})")
            return []

        try:
            import httpx

            headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json"}

            jobs = []
            # Search GitHub issues in job repos
            search_query = f"{query} type:issue state:open"
            if location:
                search_query += f" {location}"

            # Add job-related terms
            search_query += " (hiring OR job OR position OR vacancy)"

            url = "https://api.github.com/search/issues"
            params = {"q": search_query, "per_page": min(count * 2, 30), "sort": "created", "order": "desc"}

            resp = httpx.get(url, headers=headers, params=params, timeout=10.0)
            resp.raise_for_status()

            results = resp.json().get("items", [])

            for item in results[:count]:
                # Extract job details from issue
                title = item.get("title", "")
                body = item.get("body", "")[:500] if item.get("body") else ""
                repo = item.get("repository_url", "").split("/")[-2:] if item.get("repository_url") else ["", ""]
                company = repo[0] if repo else "GitHub"

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location or "Remote",
                        "summary": body,
                        "link": item.get("html_url", ""),
                        "source": "GitHub",
                    }
                )

            return jobs[:count]
        except Exception as e:
            print(f"GitHub MCP error: {e}")
            return []


class DuckDuckGoMCP(MCPProvider):
    """DuckDuckGo Search MCP provider - searches for jobs using DuckDuckGo."""

    def __init__(self):
        super().__init__("DuckDuckGo")
        # DuckDuckGo doesn't require authentication

    def is_available(self) -> bool:
        """DuckDuckGo is available if BeautifulSoup4 is installed."""
        return BS4_AVAILABLE

    def search_jobs(self, query: str, count: int = 5, location: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search for jobs using DuckDuckGo."""
        if not BS4_AVAILABLE:
            print("DuckDuckGo MCP error: BeautifulSoup4 not installed")
            return []

        try:
            import httpx

            # Build search query
            search_query = f"{query} jobs"
            if location:
                search_query += f" {location}"

            # Add job-specific terms
            search_query += " (hiring OR careers OR apply)"

            # DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {"q": search_query}

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            }

            resp = httpx.post(url, data=params, headers=headers, timeout=10.0, follow_redirects=True)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("div", class_="result")

            jobs = []
            for result in results[: count * 3]:  # Get extra for filtering
                try:
                    link_elem = result.find("a", class_="result__a")
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    link = link_elem.get("href", "")

                    # Skip generic job board landing/search pages
                    # We want specific job postings, not aggregator pages
                    link_lower = link.lower()
                    skip_patterns = [
                        "/jobs/search",
                        "/jobs?",
                        "linkedin.com/jobs/python",  # Generic search pages
                        "linkedin.com/jobs/remote",
                        "indeed.com/jobs?q=",
                        "glassdoor.com/Job/",  # Glassdoor job search (not specific posting)
                        "remotepython.com/jobs",  # Aggregator
                        "arc.dev/remote-jobs",  # Aggregator
                        "weworkremotely.com",  # Aggregator home
                    ]

                    if any(pattern in link_lower for pattern in skip_patterns):
                        continue

                    # Accept job-related links that look like specific postings
                    job_indicators = [
                        "/jobs/view/",  # LinkedIn specific job
                        "/viewjob?",  # Indeed specific job
                        "/job/",  # Generic job posting pattern
                        "/position/",
                        "/opening/",
                        "/vacancy/",
                        "apply",
                        "careers/",
                    ]

                    if not any(indicator in link_lower for indicator in job_indicators):
                        # If no job indicators, skip it
                        continue

                    snippet_elem = result.find("a", class_="result__snippet")
                    summary = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    # Extract company from URL or title
                    company = "Unknown"
                    if "linkedin.com" in link:
                        company = "LinkedIn"
                    elif "indeed.com" in link:
                        company = "Indeed"
                    elif "glassdoor" in link:
                        company = "Glassdoor"
                    else:
                        # Try to extract company from domain
                        from urllib.parse import urlparse

                        domain = urlparse(link).netloc
                        if domain:
                            company = domain.replace("www.", "").split(".")[0].title()

                    jobs.append(
                        {
                            "title": title,
                            "company": company,
                            "location": location or "Remote",
                            "summary": summary[:500],
                            "link": link,
                            "source": "DuckDuckGo",
                        }
                    )

                    if len(jobs) >= count:
                        break
                except Exception:
                    continue

            return jobs[:count]
        except Exception as e:
            print(f"DuckDuckGo MCP error: {e}")
            return []


class MCPAggregator:
    """Aggregates results from multiple MCP providers."""

    def __init__(self, providers: Optional[List[MCPProvider]] = None):
        # Default: GitHub (primary - real job postings) and DuckDuckGo (secondary)
        # LinkedIn removed from defaults (requires browser cookies)
        self.providers = providers or [GitHubJobsMCP(), DuckDuckGoMCP()]

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
