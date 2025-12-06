"""Direct job link finder for aggregator postings.

This module attempts to find direct application links from job aggregator postings.
When users save/track a job from an aggregator (Indeed, LinkedIn, etc.), this service
tries to find the actual company careers page or application form.

Benefits:
- Bypass aggregator tracking
- Apply directly on company website
- Faster application process
- Better user experience
"""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Common aggregator domains
AGGREGATOR_DOMAINS = {
    "indeed.com",
    "linkedin.com",
    "glassdoor.com",
    "monster.com",
    "ziprecruiter.com",
    "careerbuilder.com",
    "simplyhired.com",
    "snagajob.com",
}

# Common careers page patterns
CAREERS_PATHS = [
    "/careers",
    "/jobs",
    "/join-us",
    "/work-with-us",
    "/opportunities",
    "/employment",
    "/apply",
    "/openings",
]


def is_aggregator(url: str) -> bool:
    """Check if URL is from a job aggregator."""
    try:
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix
        domain = domain.replace("www.", "")
        return any(agg in domain for agg in AGGREGATOR_DOMAINS)
    except Exception:
        return False


def extract_company_website(job_data: Dict) -> Optional[str]:
    """Extract company website from job data.

    Args:
        job_data: Job dictionary containing company info

    Returns:
        Company website URL if found, None otherwise
    """
    # Check if job data has a direct company_url field
    if "company_url" in job_data and job_data["company_url"]:
        return job_data["company_url"]

    # Check in extensions/metadata
    extensions = job_data.get("extensions", [])
    for ext in extensions:
        if isinstance(ext, str) and ext.startswith("http"):
            if not is_aggregator(ext):
                return ext

    return None


def build_careers_urls(company_website: str) -> list[str]:
    """Generate potential careers page URLs for a company website.

    Args:
        company_website: Base company website URL

    Returns:
        List of potential careers page URLs to try
    """
    try:
        parsed = urlparse(company_website)

        # Validate that we have a proper scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            logger.debug(f"Invalid URL format: {company_website}")
            return []

        base = f"{parsed.scheme}://{parsed.netloc}"

        urls = []
        for path in CAREERS_PATHS:
            urls.append(f"{base}{path}")

        # Also try the main website
        urls.insert(0, company_website)

        return urls
    except Exception as e:
        logger.error(f"Error building careers URLs: {e}")
        return []


async def find_direct_link(job_data: Dict, timeout: int = 10) -> Optional[Dict]:
    """Find direct application link for a job posting.

    Args:
        job_data: Job dictionary with at minimum 'link' and 'company' fields
        timeout: HTTP request timeout in seconds

    Returns:
        Dict with 'direct_url' and 'source' if found, None otherwise
    """
    job_link = job_data.get("link", "")

    # If it's not an aggregator, return the link as-is
    if not is_aggregator(job_link):
        return {"direct_url": job_link, "source": "direct", "confidence": "high"}

    # Try to extract company website
    company_website = extract_company_website(job_data)

    if not company_website:
        logger.debug(f"No company website found for {job_data.get('title', 'Unknown')}")
        return None

    # Generate potential careers URLs
    potential_urls = build_careers_urls(company_website)

    # Try to find a working careers page
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in potential_urls:
            try:
                response = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )

                if response.status_code == 200:
                    # Check if page looks like a careers page
                    content = response.text.lower()
                    careers_indicators = [
                        "careers",
                        "jobs",
                        "join our team",
                        "openings",
                        "work with us",
                        "employment",
                        "apply now",
                    ]

                    if any(indicator in content for indicator in careers_indicators):
                        logger.info(f"Found careers page: {url}")
                        return {"direct_url": url, "source": "careers_page", "confidence": "medium"}
            except Exception as e:
                logger.debug(f"Failed to check {url}: {e}")
                continue

    # If we found a company website but no specific careers page
    if company_website:
        return {"direct_url": company_website, "source": "company_homepage", "confidence": "low"}

    return None


async def find_direct_links_batch(jobs: list[Dict], max_concurrent: int = 5) -> Dict[str, Optional[Dict]]:
    """Find direct links for multiple jobs concurrently.

    Args:
        jobs: List of job dictionaries
        max_concurrent: Maximum number of concurrent requests

    Returns:
        Dictionary mapping job IDs to direct link info
    """
    import asyncio

    from app.job_tracker import generate_job_id

    results = {}

    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)

    async def find_with_limit(job):
        async with semaphore:
            job_id = generate_job_id(job)
            try:
                result = await find_direct_link(job)
                return job_id, result
            except Exception as e:
                logger.error(f"Error finding direct link for {job_id}: {e}")
                return job_id, None

    # Process all jobs concurrently (with limit)
    tasks = [find_with_limit(job) for job in jobs]
    completed = await asyncio.gather(*tasks)

    for job_id, result in completed:
        results[job_id] = result

    return results
