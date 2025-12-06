"""JSearch API provider for real-time job discovery via RapidAPI.

JSearch aggregates job listings from multiple sources (Indeed, LinkedIn, etc.)
and provides structured, real-time data perfect for passive job discovery.

API Documentation: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""

import logging
import os
from datetime import UTC, datetime
from typing import Optional

import httpx

from ..base_provider import (
    BaseDiscoveryProvider,
    Company,
    CompanySize,
    DiscoveryResult,
    IndustryType,
)

logger = logging.getLogger(__name__)


class JSearchProvider(BaseDiscoveryProvider):
    """Provider for discovering jobs via JSearch API on RapidAPI.

    Uses the JSearch API to find real-time job listings, then extracts
    company information for passive discovery.

    Requires RAPIDAPI_KEY environment variable.

    Example:
        ```python
        provider = JSearchProvider()
        result = provider.discover_companies({
            'query': 'python developer',
            'locations': ['remote'],
            'limit': 50
        })
        print(f"Found {len(result.companies)} companies")
        ```
    """

    BASE_URL = "https://jsearch.p.rapidapi.com"

    def __init__(self):
        """Initialize JSearch provider with RapidAPI credentials."""
        super().__init__("jsearch")

        self.api_key = os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError(
                "RAPIDAPI_KEY environment variable is required for JSearch provider. "
                "Get your key at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
            )

        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

    def discover_companies(self, filters: Optional[dict] = None) -> DiscoveryResult:
        """Discover companies by searching for jobs via JSearch API.

        Args:
            filters: Search parameters:
                - query: Search query (e.g., "python developer", "machine learning")
                - locations: List of locations (e.g., ["remote", "san francisco"])
                - limit: Max number of jobs to fetch (default: 50, max: 1000)
                - date_posted: "all", "today", "3days", "week", "month"
                - employment_types: ["FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN"]
                - remote_jobs_only: bool

        Returns:
            DiscoveryResult with discovered companies extracted from job listings

        Raises:
            Exception: If API request fails
        """
        filters = filters or {}
        query = filters.get("query", "software developer")
        locations = filters.get("locations", ["remote"])
        limit = min(filters.get("limit", 50), 1000)  # API max is 1000
        date_posted = filters.get("date_posted", "week")
        employment_types = filters.get("employment_types", ["FULLTIME"])
        remote_only = filters.get("remote_jobs_only", False)

        # Build search query
        location_str = ", ".join(locations) if locations else "remote"
        search_query = f"{query} in {location_str}"

        logger.info(
            f"[JSearch] Searching for: '{search_query}' (limit={limit}, date_posted={date_posted})"
        )

        try:
            companies_map = {}  # Deduplicate by company name
            page = 1
            num_pages = (limit // 10) + 1  # JSearch returns ~10 results per page

            with httpx.Client(timeout=30.0) as client:
                for _ in range(num_pages):
                    params = {
                        "query": search_query,
                        "page": str(page),
                        "num_pages": "1",
                        "date_posted": date_posted,
                    }

                    if remote_only:
                        params["remote_jobs_only"] = "true"

                    if employment_types:
                        params["employment_types"] = ",".join(employment_types)

                    response = client.get(
                        f"{self.BASE_URL}/search",
                        headers=self.headers,
                        params=params,
                    )

                    if response.status_code != 200:
                        logger.error(
                            f"[JSearch] API error: {response.status_code} - {response.text}"
                        )
                        break

                    data = response.json()
                    jobs = data.get("data", [])

                    if not jobs:
                        logger.info(f"[JSearch] No more results at page {page}")
                        break

                    # Extract companies from job listings
                    for job in jobs:
                        company = self._extract_company_from_job(job)
                        if company and company.name not in companies_map:
                            companies_map[company.name] = company

                    logger.info(
                        f"[JSearch] Page {page}: Found {len(jobs)} jobs, "
                        f"{len(companies_map)} unique companies so far"
                    )

                    if len(companies_map) >= limit:
                        break

                    page += 1

            companies = list(companies_map.values())[:limit]

            logger.info(
                f"[JSearch] Discovery complete: {len(companies)} unique companies found"
            )

            return DiscoveryResult(
                source=self.provider_name,
                companies=companies,
                total_found=len(companies),
                timestamp=datetime.now(UTC),
                metadata={
                    "query": search_query,
                    "total_jobs_found": len(companies_map),
                    "companies_returned": len(companies),
                    "date_posted_filter": date_posted,
                    "remote_only": remote_only,
                },
            )

        except Exception as e:
            logger.error(f"[JSearch] Discovery failed: {e}")
            raise

    def _extract_company_from_job(self, job: dict) -> Optional[Company]:
        """Extract company information from a JSearch job listing.

        Args:
            job: Job data from JSearch API

        Returns:
            Company object or None if extraction fails
        """
        try:
            employer_name = job.get("employer_name")
            if not employer_name:
                return None

            # Extract company details
            employer_website = job.get("employer_website")
            employer_logo = job.get("employer_logo")

            # Try to infer company size from employer data
            # JSearch doesn't always provide this, so we'll default to UNKNOWN
            company_size = CompanySize.UNKNOWN

            # Extract locations as a list
            locations = []
            if job.get("job_is_remote"):
                locations.append("Remote")
            else:
                city = job.get("job_city")
                state = job.get("job_state")
                country = job.get("job_country")
                if city:
                    locations.append(city)
                elif state:
                    locations.append(state)
                elif country:
                    locations.append(country)

            # Determine industry from job title/description (simplified)
            industry = self._infer_industry(job)

            # Build tech stack from job description/requirements
            tech_stack = self._extract_tech_stack(job)

            # Try to find careers URL (may not always be available)
            careers_url = None
            apply_link = job.get("job_apply_link")
            if apply_link and employer_website and employer_website in apply_link:
                careers_url = apply_link

            return Company(
                name=employer_name,
                website=employer_website,
                careers_url=careers_url,
                industry=industry,
                size=company_size,
                locations=locations,
                tech_stack=tech_stack,
                description=job.get("job_description", "")[:500],  # Truncate
                metadata={
                    "logo_url": employer_logo,
                    "job_title": job.get("job_title"),
                    "posted_date": job.get("job_posted_at_datetime_utc"),
                    "source_job_id": job.get("job_id"),
                },
            )

        except Exception as e:
            logger.warning(f"[JSearch] Failed to extract company from job: {e}")
            return None

    def _infer_industry(self, job: dict) -> IndustryType:
        """Infer industry from job title and description.

        Args:
            job: Job data

        Returns:
            IndustryType (defaults to TECH for now)
        """
        # TODO: Add more sophisticated industry detection
        title = (job.get("job_title") or "").lower()
        description = (job.get("job_description") or "").lower()

        tech_keywords = ["software", "developer", "engineer", "programmer", "data", "ai", "ml"]

        if any(keyword in title or keyword in description for keyword in tech_keywords):
            return IndustryType.TECH

        return IndustryType.OTHER

    def _extract_tech_stack(self, job: dict) -> list[str]:
        """Extract technologies from job description.

        Args:
            job: Job data

        Returns:
            List of technologies mentioned
        """
        description = (job.get("job_description") or "").lower()
        highlights = job.get("job_highlights", {})
        qualifications = highlights.get("Qualifications", [])

        # Common tech keywords to look for
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "node.js",
            "java",
            "c++",
            "go",
            "rust",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "sql",
            "postgresql",
            "mongodb",
            "redis",
            "kafka",
            "tensorflow",
            "pytorch",
        ]

        found_tech = []
        search_text = description + " " + " ".join(qualifications)

        for tech in tech_keywords:
            if tech in search_text:
                found_tech.append(tech)

        return found_tech

    def supported_industries(self) -> list[IndustryType]:
        """Return supported industries.

        JSearch can find jobs in any industry, but we'll focus on tech initially.

        Returns:
            List of supported industries
        """
        return [IndustryType.TECH, IndustryType.OTHER]

    def get_metadata(self) -> dict:
        """Return provider metadata.

        Returns:
            Provider information dictionary
        """
        return {
            "name": self.provider_name,
            "enabled": self.enabled,
            "industries": [ind.value for ind in self.supported_industries()],
            "requires_auth": True,
            "auth_type": "RapidAPI Key",
            "rate_limit": "Unknown (depends on RapidAPI plan)",
            "features": [
                "Real-time job listings",
                "Multiple job boards (Indeed, LinkedIn, etc.)",
                "Remote job filtering",
                "Date posted filtering",
                "Employment type filtering",
            ],
        }
