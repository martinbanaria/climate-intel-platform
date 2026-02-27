# API Contracts & Backend Integration Plan

## Overview
Climate-Smart Market Intelligence Platform - Backend implementation to replace mock data with real database storage and API endpoints.

## Mock Data Currently Used
Located in `/app/frontend/src/mockData.js`:
- **marketItems**: 62+ items (vegetables, meat, poultry, fish, rice, spices, fuel)
- **climateMetrics**: 8 climate monitoring metrics
- **bestDeals**: Filtered top deals from marketItems
- **categories**: 9 categories for filtering

## Database Schema

### Collections

#### 1. `market_items`
```python
{
    "_id": ObjectId,
    "name": str,  # "Lettuce (Romaine)"
    "category": str,  # "vegetables", "meat", "poultry", "fish", "rice", "spices", "fuel"
    "currentPrice": float,
    "averagePrice": float,
    "unit": str,  # "kg", "L", "piece"
    "location": str,  # "NCR"
    "icon": str,  # emoji
    "status": str,  # "MURA", "STABLE", "MAHAL"
    "savings": float,  # currentPrice - averagePrice
    "trend": [float],  # Array of 6 historical prices
    "lastUpdated": datetime,
    "climateImpact": {
        "level": str,  # "low", "medium", "high"
        "factors": [str],  # Array of impact factors
        "forecast": str  # Advisory text
    },
    "createdAt": datetime,
    "updatedAt": datetime
}
```

#### 2. `climate_metrics`
```python
{
    "_id": ObjectId,
    "name": str,  # "Temperature", "Rainfall", etc.
    "category": str,  # "climate"
    "currentValue": float,
    "averageValue": float,
    "unit": str,  # "°C", "mm", "AQI", etc.
    "status": str,  # "GOOD", "MODERATE", "WARNING", "ALERT"
    "icon": str,  # emoji
    "trend": [float],  # Array of 6 historical readings
    "lastUpdated": datetime,
    "recommendation": str,  # Advisory text
    "impact": str,  # Market impact description
    "createdAt": datetime,
    "updatedAt": datetime
}
```

#### 3. `user_favorites`
```python
{
    "_id": ObjectId,
    "userId": str,  # For future auth implementation
    "itemId": str,  # Reference to market_item or climate_metric
    "itemType": str,  # "market" or "climate"
    "createdAt": datetime
}
```

## API Endpoints

### Base URL: `/api`

### Market Items

#### `GET /api/market-items`
**Description**: Get all market items with optional filtering
**Query Parameters**:
- `category` (optional): Filter by category
- `search` (optional): Search by item name
- `sort` (optional): Sort by "best", "price-low", "price-high", "name"
- `limit` (optional): Number of items to return (default: 100)

**Response**:
```json
{
    "success": true,
    "count": 62,
    "data": [
        {
            "id": "507f1f77bcf86cd799439011",
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
    ]
}
```

#### `GET /api/market-items/:id`
**Description**: Get single market item by ID
**Response**: Single item object

#### `POST /api/market-items`
**Description**: Create new market item (admin only - future)
**Request Body**: Item object
**Response**: Created item

#### `PUT /api/market-items/:id`
**Description**: Update market item (admin only - future)
**Request Body**: Updated fields
**Response**: Updated item

#### `DELETE /api/market-items/:id`
**Description**: Delete market item (admin only - future)
**Response**: Success message

### Climate Metrics

#### `GET /api/climate-metrics`
**Description**: Get all climate metrics
**Response**:
```json
{
    "success": true,
    "count": 8,
    "data": [
        {
            "id": "c1",
            "name": "Temperature",
            "category": "climate",
            "currentValue": 28.5,
            "averageValue": 31.2,
            "unit": "°C",
            "status": "GOOD",
            "icon": "🌡️",
            "trend": [32, 31, 30, 29.5, 29, 28.5],
            "lastUpdated": "2026-02-27T07:00:00Z",
            "recommendation": "Comfortable temperature range...",
            "impact": "Lower temperatures benefit crop growth..."
        }
    ]
}
```

#### `GET /api/climate-metrics/:id`
**Description**: Get single climate metric by ID

### Best Deals

#### `GET /api/best-deals`
**Description**: Get top deals (MURA status items sorted by savings)
**Query Parameters**:
- `limit` (optional): Number of deals (default: 8)

**Response**:
```json
{
    "success": true,
    "count": 8,
    "data": [/* Array of market items with highest savings */]
}
```

### Categories

#### `GET /api/categories`
**Description**: Get all categories
**Response**:
```json
{
    "success": true,
    "data": [
        { "id": "all", "name": "All Items", "icon": "📊" },
        { "id": "vegetables", "name": "Vegetables", "icon": "🥬" }
    ]
}
```

### Favorites (Future Enhancement)

#### `GET /api/favorites`
**Description**: Get user's favorite items

#### `POST /api/favorites`
**Description**: Add item to favorites
**Request Body**:
```json
{
    "itemId": "507f1f77bcf86cd799439011",
    "itemType": "market"
}
```

#### `DELETE /api/favorites/:itemId`
**Description**: Remove item from favorites

## Frontend Integration Changes

### Files to Update

1. **`/app/frontend/src/mockData.js`** → **`/app/frontend/src/api/index.js`**
   - Replace mock data exports with API calls
   - Use axios for HTTP requests

2. **`/app/frontend/src/pages/Home.jsx`**
   - Replace `import { marketItems, climateMetrics, categories } from '../mockData'`
   - Add API calls in `useEffect` to fetch data
   - Add loading states
   - Add error handling

3. **`/app/frontend/src/components/BestDeals.jsx`**
   - Fetch best deals from API instead of using local filter

### API Service Layer

Create `/app/frontend/src/api/index.js`:
```javascript
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const marketAPI = {
    getAll: (params) => axios.get(`${API}/market-items`, { params }),
    getById: (id) => axios.get(`${API}/market-items/${id}`),
    getBestDeals: (limit = 8) => axios.get(`${API}/best-deals`, { params: { limit } })
};

export const climateAPI = {
    getAll: () => axios.get(`${API}/climate-metrics`),
    getById: (id) => axios.get(`${API}/climate-metrics/${id}`)
};

export const categoryAPI = {
    getAll: () => axios.get(`${API}/categories`)
};
```

## Implementation Steps

### Phase 1: Database Setup & Models
1. Create Pydantic models for validation
2. Set up MongoDB collections with indexes
3. Create seed script to populate initial data from mockData.js

### Phase 2: API Endpoints
1. Implement market items endpoints
2. Implement climate metrics endpoints
3. Implement best deals endpoint
4. Implement categories endpoint
5. Add proper error handling and validation

### Phase 3: Frontend Integration
1. Create API service layer
2. Update Home component to use API
3. Add loading states and error handling
4. Update BestDeals component
5. Test all functionality

### Phase 4: Testing & Optimization
1. Test all API endpoints
2. Test frontend integration
3. Add caching if needed
4. Optimize queries
5. Add pagination if needed

## Success Criteria
- All mock data replaced with database storage
- All features working identically to mock version
- Proper error handling and loading states
- Data persists across page refreshes
- API responses under 200ms for list endpoints
