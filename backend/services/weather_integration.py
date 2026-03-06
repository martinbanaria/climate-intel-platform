"""
WeatherAPI.com integration for Climate Intel.
Replaces mock climate_metrics in MongoDB with real weather data for the Philippines.
Commercial use permitted on WeatherAPI free tier (1M calls/month).

Fetches current conditions for Manila (NCR) and updates 8 climate metric documents:
  Temperature, Rainfall, Air Quality Index, Humidity, UV Index,
  Soil Moisture (derived), Drought Index (derived), Wind Speed
"""

import aiohttp
import asyncio
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY", "")
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"

# Philippine location used for all climate metrics
PH_LOCATION = "Manila,Philippines"

# Maps WeatherAPI EPA AQI category (1-6) → estimated AQI value
EPA_TO_AQI = {1: 25, 2: 75, 3: 125, 4: 175, 5: 250, 6: 350}


# ──────────────────────────────────────────────
# Status helpers
# ──────────────────────────────────────────────


def _temp_status(val: float) -> str:
    if val > 38:
        return "CRITICAL"
    if val > 36:
        return "WARNING"
    if val > 33:
        return "MODERATE"
    return "GOOD"


def _rainfall_status(val: float) -> str:
    if val > 100:
        return "WARNING"  # Heavy rain — flooding risk
    if val > 50:
        return "MODERATE"
    return "GOOD"


def _aqi_status(val: float) -> str:
    if val > 200:
        return "CRITICAL"
    if val > 100:
        return "WARNING"
    if val > 50:
        return "MODERATE"
    return "GOOD"


def _humidity_status(val: float) -> str:
    if val > 90:
        return "WARNING"
    if val > 80:
        return "MODERATE"
    return "GOOD"


def _uv_status(val: float) -> str:
    if val > 10:
        return "CRITICAL"
    if val > 7:
        return "WARNING"
    if val > 5:
        return "MODERATE"
    return "GOOD"


def _soil_status(val: float) -> str:
    if val < 15 or val > 65:
        return "WARNING"
    if val < 22 or val > 50:
        return "MODERATE"
    return "GOOD"


def _drought_status(val: float) -> str:
    if val > 4:
        return "CRITICAL"
    if val > 3:
        return "WARNING"
    if val > 2:
        return "MODERATE"
    return "GOOD"


def _wind_status(val: float) -> str:
    if val > 60:
        return "CRITICAL"
    if val > 40:
        return "WARNING"
    if val > 30:
        return "MODERATE"
    return "GOOD"


# ──────────────────────────────────────────────
# Recommendation + impact text
# ──────────────────────────────────────────────


def _temp_text(val: float):
    if val > 36:
        return (
            "Extreme heat advisory. Limit outdoor exposure, keep crops watered.",
            "High temperatures stress leafy vegetables and livestock, driving prices up.",
        )
    if val > 33:
        return (
            "Hot conditions. Early morning farming activities recommended.",
            "Heat stress reduces yield of temperature-sensitive crops like lettuce and cabbage.",
        )
    return (
        "Comfortable temperature range. Good conditions for outdoor farming.",
        "Favorable temperatures support stable crop yields and steady market prices.",
    )


def _rainfall_text(val: float):
    if val > 100:
        return (
            "Heavy rainfall alert. Risk of flooding in low-lying farms.",
            "Excessive rain damages root crops and disrupts supply chain — expect price spikes.",
        )
    if val > 50:
        return (
            "Significant rainfall. Monitor drainage in farm areas.",
            "High rainfall may affect harvest operations but supports soil water reserves.",
        )
    if val < 2:
        return (
            "Dry conditions. Irrigation may be needed for crops.",
            "Low rainfall increases irrigation costs and may stress drought-sensitive crops.",
        )
    return (
        "Adequate rainfall for agriculture. Good conditions for farming.",
        "Optimal moisture levels supporting vegetable production and lowering irrigation costs.",
    )


def _aqi_text(val: float):
    if val > 150:
        return (
            "Unhealthy air quality. Wear masks outdoors, limit strenuous activity.",
            "Poor air quality stresses crops and reduces pollinator activity.",
        )
    if val > 100:
        return (
            "Moderate air quality concerns. Sensitive groups should reduce outdoor exposure.",
            "Elevated pollution may affect open-air markets and farm worker productivity.",
        )
    return (
        "Air quality is good. Safe for all outdoor activities.",
        "Good air quality supports healthy crop growth and market operations.",
    )


def _humidity_text(val: float):
    if val > 88:
        return (
            "Very high humidity. High risk of fungal disease in crops.",
            "Excessive humidity promotes mold and blight in vegetables, reducing supply.",
        )
    if val > 80:
        return (
            "Elevated humidity. Monitor crops for fungal issues.",
            "Higher humidity may increase disease pressure on leafy vegetables.",
        )
    return (
        "Comfortable humidity levels. Good conditions for most crops.",
        "Optimal humidity supports healthy crop development and stable yields.",
    )


