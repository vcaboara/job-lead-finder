#!/usr/bin/env python3

import argparse
import logging
import sys
import time
from typing import Dict, List, Optional

from duckduckgo_search import DDGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SearchProvider:
    """Base class for search providers."""

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Execute search and return standardized results."""
        raise NotImplementedError


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider."""

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search using DuckDuckGo API."""
        logger.debug("Searching DuckDuckGo for: %s", query)

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        # Standardize result format
        standardized = []
        for r in results:
            standardized.append(
                {
                    "url": r.get("href", "N/A"),
                    "title": r.get("title", "N/A"),
                    "snippet": r.get("body", "N/A"),
                }
            )

        logger.debug("Found %d results", len(standardized))
        return standardized


# Future providers can be added here:
# class GoogleProvider(SearchProvider):
#     def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
#         # Use Google Custom Search API
#         pass
#
# class BingProvider(SearchProvider):
#     def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
#         # Use Bing Search API
#         pass


def get_search_provider(provider: str = "duckduckgo") -> SearchProvider:
    """Factory function to get search provider instance."""
    providers = {
        "duckduckgo": DuckDuckGoProvider,
        # "google": GoogleProvider,
        # "bing": BingProvider,
    }

    if provider not in providers:
        raise ValueError(f"Unsupported search provider: {provider}. Available: {list(providers.keys())}")

    return providers[provider]()


def search_with_retry(
    query: str, max_results: int = 10, max_retries: int = 3, provider: str = "duckduckgo"
) -> List[Dict[str, str]]:
    """
    Search using specified provider with retry mechanism.

    Args:
        query: Search query
        max_results: Maximum number of results to return
        max_retries: Maximum number of retry attempts
        provider: Search provider to use (default: duckduckgo)

    Returns:
        List of search results with standardized format
    """
    search_provider = get_search_provider(provider)

    for attempt in range(max_retries):
        try:
            logger.info("Searching for: %s (attempt %d/%d)", query, attempt + 1, max_retries)

            results = search_provider.search(query, max_results)

            if not results:
                logger.warning("No results found")
                return []

            logger.info("Found %d results", len(results))
            return results

        except Exception as e:
            logger.error("Attempt %d/%d failed: %s", attempt + 1, max_retries, str(e))
            if attempt < max_retries - 1:
                logger.debug("Waiting 1 second before retry...")
                time.sleep(1)
            else:
                logger.error("All %d attempts failed", max_retries)
                raise


def format_results(results: List[Dict[str, str]]) -> None:
    """Format and print search results to stdout."""
    for i, r in enumerate(results, 1):
        print(f"\n=== Result {i} ===")
        print(f"URL: {r['url']}")
        print(f"Title: {r['title']}")
        print(f"Snippet: {r['snippet']}")


def search(
    query: str, max_results: int = 10, max_retries: int = 3, provider: str = "duckduckgo"
) -> Optional[List[Dict[str, str]]]:
    """
    Main search function that handles search with retry mechanism.

    Args:
        query: Search query
        max_results: Maximum number of results to return
        max_retries: Maximum number of retry attempts
        provider: Search provider to use

    Returns:
        List of search results or None on failure
    """
    try:
        results = search_with_retry(query, max_results, max_retries, provider)
        if results:
            format_results(results)
        return results

    except Exception as e:
        logger.error("Search failed: %s", str(e), exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Search the web using various search providers")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results (default: 10)")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retry attempts (default: 3)")
    parser.add_argument(
        "--provider",
        choices=["duckduckgo"],  # Add more as implemented: "google", "bing"
        default="duckduckgo",
        help="Search provider to use (default: duckduckgo)",
    )

    args = parser.parse_args()
    search(args.query, args.max_results, args.max_retries, args.provider)


if __name__ == "__main__":
    main()
