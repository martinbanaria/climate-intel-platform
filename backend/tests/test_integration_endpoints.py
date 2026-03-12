"""
Tests for Integration trigger endpoints and status.
POST /api/integration/run-weather-update
POST /api/integration/run-doe-update
GET  /api/integration/status
GET  /api/health
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestHealthEndpoint:
    """GET /api/health — server health + MongoDB diagnostics"""

    def test_health_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200

    def test_health_structure(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data["status"] == "ok"
        assert "mongodb" in data
        assert data["mongodb"] == "connected"

    def test_health_env_diagnostics(self):
        """Health should report API key availability (added in a108a82)."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        # These fields were added for debugging Render env
        if "weatherapi_key_set" in data:
            assert isinstance(data["weatherapi_key_set"], bool)
        if "newsdata_key_set" in data:
            assert isinstance(data["newsdata_key_set"], bool)


class TestIntegrationStatus:
    """GET /api/integration/status"""

    def test_status_success(self):
        response = requests.get(f"{BASE_URL}/api/integration/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_status_has_item_count(self):
        response = requests.get(f"{BASE_URL}/api/integration/status")
        data = response.json()
        assert "total_items" in data or "data" in data


class TestWeatherUpdate:
    """POST /api/integration/run-weather-update"""

    def test_weather_update_endpoint_exists(self):
        """Endpoint should be registered and respond (success depends on API key)."""
        response = requests.post(f"{BASE_URL}/api/integration/run-weather-update")
        # 200 if key present, 500 if missing — either way, not 404
        assert response.status_code != 404

    def test_weather_update_returns_json(self):
        response = requests.post(f"{BASE_URL}/api/integration/run-weather-update")
        data = response.json()
        assert "success" in data


class TestDOEUpdate:
    """POST /api/integration/run-doe-update"""

    def test_doe_update_endpoint_exists(self):
        response = requests.post(f"{BASE_URL}/api/integration/run-doe-update")
        assert response.status_code != 404

    def test_doe_update_returns_json(self):
        response = requests.post(
            f"{BASE_URL}/api/integration/run-doe-update",
            timeout=180,
        )
        data = response.json()
        assert "success" in data
