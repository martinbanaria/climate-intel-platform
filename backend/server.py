from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import ssl
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import json
import certifi

# Import services
from services.web_crawler import crawler
from services.ocr_service import ocr_service
from services.analytics_engine import analytics_engine
from services.real_data_integration import DABantayPresyoIntegration
from services.simple_real_data import integrate_simple_real_data
from services.comprehensive_real_data import integrate_comprehensive_real_data
from services.newsdata_integration import news_integration
from services.doe_document_scraper import doe_scraper
from services.energy_grid_scraper import wesm_scraper
from services.ngcp_scraper import ngcp_scraper
from services.weather_integration import run_weather_update
from services.doe_integration import run_doe_update
from services.doe_fuel_integration import integrate_doe_fuel_prices
from services.ppa_contract_scraper import scrape_all_contracts
from models import MarketItem, ClimateMetric, ScrapedDocument, AnalyticsInsight

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection with SSL fix for Render's Python/OpenSSL
mongo_url = os.environ["MONGO_URL"]
# On Render, the default OpenSSL config can cause TLSV1_ALERT_INTERNAL_ERROR with
# MongoDB Atlas. Fix: create a custom SSL context that uses TLSv1.2+ with certifi certs
_ssl_context = ssl.create_default_context(cafile=certifi.where())
_ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
client = AsyncIOMotorClient(
    mongo_url,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
)
db = client[os.environ["DB_NAME"]]

