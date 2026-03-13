"""
PPA/RE Service Contract Scraper
Downloads and parses DOE legacy site PDFs of awarded RE projects.
Source: legacy.doe.gov.ph/renewable-energy/awarded{type}
"""
import aiohttp
import asyncio
import io
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Latest PDFs (as of April 2025) for each RE technology
PDF_SOURCES = {
    "Solar": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Solar%20as%20of%20April%202025.pdf",
        "own_use": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Solar%20%28Own-Use%29%20as%20of%20April%202025.pdf",
    },
    "Wind": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Wind%20as%20of%20April%202025.pdf",
    },
    "Hydropower": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Hydropower%20as%20of%20April%202025.pdf",
        "own_use": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Hydropower%20%28Own-Use%29%20as%20of%20April%202025.pdf",
    },
    "Biomass": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Biomass%20as%20of%20April%202025.pdf",
        "own_use": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Biomass%20%28Own-Use%29%20as%20of%20April%202025.pdf",
    },
    "Ocean": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Ocean%20as%20of%20April%202025.pdf",
    },
    "Geothermal": {
        "commercial": "https://legacy.doe.gov.ph/sites/default/files/pdf/renewable_energy/Awarded%20Geothermal%20as%20of%20April%202025.pdf",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def download_pdf(url: str) -> Optional[bytes]:
    """Download a PDF from URL, return bytes or None on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    logger.info(f"Downloaded {len(data)} bytes from {url.split('/')[-1]}")
                    return data
                else:
                    logger.warning(f"HTTP {resp.status} for {url}")
                    return None
    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        return None


def parse_pdf_text(pdf_bytes: bytes) -> str:
    """Extract all text from PDF bytes using PyPDF2."""
    import PyPDF2
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return "\n".join(pages_text)


def parse_re_contracts(text: str, technology: str, contract_type: str = "commercial") -> List[Dict]:
    """
    Parse awarded RE contract entries from extracted PDF text.

    Each row in the PDF has: ISLAND, REGION, PROVINCE, CITY, PROJECT NAME,
    COMPANY NAME, STAGE OF CONTRACT, POTENTIAL CAPACITY (MW), INSTALLED CAPACITY (MW).

    We use the stage keywords as anchors to split entries.
    """
    # Join all lines (company names wrap across lines)
    flat = " ".join(text.split("\n"))

    # Match pattern: Stage keyword followed by capacity numbers
    entry_re = re.compile(
        r"(Development|Pre-Development|Commercial Operation)\s+([\d,.]+)\s*([\d,.]*)"
    )

    entries = []
    prev_end = 0
    prev_island = ""

    for match in entry_re.finditer(flat):
        prefix = flat[prev_end:match.start()].strip()
        prev_end = match.end()

        stage = match.group(1)
        potential_mw = _parse_float(match.group(2))
        installed_mw = _parse_float(match.group(3)) if match.group(3) else 0.0

        # Skip header/total/summary rows
        if any(skip in prefix for skip in ["ISLAND", "Grand Total", "POTENTIAL CAPACITY", "STAGE OF CONTRACT"]):
            continue
        if not prefix or len(prefix) < 5:
            continue
        # Skip island total lines
        if re.match(r"^(Luzon|Visayas|Mindanao)\s+Total$", prefix.strip()):
            continue
        if prefix.strip().endswith("Total"):
            continue

        # Extract island
        island = ""
        for isl in ["Luzon", "Visayas", "Mindanao"]:
            if isl in prefix:
                island = isl
                prefix = prefix.replace(isl, "", 1).strip()
                break
        if not island:
            island = prev_island
        else:
            prev_island = island

        # Split prefix into project name and company name
        project_name, company = _split_project_company(prefix, technology)

        if not project_name:
            continue

        entries.append({
            "project_name": project_name.strip(),
            "developer": company.strip(),
            "technology": technology,
            "contract_type": contract_type,
            "island": island,
            "stage": stage,
            "potential_capacity_mw": potential_mw,
            "installed_capacity_mw": installed_mw,
        })

    return entries


def _parse_float(s: str) -> float:
    """Parse a float from string, handling commas."""
    try:
        return float(s.replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _split_project_company(prefix: str, technology: str) -> tuple:
    """
    Split the prefix text into (project_name, company_name).
    Project names typically end with 'Project', 'Plant', 'System', 'Facility', 'PV'.
    """
    # Look for project name ending keywords
    proj_keywords = [
        r"Power Project(?:\s*[-–]\s*Phase\s*\w+)?",
        r"Energy Project(?:\s*[-–]\s*Phase\s*\w+)?",
        r"Power Plant(?:\s*[-–]\s*Phase\s*\w+)?",
        r"Solar PV(?:\s*[-–]\s*Phase\s*\w+)?",
        r"PV System",
        r"Power Station",
        r"Power Facility",
        r"Solar Rooftop",
        r"Wind Farm",
    ]

    pattern = "|".join(proj_keywords)
    # Find the LAST occurrence of a project keyword (handles cases where location
    # also contains these words)
    matches = list(re.finditer(pattern, prefix, re.IGNORECASE))

    if matches:
        last_match = matches[-1]
        project_name = prefix[:last_match.end()].strip()
        company = prefix[last_match.end():].strip()

        # Clean location prefix from project name
        # Region codes like "I", "II", "III", "CAR", "NCR", "IV-A" etc.
        project_name = re.sub(
            r"^(?:(?:CAR|NCR|ARMM|BARMM|CARAGA)\s+|(?:I{1,3}|IV-?[AB]?|V|VI{0,3}|IX|X{1,3}|XI{1,3})\s+)?",
            "", project_name
        ).strip()

        return project_name, company

    # Fallback: return full prefix as project name
    return prefix, ""


async def scrape_all_contracts(db=None) -> Dict:
    """
    Download all latest DOE RE contract PDFs, parse them, and optionally upsert to MongoDB.
    Returns summary stats.
    """
    all_entries = []
    errors = []

    for tech, urls in PDF_SOURCES.items():
        for ctype, url in urls.items():
            logger.info(f"Processing {tech} ({ctype})...")
            pdf_bytes = await download_pdf(url)
            if not pdf_bytes:
                errors.append(f"Failed to download {tech} ({ctype})")
                continue

            try:
                text = parse_pdf_text(pdf_bytes)
                entries = parse_re_contracts(text, tech, ctype)
                logger.info(f"  Parsed {len(entries)} {tech} ({ctype}) entries")
                all_entries.extend(entries)
            except Exception as e:
                logger.error(f"Parse error for {tech} ({ctype}): {e}")
                errors.append(f"Parse error for {tech} ({ctype}): {str(e)}")

            # Rate limit between downloads
            await asyncio.sleep(1.0)

    # Upsert to MongoDB if db is provided
    upserted = 0
    if db is not None:
        collection = db.ppa_contracts
        for entry in all_entries:
            # Create a unique key from project name + developer + technology
            doc_id = f"{entry['project_name']}|{entry['developer']}|{entry['technology']}"
            entry["doc_id"] = doc_id
            entry["scraped_at"] = datetime.utcnow()
            entry["source"] = "DOE Legacy Site"
            entry["data_as_of"] = "April 2025"

            result = await collection.update_one(
                {"doc_id": doc_id},
                {"$set": entry},
                upsert=True,
            )
            if result.upserted_id or result.modified_count:
                upserted += 1

        # Create index on doc_id
        await collection.create_index("doc_id", unique=True)
        await collection.create_index("technology")
        await collection.create_index("stage")

        logger.info(f"Upserted {upserted} contracts to MongoDB")

    # Build summary
    from collections import Counter
    tech_counts = Counter(e["technology"] for e in all_entries)
    stage_counts = Counter(e["stage"] for e in all_entries)
    total_potential = sum(e["potential_capacity_mw"] for e in all_entries)
    total_installed = sum(e["installed_capacity_mw"] for e in all_entries)

    return {
        "success": True,
        "total_contracts": len(all_entries),
        "upserted": upserted,
        "by_technology": dict(tech_counts),
        "by_stage": dict(stage_counts),
        "total_potential_mw": round(total_potential, 2),
        "total_installed_mw": round(total_installed, 2),
        "errors": errors,
        "scraped_at": datetime.utcnow().isoformat(),
    }
