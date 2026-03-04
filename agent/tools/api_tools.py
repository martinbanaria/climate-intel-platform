"""
API tools for the Climate Intel Dev Agent.

4 tools for probing the backend REST API (prod or local):
  check_api_health     — GET /api/health
  probe_endpoint       — GET any /api/* path
  trigger_integration  — POST to /api/integration/* endpoints
  check_backend_status — Comprehensive probe across all endpoint groups
"""

import json
import logging
from pathlib import Path
import sys

import aiohttp
from claude_agent_sdk import tool

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import BACKEND_PROD_URL, BACKEND_LOCAL_URL

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=60)


def _base_url(target: str) -> str:
    return BACKEND_LOCAL_URL if str(target).lower() == "local" else BACKEND_PROD_URL


# ── Tool 1: check_api_health ──────────────────────────────────────────────────

@tool(
    "check_api_health",
    "Check whether the Climate Intel backend API is alive. "
    "target is 'prod' (default) or 'local'. Returns status, version, and uptime.",
    {"target": str},
)
async def check_api_health(args: dict) -> dict:
    target = args.get("target") or "prod"
    base = _base_url(target)
    url = f"{base}/api/health"

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.get(url) as resp:
                body = await resp.json(content_type=None)
                result = {
                    "target": target,
                    "url": url,
                    "status_code": resp.status,
                    "healthy": resp.status == 200,
                    "body": body,
                }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        logger.error(f"check_api_health error: {e}")
        return {"content": [{"type": "text", "text": f"Health check failed for {url}: {e}"}]}


# ── Tool 2: probe_endpoint ────────────────────────────────────────────────────

@tool(
    "probe_endpoint",
    "GET any Climate Intel API path and inspect the response. "
    "path should start with /api (e.g. '/api/market-items'). "
    "target is 'prod' (default) or 'local'. "
    "Returns status code, response time ms, and a sample of the response body.",
    {"path": str, "target": str},
)
async def probe_endpoint(args: dict) -> dict:
    path = args.get("path") or "/api/health"
    target = args.get("target") or "prod"
    base = _base_url(target)
    if not path.startswith("/"):
        path = "/" + path
    url = f"{base}{path}"

    import time
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            t0 = time.monotonic()
            async with session.get(url) as resp:
                elapsed_ms = round((time.monotonic() - t0) * 1000)
                text = await resp.text()
                # Try to parse as JSON; fall back to raw text
                try:
                    body = json.loads(text)
                    # Truncate large arrays for readability
                    if isinstance(body, list) and len(body) > 5:
                        sample = body[:5]
                        note = f"[...{len(body) - 5} more items omitted]"
                    elif isinstance(body, dict):
                        sample = body
                        note = None
                    else:
                        sample = body
                        note = None
                except json.JSONDecodeError:
                    sample = text[:500]
                    note = "response is not JSON"

                result = {
                    "url": url,
                    "status_code": resp.status,
                    "response_ms": elapsed_ms,
                    "body_sample": sample,
                }
                if note:
                    result["note"] = note

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}
    except Exception as e:
        logger.error(f"probe_endpoint error: {e}")
        return {"content": [{"type": "text", "text": f"Error probing {url}: {e}"}]}


# ── Tool 3: trigger_integration ───────────────────────────────────────────────

_KNOWN_INTEGRATION_ENDPOINTS = [
    "run-da-bantay-presyo",
    "run-comprehensive-real-data",
    "run-weather-update",
    "run-doe-update",
    "status",
]


@tool(
    "trigger_integration",
    "POST (or GET for 'status') to a Climate Intel integration endpoint. "
    "endpoint is the last path segment, e.g. 'run-da-bantay-presyo', "
    "'run-comprehensive-real-data', 'run-weather-update', 'run-doe-update', or 'status'. "
    "target is 'prod' (default) or 'local'. "
    "params_json is an optional JSON string of query params, e.g. '{\"days\": 7}'.",
    {"endpoint": str, "target": str, "params_json": str},
)
async def trigger_integration(args: dict) -> dict:
    endpoint = (args.get("endpoint") or "status").strip("/")
    target = args.get("target") or "prod"
    base = _base_url(target)
    url = f"{base}/api/integration/{endpoint}"

    try:
        params = json.loads(args.get("params_json") or "{}")
    except json.JSONDecodeError:
        params = {}

    method = "GET" if endpoint == "status" else "POST"

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            req = session.get if method == "GET" else session.post
            async with req(url, params=params) as resp:
                try:
                    body = await resp.json(content_type=None)
                except Exception:
                    body = await resp.text()
                result = {
                    "method": method,
                    "url": url,
                    "params": params,
                    "status_code": resp.status,
                    "success": resp.status == 200,
                    "body": body,
                }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}
    except Exception as e:
        logger.error(f"trigger_integration error: {e}")
        return {"content": [{"type": "text", "text": f"Error calling {url}: {e}"}]}


# ── Tool 4: check_backend_status ──────────────────────────────────────────────

_PROBE_PATHS = [
    "/api/health",
    "/api/market-items",
    "/api/analytics/market-analytics",
    "/api/energy/grid-status",
    "/api/energy/analytics",
    "/api/energy/news",
    "/api/energy/doe-circulars",
    "/api/climate-metrics",
    "/api/integration/status",
]


@tool(
    "check_backend_status",
    "Run a comprehensive health probe across all Climate Intel API endpoint groups. "
    "target is 'prod' (default) or 'local'. "
    "Returns status code and response time for each endpoint.",
    {"target": str},
)
async def check_backend_status(args: dict) -> dict:
    target = args.get("target") or "prod"
    base = _base_url(target)

    import time
    results = []

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        for path in _PROBE_PATHS:
            url = f"{base}{path}"
            try:
                t0 = time.monotonic()
                async with session.get(url) as resp:
                    elapsed_ms = round((time.monotonic() - t0) * 1000)
                    try:
                        body = await resp.json(content_type=None)
                        # Quick data presence check
                        if isinstance(body, list):
                            data_note = f"{len(body)} items"
                        elif isinstance(body, dict):
                            keys = list(body.keys())[:4]
                            data_note = f"keys: {keys}"
                        else:
                            data_note = str(body)[:80]
                    except Exception:
                        data_note = "non-JSON response"

                    results.append({
                        "path": path,
                        "status": resp.status,
                        "ok": resp.status == 200,
                        "ms": elapsed_ms,
                        "data": data_note,
                    })
            except Exception as e:
                results.append({
                    "path": path,
                    "status": None,
                    "ok": False,
                    "ms": None,
                    "error": str(e),
                })

    healthy = sum(1 for r in results if r["ok"])
    summary = {
        "target": target,
        "base_url": base,
        "endpoints_checked": len(results),
        "healthy": healthy,
        "degraded": len(results) - healthy,
        "all_ok": healthy == len(results),
        "results": results,
    }
    return {"content": [{"type": "text", "text": json.dumps(summary, indent=2)}]}
