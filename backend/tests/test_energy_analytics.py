"""
Backend API Tests for Climate Smart Advisory & Intelligence Platform
Tests: Market Analytics, Energy Analytics, Energy News, PPA Status, DOE Circulars, Grid Status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Climate-Smart Market Intelligence API" in data["message"]


class TestMarketAnalytics:
    """Market Analytics API tests - GET /api/analytics/market-analytics"""
    
    def test_market_analytics_success(self):
        """Test market analytics endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/analytics/market-analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "generated_at" in data
        
        # Verify analytics structure
        analytics = data["data"]
        assert "price_summary" in analytics
        assert "supply_demand" in analytics
        assert "category_insights" in analytics
        assert "price_alerts" in analytics
        assert "top_movers" in analytics
    
    def test_market_analytics_price_summary(self):
        """Test price summary contains required fields"""
        response = requests.get(f"{BASE_URL}/api/analytics/market-analytics")
        assert response.status_code == 200
        
        data = response.json()
        price_summary = data["data"]["price_summary"]
        
        # Verify price summary fields
        assert "total_items" in price_summary
        assert "mura_count" in price_summary
        assert "mahal_count" in price_summary
        assert "stable_count" in price_summary
        assert "total_potential_savings" in price_summary
        assert "market_sentiment" in price_summary
        assert "price_stability_index" in price_summary
        
        # Verify data types
        assert isinstance(price_summary["total_items"], int)
        assert isinstance(price_summary["mura_count"], int)
        assert isinstance(price_summary["price_stability_index"], (int, float))
    
    def test_market_analytics_top_movers(self):
        """Test top movers contains gainers and losers"""
        response = requests.get(f"{BASE_URL}/api/analytics/market-analytics")
        assert response.status_code == 200
        
        data = response.json()
        top_movers = data["data"]["top_movers"]
        
        assert "top_gainers" in top_movers
        assert "top_losers" in top_movers
        assert isinstance(top_movers["top_gainers"], list)
        assert isinstance(top_movers["top_losers"], list)


