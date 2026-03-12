"""
Telegram Bot service — sends daily price alerts to subscribers.

Uses Telegram Bot API directly via aiohttp (no additional dependencies).

Setup:
1. Create a bot via @BotFather → get TELEGRAM_BOT_TOKEN
2. Users start the bot and are subscribed via POST /api/telegram/subscribe
3. GitHub Actions calls POST /api/telegram/send-daily-alert each morning

Env vars:
  TELEGRAM_BOT_TOKEN — from BotFather
"""

import os
import logging
import aiohttp
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _token() -> Optional[str]:
    return os.environ.get("TELEGRAM_BOT_TOKEN")


async def send_message(chat_id: str, text: str) -> bool:
    """Send a message to a single chat_id. Returns True on success."""
    token = _token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping send")
        return False
    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return True
                body = await resp.text()
                logger.error(f"Telegram API error {resp.status}: {body}")
                return False
    except Exception as e:
        logger.error(f"Telegram send failed for chat_id={chat_id}: {e}")
        return False


def build_daily_alert(top_items: list, climate_metrics: list, grid_status: dict) -> str:
    """Build the daily alert message text (HTML-formatted for Telegram)."""
    now = datetime.now().strftime("%b %d, %Y")
    lines = [f"<b>🌾 Climate Intel Daily — {now}</b>\n"]

    # Top movers
    lines.append("<b>📊 Notable Price Movements</b>")
    for item in top_items[:5]:
        name = item.get("name", "Unknown")
        price = item.get("currentPrice", 0)
        label = item.get("priceStatus", "")
        emoji = "🔴" if label == "MAHAL" else "🟢" if label == "MURA" else "🟡"
        lines.append(f"{emoji} {name}: ₱{price:.2f}")

    # Climate snapshot
    lines.append("\n<b>🌤 Climate Snapshot (Manila)</b>")
    for m in climate_metrics[:4]:
        mname = m.get("name", "")
        val = m.get("currentValue") or m.get("value", "")
        unit = m.get("unit", "")
        lines.append(f"• {mname}: {val} {unit}")

    # Grid status
    if grid_status:
        status = grid_status.get("overall_status", "UNKNOWN")
        emoji = "🔴" if status == "TIGHT" else "🟡" if status == "ELEVATED" else "🟢"
        lines.append(f"\n<b>⚡ Grid Status:</b> {emoji} {status}")

    lines.append("\n<i>View full data: https://frontend-qxb1lmjh3-martin-banarias-projects.vercel.app</i>")
    return "\n".join(lines)


async def broadcast(db, message: str) -> dict:
    """Send message to all active subscribers. Returns send stats."""
    subscribers = []
    async for doc in db.telegram_subscribers.find({"active": True}, {"chat_id": 1}):
        subscribers.append(doc["chat_id"])

    sent, failed = 0, 0
    for chat_id in subscribers:
        ok = await send_message(chat_id, message)
        if ok:
            sent += 1
        else:
            failed += 1

    logger.info(f"Telegram broadcast: {sent} sent, {failed} failed out of {len(subscribers)}")
    return {"total": len(subscribers), "sent": sent, "failed": failed}