def _uv_text(val: float):
    if val > 10:
        return (
            "Extreme UV. Use SPF 50+ sunscreen. Avoid sun 10am–4pm.",
            "Extreme UV can scorch sensitive crops and stress field workers.",
        )
    if val > 7:
        return (
            "Very high UV levels. Use SPF 50+ and seek shade during 10am–4pm.",
            "High UV can stress crops but also helps natural pest control.",
        )
    return (
        "Moderate UV. Use standard sun protection when outdoors.",
        "Normal UV levels support photosynthesis without crop stress.",
    )


def _soil_text(val: float):
    if val < 15:
        return (
            "Very low soil moisture. Irrigation urgently needed.",
            "Dry soils reduce vegetable yields and push prices higher.",
        )
    if val > 60:
        return (
            "Waterlogged soil conditions. Risk of root rot.",
            "Excessive soil moisture damages root crops and tubers.",
        )
    return (
        "Optimal soil moisture for planting. Good conditions for crop growth.",
        "Excellent soil conditions supporting vegetable production and stable prices.",
    )


def _drought_text(val: float):
    if val > 3.5:
        return (
            "Significant drought risk. Water conservation measures advised.",
            "Drought conditions reduce crop yields and drive commodity prices higher.",
        )
    if val > 2:
        return (
            "Mild drought stress. Monitor water availability for crops.",
            "Moderate drought may affect irrigation-dependent crops.",
        )
    return (
        "Low drought risk. Adequate water supply for agriculture.",
        "Minimal drought stress keeping crop prices stable.",
    )


def _wind_text(val: float):
    if val > 60:
        return (
            "Strong winds. Risk of crop damage and dangerous fishing conditions.",
            "High winds damage standing crops and disrupt supply chains significantly.",
        )
    if val > 40:
        return (
            "Moderate winds. Secure farm structures and greenhouses.",
            "Strong winds may affect pollination and damage tall crops.",
        )
    return (
        "Gentle breeze conditions. Safe for all outdoor activities.",
        "Calm conditions favorable for farming operations and fishing.",
    )


# ──────────────────────────────────────────────
# Derived metrics (no direct API field)
# ──────────────────────────────────────────────


def _estimate_soil_moisture(precip_mm: float, humidity: float) -> float:
    """Estimate soil moisture % from rainfall and humidity heuristic."""
    base = 20.0
    rain_contrib = min(precip_mm * 1.2, 35)
    humidity_contrib = max(0, (humidity - 60) * 0.3)
    return round(min(100, max(0, base + rain_contrib + humidity_contrib)), 1)


def _estimate_drought_index(precip_mm: float, humidity: float) -> float:
    """Estimate drought index (0–5 scale; higher = more drought risk)."""
    rain_relief = min(precip_mm * 0.3, 3.5)
    humidity_relief = max(0, (humidity - 50) * 0.04)
    index = max(0, 5 - rain_relief - humidity_relief)
    return round(index, 1)


# ──────────────────────────────────────────────
# Trend management
# ──────────────────────────────────────────────


def _update_trend(existing_trend: list, new_value: float, max_len: int = 7) -> list:
    """Shift existing trend left, append new value, keep last max_len entries."""
    trend = list(existing_trend) if existing_trend else []
    trend.append(round(new_value, 1))
    return trend[-max_len:]


# ──────────────────────────────────────────────
# Main fetch
# ──────────────────────────────────────────────


async def fetch_weather_data() -> dict:
    """Fetch current weather + AQI from WeatherAPI.com.
    Returns the JSON data on success, or a dict with 'error' key on failure."""
    if not WEATHERAPI_KEY:
        msg = "WEATHERAPI_KEY not set in environment"
        logger.error(msg)
        return {"error": msg}

    url = f"{WEATHERAPI_BASE}/current.json?key={WEATHERAPI_KEY}&q={PH_LOCATION}&aqi=yes"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    msg = f"WeatherAPI returned HTTP {resp.status}: {body[:200]}"
                    logger.error(msg)
                    return {"error": msg}
                return await resp.json()
    except asyncio.TimeoutError:
        msg = "WeatherAPI request timed out after 15s"
        logger.error(msg)
        return {"error": msg}
    except Exception as e:
        msg = f"WeatherAPI fetch error: {e}"
        logger.error(msg)
        return {"error": msg}


# ──────────────────────────────────────────────
# MongoDB update
# ──────────────────────────────────────────────


