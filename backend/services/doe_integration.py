"""
DOE Issuances integration for Climate Intel.
Scrapes real Department Circulars, Department Orders, and other issuances
from the DOE Philippines website (doe.gov.ph) via Nuxt.js SSR HTML.

The DOE site is a Nuxt.js SPA with server-side rendering. The SSR HTML
contains a `window.__NUXT__` script block with structured article data.
We parse this directly with regex + json rather than relying on fragile
HTML selectors.

Also fetches DOE "What's New" articles for energy market news/advisories.

Pagination:
  Using `subcategory=Department+Circular` (and other subcategories) in the
  DOE URL unlocks full pagination (137+ pages for DCs alone, 4 items/page).
  The generic `category=Issuances` URL only shows ~2 pages of featured items.
  We detect the max page from the <select> pagination combobox in the HTML
  and iterate through all pages (full mode) or just the first few (daily mode).
"""

import aiohttp
import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DOE_BASE = "https://doe.gov.ph"
DOE_CMS_BASE = "https://prod-cms.doe.gov.ph"

# NOTE: All DOE subcategory URLs return the SAME article listing (the
# subcategory filter is cosmetic in the SSR HTML). So we only need to
# paginate through ONE subcategory URL to get all issuances. We use
# "Department Circular" because it unlocks the full 137-page pagination.
DOE_LISTING_SUBCATEGORY = "Department Circular"

# Rate limit: seconds to wait between page fetches
PAGE_DELAY = 1.5

# Default pages to fetch per subcategory in daily/incremental mode
DEFAULT_MAX_PAGES = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ──────────────────────────────────────────────
# HTML + __NUXT__ parsing
# ──────────────────────────────────────────────


def _extract_nuxt_articles(html: str) -> List[Dict]:
    """
    Extract article data from the __NUXT__ script block in DOE SSR HTML.

    The __NUXT__ block is a JS IIFE, not pure JSON. We extract the articles
    array by finding it within the script content via regex, then parse the
    HTML content field with BeautifulSoup for a clean text summary.
    """
    # Find the script containing window.__NUXT__
    match = re.search(r"window\.__NUXT__\s*=\s*(.+?);\s*</script>", html, re.DOTALL)
    if not match:
        logger.debug("Could not find __NUXT__ in DOE HTML")
        return []

    nuxt_js = match.group(1)

    # Extract the articles array from the JS blob.
    # Articles are inside "articles":[...] — find this JSON array.
    articles_match = re.search(
        r'"articles"\s*:\s*(\[.*?\])\s*,\s*"', nuxt_js, re.DOTALL
    )
    if not articles_match:
        # Fallback: try without trailing comma constraint
        articles_match = re.search(
            r'"articles"\s*:\s*(\[.*?\])\s*\}', nuxt_js, re.DOTALL
        )
    if not articles_match:
        logger.debug("Could not extract articles array from __NUXT__")
        return []

    raw = articles_match.group(1)

    # The JS may use `undefined` or `null` — normalize for JSON parsing
    raw = raw.replace("undefined", "null")

    try:
        articles = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse articles JSON: {e}")
        return []

    return articles


def _extract_articles_from_html(html: str) -> List[Dict]:
    """
    Fallback: extract articles by parsing the rendered HTML with BeautifulSoup.
    Used when __NUXT__ extraction fails.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Each article card has an h1 with a link (title), a time element, and content
    for heading in soup.find_all("h1"):
        link_tag = heading.find("a")
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        # Article links: /articles/ID--slug or /site/GROUP/articles/ID--slug
        if "/articles/" not in href:
            continue

        title = link_tag.get_text(strip=True)
        url = link_tag["href"]

        # Find the parent card container
        card = heading.find_parent("div")
        if not card:
            continue

        # Date
        time_tag = card.find("time")
        date_text = time_tag.get_text(strip=True) if time_tag else ""
        # Parse "Date published: Feb 27 2025 02:14 PM" format
        date_published = _parse_doe_date(date_text)

        # Content: first <p> sibling after the heading
        content_parts = []
        for p in card.find_all("p"):
            text = p.get_text(strip=True)
            if text and text not in (
                "Click link to view complete file/download PDF file:",
                "Published at:",
                "Date Published (mm/dd/yyyy):",
                "Date Submitted to ONAR (mm/dd/yyyy):",
            ):
                content_parts.append(text)

        # Attachments: links to prod-cms.doe.gov.ph
        attachments = []
        for a in card.find_all("a", href=True):
            href = a["href"]
            if "prod-cms.doe.gov.ph" in href or href.startswith("/documents/"):
                attachments.append(
                    {
                        "title": a.get_text(strip=True),
                        "contentUrl": href,
                        "encodingFormat": "application/pdf"
                        if href.endswith(".pdf") or "pdf" in href
                        else "",
                    }
                )

        # Extract article ID from URL: /articles/2933685--slug or /site/eumb/articles/2933685--slug
        article_id = None
        id_match = re.search(r"/articles/(\d+)--", url)
        if id_match:
            article_id = int(id_match.group(1))

        articles.append(
            {
                "id": article_id,
                "title": title,
                "link": url,
                "content": " ".join(content_parts[:2]),  # First 2 paragraphs as summary
                "datePublished": date_published,
                "attachments": attachments,
            }
        )

    return articles


def _detect_max_page(html: str) -> int:
    """
    Detect the maximum page number from the pagination <select> combobox.
    The DOE Nuxt.js listing pages have a <select> with <option> elements
    numbered 1..N. Returns the highest option value, or 1 if not found.
    """
    soup = BeautifulSoup(html, "html.parser")
    # The pagination combobox is a <select> with option values like "1", "2", ...
    # Look for a select that contains numeric options
    for select in soup.find_all("select"):
        options = select.find_all("option")
        max_val = 0
        for opt in options:
            val = opt.get("value", opt.get_text(strip=True))
            try:
                num = int(val)
                if num > max_val:
                    max_val = num
            except (ValueError, TypeError):
                continue
        if max_val > 1:
            return max_val
    return 1


def _parse_doe_date(text: str) -> Optional[str]:
    """Parse DOE date strings into ISO format."""
    # "Date published: Feb 27 2025 02:14 PM"
    text = text.replace("Date published:", "").strip()
    formats = [
        "%b %d %Y %I:%M %p",
        "%b %d %Y",
        "%B %d, %Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def _clean_html_to_summary(html_content: str, max_len: int = 500) -> str:
    """Strip HTML tags and return a plain-text summary."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "..."
    return text


