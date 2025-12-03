"""We Work Remotely job provider.

RSS-based job board focused on remote positions in tech.
No authentication required.
"""

import logging
from typing import Any, Dict, List, Optional
from .base import MCPProvider, HTTPX_AVAILABLE, BS4_AVAILABLE

logger = logging.getLogger(__name__)

if BS4_AVAILABLE:
    from bs4 import BeautifulSoup


class WeWorkRemotelyMCP(MCPProvider):
    """We Work Remotely job board - uses RSS feeds."""

    def __init__(self):
        super().__init__("WeWorkRemotely")

    def is_available(self) -> bool:
        """WeWorkRemotely RSS feeds are always available."""
        return True

    def search_jobs(
        self, 
        query: str, 
        count: int = 5, 
        location: Optional[str] = None, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search We Work Remotely jobs via RSS feeds.
        
        Uses category RSS feeds to get job postings. Focuses on programming
        categories for tech jobs.
        
        Args:
            query: Job search query (used for filtering)
            count: Number of jobs to return
            location: Optional location filter (WWR is remote-focused)
            
        Returns:
            List of job dictionaries
        """
        if not HTTPX_AVAILABLE:
            logger.error("httpx not installed")
            return []
            
        try:
            import httpx
            import re
            import defusedxml.ElementTree as ET
            
            # Tech-focused RSS feeds
            categories = [
                "remote-back-end-programming-jobs",
                "remote-front-end-programming-jobs",
                "remote-full-stack-programming-jobs",
                "remote-devops-sysadmin-jobs",
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            
            all_jobs = []
            query_lower = query.lower()
            
            for category in categories:
                try:
                    url = f"https://weworkremotely.com/categories/{category}.rss"
                    resp = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
                    resp.raise_for_status()
                    
                    # Parse RSS XML
                    try:
                        root = ET.fromstring(resp.text)
                    except ET.ParseError as e:
                        logger.warning("Failed to parse RSS XML from %s: %s", url, e)
                        continue
                    
                    # RSS items are in channel -> item
                    for item in root.findall(".//item"):
                        try:
                            title_elem = item.find("title")
                            title = title_elem.text if title_elem is not None and title_elem.text else ""
                            link_elem = item.find("link")
                            link = link_elem.text if link_elem is not None and link_elem.text else ""
                            description_elem = item.find("description")
                            description = description_elem.text if description_elem is not None and description_elem.text else ""
                            pub_date_elem = item.find("pubDate")
                            pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""
                            
                            # Extract company from title (format: "CompanyName: Job Title")
                            company = "Unknown Company"
                            if title and ":" in title:
                                company = title.split(":", 1)[0].strip()
                            
                            # Basic relevance filtering with word boundary matching
                            if query_lower:
                                text_to_search = f"{title} {description}".lower()
                                query_words = query_lower.split()
                                # Use word boundaries for short terms to avoid false positives (e.g., 'Go', 'R', 'UI')
                                if not any(
                                    re.search(rf"\b{re.escape(word)}\b", text_to_search)
                                    for word in query_words
                                ):
                                    continue
                            
                            # Clean HTML from description
                            clean_desc = description
                            if BS4_AVAILABLE:
                                # BeautifulSoup is already imported at module level
                                soup = BeautifulSoup(description, "html.parser")
                                clean_desc = soup.get_text()[:500]
                            
                            # Extract job title (remove company prefix)
                            job_title = title
                            if ":" in title:
                                job_title = title.split(":", 1)[1].strip()
                            
                            all_jobs.append({
                                "title": job_title,
                                "company": company,
                                "location": "Remote",
                                "summary": clean_desc or job_title,
                                "link": link,
                                "source": "WeWorkRemotely",
                                "posted_date": pub_date,
                            })
                            
                        except Exception as item_error:
                            # Skip malformed items, but log for debugging
                            logger.warning(
                                "Failed to parse job item: %s (error: %s)",
                                item.findtext("title", default="(no title)"),
                                item_error
                            )
                            continue
                    
                except Exception as cat_error:
                    # Skip failed categories
                    logger.warning("Category %s failed: %s", category, cat_error)
                    continue
            
            # Return requested count
            return all_jobs[:count]
            
        except Exception as e:
            logger.error("WeWorkRemotely MCP error: %s", e, exc_info=True)
            return []
