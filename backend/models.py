from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ClimateImpactData(BaseModel):
    level: str = Field(..., description="Impact level: low, medium, high")
    factors: List[str] = Field(default_factory=list)
    forecast: str

class MarketItem(BaseModel):
    name: str
    category: str
    currentPrice: float
    averagePrice: float
    unit: str
    location: str
    icon: str
    status: str
    savings: float
    trend: List[float]
    lastUpdated: datetime
    climateImpact: ClimateImpactData
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
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
                "lastUpdated": "2026-02-27T07:00:00Z",
                "climateImpact": {
                    "level": "low",
                    "factors": ["Favorable rainfall", "Optimal temperature"],
                    "forecast": "Prices expected to remain stable"
                }
            }
        }

class ClimateMetric(BaseModel):
    name: str
    category: str = "climate"
    currentValue: float
    averageValue: float
    unit: str
    status: str
    icon: str
    trend: List[float]
    lastUpdated: datetime
    recommendation: str
    impact: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class ScrapedDocument(BaseModel):
    source_url: str
    source_type: str  # "web", "pdf", "image"
    raw_text: Optional[str] = None
    extracted_data: Optional[dict] = None
    processed: bool = False
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsInsight(BaseModel):
    insight_type: str  # "price_prediction", "climate_correlation", "market_trend"
    title: str
    description: str
    confidence: float  # 0-1
    data: dict
    generated_at: datetime = Field(default_factory=datetime.utcnow)
