"""Campaign commands for Telegram."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.db import async_session_factory
from app.services.campaigns import list_campaigns

logger = logging.getLogger(__name__)

async def campaigns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all campaigns."""
    # Since we can't depend on FastAPI injection, we use the session factory directly
    async with async_session_factory() as session:
        campaigns = await list_campaigns(session)
        
    if not campaigns:
        await update.effective_message.reply_text("No campaigns found.")
        return
        
    msg = "<b>Campaigns:</b>\n\n"
    for camp in campaigns:
        msg += f"<b>{camp.name}</b>\n"
        msg += f"Status: {camp.status}\n"
        msg += f"Goal: {camp.goal}\n\n"
        
    await update.effective_message.reply_html(msg)

def get_campaign_handlers() -> list:
    """Get all campaign command handlers."""
    return [
        CommandHandler("campaigns", campaigns_command),
    ]
