"""
Agent configuration — loads backend/.env and exposes paths and constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent

# Load credentials from backend/.env (contains MONGO_URL, DB_NAME, API keys)
load_dotenv(PROJECT_ROOT / "backend" / ".env")

# MongoDB
MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME   = os.environ.get("DB_NAME", "climate_intel")

# Anthropic
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Backend endpoints
BACKEND_PROD_URL  = "https://climate-intel-api.onrender.com"
BACKEND_LOCAL_URL = "http://localhost:8000"

# Paths
MEMORY_DIR        = PROJECT_ROOT / "memory"
CLAUDE_MD         = PROJECT_ROOT / "CLAUDE.md"
ARCHITECT_MD      = MEMORY_DIR / "technical-architect-engineer.md"
