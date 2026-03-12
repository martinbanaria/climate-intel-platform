"""
Tests for Market Items API endpoints.
GET /api/market-items
GET /api/market-items/{item_id}
GET /api/best-deals
GET /api/categories
GET /api/analytics/price-trends
GET /api/analytics/buying-opportunities
GET /api/analytics/climate-correlations
GET /api/analytics/weekly-report
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestMarketItemsExtended:
    """Extended market items tests beyond test_energy_analytics.py"""

    def test_market_items_count(self):
        """Should have 215+ items from DA Bantay Presyo (use high limit)."""
        response = requests.get(f"{BASE_URL}/api/market-items", params={"limit": 300})
        data = response.json()
        assert data["count"] >= 200

    def test_market_items_structure(self):
        """Each item should have core fields."""
        response = requests.get(f"{BASE_URL}/api/market-items")
        data = response.json()
        if data["count"] > 0:
            item = data["data"][0]
            assert "name" in item
            assert "category" in item
            assert "unit" in item

    def test_market_items_search(self):
        """Test search parameter filtering."""
        response = requests.get(f"{BASE_URL}/api/market-items", params={"search": "rice"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_market_items_limit(self):
        """Test limit parameter."""
        response = requests.get(f"{BASE_URL}/api/market-items", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5

    def test_market_items_by_id(self):
        """Fetch a single item by ID."""
        # Get a valid ID first
        response = requests.get(f"{BASE_URL}/api/market-items", params={"limit": 1})
        data = response.json()
        if data["count"] > 0:
            item_id = data["data"][0].get("_id") or data["data"][0].get("id")
            if item_id:
                response2 = requests.get(f"{BASE_URL}/api/market-items/{item_id}")
                assert response2.status_code == 200


class TestAnalyticsEndpoints:
    """Analytics endpoints beyond what test_energy_analytics.py covers."""

    def test_price_trends_by_category(self):
        """Price trends should break down by category."""
        response = requests.get(f"{BASE_URL}/api/analytics/price-trends")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should have category-level trend data
        assert "data" in data

    def test_climate_correlations(self):
        response = requests.get(f"{BASE_URL}/api/analytics/climate-correlations")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_buying_opportunities(self):
        response = requests.get(f"{BASE_URL}/api/analytics/buying-opportunities")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_weekly_report(self):
        response = requests.get(f"{BASE_URL}/api/analytics/weekly-report")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        report = data["data"]
        assert "summary" in report
        assert "period" in report

    def test_predict_endpoint(self):
        """Price prediction endpoint — uses item_id as path param."""
        # Get a valid item ID
        response = requests.get(f"{BASE_URL}/api/market-items", params={"limit": 1})
        data = response.json()
        if data["count"] > 0:
            item_id = data["data"][0].get("_id") or data["data"][0].get("id")
            if item_id:
                response2 = requests.get(f"{BASE_URL}/api/analytics/predict/{item_id}")
                assert response2.status_code == 200
