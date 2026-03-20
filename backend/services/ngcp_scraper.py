"""
NGCP Grid Status Scraper

Scrapes the "Power Situation Outlook" table from ngcp.ph using Playwright.
The table sits in the homepage right sidebar and shows:

  | (MW)                         | Luz    | Vis   | Min   |
  |------------------------------|--------|-------|-------|
  | Available Generating Capacity| 14,054 | 2,620 | 2,977 |
  | System Peak Demand           | 11,582 | 2,333 | 2,417 |
  | Operating Margin             |  2,472 |   287 |   560 |

ngcp.ph blocks plain HTTP (Cloudflare 403); Playwright + stealth bypasses it.
Results are cached for 30 minutes to avoid launching Chromium on every request.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

logger = logging.getLogger(__name__)

NGCP_URL = "https://ngcp.ph"

# Chromium flags for low-memory environments (Render free tier ~512 MB)
_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--single-process",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-sync",
    "--mute-audio",
    "--no-first-run",
]


class NGCPScraper:
    CACHE_TTL = 1800  # 30 minutes

    def __init__(self):
        self._cache: Optional[Dict] = None
        self._cache_ts: float = 0
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def scrape(self) -> Optional[Dict]:
        """
        Return Power Situation Outlook data from ngcp.ph.

        Returns:
            dict with {total_supply, total_demand, reserves, grids[], data_as_of, source}
            on success, or None on failure.
        """
        if self._cache and (time.time() - self._cache_ts) < self.CACHE_TTL:
            return self._cache

        async with self._get_lock():
            # Double-check after acquiring lock
            if self._cache and (time.time() - self._cache_ts) < self.CACHE_TTL:
                return self._cache

            result = await self._do_scrape()
            if result is not None:
                self._cache = result
                self._cache_ts = time.time()
                logger.info(
                    f"NGCP: scraped OK — demand={result.get('total_demand')} MW "
                    f"supply={result.get('total_supply')} MW"
                )
            else:
                logger.warning("NGCP: scrape returned no data")
            return result

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    async def _do_scrape(self) -> Optional[Dict]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=_CHROMIUM_ARGS,
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 900},
                )
                page = await context.new_page()
                await stealth_async(page)

                await page.goto(
                    NGCP_URL,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                # Allow JS-rendered content to settle
                await page.wait_for_timeout(2000)

                # Extract the Power Situation Outlook table via JS
                raw = await page.evaluate("""() => {
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const tbl of tables) {
                        const text = tbl.textContent || '';
                        // Identify the right table by content
                        if (!text.includes('Generating') || !text.includes('Luz')) continue;

                        const rows = Array.from(tbl.querySelectorAll('tr'));
                        return {
                            rows: rows.map(r =>
                                Array.from(r.querySelectorAll('td, th'))
                                    .map(c => c.textContent.trim())
                            )
                        };
                    }
                    // Fallback: also check for section headings
                    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,div,span'));
                    for (const el of headings) {
                        if ((el.textContent || '').includes('Power Situation Outlook')) {
                            // Walk up to find the container then the table
                            let parent = el.parentElement;
                            for (let i = 0; i < 5; i++) {
                                const tbl = parent && parent.querySelector('table');
                                if (tbl) {
                                    const rows = Array.from(tbl.querySelectorAll('tr'));
                                    return {
                                        rows: rows.map(r =>
                                            Array.from(r.querySelectorAll('td, th'))
                                                .map(c => c.textContent.trim())
                                        )
                                    };
                                }
                                parent = parent && parent.parentElement;
                            }
                        }
                    }
                    return null;
                }""")

                await browser.close()

                if not raw or not raw.get("rows"):
                    logger.warning("NGCP: could not locate Power Situation Outlook table")
                    return None

                return self._parse_table(raw["rows"])

        except Exception as exc:
            logger.error(f"NGCP scraper error: {exc}")
            return None

    def _parse_table(self, rows: List[List[str]]) -> Optional[Dict]:
        """
        Parse the Power Situation Outlook table rows.

        Expected structure:
          Row with "as of ..." timestamp
          Header: (MW)  |  Luz  |  Vis  |  Min
          Available Generating Capacity | 14054 | 2620 | 2977
          System Peak Demand            | 11582 | 2333 | 2417
          Operating Margin              |  2472 |  287 |  560
        """
        def to_float(s: str) -> Optional[float]:
            try:
                return float(s.replace(",", "").strip())
            except (ValueError, AttributeError):
                return None

        timestamp = None
        capacity: Dict[str, float] = {}
        demand:   Dict[str, float] = {}
        margin:   Dict[str, float] = {}

        for row in rows:
            if not row:
                continue

            # Timestamp row (single cell "as of 6:00 PM, ...")
            if len(row) == 1 and "as of" in row[0].lower():
                timestamp = row[0]
                continue

            label = row[0].lower()
            vals  = row[1:]   # [Luz, Vis, Min]

            regions = ["luzon", "visayas", "mindanao"]

            if "generating" in label or ("available" in label and "capacity" in label):
                for i, r in enumerate(regions):
                    v = to_float(vals[i]) if i < len(vals) else None
                    if v is not None:
                        capacity[r] = v

            elif "demand" in label or "peak" in label:
                for i, r in enumerate(regions):
                    v = to_float(vals[i]) if i < len(vals) else None
                    if v is not None:
                        demand[r] = v

            elif "margin" in label or "operating" in label or "reserve" in label:
                for i, r in enumerate(regions):
                    v = to_float(vals[i]) if i < len(vals) else None
                    if v is not None:
                        margin[r] = v

        if not capacity or not demand:
            logger.warning(f"NGCP: incomplete table data (capacity={capacity}, demand={demand})")
            return None

        # Derive margin from capacity - demand if not parsed
        if not margin:
            margin = {r: capacity.get(r, 0) - demand.get(r, 0) for r in regions}

        total_supply = int(sum(capacity.values()))
        total_demand = int(sum(demand.values()))
        total_margin = int(sum(margin.values()))

        grids = []
        for region_key, region_name in [
            ("luzon",    "Luzon"),
            ("visayas",  "Visayas"),
            ("mindanao", "Mindanao"),
        ]:
            cap = capacity.get(region_key)
            dem = demand.get(region_key)
            mar = margin.get(region_key, (cap or 0) - (dem or 0))

            # Per-grid status based on operating margin %
            if cap and cap > 0:
                margin_pct = (mar / cap) * 100
                if margin_pct < 10:
                    grid_status = "TIGHT"
                elif margin_pct < 18:
                    grid_status = "ELEVATED"
                else:
                    grid_status = "NORMAL"
            else:
                grid_status = "NORMAL"

            grids.append({
                "name":             region_name,
                "capacity":         int(cap) if cap is not None else None,
                "current":          int(dem) if dem is not None else None,
                "operating_margin": int(mar) if mar is not None else None,
                "status":           grid_status,
            })

        return {
            "total_supply": total_supply,
            "total_demand": total_demand,
            "reserves":     total_margin,
            "grids":        grids,
            "data_as_of":   timestamp,
            "source":       "NGCP Power Situation Outlook",
        }


# Singleton
ngcp_scraper = NGCPScraper()
