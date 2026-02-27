import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Analytics engine for generating actionable insights from market and climate data"""
    
    def __init__(self):
        self.insights = []
    
    def calculate_price_trends(self, market_items: List[Dict]) -> Dict:
        """Analyze price trends across categories"""
        category_trends = defaultdict(list)
        
        for item in market_items:
            category = item.get('category', 'unknown')
            if 'trend' in item and len(item['trend']) > 0:
                trend_change = item['trend'][-1] - item['trend'][0]
                category_trends[category].append({
                    'item': item['name'],
                    'change': trend_change,
                    'percent_change': (trend_change / item['trend'][0] * 100) if item['trend'][0] > 0 else 0
                })
        
        # Calculate category averages
        insights = {}
        for category, items in category_trends.items():
            avg_change = np.mean([i['percent_change'] for i in items])
            insights[category] = {
                'average_change': round(avg_change, 2),
                'trend': 'increasing' if avg_change > 0 else 'decreasing',
                'item_count': len(items)
            }
        
        return insights
    
    def generate_market_analytics(self, market_items: List[Dict]) -> Dict:
        """Generate comprehensive market analytics with price, supply/demand insights"""
        analytics = {
            'price_summary': self._generate_price_summary(market_items),
            'supply_demand': self._generate_supply_demand_insights(market_items),
            'category_insights': self._generate_category_insights(market_items),
            'price_alerts': self._generate_price_alerts(market_items),
            'top_movers': self._get_top_movers(market_items)
        }
        return analytics
    
    def _generate_price_summary(self, market_items: List[Dict]) -> Dict:
        """Generate price summary statistics"""
        mura_items = [i for i in market_items if i.get('status') == 'MURA']
        mahal_items = [i for i in market_items if i.get('status') == 'MAHAL']
        stable_items = [i for i in market_items if i.get('status') == 'STABLE']
        
        total_savings = sum(i.get('savings', 0) for i in mura_items if i.get('savings', 0) > 0)
        
        return {
            'total_items': len(market_items),
            'mura_count': len(mura_items),
            'mahal_count': len(mahal_items),
            'stable_count': len(stable_items),
            'total_potential_savings': round(total_savings, 2),
            'market_sentiment': 'favorable' if len(mura_items) > len(mahal_items) else 'cautious',
            'price_stability_index': round(len(stable_items) / len(market_items) * 100, 1) if market_items else 0
        }
    
    def _generate_supply_demand_insights(self, market_items: List[Dict]) -> List[Dict]:
        """Generate supply/demand insights based on price movements"""
        insights = []
        
        # Group by category
        categories = defaultdict(list)
        for item in market_items:
            categories[item.get('category', 'other')].append(item)
        
        for category, items in categories.items():
            if len(items) < 2:
                continue
                
            mura_pct = len([i for i in items if i.get('status') == 'MURA']) / len(items) * 100
            mahal_pct = len([i for i in items if i.get('status') == 'MAHAL']) / len(items) * 100
            
            # Determine supply/demand status
            if mura_pct > 50:
                supply_status = 'surplus'
                demand_status = 'low'
                recommendation = f'Good time to buy {category}. Prices are favorable.'
            elif mahal_pct > 50:
                supply_status = 'tight'
                demand_status = 'high'
                recommendation = f'Consider alternatives or wait for better {category} prices.'
            else:
                supply_status = 'balanced'
                demand_status = 'moderate'
                recommendation = f'{category.title()} market is stable. Standard purchasing advised.'
            
            insights.append({
                'category': category,
                'supply_status': supply_status,
                'demand_status': demand_status,
                'mura_percentage': round(mura_pct, 1),
                'mahal_percentage': round(mahal_pct, 1),
                'item_count': len(items),
                'recommendation': recommendation
            })
        
        return sorted(insights, key=lambda x: x['mura_percentage'], reverse=True)
    
    def _generate_category_insights(self, market_items: List[Dict]) -> List[Dict]:
        """Generate detailed category-level insights"""
        categories = defaultdict(list)
        for item in market_items:
            categories[item.get('category', 'other')].append(item)
        
        category_insights = []
        for category, items in categories.items():
            prices = [i.get('currentPrice', 0) for i in items if i.get('currentPrice')]
            avg_price = np.mean(prices) if prices else 0
            
            # Calculate weekly change from trend data
            weekly_changes = []
            for item in items:
                trend = item.get('trend', [])
                if len(trend) >= 2:
                    change = ((trend[-1] - trend[0]) / trend[0] * 100) if trend[0] > 0 else 0
                    weekly_changes.append(change)
            
            avg_weekly_change = np.mean(weekly_changes) if weekly_changes else 0
            
            category_insights.append({
                'category': category,
                'item_count': len(items),
                'average_price': round(avg_price, 2),
                'weekly_change_pct': round(avg_weekly_change, 2),
                'trend_direction': 'up' if avg_weekly_change > 1 else 'down' if avg_weekly_change < -1 else 'stable',
                'best_deal': min(items, key=lambda x: x.get('currentPrice', float('inf'))).get('name') if items else None
            })
        
        return category_insights
    
    def _generate_price_alerts(self, market_items: List[Dict]) -> List[Dict]:
        """Generate price alerts for significant movements"""
        alerts = []
        
        for item in market_items:
            trend = item.get('trend', [])
            if len(trend) < 2:
                continue
            
            # Calculate percentage change
            pct_change = ((trend[-1] - trend[0]) / trend[0] * 100) if trend[0] > 0 else 0
            
            if abs(pct_change) > 10:
                alert_type = 'price_spike' if pct_change > 0 else 'price_drop'
                severity = 'high' if abs(pct_change) > 20 else 'medium'
                
                alerts.append({
                    'item': item.get('name'),
                    'category': item.get('category'),
                    'alert_type': alert_type,
                    'severity': severity,
                    'change_pct': round(pct_change, 1),
                    'current_price': item.get('currentPrice'),
                    'message': f"{item.get('name')} {'increased' if pct_change > 0 else 'decreased'} by {abs(round(pct_change, 1))}%"
                })
        
        return sorted(alerts, key=lambda x: abs(x['change_pct']), reverse=True)[:10]
    
    def _get_top_movers(self, market_items: List[Dict]) -> Dict:
        """Get top gainers and losers"""
        items_with_changes = []
        
        for item in market_items:
            trend = item.get('trend', [])
            if len(trend) >= 2 and trend[0] > 0:
                pct_change = ((trend[-1] - trend[0]) / trend[0] * 100)
                items_with_changes.append({
                    'name': item.get('name'),
                    'category': item.get('category'),
                    'change_pct': round(pct_change, 2),
                    'current_price': item.get('currentPrice'),
                    'status': item.get('status')
                })
        
        sorted_items = sorted(items_with_changes, key=lambda x: x['change_pct'])
        
        return {
            'top_gainers': sorted_items[-5:][::-1],  # Top 5 highest increases
            'top_losers': sorted_items[:5]  # Top 5 biggest decreases
        }
    
    def correlate_climate_to_prices(self, market_items: List[Dict], climate_metrics: List[Dict]) -> List[Dict]:
        """Find correlations between climate conditions and price changes"""
        correlations = []
        
        # Temperature impact on vegetables
        temp_metric = next((m for m in climate_metrics if m['name'] == 'Temperature'), None)
        if temp_metric:
            vegetables = [item for item in market_items if item['category'] == 'vegetables']
            
            if temp_metric['currentValue'] < temp_metric['averageValue']:
                correlations.append({
                    'insight_type': 'climate_correlation',
                    'title': 'Lower Temperatures Supporting Vegetable Prices',
                    'description': f"Current temperature ({temp_metric['currentValue']}°C) is below average, creating favorable conditions for leafy vegetables. This is contributing to lower prices in lettuce, cabbage, and similar items.",
                    'confidence': 0.85,
                    'impact': 'positive',
                    'affected_items': len(vegetables)
                })
        
        # Rainfall impact on rice and agriculture
        rain_metric = next((m for m in climate_metrics if m['name'] == 'Rainfall'), None)
        if rain_metric:
            rice_items = [item for item in market_items if item['category'] == 'rice']
            
            if rain_metric['currentValue'] > rain_metric['averageValue']:
                correlations.append({
                    'insight_type': 'climate_correlation',
                    'title': 'Adequate Rainfall Stabilizing Rice Supply',
                    'description': f"Above-average rainfall ({rain_metric['currentValue']}mm) is improving irrigation conditions, supporting stable rice production and prices.",
                    'confidence': 0.78,
                    'impact': 'positive',
                    'affected_items': len(rice_items)
                })
        
        # UV Index impact on livestock
        uv_metric = next((m for m in climate_metrics if m['name'] == 'UV Index'), None)
        if uv_metric and uv_metric['status'] in ['WARNING', 'ALERT']:
            meat_items = [item for item in market_items if item['category'] in ['meat', 'poultry']]
            correlations.append({
                'insight_type': 'climate_correlation',
                'title': 'High UV Levels May Affect Livestock Prices',
                'description': f"Elevated UV index ({uv_metric['currentValue']}) can cause heat stress in livestock, potentially impacting meat and poultry prices in the coming weeks.",
                'confidence': 0.72,
                'impact': 'warning',
                'affected_items': len(meat_items)
            })
        
        return correlations
    
    def predict_price_movements(self, item: Dict) -> Dict:
        """Predict future price movement based on trends"""
        if 'trend' not in item or len(item['trend']) < 3:
            return {'prediction': 'insufficient_data'}
        
        trend = item['trend']
        
        # Simple linear regression
        x = np.arange(len(trend))
        y = np.array(trend)
        z = np.polyfit(x, y, 1)  # Linear fit
        slope = z[0]
        
        # Predict next value
        next_price = z[0] * len(trend) + z[1]
        
        prediction = {
            'current_price': item['currentPrice'],
            'predicted_next': round(next_price, 2),
            'trend_slope': round(slope, 2),
            'direction': 'increasing' if slope > 0 else 'decreasing',
            'confidence': min(0.9, max(0.5, 1 - abs(slope) / 10))  # Simple confidence
        }
        
        return prediction
    
    def identify_best_buying_opportunities(self, market_items: List[Dict]) -> List[Dict]:
        """Identify items with best value based on price trends and climate factors"""
        opportunities = []
        
        for item in market_items:
            if item['status'] == 'MURA' and item['savings'] > 0:
                # Check if price is still declining
                if len(item['trend']) >= 3:
                    recent_trend = item['trend'][-3:]
                    if recent_trend[0] > recent_trend[-1]:  # Declining
                        
                        # Check climate impact
                        climate_level = item.get('climateImpact', {}).get('level', 'unknown')
                        if climate_level == 'low':
                            opportunities.append({
                                'item': item['name'],
                                'category': item['category'],
                                'current_price': item['currentPrice'],
                                'savings': item['savings'],
                                'recommendation': 'Strong Buy',
                                'reason': f"Price declining with favorable climate conditions. Save ₱{item['savings']}/kg.",
                                'score': round(item['savings'] / item['currentPrice'] * 100, 1)
                            })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:10]  # Top 10
    
    def generate_weekly_report(self, market_items: List[Dict], climate_metrics: List[Dict]) -> Dict:
        """Generate comprehensive weekly analytics report"""
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': '7_days',
            'summary': {}
        }
        
        # Price trends by category
        report['price_trends'] = self.calculate_price_trends(market_items)
        
        # Climate correlations
        report['climate_impacts'] = self.correlate_climate_to_prices(market_items, climate_metrics)
        
        # Best opportunities
        report['buying_opportunities'] = self.identify_best_buying_opportunities(market_items)
        
        # Summary statistics
        mura_count = len([i for i in market_items if i['status'] == 'MURA'])
        mahal_count = len([i for i in market_items if i['status'] == 'MAHAL'])
        
        report['summary'] = {
            'total_items': len(market_items),
            'mura_items': mura_count,
            'mahal_items': mahal_count,
            'avg_savings': round(np.mean([i['savings'] for i in market_items if i['savings'] > 0]), 2),
            'top_category': max(report['price_trends'].items(), key=lambda x: abs(x[1]['average_change']))[0] if report['price_trends'] else 'N/A'
        }
        
        return report

# Initialize analytics engine
analytics_engine = AnalyticsEngine()
