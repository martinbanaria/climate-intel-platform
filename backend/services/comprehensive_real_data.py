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
    
    def generate_climate_impact(self, category: str, name: str, trend_direction: str) -> Dict:
        """Generate climate impact based on category and trend"""
        
        # Base impacts by category
        base_impacts = {
            'vegetables': {
                'level': 'low',
                'factors': ['Favorable growing conditions', 'Adequate rainfall'],
                'forecast': 'Supply stable'
            },
            'poultry': {
                'level': 'medium',
                'factors': ['Heat affecting production', 'Feed costs variable'],
                'forecast': 'Monitor temperature impact'
            },
            'meat': {
                'level': 'medium',
                'factors': ['Heat stress concerns', 'Feed availability good'],
                'forecast': 'Watch for heat waves'
            },
            'fish': {
                'level': 'low',
                'factors': ['Good fishing conditions', 'Water quality stable'],
                'forecast': 'Supply adequate'
            },
            'rice': {
                'level': 'low',
                'factors': ['Post-harvest season', 'Good irrigation'],
                'forecast': 'Stable supply'
            },
            'spices': {
                'level': 'medium',
                'factors': ['Variable weather impact'],
                'forecast': 'Supply dependent on rainfall'
            },
            'fuel': {
                'level': 'low',
                'factors': ['Global market stable'],
                'forecast': 'Prices stable'
            }
        }
        
        impact = base_impacts.get(category, {
            'level': 'low',
            'factors': ['Normal conditions'],
            'forecast': 'Stable'
        })
        
        # Adjust based on trend
        if trend_direction == 'increasing':
            if 'garlic' in name.lower():
                impact['level'] = 'high'
                impact['factors'] = ['Drought reducing yield', 'Heat damage']
                impact['forecast'] = 'Limited supply driving prices up'
        elif trend_direction == 'decreasing':
            impact['factors'].append('Good harvest')
            impact['forecast'] = 'Abundant supply, prices declining'
        
        return impact
    
    async def integrate_real_data(self, days: int = 7):
        """Integrate real price data from DA Daily Price Index + DOE fuel prices"""
        logger.info(f"Starting real data integration for last {days} days...")
        
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
                            trend_data['trend_direction']
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
