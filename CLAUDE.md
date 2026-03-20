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
| Frontend | React 19, TailwindCSS, Shadcn UI (5 components), Recharts, React Router 7, Sonner |
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
    http_utils.py                    # Shared HTTP: fetch_with_retry (exponential backoff, circuit breaker)
    daily_price_parser.py            # DA Bantay Presyo daily PDF downloader/parser (uses http_utils)
    real_data_integration.py         # /run-da-bantay-presyo endpoint service (uses http_utils)
    comprehensive_real_data.py       # 7-day history builder + climate impact computation
    weather_integration.py           # WeatherAPI.com -> climate_metrics MongoDB (canonical schema)
    newsdata_integration.py          # Real energy news via NewsData.io API (WORKING)
    energy_grid_scraper.py           # IEMOP WESM price scraper (REAL, 1-hr cache)
    ngcp_scraper.py                  # NGCP grid MW Playwright scraper (returns Optional[Dict], 30-min cache)
    doe_integration.py               # Real DOE issuances via SSR scrape -> MongoDB
    doe_document_scraper.py          # Legacy mock PPA data (ERC blocked by Cloudflare)
    doe_fuel_integration.py          # DOE fuel price scraper
    telegram_bot.py                  # Telegram Bot API broadcaster (send_message, broadcast, build_daily_alert)
    historical_backfill.py           # DA PDF backfill over arbitrary date range → price_history collection
    web_crawler.py                   # Generic async scraper (BeautifulSoup)
    ocr_service.py                   # PyPDF2 + PyTesseract

frontend/src/
  pages/Home.jsx                     # Main dashboard: market analytics + climate events + grid
  pages/EnergyIntelligence.jsx       # Energy grid/WESM/PPAs/news page
  pages/ClimateImpact.jsx            # Climate metrics page (real WeatherAPI data now)
  pages/GroceryBasket.jsx            # Cheapest basket builder + preset templates
  pages/NotFound.jsx                 # 404 catch-all route
  components/Navbar.jsx              # Top nav with mobile hamburger menu
  components/ErrorBoundary.jsx       # Top-level error boundary wrapping App
  components/MarketCard.jsx          # Commodity price card with sparkline + dialog
  components/ClimateCard.jsx         # Climate metric card with sparkline + dialog
  components/BestDeals.jsx           # Horizontal scroll carousel of best deals
  components/ui/                     # Shadcn UI — trimmed to 5: button, card, dialog, input, sonner
  api/index.js                       # All Axios API calls (marketAPI, analyticsAPI, energyAPI, climateAPI, basketAPI)
  # NOTE: Commodities, Analytics, Forecasts, Watchlist pages do NOT exist yet

frontend/public/
  index.html                         # OG/Twitter meta tags, dark theme-color, no Inter font
  favicon.svg                        # SVG favicon (emerald triangle on slate bg)
  robots.txt                         # Allow all crawlers

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
5. `comprehensive_real_data.py` — `fetch_climate_metrics()` queried non-existent fields
   (`metric_name`, `value`) instead of canonical (`name`, `currentValue`). All market items
   showed "Climate data unavailable". Fixed by standardizing all consumers on canonical schema.
6. `ngcp_scraper.py` — `scrape()` returned `{}` on failure (falsy in Python), causing
   `server.py` to skip MongoDB cache persistence. Fixed: returns `None` on failure.
7. `daily_price_parser.py` + `real_data_integration.py` — bare `timeout=30` int (deprecated
   in aiohttp), no retry logic, new session per URL. Fixed: shared `http_utils.fetch_with_retry`
   with exponential backoff, circuit breaker, shared sessions.

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

None — all endpoints now return real fetched data or honest unavailable states.

