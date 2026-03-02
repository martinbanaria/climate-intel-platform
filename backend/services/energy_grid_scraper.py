"""
Philippine WESM Price Scraper

Fetches real-time electricity market prices from IEMOP (iemop.ph).
Data: RTD Market Clearing Prices (PHP/MWh) for Luzon, Visayas, Mindanao.

File pattern:
  https://www.iemop.ph/wp-content/uploads/downloads/data/MP/MP_YYYYMMDD.csv

CSV columns:
  RUN_TIME, MKT_TYPE, TIME_INTERVAL, REGION_NAME, RESOURCE_NAME,
  RESOURCE_TYPE, COMMODITY_TYPE, MARGINAL_PRICE

Region codes:  CLUZ = Luzon, CVIS = Visayas, CMIN = Mindanao

Note: NGCP real-time MW data (grid status) is blocked by Cloudflare (403).
      Grid MW values are realistic estimates from NGCP historical data.
      Grid STATUS is derived from actual WESM price levels.
"""

import aiohttp
import csv
import io
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class WESMPriceScraper:
    CSV_URL = (
        "https://www.iemop.ph"
        "/wp-content/uploads/downloads/data/MP/MP_{date_str}.csv"
    )

    REGION_MAP = {
        "CLUZ": "luzon",
        "CVIS": "visayas",
        "CMIN": "mindanao",
    }

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    }

    # In-memory cache: key → (data, timestamp)
    _cache: Dict = {}
    CACHE_TTL = 3600  # seconds (1 hour)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _cached(self, key: str) -> Optional[Dict]:
        entry = self._cache.get(key)
        if entry and (time.time() - entry[1]) < self.CACHE_TTL:
            return entry[0]
        return None

    def _store(self, key: str, data: Dict):
        self._cache[key] = (data, time.time())

    async def _fetch_csv(self, date: datetime) -> Optional[str]:
        """Download IEMOP MP CSV for the given date. Returns text or None."""
        date_str = date.strftime("%Y%m%d")
        url = self.CSV_URL.format(date_str=date_str)
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.HEADERS, timeout=timeout) as resp:
                    if resp.status == 200:
                        return await resp.text(errors="replace")
                    logger.debug(f"IEMOP MP {date_str}: HTTP {resp.status}")
        except Exception as exc:
            logger.debug(f"IEMOP MP {date_str}: {exc}")
        return None

    def _parse_mp_csv(self, content: str) -> Dict[str, Dict]:
        """
        Parse IEMOP MP CSV.
        Returns {region_key: {current, average, min, max}} or {}.
        """
        prices: Dict[str, List[float]] = {k: [] for k in self.REGION_MAP.values()}
        try:
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                region_code = (row.get("REGION_NAME") or "").strip()
                price_raw = (row.get("MARGINAL_PRICE") or "").strip()
                region_key = self.REGION_MAP.get(region_code)
                if region_key and price_raw:
                    try:
                        prices[region_key].append(float(price_raw))
                    except ValueError:
                        pass
        except Exception as exc:
            logger.error(f"Error parsing IEMOP MP CSV: {exc}")
            return {}

        result = {}
        for key, vals in prices.items():
            if vals:
                result[key] = {
                    "current": vals[-1],
                    "average": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                }
        return result

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def fetch_price_trends(self, days: int = 7) -> Dict:
        """
        Fetch WESM price trends for the last `days` days.

        Returns a dict shaped like the existing price_trends structure:
          {
            "wesm_luzon":    {current, week_ago, month_ago, trend[], change_pct, ...},
            "wesm_visayas":  {...},
            "wesm_mindanao": {...}
          }

        Returns {} if IEMOP is unreachable.
        """
        cache_key = f"price_trends_{days}"
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        # Philippines is UTC+8
        ph_now = datetime.utcnow() + timedelta(hours=8)

        region_daily: Dict[str, List[Dict]] = {k: [] for k in self.REGION_MAP.values()}
        days_checked = 0
        days_collected = 0

        while days_collected < days and days_checked < 14:
            target = ph_now - timedelta(days=days_checked)
            days_checked += 1

            content = await self._fetch_csv(target)
            if not content:
                continue

            daily_stats = self._parse_mp_csv(content)
            if not daily_stats:
                continue

            for region_key, stats in daily_stats.items():
                region_daily[region_key].append(
                    {
                        "date": target.strftime("%Y-%m-%d"),
                        "avg": stats["average"],
                    }
                )
            days_collected += 1

        if not any(region_daily.values()):
            logger.warning("IEMOP: no data collected for any region")
            return {}

        output = {}
        for region_key, daily_list in region_daily.items():
            if not daily_list:
                continue
            daily_list.sort(key=lambda x: x["date"])  # oldest → newest
            trend = [int(round(d["avg"])) for d in daily_list]
            current = trend[-1]
            week_ago = trend[0] if len(trend) > 1 else current
            change_pct = (
                round((current - week_ago) / week_ago * 100, 1) if week_ago else 0.0
            )
            output[f"wesm_{region_key}"] = {
                "current": current,
                "week_ago": week_ago,
                "month_ago": week_ago,  # best available within 7-day window
                "trend": trend,
                "change_pct": change_pct,
                "data_date": daily_list[-1]["date"],
                "source": "IEMOP Real-Time Dispatch",
            }

        self._store(cache_key, output)
        return output

    async def derive_grid_status(self, price_trends: Optional[Dict] = None) -> Dict:
        """
        Build grid status response.

        STATUS is derived from Luzon WESM prices (real):
          > PHP 8,000/MWh → TIGHT
          > PHP 6,000/MWh → ELEVATED
          otherwise       → STABLE

        MW capacity/demand values are historical estimates from NGCP
        published data (NGCP live data is blocked by Cloudflare).
        """
        if price_trends is None:
            price_trends = await self.fetch_price_trends(days=1)

        luzon_price = (price_trends.get("wesm_luzon") or {}).get("current", 0)

        if luzon_price > 8000:
            status = "TIGHT"
        elif luzon_price > 6000:
            status = "ELEVATED"
        else:
            status = "STABLE"

        return {
            "status": status,
            "total_demand": None,   # NGCP blocked; see data_source note
            "total_supply": None,
            "reserves": None,
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "Status from IEMOP WESM prices; MW data unavailable (NGCP 403)",
            "grids": [
                {"name": "Luzon",    "status": status,   "capacity": None, "current": None},
                {"name": "Visayas",  "status": "NORMAL", "capacity": None, "current": None},
                {"name": "Mindanao", "status": "NORMAL", "capacity": None, "current": None},
            ],
        }


# Singleton
wesm_scraper = WESMPriceScraper()
