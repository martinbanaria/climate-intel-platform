"""
Shared HTTP utilities for the Climate Intel backend.
Provides retry-with-backoff for aiohttp requests.
"""
import asyncio
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=45)
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    *,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    headers: dict = None,
) -> Optional[aiohttp.ClientResponse]:
    """
    Fetch a URL with retry and exponential backoff.

    Returns the aiohttp response on HTTP 200.
    Returns None on:
      - HTTP 404 (immediately, no retry — resource doesn't exist)
      - All retries exhausted (5xx, timeouts, connection errors)

    Retries on:
      - HTTP 5xx server errors
      - aiohttp.ClientError (connection reset, DNS failure, etc.)
      - asyncio.TimeoutError
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    for attempt in range(max_retries):
        try:
            response = await session.get(url, headers=merged_headers)

            if response.status == 200:
                return response

            if response.status == 404:
                # Resource doesn't exist — no point retrying
                logger.info(f"404 Not Found: {url}")
                return None

            if response.status >= 500:
                logger.warning(
                    f"HTTP {response.status} on attempt {attempt + 1}/{max_retries}: {url}"
                )
                if attempt < max_retries - 1:
                    wait = backoff_base ** attempt
                    logger.info(f"Retrying in {wait:.0f}s...")
                    await asyncio.sleep(wait)
                continue

            # Other 4xx — don't retry
            logger.info(f"HTTP {response.status}: {url}")
            return None

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(
                f"{type(e).__name__} on attempt {attempt + 1}/{max_retries}: {url} — {e}"
            )
            if attempt < max_retries - 1:
                wait = backoff_base ** attempt
                logger.info(f"Retrying in {wait:.0f}s...")
                await asyncio.sleep(wait)

    logger.warning(f"All {max_retries} attempts failed: {url}")
    return None
