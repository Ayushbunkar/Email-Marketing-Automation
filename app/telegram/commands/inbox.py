"""Inbox and replies commands for Telegram."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from app.db import async_session_factory
from app.services.replies import list_replies

logger = logging.getLogger(__name__)

async def inbox_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List unread replies."""
    async with async_session_factory() as session:
        replies = await list_replies(session)
        
    unread = [r for r in replies if r.status == 'unread']
    
    if not unread:
        await update.effective_message.reply_text("Inbox Zero! 🎉 No unread replies.")
        return
        
    msg = f"<b>Inbox: {len(unread)} Unread Replies</b>\n\n"
    for r in unread[:3]:
        msg += f"📩 <b>From:</b> {r.from_email}\n"
        msg += f"📝 <b>Subject:</b> {r.subject}\n"
        snippet = r.body_text[:100] + "..." if len(r.body_text) > 100 else r.body_text
        msg += f"💬 <i>{snippet}</i>\n\n"
        
    if len(unread) > 3:
        msg += f"<i>...and {len(unread) - 3} more.</i>"
        
    keyboard = [
        [InlineKeyboardButton("Approve Replies", callback_data="act_approve_all")],
        [InlineKeyboardButton("Open Dashboard", callback_data="nav_inbox")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    await update.effective_message.reply_html(msg, reply_markup=reply_markup)

def get_inbox_handlers() -> list:
    """Get all inbox command handlers."""
    return [
        CommandHandler("inbox", inbox_command),
        CommandHandler("replies", inbox_command),
    ]