async def run_weather_update(db) -> dict:
    """
    Fetch live weather from WeatherAPI and upsert all 8 climate_metrics documents.
    Returns a result dict with success flag and details.
    """
    data = await fetch_weather_data()
    if "error" in data:
        return {"success": False, "error": data["error"]}

    try:
        current = data["current"]
        temp_c = current["temp_c"]
        precip_mm = current["precip_mm"]
        humidity = current["humidity"]
        uv = current["uv"]
        wind_kph = current["wind_kph"]

        # AQI: use US EPA index (1-6) → convert to AQI scale
        aqi_raw = current.get("air_quality", {}).get("us-epa-index", 1)
        aqi_val = EPA_TO_AQI.get(int(aqi_raw), 25)

        # Derived
        soil_moisture = _estimate_soil_moisture(precip_mm, humidity)
        drought_index = _estimate_drought_index(precip_mm, humidity)

        now = datetime.now(timezone.utc)

        # Build the 8 metric update payloads
        metrics = [
            {
                "name": "Temperature",
                "currentValue": round(temp_c, 1),
                "unit": "°C",
                "icon": "🌡️",
                "category": "climate",
                "status": _temp_status(temp_c),
                "texts": _temp_text(temp_c),
                "fn_trend": lambda t: _update_trend(t, temp_c),
            },
            {
                "name": "Rainfall",
                "currentValue": round(precip_mm, 1),
                "unit": "mm",
                "icon": "🌧️",
                "category": "climate",
                "status": _rainfall_status(precip_mm),
                "texts": _rainfall_text(precip_mm),
                "fn_trend": lambda t: _update_trend(t, precip_mm),
            },
            {
                "name": "Air Quality Index",
                "currentValue": aqi_val,
                "unit": "AQI",
                "icon": "🌬️",
                "category": "climate",
                "status": _aqi_status(aqi_val),
                "texts": _aqi_text(aqi_val),
                "fn_trend": lambda t: _update_trend(t, aqi_val),
            },
            {
                "name": "Humidity",
                "currentValue": humidity,
                "unit": "%",
                "icon": "💧",
                "category": "climate",
                "status": _humidity_status(humidity),
                "texts": _humidity_text(humidity),
                "fn_trend": lambda t: _update_trend(t, humidity),
            },
            {
                "name": "UV Index",
                "currentValue": round(uv, 1),
                "unit": "UV",
                "icon": "☀️",
                "category": "climate",
                "status": _uv_status(uv),
                "texts": _uv_text(uv),
                "fn_trend": lambda t: _update_trend(t, uv),
            },
            {
                "name": "Soil Moisture",
                "currentValue": soil_moisture,
                "unit": "%",
                "icon": "🌱",
                "category": "climate",
                "status": _soil_status(soil_moisture),
                "texts": _soil_text(soil_moisture),
                "fn_trend": lambda t: _update_trend(t, soil_moisture),
            },
            {
                "name": "Drought Index",
                "currentValue": drought_index,
                "unit": "scale",
                "icon": "🏜️",
                "category": "climate",
                "status": _drought_status(drought_index),
                "texts": _drought_text(drought_index),
                "fn_trend": lambda t: _update_trend(t, drought_index),
            },
            {
                "name": "Wind Speed",
                "currentValue": round(wind_kph, 1),
                "unit": "km/h",
                "icon": "💨",
                "category": "climate",
                "status": _wind_status(wind_kph),
                "texts": _wind_text(wind_kph),
                "fn_trend": lambda t: _update_trend(t, wind_kph),
            },
        ]

        updated = 0
        for m in metrics:
            # Fetch existing doc to preserve/extend its trend
            existing = await db.climate_metrics.find_one({"name": m["name"]})
            existing_trend = existing.get("trend", []) if existing else []

            rec, imp = m["texts"]
            doc = {
                "name": m["name"],
                "category": m["category"],
                "currentValue": m["currentValue"],
                "unit": m["unit"],
                "icon": m["icon"],
                "status": m["status"],
                "trend": m["fn_trend"](existing_trend),
                "recommendation": rec,
                "impact": imp,
                "lastUpdated": now,
                "updatedAt": now,
                "data_source": "WeatherAPI.com (live)",
                "location": "Manila, Philippines",
            }

            await db.climate_metrics.update_one(
                {"name": m["name"]},
                {"$set": doc, "$setOnInsert": {"createdAt": now}},
                upsert=True,
            )
            updated += 1

        logger.info(
            f"Weather update complete — {updated} metrics updated at {now.isoformat()}"
        )
        return {
            "success": True,
            "metrics_updated": updated,
            "timestamp": now.isoformat(),
            "raw": {
                "temp_c": temp_c,
                "precip_mm": precip_mm,
                "humidity": humidity,
                "uv": uv,
                "wind_kph": wind_kph,
                "aqi": aqi_val,
                "soil_moisture_est": soil_moisture,
                "drought_index_est": drought_index,
            },
        }

    except Exception as e:
        logger.error(f"Weather update failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
