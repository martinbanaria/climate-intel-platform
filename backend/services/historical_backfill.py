"""
Historical Price Archive Backfill
Iterates over a date range, downloads DA Bantay Presyo PDFs, parses prices,
and upserts snapshots to the `price_history` MongoDB collection.

Each document: {name, date (YYYY-MM-DD), price, category, source, scraped_at}
Unique index: {name, date}

DA PDFs are only published on weekdays — weekends are skipped automatically.
Rate limiting: 1.5s delay between page fetches to be polite to DA servers.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from services.daily_price_parser import daily_parser

logger = logging.getLogger(__name__)

RATE_LIMIT_SECS = 1.5

CATEGORY_MAP = {
    ("rice", "bigas", "milled", "glutinous", "basmati", "premium", "jasponica", "japonica"): "rice",
    ("chicken", "egg", "poultry"): "poultry",
    ("pork", "beef", "carabao", "meat"): "meat",
    ("fish", "tilapia", "bangus", "galunggong", "alumahan", "tuna", "mackerel"): "fish",
    ("lettuce", "cabbage", "tomato", "onion", "potato", "carrot", "broccoli",
     "pechay", "ampalaya", "eggplant", "squash", "sayote", "chayote", "mustasa", "corn",
     "kangkong", "sitaw", "mongo"): "vegetables",
    ("garlic", "ginger", "chili", "pepper"): "spices",
    ("diesel", "gasoline", "fuel", "lpg", "kerosene"): "fuel",
}


def _categorize(name: str) -> str:
    n = name.lower()
    for keywords, cat in CATEGORY_MAP.items():
        if any(k in n for k in keywords):
            return cat
    return "others"


async def backfill_date_range(db, start_date: datetime, end_date: datetime) -> dict:
    """
    Download and store daily price snapshots for every weekday in [start_date, end_date].
    Returns stats: {days_attempted, days_success, days_failed, records_upserted}
    """
    days_attempted = days_success = days_failed = records_upserted = 0
    current = start_date

    while current <= end_date:
        # Skip weekends — DA doesn't publish
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        days_attempted += 1
        date_str = current.strftime("%Y-%m-%d")
        logger.info(f"Backfilling {date_str}...")

        try:
            pdf_bytes = await daily_parser.download_pdf(current)
            if not pdf_bytes:
                logger.warning(f"No PDF found for {date_str} — skipping")
                days_failed += 1
                current += timedelta(days=1)
                await asyncio.sleep(RATE_LIMIT_SECS)
                continue

            text = daily_parser.extract_text_from_pdf(pdf_bytes)
            prices = daily_parser.parse_prices(text)

            if not prices:
                logger.warning(f"No prices parsed for {date_str}")
                days_failed += 1
                current += timedelta(days=1)
                await asyncio.sleep(RATE_LIMIT_SECS)
                continue

            for name, price in prices.items():
                doc = {
                    "name": name,
                    "date": date_str,
                    "price": price,
                    "category": _categorize(name),
                    "source": "DA Bantay Presyo",
                    "scraped_at": datetime.utcnow().isoformat(),
                }
                await db.price_history.update_one(
                    {"name": name, "date": date_str},
                    {"$set": doc},
                    upsert=True,
                )
                records_upserted += 1

            days_success += 1
            logger.info(f"✓ {date_str}: {len(prices)} items upserted")

        except Exception as e:
            logger.error(f"Error backfilling {date_str}: {e}")
            days_failed += 1

        current += timedelta(days=1)
        await asyncio.sleep(RATE_LIMIT_SECS)

    return {
        "days_attempted": days_attempted,
        "days_success": days_success,
        "days_failed": days_failed,
        "records_upserted": records_upserted,
    }
