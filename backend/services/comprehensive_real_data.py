"""
Comprehensive Real Data Integration using Daily Price Index
Fetches actual historical price data from DA Bantay Presyo + DOE fuel prices
"""
import asyncio
from datetime import datetime
from typing import Dict, List
import logging
from services.daily_price_parser import daily_parser
from services.doe_fuel_integration import integrate_doe_fuel_prices

logger = logging.getLogger(__name__)

class ComprehensiveRealDataIntegrator:
    """Comprehensive real data integrator using actual DA price data"""
    
    def __init__(self, db):
        self.db = db
    
    def categorize_item(self, name: str) -> str:
        """Categorize item based on name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['rice', 'bigas', 'milled', 'glutinous', 'basmati', 'premium']):
            return 'rice'
        elif any(word in name_lower for word in ['chicken', 'egg', 'poultry']):
            return 'poultry'
        elif any(word in name_lower for word in ['pork', 'beef', 'carabao', 'meat']):
            return 'meat'
        elif any(word in name_lower for word in ['fish', 'tilapia', 'bangus', 'galunggong', 'alumahan', 'tuna', 'mackerel']):
            return 'fish'
        elif any(word in name_lower for word in ['lettuce', 'cabbage', 'tomato', 'onion', 'potato', 'carrot', 
                                                   'broccoli', 'pechay', 'ampalaya', 'eggplant', 'squash', 
                                                   'sayote', 'chayote', 'mustasa', 'corn']):
            return 'vegetables'
        elif any(word in name_lower for word in ['garlic', 'ginger', 'chili', 'pepper']):
            return 'spices'
        elif any(word in name_lower for word in ['diesel', 'gasoline', 'fuel', 'lpg', 'kerosene']):
            return 'fuel'
        else:
            return 'others'
    
    def get_unit(self, name: str) -> str:
        """Determine unit based on commodity name"""
        name_lower = name.lower()
        if 'egg' in name_lower:
            return 'piece'
        elif any(word in name_lower for word in ['diesel', 'gasoline', 'fuel', 'kerosene']):
            return 'L'
        else:
            return 'kg'
    
    def get_icon(self, category: str) -> str:
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
    
    def determine_status(self, current_price: float, average_price: float) -> str:
        """Determine price status"""
        diff_pct = ((current_price - average_price) / average_price) * 100
        
        if diff_pct < -5:
            return "MURA"
        elif diff_pct > 5:
            return "MAHAL"
        else:
            return "STABLE"
    
    def generate_climate_impact(self, category: str, name: str, trend_direction: str, climate_metrics: Dict = None) -> Dict:
        """Generate climate impact text computed from real WeatherAPI climate_metrics."""
        if not climate_metrics:
            return {
                'level': 'low',
                'factors': ['Climate data unavailable'],
                'forecast': 'Monitor market conditions',
            }

        # Extract real metric values
        def _val(metric_name, default):
            m = climate_metrics.get(metric_name, {})
            return m.get('value', default) if m else default

        temp = _val('Temperature', 28)
        humidity = _val('Humidity', 70)
        rainfall = _val('Rainfall', 0)
        drought_idx = _val('Drought Index', 3)
        uv = _val('UV Index', 7)
        aqi = _val('Air Quality Index', 30)

        # Derive descriptors
        temp_label = 'extreme heat' if temp > 34 else 'high temperature' if temp > 31 else 'warm' if temp > 28 else 'normal temperature'
        rain_label = 'heavy rainfall' if rainfall > 20 else 'moderate rain' if rainfall > 5 else 'light rain' if rainfall > 0 else 'dry conditions'
        drought_label = 'drought conditions' if drought_idx > 6 else 'moderate dry spell' if drought_idx > 3 else 'good soil moisture'
        aqi_label = 'poor air quality' if aqi > 100 else 'moderate air quality' if aqi > 50 else 'good air quality'

        if category == 'vegetables':
            if drought_idx > 5 or (temp > 32 and rainfall == 0):
                level = 'high'
                factors = [f'Drought index {drought_idx:.1f} — soil moisture low', f'{temp:.0f}°C heat stressing crops']
                forecast = 'Limited supply expected; prices may rise'
            elif rainfall > 20:
                level = 'medium'
                factors = [f'{rain_label} ({rainfall:.1f}mm) may damage leafy vegetables', f'{aqi_label}']
                forecast = 'Heavy rain may reduce harvest; monitor supply'
            else:
                level = 'low'
                factors = [f'{temp_label} ({temp:.0f}°C)', f'{rain_label} — {drought_label}']
                forecast = 'Growing conditions stable; supply normal'

        elif category in ('poultry', 'meat'):
            if temp > 33:
                level = 'high'
                factors = [f'Extreme heat ({temp:.0f}°C) causing heat stress', f'Humidity {humidity:.0f}% amplifying stress']
                forecast = 'Heat stress reducing productivity; higher prices likely'
            elif temp > 30:
                level = 'medium'
                factors = [f'High temperature ({temp:.0f}°C) affecting output', f'Humidity {humidity:.0f}%']
                forecast = 'Monitor heat stress impact on production'
            else:
                level = 'low'
                factors = [f'Temperature normal ({temp:.0f}°C)', 'Feed supply stable']
                forecast = 'Production conditions good'

        elif category == 'fish':
            if rainfall > 20 or (uv > 10):
                level = 'medium'
                factors = [f'{rain_label} ({rainfall:.1f}mm) affecting fishing', f'UV index {uv:.0f}']
                forecast = 'Rough conditions may reduce catch; monitor supply'
            else:
                level = 'low'
                factors = [f'{rain_label} — fishing conditions {("favorable" if rainfall < 10 else "acceptable")}', f'{aqi_label}']
                forecast = 'Supply adequate; normal fishing conditions'

        elif category == 'rice':
            if drought_idx > 5:
                level = 'high'
                factors = [f'Drought index {drought_idx:.1f} — irrigation stress', f'{temp:.0f}°C heat']
                forecast = 'Irrigation demand high; watch for supply constraints'
            elif rainfall > 15:
                level = 'medium'
                factors = [f'{rain_label} ({rainfall:.1f}mm) — good for standing crop', 'Flood risk in low-lying areas']
                forecast = 'Adequate water supply; watch for flooding'
            else:
                level = 'low'
                factors = [f'{temp_label} ({temp:.0f}°C)', f'{drought_label}']
                forecast = 'Rice supply stable; normal growing season'

        elif category == 'spices':
            if drought_idx > 4:
                level = 'high' if drought_idx > 6 else 'medium'
                factors = [f'{drought_label} (index {drought_idx:.1f})', f'Low rainfall ({rainfall:.1f}mm) limiting yield']
                forecast = 'Dry conditions constraining spice production; prices may rise'
            else:
                level = 'low'
                factors = [f'{rain_label} — {drought_label}', f'Temperature {temp:.0f}°C suitable']
                forecast = 'Adequate growing conditions for spices'

        else:  # fuel, others
            level = 'low'
            factors = [f'Climate: {temp_label} ({temp:.0f}°C), {rain_label}', 'Market driven by global factors']
            forecast = 'Prices follow global crude and supply chain trends'

        # Override forecast if price trend signals supply issue
        if trend_direction == 'increasing' and level == 'low':
            level = 'medium'
            forecast = f'Prices trending up — {forecast.lower()}'
        elif trend_direction == 'decreasing':
            forecast = f'Prices declining — {forecast.lower()}'

        return {'level': level, 'factors': factors, 'forecast': forecast}
    
    async def fetch_climate_metrics(self) -> Dict:
        """Load current climate metrics from MongoDB into a dict keyed by metric_name."""
        metrics = {}
        async for doc in self.db.climate_metrics.find({}, {"_id": 0, "metric_name": 1, "value": 1, "unit": 1, "status": 1}):
            name = doc.get("metric_name", "")
            if name:
                metrics[name] = doc
        return metrics

    async def integrate_real_data(self, days: int = 7):
        """Integrate real price data from DA Daily Price Index + DOE fuel prices"""
        logger.info(f"Starting real data integration for last {days} days...")

        # Fetch real climate metrics once before the loop
        climate_metrics = await self.fetch_climate_metrics()
        if climate_metrics:
            logger.info(f"Loaded {len(climate_metrics)} climate metrics for impact computation")
        else:
            logger.warning("No climate metrics in DB — climate impact text will be generic")

        # Step 1: Integrate DA Bantay Presyo agricultural commodities
        price_history = await daily_parser.build_price_history(days)
        
        if not price_history:
            logger.error("No price history data available from DA")
        else:
            # Calculate trends
            trends = daily_parser.calculate_trends(price_history)
            logger.info(f"Calculated trends for {len(trends)} agricultural commodities")
            
            # Save agricultural commodities to database
            saved_count = 0
            for commodity, trend_data in trends.items():
                try:
                    category = self.categorize_item(commodity)
                    
                    # Skip if categorized as fuel (will be handled by DOE integration)
                    if category == 'fuel':
                        continue
                    
                    unit = self.get_unit(commodity)
                    
                    current_price = trend_data['current_price']
                    average_price = trend_data['average_price']
                    status = self.determine_status(current_price, average_price)
                    
                    # Prepare document
                    doc = {
                        'name': commodity,
                        'category': category,
                        'currentPrice': current_price,
                        'averagePrice': average_price,
                        'unit': unit,
                        'location': 'NCR',
                        'icon': self.get_icon(category),
                        'status': status,
                        'savings': round(average_price - current_price, 2),
                        'trend': trend_data['trend'],
                        'lastUpdated': datetime.utcnow(),
                        'climateImpact': self.generate_climate_impact(
                            category,
                            commodity,
                            trend_data['trend_direction'],
                            climate_metrics,
                        ),
                        'metadata': {
                            'data_source': 'DA Bantay Presyo Daily Price Index',
                            'trend_direction': trend_data['trend_direction'],
                            'price_change': trend_data['price_change'],
                            'price_change_pct': trend_data['price_change_pct'],
                            'data_points': trend_data['data_points'],
                            'date_range': trend_data['date_range']
                        },
                        'updatedAt': datetime.utcnow()
                    }
                    
                    # Check if exists
                    existing = await self.db.market_items.find_one({'name': commodity})
                    if not existing:
                        doc['createdAt'] = datetime.utcnow()
                    
                    # Upsert
                    await self.db.market_items.update_one(
                        {'name': commodity},
                        {'$set': doc},
                        upsert=True
                    )
                    saved_count += 1
                    logger.info(f"Saved: {commodity} - ₱{current_price} ({status})")
                    
                except Exception as e:
                    logger.error(f"Error saving commodity {commodity}: {str(e)}")
                    continue
            
            logger.info(f"✅ Agricultural commodities integrated: {saved_count} items")
        
        # Step 2: Integrate DOE fuel prices
        fuel_success = await integrate_doe_fuel_prices(self.db)
        
        if fuel_success:
            logger.info("✅ DOE fuel prices integrated successfully")
        else:
            logger.warning("⚠️ DOE fuel price integration failed")
        
        # Return success if at least one source worked
        return (price_history and len(price_history) > 0) or fuel_success

# Export integration function
async def integrate_comprehensive_real_data(db, days=7):
    """Main integration function for comprehensive real data"""
    integrator = ComprehensiveRealDataIntegrator(db)
    return await integrator.integrate_real_data(days)
