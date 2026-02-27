"""
Real Data Integration Service for DA Bantay Presyo
Downloads and processes PDF price reports from DA website
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
import PyPDF2
import io
import re
import logging
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

class DABantayPresyoIntegration:
    """Integration service for DA Bantay Presyo real data"""
    
    def __init__(self, db):
        self.db = db
        self.base_url = "https://www.da.gov.ph/wp-content/uploads"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def download_latest_pdf(self) -> Optional[bytes]:
        """Download the latest weekly average price PDF"""
        # Get today's date
        today = datetime.now()
        
        # Try last 14 days to find available weekly PDF
        for days_ago in range(14):
            check_date = today - timedelta(days=days_ago)
            
            # Try weekly average format first (more structured)
            weekly_url = self._construct_weekly_pdf_url(check_date)
            logger.info(f"Trying to download: {weekly_url}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(weekly_url, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            logger.info(f"Successfully downloaded weekly PDF from {check_date.strftime('%Y-%m-%d')}")
                            return await response.read()
            except Exception as e:
                logger.error(f"Error downloading {weekly_url}: {str(e)}")
                continue
        
        logger.error("Could not find any recent PDF files")
        return None
    
    def _construct_weekly_pdf_url(self, date: datetime) -> str:
        """Construct DA Bantay Presyo Weekly Average PDF URL"""
        # Format: https://www.da.gov.ph/wp-content/uploads/2026/02/Weekly-Average-Prices-February-16-21-2026.pdf
        month_name = date.strftime("%B")
        # Try to find the week containing this date
        # Weekly reports are usually for Sunday-Friday or Monday-Friday
        week_start = date - timedelta(days=date.weekday())  # Monday
        week_end = week_start + timedelta(days=5)  # Friday
        
        return f"{self.base_url}/{date.year}/{date.month:02d}/Weekly-Average-Prices-{month_name}-{week_start.day}-{week_end.day}-{date.year}.pdf"
    
    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return '\\n'.join(text_content)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""
    
    def parse_market_prices(self, text: str) -> List[Dict]:
        """Parse market prices from extracted PDF text (Weekly Average format)"""
        items = []
        
        # Split into lines
        lines = text.split('\\n')
        
        current_commodity = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a commodity name (usually in CAPS or starts with capital)
            # Common patterns: "RICE", "CHICKEN", "PORK", "FISH", "VEGETABLES"
            if line.isupper() and len(line) > 2 and not any(char.isdigit() for char in line):
                current_commodity = line
                continue
            
            # Pattern for item with price
            # Example: "Well Milled Rice 52.00"
            # Example: "Chicken (Whole) Dressed 165.50"
            match = re.match(r'^([A-Za-z\\s\\(\\)\\-/,]+?)\\s+(\\d+\\.\\d+)\\s*$', line)
            if match:
                name = match.group(1).strip()
                price = float(match.group(2))
                
                # Filter out headers and invalid entries
                if price > 1 and len(name) > 2:
                    items.append({
                        'name': name,
                        'price': price,
                        'unit': 'kg',
                        'commodity_group': current_commodity
                    })
                continue
            
            # Pattern for price range
            # Example: "Tomato 92.50-105.00"
            match = re.match(r'^([A-Za-z\\s\\(\\)\\-/,]+?)\\s+(\\d+\\.\\d+)\\s*-\\s*(\\d+\\.\\d+)', line)
            if match:
                name = match.group(1).strip()
                low_price = float(match.group(2))
                high_price = float(match.group(3))
                avg_price = (low_price + high_price) / 2
                
                if avg_price > 1 and len(name) > 2:
                    items.append({
                        'name': name,
                        'price': avg_price,
                        'price_range': {'low': low_price, 'high': high_price},
                        'unit': 'kg',
                        'commodity_group': current_commodity
                    })
        
        # Deduplicate
        unique_items = {}
        for item in items:
            name_key = item['name'].lower()
            if name_key not in unique_items:
                unique_items[name_key] = item
        
        logger.info(f"Found {len(unique_items)} unique items")
        return list(unique_items.values())
    
    def categorize_item(self, name: str) -> str:
        """Categorize item based on name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['lettuce', 'cabbage', 'tomato', 'onion', 'potato', 'carrot', 'broccoli', 'pechay', 'ampalaya', 'eggplant', 'squash', 'celery']):
            return 'vegetables'
        elif any(word in name_lower for word in ['chicken', 'egg']):
            return 'poultry'
        elif any(word in name_lower for word in ['pork', 'beef', 'carabao']):
            return 'meat'
        elif any(word in name_lower for word in ['fish', 'tilapia', 'bangus', 'galunggong', 'alumahan']):
            return 'fish'
        elif any(word in name_lower for word in ['rice', 'bigas']):
            return 'rice'
        elif any(word in name_lower for word in ['garlic', 'ginger', 'chili', 'pepper', 'salt']):
            return 'spices'
        elif any(word in name_lower for word in ['diesel', 'gasoline', 'fuel', 'lpg', 'kerosene']):
            return 'fuel'
        else:
            return 'others'
    
    def determine_status(self, current_price: float, average_price: float) -> str:
        """Determine price status"""
        diff_percent = ((current_price - average_price) / average_price) * 100
        
        if diff_percent < -5:
            return "MURA"
        elif diff_percent > 5:
            return "MAHAL"
        else:
            return "STABLE"
    
    async def process_and_save_data(self, items: List[Dict]):
        """Process parsed items and save to database"""
        saved_count = 0
        
        for item in items:
            try:
                # Get existing item to maintain trend history
                existing = await self.db.market_items.find_one({"name": item['name']})
                
                current_price = item.get('price', 0)
                
                # Calculate average from existing data or use current as baseline
                if existing and 'averagePrice' in existing:
                    average_price = existing['averagePrice']
                else:
                    average_price = current_price * 1.1  # Assume 10% higher average for new items
                
                # Update trend
                trend = existing['trend'][-5:] if existing and 'trend' in existing else []
                trend.append(current_price)
                if len(trend) > 6:
                    trend = trend[-6:]
                
                # Prepare document
                doc = {
                    'name': item['name'],
                    'category': self.categorize_item(item['name']),
                    'currentPrice': current_price,
                    'averagePrice': average_price,
                    'unit': item.get('unit', 'kg'),
                    'location': 'NCR',
                    'icon': self._get_icon(self.categorize_item(item['name'])),
                    'status': self.determine_status(current_price, average_price),
                    'savings': round(average_price - current_price, 2),
                    'trend': trend,
                    'lastUpdated': datetime.utcnow(),
                    'climateImpact': self._generate_climate_impact(item['name']),
                    'updatedAt': datetime.utcnow()
                }
                
                if not existing:
                    doc['createdAt'] = datetime.utcnow()
                
                # Upsert
                await self.db.market_items.update_one(
                    {'name': item['name']},
                    {'$set': doc},
                    upsert=True
                )
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving item {item.get('name')}: {str(e)}")
                continue
        
        logger.info(f"Saved {saved_count} items to database")
        return saved_count
    
    def _get_icon(self, category: str) -> str:
        """Get emoji icon for category"""
        icons = {
            'vegetables': '🥬',
            'poultry': '🍗',
            'meat': '🥩',
            'fish': '🐟',
            'rice': '🍚',
            'spices': '🌶️',
            'fuel': '⛽',
            'others': '📦'
        }
        return icons.get(category, '📦')
    
    def _generate_climate_impact(self, name: str) -> Dict:
        """Generate basic climate impact data"""
        # This would be enhanced with real climate data correlation
        return {
            'level': 'low',
            'factors': ['Normal conditions'],
            'forecast': 'Prices stable'
        }
    
    async def run_full_integration(self):
        """Run complete data integration process"""
        logger.info("Starting DA Bantay Presyo data integration...")
        
        # Download latest PDF
        pdf_bytes = await self.download_latest_pdf()
        if not pdf_bytes:
            logger.error("Failed to download PDF")
            return False
        
        # Extract text
        text = await self.extract_text_from_pdf(pdf_bytes)
        if not text:
            logger.error("Failed to extract text from PDF")
            return False
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        
        # Parse prices
        items = self.parse_market_prices(text)
        logger.info(f"Parsed {len(items)} items")
        
        if len(items) == 0:
            logger.warning("No items found in PDF")
            return False
        
        # Save to database
        saved = await self.process_and_save_data(items)
        
        logger.info(f"Integration complete: {saved} items updated")
        return True

# Integration function to be called from API
async def integrate_real_data():
    """Main integration function"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    integrator = DABantayPresyoIntegration(db)
    result = await integrator.run_full_integration()
    
    client.close()
    return result
