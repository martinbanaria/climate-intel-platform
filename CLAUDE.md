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
    doe_document_scraper.py          # DOE circulars + PPA scraper (WORKING)
    doe_fuel_integration.py          # DOE fuel price scraper
    web_crawler.py                   # Generic async scraper (BeautifulSoup)
    ocr_service.py                   # PyPDF2 + PyTesseract

frontend/src/
  pages/Home.jsx                     # Market prices page
  pages/EnergyIntelligence.jsx       # Energy grid/WESM/PPAs/news page
  pages/ClimateImpact.jsx            # Climate metrics page
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

## API Endpoints Reference
```
GET  /api/market-items               # 215+ commodities (filter: category, search, sort)
GET  /api/best-deals                 # Top MURA items by savings
GET  /api/analytics/market-analytics # MURA/MAHAL counts, stability index
GET  /api/analytics/price-trends     # 7-day trends
POST /api/integration/run-da-bantay-presyo          # Trigger today's PDF refresh
POST /api/integration/run-comprehensive-real-data   # Rebuild 7-day history
GET  /api/integration/status         # Last update timestamp + item count
GET  /api/energy/grid-status         # ⚠️ STILL MOCKED — hardcoded 15,234 MW
GET  /api/energy/analytics           # ⚠️ WESM prices STILL MOCKED
GET  /api/energy/news                # Real news via NewsData.io
GET  /api/energy/doe-circulars       # Real DOE circulars (scraped)
GET  /api/energy/ppa-status          # Real PPA data (scraped)
```

## What's Still Mocked (Next To Fix)
- `/api/energy/grid-status` — hardcoded Luzon/Visayas/Mindanao MW values
- `/api/energy/analytics` price_trends — hardcoded WESM ₱/MWh values
- Real sources investigated: NGCP (ngcp.ph/operations), IEMOP (iemop.ph), PEMC (wesm.ph)
- NGCP returns 403. IEMOP/PEMC pages need JS rendering or HTML scraping.

## Roadmap (In Priority Order)
- [x] A — GitHub Actions daily auto-refresh
- [x] B — Fix DA Bantay Presyo integration (3 bugs)
- [ ] C — Replace mocked grid status + WESM prices with real scraped data
- [ ] D — "Cheapest Grocery Basket" feature (most unique/viral)
- [ ] E — Telegram/Viber bot for daily price alerts
- [ ] F — Multi-year historical price archive from DA archives
- [ ] G — Crowdsourced "actual vs official" price reporting

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
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