def _classify_issuance(title: str) -> str:
    """Determine issuance type from the title."""
    title_lower = title.lower()
    if "department circular" in title_lower or title_lower.startswith("dc"):
        return "Department Circular"
    if "department order" in title_lower or title_lower.startswith("do"):
        return "Department Order"
    if "memorandum circular" in title_lower:
        return "Memorandum Circular"
    if "memorandum order" in title_lower:
        return "Memorandum Order"
    if "administrative order" in title_lower:
        return "Administrative Order"
    if "executive order" in title_lower:
        return "Executive Order"
    if "joint" in title_lower:
        return "Joint Circular"
    if "special order" in title_lower:
        return "Special Order"
    if "implementing guidelines" in title_lower:
        return "Implementing Guidelines"
    return "Issuance"


# ──────────────────────────────────────────────
# Fetch DOE issuances (with full pagination)
# ──────────────────────────────────────────────


async def _fetch_doe_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a DOE page and return raw HTML."""
    try:
        async with session.get(
            url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                logger.warning(f"DOE page returned HTTP {resp.status}: {url}")
                return None
            return await resp.text()
    except Exception as e:
        logger.error(f"Failed to fetch DOE page {url}: {e}")
        return None


async def _fetch_subcategory(
    session: aiohttp.ClientSession,
    subcategory: str,
    max_pages: int,
    seen_ids: set,
) -> List[Dict]:
    """
    Paginate through a single DOE subcategory and return all articles found.
    Respects rate limiting (PAGE_DELAY between requests).
    Deduplicates against seen_ids (shared across subcategories).
    """
    # URL-encode: spaces -> +
    subcat_param = subcategory.replace(" ", "+")
    base_url = (
        f"{DOE_BASE}/articles/group/laws-and-issuances"
        f"?subcategory={subcat_param}&display_type=Card"
    )

    articles: List[Dict] = []
    effective_max = max_pages

    for page_num in range(1, effective_max + 1):
        page_url = base_url if page_num == 1 else f"{base_url}&page={page_num}"
        html = await _fetch_doe_page(session, page_url)
        if not html:
            logger.warning(
                f"[{subcategory}] Failed to fetch page {page_num} — stopping"
            )
            break

        # On the first page, detect max pages from the pagination combobox
        if page_num == 1:
            detected_max = _detect_max_page(html)
            if detected_max > 1:
                # Cap at max_pages param (which is already the user's limit)
                effective_max = min(max_pages, detected_max)
                logger.info(
                    f"[{subcategory}] Detected {detected_max} total pages, "
                    f"will fetch up to {effective_max}"
                )

        # Try __NUXT__ extraction first (structured data)
        page_articles = _extract_nuxt_articles(html)
        if not page_articles:
            logger.debug(
                f"[{subcategory}] __NUXT__ extraction failed for page {page_num}, "
                f"falling back to HTML parsing"
            )
            page_articles = _extract_articles_from_html(html)

        if not page_articles:
            logger.info(
                f"[{subcategory}] No articles found on page {page_num} — stopping"
            )
            break

        added = 0
        for a in page_articles:
            aid = a.get("id")
            title = a.get("title", "")
            # Deduplicate by id, or by title if no id
            key = aid if aid else title
            if key and key not in seen_ids:
                articles.append(a)
                seen_ids.add(key)
                added += 1

        logger.info(
            f"[{subcategory}] Page {page_num}/{effective_max}: "
            f"{added} new articles (subtotal: {len(articles)})"
        )

        if added == 0:
            # All items on this page were duplicates — we've caught up
            logger.info(
                f"[{subcategory}] No new articles on page {page_num} — stopping"
            )
            break

        # Rate limit between pages (skip delay after last page)
        if page_num < effective_max:
            await asyncio.sleep(PAGE_DELAY)

    return articles


async def fetch_doe_issuances(full: bool = False) -> List[Dict]:
    """
    Fetch DOE issuances with pagination from the Laws and Issuances listing.

    All DOE subcategory URLs return the same article listing (the filter is
    cosmetic in SSR HTML), so we paginate through a single subcategory URL
    to get all issuance types (DCs, DOs, MCs, AOs, SOs, etc.).

    Args:
        full: If True, fetch ALL pages (historical backfill — may take several
              minutes and fetch 500+ items).
              If False (default), fetch only the first DEFAULT_MAX_PAGES pages
              (~20 most recent items for daily refresh).

    Returns:
        List of normalized issuance dicts ready for MongoDB upsert.
    """
    max_pages = 999 if full else DEFAULT_MAX_PAGES

    all_articles: List[Dict] = []
    seen_ids: set = set()

    async with aiohttp.ClientSession() as session:
        logger.info(
            f"Scraping DOE issuances (mode={'full' if full else 'incremental'}, "
            f"max_pages={'ALL' if full else max_pages})"
        )
        all_articles = await _fetch_subcategory(
            session, DOE_LISTING_SUBCATEGORY, max_pages, seen_ids
        )
        logger.info(f"DOE scrape done — {len(all_articles)} articles fetched")

    # Normalize to our schema
    issuances = []
    for article in all_articles:
        title = article.get("title", "")
        content_html = article.get("content", "")
        summary = _clean_html_to_summary(content_html)
        category = _classify_issuance(title)

        # Extract circular/order number from title
        number_match = re.search(
            r"(?:No\.?\s*)?([A-Z]{2,}\d{4}-\d{2}-\d+|[A-Z]+\d{4}-\d+-\d+)", title
        )
        circular_number = number_match.group(1) if number_match else None

        # Build attachment URLs
        attachments = []
        for att in article.get("attachments", []):
            content_url = att.get("contentUrl", "")
            if content_url.startswith("/"):
                content_url = f"{DOE_CMS_BASE}{content_url}"
            attachments.append(
                {
                    "title": att.get("title", ""),
                    "url": content_url,
                    "format": att.get("encodingFormat", ""),
                }
            )

        # Article URL — strip ?redirect= query params (ugly and long)
        link = article.get("link", "")
        link = re.split(r"\?redirect=", link)[0]
        if link.startswith("/"):
            link = f"{DOE_BASE}{link}"

        issuances.append(
            {
                "doe_id": article.get("id"),
                "circular_number": circular_number,
                "title": title,
                "category": category,
                "summary": summary,
                "date_published": article.get("datePublished"),
                "url": link,
                "attachments": attachments,
            }
        )

    logger.info(f"Fetched {len(issuances)} DOE issuances total")
    return issuances


# ──────────────────────────────────────────────
# MongoDB upsert
# ──────────────────────────────────────────────


async def run_doe_update(db, full: bool = False) -> dict:
    """
    Fetch real DOE issuances and upsert to MongoDB.

    Args:
        db: Motor database instance.
        full: If True, do a full historical backfill (all pages).
              If False (default), incremental update (first few pages).

    Returns a result dict with success flag and details.
    """
    try:
        issuances = await fetch_doe_issuances(full=full)
        if not issuances:
            return {
                "success": False,
                "error": "No issuances fetched from DOE website",
            }

        now = datetime.now(timezone.utc)
        updated = 0

        for item in issuances:
            doc = {
                **item,
                "scraped_at": now,
                "data_source": "doe.gov.ph (SSR scrape)",
            }

            # Upsert by doe_id (unique article identifier)
            if item.get("doe_id"):
                await db.doe_circulars.update_one(
                    {"doe_id": item["doe_id"]},
                    {"$set": doc, "$setOnInsert": {"created_at": now}},
                    upsert=True,
                )
            else:
                # Fallback: upsert by title
                await db.doe_circulars.update_one(
                    {"title": item["title"]},
                    {"$set": doc, "$setOnInsert": {"created_at": now}},
                    upsert=True,
                )
            updated += 1

        logger.info(
            f"DOE update complete — {updated} issuances upserted at {now.isoformat()}"
        )
        return {
            "success": True,
            "issuances_updated": updated,
            "mode": "full_backfill" if full else "incremental",
            "timestamp": now.isoformat(),
            "categories": list(set(i["category"] for i in issuances)),
        }

    except Exception as e:
        logger.error(f"DOE update failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