**Previously mock, now real or removed (March 2026):**
- PPA status → real DOE awarded RE contracts (1,254 projects from DOE Legacy Site)
- Climate impact on market items → computed from live WeatherAPI metrics per category
- ClimateImpact page insights → computed from API data in `ClimateImpact.jsx`
- Energy market outlook key drivers → now derived from actual WESM prices (was hardcoded generic strings)
- WESM price fallback → returns `source: "unavailable"` with null values (was fabricated numbers)
- `simple_real_data.py` → deleted (was legacy hardcoded prices with `random.uniform()`)
- `doe_document_scraper.scrape_doe_circulars()` → returns `[]` (was mock data; real scraping via `doe_integration.py`)

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
- **Canonical schema** (all consumers read these fields directly):
  ```
  {name, category, currentValue, averageValue, unit, icon, status,
   trend: [7 values], recommendation, impact, lastUpdated, updatedAt,
   data_source, location}
  ```
- `averageValue` = mean of the 7-point trend array
- Consumers: `comprehensive_real_data.py` (climate impact), `analytics_engine.py` (correlations), `ClimateImpact.jsx` (frontend)
- **Do not** invent alternate field names (`metric_name`, `value`, etc.) — use `name` and `currentValue`

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

## Frontend Code Audit (completed March 2026)

Two-round comprehensive audit of the entire React frontend. Build: **137.13 kB JS gzip, 6.55 kB CSS gzip** — zero warnings.

### Round 1 — Cleanup & Infrastructure (15 items)
1. Added null guards for analytics data in Home.jsx
2. Removed non-functional timePeriod filter buttons from Home.jsx and ClimateImpact.jsx
3. Added mobile hamburger menu to Navbar.jsx
4. Centralized GroceryBasket API calls into `api/index.js` (`basketAPI`)
5. Deleted dead `mockData.js`
6. Added 404 catch-all route (`NotFound.jsx`)
7. Added top-level `ErrorBoundary.jsx` wrapping entire App
8. Removed fake notification badge and non-functional Settings button
9. Fixed inconsistent branding ("ClimateWatch" -> "Climate Intel")
10. Fixed exposed API endpoint text in EnergyIntelligence empty state
11. Fixed `use-toast.js` stale listener bug (`[state]` -> `[]` dependency)
12. Fixed dead `href="#"` link in Home.jsx footer
13. Persisted favorites to `localStorage` in Home.jsx and ClimateImpact.jsx
14. Deleted 41 unused Shadcn UI component files (kept 5: button, card, dialog, input, sonner)
15. Removed 35 unused npm dependencies from `package.json` (107 packages pruned)

### Round 2 — Deep Fixes (22 items, 21 done, 1 cancelled)
1. **CRITICAL:** Hardcoded `theme="dark"` in sonner.jsx, removed `next-themes` dependency
2. **CRITICAL:** Null-guarded `.toUpperCase()` on `supply_status` and `alert.type`
3. **HIGH:** Added full-page error state to EnergyIntelligence (all 5 endpoints fail)
4. **HIGH:** Added empty states for News and Circulars tabs
5. **HIGH:** Added `<main>` landmark to all 5 pages
6. **HIGH:** Added `aria-label` to all icon-only buttons (scroll, favorite, info, close)
7. **HIGH:** Fixed duplicate SVG gradient IDs — unique per card/dialog instance
8. **MEDIUM:** Removed dead `isBetter` variable from ClimateCard.jsx
9. **MEDIUM:** Removed 8 dead API functions + entire `integrationAPI` export
10. **MEDIUM:** Replaced `filteredMetrics` useState+useEffect with `useMemo` in ClimateImpact
11. **MEDIUM:** Fixed O(n^2) min/max inside `.map()` in EnergyIntelligence
12. **MEDIUM:** Improved NotFound h1 from "404" to "404 — Page Not Found" for SEO
13. **MEDIUM:** Created `favicon.svg` and `robots.txt` in public/
14. **MEDIUM:** Added Open Graph + Twitter Card meta tags to index.html
15. **LOW:** Cleaned stale CRA template comments in index.html
16. **LOW:** Gated all `console.error` behind `NODE_ENV !== 'production'` check
17. **LOW:** Resolved dual toast system — switched all pages from `use-toast.js` to Sonner, deleted `use-toast.js` and empty `hooks/` directory
18. **LOW:** Added `type="button"` to all non-submit buttons (prevents form submission bugs)
19. **LOW:** Moved `BasketCard` component from inside GroceryBasket function body to module scope
20. **LOW:** Cancelled — Navbar architecture (structural, low impact)
21. **LOW:** Removed unused Inter font link (2 preconnects + 1 stylesheet) from index.html
22. **LOW:** Fixed DOE circular link — conditionally wraps in `<a>` only when `circular.url` exists

