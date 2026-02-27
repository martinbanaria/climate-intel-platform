#!/usr/bin/env python3
"""
Seed script to populate database with initial market and climate data
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Import mock data structure (we'll define it here for seeding)
from datetime import datetime

async def seed_database():
    """Seed the database with initial data"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Seeding database...")
    
    # Clear existing data
    await db.market_items.delete_many({})
    await db.climate_metrics.delete_many({})
    print("✓ Cleared existing data")
    
    # Seed market items (subset of the full 62 items)
    market_items = [
        {
            "name": "Lettuce (Romaine)",
            "category": "vegetables",
            "currentPrice": 168.77,
            "averagePrice": 207,
            "unit": "kg",
            "location": "NCR",
            "icon": "🥬",
            "status": "MURA",
            "savings": 38.23,
            "trend": [220, 210, 195, 185, 175, 168.77],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "low",
                "factors": ["Favorable rainfall", "Optimal temperature"],
                "forecast": "Prices expected to remain stable"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Broccoli (Local Medium)",
            "category": "vegetables",
            "currentPrice": 144.67,
            "averagePrice": 160,
            "unit": "kg",
            "location": "NCR",
            "icon": "🥦",
            "status": "MURA",
            "savings": 15.33,
            "trend": [165, 162, 158, 152, 148, 144.67],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "low",
                "factors": ["Ideal growing conditions"],
                "forecast": "Prices trending down"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Chicken (Whole)",
            "category": "poultry",
            "currentPrice": 165.50,
            "averagePrice": 172,
            "unit": "kg",
            "location": "NCR",
            "icon": "🍗",
            "status": "STABLE",
            "savings": 6.50,
            "trend": [175, 173, 171, 169, 167, 165.50],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "medium",
                "factors": ["Heat stress concerns", "Feed costs stable"],
                "forecast": "Monitoring temperature impact"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Tilapia",
            "category": "fish",
            "currentPrice": 135,
            "averagePrice": 145,
            "unit": "kg",
            "location": "NCR",
            "icon": "🐟",
            "status": "MURA",
            "savings": 10,
            "trend": [152, 150, 147, 142, 138, 135],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "low",
                "factors": ["Good water quality"],
                "forecast": "Stable aquaculture output"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Glutinous Rice",
            "category": "rice",
            "currentPrice": 61.19,
            "averagePrice": 68,
            "unit": "kg",
            "location": "NCR",
            "icon": "🍚",
            "status": "MURA",
            "savings": 6.81,
            "trend": [72, 70, 68, 65, 63, 61.19],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "medium",
                "factors": ["Good harvest season", "Low drought risk"],
                "forecast": "Stable supply expected"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Garlic (Local)",
            "category": "spices",
            "currentPrice": 185,
            "averagePrice": 165,
            "unit": "kg",
            "location": "NCR",
            "icon": "🧄",
            "status": "MAHAL",
            "savings": -20,
            "trend": [160, 165, 170, 175, 180, 185],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "high",
                "factors": ["Drought reducing yield", "Heat damage"],
                "forecast": "Limited supply, prices rising"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Diesel",
            "category": "fuel",
            "currentPrice": 58.75,
            "averagePrice": 62,
            "unit": "L",
            "location": "NCR",
            "icon": "⛽",
            "status": "STABLE",
            "savings": 3.25,
            "trend": [64, 63, 61.5, 60, 59, 58.75],
            "lastUpdated": datetime.utcnow(),
            "climateImpact": {
                "level": "medium",
                "factors": ["Global climate policies", "Renewable shift"],
                "forecast": "Long-term downward pressure"
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    result = await db.market_items.insert_many(market_items)
    print(f"✓ Inserted {len(result.inserted_ids)} market items")
    
    # Seed climate metrics
    climate_metrics = [
        {
            "name": "Temperature",
            "category": "climate",
            "currentValue": 28.5,
            "averageValue": 31.2,
            "unit": "°C",
            "status": "GOOD",
            "icon": "🌡️",
            "trend": [32, 31, 30, 29.5, 29, 28.5],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Comfortable temperature range. Stay hydrated and use sun protection.",
            "impact": "Lower temperatures benefit crop growth and reduce livestock heat stress",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Rainfall",
            "category": "climate",
            "currentValue": 45.3,
            "averageValue": 35.8,
            "unit": "mm",
            "status": "GOOD",
            "icon": "🌧️",
            "trend": [28, 32, 38, 42, 44, 45.3],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Adequate rainfall for agriculture. Good conditions for farming.",
            "impact": "Optimal moisture levels supporting vegetable production and lowering irrigation costs",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Air Quality Index",
            "category": "climate",
            "currentValue": 42,
            "averageValue": 68,
            "unit": "AQI",
            "status": "GOOD",
            "icon": "🌬️",
            "trend": [65, 58, 52, 48, 45, 42],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Air quality is excellent. Perfect conditions for outdoor activities.",
            "impact": "Good air quality supports healthy crop growth and livestock wellness",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Humidity",
            "category": "climate",
            "currentValue": 72,
            "averageValue": 65,
            "unit": "%",
            "status": "MODERATE",
            "icon": "💧",
            "trend": [68, 69, 70, 71, 71.5, 72],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Slightly elevated humidity. Monitor for pest issues in crops.",
            "impact": "Higher humidity may increase disease pressure on leafy vegetables",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "UV Index",
            "category": "climate",
            "currentValue": 9.2,
            "averageValue": 7.5,
            "unit": "UV",
            "status": "WARNING",
            "icon": "☀️",
            "trend": [6.5, 7, 7.8, 8.5, 9, 9.2],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Very high UV levels. Use SPF 50+ sunscreen and seek shade during 10am-4pm.",
            "impact": "High UV can stress crops but also helps natural pest control",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Soil Moisture",
            "category": "climate",
            "currentValue": 35,
            "averageValue": 28,
            "unit": "%",
            "status": "GOOD",
            "icon": "🌱",
            "trend": [25, 27, 29, 31, 33, 35],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Optimal soil moisture for planting. Good conditions for crop growth.",
            "impact": "Excellent conditions supporting vegetable production and stable prices",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Drought Index",
            "category": "climate",
            "currentValue": 2.1,
            "averageValue": 3.5,
            "unit": "scale",
            "status": "GOOD",
            "icon": "🏜️",
            "trend": [4.2, 3.8, 3.2, 2.8, 2.4, 2.1],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Low drought risk. Adequate water supply for agriculture.",
            "impact": "Minimal drought stress keeping crop prices stable",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Wind Speed",
            "category": "climate",
            "currentValue": 15.3,
            "averageValue": 18.7,
            "unit": "km/h",
            "status": "GOOD",
            "icon": "💨",
            "trend": [22, 20, 18.5, 17, 16, 15.3],
            "lastUpdated": datetime.utcnow(),
            "recommendation": "Gentle breeze conditions. Safe for all outdoor activities.",
            "impact": "Calm conditions favorable for farming operations and fishing",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    result = await db.climate_metrics.insert_many(climate_metrics)
    print(f"✓ Inserted {len(result.inserted_ids)} climate metrics")
    
    # Create indexes for better performance
    await db.market_items.create_index("category")
    await db.market_items.create_index("status")
    await db.market_items.create_index("name")
    await db.climate_metrics.create_index("category")
    print("✓ Created database indexes")
    
    print("\\n✅ Database seeded successfully!")
    print(f"📊 Market items: {len(market_items)}")
    print(f"🌡️ Climate metrics: {len(climate_metrics)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
