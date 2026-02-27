# Climate Intel - Complete Setup & Deployment Plan

## 📋 Project Overview

**Climate Smart Advisory & Intelligence Platform** - A data intelligence platform for the Philippines that provides market, energy, and climate insights.

### Tech Stack
- **Frontend:** React 19, TailwindCSS, Shadcn UI
- **Backend:** FastAPI, Python, Motor (MongoDB async driver)
- **Database:** MongoDB Atlas (Cloud)
- **Deployment:** Vercel (Frontend) + Render.com (Backend)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Vercel                                            │
│  URL: climate-intel.vercel.app                              │
│  ENV: REACT_APP_BACKEND_URL → points to backend             │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: Render.com (Recommended) or Railway.app           │
│  URL: climate-intel-api.onrender.com                        │
│  ENV: MONGO_URL, DB_NAME, NEWSDATA_API_KEY                  │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Database: MongoDB Atlas (Cloud)                            │
│  Free M0 Cluster (512MB storage)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Phase-by-Phase Implementation

### **PHASE 1: MongoDB Atlas Setup** ⏱️ 10 minutes

#### Step 1.1: Create MongoDB Atlas Account
1. Go to https://cloud.mongodb.com
2. Sign up with email or Google account
3. Select free M0 cluster option
4. Choose cloud provider: AWS (recommended)
5. Region: Singapore or closest to Philippines
6. Cluster name: `climate-intel-cluster`

#### Step 1.2: Configure Database Security
1. **Create database user:**
   - Username: `climate_admin` (or your choice)
   - Password: Generate strong password (save this!)
   - Role: Atlas Admin (for full access)
   
2. **Configure Network Access:**
   - Click "Network Access" → "Add IP Address"
   - Select "Allow Access from Anywhere" (0.0.0.0/0)
   - Note: This is fine for development; restrict in production

#### Step 1.3: Get Connection String
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Driver: Python, Version: 3.6 or later
4. Copy connection string, should look like:
   ```
   mongodb+srv://climate_admin:<password>@climate-intel-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password

#### Step 1.4: Create Database
1. Click "Browse Collections"
2. "Add My Own Data"
3. Database name: `climate_intel`
4. Collection name: `market_items`

---

### **PHASE 2: Local Backend Setup** ⏱️ 15 minutes

#### Step 2.1: Create Backend Environment File

Create `backend/.env`:
```bash
MONGO_URL=mongodb+srv://climate_admin:<your-password>@climate-intel-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=climate_intel
NEWSDATA_API_KEY=<your-newsdata-api-key>
```

#### Step 2.2: Set Up Python Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Expected install time: ~5 minutes (134 packages)

#### Step 2.3: Seed Database
```bash
# Still in backend/ directory with venv activated
python seed_database.py
```

This will populate MongoDB with:
- ~155 market items (commodities)
- Climate metrics
- Initial data for testing

#### Step 2.4: Start Backend Server
```bash
# From backend/ directory
uvicorn server:app --reload --port 8000
```

**Verification:**
- Server should start at http://localhost:8000
- Visit http://localhost:8000/docs → Should see FastAPI Swagger UI
- Test endpoint: http://localhost:8000/api/market-items
- Should return JSON with market items

---

### **PHASE 3: Local Frontend Setup** ⏱️ 10 minutes

#### Step 3.1: Create Frontend Environment File

Create `frontend/.env`:
```bash
REACT_APP_BACKEND_URL=http://localhost:8000
```

#### Step 3.2: Install Dependencies
```bash
cd frontend
yarn install
# Or: npm install
```

Expected install time: ~3 minutes (56 packages)

#### Step 3.3: Start Frontend Dev Server
```bash
yarn start
# Or: npm start
```

**Verification:**
- App should open at http://localhost:3000
- Home page should load with market items
- Check browser console for errors
- Navigate through all pages:
  - Home (market prices)
  - Energy Intelligence
  - Climate Impact

---

### **PHASE 4: Local Testing** ⏱️ 15 minutes

#### Step 4.1: Backend Tests
```bash
# From project root
pytest backend/tests/ -v
```

Expected: 24/24 tests passing

#### Step 4.2: Manual Testing Checklist
- [ ] Home page loads with commodity cards
- [ ] Category filter works (vegetables, meat, fish, etc.)
- [ ] Search functionality works
- [ ] Sorting works (best deals, price, name)
- [ ] Market Analytics dashboard displays data
- [ ] Energy Intelligence page loads
- [ ] Energy news displays (should fetch from NewsData.io)
- [ ] WESM price charts render
- [ ] PPAs table displays
- [ ] Climate Impact page loads
- [ ] All charts render without errors
- [ ] Mobile responsiveness (resize browser)

#### Step 4.3: Test Data Integration (Optional)
Test real data scraping:
```bash
# From backend/ directory
curl -X POST "http://localhost:8000/api/integration/run-comprehensive-real-data?days=7"
```
This scrapes DA Bantay Presyo PDFs for the last 7 days.

---

### **PHASE 5: Backend Deployment to Render.com** ⏱️ 20 minutes

#### Step 5.1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub account (easier deployment)
3. Connect your GitHub account

#### Step 5.2: Push Code to GitHub (If Not Already)
```bash
cd /Users/martinbanaria/Projects/climate-intel-main
git init  # if not already initialized
git add .
git commit -m "Initial commit - Climate Intel Platform"
gh repo create climate-intel --private --source=. --push
```

#### Step 5.3: Deploy Backend on Render
1. In Render dashboard:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `climate-intel`
   
2. **Configure Service:**
   - **Name:** `climate-intel-api`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
   
3. **Add Environment Variables in Render:**
   - `MONGO_URL`: (your MongoDB Atlas connection string)
   - `DB_NAME`: `climate_intel`
   - `NEWSDATA_API_KEY`: (your NewsData.io API key)

4. Click "Create Web Service"
5. Wait for deployment (~5-10 minutes)
6. Get your backend URL: `https://climate-intel-api.onrender.com`

