"""Telegram Bot Application initialization."""
import logging
from telegram.ext import Application
from app.config import settings
from app.telegram.dispatcher import register_handlers

logger = logging.getLogger(__name__)

async def get_bot_application() -> Application | None:
    """Initialize and return the Telegram Bot Application."""
    if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        logger.info("Telegram Bot is disabled or missing token.")
        return None

    logger.info("Initializing Telegram Bot...")
    
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register all handlers
    register_handlers(application)

    return application
