import asyncio
import os
from typing import Any, Dict, List

import aiohttp
from ai_services.ai_provider_factory import AIProviderFactory
from config import Config


class CompanyIntelligenceFinder:
    """
    Searches for companies and investors based on strategic criteria (e.g., ESG, specific technologies)
    by querying news APIs and analyzing results with an LLM.
    """

    def __init__(self, search_profile: str, api_key: str = None):
        """
        Initializes the finder with a specific search profile.

        Args:
            search_profile (str): A descriptive name for the search criteria (e.g., "ESG Leaders").
            api_key (str, optional): NewsAPI key. Defaults to NEWS_API_KEY from environment.
        """
        self.search_profile = search_profile
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY environment variable not set.")

        self.news_api_url = "https://newsapi.org/v2/everything"
        self.ai_provider = AIProviderFactory.get_provider()

    async def _search_news(
        self, query: str, sources: str = "business-insider,reuters,bloomberg"
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously searches for news articles using the NewsAPI.

        Args:
            query (str): The search query.
            sources (str): Comma-separated list of news sources.

        Returns:
            List[Dict[str, Any]]: A list of articles from the API response.
        """
        params = {
            "q": query,
            "sources": sources,
            "language": "en",
            "sortBy": "relevancy",
            "apiKey": self.api_key,
            "pageSize": 20,  # Limit to a reasonable number for analysis
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.news_api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("articles", [])
                else:
                    print(f"Error fetching news: {response.status} {await response.text()}")
                    return []

    async def _analyze_article_content(self, article_content: str, analysis_prompt: str) -> Dict[str, Any]:
        """
        Uses an AI provider to analyze article content based on a prompt.
        """
        system_prompt = (
            "You are an expert financial and technology analyst. "
            "Analyze the provided text and extract structured information based on the user's request. "
            "Respond only in JSON format."
        )

        full_prompt = f"{analysis_prompt}\n\n--- Article Content ---\n{article_content}"

        try:
            response = await self.ai_provider.generate(
                system_prompt=system_prompt,
                prompt=full_prompt,
                model=Config.get("fast_llm_model"),  # Use a fast model for analysis
                json_mode=True,
            )
            return response
        except Exception as e:
            # If the AI fails to generate valid JSON or another error occurs,
            # return a non-match structure to prevent crashes.
            print(f"Error analyzing article content: {e}")
            return {"is_match": False, "error": str(e)}

    async def find_opportunities(self, query: str, analysis_prompt: str) -> List[Dict[str, Any]]:
        """
        Main method to find and analyze opportunities.

        Args:
            query (str): The high-level search query for the news API.
            analysis_prompt (str): The detailed prompt for the LLM to analyze each article.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a potential opportunity.
        """
        print(f"Searching for opportunities with query: '{query}'")
        articles = await self._search_news(query)

        if not articles:
            print("No relevant articles found.")
            return []

        print(f"Found {len(articles)} articles. Analyzing with AI...")

        analysis_tasks = []
        for article in articles:
            content = article.get("content") or article.get("description", "")
            if content:
                task = self._analyze_article_content(content, analysis_prompt)
                analysis_tasks.append(task)

        results = await asyncio.gather(*analysis_tasks)

        # Filter out non-matching results and add article source
        opportunities = []
        for i, res in enumerate(results):
            if isinstance(res, dict) and res.get("is_match", False):
                res["source_url"] = articles[i].get("url")
                res["source_title"] = articles[i].get("title")
                opportunities.append(res)

        print(f"Identified {len(opportunities)} potential opportunities.")
        return opportunities
