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
| Scheduler | GitHub Actions cron (NOT scheduler.py — see below) |

## URLs
- Frontend (prod): https://frontend-qxb1lmjh3-martin-banarias-projects.vercel.app
- Backend (prod): https://climate-intel-api.onrender.com
- GitHub: https://github.com/martinbanaria/climate-intel-platform
- MongoDB: mongodb+srv://climateintel_admin@climate-intel.q1jjn3g.mongodb.net/

## Key Files
```
backend/
  server.py                          # All API endpoints
  scheduler.py                       # DO NOT RELY ON — Render free tier sleeps, kills it
  services/
    daily_price_parser.py            # DA Bantay Presyo daily PDF downloader/parser (WORKING)
    real_data_integration.py         # /run-da-bantay-presyo endpoint service (FIXED)
    comprehensive_real_data.py       # 7-day history builder using daily_price_parser (WORKING)
    newsdata_integration.py          # Real energy news via NewsData.io API (WORKING)
    energy_grid_scraper.py           # IEMOP WESM price scraper (REAL, 1-hr cache)
    ngcp_scraper.py                  # NGCP grid MW Playwright scraper (REAL, 30-min cache)
    doe_document_scraper.py          # DOE circulars + PPA — STILL HARDCODED MOCK DATA
    doe_fuel_integration.py          # DOE fuel price scraper
    web_crawler.py                   # Generic async scraper (BeautifulSoup)
    ocr_service.py                   # PyPDF2 + PyTesseract

frontend/src/
  pages/Dashboard.jsx                # Overview: market analytics + climate events + grid
  pages/EnergyIntelligence.jsx       # Energy grid/WESM/PPAs/news page
  pages/ClimateImpact.jsx            # Climate metrics page (mostly mock data)
  pages/Commodities.jsx              # Commodity price table
  pages/Analytics.jsx                # Market analytics dashboard
  pages/Forecasts.jsx                # Price forecasts (uses real market + mock climate)
  pages/Watchlist.jsx                # User watchlist (real market data)
  api/index.js                       # All Axios API calls

.github/workflows/daily-refresh.yml  # Automated daily data refresh (ACTIVE)
```

## Auto-Update Architecture (as of March 2026)
`scheduler.py` is NOT used in production — Render free tier sleeps after 15 min.

**GitHub Actions** runs `.github/workflows/daily-refresh.yml` every weekday at 8 AM Manila time (00:00 UTC):
1. Wakes Render backend (6 retries × 60s)
2. POSTs `/api/integration/run-da-bantay-presyo` — downloads today's DA PDF → updates prices
3. POSTs `/api/integration/run-comprehensive-real-data?days=7` — rebuilds 7-day trend history
4. GETs `/api/integration/status` — verifies freshness

## DA Bantay Presyo PDF URLs
Two patterns tried (both in `daily_price_parser.py` and `real_data_integration.py`):
```
https://www.da.gov.ph/wp-content/uploads/{year}/{month:02d}/Daily-Price-Index-{Month}-{day}-{year}.pdf
https://www.da.gov.ph/wp-content/uploads/{year}/{month:02d}/{Month}-{day}-{year}-DPI-AFC.pdf
```
DA only publishes on weekdays. Skip weekends in all downloaders.

## Key Bugs Fixed (March 2026)
1. **real_data_integration.py** — was trying weekly average PDF URLs (never available). Fixed to daily PDFs.
2. **real_data_integration.py** — `'\\n'` (literal backslash-n) used instead of `'\n'`. Fixed.
3. **real_data_integration.py** — regex raw strings had `\\s`, `\\d` (literal) instead of `\s`, `\d`. Fixed.
4. **GitHub Actions cold-start** — curl timed out on 30s. Fixed to 60s max-time with 6 retries.

---

## Real vs Mock Data Audit (March 2026)

### ✅ REAL DATA (live scraped / API-fetched)

| What | Source | Endpoint | Notes |
|------|--------|----------|-------|
| 215+ commodity prices | DA Bantay Presyo PDFs | `GET /api/market-items` | Updated daily via GitHub Actions |
| Commodity 7-day price trends | DA Bantay Presyo PDFs | `GET /api/analytics/price-trends` | Built by `comprehensive_real_data.py` |
| MURA/MAHAL/STABLE labels | Computed from real prices | `GET /api/analytics/market-analytics` | `analytics_engine.py` runs on real MongoDB |
| Market price alerts | Computed from real trends | included in market-analytics | Real % change vs previous day |
| WESM electricity prices (₱/MWh) | IEMOP `MP_YYYYMMDD.csv` | `GET /api/energy/analytics` → `price_trends` | Luzon/Visayas/Mindanao; 1-hr cache; 7-day trend |
| Grid overall status (STABLE/ELEVATED/TIGHT) | Derived from Luzon WESM price | `GET /api/energy/grid-status` → `status` | >₱8k=TIGHT, >₱6k=ELEVATED |
| Grid MW (demand, supply, margin) | NGCP homepage Playwright scrape | `GET /api/energy/grid-status` | `ngcp_scraper.py`; 30-min cache; Playwright+stealth |
| Per-region grid MW (Luzon/Visayas/Mindanao) | NGCP Power Situation Outlook table | inside grid-status response | Available Generating Capacity + System Peak Demand + Operating Margin |
| Energy news articles | NewsData.io API | `GET /api/energy/news` | Free tier: 200 calls/day |
| Watchlist items | Real market data from MongoDB | frontend state only | No backend changes needed |

### ❌ MOCK / HARDCODED DATA

