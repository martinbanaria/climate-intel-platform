import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebCrawler:
    """Web crawler for scraping market price data from various sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_url(self, url: str) -> Optional[str]:
        """Scrape content from a given URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return html
                    else:
                        logger.error(f"Failed to scrape {url}: Status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    async def extract_market_data(self, html: str, source_type: str = "da_bantay_presyo") -> List[Dict]:
        """Extract market data from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        market_data = []
        
        # Different parsing logic based on source
        if source_type == "da_bantay_presyo":
            # Parse DA Bantay Presyo format
            # This would need to be customized based on actual website structure
            items = soup.find_all('div', class_='market-item')  # Example selector
            for item in items:
                try:
                    data = {
                        'name': item.find('h3').text.strip() if item.find('h3') else None,
                        'price': float(item.find('span', class_='price').text.strip()) if item.find('span', class_='price') else None,
                        'unit': item.find('span', class_='unit').text.strip() if item.find('span', class_='unit') else 'kg',
                        'scraped_at': datetime.utcnow().isoformat()
                    }
                    if data['name'] and data['price']:
                        market_data.append(data)
                except Exception as e:
                    logger.error(f"Error parsing item: {str(e)}")
                    continue
        
        return market_data
    
    async def scrape_pagasa_climate_data(self, url: str = "https://www.pagasa.dost.gov.ph/") -> Dict:
        """Scrape climate data from PAGASA website"""
        html = await self.scrape_url(url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        climate_data = {
            'temperature': None,
            'rainfall': None,
            'humidity': None,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        # Parse PAGASA data - customize based on actual structure
        try:
            # Example parsing logic
            temp_element = soup.find('div', {'id': 'temperature'})
            if temp_element:
                climate_data['temperature'] = float(temp_element.text.strip())
        except Exception as e:
            logger.error(f"Error parsing PAGASA data: {str(e)}")
        
        return climate_data
    
    async def scrape_multiple_sources(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs concurrently"""
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

# Initialize crawler
crawler = WebCrawler()
