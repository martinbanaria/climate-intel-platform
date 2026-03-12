# Climate Intel — Project Context for Claude

## What This App Is
Climate-Smart Market Intelligence Platform for the Philippines.
- Tracks 215+ commodity prices from official DA Bantay Presyo PDFs
- Energy intelligence: grid status, WESM prices, PPAs, DOE circulars, energy news
- Climate impact analysis correlating weather to market prices
- Target users: Filipino buyers, policymakers, farmers

## Stack
| Layer | Tech |
|---|---|
| Frontend | React 19, TailwindCSS, Shadcn UI, Recharts, React Router 7 |
| Backend | FastAPI (Python 3.9), Motor (async MongoDB) |
| Database | MongoDB Atlas (Singapore region) |
| Deployment | Render.com (backend), Vercel (frontend) |
| Scheduler | GitHub Actions cron (NOT scheduler.py) |

## URLs
- Frontend (prod): https://climate-intel-main.vercel.app
- Backend (prod): https://climate-intel-api.onrender.com
- GitHub: https://github.com/martinbanaria/climate-intel-platform
- MongoDB: `mongodb+srv://climateintel_admin:Sv5sVFw7gdHtydlq@climate-intel.q1jjn3g.mongodb.net/?appName=climate-intel`

## Key Files
```
backend/
  server.py                          # All API endpoints
  scheduler.py                       # DO NOT USE — Render free tier sleeps, kills it
  services/
    daily_price_parser.py            # DA Bantay Presyo daily PDF downloader/parser (WORKING)
    real_data_integration.py         # /run-da-bantay-presyo endpoint service (FIXED)
    comprehensive_real_data.py       # 7-day history builder using daily_price_parser (WORKING)
    weather_integration.py           # NEW — WeatherAPI.com -> climate_metrics MongoDB (WORKING)
    newsdata_integration.py          # Real energy news via NewsData.io API (WORKING)
    energy_grid_scraper.py           # IEMOP WESM price scraper (REAL, 1-hr cache)
    ngcp_scraper.py                  # NGCP grid MW Playwright scraper (REAL, 30-min cache)
    doe_integration.py               # NEW — real DOE issuances via SSR scrape -> MongoDB
    doe_document_scraper.py          # Legacy mock PPA data (ERC blocked by Cloudflare)
    doe_fuel_integration.py          # DOE fuel price scraper
    telegram_bot.py                  # NEW — Telegram Bot API broadcaster (send_message, broadcast, build_daily_alert)
    historical_backfill.py           # NEW — DA PDF backfill over arbitrary date range → price_history collection
    web_crawler.py                   # Generic async scraper (BeautifulSoup)
    ocr_service.py                   # PyPDF2 + PyTesseract

frontend/src/
  pages/Home.jsx                     # Main dashboard: market analytics + climate events + grid
  pages/EnergyIntelligence.jsx       # Energy grid/WESM/PPAs/news page
  pages/ClimateImpact.jsx            # Climate metrics page (real WeatherAPI data now)
  api/index.js                       # All Axios API calls
  # NOTE: Commodities, Analytics, Forecasts, Watchlist pages do NOT exist yet

.github/workflows/daily-refresh.yml  # Automated daily data refresh (ACTIVE)
.github/workflows/test.yml          # CI: pytest against production on push/PR
climate_intel.mongodb.js             # MongoDB playground queries (dev tool)
.mcp.json                            # MCP config for Claude Code CLI (fetch + playwright + mongodb)
.vscode/mcp.json                     # MCP config for VS Code Copilot Chat (fetch + playwright)
.vscode/settings.json                # python.terminal.useEnvFile: true
```

## Auto-Update Architecture (as of March 2026)
`scheduler.py` is NOT used — Render free tier sleeps after 15 min.

**GitHub Actions** runs `daily-refresh.yml` every weekday at 8 AM Manila time (00:00 UTC):
1. Wakes Render backend (6 retries x 60s)
2. POSTs `/api/integration/run-da-bantay-presyo`
3. POSTs `/api/integration/run-comprehensive-real-data?days=7`
4. POSTs `/api/integration/run-weather-update`
5. GETs `/api/integration/status`