| What | Where | Endpoint | Notes |
|------|-------|----------|-------|
| Climate metrics (temperature, rainfall, humidity, etc.) | MongoDB `climate_metrics` collection seeded with fake values | `GET /api/climate-metrics` | No real weather scraper exists. PAGASA scraper placeholder in `web_crawler.py` does not actually parse. |
| "Key Market Impact Insights" text | Hardcoded in `ClimateImpact.jsx` (~lines 144–148) | ClimateImpact page | Static JSX, never changes regardless of actual weather |
| DOE Circulars | 2 fake entries hardcoded in `doe_document_scraper.scrape_doe_circulars()` | `GET /api/energy/doe-circulars` | Returns fake DC2026-02-001, DO2026-01 |
| PPA (Power Purchase Agreements) | 3 fake PPAs hardcoded in `doe_document_scraper.scrape_ppa_statuses()` | `GET /api/energy/ppa-status` | Fake Solar PH Nueva Ecija, Luzon Wind Farm, Mindanao Geothermal |
| PPA analytics summary | Derived from 3 fake PPAs | `GET /api/energy/analytics` → `ppa_summary` + `technology_breakdown` | Counts/capacities are meaningless |
| Energy market outlook | Hardcoded static strings in `server.py` | `GET /api/energy/analytics` → `market_outlook` | `short_term`, `supply_adequacy`, `price_forecast`, `key_drivers` — never change |

### ⚠️ SEMI-REAL (algorithm is real, but some inputs are mock)

| What | Real part | Mock input | Impact |
|------|-----------|------------|--------|
| Climate correlations | Correlation algorithm in `analytics_engine.py` | `climate_metrics` from MongoDB (mock) | Correlation output is meaningless |
| Price predictions | Heuristic engine in `analytics_engine.py` | Uses real price trends | Reasonably useful but not ML-based |
| Dashboard critical events | Builds events from all data | Climate warnings come from mock data | Market price events are real; climate events are fake |
| Forecasts page | Renders market analytics (real) + energy analytics (real WESM) | Climate input from mock collection | Price forecasts partially meaningful |

---

## API Endpoints Reference
```
GET  /api/market-items               # ✅ REAL — 215+ commodities from DA PDFs
GET  /api/best-deals                 # ✅ REAL — Top MURA items by savings
GET  /api/analytics/market-analytics # ✅ REAL — Computed from live MongoDB data
GET  /api/analytics/price-trends     # ✅ REAL — 7-day history from DA PDFs
GET  /api/analytics/climate-correlations  # ⚠️ algorithm real, climate data mock
GET  /api/analytics/buying-opportunities  # ✅ REAL — computed from real prices
GET  /api/analytics/predict/{item_id}     # ⚠️ heuristic, not ML model
POST /api/integration/run-da-bantay-presyo          # Trigger today's PDF refresh
POST /api/integration/run-comprehensive-real-data   # Rebuild 7-day history
GET  /api/integration/status         # Last update timestamp + item count
GET  /api/energy/grid-status         # ✅ REAL — NGCP Playwright scraper (30-min cache)
GET  /api/energy/analytics           # ✅ REAL prices — ❌ PPA data still mock
GET  /api/energy/news                # ✅ REAL — NewsData.io
GET  /api/energy/doe-circulars       # ❌ MOCK — 2 hardcoded fake circulars
GET  /api/energy/ppa-status          # ❌ MOCK — 3 hardcoded fake PPAs
GET  /api/climate-metrics            # ❌ MOCK — seeded MongoDB, no weather scraper
```

## What's Still Mocked (Next To Fix)
Priority order for remaining mock data:

1. **Climate Metrics** — biggest gap; ClimateImpact page is entirely fake
   - Need: PAGASA weather scraper (pagasa.dost.gov.ph) — HTML scraping or OpenMeteo API
   - OpenMeteo (open-meteo.com) is free, no auth needed, JSON API for PH coordinates
   - Would replace `climate_metrics` MongoDB collection with live data

2. **DOE Circulars** — need real scraping of doe.gov.ph
   - Structure exists in `doe_document_scraper.py`; just needs real HTTP scraping

3. **PPA Status** — need real data from DOE or ERC
   - DOE has PPA registry on website; needs scraping

4. **Energy Market Outlook** — can be derived from real WESM data
   - Currently `short_term`, `supply_adequacy`, `price_forecast` are hardcoded strings in server.py

## Roadmap (In Priority Order)
- [x] A — GitHub Actions daily auto-refresh
- [x] B — Fix DA Bantay Presyo integration (3 bugs)
- [x] C — Replace mocked grid status + WESM prices with real scraped data
- [ ] D — "Cheapest Grocery Basket" feature (most unique/viral)
- [ ] E — Telegram/Viber bot for daily price alerts
- [ ] F — Replace mock climate metrics with real weather data (OpenMeteo or PAGASA)
- [ ] G — Real DOE circulars and PPA data scraping
- [ ] H — Multi-year historical price archive from DA archives
- [ ] I — Crowdsourced "actual vs official" price reporting

## Environment Variables
```
# backend/.env
MONGO_URL=mongodb+srv://climateintel_admin:***@climate-intel.q1jjn3g.mongodb.net/
DB_NAME=climate_intel
NEWSDATA_API_KEY=pub_5e23e133f8f142d6b24fc32045eeb421

# frontend/.env.production
REACT_APP_BACKEND_URL=https://climate-intel-api.onrender.com
```

## Render Deployment Notes
- Free tier: sleeps after 15 min inactivity, ~30-60s cold start
- Auto-deploys on push to main branch
- Region: Singapore (closest to Philippines)
- Build: `pip install -r requirements.txt && python -m playwright install chromium --with-deps`
- Start: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- Chromium (for NGCP scraper) installed at build time via playwright
- First NGCP scrape per cold start: ~15-20s (Chromium launch); cached for 30 min after
