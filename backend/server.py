from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

# Import services
from services.web_crawler import crawler
from services.ocr_service import ocr_service
from services.analytics_engine import analytics_engine
from services.real_data_integration import DABantayPresyoIntegration
from services.simple_real_data import integrate_simple_real_data
from services.comprehensive_real_data import integrate_comprehensive_real_data
from services.newsdata_integration import news_integration
from services.doe_document_scraper import doe_scraper
from models import MarketItem, ClimateMetric, ScrapedDocument, AnalyticsInsight

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
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
        cursor = db.market_items.find(query).limit(limit)
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
    except Exception as e:
        logger.error(f"Error fetching market item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/best-deals")
async def get_best_deals(limit: int = 8):
    """Get top deals (MURA items sorted by savings)"""
    try:
        # Query for MURA items
        query = {"status": "MURA"}
        cursor = db.market_items.find(query)
        items = await cursor.to_list(length=100)

        # Convert ObjectId and sort by savings
        for item in items:
            item["id"] = str(item.pop("_id"))
            if "lastUpdated" in item:
                item["lastUpdated"] = item["lastUpdated"].isoformat()
            if "createdAt" in item:
                item["createdAt"] = item["createdAt"].isoformat()
            if "updatedAt" in item:
                item["updatedAt"] = item["updatedAt"].isoformat()

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
        return JSONResponse({"success": True, "data": metric})
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
    """Get DOE circulars and orders"""
    try:
        circulars = await doe_scraper.scrape_doe_circulars()
        return JSONResponse(
            {"success": True, "count": len(circulars), "data": circulars}
        )
    except Exception as e:
        logger.error(f"Error fetching DOE circulars: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/ppa-status")
async def get_ppa_statuses():
    """Get Power Purchase Agreement statuses"""
    try:
        ppa_list = await doe_scraper.scrape_ppa_statuses()
        return JSONResponse({"success": True, "count": len(ppa_list), "data": ppa_list})
    except Exception as e:
        logger.error(f"Error fetching PPA statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/grid-status")
async def get_grid_status():
    """Get current grid status (mock data - ready for NGCP integration)"""
    try:
        # Mock grid data - in production, integrate with NGCP API
        grid_data = {
            "total_demand": 15234,
            "total_supply": 16100,
            "reserves": 866,
            "status": "STABLE",
            "timestamp": datetime.utcnow().isoformat(),
            "grids": [
                {
                    "name": "Luzon",
                    "capacity": 9845,
                    "current": 8567,
                    "status": "OPTIMAL",
                },
                {
                    "name": "Visayas",
                    "capacity": 3234,
                    "current": 2987,
                    "status": "NORMAL",
                },
                {
                    "name": "Mindanao",
                    "capacity": 3021,
                    "current": 2680,
                    "status": "NORMAL",
                },
            ],
        }
        return JSONResponse({"success": True, "data": grid_data})
    except Exception as e:
        logger.error(f"Error fetching grid status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/energy/analytics")
async def get_energy_analytics():
    """Get energy market analytics including price trends and contract insights"""
    try:
        # Get PPA data
        ppa_list = await doe_scraper.scrape_ppa_statuses()

        # Calculate PPA analytics
        total_capacity = sum(ppa.get("capacity_mw", 0) for ppa in ppa_list)
        operational = [p for p in ppa_list if p.get("status") == "Operational"]
        under_construction = [
            p for p in ppa_list if p.get("status") == "Under Construction"
        ]
        contracted = [p for p in ppa_list if p.get("status") == "Contracted"]

        # Technology breakdown
        tech_breakdown = {}
        for ppa in ppa_list:
            tech = ppa.get("technology", "Unknown")
            if tech not in tech_breakdown:
                tech_breakdown[tech] = {"count": 0, "capacity_mw": 0}
            tech_breakdown[tech]["count"] += 1
            tech_breakdown[tech]["capacity_mw"] += ppa.get("capacity_mw", 0)

        # Price trends (mock data based on WESM patterns)
        price_trends = {
            "wesm_luzon": {
                "current": 5842,
                "week_ago": 5398,
                "month_ago": 5125,
                "trend": [5125, 5234, 5398, 5567, 5712, 5842],
                "change_pct": 8.2,
            },
            "wesm_visayas": {
                "current": 6123,
                "week_ago": 5890,
                "month_ago": 5678,
                "trend": [5678, 5789, 5890, 5987, 6045, 6123],
                "change_pct": 7.8,
            },
            "wesm_mindanao": {
                "current": 4567,
                "week_ago": 4432,
                "month_ago": 4298,
                "trend": [4298, 4356, 4432, 4487, 4523, 4567],
                "change_pct": 6.3,
            },
        }

        analytics = {
            "ppa_summary": {
                "total_projects": len(ppa_list),
                "total_capacity_mw": total_capacity,
                "operational_count": len(operational),
                "operational_capacity": sum(
                    p.get("capacity_mw", 0) for p in operational
                ),
                "under_construction_count": len(under_construction),
                "under_construction_capacity": sum(
                    p.get("capacity_mw", 0) for p in under_construction
                ),
                "contracted_count": len(contracted),
                "contracted_capacity": sum(p.get("capacity_mw", 0) for p in contracted),
            },
            "technology_breakdown": tech_breakdown,
            "price_trends": price_trends,
            "market_outlook": {
                "short_term": "stable",
                "supply_adequacy": "sufficient",
                "price_forecast": "moderate_increase",
                "key_drivers": [
                    "Increasing RE capacity additions",
                    "Coal plant retirements",
                    "Growing industrial demand",
                    "LNG price volatility",
                ],
            },
            "alerts": [
                {
                    "type": "price",
                    "severity": "medium",
                    "message": "WESM Luzon prices up 8.2% this week",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "type": "supply",
                    "severity": "low",
                    "message": "Reserve margin adequate at 866 MW",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ],
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
