"""
NewsData.io API Integration for Energy News
Fetches real-time energy news articles from NewsData.io
"""
import aiohttp
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NewsDataIntegration:
    """Integration with NewsData.io for energy news"""
    
    def __init__(self):
        self.base_url = "https://newsdata.io/api/1/news"
    
    @property
    def api_key(self):
        """Lazy load API key from environment"""
        return os.environ.get('NEWSDATA_API_KEY', '')
        
    async def fetch_energy_news(
        self, 
        query: str = "renewable energy",
        countries: List[str] = ["ph"],
        categories: List[str] = ["business", "environment"],
        language: str = "en"
    ) -> List[Dict]:
        """Fetch energy news from NewsData.io"""
        
        api_key = self.api_key
        if not api_key:
            logger.warning("NEWSDATA_API_KEY not configured, using mock data")
            return self._get_mock_news()
        
        params = {
            'apikey': api_key,
            'q': query,
            'country': ','.join(countries),
            'category': ','.join(categories),
            'language': language
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('results', [])
                        logger.info(f"Fetched {len(articles)} energy news articles")
                        return self._process_articles(articles)
                    else:
                        error_text = await response.text()
                        logger.error(f"NewsData.io API error: {response.status} - {error_text}")
                        return self._get_mock_news()
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return self._get_mock_news()
    
    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process and structure news articles"""
        processed = []
        for article in articles[:10]:  # Limit to 10 articles
            processed.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'source': article.get('source_id', ''),
                'url': article.get('link', ''),
                'published': article.get('pubDate', ''),
                'category': 'energy_news',
                'keywords': article.get('keywords', [])
            })
        return processed
    
    def _get_mock_news(self) -> List[Dict]:
        """Return mock energy news for development"""
        return [
            {
                'title': 'Philippines Renewable Energy Capacity Reaches 10 GW',
                'description': 'The Philippines has reached a milestone of 10 gigawatts in renewable energy capacity, driven by solar and wind projects.',
                'source': 'DOE Energy Portal',
                'url': '#',
                'published': datetime.utcnow().isoformat(),
                'category': 'renewable_energy'
            },
            {
                'title': 'New Solar Farm in Negros to Generate 150 MW',
                'description': 'A new 150 MW solar farm in Negros Occidental is set to begin operations, adding significant capacity to the Visayas grid.',
                'source': 'Energy Philippines',
                'url': '#',
                'published': datetime.utcnow().isoformat(),
                'category': 'solar_power'
            },
            {
                'title': 'DOE Approves New Wind Energy Projects',
                'description': 'The Department of Energy has approved three new wind energy projects totaling 450 MW capacity.',
                'source': 'BusinessWorld',
                'url': '#',
                'published': datetime.utcnow().isoformat(),
                'category': 'wind_power'
            }
        ]
    
    async def fetch_multiple_queries(self) -> Dict[str, List[Dict]]:
        """Fetch news for multiple energy-related queries"""
        queries = {
            'renewable_energy': 'renewable energy Philippines',
            'solar_power': 'solar power Philippines',
            'energy_policy': 'energy policy Philippines',
            'grid_updates': 'power grid Philippines'
        }
        
        results = {}
        for key, query in queries.items():
            articles = await self.fetch_energy_news(query=query)
            results[key] = articles
        
        return results

# Singleton instance
news_integration = NewsDataIntegration()
