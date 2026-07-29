"""Telegram bot endpoints (Webhook and Status)."""

from fastapi import APIRouter, Request, HTTPException, Depends
from telegram import Update
from app.config import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram."""
    # Note: In production, Telegram provides a secret token header you can verify
    # X-Telegram-Bot-Api-Secret-Token
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if settings.TELEGRAM_WEBHOOK_SECRET and secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    app = request.app
    telegram_app = getattr(app.state, "telegram_app", None)
    
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Telegram bot is not running")

    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_telegram_status(request: Request):
    """Get the current status of the Telegram Bot for the dashboard."""
    app = request.app
    telegram_app = getattr(app.state, "telegram_app", None)
    
    return {
        "enabled": settings.TELEGRAM_ENABLED,
        "is_running": telegram_app is not None,
        "mode": "webhook" if settings.TELEGRAM_WEBHOOK_URL else "polling",
        "webhook_url": settings.TELEGRAM_WEBHOOK_URL,
        "bot_info": (await telegram_app.bot.get_me()).to_dict() if telegram_app else None
    }