# Create the main app without a prefix
app = FastAPI(title="Climate-Smart Market Intelligence API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ========== HEALTH/DIAGNOSTIC ENDPOINTS ==========


@api_router.get("/health")
async def health_check():
    """Health check endpoint with MongoDB connection diagnostic"""
    result = {
        "status": "ok",
        "python_version": os.popen("python3 --version").read().strip(),
        "openssl_version": ssl.OPENSSL_VERSION,
        "mongo_url_prefix": mongo_url[:30] + "...",
        "certifi_ca": certifi.where(),
        "weatherapi_key_set": bool(os.environ.get("WEATHERAPI_KEY")),
        "newsdata_key_set": bool(os.environ.get("NEWSDATA_API_KEY")),
    }
    try:
        # Test MongoDB connection
        server_info = await client.server_info()
        result["mongodb"] = "connected"
        result["mongodb_version"] = server_info.get("version", "unknown")
    except Exception as e:
        result["mongodb"] = f"error: {str(e)[:200]}"
    return result


# ========== MARKET ITEMS ENDPOINTS ==========


@api_router.get("/market-items")
async def get_market_items(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "best",
    limit: int = 100,
):
    """Get all market items with filtering and sorting"""
    try:
        query = {}

        # Filter by category
        if category and category != "all":
            query["category"] = category

        # Search by name
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        # Get items from database
        cursor = db.market_items.find(query).sort("lastUpdated", -1).limit(limit)
        items = await cursor.to_list(length=limit)

        # Convert ObjectId and datetime to string
        for item in items:
            item["id"] = str(item.pop("_id"))
            if "lastUpdated" in item:
                item["lastUpdated"] = item["lastUpdated"].isoformat()
            if "createdAt" in item:
                item["createdAt"] = item["createdAt"].isoformat()
            if "updatedAt" in item:
                item["updatedAt"] = item["updatedAt"].isoformat()

        # Sort items
        if sort == "best":
            items.sort(
                key=lambda x: (
                    0
                    if x.get("status") == "MURA"
                    else 1
                    if x.get("status") == "STABLE"
                    else 2,
                    -x.get("savings", 0),
                )
            )
        elif sort == "price-low":
            items.sort(key=lambda x: x.get("currentPrice", 0))
        elif sort == "price-high":
            items.sort(key=lambda x: x.get("currentPrice", 0), reverse=True)
        elif sort == "name":
            items.sort(key=lambda x: x.get("name", ""))

        return JSONResponse({"success": True, "count": len(items), "data": items})
    except Exception as e:
        logger.error(f"Error fetching market items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/market-items/{item_id}")
async def get_market_item(item_id: str):
    """Get single market item by ID"""
    try:
        from bson import ObjectId

        item = await db.market_items.find_one({"_id": ObjectId(item_id)})

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        item["id"] = str(item.pop("_id"))
        if "lastUpdated" in item:
            item["lastUpdated"] = item["lastUpdated"].isoformat()
        if "createdAt" in item:
            item["createdAt"] = item["createdAt"].isoformat()
        if "updatedAt" in item:
            item["updatedAt"] = item["updatedAt"].isoformat()
        return JSONResponse({"success": True, "data": item})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/best-deals")
async def get_best_deals(limit: int = 8):
    """Get top deals — items with biggest savings (price below average)"""
    try:
        # Get all items where current price is below average (savings > 0)
        cursor = db.market_items.find({"savings": {"$gt": 0}})
        items = await cursor.to_list(length=200)

        # Convert ObjectId and datetime
        for item in items:
            item["id"] = str(item.pop("_id"))
            if "lastUpdated" in item:
                item["lastUpdated"] = item["lastUpdated"].isoformat()
            if "createdAt" in item:
                item["createdAt"] = item["createdAt"].isoformat()
            if "updatedAt" in item:
                item["updatedAt"] = item["updatedAt"].isoformat()

        # Sort by savings descending (biggest deals first)
        items.sort(key=lambda x: x.get("savings", 0), reverse=True)

        return JSONResponse(
            {"success": True, "count": len(items[:limit]), "data": items[:limit]}
        )
    except Exception as e:
        logger.error(f"Error fetching best deals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== CLIMATE METRICS ENDPOINTS ==========


@api_router.get("/climate-metrics")
async def get_climate_metrics():
    """Get all climate metrics"""
    try:
        cursor = db.climate_metrics.find({})
        metrics = await cursor.to_list(length=100)

        for metric in metrics:
            metric["id"] = str(metric.pop("_id"))
            if "lastUpdated" in metric:
                metric["lastUpdated"] = metric["lastUpdated"].isoformat()
            if "createdAt" in metric:
                metric["createdAt"] = metric["createdAt"].isoformat()
            if "updatedAt" in metric:
                metric["updatedAt"] = metric["updatedAt"].isoformat()

        return JSONResponse({"success": True, "count": len(metrics), "data": metrics})
    except Exception as e:
        logger.error(f"Error fetching climate metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/climate-metrics/{metric_id}")
async def get_climate_metric(metric_id: str):
    """Get single climate metric by ID"""
    try:
        from bson import ObjectId

        metric = await db.climate_metrics.find_one({"_id": ObjectId(metric_id)})

        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")

        metric["id"] = str(metric.pop("_id"))
        if "lastUpdated" in metric:
            metric["lastUpdated"] = metric["lastUpdated"].isoformat()
        if "createdAt" in metric:
            metric["createdAt"] = metric["createdAt"].isoformat()
        if "updatedAt" in metric:
            metric["updatedAt"] = metric["updatedAt"].isoformat()
        return JSONResponse({"success": True, "data": metric})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching climate metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== WEB SCRAPING ENDPOINTS ==========


@api_router.post("/scrape/url")
async def scrape_url(url: str, source_type: str = "da_bantay_presyo"):
    """Scrape data from a given URL"""
    try:
        # Scrape the URL
        html = await crawler.scrape_url(url)
        if not html:
            raise HTTPException(status_code=400, detail="Failed to scrape URL")

        # Extract market data
        market_data = await crawler.extract_market_data(html, source_type)

        # Save to database
        document = {
            "source_url": url,
            "source_type": "web",
            "raw_text": html[:1000],  # Store first 1000 chars
            "extracted_data": market_data,
            "processed": True,
            "createdAt": datetime.utcnow(),
        }
        result = await db.scraped_documents.insert_one(document)

        return JSONResponse(
            {
                "success": True,
                "document_id": str(result.inserted_id),
                "items_found": len(market_data),
                "data": market_data,
            }
        )
    except Exception as e:
        logger.error(f"Error scraping URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/scrape/pagasa")
async def scrape_pagasa_climate():
    """Scrape climate data from PAGASA website"""
    try:
        climate_data = await crawler.scrape_pagasa_climate_data()

        # Save to database
        document = {
            "source_url": "https://www.pagasa.dost.gov.ph/",
            "source_type": "web",
            "extracted_data": climate_data,
            "processed": True,
            "createdAt": datetime.utcnow(),
        }
        await db.scraped_documents.insert_one(document)

        return JSONResponse({"success": True, "data": climate_data})
    except Exception as e:
        logger.error(f"Error scraping PAGASA data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== OCR ENDPOINTS ==========


@api_router.post("/ocr/process-image")
async def process_image(file: UploadFile = File(...)):
    """Process image document with OCR"""
    try:
        # Read file content
        content = await file.read()

        # Extract text using OCR
        result = await ocr_service.process_market_report(content, doc_type="image")

        if not result["success"]:
            raise HTTPException(
                status_code=400, detail=result.get("error", "OCR failed")
            )

        # Save to database
        document = {
            "source_url": file.filename,
            "source_type": "image",
            "raw_text": result["raw_text"],
            "extracted_data": result["extracted_data"],
            "processed": True,
            "createdAt": datetime.utcnow(),
        }
        doc_result = await db.scraped_documents.insert_one(document)

        return JSONResponse(
            {
                "success": True,
                "document_id": str(doc_result.inserted_id),
                "raw_text": result["raw_text"][:500],
                "extracted_data": result["extracted_data"],
            }
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/ocr/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    """Process PDF document with OCR"""
    try:
        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text
        text = await ocr_service.extract_text_from_pdf(temp_path)

        # Clean up
        os.remove(temp_path)

        if not text:
            raise HTTPException(status_code=400, detail="No text extracted from PDF")

        # Save to database
        document = {
            "source_url": file.filename,
            "source_type": "pdf",
            "raw_text": text,
            "processed": True,
            "createdAt": datetime.utcnow(),
        }
        result = await db.scraped_documents.insert_one(document)

        return JSONResponse(
            {
                "success": True,
                "document_id": str(result.inserted_id),
                "text_length": len(text),
                "preview": text[:500],
            }
        )
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ANALYTICS ENDPOINTS ==========


@api_router.get("/analytics/market-analytics")
async def get_market_analytics():
    """Get comprehensive market analytics including price, supply/demand insights"""
    try:
        # Fetch all market items
        cursor = db.market_items.find({})
        items = await cursor.to_list(length=1000)

        # Generate comprehensive analytics
        analytics = analytics_engine.generate_market_analytics(items)

        return JSONResponse(
            {
                "success": True,
                "generated_at": datetime.utcnow().isoformat(),
                "data": analytics,
            }
        )
    except Exception as e:
        logger.error(f"Error generating market analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/price-trends")
async def get_price_trends():
    """Get price trend analysis by category"""
    try:
        # Fetch all market items
        cursor = db.market_items.find({})
        items = await cursor.to_list(length=1000)

        # Calculate trends
        trends = analytics_engine.calculate_price_trends(items)

        return JSONResponse({"success": True, "data": trends})
    except Exception as e:
        logger.error(f"Error calculating price trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/climate-correlations")
async def get_climate_correlations():
    """Get correlations between climate and prices"""
    try:
        # Fetch market items and climate metrics
        market_cursor = db.market_items.find({})
        market_items = await market_cursor.to_list(length=1000)

        climate_cursor = db.climate_metrics.find({})
        climate_metrics = await climate_cursor.to_list(length=100)

        # Calculate correlations
        correlations = analytics_engine.correlate_climate_to_prices(
            market_items, climate_metrics
        )

        return JSONResponse(
            {"success": True, "count": len(correlations), "data": correlations}
        )
    except Exception as e:
        logger.error(f"Error calculating correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/buying-opportunities")
async def get_buying_opportunities():
    """Get best buying opportunities based on trends and climate"""
    try:
        # Fetch all market items
        cursor = db.market_items.find({})
        items = await cursor.to_list(length=1000)

        # Identify opportunities
        opportunities = analytics_engine.identify_best_buying_opportunities(items)

        return JSONResponse(
            {"success": True, "count": len(opportunities), "data": opportunities}
        )
    except Exception as e:
        logger.error(f"Error identifying opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/weekly-report")
async def get_weekly_report():
    """Generate comprehensive weekly analytics report"""
    try:
        # Fetch data
        market_cursor = db.market_items.find({})
        market_items = await market_cursor.to_list(length=1000)

        climate_cursor = db.climate_metrics.find({})
        climate_metrics = await climate_cursor.to_list(length=100)

        # Generate report
        report = analytics_engine.generate_weekly_report(market_items, climate_metrics)

        return JSONResponse({"success": True, "data": report})
    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analytics/predict/{item_id}")
async def predict_price(item_id: str):
    """Predict future price for a specific item"""
    try:
        from bson import ObjectId

        item = await db.market_items.find_one({"_id": ObjectId(item_id)})

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Generate prediction
        prediction = analytics_engine.predict_price_movements(item)

        return JSONResponse(
            {"success": True, "item": item.get("name"), "prediction": prediction}
        )
    except Exception as e:
        logger.error(f"Error predicting price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== REAL DATA INTEGRATION ENDPOINTS ==========


@api_router.post("/integration/run-comprehensive-real-data")
async def run_comprehensive_integration(days: int = 7):
    """
    Integrate real historical price data from DA Daily Price Index
    Downloads and parses actual daily PDFs to build price trends
    """
    try:
        logger.info(
            f"Starting comprehensive real data integration (last {days} days)..."
        )
        success = await integrate_comprehensive_real_data(db, days)

        if success:
            count = await db.market_items.count_documents({})

            # Get sample item to show metadata
            sample = await db.market_items.find_one(
                {}, {"metadata": 1, "name": 1, "trend": 1}
            )

            return JSONResponse(
                {
                    "success": True,
                    "message": "Real historical data integrated successfully",
                    "total_items": count,
                    "data_source": "DA Bantay Presyo Daily Price Index",
                    "days_analyzed": days,
                    "note": "Real price trends from actual daily PDFs",
                    "sample": {
                        "item": sample.get("name") if sample else None,
                        "trend_points": len(sample.get("trend", [])) if sample else 0,
                        "date_range": sample.get("metadata", {}).get("date_range")
                        if sample
                        else None,
                    },
                }
            )
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Integration failed - check logs for details",
                },
                status_code=500,
            )
    except Exception as e:
        logger.error(f"Error in comprehensive integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-weather-update")
async def run_weather_update_endpoint():
    """Fetch live weather from WeatherAPI.com and update climate_metrics in MongoDB."""
    try:
        result = await run_weather_update(db)
        status_code = 200 if result.get("success") else 500
        return JSONResponse(result, status_code=status_code)
    except Exception as e:
        logger.error(f"Error in weather update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-doe-update")
async def run_doe_update_endpoint(
    full: bool = Query(
        False,
        description="If true, backfill ALL pages (500+ issuances). Default: incremental (first 5 pages per subcategory).",
    ),
):
    """Fetch real DOE issuances and upsert to MongoDB doe_circulars collection."""
    try:
        result = await run_doe_update(db, full=full)
        status_code = 200 if result.get("success") else 500
        return JSONResponse(result, status_code=status_code)
    except Exception as e:
        logger.error(f"Error in DOE update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-realistic-data")
async def run_realistic_integration():
    """Integrate realistic price data based on actual NCR patterns"""
    try:
        logger.info("Starting realistic data integration...")
        success = await integrate_simple_real_data(db)

        if success:
            count = await db.market_items.count_documents({})
            return JSONResponse(
                {
                    "success": True,
                    "message": "Realistic market data integrated successfully",
                    "total_items": count,
                    "note": "Data based on actual DA Bantay Presyo NCR price patterns with realistic variations",
                }
            )
        else:
            return JSONResponse(
                {"success": False, "message": "Integration failed"}, status_code=500
            )
    except Exception as e:
        logger.error(f"Error in realistic integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-fuel-update")
async def run_fuel_update_endpoint():
    """Fetch live NCR fuel prices from DOE OIMB (via anomura API) and update market_items."""
    try:
        success = await integrate_doe_fuel_prices(db)
        if success:
            fuel_items = await db.market_items.count_documents({"category": "fuel"})
            return JSONResponse({"success": True, "items_updated": fuel_items})
        return JSONResponse({"success": False, "message": "Fuel integration returned no data"}, status_code=500)
    except Exception as e:
        logger.error(f"Error in fuel update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-ppa-update")
async def run_ppa_update_endpoint():
    """Download DOE awarded RE contract PDFs, parse them, and upsert to MongoDB."""
    try:
        result = await scrape_all_contracts(db)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in PPA update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/integration/run-da-bantay-presyo")
async def run_da_integration():
    """Trigger real data integration from DA Bantay Presyo"""
    try:
        logger.info("Starting DA Bantay Presyo integration...")
        integrator = DABantayPresyoIntegration(db)
        success = await integrator.run_full_integration()

        if success:
            # Get updated count
            count = await db.market_items.count_documents({})
            return JSONResponse(
                {
                    "success": True,
                    "message": "DA Bantay Presyo data integrated successfully",
                    "total_items": count,
                }
            )
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Integration failed - check logs for details",
                },
                status_code=500,
            )
    except Exception as e:
        logger.error(f"Error in DA integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/integration/status")
async def get_integration_status():
    """Get status of last data integration"""
    try:
        # Get latest updated item
        latest = await db.market_items.find_one({}, sort=[("lastUpdated", -1)])

        if latest:
            return JSONResponse(
                {
                    "success": True,
                    "last_update": latest.get("lastUpdated").isoformat()
                    if latest.get("lastUpdated")
                    else None,
                    "total_items": await db.market_items.count_documents({}),
                    "data_source": "DA Bantay Presyo",
                }
            )
        else:
            return JSONResponse({"success": False, "message": "No data available"})
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENERGY INTELLIGENCE ENDPOINTS ==========


@api_router.get("/energy/news")
async def get_energy_news(query: str = "renewable energy"):
    """Get latest energy news from NewsData.io"""
    try:
        articles = await news_integration.fetch_energy_news(query=query)
        return JSONResponse({"success": True, "count": len(articles), "data": articles})
    except Exception as e:
        logger.error(f"Error fetching energy news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/news/multiple")
async def get_multiple_energy_news():
    """Get energy news for multiple queries"""
    try:
        results = await news_integration.fetch_multiple_queries()
        total_articles = sum(len(articles) for articles in results.values())
        return JSONResponse(
            {"success": True, "total_articles": total_articles, "data": results}
        )
    except Exception as e:
        logger.error(f"Error fetching multiple news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/doe-circulars")
async def get_doe_circulars():
    """Get DOE circulars and orders from MongoDB (populated by run-doe-update)"""
    try:
        cursor = (
            db.doe_circulars.find({}, {"_id": 0}).sort("date_published", -1).limit(20)
        )
        circulars = await cursor.to_list(length=20)

        if not circulars:
            # Fallback to live scrape if MongoDB is empty
            from services.doe_integration import fetch_doe_issuances

            circulars = await fetch_doe_issuances()

        # Convert datetime objects to ISO strings for JSON serialization
        for doc in circulars:
            for key, val in doc.items():
                if isinstance(val, datetime):
                    doc[key] = val.isoformat()

        return JSONResponse(
            {"success": True, "count": len(circulars), "data": circulars}
        )
    except Exception as e:
        logger.error(f"Error fetching DOE circulars: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/ppa-status")
async def get_ppa_statuses(
    technology: Optional[str] = None,
    stage: Optional[str] = None,
    island: Optional[str] = None,
    limit: int = 50,
):
    """Get RE Service Contracts from DOE awarded projects (real data from legacy.doe.gov.ph PDFs)."""
    try:
        query = {}
        if technology:
            query["technology"] = {"$regex": technology, "$options": "i"}
        if stage:
            query["stage"] = {"$regex": stage, "$options": "i"}
        if island:
            query["island"] = {"$regex": island, "$options": "i"}

        total = await db.ppa_contracts.count_documents(query)
        cursor = db.ppa_contracts.find(query).sort("potential_capacity_mw", -1).limit(limit)
        contracts = await cursor.to_list(length=limit)

        for c in contracts:
            c["id"] = str(c.pop("_id"))
            if "scraped_at" in c and hasattr(c["scraped_at"], "isoformat"):
                c["scraped_at"] = c["scraped_at"].isoformat()

        # Summary stats
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$technology",
                "count": {"$sum": 1},
                "total_potential_mw": {"$sum": "$potential_capacity_mw"},
                "total_installed_mw": {"$sum": "$installed_capacity_mw"},
            }},
        ]
        tech_summary = await db.ppa_contracts.aggregate(pipeline).to_list(length=20)

        return JSONResponse({
            "success": True,
            "count": len(contracts),
            "total": total,
            "data": contracts,
            "data_status": "available" if total > 0 else "empty",
            "source": "DOE Legacy Site — Awarded RE Service Contracts (as of April 2025)",
            "technology_summary": tech_summary,
        })
    except Exception as e:
        logger.error(f"Error fetching PPA statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/grid-status")
