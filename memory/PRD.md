# Climate Smart Advisory & Intelligence Platform

## Original Problem Statement
Build an enhanced version of `anomura.today` - a Climate Smart Advisory & Intelligence Platform for the Philippines that:
1. Monitors 239+ commodities (vegetables, meats, fish, fuel, etc.) with real price trends
2. Displays real-time market prices sourced from official Philippine government data (DA Bantay Presyo, DOE)
3. Provides actionable analytics on price, supply/demand, and market trends
4. Includes Energy Intelligence with WESM prices, PPAs, DOE circulars, and real-time news

## Tech Stack
- **Frontend:** React, TailwindCSS, Shadcn UI
- **Backend:** FastAPI, Python
- **Database:** MongoDB
- **Data Sources:** DA Bantay Presyo PDFs, DOE Fuel Monitoring, NewsData.io API

## Core Features

### Implemented Features ✅

#### 1. Market Prices Page (Home)
- Real-time commodity prices from DA Bantay Presyo (155 items tracked)
- Category filtering (vegetables, meat, poultry, fish, rice, spices, fuel)
- Search functionality
- Sorting options (best deals, price low/high, name)
- Historical trend charts per item
- **NEW: Market Analytics Dashboard**
  - MURA/MAHAL item counts
  - Price Stability Index
  - Total Potential Savings
  - Supply & Demand insights by category
  - Category Trends with weekly changes
  - Price Alerts for significant movements
  - Top Movers (price increases/decreases)

#### 2. Energy Intelligence Page
- **Overview Tab:**
  - Grid Status (STABLE/WARNING/ALERT)
  - Total Demand/Supply/Reserves (MW)
  - PPA Summary (total capacity, operational, under construction)
  - Technology Mix breakdown (Solar, Wind, Geothermal)
  - Market Alerts
  
- **Prices Tab:**
  - WESM Luzon/Visayas/Mindanao prices (₱/MWh)
  - Price trend charts (6-week history)
  - Week-over-week change percentages
  - Market Outlook (short-term, supply adequacy, price forecast)
  - Key market drivers
  
- **PPAs & Contracts Tab:**
  - Power Purchase Agreements portfolio table
  - Project name, technology, capacity, status, off-taker, term
  
- **News & Circulars Tab:**
  - **REAL** energy news from NewsData.io API
  - DOE Circulars and Orders
  - External article links

#### 3. Climate Impact Page
- Climate metrics display
- Temperature, rainfall, UV index tracking
- Climate-to-price correlations

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/market-items` | All market commodities with filtering |
| `GET /api/analytics/market-analytics` | Price, supply/demand insights |
| `GET /api/energy/analytics` | PPA summary, price trends, outlook |
| `GET /api/energy/news` | Real news from NewsData.io |
| `GET /api/energy/ppa-status` | PPA portfolio |
| `GET /api/energy/doe-circulars` | DOE regulations |
| `GET /api/energy/grid-status` | Grid demand/supply |

## Data Sources Status

| Source | Status | Notes |
|--------|--------|-------|
| DA Bantay Presyo | ✅ LIVE | 155 commodities tracked via PDF parsing |
| DOE Fuel Prices | ✅ LIVE | Fuel prices integrated |
| NewsData.io | ✅ LIVE | API Key configured, real news |
| WESM Prices | 🔶 MOCKED | Sample trend data |
| PPA Portfolio | 🔶 MOCKED | Sample project data |
| Grid Status | 🔶 MOCKED | Pending NGCP integration |

## Pending Tasks (P0-P2)

### P0 - Critical
- None currently

### P1 - High Priority
- [ ] Expand commodity tracking from 155 to 239+ items
- [ ] Implement real WESM price scraping (pending API access)
- [ ] Enhance DOE document scraper with template-based extraction

### P2 - Medium Priority
- [ ] Implement OCR for scanned government documents
- [ ] Add real PPA data from ERC/DOE sources
- [ ] Integrate NGCP grid status API

### Future Enhancements
- [ ] Price prediction models
- [ ] Weather-price correlation alerts
- [ ] Push notifications for price alerts
- [ ] Historical data export

## Configuration

### Environment Variables
```
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
NEWSDATA_API_KEY=pub_5e23e133f8f142d6b24fc32045eeb421

# Frontend (.env)
REACT_APP_BACKEND_URL=https://smart-commodities-1.preview.emergentagent.com
```

## Last Updated
- **Date:** February 27, 2026
- **Session:** Energy Intelligence enhancement, Market Analytics implementation
- **Test Status:** 100% pass rate (24/24 backend tests, all frontend tabs working)