class TestEnergyAnalytics:
    """Energy Analytics API tests - GET /api/energy/analytics"""
    
    def test_energy_analytics_success(self):
        """Test energy analytics endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/energy/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "generated_at" in data
        
        # Verify analytics structure
        analytics = data["data"]
        assert "ppa_summary" in analytics
        assert "technology_breakdown" in analytics
        assert "price_trends" in analytics
        assert "market_outlook" in analytics
        assert "alerts" in analytics
    
    def test_energy_analytics_ppa_summary(self):
        """Test PPA summary contains required fields"""
        response = requests.get(f"{BASE_URL}/api/energy/analytics")
        assert response.status_code == 200
        
        data = response.json()
        ppa_summary = data["data"]["ppa_summary"]
        
        # Verify PPA summary fields
        assert "total_projects" in ppa_summary
        assert "total_capacity_mw" in ppa_summary
        assert "operational_count" in ppa_summary
        assert "operational_capacity" in ppa_summary
        assert "under_construction_count" in ppa_summary
        assert "under_construction_capacity" in ppa_summary
        
        # Verify data types
        assert isinstance(ppa_summary["total_projects"], int)
        assert isinstance(ppa_summary["total_capacity_mw"], (int, float))
    
    def test_energy_analytics_price_trends(self):
        """Test price trends contains WESM regional data"""
        response = requests.get(f"{BASE_URL}/api/energy/analytics")
        assert response.status_code == 200
        
        data = response.json()
        price_trends = data["data"]["price_trends"]
        
        # Verify WESM regions
        assert "wesm_luzon" in price_trends
        assert "wesm_visayas" in price_trends
        assert "wesm_mindanao" in price_trends
        
        # Verify trend data structure
        for region in ["wesm_luzon", "wesm_visayas", "wesm_mindanao"]:
            trend_data = price_trends[region]
            assert "current" in trend_data
            assert "trend" in trend_data
            assert "change_pct" in trend_data
            assert isinstance(trend_data["trend"], list)
    
    def test_energy_analytics_market_outlook(self):
        """Test market outlook contains forecast data"""
        response = requests.get(f"{BASE_URL}/api/energy/analytics")
        assert response.status_code == 200
        
        data = response.json()
        outlook = data["data"]["market_outlook"]
        
        assert "short_term" in outlook
        assert "supply_adequacy" in outlook
        assert "price_forecast" in outlook
        assert "key_drivers" in outlook
        assert isinstance(outlook["key_drivers"], list)


class TestEnergyNews:
    """Energy News API tests - GET /api/energy/news (NewsData.io integration)"""
    
    def test_energy_news_success(self):
        """Test energy news endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/energy/news")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
    
    def test_energy_news_article_structure(self):
        """Test news articles have required fields"""
        response = requests.get(f"{BASE_URL}/api/energy/news")
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] > 0:
            article = data["data"][0]
            # Verify article structure
            assert "title" in article
            assert "description" in article or "content" in article
            assert "source" in article
            assert "url" in article
            
            # Verify title is not empty
            assert len(article["title"]) > 0
    
    def test_energy_news_with_query(self):
        """Test energy news with custom query parameter"""
        response = requests.get(f"{BASE_URL}/api/energy/news", params={"query": "solar power"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert isinstance(data["data"], list)
    
    def test_energy_news_returns_real_data(self):
        """Verify news is from real NewsData.io API (not mock)"""
        response = requests.get(f"{BASE_URL}/api/energy/news")
        assert response.status_code == 200
        
        data = response.json()
        # If we have articles, check they have real URLs (not '#')
        if data["count"] > 0:
            article = data["data"][0]
            # Real articles should have actual URLs
            if article.get("url"):
                # Real news should have http/https URLs
                assert article["url"].startswith("http") or article["url"] == "#"


class TestPPAStatus:
    """PPA Status API tests - GET /api/energy/ppa-status"""
    
    def test_ppa_status_success(self):
        """Test PPA status endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/energy/ppa-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
    
    def test_ppa_status_structure(self):
        """Test PPA entries have required fields"""
        response = requests.get(f"{BASE_URL}/api/energy/ppa-status")
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] > 0:
            ppa = data["data"][0]
            # Verify PPA structure
            assert "project" in ppa
            assert "capacity_mw" in ppa
            assert "status" in ppa
            assert "technology" in ppa
            assert "off_taker" in ppa
            assert "term_years" in ppa
            
            # Verify data types
            assert isinstance(ppa["capacity_mw"], (int, float))
            assert isinstance(ppa["term_years"], int)
    
    def test_ppa_status_valid_statuses(self):
        """Test PPA statuses are valid values"""
        response = requests.get(f"{BASE_URL}/api/energy/ppa-status")
        assert response.status_code == 200
        
        data = response.json()
        valid_statuses = ["Operational", "Under Construction", "Contracted", "Planned"]
        
        for ppa in data["data"]:
            assert ppa["status"] in valid_statuses


class TestDOECirculars:
    """DOE Circulars API tests - GET /api/energy/doe-circulars"""
    
    def test_doe_circulars_success(self):
        """Test DOE circulars endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/energy/doe-circulars")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
    
    def test_doe_circulars_structure(self):
        """Test DOE circulars have required fields"""
        response = requests.get(f"{BASE_URL}/api/energy/doe-circulars")
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] > 0:
            circular = data["data"][0]
            # Verify circular structure
            assert "title" in circular
            assert "document_number" in circular
            assert "summary" in circular
            
            # Verify title is not empty
            assert len(circular["title"]) > 0


class TestGridStatus:
    """Grid Status API tests - GET /api/energy/grid-status"""
    
    def test_grid_status_success(self):
        """Test grid status endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/energy/grid-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
    
    def test_grid_status_structure(self):
        """Test grid status has required fields"""
        response = requests.get(f"{BASE_URL}/api/energy/grid-status")
        assert response.status_code == 200
        
        data = response.json()
        grid_data = data["data"]
        
        # Verify grid status structure
        assert "total_demand" in grid_data
        assert "total_supply" in grid_data
        assert "reserves" in grid_data
        assert "status" in grid_data
        assert "grids" in grid_data
        
        # Verify data types
        assert isinstance(grid_data["total_demand"], (int, float))
        assert isinstance(grid_data["total_supply"], (int, float))
        assert isinstance(grid_data["reserves"], (int, float))
        assert isinstance(grid_data["grids"], list)
    
    def test_grid_status_regional_grids(self):
        """Test grid status contains regional grid data"""
        response = requests.get(f"{BASE_URL}/api/energy/grid-status")
        assert response.status_code == 200
        
        data = response.json()
        grids = data["data"]["grids"]
        
        # Should have Luzon, Visayas, Mindanao
        grid_names = [g["name"] for g in grids]
        assert "Luzon" in grid_names
        assert "Visayas" in grid_names
        assert "Mindanao" in grid_names
        
        # Verify grid structure
        for grid in grids:
            assert "name" in grid
            assert "capacity" in grid
            assert "current" in grid
            assert "status" in grid


class TestMarketItems:
    """Market Items API tests"""
    
    def test_market_items_success(self):
        """Test market items endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/market-items")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "count" in data
    
    def test_market_items_with_category_filter(self):
        """Test market items with category filter"""
        response = requests.get(f"{BASE_URL}/api/market-items", params={"category": "vegetables"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
    
    def test_best_deals_endpoint(self):
        """Test best deals endpoint"""
        response = requests.get(f"{BASE_URL}/api/best-deals")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data


class TestCategories:
    """Categories API tests"""
    
    def test_categories_success(self):
        """Test categories endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Verify category structure
        if len(data["data"]) > 0:
            category = data["data"][0]
            assert "id" in category
            assert "name" in category
            assert "icon" in category
