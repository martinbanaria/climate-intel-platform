"""
MongoDB tools for the Climate Intel Dev Agent.

Mirrors the certifi TLS connection pattern from backend/server.py:38-47 so the
agent connects to Atlas the same way the production backend does.

5 tools:
  query_collection    — find query on any collection
  check_data_freshness — staleness report across all collections
  collection_stats    — doc count + date range + field presence
  verify_upsert       — confirm a doc was upserted by key/value
  full_data_audit     — real-vs-mock audit (market_items, climate_metrics, etc.)
"""

import certifi
import json
import logging
import ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

import motor.motor_asyncio
from claude_agent_sdk import tool

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import MONGO_URL, DB_NAME

logger = logging.getLogger(__name__)

# ── Lazy singleton connection (same TLS pattern as server.py:38-47) ──────────

_client = None
_db = None


async def _get_db():
    global _client, _db
    if _db is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URL,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
        )
        _db = _client[DB_NAME]
    return _db


def _serialize(doc: dict) -> dict:
    """Convert ObjectId and datetime to JSON-serializable types."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["_id"] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = _serialize(v)
        elif isinstance(v, list):
            out[k] = [_serialize(i) if isinstance(i, dict) else i for i in v]
        else:
            out[k] = v
    return out


# ── Tool 1: query_collection ──────────────────────────────────────────────────

@tool(
    "query_collection",
    "Run a find query against any Climate Intel MongoDB collection. "
    "filter_json is a JSON string (e.g. '{\"category\": \"vegetables\"}' or '{}' for all). "
    "sort_json is a JSON string like '{\"date_published\": -1}'. "
    "limit defaults to 10 when omitted.",
    {"collection": str, "filter_json": str, "limit": int, "sort_json": str},
)
async def query_collection(args: dict) -> dict:
    collection = args["collection"]
    limit = int(args.get("limit") or 10)
    try:
        filter_doc = json.loads(args.get("filter_json") or "{}")
    except json.JSONDecodeError as e:
        return {"content": [{"type": "text", "text": f"Invalid filter_json: {e}"}]}
    try:
        sort_doc = json.loads(args.get("sort_json") or "{}")
    except json.JSONDecodeError:
        sort_doc = {}

    try:
        db = await _get_db()
        coll = db[collection]
        cursor = coll.find(filter_doc)
        if sort_doc:
            cursor = cursor.sort(list(sort_doc.items()))
        cursor = cursor.limit(limit)
        docs = [_serialize(d) async for d in cursor]
        result = {
            "collection": collection,
            "count": len(docs),
            "filter": filter_doc,
            "docs": docs,
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"query_collection error: {e}")
        return {"content": [{"type": "text", "text": f"Error querying {collection}: {e}"}]}


# ── Tool 2: check_data_freshness ──────────────────────────────────────────────

_COLLECTIONS = {
    "market_items":    "updatedAt",
    "climate_metrics": "lastUpdated",
    "doe_circulars":   "scraped_at",
    "energy_news":     "published_at",
}


@tool(
    "check_data_freshness",
    "Check data freshness across all Climate Intel collections. "
    "threshold_hours is the max acceptable age in hours (default 48).",
    {"threshold_hours": int},
)
async def check_data_freshness(args: dict) -> dict:
    threshold_hours = int(args.get("threshold_hours") or 48)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=threshold_hours)

    try:
        db = await _get_db()
        report = []
        for coll_name, ts_field in _COLLECTIONS.items():
            coll = db[coll_name]
            total = await coll.count_documents({})
            # Most-recent doc by timestamp field
            latest_doc = await coll.find_one(
                {ts_field: {"$exists": True}},
                sort=[(ts_field, -1)],
                projection={ts_field: 1},
            )
            if latest_doc and latest_doc.get(ts_field):
                ts = latest_doc[ts_field]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_hours = (now - ts).total_seconds() / 3600
                stale = ts < cutoff
                report.append({
                    "collection": coll_name,
                    "docs": total,
                    "last_updated": ts.isoformat(),
                    "age_hours": round(age_hours, 1),
                    "stale": stale,
                })
            else:
                report.append({
                    "collection": coll_name,
                    "docs": total,
                    "last_updated": None,
                    "age_hours": None,
                    "stale": True,
                })

        stale_count = sum(1 for r in report if r["stale"])
        result = {
            "threshold_hours": threshold_hours,
            "checked_at": now.isoformat(),
            "stale_collections": stale_count,
            "collections": report,
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"check_data_freshness error: {e}")
        return {"content": [{"type": "text", "text": f"Error checking freshness: {e}"}]}


# ── Tool 3: collection_stats ──────────────────────────────────────────────────

@tool(
    "collection_stats",
    "Get document count, date range, and top field values for a MongoDB collection.",
    {"collection": str},
)
async def collection_stats(args: dict) -> dict:
    collection = args["collection"]
    try:
        db = await _get_db()
        coll = db[collection]
        total = await coll.count_documents({})

        # Sample up to 5 docs to infer schema
        sample_docs = [_serialize(d) async for d in coll.find({}).limit(5)]
        fields = set()
        for doc in sample_docs:
            fields.update(doc.keys())

        # Date range
        date_range = {}
        for ts_field in ("updatedAt", "lastUpdated", "scraped_at", "published_at", "date_published"):
            if ts_field in fields:
                oldest = await coll.find_one({ts_field: {"$exists": True}}, sort=[(ts_field, 1)])
                newest = await coll.find_one({ts_field: {"$exists": True}}, sort=[(ts_field, -1)])
                if oldest and newest:
                    date_range = {
                        "field": ts_field,
                        "oldest": _serialize(oldest).get(ts_field),
                        "newest": _serialize(newest).get(ts_field),
                    }
                break

        result = {
            "collection": collection,
            "total_docs": total,
            "fields": sorted(fields - {"_id"}),
            "date_range": date_range,
            "sample": sample_docs[:2],
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"collection_stats error: {e}")
        return {"content": [{"type": "text", "text": f"Error getting stats for {collection}: {e}"}]}


# ── Tool 4: verify_upsert ─────────────────────────────────────────────────────

@tool(
    "verify_upsert",
    "Confirm a specific document was correctly upserted in a collection. "
    "Looks up match_field == match_value and returns the doc if found.",
    {"collection": str, "match_field": str, "match_value": str},
)
async def verify_upsert(args: dict) -> dict:
    collection = args["collection"]
    match_field = args["match_field"]
    match_value = args["match_value"]

    # Try numeric conversion for id fields
    query_value: object = match_value
    try:
        query_value = int(match_value)
    except (ValueError, TypeError):
        pass

    try:
        db = await _get_db()
        doc = await db[collection].find_one({match_field: query_value})
        if doc:
            result = {"found": True, "doc": _serialize(doc)}
        else:
            result = {"found": False, "collection": collection, "match_field": match_field, "match_value": match_value}
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"verify_upsert error: {e}")
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}


# ── Tool 5: full_data_audit ───────────────────────────────────────────────────

@tool(
    "full_data_audit",
    "Run a comprehensive real-vs-mock data audit across all Climate Intel collections. "
    "Checks: market_items >= 200, climate_metrics == 8, doe_circulars >= 1, "
    "energy_news >= 1. Pass target='prod' or target='local'.",
    {"target": str},
)
async def full_data_audit(args: dict) -> dict:
    try:
        db = await _get_db()
        now = datetime.now(timezone.utc)

        checks = []

        # market_items
        mi_count = await db.market_items.count_documents({})
        checks.append({
            "collection": "market_items",
            "count": mi_count,
            "expected": ">= 200",
            "pass": mi_count >= 200,
            "note": "DA Bantay Presyo PDF commodity prices",
        })

        # climate_metrics
        cm_count = await db.climate_metrics.count_documents({})
        checks.append({
            "collection": "climate_metrics",
            "count": cm_count,
            "expected": "== 8",
            "pass": cm_count == 8,
            "note": "WeatherAPI.com: Temp, Humidity, Rainfall, UV, AQI, Wind, Soil, Drought",
        })

        # doe_circulars
        dc_count = await db.doe_circulars.count_documents({})
        checks.append({
            "collection": "doe_circulars",
            "count": dc_count,
            "expected": ">= 1",
            "pass": dc_count >= 1,
            "note": "doe.gov.ph SSR scrape — issuances",
        })

        # energy_news
        en_count = await db.energy_news.count_documents({})
        checks.append({
            "collection": "energy_news",
            "count": en_count,
            "expected": ">= 1",
            "pass": en_count >= 1,
            "note": "NewsData.io energy news",
        })

        # Summary
        passed = sum(1 for c in checks if c["pass"])
        result = {
            "audited_at": now.isoformat(),
            "passed": passed,
            "total": len(checks),
            "all_pass": passed == len(checks),
            "checks": checks,
            "mock_data_remaining": [
                "PPA status (doe_document_scraper.py — ERC blocked by Cloudflare)",
                "Energy market outlook (hardcoded strings in server.py)",
                "ClimateImpact key insights (static JSX in ClimateImpact.jsx:144-148)",
            ],
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"full_data_audit error: {e}")
        return {"content": [{"type": "text", "text": f"Audit error: {e}"}]}