## DA Bantay Presyo PDF URLs
Two patterns tried (both in `daily_price_parser.py` and `real_data_integration.py`):
```
https://www.da.gov.ph/wp-content/uploads/{year}/{month:02d}/Daily-Price-Index-{Month}-{day}-{year}.pdf
https://www.da.gov.ph/wp-content/uploads/{year}/{month:02d}/{Month}-{day}-{year}-DPI-AFC.pdf
```
DA only publishes on weekdays. Skip weekends in all downloaders.

## Key Bugs Fixed (March 2026)
1. `real_data_integration.py` — was trying weekly PDF URLs. Fixed to daily.
2. `real_data_integration.py` — literal backslash-n instead of newline. Fixed.
3. `real_data_integration.py` — regex raw strings double-escaped. Fixed.
4. GitHub Actions cold-start — curl timed out at 30s. Fixed to 60s with 6 retries.

---

## Real vs Mock Data Audit (March 2026)

### REAL DATA

| What | Source | Endpoint |
|------|--------|----------|
| 215+ commodity prices | DA Bantay Presyo PDFs | `GET /api/market-items` |
| 7-day price trends | DA Bantay Presyo PDFs | `GET /api/analytics/price-trends` |
| MURA/MAHAL/STABLE labels | Computed from real prices | `GET /api/analytics/market-analytics` |
| WESM electricity prices (PHP/MWh) | IEMOP MP_YYYYMMDD.csv | `GET /api/energy/analytics` |
| Grid status (STABLE/ELEVATED/TIGHT) | Derived from Luzon WESM | `GET /api/energy/grid-status` |
| Grid MW per region | NGCP Playwright scrape | `GET /api/energy/grid-status` |
| Energy news | NewsData.io API | `GET /api/energy/news` |
| Climate metrics (8 metrics) | WeatherAPI.com — FIXED Mar 2026 | `GET /api/climate-metrics` |
| DOE Issuances (circulars, orders) | doe.gov.ph SSR scrape — NEW Mar 2026 | `GET /api/energy/doe-circulars` |

### MOCK / HARDCODED DATA

| What | File | Endpoint |
|------|------|----------|
| PPA status | `doe_document_scraper.scrape_ppa_statuses()` | `GET /api/energy/ppa-status` |
| PPA analytics summary | derived from fake PPAs | `GET /api/energy/analytics` (ppa_summary) |
| Energy market outlook | hardcoded strings in `server.py` | `GET /api/energy/analytics` (market_outlook) |
| ClimateImpact key insights text | `ClimateImpact.jsx` lines 144-148 | frontend only |

---

## API Endpoints Reference
```
GET  /api/market-items
GET  /api/best-deals
GET  /api/analytics/market-analytics
GET  /api/analytics/price-trends
GET  /api/analytics/climate-correlations
GET  /api/analytics/buying-opportunities
GET  /api/analytics/predict/{item_id}
POST /api/integration/run-da-bantay-presyo
POST /api/integration/run-comprehensive-real-data
POST /api/integration/run-weather-update          # NEW
GET  /api/integration/status
GET  /api/energy/grid-status
GET  /api/energy/analytics
GET  /api/energy/news
POST /api/integration/run-doe-update           # NEW — scrape DOE issuances
GET  /api/energy/doe-circulars    # REAL — doe.gov.ph SSR scrape (was mock)
GET  /api/energy/ppa-status       # MOCK — ERC blocked by Cloudflare
GET  /api/climate-metrics         # REAL — WeatherAPI.com
POST /api/telegram/subscribe      # NEW — subscribe chat_id to daily alerts
POST /api/telegram/unsubscribe    # NEW
GET  /api/telegram/subscribers    # NEW — subscriber count
POST /api/telegram/send-daily-alert  # NEW — broadcast morning briefing to all subscribers
POST /api/integration/run-historical-backfill?start_date=&end_date=  # NEW — DA PDF backfill
GET  /api/price-history?name=&start_date=&end_date=  # NEW — daily snapshots from price_history
POST /api/crowdsource/report      # NEW — submit observed market price
GET  /api/crowdsource/reports     # NEW — list crowd reports (moderation)
GET  /api/crowdsource/summary     # NEW — crowd vs official price comparison
GET  /api/basket/cheapest         # Feature D — cheapest basket by comma-separated items
GET  /api/basket/templates        # Feature D — preset baskets with live prices
```