### Files deleted during audit
- `frontend/src/mockData.js`
- `frontend/src/hooks/use-toast.js` (and `hooks/` directory)
- 41 files in `frontend/src/components/ui/` (accordion, alert-dialog, alert, aspect-ratio, avatar, badge, breadcrumb, calendar, carousel, checkbox, collapsible, command, context-menu, drawer, dropdown-menu, form, hover-card, input-otp, label, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, skeleton, slider, switch, table, tabs, textarea, toast, toaster, toggle-group, toggle, tooltip)

### npm dependencies removed
35 packages removed from `package.json`, including: `@radix-ui/react-accordion`, `@radix-ui/react-alert-dialog`, `@radix-ui/react-avatar`, `@radix-ui/react-checkbox`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-label`, `@radix-ui/react-menubar`, `@radix-ui/react-navigation-menu`, `@radix-ui/react-popover`, `@radix-ui/react-progress`, `@radix-ui/react-radio-group`, `@radix-ui/react-scroll-area`, `@radix-ui/react-select`, `@radix-ui/react-separator`, `@radix-ui/react-slider`, `@radix-ui/react-switch`, `@radix-ui/react-tabs`, `@radix-ui/react-toggle`, `@radix-ui/react-toggle-group`, `@radix-ui/react-tooltip`, `cmdk`, `date-fns`, `embla-carousel-react`, `input-otp`, `next-themes`, `react-day-picker`, `react-resizable-panels`, `vaul`, etc.

Only 2 Radix packages retained: `@radix-ui/react-dialog`, `@radix-ui/react-slot`.

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
- [x] J — Frontend code audit: cleanup, accessibility, performance, SEO (2 rounds, 36 fixes)

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

## HTTP Reliability (`backend/services/http_utils.py`)
All external HTTP fetches (DA PDFs, DOE, etc.) should use the shared `fetch_with_retry`:
```python
from services.http_utils import fetch_with_retry, DEFAULT_TIMEOUT
async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
    response = await fetch_with_retry(session, url, max_retries=3, headers=headers)
```
- **Retry policy**: 3 attempts, exponential backoff (2s, 4s, 8s)
- **Retries on**: HTTP 5xx, `aiohttp.ClientError`, `asyncio.TimeoutError`
- **No retry on**: HTTP 404 (resource doesn't exist), other 4xx
- **Default timeout**: 45s per request
- **Circuit breaker** in `daily_price_parser.download_multiple_days()`: stops after 3 consecutive days with no PDF
- **Shared session**: one `aiohttp.ClientSession` per download batch, not per URL
- **Rate limiting**: 1s delay between DA.gov.ph requests (government site)

### NGCP Scraper Contract
`ngcp_scraper.scrape()` returns `Optional[Dict]`:
- Success: `{total_supply, total_demand, reserves, grids[], data_as_of, source}`
- Failure: `None` (not `{}` — empty dicts are falsy in Python and cause subtle bugs)
- `server.py` checks `if ngcp_data is not None:` before caching to MongoDB

---

## Render Deployment Notes
- Free tier: sleeps after 15 min inactivity, ~30-60s cold start
- Auto-deploys on push to main branch
- Region: Singapore
- Build: `pip install -r requirements.txt && python -m playwright install chromium --with-deps`
- Start: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- First NGCP scrape per cold start: ~15-20s (Chromium launch); cached 30 min after