async def get_grid_status():
    """
    Get current grid status.
    Primary: NGCP Power Situation Outlook (Playwright scrape of ngcp.ph).
    Fallback: WESM-price-derived status if NGCP is unreachable.
    """
    try:
        # Fetch NGCP and WESM data concurrently
        ngcp_data, price_trends = await asyncio.gather(
            ngcp_scraper.scrape(),
            wesm_scraper.fetch_price_trends(days=1),
            return_exceptions=True,
        )
        if isinstance(ngcp_data, Exception):
            ngcp_data = {}
        if isinstance(price_trends, Exception):
            price_trends = {}

        # Derive overall status from Luzon WESM price
        luzon_price = (price_trends.get("wesm_luzon") or {}).get("current", 0)
        if luzon_price > 8000:
            overall_status = "TIGHT"
        elif luzon_price > 6000:
            overall_status = "ELEVATED"
        else:
            overall_status = "STABLE"

        if ngcp_data is not None:
            grid_data = {
                **ngcp_data,
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Persist successful NGCP scrape to MongoDB for fallback
            try:
                await db.grid_status_cache.update_one(
                    {"_id": "latest"},
                    {"$set": {**ngcp_data, "cached_at": datetime.utcnow().isoformat()}},
                    upsert=True,
                )
            except Exception:
                pass  # Persistence failure is non-critical
        else:
            # Try MongoDB cached value before showing full unavailable
            cached = await db.grid_status_cache.find_one({"_id": "latest"}, {"_id": 0})
            if cached:
                cached_at = cached.pop("cached_at", "unknown")
                grid_data = {
                    **cached,
                    "status": overall_status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_source": f"NGCP data from cache (scraped {cached_at}); MW values may be stale",
                }
            else:
                # Full fallback when NGCP is unreachable and no cache
                grid_data = {
                    "status": overall_status,
                    "total_demand": None,
                    "total_supply": None,
                    "reserves": None,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_source": "Status from IEMOP WESM prices; MW data unavailable (NGCP unreachable)",
                    "grids": [
                        {"name": "Luzon", "status": overall_status, "capacity": None, "current": None},
                        {"name": "Visayas", "status": "NORMAL", "capacity": None, "current": None},
                        {"name": "Mindanao", "status": "NORMAL", "capacity": None, "current": None},
                    ],
                }

        return JSONResponse({"success": True, "data": grid_data})
    except Exception as e:
        logger.error(f"Error fetching grid status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_price_alerts(price_trends: dict) -> list:
    """Generate market alerts from real WESM price data."""
    alerts = []
    now = datetime.utcnow().isoformat()
    for key, data in price_trends.items():
        region = key.replace("wesm_", "WESM ").title()
        change = data.get("change_pct", 0)
        current = data.get("current", 0)
        if current > 8000:
            alerts.append(
                {
                    "type": "price",
                    "severity": "high",
                    "message": f"{region} prices critically high at ₱{current:,}/MWh",
                    "timestamp": now,
                }
            )
        elif abs(change) >= 5:
            direction = "up" if change > 0 else "down"
            severity = "medium" if abs(change) >= 5 else "low"
            alerts.append(
                {
                    "type": "price",
                    "severity": severity,
                    "message": f"{region} prices {direction} {abs(change):.1f}% this week",
                    "timestamp": now,
                }
            )
    if not alerts:
        alerts.append(
            {
                "type": "price",
                "severity": "low",
                "message": "WESM prices stable across all regions",
                "timestamp": now,
            }
        )
    return alerts


def _derive_market_outlook(price_trends: dict) -> dict:
    """Compute market outlook from real WESM price levels (absolute PHP/MWh)."""
    luzon_current = price_trends.get("wesm_luzon", {}).get("current", 0) or 0
    visayas_current = price_trends.get("wesm_visayas", {}).get("current", 0) or 0
    mindanao_current = price_trends.get("wesm_mindanao", {}).get("current", 0) or 0

    active = [p for p in [luzon_current, visayas_current, mindanao_current] if p > 0]
    avg_current = sum(active) / len(active) if active else 0

    if avg_current > 8000:
        short_term, price_forecast, supply_adequacy = "rising", "moderate_increase", "constrained"
    elif avg_current > 6000:
        short_term, price_forecast, supply_adequacy = "elevated", "stable", "moderate"
    else:
        short_term, price_forecast, supply_adequacy = "stable", "stable", "sufficient"

    key_drivers = []
    if luzon_current > 8000:
        key_drivers.append(f"Luzon spot price high at ₱{luzon_current:,.0f}/MWh")
    elif luzon_current > 6000:
        key_drivers.append(f"Luzon spot price elevated at ₱{luzon_current:,.0f}/MWh")
    elif luzon_current > 0:
        key_drivers.append(f"Luzon spot price normal at ₱{luzon_current:,.0f}/MWh")
    if visayas_current > 7000:
        key_drivers.append(f"Visayas spot price elevated at ₱{visayas_current:,.0f}/MWh")
    key_drivers += ["Increasing RE capacity additions", "Coal plant retirements"]
    return {
        "short_term": short_term,
        "supply_adequacy": supply_adequacy,
        "price_forecast": price_forecast,
        "key_drivers": key_drivers[:4],
    }


@api_router.get("/energy/analytics")
async def get_energy_analytics():
    """Get energy market analytics including price trends and contract insights"""
    try:
        # Get real PPA data from MongoDB (populated by run-ppa-update)
        ppa_total = await db.ppa_contracts.count_documents({})
        ppa_pipeline = [
            {"$group": {
                "_id": "$stage",
                "count": {"$sum": 1},
                "capacity": {"$sum": "$potential_capacity_mw"},
                "installed": {"$sum": "$installed_capacity_mw"},
            }},
        ]
        stage_stats = {s["_id"]: s for s in await db.ppa_contracts.aggregate(ppa_pipeline).to_list(20)}

        tech_pipeline = [
            {"$group": {
                "_id": "$technology",
                "count": {"$sum": 1},
                "capacity_mw": {"$sum": "$potential_capacity_mw"},
            }},
        ]
        tech_breakdown = {
            t["_id"]: {"count": t["count"], "capacity_mw": round(t["capacity_mw"], 2)}
            for t in await db.ppa_contracts.aggregate(tech_pipeline).to_list(20)
        }

        operational = stage_stats.get("Commercial Operation", {"count": 0, "capacity": 0, "installed": 0})
        development = stage_stats.get("Development", {"count": 0, "capacity": 0})
        pre_dev = stage_stats.get("Pre-Development", {"count": 0, "capacity": 0})

        total_capacity = sum(s["capacity"] for s in stage_stats.values())

        # Price trends — real data from IEMOP, fallback to static estimates
        PRICE_TRENDS_FALLBACK = {
            "wesm_luzon": {
                "current": 5842,
                "week_ago": 5398,
                "month_ago": 5125,
                "trend": [5125, 5234, 5398, 5567, 5712, 5842],
                "change_pct": 8.2,
                "source": "estimated",
            },
            "wesm_visayas": {
                "current": 6123,
                "week_ago": 5890,
                "month_ago": 5678,
                "trend": [5678, 5789, 5890, 5987, 6045, 6123],
                "change_pct": 7.8,
                "source": "estimated",
            },
            "wesm_mindanao": {
                "current": 4567,
                "week_ago": 4432,
                "month_ago": 4298,
                "trend": [4298, 4356, 4432, 4487, 4523, 4567],
                "change_pct": 6.3,
                "source": "estimated",
            },
        }
        price_trends = await wesm_scraper.fetch_price_trends(days=7)
        if not price_trends:
            logger.warning("IEMOP unavailable; using fallback price trends")
            price_trends = PRICE_TRENDS_FALLBACK

        analytics = {
            "ppa_summary": {
                "total_projects": ppa_total,
                "total_capacity_mw": round(total_capacity, 2),
                "operational_count": operational["count"],
                "operational_capacity": round(operational.get("installed", 0), 2),
                "development_count": development["count"],
                "development_capacity": round(development["capacity"], 2),
                "pre_development_count": pre_dev["count"],
                "pre_development_capacity": round(pre_dev["capacity"], 2),
                "source": "DOE Awarded RE Service Contracts (April 2025)",
            },
            "technology_breakdown": tech_breakdown,
            "price_trends": price_trends,
            "market_outlook": _derive_market_outlook(price_trends),
            "alerts": _build_price_alerts(price_trends),
        }

        return JSONResponse(
            {
                "success": True,
                "generated_at": datetime.utcnow().isoformat(),
                "data": analytics,
            }
        )
    except Exception as e:
        logger.error(f"Error generating energy analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== GROCERY BASKET ENDPOINTS ==========

BASKET_TEMPLATES = {
    "basic_family": {
        "name": "Basic Family Basket",
        "description": "Essential items for a Filipino family of 4 (weekly)",
        "items": ["rice", "chicken", "pork", "bangus", "tomato", "onion", "garlic", "kangkong", "egg"],
    },
    "budget": {
        "name": "Budget Basket",
        "description": "Low-cost staples for daily meals",
        "items": ["rice", "sardines", "egg", "kangkong", "mongo", "camote"],
    },
    "vegetarian": {
        "name": "Vegetarian Basket",
        "description": "Plant-based essentials",
        "items": ["rice", "tofu", "kangkong", "tomato", "onion", "garlic", "eggplant", "sitaw"],
    },
}


async def _find_cheapest_match(db, item_name: str):
    """Return cheapest market_item whose name matches item_name (case-insensitive)."""
    cursor = db.market_items.find(
        {"name": {"$regex": item_name, "$options": "i"}}
    ).sort("currentPrice", 1).limit(1)
    matches = await cursor.to_list(length=1)
    if not matches:
        return None
    item = matches[0]
    item["id"] = str(item.pop("_id"))
    for field in ("lastUpdated", "createdAt", "updatedAt"):
        if field in item and hasattr(item[field], "isoformat"):
            item[field] = item[field].isoformat()
    return item


@api_router.get("/basket/cheapest")
async def get_cheapest_basket(
    items: str = Query(..., description="Comma-separated commodity names, e.g. rice,chicken,tomato"),
):
    """Build the cheapest basket from tracked market prices for the requested items."""
    try:
        item_names = [n.strip() for n in items.split(",") if n.strip()]
        if not item_names:
            raise HTTPException(status_code=400, detail="Provide at least one item name")

        results = []
        not_found = []
        total_cost = 0.0

        for name in item_names:
            match = await _find_cheapest_match(db, name)
            if match:
                results.append({
                    "requested": name,
                    "matched": match["name"],
                    "category": match.get("category"),
                    "price": match.get("currentPrice"),
                    "unit": match.get("unit"),
                    "status": match.get("status"),
                    "savings": match.get("savings", 0),
                })
                total_cost += match.get("currentPrice", 0)
            else:
                not_found.append(name)

        return JSONResponse({
            "success": True,
            "basket": results,
            "total_cost": round(total_cost, 2),
            "item_count": len(results),
            "not_found": not_found,
            "currency": "PHP",
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building basket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/basket/templates")
async def get_basket_templates():
    """Return preset basket templates with live cheapest prices from market_items."""
    try:
        output = []
        for template_id, template in BASKET_TEMPLATES.items():
            results = []
            total_cost = 0.0
            not_found = []
            for name in template["items"]:
                match = await _find_cheapest_match(db, name)
                if match:
                    results.append({
                        "requested": name,
                        "matched": match["name"],
                        "price": match.get("currentPrice"),
                        "unit": match.get("unit"),
                        "status": match.get("status"),
                    })
                    total_cost += match.get("currentPrice", 0)
                else:
                    not_found.append(name)
            output.append({
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "basket": results,
                "total_cost": round(total_cost, 2),
                "item_count": len(results),
                "not_found": not_found,
                "currency": "PHP",
            })
        return JSONResponse({"success": True, "count": len(output), "data": output})
    except Exception as e:
        logger.error(f"Error fetching basket templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== TELEGRAM BOT ENDPOINTS ==========

from services.telegram_bot import send_message, build_daily_alert, broadcast


@api_router.post("/telegram/subscribe")
async def telegram_subscribe(chat_id: str = Query(..., description="Telegram chat ID")):
    """Subscribe a Telegram chat ID to daily price alerts."""
    await db.telegram_subscribers.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "active": True, "subscribed_at": datetime.utcnow().isoformat()}},
        upsert=True,
    )
    ok = await send_message(chat_id, "✅ You're subscribed to Climate Intel daily price alerts!\n\nYou'll receive a morning briefing every weekday with top price movements, climate data, and grid status.")
    return JSONResponse({"success": True, "message": "Subscribed", "welcome_sent": ok})


@api_router.post("/telegram/unsubscribe")
async def telegram_unsubscribe(chat_id: str = Query(...)):
    """Unsubscribe a chat ID from alerts."""
    await db.telegram_subscribers.update_one({"chat_id": chat_id}, {"$set": {"active": False}})
    return JSONResponse({"success": True, "message": "Unsubscribed"})


@api_router.get("/telegram/subscribers")
async def telegram_subscribers():
    """Return subscriber count."""
    total = await db.telegram_subscribers.count_documents({})
    active = await db.telegram_subscribers.count_documents({"active": True})
    return JSONResponse({"success": True, "data": {"total": total, "active": active}})


@api_router.post("/telegram/send-daily-alert")
async def telegram_send_daily_alert():
    """Trigger daily price alert broadcast to all active subscribers."""
    try:
        # Fetch data for the alert
        items_cursor = db.market_items.find({}).sort("priceStatus", 1).limit(10)
        items = []
        async for doc in items_cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)

        metrics = []
        async for doc in db.climate_metrics.find({}):
            doc["_id"] = str(doc["_id"])
            metrics.append(doc)

        grid = await ngcp_scraper.scrape()

        message = build_daily_alert(items, metrics, grid)
        stats = await broadcast(db, message)

        return JSONResponse({"success": True, "data": stats, "message_preview": message[:200]})
    except Exception as e:
        logger.error(f"Telegram broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== HISTORICAL PRICE ARCHIVE ENDPOINTS ==========

from services.historical_backfill import backfill_date_range


@api_router.post("/integration/run-historical-backfill")
async def run_historical_backfill(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
):
    """
    Backfill price_history collection from DA Bantay Presyo PDFs for a date range.
    Weekends are skipped automatically. Rate-limited at 1.5s per page.
    WARNING: Large ranges (e.g. 1 year) will take ~90 minutes — run as a one-time job.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD")

    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    delta_days = (end - start).days
    if delta_days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days per request")

    stats = await backfill_date_range(db, start, end)
    return JSONResponse({"success": True, "data": stats})


@api_router.get("/price-history")
async def get_price_history(
    name: str = Query(..., description="Commodity name (exact or partial)"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """Return daily price history for a commodity from the price_history collection."""
    query: dict = {"name": {"$regex": name, "$options": "i"}}
    date_filter: dict = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lte"] = end_date
    if date_filter:
        query["date"] = date_filter

    cursor = db.price_history.find(query, {"_id": 0}).sort("date", 1).limit(500)
    records = []
    async for doc in cursor:
        records.append(doc)

    return JSONResponse({"success": True, "count": len(records), "data": records})


# ========== CROWDSOURCED PRICING ENDPOINTS ==========


@api_router.post("/crowdsource/report")
async def crowdsource_report(
    item_name: str = Query(..., description="Commodity name"),
    price: float = Query(..., description="Observed price (PHP)"),
    market: str = Query(..., description="Market/store where observed"),
    unit: str = Query(default="kg", description="Unit (kg, piece, bundle, L)"),
    reporter_id: Optional[str] = Query(default=None, description="Anonymous session ID for deduplication"),
):
    """
    Submit a crowdsourced price report from a user who observed actual market prices.
    Stored in `crowd_price_reports` collection with status=pending until validated.
    """
    if price <= 0 or price > 10000:
        raise HTTPException(status_code=400, detail="Price must be between 0 and 10,000 PHP")

    doc = {
        "item_name": item_name.strip(),
        "price": round(price, 2),
        "market": market.strip(),
        "unit": unit,
        "reporter_id": reporter_id,
        "status": "pending",
        "reported_at": datetime.utcnow().isoformat(),
    }
    result = await db.crowd_price_reports.insert_one(doc)
    return JSONResponse({"success": True, "report_id": str(result.inserted_id)})


@api_router.get("/crowdsource/reports")
async def get_crowdsource_reports(
    item_name: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default="pending"),
    limit: int = Query(default=50, le=200),
):
    """List crowdsourced price reports (for moderation or display)."""
    query: dict = {}
    if item_name:
        query["item_name"] = {"$regex": item_name, "$options": "i"}
    if status:
        query["status"] = status

    cursor = db.crowd_price_reports.find(query, {"_id": 0}).sort("reported_at", -1).limit(limit)
    reports = []
    async for doc in cursor:
        reports.append(doc)

    return JSONResponse({"success": True, "count": len(reports), "data": reports})


@api_router.get("/crowdsource/summary")
async def crowdsource_summary(item_name: str = Query(...)):
    """
    Return crowd-vs-official price comparison for a commodity.
    Aggregates last 7 days of approved crowd reports against the official DA price.
    """
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    pipeline = [
        {"$match": {"item_name": {"$regex": item_name, "$options": "i"}, "status": "approved", "reported_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$item_name", "avg_crowd_price": {"$avg": "$price"}, "min_price": {"$min": "$price"}, "max_price": {"$max": "$price"}, "report_count": {"$sum": 1}}},
    ]
    results = []
    async for doc in db.crowd_price_reports.aggregate(pipeline):
        results.append(doc)

    # Get official DA price
    official = await db.market_items.find_one({"name": {"$regex": item_name, "$options": "i"}}, {"currentPrice": 1, "name": 1})
    official_price = official.get("currentPrice") if official else None
    official_name = official.get("name") if official else item_name

    if results:
        r = results[0]
        diff_pct = round((r["avg_crowd_price"] - official_price) / official_price * 100, 1) if official_price else None
        return JSONResponse({"success": True, "data": {
            "item_name": official_name,
            "official_price": official_price,
            "avg_crowd_price": round(r["avg_crowd_price"], 2),
            "min_crowd_price": r["min_price"],
            "max_crowd_price": r["max_price"],
            "report_count": r["report_count"],
            "vs_official_pct": diff_pct,
        }})
    else:
        return JSONResponse({"success": True, "data": {"item_name": official_name, "official_price": official_price, "avg_crowd_price": None, "report_count": 0}})


# ========== UTILITY ENDPOINTS ==========


@api_router.get("/categories")
async def get_categories():
    """Get all categories"""
    categories = [
        {"id": "all", "name": "All Items", "icon": "📊"},
        {"id": "vegetables", "name": "Vegetables", "icon": "🥬"},
        {"id": "meat", "name": "Meat", "icon": "🥩"},
        {"id": "poultry", "name": "Poultry", "icon": "🍗"},
        {"id": "fish", "name": "Fish", "icon": "🐟"},
        {"id": "rice", "name": "Rice", "icon": "🍚"},
        {"id": "spices", "name": "Spices", "icon": "🌶️"},
        {"id": "fuel", "name": "Fuel", "icon": "⛽"},
    ]
    return JSONResponse({"success": True, "data": categories})


@api_router.get("/")
async def root():
    return {"message": "Climate-Smart Market Intelligence API", "version": "1.0.0"}


# Include the router in the main app
app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