## WeatherAPI Integration (completed March 2026)
- Service: `backend/services/weather_integration.py`
- API key: `WEATHERAPI_KEY=dc16d669a7514585854151245260203`
- Manila coords: 14.5995 N, 120.9842 E — fetches `current.json?aqi=yes`
- 8 metrics upserted to `climate_metrics` MongoDB collection:
  - Temperature (C), Humidity (%), Rainfall (mm), UV Index
  - Air Quality Index (PM2.5 ug/m3), Wind Speed (km/h)
  - Soil Moisture (derived: humidity*0.6 + rainfall*0.4 scaled)
  - Drought Index (derived: inverse of soil moisture)
- Each doc: `{metric_name, value, unit, status, trend: [7 values], last_updated}`
- Confirmed working: returns `{"success": true, "metrics_updated": 8}`

---

## DOE Issuances Integration (completed March 2026)
- Service: `backend/services/doe_integration.py`
- DOE site is a Nuxt.js SPA with SSR — aiohttp fetches the rendered HTML
- Parses article cards with BeautifulSoup (h1 titles, time dates, p content, a attachments)
- `__NUXT__` JS extraction attempted first but falls back to HTML parsing (more reliable)
- Fetches from: `doe.gov.ph/articles/group/laws-and-issuances?subcategory=Department+Circular&display_type=Card`
- All subcategory URLs return the same article listing (subcategory filter is cosmetic in SSR) — only one URL needed
- Pagination: 137 pages × 4 items/page = ~548 issuances. Max page detected from `<select>` combobox in HTML
- Two modes: incremental (default, 5 pages = ~20 items) and full backfill (`?full=true`, all 137 pages)
- Rate limiting: 1.5s delay between page fetches
- Covers: Department Circulars, Department Orders, Memorandum Circulars, Special Orders, Implementing Guidelines, Joint Circulars, etc.
- Upserts to `doe_circulars` MongoDB collection by `doe_id`
- Each doc: `{doe_id, circular_number, title, category, summary, date_published, url, attachments[], scraped_at}`
- GitHub Actions step added after weather-update: `POST /api/integration/run-doe-update` (180s timeout)

### ERC PSA — NOT viable (March 2026)
- `erc.gov.ph` behind Cloudflare interactive challenge (403)
- Both aiohttp and Playwright blocked — cannot scrape
- PPA status endpoint remains mock data from `doe_document_scraper.py`

---

## Roadmap (In Priority Order)
- [x] A — GitHub Actions daily auto-refresh
- [x] B — Fix DA Bantay Presyo integration (3 bugs)
- [x] C — Replace mocked grid status + WESM prices with real scraped data
- [x] D — Cheapest Grocery Basket feature (GET /api/basket/cheapest + /api/basket/templates)
- [x] E — Telegram bot for daily price alerts (needs TELEGRAM_BOT_TOKEN env var on Render)
- [x] F — Replace mock climate metrics with real WeatherAPI data
- [x] G — Real DOE circulars (ERC blocked by Cloudflare; PPA stays mock)
- [x] H — Multi-year historical price archive (POST /api/integration/run-historical-backfill)
- [x] I — Crowdsourced pricing (POST /api/crowdsource/report, GET /api/crowdsource/summary)

## Environment Variables
```
# backend/.env
MONGO_URL=mongodb+srv://climateintel_admin:Sv5sVFw7gdHtydlq@climate-intel.q1jjn3g.mongodb.net/
DB_NAME=climate_intel
NEWSDATA_API_KEY=pub_5e23e133f8f142d6b24fc32045eeb421
WEATHERAPI_KEY=dc16d669a7514585854151245260203

# frontend/.env.production
REACT_APP_BACKEND_URL=https://climate-intel-api.onrender.com
```

## Dev Tooling (Local)
- `.vscode/settings.json` — `python.terminal.useEnvFile: true` auto-injects `backend/.env`
- `climate_intel.mongodb.js` — MongoDB playground at project root for querying Atlas directly

## MCP Server Config
Two separate config files depending on which agent/tool you're using:

**Claude Code CLI** (opencode / `claude` command) — reads `.mcp.json` in project root:
- File: `.mcp.json` (project root)
- Servers: `fetch` (mcp-fetch via npx), `playwright` (@playwright/mcp via npx), `mongodb` (@modelcontextprotocol/server-mongodb)
- MongoDB MCP connects directly to Atlas with full connection string

**VS Code Copilot Chat** — reads `.vscode/mcp.json`:
- File: `.vscode/mcp.json`
- Servers: `fetch` + `playwright` (same packages, no MongoDB since it's provided by VS Code extension)

Both files are committed to the repo. If MCP servers show as not configured in Claude Code, check that `.mcp.json` exists at project root and run `claude mcp list` to verify.

## Climate Intel Dev Agent (completed March 2026)
A local CLI assistant powered by the Claude Agent SDK with live access to MongoDB Atlas
and the production backend API.

```
agent/
  __init__.py          # Package stub
  __main__.py          # python -m agent entry point
  cli.py               # Single-query and --repl modes
  client.py            # ClaudeAgentOptions: all tools + system prompt + adaptive thinking
  config.py            # Loads backend/.env, exposes URLs and paths
  requirements.txt     # claude-agent-sdk, motor, aiohttp, python-dotenv, anyio
  prompts/
    system.py          # build_system_prompt(): preamble + technical-architect-engineer.md + CLAUDE.md
  tools/
    mongodb_tools.py   # 5 tools: query_collection, check_data_freshness, collection_stats,
                       #          verify_upsert, full_data_audit
    api_tools.py       # 4 tools: check_api_health, probe_endpoint,
                       #          trigger_integration, check_backend_status
```

**Usage** (run from a separate terminal — NOT inside Claude Code):
```bash
pip install -r agent/requirements.txt
python -m agent "Check data freshness across all collections"
python -m agent --repl
```

**Important**: The agent uses `ClaudeSDKClient` which launches a subprocess. It cannot run
nested inside an active `claude` CLI session (CLAUDECODE env var blocks it). Run from a
plain terminal tab.

Model: `claude-opus-4-6` with `thinking: {type: "adaptive"}`.

---

## QA Testing (added March 2026)

### Test Suite
```bash
# Local (start backend first: cd backend && uvicorn server:app --port 8000)
REACT_APP_BACKEND_URL=http://localhost:8000 pytest backend/tests/ -v

# Production (wakes Render automatically via retry)
REACT_APP_BACKEND_URL=https://climate-intel-api.onrender.com pytest backend/tests/ -v
```

### Test Files
| File | Tests | Covers |
|------|-------|--------|
| `test_energy_analytics.py` | 24 | Health, market analytics, energy analytics, news, PPA, DOE, grid, items, categories |
| `test_climate_metrics.py` | 8 | Climate metrics list, structure, known names, valid statuses, data source, by-ID |
| `test_integration_endpoints.py` | 9 | Health diagnostics, integration status, weather update, DOE update triggers |
| `test_market_items.py` | 10 | Item count, structure, search, limit, by-ID, price trends, correlations, opportunities, report, predict |
| **Total** | **51** | All 30 API endpoints covered |

### CI/CD
- `.github/workflows/test.yml` — runs `pytest` against production on push/PR to `backend/` files
- `.github/workflows/daily-refresh.yml` — data refresh (weekdays 8 AM Manila)

### Known Test Behaviors
- Grid MW values (`total_demand`, `total_supply`) are `None` locally (no Chromium) — tests accept `None`
- WeatherAPI update returns `success=False` when `WEATHERAPI_KEY` env var is missing
- `/api/climate-metrics/{id}` returns 500 for both valid and invalid IDs (endpoint bug — not blocking)
- `/api/market-items` defaults to `limit=100` — tests use `limit=300` to verify full count

---

## Render Deployment Notes
- Free tier: sleeps after 15 min inactivity, ~30-60s cold start
- Auto-deploys on push to main branch
- Region: Singapore
- Build: `pip install -r requirements.txt && python -m playwright install chromium --with-deps`
- Start: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- First NGCP scrape per cold start: ~15-20s (Chromium launch); cached 30 min after
