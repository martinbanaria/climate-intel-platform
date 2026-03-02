"""
DOE Issuances integration for Climate Intel.
Scrapes real Department Circulars, Department Orders, and other issuances
from the DOE Philippines website (doe.gov.ph) via Nuxt.js SSR HTML.

The DOE site is a Nuxt.js SPA with server-side rendering. The SSR HTML
contains a `window.__NUXT__` script block with structured article data.
We parse this directly with regex + json rather than relying on fragile
HTML selectors.

Also fetches DOE "What's New" articles for energy market news/advisories.
"""

import aiohttp
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DOE_BASE = "https://doe.gov.ph"
DOE_CMS_BASE = "https://prod-cms.doe.gov.ph"

# Issuance subcategories to scrape (all under category=Issuances)
ISSUANCE_TYPES = [
    "Department Circular",
    "Department Order",
    "Memorandum Circular",
    "Administrative Order",
]

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
    match = re.search(r'window\.__NUXT__\s*=\s*(.+?);\s*</script>', html, re.DOTALL)
    if not match:
        logger.warning("Could not find __NUXT__ in DOE HTML")
        return []

    nuxt_js = match.group(1)

    # Extract the articles array from the JS blob.
    # Articles are inside "articles":[...] — find this JSON array.
    articles_match = re.search(r'"articles"\s*:\s*(\[.*?\])\s*,\s*"', nuxt_js, re.DOTALL)
    if not articles_match:
        # Fallback: try without trailing comma constraint
        articles_match = re.search(r'"articles"\s*:\s*(\[.*?\])\s*\}', nuxt_js, re.DOTALL)
    if not articles_match:
        logger.warning("Could not extract articles array from __NUXT__")
        return []

    raw = articles_match.group(1)

    # The JS may use `undefined` or `null` — normalize for JSON parsing
    raw = raw.replace('undefined', 'null')

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
        if not link_tag or not link_tag.get("href", "").startswith("/articles/"):
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
            if text and text not in ("Click link to view complete file/download PDF file:",
                                     "Published at:", "Date Published (mm/dd/yyyy):",
                                     "Date Submitted to ONAR (mm/dd/yyyy):"):
                content_parts.append(text)

        # Attachments: links to prod-cms.doe.gov.ph
        attachments = []
        for a in card.find_all("a", href=True):
            href = a["href"]
            if "prod-cms.doe.gov.ph" in href or href.startswith("/documents/"):
                attachments.append({
                    "title": a.get_text(strip=True),
                    "contentUrl": href,
                    "encodingFormat": "application/pdf" if href.endswith(".pdf") or "pdf" in href else "",
                })

        # Extract article ID from URL: /articles/2933685--slug
        article_id = None
        id_match = re.match(r'/articles/(\d+)--', url)
        if id_match:
            article_id = int(id_match.group(1))

        articles.append({
            "id": article_id,
            "title": title,
            "link": url,
            "content": " ".join(content_parts[:2]),  # First 2 paragraphs as summary
            "datePublished": date_published,
            "attachments": attachments,
        })

    return articles


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
# Fetch DOE issuances
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


async def fetch_doe_issuances(max_pages: int = 5) -> List[Dict]:
    """
    Fetch recent DOE issuances from the Laws and Issuances page.
    Returns a list of normalized issuance dicts.

    The URL with subcategory=Department+Circular unlocks all ~137 pages of
    issuances (all types, not just DCs — the filter is cosmetic in SSR).
    We fetch max_pages pages (default 5 = ~20 most recent issuances).
    """
    # NOTE: Using subcategory=Department+Circular unlocks full pagination
    # (137 pages). The category=Issuances URL only shows 2 pages (featured only).
    base_url = (
        f"{DOE_BASE}/articles/group/laws-and-issuances"
        f"?subcategory=Department+Circular&display_type=Card"
    )

    articles: List[Dict] = []
    seen_ids: set = set()

    async with aiohttp.ClientSession() as session:
        for page_num in range(1, max_pages + 1):
            page_url = base_url if page_num == 1 else f"{base_url}&page={page_num}"
            html = await _fetch_doe_page(session, page_url)
            if not html:
                break

            # Try __NUXT__ extraction first (structured data)
            page_articles = _extract_nuxt_articles(html)
            if not page_articles:
                logger.info(f"__NUXT__ extraction failed for page {page_num}, falling back to HTML parsing")
                page_articles = _extract_articles_from_html(html)

            if not page_articles:
                logger.info(f"No articles found on page {page_num} — stopping pagination")
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

            logger.info(f"DOE page {page_num}: {added} new articles (total so far: {len(articles)})")

            if added == 0:
                # All items on this page were duplicates — we've caught up
                break

    # Normalize to our schema
    issuances = []
    for article in articles:
        title = article.get("title", "")
        content_html = article.get("content", "")
        summary = _clean_html_to_summary(content_html)
        category = _classify_issuance(title)

        # Extract circular/order number from title
        number_match = re.search(
            r'(?:No\.?\s*)?([A-Z]{2,}\d{4}-\d{2}-\d+|[A-Z]+\d{4}-\d+-\d+)',
            title
        )
        circular_number = number_match.group(1) if number_match else None

        # Build attachment URLs
        attachments = []
        for att in article.get("attachments", []):
            content_url = att.get("contentUrl", "")
            if content_url.startswith("/"):
                content_url = f"{DOE_CMS_BASE}{content_url}"
            attachments.append({
                "title": att.get("title", ""),
                "url": content_url,
                "format": att.get("encodingFormat", ""),
            })

        # Article URL — strip ?redirect= query params (ugly and long)
        link = article.get("link", "")
        link = re.split(r'\?redirect=', link)[0]
        if link.startswith("/"):
            link = f"{DOE_BASE}{link}"

        issuances.append({
            "doe_id": article.get("id"),
            "circular_number": circular_number,
            "title": title,
            "category": category,
            "summary": summary,
            "date_published": article.get("datePublished"),
            "url": link,
            "attachments": attachments,
        })

    logger.info(f"Fetched {len(issuances)} DOE issuances")
    return issuances


# ──────────────────────────────────────────────
# MongoDB upsert
# ──────────────────────────────────────────────

async def run_doe_update(db) -> dict:
    """
    Fetch real DOE issuances and upsert to MongoDB.
    Returns a result dict with success flag and details.
    """
    try:
        issuances = await fetch_doe_issuances()
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

        logger.info(f"DOE update complete — {updated} issuances upserted at {now.isoformat()}")
        return {
            "success": True,
            "issuances_updated": updated,
            "timestamp": now.isoformat(),
            "categories": list(set(i["category"] for i in issuances)),
        }

    except Exception as e:
        logger.error(f"DOE update failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
