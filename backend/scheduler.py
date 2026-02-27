"""
Background scheduler for automated data integration
Runs daily to fetch latest market prices
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime
from services.real_data_integration import integrate_real_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scheduled_integration():
    """Run scheduled data integration"""
    logger.info(f"[{datetime.now()}] Running scheduled DA Bantay Presyo integration...")
    try:
        result = await integrate_real_data()
        if result:
            logger.info("Scheduled integration completed successfully")
        else:
            logger.error("Scheduled integration failed")
    except Exception as e:
        logger.error(f"Error in scheduled integration: {str(e)}")

def run_scheduler():
    """Run the scheduler"""
    # Schedule daily at 8 AM
    schedule.every().day.at("08:00").do(lambda: asyncio.run(scheduled_integration()))
    
    # Schedule every 6 hours as backup
    schedule.every(6).hours.do(lambda: asyncio.run(scheduled_integration()))
    
    logger.info("Scheduler started - DA Bantay Presyo integration will run daily at 8 AM and every 6 hours")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_scheduler()
