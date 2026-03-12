"""
NewsData.io API Integration for Energy and Commodity News (Philippines)
Fetches real-time articles from NewsData.io.

Free tier: 200 calls/day. Each fetch_multiple_queries call makes ~7 API calls.
API key env var: NEWSDATA_API_KEY
"""
import aiohttp
import asyncio
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

NEWSDATA_URL = "https://newsdata.io/api/1/news"

# Queries covering energy AND key commodity prices (rice, pork, fish, onion prices PH)
QUERIES = {
    "renewable_energy":   "renewable energy Philippines",
    "solar_power":        "solar power Philippines",
    "energy_policy":      "energy policy Philippines DOE",
    "grid_updates":       "power grid Philippines NGCP WESM",
    "rice_prices":        "rice prices Philippines supply",
    "onion_garlic_prices": "onion garlic prices Philippines",
    "fuel_prices":        "fuel prices Philippines DOE OIMB",
}


class NewsDataIntegration:
    """Integration with NewsData.io for energy and commodity news"""

    def __init__(self):
        self.base_url = NEWSDATA_URL

    @property
    def api_key(self):
        return os.environ.get("NEWSDATA_API_KEY", "")

    async def fetch_energy_news(
        self,
        query: str = "renewable energy Philippines",
        countries: List[str] = ["ph"],
        categories: List[str] = ["business", "environment"],
        language: str = "en",
    ) -> List[Dict]:
        """Fetch news from NewsData.io. Returns empty list if API key missing or call fails."""
        api_key = self.api_key
        if not api_key:
            logger.warning("NEWSDATA_API_KEY not set — skipping news fetch")
            return []

        params = {
            "apikey": api_key,
            "q": query,
            "country": ",".join(countries),
            "category": ",".join(categories),
            "language": language,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url, params=params, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("results", [])
                        logger.info(f"NewsData query '{query}': {len(articles)} articles")
                        return self._process_articles(articles)
                    body = await response.text()
                    logger.error(f"NewsData API {response.status}: {body[:200]}")
                    return []
        except Exception as e:
            logger.error(f"NewsData fetch error (query='{query}'): {e}")
            return []

    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Normalize article fields."""
        processed = []
        for article in articles[:10]:
            processed.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source_id", ""),
                "url": article.get("link", ""),
                "published": article.get("pubDate", ""),
                "category": "energy_news",
                "keywords": article.get("keywords", []),
            })
        return processed

    async def fetch_multiple_queries(self) -> Dict[str, List[Dict]]:
        """Fetch news for all configured queries concurrently."""
        tasks = {key: self.fetch_energy_news(query=q) for key, q in QUERIES.items()}
        results = {}
        for key, coro in tasks.items():
            results[key] = await coro
            await asyncio.sleep(0.1)  # Avoid rate-limit bursts
        return results


# Singleton instance
news_integration = NewsDataIntegration()
