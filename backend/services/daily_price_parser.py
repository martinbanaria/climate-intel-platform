"""
Daily Price Index Parser for DA Bantay Presyo
Parses daily price index PDFs to extract real historical price data
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
import PyPDF2
import io
import re
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class DailyPriceIndexParser:
    """Parser for DA Bantay Presyo Daily Price Index PDFs"""

    def __init__(self):
        self.base_url = "https://www.da.gov.ph/wp-content/uploads"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _construct_daily_url(self, date: datetime) -> List[str]:
        """Construct possible Daily Price Index PDF URLs"""
        month_name = date.strftime("%B")
        # DA uses multiple naming patterns, try both
        urls = [
            f"{self.base_url}/{date.year}/{date.month:02d}/Daily-Price-Index-{month_name}-{date.day}-{date.year}.pdf",
            f"{self.base_url}/{date.year}/{date.month:02d}/{month_name}-{date.day}-{date.year}-DPI-AFC.pdf",
        ]
        return urls

    async def download_pdf(self, date: datetime) -> Optional[bytes]:
        """Download Daily Price Index PDF for a specific date"""
        urls = self._construct_daily_url(date)

        # Try all possible URL patterns
        for url in urls:
            logger.info(f"Trying: {url}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, headers=self.headers, timeout=30
                    ) as response:
                        if response.status == 200:
                            logger.info(
                                f"✓ Downloaded PDF for {date.strftime('%Y-%m-%d')}"
                            )
                            return await response.read()
                        else:
                            logger.debug(
                                f"URL not found: {url} (Status {response.status})"
                            )
            except Exception as e:
                logger.debug(f"Failed: {url} - {str(e)}")
                continue

        logger.warning(f"No PDF found for {date.strftime('%Y-%m-%d')}")
        return None

    async def download_multiple_days(
        self, days: int = 7
    ) -> List[Tuple[datetime, bytes]]:
        """Download PDFs for the last N days"""
        today = datetime.now()
        downloads = []

        for days_ago in range(days):
            date = today - timedelta(days=days_ago)
            # Skip weekends for daily reports
            if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue

            pdf_bytes = await self.download_pdf(date)
            if pdf_bytes:
                downloads.append((date, pdf_bytes))

            # Small delay to be respectful
            await asyncio.sleep(0.5)

        logger.info(f"Downloaded {len(downloads)} PDFs out of {days} days")
        return downloads

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = []
            # Extract all pages to get all 200+ commodities
            for page_num in range(len(pdf_reader.pages)):
                text = pdf_reader.pages[page_num].extract_text()
                if text:
                    text_content.append(text)

            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

    def parse_prices(self, text: str) -> Dict[str, float]:
        """Parse commodity prices from Daily Price Index text - ULTRA COMPREHENSIVE"""
        prices = {}
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Skip ONLY obvious headers (be less aggressive)
            skip_patterns = [
                "DAILY PRICE INDEX",
                "DEPARTMENT OF AGRICULTURE",
                "BANTAY PRESYO",
                "PREVAILING RETAIL PRICE",
                "NATIONAL CAPITAL REGION",
                "Page ",
                "Prepared by",
                "Source:",
            ]

            if any(pattern in line for pattern in skip_patterns):
                continue

            # Skip if entire line is uppercase AND doesn't contain numbers
            if line.isupper() and not re.search(r"\d", line):
                continue

            # Skip lines with "n/a" prices
            if "n/a" in line.lower():
                continue

            # MULTIPLE patterns to catch all price formats:
            # Pattern 1: Standard "Name    123.45" (2 decimal places)
            # Pattern 2: "Name    123.4" or "Name    123" (1 or 0 decimals)
            # Pattern 3: "Name 123.45" (less whitespace)

            price_patterns = [
                r"(\d+\.\d{2})\s*$",  # 123.45 at end
                r"(\d+\.\d{1})\s*$",  # 123.4 at end
                r"(\d+)\s*$",  # 123 at end (no decimal)
            ]

            matched = False
            for pattern in price_patterns:
                price_match = re.search(pattern, line)
                if price_match:
                    price_str = price_match.group(1)
                    try:
                        price = float(price_str)
                        # Very permissive price range (0.50 to 50,000)
                        if 0.5 <= price <= 50000:
                            # Extract commodity name (everything before the price)
                            commodity_part = line[: price_match.start()].strip()

                            # Minimal cleaning - keep almost everything
                            commodity_name = self._clean_commodity_name(commodity_part)
                            if commodity_name and len(commodity_name) >= 2:
                                prices[commodity_name] = price
                                matched = True
                                break
                    except ValueError:
                        pass

                if matched:
                    break

        return prices

    def _clean_commodity_name(self, name: str) -> Optional[str]:
        """Clean and standardize commodity name - MINIMAL filtering"""
        name = name.strip()

        # Skip if too short
        if len(name) < 2:
            return None

        # Only skip the most obvious non-commodity text
        skip_keywords = [
            "page",
            "prevailing",
            "retail price",
            "department",
            "table",
            "source",
            "prepared",
        ]
        name_lower = name.lower()

        # Only skip if the ENTIRE name is just the keyword
        for keyword in skip_keywords:
            if name_lower == keyword or name_lower.startswith(keyword + " "):
                return None

        # Remove trailing/leading special chars but keep commas inside
        name = re.sub(r"^[,\s\-\.]+", "", name)
        name = re.sub(r"[,\s\-\.]+$", "", name)

        # Accept almost anything that's left
        return name if len(name) >= 2 else None

    async def build_price_history(self, days: int = 7) -> Dict[str, List[Dict]]:
        """Build price history for commodities over multiple days"""
        logger.info(f"Building price history for last {days} days...")

        # Download PDFs
        pdfs = await self.download_multiple_days(days)

        if not pdfs:
            logger.error("No PDFs downloaded")
            return {}

        # Parse each PDF
        price_history = defaultdict(list)

        for date, pdf_bytes in pdfs:
            text = self.extract_text_from_pdf(pdf_bytes)
            prices = self.parse_prices(text)

            logger.info(f"Parsed {len(prices)} prices for {date.strftime('%Y-%m-%d')}")

            for commodity, price in prices.items():
                price_history[commodity].append({"date": date, "price": price})

        # Sort by date for each commodity
        for commodity in price_history:
            price_history[commodity].sort(key=lambda x: x["date"])

        logger.info(f"Built history for {len(price_history)} commodities")
        return dict(price_history)

    def calculate_trends(self, price_history: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Calculate trends and statistics from price history"""
        trends = {}

        for commodity, history in price_history.items():
            # Keep ALL commodities, even with single data point
            # (removed filter: if len(history) < 2: continue)

            prices = [h["price"] for h in history]
            dates = [h["date"] for h in history]

            current_price = prices[-1]
            average_price = sum(prices) / len(prices)

            # Calculate trend direction
            if len(prices) >= 3:
                recent_avg = sum(prices[-3:]) / 3
                older_avg = sum(prices[:3]) / 3
                trend_direction = (
                    "increasing" if recent_avg > older_avg else "decreasing"
                )
            elif len(prices) == 2:
                # For 2 data points, compare directly
                trend_direction = (
                    "increasing" if prices[-1] > prices[0] else "decreasing"
                )
            else:
                # Single data point - mark as stable
                trend_direction = "stable"

            # Calculate price change
            price_change = current_price - prices[0]
            price_change_pct = (price_change / prices[0]) * 100 if prices[0] > 0 else 0

            trends[commodity] = {
                "current_price": current_price,
                "average_price": round(average_price, 2),
                "trend": prices,  # Last 7 days
                "trend_direction": trend_direction,
                "price_change": round(price_change, 2),
                "price_change_pct": round(price_change_pct, 2),
                "data_points": len(prices),
                "date_range": {
                    "start": dates[0].strftime("%Y-%m-%d"),
                    "end": dates[-1].strftime("%Y-%m-%d"),
                },
            }

        return trends


# Singleton instance
daily_parser = DailyPriceIndexParser()