#### Step 5.4: Verify Backend Deployment
- Visit: `https://climate-intel-api.onrender.com/docs`
- Should see FastAPI Swagger UI
- Test: `https://climate-intel-api.onrender.com/api/market-items`
- Should return JSON data

**Important Notes:**
- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- For production, consider paid tier ($7/month) for always-on

---

### **PHASE 6: Frontend Deployment to Vercel** ⏱️ 15 minutes

#### Step 6.1: Update Frontend Environment for Production

Create `frontend/.env.production`:
```bash
REACT_APP_BACKEND_URL=https://climate-intel-api.onrender.com
```

Replace with your actual Render backend URL.

#### Step 6.2: Test Production Build Locally
```bash
cd frontend
yarn build
npx serve -s build
```
- Opens at http://localhost:3000
- Verify it connects to production backend
- Check all features work

#### Step 6.3: Deploy to Vercel

**Option A: Vercel CLI**
```bash
npm install -g vercel
cd frontend
vercel
```
Follow prompts:
- Set up and deploy? Yes
- Scope: Your account
- Link to existing project? No
- Project name: `climate-intel`
- Directory: `./` (current directory)
- Override settings? No

Then deploy to production:
```bash
vercel --prod
```

**Option B: Vercel Dashboard (Easier - Recommended)**
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New" → "Project"
4. Import your GitHub repo: `climate-intel`
5. **Configure:**
   - Framework Preset: Create React App
   - Root Directory: `frontend`
   - Build Command: `yarn build` (auto-detected)
   - Output Directory: `build` (auto-detected)
6. **Add Environment Variable:**
   - Key: `REACT_APP_BACKEND_URL`
   - Value: `https://climate-intel-api.onrender.com`
7. Click "Deploy"
8. Wait ~3 minutes for deployment

#### Step 6.4: Get Your Vercel URL
- Will be something like: `https://climate-intel-abc123.vercel.app`
- Or configure custom domain if you have one

#### Step 6.5: Update Backend CORS (Optional - For Security)

For better security, update backend CORS to only allow your Vercel domain.

In `backend/server.py` line 808, change:
```python
allow_origins=["*"]
```
to:
```python
allow_origins=[
    "http://localhost:3000",  # Local development
    "https://climate-intel-abc123.vercel.app",  # Your Vercel URL
    "https://*.vercel.app"  # All Vercel preview deployments
]
```

Then redeploy backend on Render (it auto-deploys from GitHub on push).

---

### **PHASE 7: Final Verification** ⏱️ 10 minutes

#### Production Testing Checklist
- [ ] Visit your Vercel URL
- [ ] All pages load correctly
- [ ] Market items display with real data
- [ ] Energy news fetches (check NewsData.io quota)
- [ ] Charts render properly
- [ ] Mobile responsive design works
- [ ] No console errors in browser
- [ ] Backend API calls succeed (check Network tab)
- [ ] Test from different devices/browsers

#### Performance Checks
- [ ] Lighthouse score (run in Chrome DevTools)
- [ ] Backend response times acceptable
- [ ] Images load properly
- [ ] Page load times under 3 seconds

---

## 📁 Files to Create

```
project-root/
├── backend/
│   └── .env                    # MongoDB URL, DB name, API keys (DO NOT COMMIT)
│
└── frontend/
    ├── .env                    # Local: http://localhost:8000 (DO NOT COMMIT)
    └── .env.production         # Production: https://your-backend.onrender.com (DO NOT COMMIT)
```

**Important:** All `.env` files are already in `.gitignore` and will not be committed to Git.

---

## 🚨 Important Notes & Gotchas

### **MongoDB Atlas**
- Free tier: 512MB storage (sufficient for this project)
- Automatic backups not included in free tier
- Connection limit: 500 concurrent connections
- Data transfer: 10GB/week outbound limit

### **Render.com Free Tier**
- Sleeps after 15 minutes of inactivity
- Cold start: ~30 seconds on first request after sleep
- 750 hours/month free (enough for one service)
- Auto-deploys from GitHub on push
- Build time limit: 15 minutes
- Logs retained for 7 days

