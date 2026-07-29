"""Analytics commands for Telegram."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.db import async_session_factory
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch high-level analytics."""
    async with async_session_factory() as session:
        # We can just count campaigns and contacts for a quick summary
        # For real analytics, we would query an Events table or similar
        contacts_query = await session.execute(text("SELECT COUNT(*) FROM contacts"))
        contacts_count = contacts_query.scalar()
        
        campaigns_query = await session.execute(text("SELECT COUNT(*) FROM campaigns"))
        campaigns_count = campaigns_query.scalar()
        
    msg = (
        "<b>Analytics Snapshot</b>\n\n"
        f"👥 Total Contacts: {contacts_count}\n"
        f"📢 Total Campaigns: {campaigns_count}\n\n"
        "<i>For detailed charts and metrics (open rates, click rates, etc.), please open the React Dashboard.</i>"
    )
    await update.effective_message.reply_html(msg)

def get_analytics_handlers() -> list:
    """Get all analytics command handlers."""
    return [
        CommandHandler("analytics", analytics_command),
        CommandHandler("stats", analytics_command),
    ]
