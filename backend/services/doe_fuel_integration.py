"""
DOE Fuel Price Integration
Fetches weekly NCR retail fuel prices from the anomura.today public API,
which sources data from DOE Oil Industry Management Bureau (OIMB).

API: https://anomura-api.geianmarkdenorte.workers.dev/api/fuel/latest
Returns ncr_summary with common prices for RON 91/95/97/100, Diesel, Diesel Plus, Kerosene.
"""
import aiohttp
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ANOMURA_FUEL_API = "https://anomura-api.geianmarkdenorte.workers.dev/api/fuel/latest"

# Maps anomura API product names -> our market_items names
PRODUCT_MAP = {
    "RON 91": "Gasoline 91",
    "RON 95": "Gasoline 95",
    "RON 97/100": "Gasoline 97",
    "DIESEL": "Diesel",
    "DIESEL PLUS": "Diesel Plus",
    "KEROSENE": "Kerosene",
}


class DOEFuelPriceIntegration:
    """Integration service for DOE fuel prices via anomura API"""

    async def scrape_fuel_prices(self):
        """Fetch current NCR fuel prices from anomura API (DOE OIMB data source)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    ANOMURA_FUEL_API,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Anomura fuel API returned {resp.status}")
                        return {}
                    data = await resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch anomura fuel API: {e}")
            return {}

        week_start = data.get("week_start", "")
        ncr_summary = data.get("ncr_summary", [])

        fuel_prices = {}
        for item in ncr_summary:
            product = item.get("product", "")
            if product not in PRODUCT_MAP:
                continue
            name = PRODUCT_MAP[product]
            common = item.get("common_price")
            if common is None:
                low = item.get("range_low", 0)
                high = item.get("range_high", 0)
                price = round((low + high) / 2, 2)
            else:
                price = common
            unit = "kg" if name == "LPG" else "L"
            fuel_prices[name] = {
                "price": price,
                "range_low": item.get("range_low"),
                "range_high": item.get("range_high"),
                "unit": unit,
                "source": "DOE OIMB via anomura.today",
                "region": "NCR",
                "week_start": week_start,
            }

        logger.info(f"Fetched {len(fuel_prices)} fuel prices for week of {week_start}")
        return fuel_prices

    def generate_fuel_metadata(self):
        return {
            "data_source": "DOE Oil Industry Management Bureau (OIMB)",
            "api": "anomura-api.geianmarkdenorte.workers.dev",
            "monitoring_system": "Weekly retail pump price monitoring",
            "note": "NCR common price; falls back to midpoint of low/high range",
            "update_frequency": "Weekly (Tuesday announcements)",
            "regions": ["NCR"],
        }


async def integrate_doe_fuel_prices(db):
    """Fetch live DOE fuel prices and upsert to market_items collection."""
    logger.info("Integrating DOE fuel prices via anomura API...")

    integrator = DOEFuelPriceIntegration()
    fuel_prices = await integrator.scrape_fuel_prices()
    metadata = integrator.generate_fuel_metadata()

    if not fuel_prices:
        logger.warning("No fuel prices returned from anomura API")
        return False

    saved_count = 0
    for fuel_name, data in fuel_prices.items():
        try:
            existing = await db.market_items.find_one({"name": fuel_name})
            current_price = data["price"]

            if existing and "averagePrice" in existing:
                average_price = existing["averagePrice"]
            else:
                average_price = current_price

            trend = existing["trend"][-5:] if existing and "trend" in existing else []
            trend.append(current_price)
            if len(trend) > 6:
                trend = trend[-6:]

            diff_pct = ((current_price - average_price) / average_price) * 100 if average_price else 0
            if diff_pct < -5:
                status = "MURA"
            elif diff_pct > 5:
                status = "MAHAL"
            else:
                status = "STABLE"

            doc = {
                "name": fuel_name,
                "category": "fuel",
                "currentPrice": current_price,
                "averagePrice": average_price,
                "unit": data["unit"],
                "location": data["region"],
                "icon": "⛽",
                "status": status,
                "savings": round(average_price - current_price, 2),
                "trend": trend,
                "priceRange": {"low": data.get("range_low"), "high": data.get("range_high")},
                "weekStart": data.get("week_start"),
                "lastUpdated": datetime.utcnow(),
                "climateImpact": {
                    "level": "low",
                    "factors": ["Global crude oil market", "DOE price monitoring"],
                    "forecast": "Prices following global crude trends",
                },
                "metadata": metadata,
                "updatedAt": datetime.utcnow(),
            }

            if not existing:
                doc["createdAt"] = datetime.utcnow()

            await db.market_items.update_one(
                {"name": fuel_name},
                {"$set": doc},
                upsert=True,
            )
            saved_count += 1
            logger.info(f"Saved fuel: {fuel_name} ₱{current_price}/{data['unit']}")

        except Exception as e:
            logger.error(f"Error saving fuel price {fuel_name}: {e}")

    logger.info(f"✅ DOE fuel prices integrated: {saved_count} items")
    return saved_count > 0