### **Vercel Free Tier**
- Unlimited deployments
- 100GB bandwidth/month
- Automatic SSL/HTTPS
- Preview deployments for every git push
- Automatic CI/CD from GitHub
- Edge network for fast global access

### **NewsData.io Free Tier**
- 200 API calls/day
- Historical data: 7 days
- 10 results per request
- Consider caching news in MongoDB to reduce API calls
- Rate limit: 1 request per second

---

## 💰 Cost Breakdown

| Service | Free Tier | Paid Option (if needed) |
|---------|-----------|------------------------|
| MongoDB Atlas | 512MB | $0.08/GB (~$25/month for 5GB) |
| Render.com | 750 hrs/month | $7/month (always-on) |
| Vercel | Unlimited | $20/month (Pro features) |
| NewsData.io | 200 calls/day | $30/month (1000 calls/day) |
| **Total** | **$0/month** | **~$62/month** (if all paid) |

**Recommendation:** Free tiers are sufficient for development and moderate traffic (up to ~1000 users/month).

---

## 🎬 Execution Order

1. ✅ MongoDB Atlas setup
2. ✅ Create `backend/.env` file
3. ✅ Setup Python venv and install dependencies
4. ✅ Seed database with initial data
5. ✅ Test backend locally
6. ✅ Create `frontend/.env` file
7. ✅ Install frontend dependencies
8. ✅ Test frontend locally
9. ✅ Run backend tests (pytest)
10. ✅ Manual testing in browser
11. ✅ Push code to GitHub
12. ✅ Deploy backend to Render
13. ✅ Deploy frontend to Vercel
14. ✅ Final production testing

---

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is already in use
lsof -ti:8000 | xargs kill -9

# Check MongoDB connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import os; from dotenv import load_dotenv; load_dotenv(); client = AsyncIOMotorClient(os.environ['MONGO_URL']); print('Connected!')"
```

### Frontend Can't Connect to Backend
1. Check `REACT_APP_BACKEND_URL` is set correctly
2. Verify backend is running
3. Check CORS settings in backend
4. Check browser console for errors

### MongoDB Connection Timeout
1. Verify MongoDB Atlas IP whitelist includes 0.0.0.0/0
2. Check connection string has correct password
3. Ensure cluster is active (not paused)

### Render Deployment Fails
1. Check build logs in Render dashboard
2. Verify `requirements.txt` has all dependencies
3. Ensure start command is correct
4. Check environment variables are set

### Vercel Build Fails
1. Check build logs in Vercel dashboard
2. Verify all dependencies in `package.json`
3. Test build locally: `yarn build`
4. Check if `REACT_APP_BACKEND_URL` is set in Vercel env vars

### NewsData.io API Not Working
1. Verify API key is correct
2. Check quota (200 calls/day on free tier)
3. Test API key: `curl "https://newsdata.io/api/1/news?apikey=YOUR_KEY&q=energy"`

---

## 📚 Useful Commands

### Backend Commands
```bash
# Activate virtual environment
source backend/venv/bin/activate

# Start server
uvicorn server:app --reload --port 8000

# Run tests
pytest backend/tests/ -v

# Seed database
python backend/seed_database.py

# Run data integration
curl -X POST "http://localhost:8000/api/integration/run-comprehensive-real-data?days=7"
```

### Frontend Commands
```bash
# Start dev server
yarn start

# Build for production
yarn build

# Test production build locally
npx serve -s build

# Lint code
yarn lint
```

### Deployment Commands
```bash
# Deploy to Vercel
vercel --prod

# View Vercel logs
vercel logs

# Check Render status
curl https://climate-intel-api.onrender.com/api/
```

---

## 🔐 Security Checklist

- [ ] All `.env` files are in `.gitignore`
- [ ] No API keys committed to GitHub
- [ ] MongoDB uses strong password
- [ ] MongoDB IP whitelist configured
- [ ] CORS restricted to specific origins in production
- [ ] Vercel environment variables set correctly
- [ ] Render environment variables set correctly
- [ ] NewsData.io API key kept secret

---

## 📞 Support Resources

- **MongoDB Atlas:** https://docs.atlas.mongodb.com/
- **Render.com:** https://render.com/docs
- **Vercel:** https://vercel.com/docs
- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/

---

## 📝 Next Steps After Deployment

1. **Monitor Usage:**
   - MongoDB Atlas: Check storage and bandwidth usage
   - Render: Monitor uptime and cold start times
   - Vercel: Check bandwidth usage
   - NewsData.io: Track API call quota

2. **Performance Optimization:**
   - Implement caching for news articles
   - Add Redis for session management
   - Optimize database queries
   - Implement CDN for static assets

3. **Feature Enhancements:**
   - Add user authentication
   - Implement favorites/watchlist
   - Email alerts for price changes
   - Mobile app (React Native)

4. **Production Readiness:**
   - Set up monitoring (Sentry, LogRocket)
   - Implement analytics (Google Analytics, Plausible)
   - Add error tracking
   - Set up uptime monitoring (UptimeRobot)

---

**Last Updated:** February 27, 2026  
**Status:** Ready for Deployment  
**Estimated Total Setup Time:** ~90 minutes
