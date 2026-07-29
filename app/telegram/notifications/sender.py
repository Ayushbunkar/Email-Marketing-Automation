"""Helper to send real-time alerts to Telegram admins from FastAPI/Celery."""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_alert(message: str, parse_mode: str = "HTML") -> None:
    """
    Send an alert to all Telegram Admin IDs.
    Uses httpx directly to avoid lifecycle conflicts with the python-telegram-bot Application
    if called from a background task or another thread.
    """
    if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        return

    admin_ids = [id_str.strip() for id_str in settings.TELEGRAM_ADMIN_IDS.split(",") if id_str.strip()]
    if not admin_ids:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    async with httpx.AsyncClient() as client:
        for admin_id in admin_ids:
            payload = {
                "chat_id": admin_id,
                "text": message,
                "parse_mode": parse_mode,
            }
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.error(f"Failed to send Telegram alert to {admin_id}: {response.text}")
            except Exception as e:
                logger.error(f"Exception sending Telegram alert to {admin_id}: {e}")
