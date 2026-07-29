"""Callback handlers for Telegram Inline Keyboards."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.telegram.commands.campaigns import campaigns_command
from app.telegram.commands.contacts import contacts_command
from app.telegram.commands.inbox import inbox_command
from app.telegram.commands.analytics import analytics_command

logger = logging.getLogger(__name__)

async def navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle navigation callbacks from the main dashboard."""
    query = update.callback_query
    await query.answer()

    data = query.data
    
    if data == "nav_dashboard":
        # Delete the previous message to prevent duplicate dashboards piling up
        try:
            await query.message.delete()
        except:
            pass
        from app.telegram.commands.system import start_command
        await start_command(update, context)
    elif data == "nav_campaigns":
        await campaigns_command(update, context)
    elif data == "nav_contacts":
        await contacts_command(update, context)
    elif data == "nav_inbox" or data == "nav_replies":
        await inbox_command(update, context)
    elif data == "nav_analytics":
        await analytics_command(update, context)
    elif data == "nav_help":
        from app.telegram.commands.system import help_command
        await help_command(update, context)
    elif data == "nav_settings":
        msg = (
            "⚙ <b>Settings</b>\n\n"
            "This bot operates securely under your Hermes Workspace.\n"
            "To manage workspace preferences (billing, team members, integrations), please use the React Dashboard.\n\n"
            "Bot ID: <code>" + str(context.bot.id) + "</code>"
        )
        await query.message.reply_html(msg)
    elif data == "nav_approvals":
        # Show pending approvals
        # Re-use inbox command for now as approvals are primarily replies in this MVP
        await inbox_command(update, context)
    else:
        await query.message.reply_html(f"Unrecognized action: {data}")

def get_callback_handlers() -> list:
    """Get all callback handlers."""
    return [
        CallbackQueryHandler(navigation_callback, pattern="^nav_"),
    ]
